# Integrated WalkBot

Pipeline: GSI -> normalized snapshot -> WalkBot FSM -> route/waypoint -> Navigator -> InputAdapter.

Safety boundary:
- default adapter performs no OS input;
- Windows input is explicitly opt-in;
- Windows input is allowed only for an owned CS2 process and, by default, only while that process owns the foreground window;
- every adapter exposes release_all();
- GSI timeout, player death/not-playing, process death, stop and emergency-stop release movement;
- navigation has no process/memory access;
- lifecycle is controlled by the FSM;
- stuck detection releases movement before bounded recovery.

The input layer intentionally sends only W/A/S/D. It does not read CS2 memory, inject DLLs or access credentials.
