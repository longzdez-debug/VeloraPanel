# WALKBOT Modernization Phase Status

| Phase | Status | Evidence |
|---|---|---|
| 1 Audit | COMPLETE | WALKBOT_ARCHITECTURE_AUDIT.md |
| 2 WorldModel/Core | COMPLETE | world.py, movement_intent.py, options.py |
| 3 GSI normalization | COMPLETE | gsi_normalizer.py, WalkBot integration |
| 4 Screen capture | COMPLETE | screen.py: bounded buffer + Windows GDI capture |
| 5 Vision | INTEGRATED FOUNDATION | vision.py: real CPU frame metrics + backend boundary |
| 6 Localization | FOUNDATION COMPLETE | localization.py + WorldModel provenance |
| 7 NavMesh | FOUNDATION COMPLETE | navigation.py NavArea/NavEdge/NavGraph |
| 8 A* | FOUNDATION COMPLETE | NavGraph.astar with configurable edge cost |
| 9 Route DB | FOUNDATION COMPLETE | route_database.py variants/weights/fallback |
| 10 Decision Engine | FOUNDATION COMPLETE | decision.py emits goals/actions only |
| 11 Movement | FOUNDATION COMPLETE | MovementIntent + Steering + MovementController |
| 12 Stuck/Recovery | FOUNDATION COMPLETE | stuck.py + recovery.py |
| 13 Evidence/Heatmaps | FOUNDATION COMPLETE | evidence.py with exponential decay |
| 14 Behaviour | FOUNDATION COMPLETE | deterministic bounded BehaviourSampler |
| 15 Replay/Telemetry | INTEGRATED FOUNDATION | replay.py + replay_runner.py + telemetry.py + WalkBot replay hooks |
| 16 Performance | INTEGRATED FOUNDATION | bounded frame pipeline + scheduler drop/capture/vision metrics |
| 17 Full integration | IN PROGRESS | GSI health, WorldModel, navigation/recovery, replay and movement boundaries integrated; Windows runtime/CI verification remains |

## What is deliberately not claimed as complete

- Visual landmark/object detection is not claimed without real map assets/models.
- GPU backends are not claimed without an actual optional backend implementation.
- Full Decision -> Navigation -> Steering -> Input runtime wiring is not claimed until the legacy WalkBot path is migrated and regression-tested.
- CS2 runtime validation is not claimed from repository inspection alone.
- Tests are maintained in-repo and CI is triggered on pushes; runtime/build verification remains Windows-environment dependent.

## External-only guarantee

The modernization keeps the external boundary. No memory reader, injection, hook, offset/signature scanner or internal CS2 API was added.


## Latest integration checkpoint
- External input boundary is now isolated in `external_input.py`; the NullInput test adapter no longer imports WalkBot.
- WalkBot movement now passes through DecisionEngine -> Steering/legacy fallback -> MovementController -> ExternalInput.
- Legacy waypoint paths remain supported without requiring a navigation graph.
- Architecture guard test rejects forbidden process-memory/injection primitives in `src/velora`.
- GitHub Actions CI was triggered by the latest commits; final runtime/build verification remains Windows-environment dependent.
