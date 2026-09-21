import re


_SECRET_PATTERNS = (
    re.compile(r"(?i)(password|passwd|shared_secret|identity_secret|bot_token|gsi token|token)(\s*[:=]\s*)(\S+)"),
    re.compile(r"https?://steamcommunity\.com/tradeoffer/new/\?partner=\d+&token=[A-Za-z0-9_-]+", re.IGNORECASE),
)


def redact(value) -> str:
    text = str(value)
    for pattern in _SECRET_PATTERNS:
        text = pattern.sub(lambda match: f"{match.group(1)}{match.group(2)}***" if match.lastindex and match.lastindex >= 3 else "***", text)
    return text
