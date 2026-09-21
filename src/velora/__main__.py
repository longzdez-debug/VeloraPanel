import asyncio
import os
from .account import Account
from .accounts import AccountStore
from .config import Config
from .dashboard import Dashboard
from .diagnostics import run_checks
from .input import NullInput
from .log import configure_logging
from .supervisor import Supervisor
from .walkbot import WalkBot
from .window_guard import Cs2WindowGuard
from .windows import WindowsInput

def main():
    c = Config.from_env()
    os.makedirs(c.data_dir, exist_ok=True)
    logger = configure_logging(c.data_dir)
    for check in run_checks(c.data_dir, c.gsi_port, c.dashboard_port, c.gsi_host):
        logger.info("diagnostic %s: %s - %s", check.name, check.ok, check.detail)

    sup = Supervisor(c)
    store = AccountStore(os.path.join(c.data_dir, "accounts.json"))
    profiles = store.load()
    if not profiles:
        profiles = [type("P", (), {
            "id": "local", "name": "Local", "steam_id": "", "enabled": True,
            "walkbot": True, "executable": "", "launch_args": []
        })()]

    for p in profiles:
        if c.input_enabled:
            guard = Cs2WindowGuard(sup.processes, c.input_require_foreground)
            adapter = WindowsInput(enabled=True, guard=guard)
            sup.bind_window_guard(p.id, guard)
        else:
            adapter = NullInput()
        account = Account(
            p.id, p.name, WalkBot(adapter), p.steam_id or None,
            enabled=p.enabled, executable=p.executable, launch_args=list(p.launch_args),
        )
        account.walkbot.enabled = bool(p.walkbot)
        sup.add_account(account)

    ui = Dashboard(sup, c.dashboard_host, c.dashboard_port)
    ui.start()
    logger.info("VELORA PANEL: http://%s:%s", c.dashboard_host, c.dashboard_port)
    try:
        asyncio.run(sup.run())
    except KeyboardInterrupt:
        logger.info("shutdown requested")
    finally:
        ui.stop()
        sup.stop()

if __name__ == "__main__":
    main()
