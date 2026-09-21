import threading
import os

from core.paths import SETTINGS_DIR
from core.storage import read_json, write_json
from core.config_validation import validate_settings
from core.fsm_compat import convert_fsm_settings, load_fsm_settings
from core.steam_paths import resolve_paths
from core.audit import record


class SettingsManager:
    _instance = None
    _file_path = SETTINGS_DIR / "settings.json"
    _settings = {}
    _hidden_keys = {
        "SteamMutexInitDelay",
        "SteamMutexName",
        "SteamMutexCloseAttempts",
        "SteamMutexRetryDelay",
        "SteamMutexInitTimeout",
        "SteamMutexPollInterval",
    }

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(SettingsManager, cls).__new__(cls)
            cls._instance._lock = threading.RLock()
            cls._instance._load()
        return cls._instance

    def _load(self):
        self._file_path.parent.mkdir(parents=True, exist_ok=True)

        if not os.path.exists(self._file_path):
            self._settings = {}
            self._save()
            self._discover_installations()
            return

        try:
            self._settings = read_json(self._file_path, {})
            if not isinstance(self._settings, dict):
                raise RuntimeError("settings.json must contain an object")
            for error in validate_settings(self._settings):
                print(f"⚠️ Некорректная настройка: {error}")
        except RuntimeError as exc:
            print(f"❌ Ошибка чтения settings.json: {exc}")
            self._settings = {}
            self._save()
            return

        if self._remove_hidden_keys():
            self._save()
        self._discover_installations()

    def _discover_installations(self):
        steam, cs2 = resolve_paths(
            self._settings.get("SteamPath"),
            self._settings.get("CS2Path"),
        )
        changed = False
        if steam and self._settings.get("SteamPath") != str(steam):
            self._settings["SteamPath"] = str(steam)
            changed = True
        if cs2 and self._settings.get("CS2Path") != str(cs2):
            self._settings["CS2Path"] = str(cs2)
            changed = True
        if changed:
            self._save()
            record("installation_discovery", "Steam/CS2 paths discovered")

    def _save(self):
        self._remove_hidden_keys()
        write_json(self._file_path, self._settings)

    def _remove_hidden_keys(self):
        removed = False
        for key in self._hidden_keys:
            if key in self._settings:
                self._settings.pop(key, None)
                removed = True
        return removed

    def get(self, key, default=None):
        """
        Получение значения настройки.
        Если ключ отсутствует, создаёт его с default и возвращает default.
        """
        with self._lock:
            if key in self._hidden_keys:
                return default
            if key not in self._settings:
                self._settings[key] = default
                self._save()
            return self._settings[key]

    def set(self, key, value):
        with self._lock:
            if key in self._hidden_keys:
                self.delete(key)
                return
            self._settings[key] = value
            self._save()

    def delete(self, key):
        with self._lock:
            if key in self._settings:
                del self._settings[key]
                self._save()

    def all(self):
        with self._lock:
            return {k: v for k, v in self._settings.items() if k not in self._hidden_keys}

    def import_fsm_file(self, path, overwrite=False):
        imported = convert_fsm_settings(load_fsm_settings(path))
        with self._lock:
            for key, value in imported.items():
                if overwrite or key not in self._settings:
                    self._settings[key] = value
            self._save()
        return imported