from velora.game_state import GameStateNormalizer
def test_gsi_normalization():
    s=GameStateNormalizer().from_gsi({"map":{"name":"de_dust2","round":17,"phase":"live"},"player":{"team":"T","state":"alive","position":[1,2,3],"velocity":{"x":4,"y":5,"z":6}}})
    assert s.map_name=="de_dust2" and s.round_number==17 and s.position.x==1 and s.velocity.z==6
