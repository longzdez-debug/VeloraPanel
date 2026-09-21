from __future__ import annotations
from dataclasses import asdict, dataclass, field
from .storage import JsonStore

@dataclass
class AccountProfile:
    id: str
    name: str
    steam_id: str = ""
    enabled: bool = True
    walkbot: bool = True
    executable: str = ""
    launch_args: list[str] = field(default_factory=list)
    route_map: str | None = None
    route_start: str | None = None
    route_goal: str | None = None

class AccountStore:
    def __init__(self, path):
        self.store = JsonStore(path)

    def load(self):
        raw = self.store.load([])
        if not isinstance(raw, list):
            return []
        result = []
        for item in raw:
            if not isinstance(item, dict) or not item.get("id"):
                continue
            args = item.get("launch_args", [])
            if not isinstance(args, list):
                args = []
            result.append(AccountProfile(
                id=str(item["id"]),
                name=str(item.get("name") or item["id"]),
                steam_id=str(item.get("steam_id") or ""),
                enabled=bool(item.get("enabled", True)),
                walkbot=bool(item.get("walkbot", True)),
                executable=str(item.get("executable") or ""),
                launch_args=[str(x) for x in args],
                route_map=str(item["route_map"]) if item.get("route_map") else None,
                route_start=str(item["route_start"]) if item.get("route_start") else None,
                route_goal=str(item["route_goal"]) if item.get("route_goal") else None,
            ))
        return result

    def save(self, profiles):
        self.store.save([asdict(p) for p in profiles])

    def upsert(self, profile: AccountProfile):
        profiles = self.load()
        for i, current in enumerate(profiles):
            if current.id == profile.id:
                profiles[i] = profile
                self.save(profiles)
                return
        profiles.append(profile)
        self.save(profiles)
