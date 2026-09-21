from velora.input import NullInput
from velora.walkbot import WalkBot,Waypoint,WalkConfig
from velora.model import WalkState,GsiSnapshot

def boot():
 i=NullInput();w=WalkBot(i);w.start();w.fsm.dispatch("ready");w.fsm.dispatch("live");w.fsm.dispatch("spawn")
 w.last_gsi=__import__("time").monotonic()
 return i,w

def test_lifecycle():
 i=NullInput();w=WalkBot(i);w.start();w.fsm.dispatch("ready")
 w.on_gsi(GsiSnapshot(0,activity="playing",health=100,map_name="de_dust2",round_phase="live"))
 assert w.fsm.state==WalkState.NAVIGATING

def test_arrival_releases_input():
 i,w=boot();w.set_path([Waypoint("a",0,0)]);w.tick((0,0,0))
 assert i.last==(False,False,False,False)

def test_recovery_can_replan():
 i,w=boot()
 calls=[]
 w.replan=lambda p:(calls.append(p) or True)
 w.set_path([Waypoint("a",500,0)])
 w.cfg=WalkConfig(stuck_seconds=0,max_recoveries=2,recovery_seconds=0,recovery_side_seconds=0)
 w.progress_position=(0,0,0);w.last_progress=0
 w.tick((0,0,0))
 assert w.fsm.state==WalkState.RECOVERING
 w.tick((0,0,0))
 assert calls and w.fsm.state==WalkState.NAVIGATING

def test_gsi_timeout_releases():
 i,w=boot();w.set_path([Waypoint("a",500,0)])
 w.last_gsi=0;w.tick((0,0,0))
 assert i.last==(False,False,False,False)

def test_live_gsi_drives_forward_input():
 import time
 i=NullInput();w=WalkBot(i);w.start()
 w.on_gsi(GsiSnapshot(
     time.monotonic(), activity="playing", health=100, map_name="de_dust2",
     round_phase="live", position=(0,0,0), forward=(1,0,0),
 ))
 w.set_path([Waypoint("a",500,0)])
 w.tick((0,0,0))
 assert i.last==(True,False,False,False)

def test_telemetry_exposes_navigation_and_recovery_state():
 i,w=boot();w.set_path([Waypoint("a",500,0),Waypoint("b",900,0)])
 w.tick((0,0,0))
 t=w.telemetry()
 assert t["state"]=="navigating"
 assert t["target_node"]=="a"
 assert t["path_length"]==2
 assert t["position"]==[0,0,0]
 assert t["distance_to_target"]==500.0
 assert t["stuck_count"]==0

def test_telemetry_exposes_perception_state():
 i,w=boot()
 w.world.update_vision(frame_id=7,observation_count=3,confidence=0.8)
 t=w.telemetry()
 assert t["vision_frame_id"]==7
 assert t["vision_observation_count"]==3
 assert t["vision_confidence"]==0.8

def test_gsi_timeout_stops_through_movement_controller():
    i, w = boot()
    w.set_path([Waypoint("a", 500, 0)])
    calls = []
    original = w.movement_controller.stop
    w.movement_controller.stop = lambda: (calls.append(True), original())[1]
    w.last_gsi = 0
    w.tick((0, 0, 0))
    assert calls
