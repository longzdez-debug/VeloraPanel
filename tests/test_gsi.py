import json
from velora.gsi import GsiServer
def test_server_constructs(): assert GsiServer(token="secret").token=="secret"


def test_gsi_rejects_malformed_json_and_invalid_token():
    import threading
    from http.client import HTTPConnection
    server = GsiServer(host="127.0.0.1", port=0, token="secret")
    # The production server binds the configured port; use an ephemeral free
    # port selected by the OS, then replace the server port before start.
    import socket
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        port = sock.getsockname()[1]
    server.port = port
    server.start()
    try:
        conn = HTTPConnection("127.0.0.1", port, timeout=2)
        conn.request("POST", "/", body=b"not-json", headers={"Content-Length":"8"})
        assert conn.getresponse().status == 400
        conn.close()

        conn = HTTPConnection("127.0.0.1", port, timeout=2)
        body = json.dumps({"auth":{"token":"wrong"}}).encode()
        conn.request("POST", "/", body=body)
        assert conn.getresponse().status == 401
        conn.close()
    finally:
        server.stop()


def test_gsi_callback_exception_does_not_break_endpoint():
    import socket
    from http.client import HTTPConnection
    server = GsiServer(host="127.0.0.1", port=0)
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        port = sock.getsockname()[1]
    server.port = port
    server.on_snapshot(lambda snap: (_ for _ in ()).throw(RuntimeError("boom")))
    server.start()
    try:
        conn = HTTPConnection("127.0.0.1", port, timeout=2)
        body = json.dumps({"provider":{"timestamp":1},"map":{"name":"de_dust2","phase":"live","round":1},"round":{"phase":"live"},"player":{"steamid":"1","activity":"playing","state":{"health":100}}}).encode()
        conn.request("POST", "/", body=body)
        assert conn.getresponse().status == 204
        conn.close()
    finally:
        server.stop()


def test_gsi_extracts_player_xp_when_present():
    import socket
    from http.client import HTTPConnection
    seen = []
    server = GsiServer(host="127.0.0.1", port=0)
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        port = sock.getsockname()[1]
    server.port = port
    server.on_snapshot(seen.append)
    server.start()
    try:
        body = json.dumps({"provider":{"timestamp":7},"map":{"name":"de_dust2","phase":"live","round":1},"round":{"phase":"live"},"player":{"steamid":"1","activity":"playing","state":{"health":100,"xp":123}}}).encode()
        conn = HTTPConnection("127.0.0.1", port, timeout=2)
        conn.request("POST", "/", body=body)
        assert conn.getresponse().status == 204
        conn.close()
        assert seen and seen[0].xp == 123
    finally:
        server.stop()


def test_gsi_extracts_explicit_team_result_data():
    import socket
    from http.client import HTTPConnection
    seen = []
    server = GsiServer(host="127.0.0.1", port=0)
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        port = sock.getsockname()[1]
    server.port = port
    server.on_snapshot(seen.append)
    server.start()
    try:
        body = json.dumps({
            "provider": {"timestamp": 8},
            "map": {
                "name": "de_dust2", "phase": "gameover", "round": 30,
                "team_ct": {"score": 16}, "team_t": {"score": 12},
            },
            "round": {"phase": "gameover"},
            "player": {
                "steamid": "1", "team": "CT", "activity": "playing",
                "state": {"health": 0},
            },
        }).encode()
        conn = HTTPConnection("127.0.0.1", port, timeout=2)
        conn.request("POST", "/", body=body)
        assert conn.getresponse().status == 204
        conn.close()
        assert seen[0].player_team == "CT"
        assert seen[0].team_score == 16
        assert seen[0].opponent_score == 12
    finally:
        server.stop()
