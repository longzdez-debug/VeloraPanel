import asyncio
from dataclasses import dataclass,field
from .config import Config
from .gsi import GsiServer
@dataclass
class Supervisor:
 config:Config;accounts:list=field(default_factory=list);running:bool=False
 def __post_init__(self):self.gsi=GsiServer(self.config.gsi_host,self.config.gsi_port,self.config.gsi_token)
 def add_account(self,a):self.accounts.append(a)
 def on_gsi(self,snap):
  for a in self.accounts:a.on_gsi(snap)
 async def run(self):
  self.running=True;self.gsi.on_snapshot(self.on_gsi);self.gsi.start();delay=1/max(self.config.tick_hz,1)
  try:
   while self.running:
    for a in self.accounts:
     pos=(a.walkbot.last_position)
     a.walkbot.tick(pos)
    await asyncio.sleep(delay)
  finally:self.gsi.stop()
 def stop(self):
  self.running=False
  for a in self.accounts:a.stop()
