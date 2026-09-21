import asyncio
from .config import Config
from .input import NullInput
from .walkbot import WalkBot
from .account import Account
from .supervisor import Supervisor
from .dashboard import Dashboard
async def main():
 s=Supervisor(Config.from_env());s.add_account(Account("local","Local",WalkBot(NullInput())));ui=Dashboard(s);ui.start()
 try:await s.run()
 except KeyboardInterrupt:pass
 finally:s.stop();ui.stop()
if __name__=="__main__":asyncio.run(main())
