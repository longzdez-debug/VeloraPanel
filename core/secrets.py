import base64
import binascii
import ctypes
import json
import os
from ctypes import wintypes
from pathlib import Path

from core.paths import ROOT


_STORE_PATH = ROOT / "secrets.dat"
_ENTROPY = b"VELORA-PANEL-CREDENTIALS-v1"


class _Blob(ctypes.Structure):
    _fields_ = [("cbData", wintypes.DWORD), ("pbData", ctypes.POINTER(ctypes.c_ubyte))]


def _crypt(data: bytes, protect: bool) -> bytes:
    crypt = ctypes.windll.crypt32.CryptProtectData if protect else ctypes.windll.crypt32.CryptUnprotectData
    in_buffer = (ctypes.c_ubyte * len(data)).from_buffer_copy(data)
    entropy_buffer = (ctypes.c_ubyte * len(_ENTROPY)).from_buffer_copy(_ENTROPY)
    input_blob = _Blob(len(data), in_buffer)
    entropy_blob = _Blob(len(_ENTROPY), entropy_buffer)
    output_blob = _Blob()
    if not crypt(
        ctypes.byref(input_blob),
        None,
        ctypes.byref(entropy_blob),
        None,
        None,
        0,
        ctypes.byref(output_blob),
    ):
        raise ctypes.WinError()
    try:
        return ctypes.string_at(output_blob.pbData, output_blob.cbData)
    finally:
        ctypes.windll.kernel32.LocalFree(output_blob.pbData)


def load() -> dict:
    if not _STORE_PATH.exists():
        return {}
    try:
        encrypted = base64.b64decode(_STORE_PATH.read_bytes(), validate=True)
        value = json.loads(_crypt(encrypted, False).decode("utf-8"))
        if not isinstance(value, dict):
            raise ValueError("secret store must contain an object")
        return value
    except (OSError, ValueError, json.JSONDecodeError, binascii.Error, ctypes.ArgumentError) as exc:
        raise RuntimeError(f"Cannot decrypt secret store: {exc}") from exc


def save(value: dict) -> None:
    if not isinstance(value, dict):
        raise TypeError("secret store must contain an object")
    plaintext = json.dumps(value, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    encrypted = _crypt(plaintext, True)
    temporary = _STORE_PATH.with_suffix(".tmp")
    with temporary.open("wb") as handle:
        handle.write(base64.b64encode(encrypted))
        handle.flush()
        os.fsync(handle.fileno())
    temporary.replace(_STORE_PATH)


def get_accounts() -> dict:
    return load().get("accounts", {})


def set_accounts(accounts: dict) -> None:
    value = load() if _STORE_PATH.exists() else {}
    value["accounts"] = accounts
    save(value)
