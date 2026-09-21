# VELORA WalkBot Modernization Plan

## Target architecture

GSI + Screen Capture -> normalized observations -> WorldModel -> DecisionEngine -> NavigationGoal -> PathPlanner -> MovementIntent -> Steering -> MovementController -> external input.

## Phases

1. Audit existing architecture. COMPLETE.
2. Core: WorldModel, provenance, navigation/movement contracts. COMPLETE.
3. GSI: parser, normalized GameState, WorldModel publisher, health. INTEGRATED FOUNDATION.
4. Screen Capture: IScreenCapture, metadata, bounded frame pipeline.
5. Vision: IVisionBackend, observation contracts, CPU-safe pipeline, optional GPU. FOUNDATION COMPLETE.
6. Localization: GSI + visual landmarks + prior estimate with confidence. FOUNDATION COMPLETE.
7. NavMesh: NavArea/NavEdge/NavGraph.
8. Path planning: A* with configurable cost provider.
9. Route database: metadata, conditions, variants, fallbacks, weighted selection.
10. Decision engine: goals/intents only, never input.
11. Movement: MovementIntent, steering, feedback-driven controller.
12. Stuck/recovery: extracted detector and policy engine.
13. Evidence/heatmaps: decaying evidence by navigation area.
14. Behaviour profiles: bounded deterministic variation.
15. Replay/telemetry/debug: record observations, decisions, paths and commands. INTEGRATED FOUNDATION.
16. Performance: bounded queues, throttled perception, caching and latency metrics. INTEGRATED FOUNDATION.
17. Full integration: unit, integration, replay and external runtime validation. IN PROGRESS.

## Non-negotiable boundaries

1. No memory access or internal CS2 interfaces.
2. Vision never emits keyboard input.
3. GSI never emits keyboard input.
4. Navigation never emits keyboard input.
5. Decision emits goals/intents only.
6. Only the external input adapter talks to Windows input APIs.
7. Optional GPU support is dependency-injected and never required by core.
8. No mock component may be presented as production functionality.

A phase is complete only when implementation, integration, tests, telemetry/logging and documentation are updated. Runtime-only functionality that cannot be validated without CS2 is explicitly marked as requiring external runtime validation.


## Current integration checkpoint

The WalkBot runtime now routes normal movement through DecisionEngine -> Steering/legacy navigation -> MovementController -> ExternalInput, while GSI observations are normalized into WorldModel. Recovery decisions are centralized and replayable. Vision scheduling records capture/inference/drop metrics, and an offline ReplayRunner provides deterministic inspection without external input. Dashboard telemetry exposes navigation/recovery state.

Remaining validation is limited to repository CI and Windows/CS2 runtime checks; no internal game-memory or injection mechanism is required.
