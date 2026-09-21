from pathlib import Path
from urllib.parse import urlparse


def validate_settings(settings: dict) -> list[str]:
    errors = []
    if not isinstance(settings, dict):
        return ["settings.json must contain an object"]

    boolean_keys = (
        "DisableOverlay",
        "RemoveBackground",
        "AutoAcceptEnabled",
        "AutoMatchInStartEnabled",
        "AutomaticAccountSwitchingEnabled",
        "LooterDryRun",
    )
    for key in boolean_keys:
        if key in settings and not isinstance(settings[key], bool):
            errors.append(f"{key} must be boolean")

    for key in ("LooterMaxItems",):
        value = settings.get(key, 0)
        if not isinstance(value, int) or value < 0:
            errors.append(f"{key} must be a non-negative integer")

    token = settings.get("GSIAuthToken", "")
    if not isinstance(token, str) or (token and len(token) < 16):
        errors.append("GSIAuthToken must be at least 16 characters")

    chat_ids = settings.get("TelegramAllowedChatIds", [])
    if not isinstance(chat_ids, list) or any(not str(value).strip() for value in chat_ids):
        errors.append("TelegramAllowedChatIds must be a list of non-empty IDs")

    trade_link = settings.get("LooterTradeLink", "")
    if trade_link:
        parsed = urlparse(trade_link)
        if parsed.scheme != "https" or parsed.netloc != "steamcommunity.com":
            errors.append("LooterTradeLink must be an https steamcommunity.com URL")

    blocked_names = settings.get("LooterBlockedNames", [])
    if not isinstance(blocked_names, list) or any(
        not isinstance(value, str) or not value.strip() for value in blocked_names
    ):
        errors.append("LooterBlockedNames must be a list of non-empty strings")

    max_trade_value = settings.get("LooterMaxTradeValue", 0)
    if not isinstance(max_trade_value, (int, float)) or max_trade_value < 0:
        errors.append("LooterMaxTradeValue must be a non-negative number")

    priority = settings.get("ProcessPriority", "normal")
    if priority not in ("normal", "idle", "below_normal", "above_normal"):
        errors.append("ProcessPriority must be normal, idle, below_normal, or above_normal")

    affinity = settings.get("ProcessAffinity", [])
    if not isinstance(affinity, list) or any(not isinstance(cpu, int) or cpu < 0 for cpu in affinity):
        errors.append("ProcessAffinity must be a list of non-negative CPU indexes")

    for key in ("SteamLoginMinInterval", "SteamTradeMinInterval", "SteamAuthCooldown"):
        value = settings.get(key, 0)
        if not isinstance(value, int) or value < 0:
            errors.append(f"{key} must be a non-negative integer")

    for key in ("PostLaunchDelay", "InterAccountLaunchDelay"):
        value = settings.get(key, 0)
        if not isinstance(value, int) or value < 0:
            errors.append(f"{key} must be a non-negative integer")

    launch_timeout = settings.get("CS2LaunchTimeout", 180)
    if not isinstance(launch_timeout, int) or not 30 <= launch_timeout <= 1800:
        errors.append("CS2LaunchTimeout must be an integer in range 30..1800")

    bounded_ints = {
        "AutoDisconnectDelay": (0, 3600),
        "AutoDisconnectTeamChangeDelay": (0, 3600),
        "AntiAfkDelay": (1, 86400),
        "MapLoadDelay": (0, 900),
        "ChangeBatchAfterMinutes": (0, 1440),
        "LobbyInviteMode": (0, 3),
        "FarmingMode": (0, 10),
        "RoundTarget": (1, 100),
        "AccountLoginAttempts": (1, 10),
        "AutoAcceptReadTime": (1, 3600),
        "GameSearchTimeout": (30, 3600),
        "SearchRetriesBeforeShuffle": (1, 20),
        "LobbyCreationAttempts": (1, 20),
    }
    for key, (minimum, maximum) in bounded_ints.items():
        value = settings.get(key, minimum)
        if not isinstance(value, int) or not minimum <= value <= maximum:
            errors.append(f"{key} must be an integer in range {minimum}..{maximum}")

    for key in (
        "AutoDisconnectEnabled",
        "ReplaceErrorAccount",
        "AntiAfkEnabled",
        "AntiAfkMinimize",
        "AutoShuffleAfterGame",
        "Running2v2",
        "DropHistoryCache",
        "AncientMapPreload",
    ):
        if key in settings and not isinstance(settings[key], bool):
            errors.append(f"{key} must be boolean")

    for key in ("SteamPath", "CS2Path"):
        value = settings.get(key, "")
        if value and not isinstance(value, str):
            errors.append(f"{key} must be a path string")

    for key in ("SteamArg", "CS2Arg"):
        value = settings.get(key, "")
        if not isinstance(value, str):
            errors.append(f"{key} must be a launch option string")

    return errors
