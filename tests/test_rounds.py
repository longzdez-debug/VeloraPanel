from velora.rounds import MatchTracker,RoundState
def test_overtime_round_numbers_are_not_bounded():
 m=MatchTracker();m.update("de_dust2","live",24);m.update("de_dust2","live",37)
 assert m.round_number==37 and m.state==RoundState.LIVE
