import asyncio
from dataclasses import dataclass,field
from .config import Config
from .gsi import GsiServer
from .process import ProcessSupervisor
from .launcher import Cs2Launcher
from .routes import RouteStore
from .storage import JsonStore
@dataclass
class Supervisor:
 config:Config;accounts:list=field(default_factory=list);running:bool=False
 def __post_init__(self):
  self.gsi=GsiServer(self.config.gsi_host,self.config.gsi_port,self.config.gsi_token);self.processes=ProcessSupervisor();self.launcher=Cs2Launcher(self.processes)
  self.route_store=RouteStore(JsonStore(f"{self.config.data_dir}/routes.json"));self.kill_switch=False
 def add_account(self,a):
  if not any(x.id==a.id for x in self.accounts):self.accounts.append(a)
 def get_account(self,account_id):return next((a for a in self.accounts if a.id==account_id),None)
 def on_gsi(self,snap):
  for a in self.accounts:a.on_gsi(snap)
 def set_route(self,account_id,map_name,start,goal):
  a=self.get_account(account_id)
  if not a:raise KeyError(account_id)
  graph=self.route_store.get(map_name);path=graph.shortest_path(start,goal)
  if not path:raise ValueError("no route")
  a.walkbot.set_path(path);a.route_map=map_name;a.route_start=start;a.route_goal=goal
  return path
 def emergency_stop(self):
  self.kill_switch=True
  for a in self.accounts:a.walkbot.emergency_stop()
 def clear_kill_switch(self):self.kill_switch=False
 def start_account(self,account_id):
  if self.kill_switch:raise RuntimeError("global kill switch is active")
  a=self.get_account(account_id)
  if not a:raise KeyError(account_id)
  a.start()
  try:
   r=self.launcher.start(a.executable,a.launch_args);a.process_id=r.identity.pid;a.executable=r.executable;a.on_ready()
  except Exception as e:
   a.errors.append(str(e));a.fsm.dispatch("error");a.walkbot.stop();raise
 def stop_account(self,account_id):
  a=self.get_account(account_id)
  if not a:raise KeyError(account_id)
  if a.process_id:self.processes.terminate(a.process_id);a.process_id=None
  a.stop()
 async def run(self):
  self.running=True;self.gsi.on_snapshot(self.on_gsi);self.gsi.start();delay=1/max(self.config.tick_hz,1)
  try:
   while self.running:
    for a in self.accounts:
     if a.process_id and not self.processes.alive(a.process_id):a.process_id=None;a.errors.append("CS2 process exited")
     a.walkbot.tick(a.walkbot.last_position)
    await asyncio.sleep(delay)
  finally:self.gsi.stop()
 def stop(self):
  self.running=False
  for a in self.accounts:
   if a.process_id:self.processes.terminate(a.process_id);a.process_id=None
   a.stop()
