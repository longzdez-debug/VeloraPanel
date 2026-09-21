from __future__ import annotations
import ctypes
from ctypes import wintypes
from .input import NullInput
class WindowsInput(NullInput):
    _user32=ctypes.windll.user32 if hasattr(ctypes,"windll") else None
    _map={"forward":0x57,"back":0x53,"left":0x41,"right":0x44}
    def __init__(self,enabled=False):
        super().__init__(); self.enabled=enabled
    def _key(self,code,down):
        if not self.enabled or self._user32 is None:return
        class KI(ctypes.Structure):_fields_=[("wVk",wintypes.WORD),("wScan",wintypes.WORD),("dwFlags",wintypes.DWORD),("time",wintypes.DWORD),("dwExtraInfo",ctypes.POINTER(ctypes.c_ulong))]
        class II(ctypes.Union):_fields_=[("ki",KI)]
        class IN(ctypes.Structure):_fields_=[("type",wintypes.DWORD),("ii",II)]
        self._user32.SendInput(1,IN(1,II(KI(code,0,0 if down else 2,0,None))),ctypes.sizeof(IN))
    def move(self,forward,back,left,right):
        wanted={k:v for k,v in (("forward",forward),("back",back),("left",left),("right",right)) if v}
        for k in list(self._down):
            if k not in wanted:self._key(self._map[k],False);self._down.remove(k)
        for k in wanted:
            if k not in self._down:self._key(self._map[k],True);self._down.add(k)
    def release_all(self):
        for k in list(self._down):self._key(self._map[k],False)
        self._down.clear()
