from __future__ import annotations
import json,time
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
from threading import Thread
from urllib.parse import urlparse,unquote
from .diagnostics import as_dict,run_checks
from .routes import Node

HTML="""<!doctype html><html><head><meta charset=utf-8><meta name=viewport content="width=device-width,initial-scale=1"><title>VELORA PANEL</title>
<style>*{box-sizing:border-box}body{font:14px system-ui;margin:0;padding:24px;background:#090b0f;color:#eef0f3}.bar{display:flex;gap:8px;align-items:center;flex-wrap:wrap}.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(330px,1fr));gap:14px}.card{background:#141820;border:1px solid #282f3a;border-radius:14px;padding:18px}.pill{padding:5px 9px;border-radius:99px;background:#202733}.big{font-size:24px;font-weight:750;margin:10px 0}.muted{color:#8d97a6}button{background:#eef0f3;color:#111;border:0;border-radius:8px;padding:7px 10px;margin:3px;cursor:pointer}.danger{background:#e9baba}input,select{background:#0d1117;color:#fff;border:1px solid #303744;border-radius:7px;padding:7px;width:110px}pre{white-space:pre-wrap;max-height:260px;overflow:auto}.ok{color:#8fd694}.bad{color:#ef8f8f}</style></head>
<body><header class=bar><div><h1>VELORA PANEL</h1><div class=muted>Control plane / Account FSM / Match FSM / WalkBot / GSI / Routes</div></div><span id=h class=pill>offline</span><button onclick="diag()">Diagnostics</button><button onclick="clearKill()">Clear kill switch</button><button class=danger onclick="kill()">EMERGENCY STOP ALL</button></header>
<section class=card><h2>Accounts</h2><div class=bar><input id=bid placeholder='batch id'><select id=bmode><option value='manual'>Manual</option><option value='2v2'>2v2</option><option value='2v2_random'>2v2 random</option><option value='5v5'>5v5</option><option value='5v5_shuffle'>5v5 shuffle</option><option value='deathmatch'>Deathmatch</option><option value='arms_race'>Arms Race</option><option value='armory'>Armory</option></select><button onclick='createBatch()'>Create batch from selected</button><button onclick='startBatch()'>Start batch</button><button onclick='stopBatch()'>Stop batch</button></div><div id=b class=grid></div><div id=a class=grid></div></section>
<section class=card style="margin-top:16px"><h2>Route editor</h2><div class=bar><select id=map></select><button onclick="refreshMap()">Refresh</button><input id=nid placeholder="waypoint id"><input id=x placeholder="x"><input id=y placeholder="y"><input id=z placeholder="z"><button onclick="node()">Add waypoint</button></div>
<div class=bar><input id=ra placeholder="from"><input id=rb placeholder="to"><button onclick="edge()">Connect</button><input id=del placeholder="node id"><button onclick="removeNode()">Delete node</button><button onclick="save()">Save map</button></div>
<pre id=r></pre></section><section class=card style="margin-top:16px"><h2>Diagnostics</h2><pre id=d>—</pre></section>
<script>
const $=id=>document.getElementById(id);let route={nodes:[],edges:[]};
async function api(u,m='GET',body){let q={method:m,headers:{'Content-Type':'application/json'}};if(body)q.body=JSON.stringify(body);let z=await fetch(u,q);let j=await z.json();if(!z.ok)throw Error(j.error||z.statusText);return j}
async function act(id,op){try{await api('/api/accounts/'+encodeURIComponent(id)+'/'+op,'POST')}catch(e){alert(e.message)}load()}
async function kill(){try{await api('/api/emergency-stop','POST')}catch(e){alert(e.message)}load()}\nasync function clearKill(){try{await api('/api/kill-switch/clear','POST')}catch(e){alert(e.message)}load()}
async function node(){try{route=await api('/api/routes/'+encodeURIComponent($('map').value)+'/nodes','POST',{id:$('nid').value,x:+$('x').value,y:+$('y').value,z:+$('z').value});renderRoute()}catch(e){alert(e.message)}}
async function edge(){try{route=await api('/api/routes/'+encodeURIComponent($('map').value)+'/edges','POST',{a:$('ra').value,b:$('rb').value});renderRoute()}catch(e){alert(e.message)}}
async function removeNode(){try{route=await api('/api/routes/'+encodeURIComponent($('map').value)+'/nodes/delete','POST',{id:$('del').value});renderRoute()}catch(e){alert(e.message)}}
async function save(){try{let j=await api('/api/routes/'+encodeURIComponent($('map').value)+'/save','POST');$('r').textContent=JSON.stringify(j,null,2)}catch(e){alert(e.message)}}
async function refreshMap(){let m=$('map').value;if(!m)return;route=await api('/api/routes/'+encodeURIComponent(m));renderRoute()}
function renderRoute(){$('r').textContent=JSON.stringify(route,null,2)}
async function createBatch(){try{let ids=[...document.querySelectorAll('input[data-account]:checked')].map(x=>x.dataset.account);if(!ids.length)return alert('Select accounts');await api('/api/farm/batches/'+encodeURIComponent($('bid').value),'POST',{action:'create',id:$('bid').value,account_ids:ids,mode:$('bmode').value});load()}catch(e){alert(e.message)}}
async function startBatch(){try{await api('/api/farm/batches/'+encodeURIComponent($('bid').value),'POST',{action:'start'});load()}catch(e){alert(e.message)}}
async function stopBatch(){try{await api('/api/farm/batches/'+encodeURIComponent($('bid').value),'POST',{action:'stop'});load()}catch(e){alert(e.message)}}
async function diag(){try{$('d').textContent=JSON.stringify(await api('/api/diagnostics'),'',2)}catch(e){$('d').textContent=e.message}}
async function load(){try{let d=await api('/api/status');$('b').innerHTML=d.batches.map(x=>'<div class=card><strong>'+x.id+'</strong><div class=big>'+x.state+'</div><div class=muted>'+x.mode+' · '+x.size+' accounts · director: '+x.match_director+'</div><div class=muted>Ready '+x.ready_players+'/'+x.expected_players+'</div></div>').join('');$('h').textContent=(d.kill_switch?'KILL SWITCH ':'')+(d.running?'RUNNING':'STOPPED');$('a').innerHTML=d.accounts.map(x=>'<div class=card><label><input type=checkbox data-account=\''+x.id+'\'> select</label><strong>'+x.name+'</strong><div class=big>'+x.state+'</div><div class=muted>Match: '+x.match+' | Round: '+(x.round??'—')+' | WalkBot: '+x.walkbot+'</div><div class=muted>PID: '+(x.process_id||'—')+' | GSI: '+(x.gsi_age==null?'—':x.gsi_age.toFixed(1)+'s')+'</div><div class=muted>Route: '+(x.route_map||'—')+' → '+(x.route_goal||'—')+'</div><button onclick="act(\''+x.id+'\',\'start\')">Start</button><button onclick="act(\''+x.id+'\',\'schedule\')">Queue</button><button onclick="act(\''+x.id+'\',\'stop\')">Stop</button><button class=danger onclick="act(\''+x.id+'\',\'kill\')">Kill WalkBot</button><select onchange="if(this.value)assign(\''+x.id+'\',this.value)"><option value="">Assign goal…</option>'+($('map').value?route.nodes.map(n=>'<option value="'+n.id+'">'+n.id+'</option>').join(''):'')+'</select></div>').join('')}catch(e){$('h').textContent='API ERROR'}}
async function assign(id,goal){try{let map=$('map').value;if(!map)return alert('Select a route map first');await api('/api/accounts/'+encodeURIComponent(id)+'/route','POST',{map,goal});load()}catch(e){alert(e.message)}}
async function init(){let maps=await api('/api/routes');$('map').innerHTML=maps.maps.map(x=>'<option>'+x+'</option>').join('');if(maps.maps.length){await refreshMap()}load();diag()}
init();setInterval(load,800);setInterval(diag,5000)</script></body></html>"""

class Dashboard:
 def __init__(self,supervisor,host="127.0.0.1",port=8765):self.s=supervisor;self.host=host;self.port=port;self.server=None
 def start(self):
  outer=self
  class H(BaseHTTPRequestHandler):
   def _body(self):
    n=int(self.headers.get("Content-Length","0") or 0)
    if n > 1024 * 1024: raise ValueError("request body too large")
    return json.loads(self.rfile.read(n) or b"{}")
   def _json(self,obj,status=200):
    b=json.dumps(obj,ensure_ascii=False).encode();self.send_response(status);self.send_header("Content-Type","application/json");self.send_header("Cache-Control","no-store");self.end_headers();self.wfile.write(b)
   def do_GET(self):
    p=unquote(urlparse(self.path).path)
    if p=="/api/status":
     now=time.monotonic()
     return self._json({"running":outer.s.running,"kill_switch":outer.s.kill_switch,"resources":outer.s.resources.snapshot(),"batches":outer.s.farm.snapshot(),"lobbies":outer.s.lobbies.snapshot(),"scheduler":outer.s.scheduler.snapshot(),"orchestrator":outer.s.orchestrator.snapshot(),"stats":outer.s.stats.snapshot(),"accounts":[{"id":a.id,"name":a.name,"state":a.fsm.state.value,"match":a.match_state().value,"round":a.match.round_number,"rounds_seen":getattr(a,"match_rounds",0),"xp":a.last_xp,"score":a.last_score,"opponent_score":a.last_opponent_score,"result":a.last_match_result,"walkbot":a.walkbot.fsm.state.value,"process_id":a.process_id,"route_map":a.route_map,"route_goal":a.route_goal,"gsi_age":None if a.walkbot.last_gsi is None else max(0,now-a.walkbot.last_gsi),"errors":a.errors[-5:],"restart_count":a.restart_count,"next_restart_at":a.next_restart_at,"started_at":a.started_at} for a in outer.s.accounts]})
    if p=="/api/farm/batches":
     return self._json({"batches":outer.s.farm.snapshot()})
    if p=="/api/routes":
     return self._json({"maps":outer.s.route_store.maps()})
    if p=="/api/accounts":
     return self._json({"accounts":[{"id":a.id,"name":a.name,"steam_id":a.steam_id or "","enabled":a.enabled,"walkbot":bool(getattr(a.walkbot,"enabled",True)),"executable":a.executable,"launch_args":list(a.launch_args)} for a in outer.s.accounts]})
    if p.startswith("/api/routes/"):
     parts=[x for x in p.split("/") if x];return self._json(outer.s.route_store.get(parts[2]).to_dict())
    if p=="/api/diagnostics":
     return self._json(as_dict(run_checks(outer.s.config.data_dir,outer.s.config.gsi_port,outer.s.config.dashboard_port)))
    b=HTML.encode();self.send_response(200);self.send_header("Content-Type","text/html; charset=utf-8");self.send_header("Cache-Control","no-store");self.end_headers();self.wfile.write(b)
   def do_POST(self):
    p=unquote(urlparse(self.path).path);parts=[x for x in p.split("/") if x]
    try:
     if parts==["api","emergency-stop"]:outer.s.emergency_stop();return self._json({"ok":True})
     if parts==["api","kill-switch","clear"]:outer.s.clear_kill_switch();return self._json({"ok":True})
     if parts==["api","routes","create"]:
      d=self._body();name=str(d.get("map","")).strip()
      if not name:return self._json({"error":"map is required"},400)
      if name in outer.s.route_store.maps():return self._json({"error":"map already exists"},409)
      from .routes import RouteGraph
      outer.s.route_store.save(name,RouteGraph())
      return self._json({"ok":True,"map":name})
     if len(parts)==4 and parts[:2]==["api","accounts"] and parts[3]=="profile":
      a=outer.s.get_account(parts[2])
      if not a:return self._json({"error":"account not found"},404)
      d=self._body()
      if "name" in d:a.name=str(d["name"]).strip() or a.name
      if "steam_id" in d:a.steam_id=str(d["steam_id"]).strip() or None
      if "enabled" in d:a.enabled=bool(d["enabled"])
      if "walkbot" in d:a.walkbot.enabled=bool(d["walkbot"])
      if "executable" in d:a.executable=str(d["executable"])
      if "launch_args" in d:
       if not isinstance(d["launch_args"],list): return self._json({"error":"launch_args must be a list"},400)
       a.launch_args=[str(x) for x in d["launch_args"]]
      outer.s.save_account_profile(a.id)
      return self._json({"ok":True})
     if len(parts)==4 and parts[:2]==["api","accounts"] and parts[3]=="delete":
      outer.s.remove_account(parts[2])
      return self._json({"ok":True})
     if len(parts)==4 and parts[:3]==["api","lobbies"]:
      lid=parts[3]; d=self._body(); action=str(d.get("action",""))
      if action=="create": result=outer.s.create_lobby(lid,[str(x) for x in d["account_ids"]])
      elif action=="ready": result=outer.s.ready_lobby(lid,str(d.get("code","")))
      elif action=="disband": result=outer.s.disband_lobby(lid)
      elif action=="shuffle": result=outer.s.shuffle_lobby(lid,[str(x) for x in d["account_ids"]])
      else:return self._json({"error":"unknown lobby action"},404)
      return self._json({"ok":True,"lobbies":outer.s.lobbies.snapshot()})
     if len(parts)==4 and parts[:3]==["api","farm","batches"]:
      batch_id=parts[3]; d=self._body()
      action=str(d.get("action",""))
      if action=="create": batch=outer.s.create_batch(str(d["id"]),[str(x) for x in d["account_ids"]],str(d.get("mode","manual")),d.get("target_xp"),bool(d.get("repeat",False)),d.get("max_matches"))
      elif action=="start": batch=outer.s.start_batch(batch_id)
      elif action=="stop": batch=outer.s.stop_batch(batch_id)
      elif action=="ready": batch=outer.s.batch_player_ready(batch_id)
      elif action=="search": batch=outer.s.batch_start_search(batch_id)
      elif action=="found": batch=outer.s.batch_match_found(batch_id,d.get("match_id"))
      else: return self._json({"error":"unknown batch action"},404)
      return self._json({"ok":True,"batches":outer.s.farm.snapshot()})
     if len(parts)==4 and parts[:2]==["api","accounts"]:
      a=outer.s.get_account(parts[2])
      if not a:return self._json({"error":"account not found"},404)
      if parts[3]=="start":outer.s.start_account(a.id)
      elif parts[3]=="schedule":outer.s.schedule_account(a.id)
      elif parts[3]=="stop":outer.s.stop_account(a.id)
      elif parts[3]=="kill":a.walkbot.emergency_stop()
      elif parts[3]=="route":
       d=self._body();outer.s.set_route_from_position(a.id,str(d["map"]),str(d["goal"]),a.walkbot.last_position or (0,0,0));outer.s.save_account_profile(a.id)
      else:return self._json({"error":"unknown action"},404)
      return self._json({"ok":True})
     if len(parts)==5 and parts[:2]==["api","routes"] and parts[3]=="nodes" and parts[4]=="delete":
      g=outer.s.route_store.get(parts[2]);g.remove(str(self._body()["id"]));return self._json(g.to_dict())
     if len(parts)==4 and parts[:2]==["api","routes"]:
      map_name=parts[2];g=outer.s.route_store.get(map_name)
      if parts[3]=="nodes":
       d=self._body();g.add(Node(str(d["id"]),float(d["x"]),float(d["y"]),float(d.get("z",0))))
      elif parts[3]=="edges":
       d=self._body();g.connect(str(d["a"]),str(d["b"]))
      elif parts[3]=="save":
       outer.s.route_store.save(map_name,g);return self._json({"ok":True,"validation":g.validate()})
      else:return self._json({"error":"unknown route action"},404)
      return self._json(g.to_dict())
     return self._json({"error":"not found"},404)
    except Exception as e:return self._json({"error":str(e)},400)
   def log_message(self,*args):pass
  self.server=ThreadingHTTPServer((self.host,self.port),H);Thread(target=self.server.serve_forever,daemon=True).start()
 def stop(self):
  if self.server:self.server.shutdown();self.server.server_close();self.server=None
