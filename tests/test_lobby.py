from velora.lobby import LobbyManager,LobbyState
def test_lobby_supports_fsm_sizes():
    m=LobbyManager();a=[str(i) for i in range(10)];l=m.create("x",a);m.ready("x","abc");assert l.state==LobbyState.READY
def test_lobby_shuffle_preserves_members():
    m=LobbyManager();a=["1","2","3","4"];m.create("x",a);m.shuffle("x",["4","3","2","1"]);assert set(m.lobbies["x"].account_ids)==set(a)
