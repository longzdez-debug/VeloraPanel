from velora.rounds import MatchTracker,RoundState
def test_overtime_rounds_are_not_hardcoded():
 t=MatchTracker();assert t.update("de_dust2","live",37)==RoundState.LIVE;assert t.round_number==37
