# WalkBot
The integrated WalkBot is a subsystem with a strict boundary: GSI provides state, the WalkBot consumes normalized state, navigation chooses a waypoint target, and InputAdapter is the only output boundary.
States: DISABLED -> INITIALIZING -> WAITING_FOR_GAME -> WAITING_FOR_SPAWN -> NAVIGATING -> ARRIVING/WAITING -> STUCK -> RECOVERING/REPLANNING.
The design deliberately separates path data, navigation policy, lifecycle supervision and input. This follows the useful architectural lessons from external CS2 walkbot projects while avoiding a monolithic bot.
