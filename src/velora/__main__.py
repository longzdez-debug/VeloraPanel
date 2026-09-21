import asyncio
import os

from velora.account import Account
from velora.accounts import AccountStore
from velora.config import Config
from velora.dashboard import Dashboard
from velora.diagnostics import run_checks
from velora.input import NullInput
from velora.log import configure_logging
from velora.supervisor import Supervisor
from velora.walkbot import WalkBot
from velora.window_guard import Cs2WindowGuard
from velora.windows import WindowsInput


async def _run_supervisor(sup, logger):
    loop = asyncio.get_running_loop()

    def handle_asyncio_error(loop, context):
        logger.error("ASYNCIO LOOP ERROR: %s", context.get("message", "unknown"), exc_info=context.get("exception"))

    loop.set_exception_handler(handle_asyncio_error)
    await sup.run()


def main():
    c = Config.from_env()
    os.makedirs(c.data_dir, exist_ok=True)
    logger = configure_logging(c.data_dir)
    for check in run_checks(c.data_dir, c.gsi_port, c.dashboard_port, c.gsi_host):
        logger.info("diagnostic %s: %s - %s", check.name, check.ok, check.detail)

    logger.info("VELORA PANEL startup: python=%s pid=%s", os.sys.version.split()[0], os.getpid())
    logger.info(
        "WalkBot input: enabled=%s foreground_guard=%s mouse_turn_counts=%s",
        c.input_enabled, c.input_require_foreground, c.mouse_turn_counts,
    )
    sup = Supervisor(c)
    store = AccountStore(os.path.join(c.data_dir, "accounts.json"))
    sup.attach_account_store(store)
    profiles = store.load()
    if not profiles:
        profiles = [type("P", (), {
            "id": "local", "name": "Local", "steam_id": "", "enabled": True,
            "walkbot": True, "executable": "", "launch_args": []
        })()]

    for p in profiles:
        if c.input_enabled:
            guard = Cs2WindowGuard(sup.processes, c.input_require_foreground)
            adapter = WindowsInput(
                enabled=True,
                guard=guard,
                mouse_turn_counts=c.mouse_turn_counts,
            )
            sup.bind_window_guard(p.id, guard)
        else:
            adapter = NullInput()
        account = Account(
            p.id, p.name, WalkBot(adapter), p.steam_id or None,
            enabled=p.enabled, executable=p.executable, launch_args=list(p.launch_args),
        )
        account.walkbot.enabled = bool(p.walkbot)
        account.route_map = getattr(p, "route_map", None)
        account.route_start = getattr(p, "route_start", None)
        account.route_goal = getattr(p, "route_goal", None)
        sup.add_account(account)
        if account.route_map and account.route_goal:
            try:
                sup.set_route(account.id, account.route_map, account.route_start or account.route_goal, account.route_goal)
            except Exception as exc:
                logger.warning("route restore failed for %s: %s", account.id, exc)

    ui = Dashboard(sup, c.dashboard_host, c.dashboard_port)
    ui.start()
    logger.info("VELORA PANEL: http://%s:%s", c.dashboard_host, c.dashboard_port)
    try:
        asyncio.run(_run_supervisor(sup, logger))
    except KeyboardInterrupt:
        logger.info("shutdown requested")
    finally:
        logger.info("VELORA PANEL shutdown")
        ui.stop()
        sup.stop()


if __name__ == "__main__":
    main()
