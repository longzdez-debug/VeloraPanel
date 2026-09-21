import asyncio,os
from .account import Account
from .accounts import AccountStore
from .config import Config
from .dashboard import Dashboard
from .diagnostics import run_checks
from .input import NullInput
from .log import configure_logging
from .supervisor import Supervisor
from .walkbot import WalkBot

def main():
 c=Config.from_env();os.makedirs(c.data_dir,exist_ok=True)
 logger=configure_logging(c.data_dir)
 checks=run_checks(c.data_dir,c.gsi_port,c.dashboard_port)
 for check in checks:logger.info("diagnostic %s: %s - %s",check.name,check.ok,check.detail)
 sup=Supervisor(c);store=AccountStore(os.path.join(c.data_dir,"accounts.json"))
 for p in store.load():sup.add_account(Account(p.id,p.name,WalkBot(NullInput()),p.steam_id or None))
 if not sup.accounts:sup.add_account(Account("local","Local",WalkBot(NullInput())))
 ui=Dashboard(sup,c.dashboard_host,c.dashboard_port);ui.start()
 logger.info("VELORA PANEL: http://%s:%s",c.dashboard_host,c.dashboard_port)
 try:asyncio.run(sup.run())
 except KeyboardInterrupt:logger.info("shutdown requested")
 finally:ui.stop();sup.stop()

if __name__=="__main__":main()
