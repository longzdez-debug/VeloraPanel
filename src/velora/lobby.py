from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum

class LobbyState(str, Enum):
    IDLE="idle"; CREATING="creating"; READY="ready"; DISBANDED="disbanded"; ERROR="error"

@dataclass
class Lobby:
    id: str
    account_ids: list[str]
    state: LobbyState=LobbyState.IDLE
    code: str=""
    errors: list[str]=field(default_factory=list)

class LobbyManager:
    def __init__(self): self.lobbies={}
    def create(self,lobby_id,account_ids):
        if lobby_id in self.lobbies: raise ValueError("lobby already exists")
        if len(account_ids) not in (4,10): raise ValueError("supported lobby sizes are 4 or 10")
        l=Lobby(lobby_id,list(account_ids),LobbyState.CREATING);self.lobbies[lobby_id]=l;return l
    def ready(self,lobby_id,code=""): l=self.lobbies[lobby_id];l.code=code;l.state=LobbyState.READY;return l
    def disband(self,lobby_id): l=self.lobbies[lobby_id];l.state=LobbyState.DISBANDED;return l
    def shuffle(self,lobby_id,account_ids):
        l=self.lobbies[lobby_id]
        if set(l.account_ids)!=set(account_ids): raise ValueError("shuffle must preserve lobby members")
        l.account_ids=list(account_ids);return l
    def snapshot(self): return [{"id":l.id,"accounts":l.account_ids,"state":l.state.value,"code":l.code,"errors":l.errors[-5:]} for l in self.lobbies.values()]
