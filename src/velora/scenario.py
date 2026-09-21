from __future__ import annotations
from dataclasses import dataclass
from enum import Enum

class ScenarioState(str, Enum):
    IDLE="idle"; RUNNING="running"; COMPLETE="complete"; FAILED="failed"

@dataclass(frozen=True)
class Scenario:
    mode: str
    required_players: int
    shuffle_after_match: bool=False

SCENARIOS={
    "2v2":Scenario("2v2",4),
    "2v2_random":Scenario("2v2_random",4),
    "5v5":Scenario("5v5",10),
    "5v5_shuffle":Scenario("5v5_shuffle",10,True),
    "deathmatch":Scenario("deathmatch",1),
    "arms_race":Scenario("arms_race",1),
    "armory":Scenario("armory",1),
    "manual":Scenario("manual",1),
}

class ScenarioEngine:
    def __init__(self): self.state=ScenarioState.IDLE; self.current=None; self.match_count=0
    def load(self, mode, player_count=None):
        if mode not in SCENARIOS: raise ValueError(f"unsupported farm mode: {mode}")
        if mode == "manual" and player_count is not None:
            self.current = Scenario("manual", max(1, int(player_count)))
        else:
            self.current = SCENARIOS[mode]
        self.state=ScenarioState.IDLE
        return self.current
    def start(self):
        if not self.current: raise RuntimeError("scenario not loaded")
        self.state=ScenarioState.RUNNING
    def complete_match(self):
        if not self.current: raise RuntimeError("scenario not loaded")
        self.match_count+=1; self.state=ScenarioState.COMPLETE
        return self.current.shuffle_after_match
    def fail(self): self.state=ScenarioState.FAILED
    def reset(self): self.state=ScenarioState.IDLE
