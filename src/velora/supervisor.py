from __future__ import annotations
import asyncio
from dataclasses import dataclass, field
from time import monotonic, time
from .config import Config
from .gsi import GsiServer
from .process import ProcessSupervisor
from .launcher import Cs2Launcher
from .model import AccountState
from .routes import RouteStore
from .route_database import RouteDatabase
from .storage import JsonStore
from .scheduler import Job, Scheduler
from .account_pool import AccountPool
from .farm import BatchState, FarmManager
from .resource import ResourceBudget, ResourceManager
from .lobby import LobbyManager
from .stats import StatsStore
from .orchestrator import BatchRuntime, FarmOrchestrator
from .log import get_logger

@dataclass
class Supervisor:
    config: Config
    accounts: list = field(default_factory=list)
    running: bool = False

    def __post_init__(self):
        self.logger = get_logger("supervisor")
        self.logger.info("supervisor initializing")
        self.gsi = GsiServer(self.config.gsi_host, self.config.gsi_port, self.config.gsi_token)
        self.processes = ProcessSupervisor()
        self.launcher = Cs2Launcher(self.processes, self.config.process_start_timeout)
        self.route_store = RouteStore(JsonStore(f"{self.config.data_dir}/routes.json"))
        self.route_database = RouteDatabase()
        self.pool = AccountPool()
        self.resources = ResourceManager(ResourceBudget(max_accounts=getattr(self.config, "max_concurrent_accounts", 1), max_batches=getattr(self.config, "max_parallel_batches", 1)))
        self.farm = FarmManager(self.pool, self.resources)
        self.farm_store = JsonStore(f"{self.config.data_dir}/farm.json")
        self.farm.load_snapshot(self.farm_store.load([]))
        self.scheduler = Scheduler(max_concurrent=getattr(self.config, "max_concurrent_accounts", 1))
        self.lobbies = LobbyManager()
        self.stats = StatsStore()
        self.stats_store = JsonStore(f"{self.config.data_dir}/stats.json")
        self.stats.load_snapshot(self.stats_store.load([]))
        self.runtime_store = JsonStore(f"{self.config.data_dir}/runtime")
        self.orchestrator = FarmOrchestrator(self)
        self.scheduler.load_snapshot(self.runtime_store.load("scheduler", []))
        self.orchestrator.load_snapshot(self.runtime_store.load("orchestrator", []))
        # A FARMING batch is recoverable only when its persisted runtime still
        # contains the active match identity. If the two durable snapshots got
        # out of sync (for example, a crash between atomic saves), fail closed
        # instead of leaving the batch permanently stuck in FARMING.
        for batch in self.farm.batches.values():
            runtime = self.orchestrator.runtime.get(batch.id)
            if batch.state.value == "farming" and (runtime is None or runtime.match_key is None):
                batch.state = type(batch.state).ERROR
                batch.errors.append("recovery required: active match runtime is missing")
        self.kill_switch = False
        self.window_guards = {}
        self.matchmaking = {}
        self.account_store = None
        self._last_persist_at = 0.0
        self._persist_interval = 0.5

    def attach_account_store(self, store):
        self.account_store = store

    def bind_matchmaking(self, account_id, adapter):
        self.matchmaking[account_id] = adapter

    def _auto_matchmaking_tick(self, a):
        if not self.config.auto_matchmaking or self.kill_switch or not a.process_id:
            return
        if a.fsm.state != AccountState.MENU:
            return
        adapter = self.matchmaking.get(a.id)
        if adapter is None:
            return
        try:
            if adapter.start(self.config.matchmaking_mode):
                self.logger.info("automatic matchmaking started account=%s mode=%s", a.id, self.config.matchmaking_mode)
        except Exception as exc:
            a.errors.append(f"automatic matchmaking failed: {exc}")
            self.logger.exception("automatic matchmaking failed account=%s", a.id)

    def _ensure_route_for_live(self, a):
        if not a.route_map or not a.route_goal or not a.walkbot.enabled:
            return
        if a.walkbot.last_position is None or a.walkbot.path:
            return
        try:
            self.set_route_from_position(a.id, a.route_map, a.route_goal, a.walkbot.last_position)
            self.logger.info("auto route assigned account=%s map=%s goal=%s", a.id, a.route_map, a.route_goal)
        except Exception as exc:
            self.logger.debug("auto route not assigned account=%s: %s", a.id, exc)

    def save_account_profile(self, account_id):
        if self.account_store is None:
            return
        a = self.get_account(account_id)
        if a is None:
            raise KeyError(account_id)
        from .accounts import AccountProfile
        current = next((p for p in self.account_store.load() if p.id == account_id), None)
        route_map = getattr(a, "route_map", None)
        route_start = getattr(a, "route_start", None)
        route_goal = getattr(a, "route_goal", None)
        if route_map is None and current is not None:
            route_map = current.route_map
        if route_start is None and current is not None:
            route_start = current.route_start
        if route_goal is None and current is not None:
            route_goal = current.route_goal
        self.account_store.upsert(AccountProfile(
            id=a.id,
            name=a.name,
            steam_id=a.steam_id or "",
            enabled=a.enabled,
            walkbot=bool(getattr(a.walkbot, "enabled", True)),
            executable=a.executable,
            launch_args=list(a.launch_args),
            route_map=route_map,
            route_start=route_start,
            route_goal=route_goal,
        ))

    def add_account(self, a):
        self.logger.info("account added id=%s name=%s enabled=%s", a.id, getattr(a, "name", "<unnamed>"), a.enabled)
        if not any(x.id == a.id for x in self.accounts):
            self.accounts.append(a)
        self.pool.add(a)
        self._bind_walkbot(a)
        existing = self.scheduler.get(f"account:{a.id}")
        if existing is None:
            self.scheduler.add(Job(f"account:{a.id}", a.id, enabled=False))

    def _bind_walkbot(self, a):
        def replan(position):
            if not a.route_map or not a.route_goal:
                return False
            graph = self.route_store.get(a.route_map)
            self.route_database.import_graph(a.route_map, graph, route_id="default")
            selected = self.route_database.select(a.route_map)
            if selected is None:
                return False
            path = graph.path_from_position(position, a.route_goal, max_snap_distance=1200)
            if not path:
                return False
            a.walkbot.set_path(path)
            return True
        a.walkbot.replan = replan

    def bind_window_guard(self, account_id, guard):
        self.window_guards[account_id] = guard
        a = self.get_account(account_id)
        if a and hasattr(guard, "bind"):
            guard.bind(a.process_id)

    def remove_account(self, account_id):
        self.logger.info("account removal requested id=%s", account_id)
        a = self.get_account(account_id)
        if a is None:
            raise KeyError(account_id)
        if any(account_id in b.account_ids and b.state not in (BatchState.IDLE, BatchState.FINISHED, BatchState.ERROR) for b in self.farm.batches.values()):
            raise RuntimeError("account is used by an active batch")
        if a.process_id or a.fsm.state != AccountState.OFFLINE:
            self.stop_account(account_id)
        self.scheduler.remove(f"account:{account_id}")
        self.pool.remove(account_id)
        self.accounts = [item for item in self.accounts if item.id != account_id]
        self.window_guards.pop(account_id, None)
        if self.account_store is not None:
            profiles = [p for p in self.account_store.load() if p.id != account_id]
            self.account_store.save(profiles)

    def get_account(self, account_id):
        return next((x for x in self.accounts if x.id == account_id), None)

    def schedule_account(self, account_id, priority=0, cooldown=0.0):
        if not self.get_account(account_id):
            raise KeyError(account_id)
        self.scheduler.add(Job(f"account:{account_id}", account_id, priority=priority, cooldown=cooldown, enabled=True))
        return f"account:{account_id}"

    def unschedule_account(self, account_id):
        self.scheduler.remove(f"account:{account_id}")

    def on_gsi(self, snap):
        if snap.steam_id:
            targets = [a for a in self.accounts if a.steam_id and a.steam_id == snap.steam_id]
        else:
            unbound = [a for a in self.accounts if not a.steam_id]
            targets = unbound if len(unbound) == 1 else []
        for a in targets:
            a.on_gsi(snap)
            if a.route_map and snap.map_name and snap.map_name != a.route_map:
                a.walkbot.emergency_stop()

    def create_lobby(self, lobby_id, account_ids):
        return self.lobbies.create(lobby_id, list(account_ids))

    def ready_lobby(self, lobby_id, code=""):
        return self.lobbies.ready(lobby_id, code)

    def disband_lobby(self, lobby_id):
        return self.lobbies.disband(lobby_id)

    def shuffle_lobby(self, lobby_id, account_ids):
        return self.lobbies.shuffle(lobby_id, list(account_ids))

    def _save_farm(self, force=True):
        now = monotonic()
        if not force and now - self._last_persist_at < self._persist_interval:
            return False
        self._last_persist_at = now
        self.farm_store.save(self.farm.snapshot())
        self.runtime_store.save("scheduler", self.scheduler.snapshot())
        self.runtime_store.save("orchestrator", self.orchestrator.snapshot())
        self.stats_store.save(self.stats.snapshot())
        return True

    def create_batch(self, batch_id, account_ids, mode="manual", target_xp=None, repeat=False, max_matches=None):
        self.logger.info("batch create id=%s mode=%s accounts=%d", batch_id, mode, len(account_ids))
        result=self.farm.create_batch(batch_id, list(account_ids), mode=mode, target_xp=target_xp, repeat=repeat, max_matches=max_matches); self._save_farm(); return result

    def start_batch(self, batch_id):
        self.logger.info("batch start id=%s", batch_id)
        batch = self.farm.start_batch(batch_id)
        # Establish the farm baseline before any process can emit a GSI event.
        # Otherwise the GSI callback may race with startup and its first XP value
        # could be discarded after the launcher returns.
        for account_id in batch.account_ids:
            state = self.pool.farm[account_id]
            state.xp_before = None
            state.xp_after = None
            account = self.get_account(account_id)
            if account is not None:
                account.last_xp = None
                account.last_gsi = None
                account.last_provider_timestamp = None
                account.last_match_result = None
                account.last_score = None
                account.last_opponent_score = None
                account.match_rounds = 0
                account.match_terminal_latched = False
        started = []
        try:
            for account_id in batch.account_ids:
                self.start_account(account_id)
                started.append(account_id)
        except Exception as exc:
            batch.errors.append(str(exc))
            self.farm.stop_batch(batch_id)
            for account_id in started:
                try:
                    self.stop_account(account_id)
                except Exception:
                    pass
            self._save_farm()
            raise
        self.farm.mark_ready(batch_id)
        self._save_farm()
        return batch

    def stop_batch(self, batch_id):
        self.logger.info("batch stop id=%s", batch_id)
        batch = self.farm.stop_batch(batch_id)
        for account_id in batch.account_ids:
            try:
                self.stop_account(account_id)
            except Exception:
                pass
        self._save_farm()
        return batch

    def batch_player_ready(self, batch_id):
        result=self.farm.player_ready(batch_id); self._save_farm(); return result

    def batch_start_search(self, batch_id):
        result=self.farm.start_search(batch_id); self._save_farm(); return result

    def batch_match_found(self, batch_id, match_id=None):
        result=self.farm.match_found(batch_id, match_id); self._save_farm(); return result

    def recover_batch(self, batch_id):
        self.logger.warning("batch recovery requested id=%s", batch_id)
        batch = self.farm.recover_farming_batch(batch_id)
        runtime = self.orchestrator.runtime.setdefault(batch.id, BatchRuntime(batch.id))
        runtime.recovery_claimed = True
        started = []
        try:
            for account_id in batch.account_ids:
                self.start_account(account_id)
                started.append(account_id)
        except Exception as exc:
            batch.errors.append(f"recovery failed: {exc}")
            for account_id in started:
                try:
                    self.stop_account(account_id)
                except Exception:
                    pass
            self.farm.resources.stop_batch(batch.id)
            runtime.recovery_claimed = False
            self._save_farm()
            raise
        self._save_farm()
        return batch

    def delete_batch(self, batch_id):
        batch = self.farm.batches.get(batch_id)
        if batch is None:
            raise KeyError(batch_id)
        if batch.state not in (BatchState.IDLE, BatchState.FINISHED, BatchState.ERROR):
            raise RuntimeError("cannot delete an active batch")
        self.farm.batches.pop(batch_id)
        self.orchestrator.runtime.pop(batch_id, None)
        if batch_id in self.lobbies.lobbies:
            self.lobbies.disband(batch_id)
        self._save_farm()

    def set_route(self, account_id, map_name, start, goal):
        a = self.get_account(account_id)
        if not a:
            raise KeyError(account_id)
        graph = self.route_store.get(map_name)
        self.route_database.import_graph(map_name, graph, route_id="default")
        path = graph.shortest_path(start, goal)
        if not path:
            raise ValueError("no route")
        a.walkbot.set_path(path)
        a.route_map, a.route_start, a.route_goal = map_name, start, goal
        return path

    def set_route_from_position(self, account_id, map_name, goal, position):
        a = self.get_account(account_id)
        if not a:
            raise KeyError(account_id)
        graph = self.route_store.get(map_name)
        self.route_database.import_graph(map_name, graph, route_id="default")
        path = graph.path_from_position(position, goal, max_snap_distance=1200)
        if not path:
            raise ValueError("no route from current position")
        a.walkbot.set_path(path)
        a.route_map, a.route_start, a.route_goal = map_name, path[0].id, goal
        return path

    def emergency_stop(self):
        self.logger.critical("EMERGENCY STOP ALL")
        self.kill_switch = True
        for batch in list(self.farm.batches.values()):
            if batch.state not in (BatchState.FINISHED, BatchState.STOPPING, BatchState.IDLE):
                try:
                    self.stop_batch(batch.id)
                except Exception as exc:
                    batch.errors.append(f"emergency stop failed: {exc}")
        for a in self.accounts:
            try:
                self.stop_account(a.id)
            except Exception as exc:
                a.errors.append(f"emergency stop failed: {exc}")
            a.walkbot.emergency_stop()
        self._save_farm()

    def clear_kill_switch(self):
        self.logger.warning("KILL SWITCH cleared")
        self.kill_switch = False

    def start_account(self, account_id):
        self.logger.info("account start requested id=%s", account_id)
        if self.kill_switch:
            raise RuntimeError("global kill switch is active")
        a = self.get_account(account_id)
        if not a:
            raise KeyError(account_id)
        if a.process_id and self.processes.alive(a.process_id):
            return a.process_id
        if not self.resources.start_account(a.id):
            raise RuntimeError("account resource capacity reached")
        # Reset GSI sequencing before launching so no first snapshot can race
        # with a post-launch reset.
        a.last_gsi = None
        a.last_provider_timestamp = None
        a.last_xp = None
        a.start()
        try:
            r = self.launcher.start(a.executable, a.launch_args, via_steam=self.config.launch_via_steam)
            a.process_id = r.identity.pid
            a.executable = r.executable
            a.started_at = monotonic()
            guard = self.window_guards.get(a.id)
            if guard is not None and hasattr(guard, "bind"):
                guard.bind(a.process_id)
            return a.process_id
        except Exception as e:
            self.logger.exception("account start failed id=%s", account_id)
            self.resources.stop_account(a.id)
            a.errors.append(str(e))
            if a.fsm.state != AccountState.ERROR:
                a.fsm.dispatch("error")
            a.walkbot.stop()
            a.stop()
            raise

    def stop_account(self, account_id):
        self.logger.info("account stop requested id=%s", account_id)
        a = self.get_account(account_id)
        if not a:
            raise KeyError(account_id)
        if a.process_id:
            self.processes.terminate(a.process_id)
            a.process_id = None
        self.resources.stop_account(a.id)
        guard = self.window_guards.get(a.id)
        if guard is not None and hasattr(guard, "bind"):
            guard.bind(None)
        a.stop()

    def _process_death(self, a):
        pid = a.process_id
        if pid:
            try:
                if self.processes.alive(pid):
                    self.processes.terminate(pid)
            except OSError:
                pass
        a.process_id = None
        a.started_at = None
        a.last_gsi = None
        self.resources.stop_account(a.id)
        a.walkbot.emergency_stop()
        guard = self.window_guards.get(a.id)
        if guard is not None and hasattr(guard, "bind"):
            guard.bind(None)
        a.errors.append(f"CS2 process exited (pid {pid})")
        if a.fsm.state not in (AccountState.OFFLINE, AccountState.ERROR):
            try:
                a.fsm.dispatch("error")
            except Exception:
                pass
        if self.config.watchdog_enabled and a.enabled and not self.kill_switch:
            a.restart_count += 1
            if a.restart_count <= self.config.watchdog_max_restarts:
                a.next_restart_at = monotonic() + self.config.watchdog_backoff * (2 ** (a.restart_count - 1))
            else:
                a.errors.append("watchdog restart limit reached")

    async def run(self):
        self.logger.info("supervisor run loop starting")
        self.running = True
        self.gsi.on_snapshot(self.on_gsi)
        self.gsi.start()
        delay = 1 / max(self.config.tick_hz, 1)
        try:
            while self.running:
                now = monotonic()
                scheduler_now = time()
                job = self.scheduler.next(scheduler_now)
                if job is not None and not self.kill_switch:
                    account = self.get_account(job.account_id)
                    # A scheduler job must never launch an account that is
                    # already owned by a live farm batch or process.
                    if account is None or account.process_id or any(
                        job.account_id in batch.account_ids
                        and batch.state in (
                            BatchState.SELECTING,
                            BatchState.STARTING,
                            BatchState.WAITING_FOR_READY,
                            BatchState.FARMING,
                            BatchState.STOPPING,
                        )
                        for batch in self.farm.batches.values()
                    ):
                        self.scheduler.mark_done(job.id, success=True, now=scheduler_now)
                    else:
                        self.scheduler.mark_active(job.id)
                        try:
                            self.start_account(job.account_id)
                            self.scheduler.mark_done(job.id, success=True, now=scheduler_now)
                        except Exception:
                            self.scheduler.mark_done(job.id, success=False, now=scheduler_now)
                self.orchestrator.tick(now)
                self._save_farm(force=False)
                for a in self.accounts:
                    if a.process_id and not self.processes.alive(a.process_id):
                        self._process_death(a)
                    if (
                        a.process_id and a.started_at and a.last_gsi is None
                        and now - a.started_at > self.config.process_start_timeout
                    ):
                        a.errors.append(f"startup readiness timeout ({self.config.process_start_timeout:.0f}s)")
                        self._process_death(a)
                    if (
                        a.process_id is None and a.next_restart_at and now >= a.next_restart_at
                        and a.restart_count <= self.config.watchdog_max_restarts and not self.kill_switch
                    ):
                        a.next_restart_at = 0.0
                        try:
                            self.start_account(a.id)
                            a.errors.append(f"watchdog restart #{a.restart_count}")
                        except Exception as exc:
                            a.errors.append(f"watchdog restart failed: {exc}")
                    try:
                        self._auto_matchmaking_tick(a)
                        if a.fsm.state == AccountState.IN_MATCH:
                            self._ensure_route_for_live(a)
                        a.walkbot.tick(a.walkbot.last_position)
                    except Exception as exc:
                        a.walkbot.emergency_stop()
                        a.errors.append(f"WalkBot tick failed: {exc}")
                await asyncio.sleep(delay)
        except Exception:
            self.logger.exception("supervisor run loop crashed")
            raise
        finally:
            self.logger.info("supervisor run loop stopping")
            self.gsi.stop()

    def stop(self):
        self.logger.info("supervisor shutdown requested")
        self.running = False
        # Persist the post-shutdown state, never a pre-shutdown FARMING snapshot.
        for batch in list(self.farm.batches.values()):
            if batch.state not in (BatchState.FINISHED, BatchState.STOPPING, BatchState.IDLE):
                try:
                    self.stop_batch(batch.id)
                except Exception as exc:
                    batch.errors.append(f"shutdown stop failed: {exc}")
        for a in self.accounts:
            try:
                if a.process_id:
                    self.processes.terminate(a.process_id)
            except Exception:
                pass
            a.process_id = None
            a.started_at = None
            self.resources.stop_account(a.id)
            guard = self.window_guards.get(a.id)
            if guard is not None and hasattr(guard, "bind"):
                guard.bind(None)
            a.walkbot.stop()
            try:
                a.stop()
            except Exception:
                pass
        self._save_farm()
