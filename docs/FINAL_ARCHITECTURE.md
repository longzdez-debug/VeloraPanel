# VELORA final architecture

VELORA is split into control-plane and game-plane boundaries.

Control plane: Dashboard -> Supervisor -> Account profiles -> Process ownership.
Game plane: CS2 GSI -> normalized snapshot -> Match FSM -> WalkBot FSM -> RouteGraph -> Navigator -> InputAdapter.

Persistent state is JSON with atomic replace. Secrets are environment/local configuration only and are never committed.

A production deployment should keep NullInput as the default and explicitly enable WindowsInput only after a user-controlled safety switch is present.