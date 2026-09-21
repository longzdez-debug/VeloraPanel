# Integrated WalkBot

Pipeline: GSI -> normalized snapshot -> WalkBot FSM -> route/waypoint -> Navigator -> InputAdapter.

Safety boundary:
- default adapter performs no OS input;
- every adapter exposes release_all();
- navigation has no process/memory access;
- lifecycle is controlled by the FSM;
- stuck detection releases movement before recovery.

Any future Windows input implementation stays behind InputAdapter and must support an immediate global release/disable switch.
