import asyncio
from dataclasses import dataclass,field
from .config import Config
from .gsi import GsiServer
from .process import ProcessSupervisor
@dataclass
class Supervisor:
 config:Config;accounts:list=field(default_factory=list);running:bool=False
 def __post_init__(self):self.gsi=GsiServer(self.config.gsi_host,self.config.gsi_port,self.config.gsi_token);self.processes=ProcessSupervisor()
 def add_account(self,a):
  if not any(x.id==a.id for x in self.accounts):self.accounts.append(a)
 def get_account(self,account_id):
  return next((a for a in self.accounts if a.id==account_id),None)
 def on_gsi(self,snap):
  for a in self.accounts:a.on_gsi(snap)
 async def run(self):
  self.running=True;self.gsi.on_snapshot(self.on_gsi);self.gsi.start();delay=1/max(self.config.tick_hz,1)
  try:
   while self.running:
    for a in self.accounts:a.walkbot.tick(a.walkbot.last_position)
    await asyncio.sleep(delay)
  finally:self.gsi.stop()
 def start_account(self,account_id):
  a=self.get_account(account_id)
  if not a:raise KeyError(account_id)
  a.start()
 def stop_account(self,account_id):
  a=self.get_account(account_id)
  if not a:raise KeyError(account_id)
  a.stop()
 def stop(self):
  self.running=False
  for a in self.accounts:a.stop()
