from velora.input import NullInput
from velora.walkbot import WalkBot,Waypoint
from velora.model import WalkState,GsiSnapshot
def test_lifecycle():
 i=NullInput();w=WalkBot(i);w.start();assert w.fsm.state==WalkState.INITIALIZING;w.fsm.dispatch("ready");w.on_gsi(GsiSnapshot(0,activity="playing"));assert w.fsm.state==WalkState.WAITING_FOR_SPAWN
def test_arrival_releases_input():
 i=NullInput();w=WalkBot(i);w.start();w.fsm.dispatch("ready");w.fsm.dispatch("live");w.fsm.dispatch("spawn");w.set_path([Waypoint("a",0,0)]);w.tick((0,0,0));assert i.last==(False,False,False,False)
