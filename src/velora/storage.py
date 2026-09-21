from __future__ import annotations
import json, os, tempfile

class JsonStore:
    def __init__(self, path):
        self.path = path

    def load(self, *args):
        if len(args) == 1:
            default = args[0]
            path = self.path
        elif len(args) == 2:
            key, default = args
            path = os.path.join(self.path, f"{key}.json")
        else:
            raise TypeError("load() expects default or key, default")
        try:
            with open(path, encoding="utf-8") as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return default

    def save(self, *args):
        if len(args) == 1:
            value = args[0]
            path = self.path
        elif len(args) == 2:
            key, value = args
            path = os.path.join(self.path, f"{key}.json")
        else:
            raise TypeError("save() expects value or key, value")
        os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
        fd, tmp = tempfile.mkstemp(prefix=".velora-", dir=os.path.dirname(path) or ".")
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                json.dump(value, f, ensure_ascii=False, indent=2)
                f.flush()
                os.fsync(f.fileno())
            os.replace(tmp, path)
        finally:
            if os.path.exists(tmp):
                os.unlink(tmp)
