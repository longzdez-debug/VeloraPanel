from __future__ import annotations
import hashlib, hmac, json, time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from threading import Thread
from .model import GsiSnapshot

def _vec(value):
    if not isinstance(value, str):
        return None
    try:
        x = [float(v) for v in value.replace(",", " ").split()]
        return tuple(x[:3]) if len(x) >= 3 else None
    except ValueError:
        return None

class GsiServer:
    def __init__(self, host="127.0.0.1", port=27100, token=""):
        self.host, self.port, self.token = host, port, token
        self._last_key = None
        self.last_received = None
        self._server = None
        self._on_snapshot = None

    def on_snapshot(self, callback):
        self._on_snapshot = callback

    def start(self):
        outer = self
        class Handler(BaseHTTPRequestHandler):
            def do_POST(self):
                try:
                    n = int(self.headers.get("Content-Length", "0"))
                    if n <= 0 or n > 2_000_000:
                        self.send_response(400); self.end_headers(); return
                    body = self.rfile.read(n)
                except (ValueError, OSError):
                    self.send_response(400); self.end_headers(); return
                try:
                    data = json.loads(body)
                except (json.JSONDecodeError, UnicodeDecodeError):
                    self.send_response(400); self.end_headers(); return
                if not isinstance(data, dict):
                    self.send_response(400); self.end_headers(); return

                auth = data.get("auth") or {}
                supplied = auth.get("token", "") if isinstance(auth, dict) else ""
                if outer.token and not hmac.compare_digest(str(supplied), outer.token):
                    self.send_response(401); self.end_headers(); return

                provider = data.get("provider") or {}
                map_data = data.get("map") or {}
                round_data = data.get("round") or {}
                player = data.get("player") or {}
                state = player.get("state") or {}
                if not all(isinstance(x, dict) for x in (provider, map_data, round_data, player, state)):
                    self.send_response(400); self.end_headers(); return

                position = _vec(player.get("position") or state.get("position"))
                forward = _vec(player.get("forward") or player.get("forward_direction"))
                ts = provider.get("timestamp")
                key = (ts, hashlib.sha256(body).hexdigest())
                if key == outer._last_key:
                    self.send_response(204); self.end_headers(); return
                outer._last_key = key
                outer.last_received = time.monotonic()
                rn = map_data.get("round")
                try:
                    rn = int(rn) if rn is not None else None
                except (TypeError, ValueError):
                    rn = None
                steam_id = player.get("steamid") or player.get("steam_id")
                xp = None
                for source in (player, state, data.get("stats") or {}):
                    value = source.get("xp") if isinstance(source, dict) else None
                    if value is not None:
                        try:
                            xp = int(value)
                            break
                        except (TypeError, ValueError):
                            pass
                player_team = player.get("team") or state.get("team")
                if isinstance(player_team, str):
                    player_team = player_team.upper()
                team_score = opponent_score = None
                teams = {
                    "CT": map_data.get("team_ct"),
                    "T": map_data.get("team_t"),
                }
                if player_team in teams:
                    own = teams.get(player_team)
                    other = teams.get("T" if player_team == "CT" else "CT")
                    try:
                        team_score = int(own.get("score")) if isinstance(own, dict) and own.get("score") is not None else None
                    except (TypeError, ValueError):
                        team_score = None
                    try:
                        opponent_score = int(other.get("score")) if isinstance(other, dict) and other.get("score") is not None else None
                    except (TypeError, ValueError):
                        opponent_score = None
                snap = GsiSnapshot(
                    received_at=time.monotonic(),
                    provider_timestamp=ts,
                    map_name=map_data.get("name"),
                    map_phase=map_data.get("phase"),
                    round_phase=round_data.get("phase"),
                    activity=player.get("activity"),
                    health=state.get("health"),
                    steam_id=steam_id,
                    position=position,
                    forward=forward,
                    round_number=rn,
                    xp=xp,
                    player_team=player_team,
                    team_score=team_score,
                    opponent_score=opponent_score,
                    raw=data,
                )
                if outer._on_snapshot:
                    try:
                        outer._on_snapshot(snap)
                    except Exception:
                        pass
                self.send_response(204); self.end_headers()

            def log_message(self, *args):
                pass
        self._server = ThreadingHTTPServer((self.host, self.port), Handler)
        Thread(target=self._server.serve_forever, daemon=True).start()

    def stop(self):
        if self._server:
            self._server.shutdown()
            self._server.server_close()
            self._server = None
