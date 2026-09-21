from __future__ import annotations
import asyncio
from time import monotonic
from dataclasses import dataclass, field
from .config import Config
from .gsi import GsiServer
from .process import ProcessSupervisor
from .launcher import Cs2Launcher
from .model import AccountState
from .routes import RouteStore
from .storage import JsonStore
from .scheduler import Job, Scheduler

@dataclass
class Supervisor:
    config: Config
    accounts: list = field(default_factory=list)
    running: bool = False

    def __post_init__(self):
        self.gsi = GsiServer(self.config.gsi_host, self.config.gsi_port, self.config.gsi_token)
        self.processes = ProcessSupervisor()
        self.launcher = Cs2Launcher(self.processes)
        self.route_store = RouteStore(JsonStore(f"{self.config.data_dir}/routes.json"))
        self.scheduler = Scheduler(max_concurrent=1)
        self.kill_switch = False
        self.window_guards = {}
        self._watchdog_due = {}

    def add_account(self, a):
        if not any(x.id == a.id for x in self.accounts):
            self.accounts.append(a)
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

    def on_gsi(self, snap):
        for a in self.accounts:
            a.on_gsi(snap)
            if a.route_map and snap.map_name and snap.map_name != a.route_map:
                a.walkbot.input.release_all()

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
        a.start()
        try:
            r = self.launcher.start(a.executable, a.launch_args)
            a.process_id = r.identity.pid
            a.executable = r.executable
            guard = self.window_guards.get(a.id)
            if guard is not None and hasattr(guard, "bind"):
                guard.bind(a.process_id)
            return a.process_id
        except Exception as e:
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
        guard = self.window_guards.get(a.id)
        if guard is not None and hasattr(guard, "bind"):
            guard.bind(None)
        a.stop()

    def _process_death(self, a):
        pid = a.process_id
        a.process_id = None
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
                for a in self.accounts:
                    if a.process_id and not self.processes.alive(a.process_id):
                        self._process_death(a)
                    if (a.process_id is None and a.next_restart_at and now >= a.next_restart_at
                            and a.restart_count <= self.config.watchdog_max_restarts and not self.kill_switch):
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
        for a in self.accounts:
            if a.process_id:
                self.processes.terminate(a.process_id)
                a.process_id = None
            guard = self.window_guards.get(a.id)
            if guard is not None and hasattr(guard, "bind"):
                guard.bind(None)
            a.walkbot.stop()
