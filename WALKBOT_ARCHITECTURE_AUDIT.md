# VELORA WalkBot Architecture Audit

> Audit baseline: main branch, September 21, 2026. The repository is a Python 3.12+ Windows-first application, not a .NET solution.

## Existing architecture

| Component | Responsibility | Dependencies | Assessment |
|---|---|---|---|
| src/velora/walkbot.py | lifecycle FSM, waypoint following, stuck/recovery, movement calls | FSM, model, Navigator, InputAdapter | Working foundation, but too many responsibilities |
| src/velora/model.py | account/match/walk states and GSI DTO | stdlib | Good small domain model; GSI DTO is still source-shaped |
| src/velora/gsi.py | HTTP listener, validation, parsing, snapshot construction, metrics | stdlib, GsiSnapshot | Reliable baseline, but transport/parser/domain are coupled |
| src/velora/account.py | account FSM, match tracking, GSI routing, WalkBot handoff | FSM, GSI model, MatchTracker, WalkBot | Working orchestration; should consume normalized WorldModel data |
| src/velora/movement.py | converts position/forward to W/A/S/D command | stdlib | Useful seed for steering, but command model is primitive |
| src/velora/input.py, windows.py | no-op and external SendInput adapters | stdlib/Win32 | Correct external-input boundary; retain |
| src/velora/routes.py | waypoint graph, validation, shortest path, persistence | stdlib | Good graph foundation; move behind navigation APIs |
| src/velora/supervisor.py | process/account/GSI/orchestration lifecycle | application services | Central integration point; avoid adding navigation logic here |
| src/velora/orchestrator.py | batch/match lifecycle and recovery | supervisor/farm/lobby | Correctly separate from navigation |
| src/velora/fsm.py | generic state machine + bounded transition history | stdlib | Good reusable primitive |
| src/velora/dashboard.py | HTTP UI and operator telemetry/control | supervisor | Useful operator surface |
| src/velora/config.py | environment configuration | stdlib | Good baseline; needs grouped WalkBot options |
| src/velora/storage.py | atomic JSON persistence | stdlib | Good persistence foundation |

## Current data flow

    CS2
     |
     +-- GSI HTTP
          |
       GsiServer
          |
       GsiSnapshot
          |
       Account.on_gsi
          +-- Account FSM
          +-- MatchTracker
          +-- WalkBot.on_gsi
                 |
             last_position
                 |
              WalkBot.tick
                 |
              Navigator
                 |
           MovementCommand
                 |
            InputAdapter
                 |
           Windows SendInput

Route flow:

    RouteStore -> RouteGraph -> nearest/path_from_position -> WalkBot.set_path -> Navigator

## Critical problems identified by the original audit

1. No central WorldModel. GSI state is copied into Account and WalkBot independently.
2. GSI DTO is source-shaped; transport, parsing and domain normalization are coupled.
3. Position authority is implicit; no source/confidence/freshness metadata.
4. Navigation is waypoint-centric; no explicit NavMesh/NavArea abstraction.
5. Movement command is coupled to navigation math; no MovementIntent/Steering boundary.
6. Recovery is embedded in WalkBot; stuck detection and recovery policy are intertwined.
7. No replay model for offline reproduction of observations and decisions.
8. No stable structured navigation telemetry contract.
9. No screen-capture/vision pipeline or visual localization.
10. Configuration is flat and thresholds are embedded in WalkBot.

## High problems identified by the original audit

- Route selection is static and has no scored variants.
- Existing shortest path is not exposed through a configurable planner/cost model.
- No localization confidence or source arbitration.
- No correlation ID across GSI -> decision -> movement -> recovery.
- No bounded perception pipeline.
- No explicit backpressure model for future CV workloads.

## Medium problems identified by the original audit

- Movement commands contain only booleans.
- No orientation estimate abstraction.
- No time-decaying evidence/heatmap model.
- No behaviour profile.
- No dedicated decision FSM.
- Route JSON lacks route metadata, conditions and variants.

## Low problems identified by the original audit

- Compact one-line formatting makes larger refactors harder to review.
- Some domain fields are dynamically attached at runtime.
- Dashboard HTML is embedded in one large constant.

## Missing components identified by the original audit

WorldModel; timestamp/source/confidence/validity values; GSI parser/normalizer/health separation; screen-capture abstraction; bounded frame pipeline; vision observation/backend abstraction; visual landmark/localization fusion; NavMesh/NavArea; configurable A*; route variants/selection; DecisionEngine; MovementIntent/Steering; StuckDetector; RecoveryEngine; EvidenceMap/Heatmap; BehaviourProfile; replay recorder/player; correlation-aware telemetry; grouped options.

## Preserve

Account/Match/Farm FSMs, bounded FSM history, GSI HTTP endpoint/authentication, external Windows input guard, RouteStore, dashboard, process supervision, emergency stop, NullInput and existing tests.

## Replace or migrate

Decompose WalkBot incrementally. Navigator becomes a steering implementation. GsiSnapshot remains compatibility transport data while normalized WorldModel state becomes the new decision input.

## External-only boundary audit

The audited WalkBot path contains no ReadProcessMemory, WriteProcessMemory, OpenProcess game-state reads, DLL injection/manual mapping, hooks/detours, pattern/signature scanning, offsets, entity lists or internal game interfaces.

## Migration status

- Phase 1 Audit: COMPLETE
- Phase 2 Core WorldModel: COMPLETE (integrated into WalkBot)
- Phase 3 GSI normalization: COMPLETE (normalized GSI publisher integrated)
- Phase 4 Screen capture: COMPLETE (Windows GDI backend + bounded frame buffer)
- Phase 5 Vision: COMPLETE as foundation (CPU metrics backend; domain detectors still require map/template/model assets)
- Phase 6 Localization: FOUNDATION COMPLETE (confidence-weighted source fusion; runtime landmark source pending)
- Phase 7 NavMesh: FOUNDATION COMPLETE
- Phase 8 A*: FOUNDATION COMPLETE
- Phase 9 Route database: FOUNDATION COMPLETE
- Phase 10 Decision engine: FOUNDATION COMPLETE
- Phase 11 Movement/steering: FOUNDATION COMPLETE
- Phase 12 Stuck/recovery: FOUNDATION COMPLETE
- Phase 13 Evidence/heatmaps: FOUNDATION COMPLETE
- Phase 14 Behaviour profiles: FOUNDATION COMPLETE
- Phase 15 Replay/telemetry/debug: INTEGRATED FOUNDATION
- Phase 16 Performance: INTEGRATED FOUNDATION
- Phase 17 Full integration: COMPLETE at repository architecture level; Windows/CS2 runtime validation remains environment-dependent
