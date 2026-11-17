"""Per-user Windows DPAPI protection, available on Windows 7 without extra DLLs.

No machine-wide flag or plaintext fallback is used. Native calls are lazy so
non-Windows source runs and isolated tests do not load Windows libraries.
"""

from __future__ import annotations

import base64
import sys


def uses_dpapi() -> bool:
    return sys.platform == "win32"


def _crypt(data: bytes, *, decrypt: bool) -> bytes:
    if not uses_dpapi():
        raise OSError("此 API Key 由 Windows 用户账户保护，请在原账户使用或重新填写。")
    import ctypes
    from ctypes import wintypes

    class DataBlob(ctypes.Structure):
        _fields_ = [("cbData", wintypes.DWORD), ("pbData", ctypes.POINTER(ctypes.c_ubyte))]

    crypt32 = ctypes.WinDLL("crypt32", use_last_error=True)
    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    function = crypt32.CryptUnprotectData if decrypt else crypt32.CryptProtectData
    function.argtypes = [
        ctypes.POINTER(DataBlob),
        ctypes.POINTER(ctypes.c_wchar_p) if decrypt else ctypes.c_wchar_p,
        ctypes.POINTER(DataBlob), ctypes.c_void_p, ctypes.c_void_p,
        wintypes.DWORD, ctypes.POINTER(DataBlob),
    ]
    function.restype = wintypes.BOOL
    kernel32.LocalFree.argtypes = [ctypes.c_void_p]
    kernel32.LocalFree.restype = ctypes.c_void_p
    buffer = (ctypes.c_ubyte * len(data)).from_buffer_copy(data)
    incoming = DataBlob(len(data), buffer)
    outgoing = DataBlob()
    try:
        # CRYPTPROTECT_UI_FORBIDDEN; omit CRYPTPROTECT_LOCAL_MACHINE so only
        # this user's credentials can unprotect the persisted blob.
        if not function(ctypes.byref(incoming), None, None, None, None, 1, ctypes.byref(outgoing)):
            raise OSError("Windows 无法保护或读取 API Key，请在当前账户重新保存设置。")
        return ctypes.string_at(outgoing.pbData, outgoing.cbData)
    finally:
        ctypes.memset(buffer, 0, len(data))
        if outgoing.pbData:
            ctypes.memset(outgoing.pbData, 0, outgoing.cbData)
            kernel32.LocalFree(ctypes.cast(outgoing.pbData, ctypes.c_void_p))


def protect_key(key: str) -> str:
    return base64.b64encode(_crypt(key.encode("utf-8"), decrypt=False)).decode("ascii")


def unprotect_key(value: str) -> str:
    if not isinstance(value, str) or len(value) > 32768:
        raise ValueError("受保护的 API Key 格式不正确，请重新填写。")
    return _crypt(base64.b64decode(value, validate=True), decrypt=True).decode("utf-8")
