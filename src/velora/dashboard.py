from __future__ import annotations
import json,os,time
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
from threading import Thread
from urllib.parse import urlparse,unquote
from .diagnostics import as_dict,run_checks
from .routes import Node
from .storage import JsonStore
from .log import get_logger

HTML="""<!doctype html><html><head><meta charset=utf-8><meta name=viewport content="width=device-width,initial-scale=1"><title>VELORA PANEL</title>
<style>
:root{--bg:#070a0f;--p:#0d1219;--p2:#111923;--line:#202b38;--txt:#edf3f8;--muted:#7e8b9b;--cyan:#55d6ff;--green:#56e39f;--red:#ff5c70;--amber:#f2bd63}
*{box-sizing:border-box}body{margin:0;background:radial-gradient(900px 450px at 75% -10%,#123244,transparent 60%),var(--bg);color:var(--txt);font:13px Inter,system-ui,sans-serif}button,input,select{font:inherit}button{border:1px solid var(--line);background:#151d27;color:var(--txt);border-radius:7px;padding:8px 11px;cursor:pointer}button:hover{border-color:#456074;background:#1a2531}.primary{background:#143445!important;border-color:#2b6178!important;color:#8ee8ff!important}.danger{background:#35151d!important;border-color:#71313d!important;color:#ff9aaa!important}input,select{background:#090e14;color:var(--txt);border:1px solid var(--line);border-radius:7px;padding:8px;outline:0}.app{min-height:100vh;display:grid;grid-template-columns:230px 1fr}.side{background:#090d13;border-right:1px solid var(--line);padding:22px 13px;display:flex;flex-direction:column}.logo{padding:0 12px 25px}.logo b{font-size:22px;letter-spacing:.16em}.logo small{display:block;color:#647285;letter-spacing:.13em;margin-top:4px}.nt{font-size:10px;color:#536171;letter-spacing:.16em;padding:13px 12px 6px}.nav button{display:block;width:100%;text-align:left;border:0;background:transparent;color:#8996a5}.nav button.active,.nav button:hover{background:#121b25;color:#eefaff}.nav button.active:before{content:"";display:inline-block;width:3px;height:14px;background:var(--cyan);border-radius:3px;margin-right:9px;vertical-align:-2px}.side-status{margin-top:auto;border:1px solid var(--line);background:#0c1219;border-radius:8px;padding:11px}.dot{display:inline-block;width:7px;height:7px;border-radius:50%;background:var(--green);box-shadow:0 0 9px var(--green);margin-right:7px}.content{min-width:0}.top{height:68px;border-bottom:1px solid var(--line);background:#090d13e8;display:flex;align-items:center;justify-content:space-between;padding:0 26px;position:sticky;top:0;z-index:3}.crumb{color:var(--muted)}.crumb b{color:var(--txt)}.actions{display:flex;gap:7px}.main{padding:25px;max-width:1550px;margin:auto}.page{display:none}.page.active{display:block}.hero{margin-bottom:18px}.eyebrow{color:var(--cyan);font-size:10px;letter-spacing:.18em}.hero h1{font-size:28px;margin:5px 0}.muted{color:var(--muted)}.cards{display:grid;grid-template-columns:repeat(4,1fr);gap:11px}.card,.panel{background:var(--p);border:1px solid var(--line);border-radius:9px}.metric{padding:15px}.metric label{display:block;color:var(--muted);font-size:10px;letter-spacing:.1em}.metric strong{display:block;font-size:27px;margin:8px 0}.panel{margin-top:13px;overflow:hidden}.ph{padding:13px 15px;border-bottom:1px solid var(--line);display:flex;justify-content:space-between;align-items:center}.ph b{font-size:12px}.pb{padding:15px}.danger-panel{border-color:#54232e}.danger-row{display:flex;align-items:center;justify-content:space-between;gap:20px}.danger-row b{color:#ff8595}.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(300px,1fr));gap:10px}.acct{background:#0f151d;border:1px solid var(--line);border-radius:8px;padding:12px}.acct-head{display:flex;align-items:center;gap:8px}.acct-name{font-weight:700;flex:1}.pill{font-size:10px;padding:4px 7px;border:1px solid #2c3947;border-radius:99px}.run{color:var(--green);border-color:#24523f}.err{color:var(--red);border-color:#61303a}.meta{display:grid;grid-template-columns:1fr 1fr;gap:6px;margin:11px 0}.meta div{background:#0a1016;border-radius:5px;padding:7px;color:var(--muted);font-size:10px}.meta b{display:block;color:var(--txt);margin-top:2px}.actions-small{display:flex;flex-wrap:wrap;gap:5px}.actions-small button{font-size:10px;padding:6px 8px}.toolbar{display:flex;gap:7px;flex-wrap:wrap}.batch{display:flex;gap:14px;align-items:center;padding:11px 0;border-bottom:1px solid #17202a}.batch:last-child{border:0}.batch-id{width:150px;font-weight:700}.grow{flex:1}.diag-grid{display:grid;grid-template-columns:1fr 1fr;gap:8px}.diag{padding:11px;border:1px solid var(--line);border-radius:7px;background:#0b1118;display:flex;justify-content:space-between}.ok{color:var(--green)}.warn{color:var(--amber)}.bad{color:var(--red)}.cyan{color:var(--cyan)}.log{font:11px/1.7 ui-monospace,Consolas,monospace;color:#aeb9c5;white-space:pre-wrap;max-height:330px;overflow:auto}.route{display:grid;grid-template-columns:220px 1fr 230px;min-height:520px}.tools,.inspect{padding:15px;background:#0b1118}.tools{border-right:1px solid var(--line)}.inspect{border-left:1px solid var(--line)}.tools button{display:block;width:100%;text-align:left;margin-bottom:6px}.canvas{position:relative;overflow:hidden;background-color:#080d13;background-image:linear-gradient(#111923 1px,transparent 1px),linear-gradient(90deg,#111923 1px,transparent 1px);background-size:32px 32px}.node{position:absolute;width:13px;height:13px;border:2px solid var(--cyan);border-radius:50%;background:#09141b}.node.sel{background:var(--cyan);box-shadow:0 0 18px #55d6ff}.center{position:absolute;inset:0;display:flex;align-items:center;justify-content:center;color:#3d4a58}@media(max-width:1000px){.app{grid-template-columns:190px 1fr}.cards{grid-template-columns:1fr 1fr}.route{grid-template-columns:180px 1fr}.inspect{display:none}}@media(max-width:700px){.app{display:block}.side{min-height:auto}.cards{grid-template-columns:1fr}.top{height:auto;padding:14px}.main{padding:14px}}
</style></head><body><div class=app>
<aside class=side><div class=logo><b>VELORA</b><small>FARM ORCHESTRATION</small></div><div class=nt>CONTROL</div><div class=nav>
<button class=active data-page=overview>◉ Dashboard</button><button data-page=accounts>Accounts</button><button data-page=batches>Batches</button><button data-page=fsm>Account FSM</button><button data-page=match>Match FSM</button><button data-page=walkbot>WalkBot</button><button data-page=gsi>GSI</button></div><div class=nt>MANAGEMENT</div><div class=nav><button data-page=routes>Route Editor</button><button data-page=diagnostics>Diagnostics</button><button data-page=logs>Logs</button></div><div class=side-status><span class=dot></span><b id=sideState>SYSTEM ONLINE</b><div class=muted>127.0.0.1 · control plane</div></div></aside>
<div class=content><header class=top><div class=crumb>VELORA / <b id=pageTitle>Dashboard</b></div><div class=actions><select id=language onchange="setLanguage(this.value)" title="Language"><option value="en">EN</option><option value="ru">RU</option></select><span id=topState class="pill run">RUNNING</span><button onclick=diag()>Diagnostics</button><button id=clearKillBtn onclick=clearKill style="display:none">CLEAR KILL SWITCH</button><button class=danger onclick=kill()>EMERGENCY STOP ALL</button></div></header><main class=main>
<section id=overview class="page active"><div class=hero><div class=eyebrow>CONTROL PLANE</div><h1>Command Center</h1><div class=muted>Account FSM · Match FSM · WalkBot · GSI · Routes</div></div><div class=cards>
<div class="card metric"><label>ACCOUNTS</label><strong id=mA>—</strong><span class=muted>registered</span></div><div class="card metric"><label>RUNNING</label><strong id=mR class=ok>—</strong><span class=muted>active accounts</span></div><div class="card metric"><label>BATCHES</label><strong id=mB class=cyan>—</strong><span class=muted>orchestration</span></div><div class="card metric"><label>WALKBOT</label><strong id=mW>—</strong><span class=muted>workers</span></div></div>
<div class="panel danger-panel"><div class=ph><b>EMERGENCY CONTROL</b><span class=bad>KILL SWITCH</span></div><div class="pb danger-row"><div><b>Emergency Stop All</b><div class=muted>Stop active batches, FSM workers and WalkBot processes.</div></div><button class=danger onclick=kill()>STOP ALL</button></div></div>
<div class=panel><div class=ph><b>ACTIVE ACCOUNTS</b><button onclick="go('accounts')">VIEW ALL →</button></div><div id=ovAccounts class="pb grid"></div></div></section>

<section id=accounts class=page><div class=hero><div class=eyebrow>CONTROL</div><h1>Accounts</h1><div class=muted>Select accounts and create an orchestration batch.</div></div><div class=panel><div class=pb><div class=toolbar><input id=bid placeholder="batch id"><select id=bmode><option value=manual>Manual</option><option value=2v2>2v2</option><option value=2v2_random>2v2 Random</option><option value=5v5>5v5</option><option value=5v5_shuffle>5v5 Shuffle</option><option value=deathmatch>Deathmatch</option><option value=arms_race>Arms Race</option><option value=armory>Armory</option></select><button class=primary onclick=createBatch>CREATE BATCH FROM SELECTED</button><button onclick=startBatch>START BATCH</button><button onclick=stopBatch>STOP BATCH</button></div></div></div><div id=accountsList class="grid" style="margin-top:13px"></div></section>

<section id=batches class=page><div class=hero><div class=eyebrow>ORCHESTRATION</div><h1>Batches</h1></div><div class=panel><div class=pb id=batchList></div></div></section>

<section id=routes class=page><div class=hero><div class=eyebrow>NAVIGATION</div><h1>Route Editor</h1></div><div class=panel><div class=ph><div class=toolbar><select id=map></select><button onclick=refreshMap>REFRESH</button><button onclick=newMap>+ NEW MAP</button></div><span id=routeInfo class=muted>—</span></div><div class=route><div class=tools><div class=eyebrow>TOOLS</div><button onclick="focusTool('add')">＋ Add waypoint</button><button onclick="focusTool('connect')">↔ Connect</button><button onclick="focusTool('delete')">× Delete node</button><button onclick=save>↓ Save map</button><hr style="border:0;border-top:1px solid var(--line);margin:15px 0"><input id=nid placeholder="node id"><input id=x placeholder=x><input id=y placeholder=y><input id=z placeholder=z><button class=primary onclick=node>ADD NODE</button></div><div id=canvas class=canvas><div class=center>ROUTE GRAPH</div></div><div class=inspect><div class=eyebrow>NODE INSPECTOR</div><div id=inspector class=muted style="margin:12px 0">Select a node.</div><input id=ra placeholder=from style="width:100%;margin:5px 0"><input id=rb placeholder=to style="width:100%;margin:5px 0"><button onclick=edge style="width:100%">CONNECT NODES</button><input id=del placeholder="node id" style="width:100%;margin:15px 0 5px"><button class=danger onclick=removeNode style="width:100%">DELETE NODE</button></div></div></div></section>

<section id=diagnostics class=page><div class=hero><div class=eyebrow>SYSTEM</div><h1>Diagnostics</h1></div><button class=primary onclick=diag>RUN DIAGNOSTICS</button><div id=diagGrid class=diag-grid style="margin-top:13px"></div><div class=panel><div class=ph><b>RAW OUTPUT</b><button onclick=clearDiag>CLEAR</button></div><div class=pb><div id=diagRaw class=log>—</div></div></div></section>
<section id=logs class=page><div class=hero><div class=eyebrow>SYSTEM</div><h1>Logs</h1></div><div class=panel><div class=pb><div id=logsBox class=log>Waiting…</div></div></div></section>
<section id=fsm class=page><div class=hero><div class=eyebrow>STATE MACHINE</div><h1>Account FSM</h1></div><div class=panel><div class=pb id=fsmBox></div></div></section>
<section id=match class=page><div class=hero><div class=eyebrow>STATE MACHINE</div><h1>Match FSM</h1></div><div class=panel><div class=pb id=matchBox></div></div></section>
<section id=walkbot class=page><div class=hero><div class=eyebrow>AUTOMATION</div><h1>WalkBot</h1></div><div class=panel><div class=pb id=walkBox></div></div></section>
<section id=gsi class=page><div class=hero><div class=eyebrow>TELEMETRY</div><h1>GSI</h1></div><div class=panel><div class=pb id=gsiBox></div></div></section>
</main></div></div>
<script>
const $=id=>document.getElementById(id);let route={nodes:[],edges:[]};
async function api(u,m='GET',body){const q={method:m,headers:{'Content-Type':'application/json'}};if(body)q.body=JSON.stringify(body);const r=await fetch(u,q),j=await r.json();if(!r.ok)throw Error(j.error||r.statusText);return j}
const I18N={ru:{'Dashboard':'Панель','Accounts':'Аккаунты','Batches':'Батчи','Account FSM':'FSM аккаунтов','Match FSM':'FSM матчей','Route Editor':'Редактор маршрутов','Diagnostics':'Диагностика','Logs':'Логи','CONTROL':'УПРАВЛЕНИЕ','MANAGEMENT':'УПРАВЛЕНИЕ','SYSTEM ONLINE':'СИСТЕМА В СЕТИ','SYSTEM STOPPED':'СИСТЕМА ОСТАНОВЛЕНА','KILL SWITCH ACTIVE':'KILL SWITCH АКТИВЕН','RUNNING':'РАБОТАЕТ','STOPPED':'ОСТАНОВЛЕНО','CLEAR KILL SWITCH':'СБРОСИТЬ KILL SWITCH','EMERGENCY STOP ALL':'АВАРИЙНАЯ ОСТАНОВКА','CONTROL PLANE':'ЦЕНТР УПРАВЛЕНИЯ','Command Center':'Командный центр','ACCOUNTS':'АККАУНТЫ','registered':'зарегистрировано','active accounts':'активные аккаунты','BATCHES':'БАТЧИ','orchestration':'оркестрация','WALKBOT':'WALKBOT','workers':'воркеры','EMERGENCY CONTROL':'АВАРИЙНОЕ УПРАВЛЕНИЕ','STOP ALL':'ОСТАНОВИТЬ ВСЕ','ACTIVE ACCOUNTS':'АКТИВНЫЕ АККАУНТЫ','VIEW ALL →':'ПОКАЗАТЬ ВСЕ →','No accounts.':'Нет аккаунтов.','Select accounts and create an orchestration batch.':'Выберите аккаунты и создайте батч.','CREATE BATCH FROM SELECTED':'СОЗДАТЬ БАТЧ ИЗ ВЫБРАННЫХ','START BATCH':'ЗАПУСТИТЬ БАТЧ','STOP BATCH':'ОСТАНОВИТЬ БАТЧ','ORCHESTRATION':'ОРКЕСТРАЦИЯ','No batches.':'Нет батчей.','NAVIGATION':'НАВИГАЦИЯ','REFRESH':'ОБНОВИТЬ','+ NEW MAP':'+ НОВАЯ КАРТА','TOOLS':'ИНСТРУМЕНТЫ','＋ Add waypoint':'＋ ДОБАВИТЬ ТОЧКУ','↔ Connect':'↔ СОЕДИНИТЬ','× Delete node':'× УДАЛИТЬ УЗЕЛ','↓ Save map':'↓ СОХРАНИТЬ КАРТУ','NODE INSPECTOR':'ИНСПЕКТОР УЗЛА','Select a node.':'Выберите узел.','CONNECT NODES':'СОЕДИНИТЬ УЗЛЫ','DELETE NODE':'УДАЛИТЬ УЗЕЛ','SYSTEM':'СИСТЕМА','RUN DIAGNOSTICS':'ЗАПУСТИТЬ ДИАГНОСТИКУ','RAW OUTPUT':'СЫРОЙ ВЫВОД','CLEAR':'ОЧИСТИТЬ','AUTOMATION':'АВТОМАТИЗАЦИЯ','TELEMETRY':'ТЕЛЕМЕТРИЯ','Waiting…':'Ожидание…','No recent account errors.':'Нет последних ошибок аккаунтов.','No data.':'Нет данных.','OFFLINE':'ОФЛАЙН','MATCH':'МАТЧ','PID':'PID','START':'ЗАПУСК','QUEUE':'В ОЧЕРЕДЬ','STOP':'СТОП','KILL BOT':'ОСТАНОВИТЬ БОТА','DELETE':'УДАЛИТЬ','RECOVER':'ВОССТАНОВИТЬ','Manual':'Ручной','2v2 Random':'2v2 случайный','5v5 Shuffle':'5v5 перемешивание','Deathmatch':'Deathmatch','Arms Race':'Arms Race','Armory':'Armory','Language':'Язык'}};
function applyLanguage(lang){document.documentElement.lang=lang;document.querySelectorAll('#language option').forEach(o=>o.selected=o.value===lang);if(lang==='en')return;const map=I18N[lang]||{};const walk=n=>n.childNodes.forEach(ch=>{if(ch.nodeType===3){const raw=ch.nodeValue.trim();if(map[raw])ch.nodeValue=ch.nodeValue.replace(raw,map[raw])}else if(ch.nodeType===1&&ch.id!=='language')walk(ch)});walk(document.body)}
async function setLanguage(lang){if(!['en','ru'].includes(lang))return;try{await api('/api/settings/language','POST',{language:lang});location.reload()}catch(e){alert(e.message)}}
function go(p){document.querySelectorAll('.page').forEach(x=>x.classList.toggle('active',x.id===p));document.querySelectorAll('.nav button').forEach(x=>x.classList.toggle('active',x.dataset.page===p));$('pageTitle').textContent=p[0].toUpperCase()+p.slice(1)}
document.querySelectorAll('.nav button').forEach(x=>x.onclick=()=>go(x.dataset.page));
async function kill(){try{await api('/api/emergency-stop','POST')}catch(e){alert(e.message)}load()}
async function act(id,op){try{await api('/api/accounts/'+encodeURIComponent(id)+'/'+op,'POST')}catch(e){alert(e.message)}load()}
async function removeAccount(id){if(!confirm('Delete account '+id+'?'))return;try{await api('/api/accounts/'+encodeURIComponent(id)+'/delete','POST');load()}catch(e){alert(e.message)}}
function card(x){return '<div class=acct><div class=acct-head><input type=checkbox data-account="'+x.id+'"><span class=acct-name>'+x.name+'</span><span class="pill '+(String(x.state).toLowerCase().includes('error')?'err':'run')+'">'+x.state+'</span></div><div class=meta><div>MATCH<b>'+x.match+'</b></div><div>WALKBOT<b>'+x.walkbot+'</b></div><div>GSI<b>'+(x.gsi_age==null?'—':x.gsi_age.toFixed(1)+'s')+'</b></div><div>PID<b>'+(x.process_id||'—')+'</b></div></div><div class=muted style="font-size:10px;margin-bottom:8px">Route: '+(x.route_map||'—')+' → '+(x.route_goal||'—')+'</div><div class=actions-small><button onclick="act(\''+x.id+'\',\'start\')">START</button><button onclick="act(\''+x.id+'\',\'schedule\')">QUEUE</button><button onclick="act(\''+x.id+'\',\'stop\')">STOP</button><button class=danger onclick="act(\''+x.id+'\',\'kill\')">KILL BOT</button><button class=danger onclick="removeAccount(\''+x.id+'\')">DELETE</button></div></div>'}
async function createBatch(){try{const ids=[...document.querySelectorAll('input[data-account]:checked')].map(x=>x.dataset.account);if(!ids.length)throw Error('Select accounts');if(!$('bid').value.trim())throw Error('Batch id is required');await api('/api/farm/batches/'+encodeURIComponent($('bid').value),'POST',{action:'create',id:$('bid').value,account_ids:ids,mode:$('bmode').value});load()}catch(e){alert(e.message)}}
async function startBatch(){try{await api('/api/farm/batches/'+encodeURIComponent($('bid').value),'POST',{action:'start'});load()}catch(e){alert(e.message)}}
async function stopBatch(){try{await api('/api/farm/batches/'+encodeURIComponent($('bid').value),'POST',{action:'stop'});load()}catch(e){alert(e.message)}}
async function batchAct(id,a){try{await api('/api/farm/batches/'+encodeURIComponent(id),'POST',{action:a});load()}catch(e){alert(e.message)}}
async function refreshMaps(){const m=await api('/api/routes');$('map').innerHTML=m.maps.map(x=>'<option>'+x+'</option>').join('')}
async function newMap(){const n=prompt('Map name');if(!n)return;try{await api('/api/routes/create','POST',{map:n});await refreshMaps();$('map').value=n;refreshMap()}catch(e){alert(e.message)}}
async function refreshMap(){if(!$('map').value)return;route=await api('/api/routes/'+encodeURIComponent($('map').value));renderRoute()}
function renderRoute(){const c=$('canvas');c.innerHTML='<div class=center>ROUTE GRAPH / '+route.nodes.length+' NODES · '+route.edges.length+' EDGES</div>';const pos=new Map();route.nodes.forEach((n,i)=>pos.set(n.id,{x:12+(i*41)%78,y:15+(i*59)%72}));const svg=document.createElementNS('http://www.w3.org/2000/svg','svg');svg.setAttribute('width','100%');svg.setAttribute('height','100%');svg.style.position='absolute';svg.style.inset='0';svg.style.pointerEvents='none';route.edges.forEach(e=>{const p=pos.get(e[0]),q=pos.get(e[1]);if(!p||!q)return;const line=document.createElementNS('http://www.w3.org/2000/svg','line');line.setAttribute('x1',p.x+'%');line.setAttribute('y1',p.y+'%');line.setAttribute('x2',q.x+'%');line.setAttribute('y2',q.y+'%');line.setAttribute('stroke','#365061');line.setAttribute('stroke-width','2');svg.appendChild(line)});c.appendChild(svg);route.nodes.forEach(n=>{const e=document.createElement('button');const p=pos.get(n.id);e.className='node';e.style.left=p.x+'%';e.style.top=p.y+'%';e.title=n.id;e.onclick=()=>{document.querySelectorAll('.node').forEach(x=>x.classList.remove('sel'));e.classList.add('sel');$('inspector').innerHTML='<b>'+n.id+'</b><br><br>X '+n.x+'<br>Y '+n.y+'<br>Z '+n.z+'<br><br>CONNECTED: '+route.edges.filter(x=>x[0]===n.id||x[1]===n.id).length;$('del').value=n.id;$('nid').value=n.id;$('x').value=n.x;$('y').value=n.y;$('z').value=n.z};c.appendChild(e)});$('routeInfo').textContent=route.nodes.length+' nodes · '+route.edges.length+' edges'}
async function node(){try{route=await api('/api/routes/'+encodeURIComponent($('map').value)+'/nodes','POST',{id:$('nid').value,x:+$('x').value,y:+$('y').value,z:+$('z').value});renderRoute()}catch(e){alert(e.message)}}
async function edge(){try{route=await api('/api/routes/'+encodeURIComponent($('map').value)+'/edges','POST',{a:$('ra').value,b:$('rb').value});renderRoute()}catch(e){alert(e.message)}}
async function removeNode(){try{route=await api('/api/routes/'+encodeURIComponent($('map').value)+'/nodes/delete','POST',{id:$('del').value});renderRoute()}catch(e){alert(e.message)}}
async function save(){try{const j=await api('/api/routes/'+encodeURIComponent($('map').value)+'/save','POST');$('routeInfo').textContent='SAVED · '+(j.validation?.length||0)+' validation issues'}catch(e){alert(e.message)}}
function focusTool(t){$(t==='add'?'nid':t==='connect'?'ra':'del').focus()}
function clearDiag(){$('diagRaw').textContent='—';$('diagGrid').innerHTML=''}
async function diag(){try{const d=await api('/api/diagnostics');$('diagRaw').textContent=JSON.stringify(d,null,2);const checks=Array.isArray(d)?d:[];$('diagGrid').innerHTML=checks.map(v=>'<div class=diag><div><b>'+v.name.replaceAll('_',' ').toUpperCase()+'</b><div class=muted>'+v.detail+'</div></div><span class="'+(v.ok?'ok':'bad')+'">● '+(v.ok?'PASS':'FAIL')+'</span></div>').join('')||'<div class=muted>No diagnostic data.</div>';applyLanguage($('language').value)}catch(e){$('diagRaw').textContent=e.message;$('diagGrid').innerHTML='<div class="diag"><span class=bad>● FAIL</span><span>'+e.message+'</span></div>'}}
function views(d){const a=d.accounts||[],b=d.batches||[];$('mA').textContent=a.length;$('mR').textContent=a.filter(x=>String(x.state).toLowerCase().includes('run')).length;$('mB').textContent=b.length;$('mW').textContent=a.filter(x=>String(x.walkbot).toLowerCase().includes('run')||String(x.walkbot).toLowerCase().includes('active')).length;$('topState').textContent=d.kill_switch?'KILL SWITCH':d.running?'RUNNING':'STOPPED';$('topState').className='pill '+(d.kill_switch?'err':'run');$('sideState').textContent=d.kill_switch?'KILL SWITCH ACTIVE':d.running?'SYSTEM ONLINE':'SYSTEM STOPPED';$('clearKillBtn').style.display=d.kill_switch?'inline-block':'none';$('ovAccounts').innerHTML=a.slice(0,8).map(card).join('')||'<div class=muted>No accounts.</div>';$('accountsList').innerHTML=a.map(card).join('')||'<div class=muted>No accounts.</div>';$('batchList').innerHTML=b.map(x=>'<div class=batch><b class=batch-id>'+x.id+'</b><div class=grow><b>'+x.state+'</b><div class=muted>'+x.mode+' · '+x.size+' accounts · '+x.ready_players+'/'+x.expected_players+' ready</div></div><button onclick="batchAct(\''+x.id+'\',\'recover\')">RECOVER</button><button class=danger onclick="batchAct(\''+x.id+'\',\'stop\')">STOP</button></div>').join('')||'<div class=muted>No batches.</div>';[['fsmBox','state'],['matchBox','match'],['walkBox','walkbot'],['gsiBox','gsi_age']].forEach(([id,k])=>$(id).innerHTML=a.map(x=>'<div class=diag><b>'+x.name+'</b><span class=cyan>'+ (k==='gsi_age'?(x[k]==null?'OFFLINE':x[k].toFixed(1)+'s ago'):x[k])+'</span></div>').join('')||'<div class=muted>No data.</div>');$('logsBox').textContent=a.flatMap(x=>(x.errors||[]).map(e=>x.name+'  '+e)).join('\n')||'No recent account errors.'}
async function clearKill(){try{await api('/api/kill-switch/clear','POST');load()}catch(e){alert(e.message)}}
async function load(){try{views(await api('/api/status'))}catch(e){$('topState').textContent='API ERROR';$('topState').className='pill err'}}
async function loadLanguage(){try{const j=await api('/api/settings/language');const saved=j.language||'en';$('language').value=saved;applyLanguage(saved)}catch(e){console.error(e)}}
async function loadLogs(){try{const j=await api('/api/logs?lines=500');$('logsBox').textContent=j.content||'No logs.'}catch(e){$('logsBox').textContent='LOG API ERROR: '+e.message}}
async function init(){try{await refreshMaps();if($('map').options.length)await refreshMap()}catch(e){}await loadLanguage();load();diag();loadLogs()}init();setInterval(load,1500);setInterval(diag,7000);setInterval(loadLogs,3000)
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
