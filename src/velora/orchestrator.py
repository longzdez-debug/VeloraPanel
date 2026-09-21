from __future__ import annotations
from dataclasses import dataclass,field
from time import monotonic
from .account_pool import FarmStatus
from .farm import BatchState
from .match_director import MatchDirectorState
from .model import AccountState,MatchState

@dataclass
class BatchRuntime:
    batch_id:str
    ready:set[str]=field(default_factory=set)
    retries:int=0
    next_retry:float=0.0
    last_state:str=""
    last_error:str|None=None

class FarmOrchestrator:
    """Closed-loop control plane joining accounts, lobbies, director, farm state and recovery."""
    def __init__(self,supervisor):
        self.s=supervisor;self.runtime={};self.max_retries=3;self.retry_delay=5.0
    def _rt(self,b): return self.runtime.setdefault(b.id,BatchRuntime(b.id))
    def _fail(self,b,message,now):
        rt=self._rt(b);rt.retries+=1;rt.last_error=message;b.errors.append(message)
        if rt.retries>self.max_retries:self.s.farm.finish_batch(b.id,False);return
        rt.next_retry=now+self.retry_delay*(2**(rt.retries-1));
        for aid in b.account_ids:
            a=self.s.get_account(aid)
            if a and a.fsm.state!=AccountState.ERROR:
                try:self.s.stop_account(aid)
                except Exception:pass
        b.state=BatchState.ERROR
    def _ready_accounts(self,b):
        return {a.id for a in (self.s.get_account(x) for x in b.account_ids) if a and a.last_gsi is not None and a.fsm.state in (AccountState.MENU,AccountState.QUEUING,AccountState.IN_MATCH)}
    def _all_live(self,b):
        return all((a:=self.s.get_account(x)) is not None and a.fsm.state==AccountState.IN_MATCH for x in b.account_ids)
    def tick(self,now=None):
        now=monotonic() if now is None else now
        for b in list(self.s.farm.batches.values()):
            rt=self._rt(b)
            if b.state in (BatchState.FINISHED,BatchState.STOPPING):continue
            if b.state==BatchState.ERROR:
                if now<rt.next_retry:continue
                if rt.retries>self.max_retries:continue
                try:
                    self.s.farm.start_batch(b.id);rt.ready.clear();b.errors.append(f"recovery attempt #{rt.retries}")
                except Exception as e:rt.next_retry=now+self.retry_delay;rt.last_error=str(e)
                continue
            accounts=[self.s.get_account(x) for x in b.account_ids]
            if any(a is None or not a.enabled for a in accounts):
                self._fail(b,"batch contains unavailable account",now);continue
            if b.state==BatchState.STARTING:
                for a in accounts:
                    if a.last_gsi is not None:rt.ready.add(a.id)
                if len(rt.ready)==b.size:self.s.farm.mark_ready(b.id)
            if b.state==BatchState.WAITING_FOR_READY:
                for a in accounts:
                    if a.id not in rt.ready and a.last_gsi is not None and a.fsm.state in (AccountState.MENU,AccountState.QUEUING,AccountState.IN_MATCH):
                        rt.ready.add(a.id);self.s.farm.player_ready(b.id)
                if b.director.state==MatchDirectorState.LOBBY_READY:
                    if b.id not in self.s.lobbies.lobbies:
                        try:self.s.create_lobby(b.id,b.account_ids)
                        except Exception:pass
                    try:self.s.ready_lobby(b.id,"orchestrated")
                    except Exception:pass
                    self.s.farm.start_search(b.id)
            if b.director.state==MatchDirectorState.SEARCHING and self._all_live(b):
                self.s.farm.match_found(b.id)
                try:b.director.start_farming()
                except RuntimeError:pass
            if b.state==BatchState.FARMING:
                if all((a:=self.s.get_account(x)) is not None and a.match_state()==MatchState.GAME_OVER for x in b.account_ids):
                    self.s.stats.record_match(b.account_ids[0])
                    b.director.finish();self.s.farm.finish_batch(b.id,True)
            rt.last_state=b.state.value
    def snapshot(self):
        return [{"batch_id":x.batch_id,"ready":sorted(x.ready),"retries":x.retries,"next_retry":x.next_retry,"last_state":x.last_state,"last_error":x.last_error} for x in self.runtime.values()]
    def load_snapshot(self,items):
        for x in items or []:
            try:self.runtime[str(x["batch_id"])]=BatchRuntime(str(x["batch_id"]),set(x.get("ready",[])),int(x.get("retries",0)),float(x.get("next_retry",0)),str(x.get("last_state","")),x.get("last_error"))
            except (KeyError,TypeError,ValueError):pass
