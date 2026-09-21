import asyncio
from .config import Config
from .input import NullInput
from .walkbot import WalkBot
from .account import Account
from .supervisor import Supervisor
from .dashboard import Dashboard
from .log import configure
async def main():
 configure();s=Supervisor(Config.from_env());s.add_account(Account("local","Local",WalkBot(NullInput())));ui=Dashboard(s);ui.start()
 print("VELORA PANEL: http://127.0.0.1:8765")
 try:await s.run()
 except KeyboardInterrupt:pass
 finally:s.stop();ui.stop()
if __name__=="__main__":asyncio.run(main())
