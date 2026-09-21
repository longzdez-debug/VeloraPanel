import asyncio,logging,os
from .account import Account
from .accounts import AccountStore
from .config import Config
from .dashboard import Dashboard
from .input import NullInput
from .supervisor import Supervisor
from .walkbot import WalkBot
def main():
 logging.basicConfig(level=logging.INFO,format="%(asctime)s %(levelname)s %(message)s")
 c=Config.from_env();os.makedirs(c.data_dir,exist_ok=True);sup=Supervisor(c);store=AccountStore(os.path.join(c.data_dir,"accounts.json"))
 profiles=store.load()
 if not profiles: profiles=[]
 for p in profiles:sup.add_account(Account(p.id,p.name,WalkBot(NullInput()),p.steam_id or None))
 if not sup.accounts:sup.add_account(Account("local","Local",WalkBot(NullInput())))
 ui=Dashboard(sup,c.dashboard_host,c.dashboard_port);ui.start()
 print(f"VELORA PANEL: http://{c.dashboard_host}:{c.dashboard_port}")
 try:asyncio.run(sup.run())
 except KeyboardInterrupt:pass
 finally:ui.stop();sup.stop()
if __name__=="__main__":main()
