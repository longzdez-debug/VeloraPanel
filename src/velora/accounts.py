from __future__ import annotations

from dataclasses import asdict, dataclass, field
import json

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
            result.append(
                AccountProfile(
                    id=str(item["id"]),
                    name=str(item.get("name") or item["id"]),
                    steam_id=str(item.get("steam_id") or ""),
                    enabled=bool(item.get("enabled", True)),
                    walkbot=bool(item.get("walkbot", True)),
                    executable=str(item.get("executable") or ""),
                    launch_args=[str(x) for x in item.get("launch_args", [])],
                )
            )
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
