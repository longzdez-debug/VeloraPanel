from velora.scenario import ScenarioEngine
def test_scenarios_have_expected_team_sizes():
 e=ScenarioEngine()
 e.load("2v2"); assert e.current.required_players==4
 e.load("5v5_shuffle"); assert e.current.required_players==10 and e.current.shuffle_after_match
