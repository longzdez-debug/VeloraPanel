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
from .storage import JsonStore
from .scheduler import Job, Scheduler
from .account_pool import AccountPool
from .farm import FarmManager
from .resource import ResourceBudget, ResourceManager
from .lobby import LobbyManager
from .stats import StatsStore
from .orchestrator import FarmOrchestrator

@dataclass
class Supervisor:
    config: Config
    accounts: list = field(default_factory=list)
    running: bool = False

    def __post_init__(self):
        self.gsi = GsiServer(self.config.gsi_host, self.config.gsi_port, self.config.gsi_token)
        self.processes = ProcessSupervisor()
        self.launcher = Cs2Launcher(self.processes, self.config.process_start_timeout)
        self.route_store = RouteStore(JsonStore(f"{self.config.data_dir}/routes.json"))
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
        self.runtime_store = JsonStore(f"{self.config.data_dir}/runtime.json")
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

    def add_account(self, a):
        if not any(x.id == a.id for x in self.accounts):
            self.accounts.append(a)
        self.pool.add(a)
        self._bind_walkbot(a)
        self.scheduler.add(Job(f"account:{a.id}", a.id, enabled=False))

    def _bind_walkbot(self, a):
        def replan(position):
            if not a.route_map or not a.route_goal:
                return False
            graph = self.route_store.get(a.route_map)
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
                a.walkbot.input.release_all()

    def create_lobby(self, lobby_id, account_ids):
        return self.lobbies.create(lobby_id, list(account_ids))

    def ready_lobby(self, lobby_id, code=""):
        return self.lobbies.ready(lobby_id, code)

    def disband_lobby(self, lobby_id):
        return self.lobbies.disband(lobby_id)

    def shuffle_lobby(self, lobby_id, account_ids):
        return self.lobbies.shuffle(lobby_id, list(account_ids))

    def _save_farm(self):
        self.farm_store.save(self.farm.snapshot())
        self.runtime_store.save("scheduler", self.scheduler.snapshot())
        self.runtime_store.save("orchestrator", self.orchestrator.snapshot())
        self.stats_store.save(self.stats.snapshot())

    def create_batch(self, batch_id, account_ids, mode="manual", target_xp=None, repeat=False, max_matches=None):
        result=self.farm.create_batch(batch_id, list(account_ids), mode=mode, target_xp=target_xp, repeat=repeat, max_matches=max_matches); self._save_farm(); return result

    def start_batch(self, batch_id):
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

    def set_route(self, account_id, map_name, start, goal):
        a = self.get_account(account_id)
        if not a:
            raise KeyError(account_id)
        graph = self.route_store.get(map_name)
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
        path = graph.path_from_position(position, goal, max_snap_distance=1200)
        if not path:
            raise ValueError("no route from current position")
        a.walkbot.set_path(path)
        a.route_map, a.route_start, a.route_goal = map_name, path[0].id, goal
        return path

    def emergency_stop(self):
        self.kill_switch = True
        for a in self.accounts:
            a.walkbot.emergency_stop()

    def clear_kill_switch(self):
        self.kill_switch = False

    def start_account(self, account_id):
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
            self.resources.stop_account(a.id)
            a.errors.append(str(e))
            if a.fsm.state != AccountState.ERROR:
                a.fsm.dispatch("error")
            a.walkbot.stop()
            raise

    def stop_account(self, account_id):
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
                    self.scheduler.mark_active(job.id)
                    try:
                        self.start_account(job.account_id)
                        self.scheduler.mark_done(job.id, success=True)
                    except Exception:
                        self.scheduler.mark_done(job.id, success=False)
                self.orchestrator.tick(now)
                self._save_farm()
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
                        a.walkbot.tick(a.walkbot.last_position)
                    except Exception as exc:
                        a.walkbot.emergency_stop()
                        a.errors.append(f"WalkBot tick failed: {exc}")
                await asyncio.sleep(delay)
        finally:
            self.gsi.stop()

    def stop(self):
        self.running = False
        self._save_farm()
        for a in self.accounts:
            if a.process_id:
                self.processes.terminate(a.process_id)
                a.process_id = None
            self.resources.stop_account(a.id)
            a.started_at = None
            guard = self.window_guards.get(a.id)
            if guard is not None and hasattr(guard, "bind"):
                guard.bind(None)
            a.walkbot.stop()
