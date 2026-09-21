    outer.logger.debug("GET %s",p)
    if p=="/api/status":
     now=time.monotonic()
     return self._json({"running":outer.s.running,"kill_switch":outer.s.kill_switch,"resources":outer.s.resources.snapshot(),"batches":outer.s.farm.snapshot(),"lobbies":outer.s.lobbies.snapshot(),"scheduler":outer.s.scheduler.snapshot(),"orchestrator":outer.s.orchestrator.snapshot(),"stats":outer.s.stats.snapshot(),"gsi":outer.s.gsi.snapshot(),"accounts":[{"id":a.id,"name":a.name,"state":a.fsm.state.value,"match":a.match_state().value,"round":a.match.round_number,"rounds_seen":getattr(a,"match_rounds",0),"xp":a.last_xp,"score":a.last_score,"opponent_score":a.last_opponent_score,"result":a.last_match_result,"walkbot":a.walkbot.fsm.state.value,"walkbot_telemetry":a.walkbot.telemetry(),"process_id":a.process_id,"route_map":a.route_map,"route_goal":a.route_goal,"gsi_age":None if a.walkbot.last_gsi is None else max(0,now-a.walkbot.last_gsi),"errors":a.errors[-5:],"restart_count":a.restart_count,"next_restart_at":a.next_restart_at,"started_at":a.started_at,"fsm_history":outer._history(a.fsm),"match_history":outer._history(a.match),"walkbot_history":outer._history(a.walkbot.fsm)} for a in outer.s.accounts]})
    if p=="/api/events":
     try:
      from urllib.parse import parse_qs
      limit=max(1,min(200,int(parse_qs(urlparse(self.path).query).get("limit",["100"])[0])))
     except ValueError: limit=100
     with outer._event_lock: events=list(outer._events[-limit:])
     return self._json({"events":events})