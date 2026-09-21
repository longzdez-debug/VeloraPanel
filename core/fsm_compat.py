import json
from pathlib import Path


FSM_TO_VELORA = {
    "STEAM_PATH": "SteamPath",
    "CSGO_PATH": "CS2Path",
    "STEAM_LAUNCH_OPTIONS": "SteamArg",
    "ADDITIONAL_LAUNCH_OPTIONS": "CS2Arg",
    "ENABLE_AUTOACCEPT": "AutoAcceptEnabled",
    "AUTO_LOOT": "LooterEnabled",
    "TRADEOFFER_LINK": "LooterTradeLink",
    "AUTODISCONNECTS": "AutoDisconnectEnabled",
    "AUTODISCONNECTS_DELAY": "AutoDisconnectDelay",
    "ACCOUNTS_LAUNCH_DELAY": "AccountsLaunchDelay",
    "GAME_SEARCH_TIMEOUT": "GameSearchTimeout",
    "LOBBY_CREATION_ATTEMPTS_BEFORE_SHUFFLE": "LobbyCreationAttempts",
    "SEARCH_RETRIES_BEFORE_SHUFFLE": "SearchRetriesBeforeShuffle",
    "AUTOSHUFFLE_AFTER_GAME": "AutoShuffleAfterGame",
    "DISABLE_STEAM_OVERLAY": "DisableOverlay",
    "REPLACE_ERROR_ACCOUNT": "ReplaceErrorAccount",
    "AUTODISCONNECTS": "AutoDisconnectEnabled",
    "AUTODISCONNECTS_DELAY": "AutoDisconnectDelay",
    "AUTODISCONNECTS_CHANGE_TEAMS_DELAY": "AutoDisconnectTeamChangeDelay",
    "ANTI_AFK": "AntiAfkEnabled",
    "ANTI_AFK_DELAY": "AntiAfkDelay",
    "ANTI_AFK_MINIMIZE": "AntiAfkMinimize",
    "MAP_LOAD_DELAY": "MapLoadDelay",
    "CHANGE_BATCH_AFTER_N_MINUTES": "ChangeBatchAfterMinutes",
    "LOBBY_INVITE_MODE": "LobbyInviteMode",
    "FARMING_MODE": "FarmingMode",
    "RUNNING2VS2": "Running2v2",
    "DROP_HISTORY_CACHE": "DropHistoryCache",
    "ROUND_TARGET": "RoundTarget",
    "ACCOUNT_LOGIN_ATTEMPTS": "AccountLoginAttempts",
    "ANCIENT_MAP_PRELOAD": "AncientMapPreload",
    "AUTOACCEPT_READ_TIME": "AutoAcceptReadTime",
}


def load_fsm_settings(path) -> dict:
    source = Path(path)
    with source.open("r", encoding="utf-8") as handle:
        value = json.load(handle)
    if not isinstance(value, dict):
        raise ValueError("FSM settings must contain an object")
    return value


def convert_fsm_settings(value: dict) -> dict:
    if not isinstance(value, dict):
        raise TypeError("FSM settings must contain an object")
    converted = {}
    for source_key, target_key in FSM_TO_VELORA.items():
        if source_key in value:
            converted[target_key] = value[source_key]
    return converted
