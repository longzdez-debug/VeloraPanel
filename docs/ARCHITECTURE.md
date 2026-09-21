# VELORA architecture
Supervisor -> Account FSM -> Match/GSI interpretation -> WalkBot FSM -> navigation -> InputAdapter.
The UI is a client of this core, never the owner of state.
Every lifecycle action is represented by an explicit event. GSI snapshots are normalized at the boundary and duplicate payloads are ignored. Process ownership records PID, launch time and executable path. Persistence is atomic.
