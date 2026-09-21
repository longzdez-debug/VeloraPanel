from __future__ import annotations
import json,os,time
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
from threading import Thread
from urllib.parse import urlparse,unquote
from .diagnostics import as_dict,run_checks
from .routes import Node
from .storage import JsonStore
from .log import get_logger

HTML="""<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>VELORA PANEL</title><style>
:root{--bg:#07090d;--s:#0d1219;--s2:#111923;--line:#202b38;--txt:#edf4fa;--muted:#788696;--cyan:#62ddff;--green:#55e6a3;--red:#ff6178;--amber:#f5c36b}*{box-sizing:border-box}body{margin:0;background:radial-gradient(900px 500px at 70% -10%,#12394b55,transparent 60%),var(--bg);color:var(--txt);font:13px Inter,system-ui,sans-serif}button,input,select{font:inherit}button{border:1px solid var(--line);background:#151d27;color:var(--txt);border-radius:8px;padding:8px 11px;cursor:pointer;transition:.15s}button:hover{border-color:#456174;transform:translateY(-1px)}.primary{background:#123b4c!important;border-color:#2b6c84!important;color:#9deaff!important}.danger{background:#35151d!important;border-color:#71313d!important;color:#ff9aaa!important}input,select{background:#090e14;color:var(--txt);border:1px solid var(--line);border-radius:8px;padding:9px;outline:0}input:focus,select:focus{border-color:#36718a}.app{min-height:100vh;display:grid;grid-template-columns:245px 1fr}.side{position:sticky;top:0;height:100vh;background:#090d13ee;border-right:1px solid var(--line);padding:22px 13px;display:flex;flex-direction:column;backdrop-filter:blur(16px)}.brand{display:flex;align-items:center;gap:10px;padding:0 10px 25px}.mark{width:34px;height:34px;border:1px solid #2e728b;border-radius:10px;display:grid;place-items:center;color:var(--cyan);background:#102631;font-weight:900}.brand b{font-size:19px;letter-spacing:.15em}.brand small{display:block;color:#607080;font-size:9px;letter-spacing:.13em;margin-top:3px}.label{color:#536273;font-size:9px;letter-spacing:.18em;padding:13px 11px 7px}.nav{display:grid;gap:3px}.nav button{border:0;background:transparent;color:#8997a7;text-align:left;width:100%;padding:10px 11px}.nav button:hover{background:#101721;color:#eaf7fd}.nav button.active{background:#111d28;color:#effbff;box-shadow:inset 2px 0 var(--cyan)}.ico{display:inline-block;width:24px;color:#68798a}.active .ico{color:var(--cyan)}.sidefoot{margin-top:auto;border:1px solid var(--line);background:#0c1219;border-radius:11px;padding:12px}.pulse{width:7px;height:7px;border-radius:50%;display:inline-block;background:var(--green);box-shadow:0 0 11px var(--green);margin-right:7px}.sidefoot small{display:block;color:var(--muted);margin-top:7px}.main{min-width:0}.top{height:70px;border-bottom:1px solid var(--line);background:#090d13df;backdrop-filter:blur(16px);display:flex;align-items:center;justify-content:space-between;padding:0 28px;position:sticky;top:0;z-index:5}.crumb{color:var(--muted)}.crumb b{color:var(--txt)}.topactions{display:flex;align-items:center;gap:7px}.chip{display:inline-flex;align-items:center;padding:7px 10px;border:1px solid #28543f;border-radius:999px;color:var(--green);font-size:9px;font-weight:800}.chip.bad{color:var(--red);border-color:#63313a}.content{padding:28px;max-width:1650px;margin:auto}.page{display:none}.page.active{display:block}.hero{display:flex;justify-content:space-between;align-items:end;gap:15px;margin:3px 0 22px}.eyebrow{color:var(--cyan);font-size:9px;font-weight:800;letter-spacing:.2em}.hero h1{font-size:30px;letter-spacing:-.04em;margin:5px 0}.muted{color:var(--muted)}.hero p{margin:0;color:var(--muted)}.actions{display:flex;gap:7px;flex-wrap:wrap}.metrics{display:grid;grid-template-columns:repeat(4,1fr);gap:12px}.metric,.panel{background:#0d1219ee;border:1px solid var(--line);border-radius:13px}.metric{padding:17px;position:relative;overflow:hidden}.metric:after{content:"";position:absolute;right:-35px;top:-35px;width:100px;height:100px;border-radius:50%;background:#62ddff0b}.metric label{display:block;color:#718091;font-size:9px;letter-spacing:.13em;font-weight:800}.metric strong{display:block;font-size:30px;margin:8px 0 4px}.metric small{color:var(--muted)}.grid2{display:grid;grid-template-columns:1.5fr .9fr;gap:13px;margin-top:13px}.panel{overflow:hidden}.ph{min-height:52px;padding:12px 15px;border-bottom:1px solid var(--line);display:flex;justify-content:space-between;align-items:center;gap:10px}.ph b{font-size:11px;letter-spacing:.06em}.ph small{color:var(--muted);display:block;margin-top:3px}.pb{padding:15px}.danger-panel{border-color:#542733;background:#30111955}.danger-row{display:flex;justify-content:space-between;align-items:center;gap:15px}.danger-row b{color:#ff9aaa}.danger-row p{margin:4px 0 0;color:var(--muted);font-size:11px}.health{display:grid;grid-template-columns:1fr 1fr;gap:8px}.health div{border:1px solid var(--line);background:#0b1016;border-radius:9px;padding:10px}.health small{display:block;color:var(--muted);font-size:9px}.health b{display:block;margin-top:6px;font-size:11px}.ok{color:var(--green)}.bad{color:var(--red)}.warn{color:var(--amber)}.accounts{display:grid;gap:7px}.acct{display:grid;grid-template-columns:1.4fr 110px 100px 100px auto;gap:10px;align-items:center;padding:10px;border:1px solid #1b2530;border-radius:10px;background:#0d131b}.acctmain{display:flex;align-items:center;gap:9px;min-width:0}.avatar{width:30px;height:30px;border-radius:9px;background:#122331;border:1px solid #234456;color:var(--cyan);display:grid;place-items:center;font-size:10px;font-weight:800}.acctmain b{display:block;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}.acctmain small{color:var(--muted);font-size:9px}.state{width:max-content;padding:4px 7px;border:1px solid #2b3947;border-radius:999px;font-size:9px;font-weight:800}.actions-sm{display:flex;gap:4px;justify-content:end}.actions-sm button{padding:6px 8px;font-size:9px}.cell{font-size:9px;color:var(--muted)}.cell b{display:block;color:var(--txt);font-size:10px;margin-top:3px}.toolbar{display:flex;gap:7px;flex-wrap:wrap;align-items:center}.toolbar .search{min-width:220px}.batch{display:grid;grid-template-columns:170px 1fr 100px 120px auto;gap:10px;align-items:center;padding:12px 0;border-bottom:1px solid #18212b}.batch:last-child{border:0}.progress{height:5px;background:#18212b;border-radius:9px;overflow:hidden;margin-top:6px}.progress i{display:block;height:100%;background:linear-gradient(90deg,#1e9dcc,var(--cyan))}.fsm{display:grid;grid-template-columns:repeat(5,1fr);gap:9px}.fsm div{border:1px solid var(--line);background:#0b1118;border-radius:11px;padding:14px;min-height:82px}.fsm b{display:block;margin-top:9px}.table{width:100%;border-collapse:collapse}.table th{color:#667688;font-size:9px;text-align:left;padding:9px;border-bottom:1px solid var(--line)}.table td{padding:10px 9px;border-bottom:1px solid #17202a;font-size:10px;color:#aab7c4}.table td b{color:var(--txt)}.route{display:grid;grid-template-columns:205px 1fr 240px;min-height:570px}.tools,.inspect{padding:14px;background:#0b1016}.tools{border-right:1px solid var(--line)}.inspect{border-left:1px solid var(--line)}.tools button{display:block;width:100%;text-align:left;margin-bottom:6px}.canvas{position:relative;overflow:hidden;background-color:#080d13;background-image:linear-gradient(#121a23 1px,transparent 1px),linear-gradient(90deg,#121a23 1px,transparent 1px);background-size:32px 32px}.node{position:absolute;width:15px;height:15px;border:2px solid var(--cyan);border-radius:50%;background:#09141b;padding:0;z-index:2}.node.sel,.node:hover{background:var(--cyan);box-shadow:0 0 18px #62ddff99}.field{display:grid;gap:6px}.field label{color:var(--muted);font-size:9px}.field input{width:100%}.log{font:11px/1.7 ui-monospace,Consolas,monospace;color:#b8c4cf;white-space:pre-wrap;max-height:560px;overflow:auto}.toastbox{position:fixed;right:22px;bottom:22px;z-index:20;display:grid;gap:8px}.toast{min-width:250px;padding:12px 14px;background:#111820;border:1px solid var(--line);border-radius:10px;box-shadow:0 18px 60px #0008;font-size:11px}.modal{position:fixed;inset:0;background:#0009;display:none;place-items:center;z-index:30}.modal.open{display:grid}.modal>div{width:min(500px,calc(100vw - 30px));background:#0e141c;border:1px solid #2b3948;border-radius:14px;padding:18px}.modal p{color:var(--muted);font-size:11px}.modal-actions{display:flex;justify-content:end;gap:7px}@media(max-width:1150px){.grid2{grid-template-columns:1fr}.acct{grid-template-columns:1.4fr 100px 100px auto}.hide-md{display:none}.route{grid-template-columns:180px 1fr}.inspect{display:none}}@media(max-width:850px){.app{display:block}.side{position:relative;height:auto;border-right:0;border-bottom:1px solid var(--line)}.label,.sidefoot{display:none}.nav{grid-template-columns:repeat(4,1fr)}.top{position:relative}.metrics{grid-template-columns:1fr 1fr}.content{padding:16px}.route{grid-template-columns:1fr}.tools{border:0;border-bottom:1px solid var(--line)}.canvas{height:450px}}@media(max-width:580px){.metrics{grid-template-columns:1fr}.hero{display:block}.actions{margin-top:12px}.nav{grid-template-columns:1fr 1fr}.acct,.batch{grid-template-columns:1fr}.actions-sm{justify-content:start}.topactions .chip,.topactions button:not(.icon){display:none}.fsm{grid-template-columns:1fr 1fr}}
</style></head><body>
<div class=app><aside class=side><div class=brand><div class=mark>V</div><div><b>VELORA</b><small>FARM CONTROL CENTER</small></div></div><div class=label>CONTROL</div><nav class=nav>
<button class=active data-page=overview><span class=ico>◉</span>Dashboard</button><button data-page=accounts><span class=ico>◎</span>Accounts</button><button data-page=batches><span class=ico>▦</span>Batches</button><button data-page=fsm><span class=ico>◇</span>Account FSM</button><button data-page=match><span class=ico>◆</span>Match FSM</button><button data-page=walkbot><span class=ico>⌁</span>WalkBot</button><button data-page=gsi><span class=ico>⌁</span>GSI</button></nav><div class=label>MANAGEMENT</div><nav class=nav><button data-page=routes><span class=ico>⌖</span>Route Editor</button><button data-page=diagnostics><span class=ico>✓</span>Diagnostics</button><button data-page=logs><span class=ico>≡</span>Logs</button></nav><div class=sidefoot><span class=pulse></span><b id=sideState>SYSTEM ONLINE</b><small>127.0.0.1 · local control plane</small></div></aside>
<div class=main><header class=top><div class=crumb>VELORA / <b id=pageTitle>Dashboard</b></div><div class=topactions><span id=topState class=chip><span class=pulse></span>RUNNING</span><select id=language onchange=setLanguage(this.value) title=Language><option value="en">EN</option><option value="ru">RU</option></select><button class=icon onclick=refreshAll title=Refresh>↻</button><button id=clearKillBtn onclick=clearKill style=display:none>CLEAR KILL SWITCH</button><button class=danger onclick="confirmAction('Emergency Stop','Stop all active batches, FSM workers and WalkBot processes?',kill)">EMERGENCY STOP</button></div></header><main class=content>
<section id=overview class="page active"><div class=hero><div><div class=eyebrow>CONTROL PLANE</div><h1>Command Center</h1><p>Real-time account orchestration, FSM, matches, WalkBot and telemetry.</p></div><div class=actions><button onclick=diag>RUN DIAGNOSTICS</button><button class=primary onclick="go('accounts')">MANAGE ACCOUNTS →</button></div></div>
<div class=metrics><div class=metric><label>ACCOUNTS</label><strong id=mA>—</strong><small>registered accounts</small></div><div class=metric><label>RUNNING</label><strong id=mR>—</strong><small>active account workers</small></div><div class=metric><label>BATCHES</label><strong id=mB>—</strong><small>orchestration jobs</small></div><div class=metric><label>WALKBOT</label><strong id=mW>—</strong><small>active workers</small></div></div>
<div class="panel danger-panel" style="margin-top:13px"><div class=ph><div><b>EMERGENCY CONTROL</b><small>Global kill switch and recovery controls</small></div><span class="state bad">● KILL SWITCH</span></div><div class="pb danger-row"><div><b>Emergency Stop All</b><p>Immediately stop active batches and automation workers.</p></div><button class=danger onclick="confirmAction('Emergency Stop','Stop all active batches, FSM workers and WalkBot processes?',kill)">STOP ALL</button></div></div>
<div class=grid2><div class=panel><div class=ph><div><b>ACTIVE ACCOUNTS</b><small>Live supervisor snapshot</small></div><button onclick="go('accounts')">VIEW ALL →</button></div><div class=pb><div id=ovAccounts class=accounts></div></div></div><div class=panel><div class=ph><div><b>SYSTEM HEALTH</b><small>Latest diagnostics</small></div><button onclick=diag>CHECK</button></div><div class=pb><div id=healthGrid class=health></div></div></div></div></section>
<section id=accounts class=page><div class=hero><div><div class=eyebrow>CONTROL</div><h1>Accounts</h1><p>Manage account workers, routes and process lifecycle.</p></div><div class=actions><button onclick=refreshAll>↻ Refresh</button></div></div><div class=panel><div class=ph><div class=toolbar><input class=search id=accountSearch oninput="renderAccounts(lastStatus?.accounts||[])"><select id=accountFilter onchange="renderAccounts(lastStatus?.accounts||[])"><option value=all>All states</option><option value=running>Running</option><option value=error>Error</option><option value=stopped>Stopped</option></select></div><div class=toolbar><input id=bid placeholder="batch id"><select id=bmode><option value=manual>Manual</option><option value=2v2>2v2</option><option value=2v2_random>2v2 Random</option><option value=5v5>5v5</option><option value=5v5_shuffle>5v5 Shuffle</option><option value=deathmatch>Deathmatch</option><option value=arms_race>Arms Race</option><option value=armory>Armory</option></select><button class=primary onclick=createBatch>CREATE BATCH</button></div></div><div class=pb><div id=accountsList class=accounts></div></div></div></section>
<section id=batches class=page><div class=hero><div><div class=eyebrow>ORCHESTRATION</div><h1>Batches</h1><p>Match jobs, readiness and recovery state.</p></div></div><div class=panel><div class=pb><div id=batchList></div></div></div></section>
<section id=fsm class=page><div class=hero><div><div class=eyebrow>STATE MACHINE</div><h1>Account FSM</h1><p>Live account lifecycle states across all workers.</p></div></div><div class=panel><div class=ph><b>ACCOUNT LIFECYCLE</b><small>Live snapshot</small></div><div class=pb><div id=fsmBoard class=fsm></div></div></div><div class="panel" style="margin-top:13px"><div class=ph><b>STATE TABLE</b></div><div class=pb><table class=table><thead><tr><th>ACCOUNT</th><th>STATE</th><th>RESTARTS</th><th>PID</th><th>STARTED</th></tr></thead><tbody id=fsmTable></tbody></table></div></div></section>
<section id=match class=page><div class=hero><div><div class=eyebrow>STATE MACHINE</div><h1>Match FSM</h1><p>Match search, gameplay and result telemetry.</p></div></div><div class=panel><div class=pb><div id=matchBoard class=accounts></div></div></div></section>
<section id=walkbot class=page><div class=hero><div><div class=eyebrow>AUTOMATION</div><h1>WalkBot</h1><p>Navigation state, route target and telemetry age.</p></div></div><div class=panel><div class=pb><div id=walkBoard class=accounts></div></div></div></section>
<section id=gsi class=page><div class=hero><div><div class=eyebrow>TELEMETRY</div><h1>Game State Integration</h1><p>Connection age and process telemetry for every account.</p></div></div><div class=metrics id=gsiMetrics></div><div class=panel style="margin-top:13px"><div class=pb><table class=table><thead><tr><th>ACCOUNT</th><th>GSI AGE</th><th>PID</th><th>ROUND</th><th>SCORE</th><th>OPPONENT</th></tr></thead><tbody id=gsiTable></tbody></table></div></div></section>
<section id=routes class=page><div class=hero><div><div class=eyebrow>NAVIGATION</div><h1>Route Editor</h1><p>Build and validate WalkBot navigation graphs.</p></div><div class=actions><select id=map></select><button onclick=refreshMap>REFRESH</button><button class=primary onclick=newMap>+ NEW MAP</button></div></div><div class=panel><div class=ph><div><b>ROUTE GRAPH</b><small id=routeInfo>—</small></div><button onclick=save>SAVE MAP</button></div><div class=route><div class=tools><div class=eyebrow style="margin-bottom:10px">TOOLS</div><button onclick="focusTool('add')">＋ Add waypoint</button><button onclick="focusTool('connect')">↔ Connect nodes</button><button onclick="focusTool('delete')">× Delete node</button><hr style="border:0;border-top:1px solid var(--line);margin:14px 0"><div class=field><label>NODE ID</label><input id=nid placeholder=spawn_a><label>X / Y / Z</label><div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:5px"><input id=x placeholder=X><input id=y placeholder=Y><input id=z placeholder=Z></div><button class=primary onclick=node>ADD / UPDATE NODE</button></div></div><div id=canvas class=canvas><div style="position:absolute;inset:0;display:grid;place-items:center;color:#3f4d5b;font-size:10px;letter-spacing:.12em">ROUTE GRAPH</div></div><div class=inspect><div class=eyebrow>NODE INSPECTOR</div><div id=inspector class=muted style="margin:12px 0 18px">Select a node.</div><div class=field><label>CONNECT FROM</label><input id=ra placeholder=node_a><label>CONNECT TO</label><input id=rb placeholder=node_b><button onclick=edge>CONNECT</button><label style="margin-top:9px">DELETE NODE</label><input id=del placeholder="node id"><button class=danger onclick=removeNode>DELETE NODE</button></div></div></div></div></section>
<section id=diagnostics class=page><div class=hero><div><div class=eyebrow>SYSTEM</div><h1>Diagnostics</h1><p>Runtime, Steam, CS2, ports and data directory checks.</p></div><button class=primary onclick=diag>RUN DIAGNOSTICS</button></div><div id=diagGrid class=health></div><div class=panel style="margin-top:13px"><div class=ph><b>RAW OUTPUT</b><button onclick=clearDiag>CLEAR</button></div><div class=pb><div id=diagRaw class=log>—</div></div></div></section>
<section id=logs class=page><div class=hero><div><div class=eyebrow>SYSTEM</div><h1>Logs</h1><p>Runtime log stream for diagnosis.</p></div><button onclick=loadLogs>↻ Refresh</button></div><div class=panel><div class=ph><b>VELORA.LOG</b><small id=logMeta>—</small></div><div class=pb><div id=logsBox class=log>Waiting…</div></div></div></section>
</main></div></div><div id=modal class=modal><div><h3 id=modalTitle>Confirm</h3><p id=modalText></p><div class=modal-actions><button onclick=closeModal>CANCEL</button><button id=modalOk class=danger>CONFIRM</button></div></div></div><div id=toastbox class=toastbox></div>
<script>
window.addEventListener('error',function(e){try{fetch('/api/client-error',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({message:e.message||'Script load error',source:e.filename||'',line:e.lineno||0,column:e.colno||0})})}catch(_){}});
window.addEventListener('unhandledrejection',function(e){try{fetch('/api/client-error',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({message:e.reason&&e.reason.stack||String(e.reason||'Unhandled rejection')})})}catch(_){}});
fetch('/api/client-error',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({message:'CLIENT BOOT SCRIPT REACHED'})}).catch(function(){});
</script><script>
const $=id=>document.getElementById(id);let route={nodes:[],edges:[]},lastStatus=null,lastDiag=null;
function clientError(message,source='',line=0,column=0){try{fetch('/api/client-error',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({message:String(message||'Unknown client error'),source:String(source||''),line:Number(line)||0,column:Number(column)||0})})}catch(_){}}
window.addEventListener('error',e=>clientError(e.message,e.filename,e.lineno,e.colno));
window.addEventListener('unhandledrejection',e=>clientError(e.reason?.stack||e.reason?.message||String(e.reason||'Unhandled rejection')));
async function api(u,m='GET',body){const q={method:m,headers:{'Content-Type':'application/json'}};if(body!==undefined)q.body=JSON.stringify(body);const r=await fetch(u,q);let j={};try{j=await r.json()}catch{}if(!r.ok)throw Error(j.error||r.statusText||'Request failed');return j}
function esc(v){return String(v??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]))}function jsesc(v){return String(v??'').replace(/\\\\/g,'\\\\\\\\').replace(/'/g,"\\'")}
function toast(t,bad=false){const e=document.createElement('div');e.className='toast';e.textContent=t;if(bad)e.style.borderColor='#71313d';$('toastbox').appendChild(e);setTimeout(()=>e.remove(),3500)}
function confirmAction(t,p,fn){$('modalTitle').textContent=t;$('modalText').textContent=p;$('modal').classList.add('open');$('modalOk').onclick=async()=>{closeModal();await fn()}}function closeModal(){$('modal').classList.remove('open')}
function go(p){document.querySelectorAll('.page').forEach(x=>x.classList.toggle('active',x.id===p));document.querySelectorAll('.nav button').forEach(x=>x.classList.toggle('active',x.dataset.page===p));const b=document.querySelector('.nav button[data-page="'+p+'"]');$('pageTitle').textContent=b?b.textContent.trim():p}
document.querySelectorAll('.nav button').forEach(x=>x.onclick=()=>go(x.dataset.page));
const I18N={ru:{'Dashboard':'Панель','Accounts':'Аккаунты','Batches':'Батчи','Account FSM':'FSM аккаунтов','Match FSM':'FSM матчей','WalkBot':'WalkBot','GSI':'GSI','Route Editor':'Редактор маршрутов','Diagnostics':'Диагностика','Logs':'Логи','CONTROL':'УПРАВЛЕНИЕ','MANAGEMENT':'УПРАВЛЕНИЕ','Command Center':'Командный центр','ACTIVE ACCOUNTS':'АКТИВНЫЕ АККАУНТЫ','SYSTEM HEALTH':'СОСТОЯНИЕ СИСТЕМЫ','EMERGENCY CONTROL':'АВАРИЙНОЕ УПРАВЛЕНИЕ','STOP ALL':'ОСТАНОВИТЬ ВСЕ','EMERGENCY STOP':'АВАРИЙНАЯ ОСТАНОВКА','RUNNING':'РАБОТАЕТ','SYSTEM ONLINE':'СИСТЕМА В СЕТИ','SYSTEM STOPPED':'СИСТЕМА ОСТАНОВЛЕНА','CLEAR KILL SWITCH':'СБРОСИТЬ KILL SWITCH','CREATE BATCH':'СОЗДАТЬ БАТЧ','REFRESH':'ОБНОВИТЬ','SAVE MAP':'СОХРАНИТЬ КАРТУ','RUN DIAGNOSTICS':'ЗАПУСТИТЬ ДИАГНОСТИКУ','RAW OUTPUT':'СЫРОЙ ВЫВОД','CANCEL':'ОТМЕНА','CONFIRM':'ПОДТВЕРДИТЬ','START':'ЗАПУСК','STOP':'СТОП','KILL':'УБИТЬ','RECOVER':'ВОССТАНОВИТЬ','No accounts.':'Нет аккаунтов.','No batches.':'Нет батчей.','Language':'Язык'}};function applyLanguage(lang){if(lang!=='ru')return;const map=I18N.ru;const walk=n=>{n.childNodes.forEach(ch=>{if(ch.nodeType===3){const t=ch.nodeValue.trim();if(map[t])ch.nodeValue=ch.nodeValue.replace(t,map[t])}else if(ch.nodeType===1&&ch.id!=='language')walk(ch)})};walk(document.body)}
async function setLanguage(lang){try{await api('/api/settings/language','POST',{language:lang});location.reload()}catch(e){toast(e.message,true)}}
async function kill(){try{await api('/api/emergency-stop','POST');toast('Emergency stop requested')}catch(e){toast(e.message,true)}await load()}
async function clearKill(){try{await api('/api/kill-switch/clear','POST');toast('Kill switch cleared');await load()}catch(e){toast(e.message,true)}}
function stateClass(v){const s=String(v||'').toLowerCase();return s.includes('error')||s.includes('fail')?'bad':s.includes('run')||s.includes('active')?'ok':s.includes('wait')||s.includes('sched')?'warn':''}
function initials(v){return String(v||'?').split(/\s+/).map(x=>x[0]).join('').slice(0,2).toUpperCase()}
function accountRow(x,check=false){return '<div class=acct><div class=acctmain>'+(check?'<input type=checkbox data-account="'+esc(x.id)+'">':'')+'<div class=avatar>'+initials(x.name)+'</div><div><b>'+esc(x.name)+'</b><small>'+esc(x.id)+'</small></div></div><span class="state '+stateClass(x.state)+'">● '+esc(x.state)+'</span><div class="cell hide-md">MATCH<b>'+esc(x.match)+'</b></div><div class="cell hide-md">WALKBOT<b>'+esc(x.walkbot)+'</b></div><div class=actions-sm><button onclick="act(this.dataset.id,'start')" data-id="'+esc(x.id)+'">START</button><button onclick="act(this.dataset.id,'stop')" data-id="'+esc(x.id)+'">STOP</button><button class=danger onclick="act(this.dataset.id,'kill')" data-id="'+esc(x.id)+'">KILL</button></div></div>'}
function renderAccounts(a){const q=($('accountSearch')?.value||'').toLowerCase(),f=$('accountFilter')?.value||'all';const list=a.filter(x=>(!q||String(x.name).toLowerCase().includes(q)||String(x.id).toLowerCase().includes(q))&&(f==='all'||stateClass(x.state)===({'running':'ok','error':'bad','stopped':''}[f])));$('accountsList').innerHTML=list.map(x=>accountRow(x,true)).join('')||'<div class=muted>No accounts.</div>'}
function views(d){lastStatus=d;const a=d.accounts||[],b=d.batches||[];$('mA').textContent=a.length;$('mR').textContent=a.filter(x=>stateClass(x.state)==='ok').length;$('mB').textContent=b.length;$('mW').textContent=a.filter(x=>stateClass(x.walkbot)==='ok').length;const ks=!!d.kill_switch;$('topState').innerHTML='<span class=pulse></span>'+(ks?'KILL SWITCH':'RUNNING');$('topState').className='chip '+(ks?'bad':'');$('sideState').textContent=ks?'KILL SWITCH ACTIVE':d.running?'SYSTEM ONLINE':'SYSTEM STOPPED';$('clearKillBtn').style.display=ks?'inline-block':'none';$('ovAccounts').innerHTML=a.slice(0,8).map(x=>accountRow(x)).join('')||'<div class=muted>No accounts.</div>';renderAccounts(a);renderBatches(b);renderFSM(a);renderMatch(a);renderWalk(a);renderGsi(a)}
function renderBatches(b){$('batchList').innerHTML=b.map(x=>{const p=x.expected_players?Math.min(100,Math.round((x.ready_players||0)/x.expected_players*100)):0;return '<div class=batch><div><b>'+esc(x.id)+'</b><div class=muted>'+esc(x.mode)+'</div></div><div><b>'+esc(x.state)+'</b><div class=progress><i style="width:'+p+'%"></i></div></div><div class=cell>'+x.size+' accounts</div><div class=cell>'+(x.ready_players||0)+' / '+(x.expected_players||0)+' ready</div><div class=actions-sm><button onclick="batchAct(this.dataset.id,'recover')" data-id="'+esc(x.id)+'">RECOVER</button><button class=danger onclick="batchAct(this.dataset.id,'stop')" data-id="'+esc(x.id)+'">STOP</button></div></div>'}).join('')||'<div class=muted>No batches.</div>'}
function renderFSM(a){const g={};a.forEach(x=>g[x.state]=(g[x.state]||0)+1);$('fsmBoard').innerHTML=Object.entries(g).map(([k,v])=>'<div><small class=muted>ACCOUNT STATE</small><b>'+esc(k)+'</b><small class=muted>'+v+' account(s)</small></div>').join('')||'<div class=muted>No states.</div>';$('fsmTable').innerHTML=a.map(x=>'<tr><td><b>'+esc(x.name)+'</b></td><td>'+esc(x.state)+'</td><td>'+x.restart_count+'</td><td>'+esc(x.process_id||'—')+'</td><td>'+esc(x.started_at||'—')+'</td></tr>').join('')}
function renderMatch(a){$('matchBoard').innerHTML=a.map(x=>'<div class=acct><div class=acctmain><div class=avatar>'+initials(x.name)+'</div><div><b>'+esc(x.name)+'</b><small>'+esc(x.id)+'</small></div></div><span class="state '+stateClass(x.match)+'">● '+esc(x.match)+'</span><div class=cell>ROUND<b>'+x.round+'</b></div><div class=cell>SCORE<b>'+x.score+' : '+x.opponent_score+'</b></div><div class=cell>RESULT<b>'+esc(x.result||'—')+'</b></div></div>').join('')||'<div class=muted>No match data.</div>'}
function renderWalk(a){$('walkBoard').innerHTML=a.map(x=>'<div class=acct><div class=acctmain><div class=avatar>'+initials(x.name)+'</div><div><b>'+esc(x.name)+'</b><small>'+esc(x.id)+'</small></div></div><span class="state '+stateClass(x.walkbot)+'">● '+esc(x.walkbot)+'</span><div class=cell>ROUTE<b>'+esc(x.route_map||'—')+'</b></div><div class=cell>GOAL<b>'+esc(x.route_goal||'—')+'</b></div><div class=cell>GSI<b>'+((x.gsi_age==null)?'OFFLINE':x.gsi_age.toFixed(1)+'s')+'</b></div><div class=actions-sm><button class=danger onclick="act(this.dataset.id,'kill')" data-id="'+esc(x.id)+'">KILL</button></div></div>').join('')||'<div class=muted>No WalkBot workers.</div>'}
function renderGsi(a){const on=a.filter(x=>x.gsi_age!=null&&x.gsi_age<10).length;$('gsiMetrics').innerHTML='<div class=metric><label>GSI ONLINE</label><strong>'+on+'</strong><small>telemetry streams</small></div><div class=metric><label>GSI OFFLINE</label><strong>'+(a.length-on)+'</strong><small>no recent event</small></div><div class=metric><label>PROCESS PIDS</label><strong>'+a.filter(x=>x.process_id).length+'</strong><small>active process handles</small></div><div class=metric><label>ROUND EVENTS</label><strong>'+a.reduce((n,x)=>n+(x.rounds_seen||0),0)+'</strong><small>observed rounds</small></div>';$('gsiTable').innerHTML=a.map(x=>'<tr><td><b>'+esc(x.name)+'</b></td><td class="'+(x.gsi_age!=null&&x.gsi_age<10?'ok':'bad')+'">'+(x.gsi_age==null?'OFFLINE':x.gsi_age.toFixed(1)+'s')+'</td><td>'+esc(x.process_id||'—')+'</td><td>'+x.round+'</td><td>'+x.score+'</td><td>'+x.opponent_score+'</td></tr>').join('')}
async function load(){try{views(await api('/api/status'))}catch(e){$('topState').textContent='API ERROR';$('topState').className='chip bad';toast('Status API: '+e.message,true)}}
async function diag(){try{lastDiag=await api('/api/diagnostics');$('diagRaw').textContent=JSON.stringify(lastDiag,null,2);const rows=Array.isArray(lastDiag)?lastDiag:Object.entries(lastDiag||{}).map(([name,v])=>({name,ok:!!(v&&v.ok),detail:v&&v.detail||String(v??'')}));$('diagGrid').innerHTML=rows.map(v=>'<div><small>'+esc(String(v.name||'CHECK').replaceAll('_',' ').toUpperCase())+'</small><b class="'+(v.ok?'ok':'bad')+'">'+(v.ok?'● PASS':'● FAIL')+'</b><small style="display:block;margin-top:5px">'+esc(v.detail||'')+'</small></div>').join('')||'<div class=muted>No diagnostic data.</div>';$('healthGrid').innerHTML=$('diagGrid').innerHTML}catch(e){$('diagRaw').textContent=e.message;clientError(e.stack||e.message)}}
function clearDiag(){$('diagRaw').textContent='—';$('diagGrid').innerHTML=''}
async function loadLogs(){try{const j=await api('/api/logs?lines=500');$('logsBox').textContent=j.content||'No logs.';$('logMeta').textContent=(j.lines||500)+' lines · '+(j.path||'')}catch(e){$('logsBox').textContent='LOG API ERROR: '+e.message}}
async function act(id,op){try{await api('/api/accounts/'+encodeURIComponent(id)+'/'+op,'POST');toast(op.toUpperCase()+' requested');await load()}catch(e){toast(e.message,true)}}
async function batchAct(id,a){try{await api('/api/farm/batches/'+encodeURIComponent(id),'POST',{action:a});toast(a.toUpperCase()+' requested');await load()}catch(e){toast(e.message,true)}}
async function createBatch(){try{const ids=[...document.querySelectorAll('input[data-account]:checked')].map(x=>x.dataset.account),id=$('bid').value.trim();if(!ids.length)throw Error('Select accounts first');if(!id)throw Error('Batch id is required');await api('/api/farm/batches/'+encodeURIComponent(id),'POST',{action:'create',id,account_ids:ids,mode:$('bmode').value});toast('Batch created');await load()}catch(e){toast(e.message,true)}}
async function refreshMaps(){const m=await api('/api/routes');$('map').innerHTML=(m.maps||[]).map(x=>'<option value="'+esc(x)+'">'+esc(x)+'</option>').join('')}
async function refreshMap(){if(!$('map').value)return;route=await api('/api/routes/'+encodeURIComponent($('map').value));renderRoute()}
async function newMap(){const n=prompt('Map name');if(!n?.trim())return;try{await api('/api/routes/create','POST',{map:n.trim()});await refreshMaps();$('map').value=n.trim();await refreshMap();toast('Map created')}catch(e){toast(e.message,true)}}
function renderRoute(){const c=$('canvas');c.innerHTML='';const pos=new Map();route.nodes.forEach((n,i)=>{const a=i/Math.max(1,route.nodes.length)*Math.PI*2;pos.set(n.id,{x:50+36*Math.cos(a),y:50+36*Math.sin(a)})});const svg=document.createElementNS('http://www.w3.org/2000/svg','svg');svg.setAttribute('width','100%');svg.setAttribute('height','100%');svg.style.cssText='position:absolute;inset:0';route.edges.forEach(e=>{const p=pos.get(e[0]),q=pos.get(e[1]);if(!p||!q)return;const l=document.createElementNS('http://www.w3.org/2000/svg','line');l.setAttribute('x1',p.x+'%');l.setAttribute('y1',p.y+'%');l.setAttribute('x2',q.x+'%');l.setAttribute('y2',q.y+'%');l.setAttribute('stroke','#365061');l.setAttribute('stroke-width','2');svg.appendChild(l)});c.appendChild(svg);if(!route.nodes.length)c.innerHTML='<div style="position:absolute;inset:0;display:grid;place-items:center;color:#3f4d5b">NO NODES · ADD WAYPOINT</div>';route.nodes.forEach(n=>{const e=document.createElement('button'),p=pos.get(n.id);e.className='node';e.style.left='calc('+p.x+'% - 7px)';e.style.top='calc('+p.y+'% - 7px)';e.title=n.id;e.onclick=()=>{document.querySelectorAll('.node').forEach(x=>x.classList.remove('sel'));e.classList.add('sel');$('inspector').innerHTML='<b>'+esc(n.id)+'</b><br><br>X '+n.x+'<br>Y '+n.y+'<br>Z '+n.z+'<br><br>CONNECTED: '+route.edges.filter(x=>x[0]===n.id||x[1]===n.id).length;$('del').value=n.id;$('nid').value=n.id;$('x').value=n.x;$('y').value=n.y;$('z').value=n.z};c.appendChild(e)});$('routeInfo').textContent=route.nodes.length+' nodes · '+route.edges.length+' edges'}
async function node(){try{route=await api('/api/routes/'+encodeURIComponent($('map').value)+'/nodes','POST',{id:$('nid').value,x:+$('x').value,y:+$('y').value,z:+$('z').value});renderRoute();toast('Node saved')}catch(e){toast(e.message,true)}}
async function edge(){try{route=await api('/api/routes/'+encodeURIComponent($('map').value)+'/edges','POST',{a:$('ra').value,b:$('rb').value});renderRoute();toast('Edge connected')}catch(e){toast(e.message,true)}}
async function removeNode(){try{route=await api('/api/routes/'+encodeURIComponent($('map').value)+'/nodes/delete','POST',{id:$('del').value});renderRoute();toast('Node deleted')}catch(e){toast(e.message,true)}}
async function save(){try{const j=await api('/api/routes/'+encodeURIComponent($('map').value)+'/save','POST');toast('Map saved'+(j.validation?.length?' · validation issues':''),!!j.validation?.length)}catch(e){toast(e.message,true)}}
function focusTool(t){$(t==='add'?'nid':t==='connect'?'ra':'del').focus()}
async function refreshAll(){await load();await diag();await loadLogs()}
async function loadLanguage(){try{const lang=(await api('/api/settings/language')).language||'en';$('language').value=lang;applyLanguage(lang)}catch{}}
async function init(){await loadLanguage();await load();await diag();await loadLogs();try{await refreshMaps();if($('map').options.length)await refreshMap()}catch(e){toast('Route API: '+e.message,true)}}
document.querySelectorAll('.nav button').forEach(x=>x.onclick=()=>go(x.dataset.page));init();setInterval(load,1500);setInterval(diag,7000);setInterval(loadLogs,3000);
</script></body></html>"""


def _as_bool(value, field):
 if isinstance(value, bool):
  return value
 if isinstance(value, str):
  normalized=value.strip().lower()
  if normalized in {"1","true","yes","on"}: return True
  if normalized in {"0","false","no","off"}: return False
 raise ValueError(f"{field} must be a boolean")

class Dashboard:
 def __init__(self,supervisor,host="127.0.0.1",port=8765):
  self.s=supervisor;self.host=host;self.port=port;self.server=None
  self.logger=get_logger("dashboard")
  self.settings=JsonStore(os.path.join(self.s.config.data_dir,"settings.json"))
  saved=self.settings.load({"language":"en"})
  self.language=saved.get("language","en") if isinstance(saved,dict) else "en"
  if self.language not in {"en","ru"}: self.language="en"
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
    outer.logger.debug("GET %s",p)
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
     outer.logger.info("diagnostics requested")
     return self._json(as_dict(run_checks(outer.s.config.data_dir,outer.s.config.gsi_port,outer.s.config.dashboard_port)))
    if p=="/api/settings/language":
     return self._json({"language":outer.language,"supported":["en","ru"]})
    if p=="/api/logs":
     from urllib.parse import parse_qs
     try: lines=max(1,min(5000,int(parse_qs(urlparse(self.path).query).get("lines",["500"])[0])))
     except ValueError: lines=500
     path=os.path.join(outer.s.config.data_dir,"velora.log")
     try:
      with open(path,encoding="utf-8",errors="replace") as f: content="".join(f.readlines()[-lines:])
     except FileNotFoundError: content=""
     return self._json({"path":path,"lines":lines,"content":content})
    b=HTML.encode();self.send_response(200);self.send_header("Content-Type","text/html; charset=utf-8");self.send_header("Cache-Control","no-store");self.end_headers();self.wfile.write(b)
   def do_POST(self):
    p=unquote(urlparse(self.path).path);parts=[x for x in p.split("/") if x]
    try:
     if parts==["api","client-error"]:
      d=self._body();outer.logger.error("CLIENT ERROR message=%s source=%s line=%s column=%s",str(d.get("message","")),str(d.get("source","")),d.get("line",0),d.get("column",0));return self._json({"ok":True})
     if parts==["api","emergency-stop"]:outer.logger.warning("EMERGENCY STOP requested");outer.s.emergency_stop();return self._json({"ok":True})
     if parts==["api","kill-switch","clear"]:outer.logger.warning("KILL SWITCH clear requested");outer.s.clear_kill_switch();return self._json({"ok":True})
     if parts==["api","settings","language"]:
      d=self._body();lang=str(d.get("language","en")).lower()
      if lang not in {"en","ru"}: return self._json({"error":"unsupported language"},400)
      outer.language=lang;outer.settings.save({"language":lang});outer.logger.info("language changed to %s",lang)
      return self._json({"ok":True,"language":lang})
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
      if "enabled" in d:a.enabled=_as_bool(d["enabled"],"enabled")
      if "walkbot" in d:a.walkbot.enabled=_as_bool(d["walkbot"],"walkbot")
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
      elif action=="recover": batch=outer.s.recover_batch(batch_id)
      elif action=="delete": outer.s.delete_batch(batch_id); batch=None
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
    except Exception as e:
     outer.logger.exception("HTTP request failed: %s %s",self.command,self.path)
     return self._json({"error":str(e)},400)
   def log_message(self,*args):outer.logger.debug("HTTP %s"," ".join(str(x) for x in args))
  self.server=ThreadingHTTPServer((self.host,self.port),H);Thread(target=self.server.serve_forever,daemon=True).start()
 def stop(self):
  if self.server:self.server.shutdown();self.server.server_close();self.server=None
