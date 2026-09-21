# Roadmap

The core launchable control plane is implemented. Remaining work is validation and optional expansion rather than missing foundation.

## Before real input
- Run the complete pytest suite.
- Verify the GSI token and CS2 GSI delivery.
- Build at least one real map route in the route editor.
- Dry-run with NullInput.
- Enable foreground-gated Windows input only after the dry run.

## Optional future expansion
1. Replay-based GSI integration fixtures for long-session regression tests.
2. Richer map geometry and collision-aware navigation.
3. Mouse/yaw control and route calibration where required by a supported WalkBot mode.
4. Persistent scheduler jobs and resource budgets for large multi-account deployments.
5. Dashboard authentication if remote/LAN administration is ever required.
