from __future__ import annotations

import os
import sys
from pathlib import Path, PureWindowsPath


def path_text_error(value: str, *, windows: bool | None = None) -> str | None:
    """Check spelling without resolving, rewriting or touching a user's path."""
    if not isinstance(value, str) or not value.strip():
        return "请选择有效的文件或文件夹位置。"
    if any(ord(char) < 32 for char in value):
        return "位置中含有换行或无效字符，请重新选择。"
    if windows is None:
        windows = os.name == "nt"
    if windows:
        path = PureWindowsPath(value)
        drive = path.drive
        if drive.startswith("\\\\?\\"):
            drive = drive[4:]
        if drive.upper().startswith("UNC\\"):
            drive = drive[4:]
        if drive.startswith("\\\\"):
            drive = drive[2:]
        if drive and not (len(drive) == 2 and drive[0].isascii() and drive[0].isalpha() and drive[1] == ":"):
            if any(char in '<>:"|?*' for char in drive) or drive.startswith(".\\"):
                return "位置中的盘符或共享目录无效，请重新选择。"
        parts = path.parts[1:] if path.anchor else path.parts
        for part in parts:
            if part in {".", ".."}:
                continue
            if any(char in '<>:"|?*' for char in part) or part.endswith((" ", ".")):
                return "位置中含有 Windows 不支持的字符，请重新选择。"
            if PureWindowsPath(part).is_reserved():
                return "位置使用了 Windows 系统保留名称，请重新选择。"
    return None


def absolute_path_hint(value: object) -> Path | None:
    """Accept only well-formed absolute directory hints from system settings."""
    if not isinstance(value, (str, Path)):
        return None
    text = str(value)
    if path_text_error(text):
        return None
    path = Path(text)
    return path if path.is_absolute() else None


def _windows_shell_folder(csidl: int) -> Path | None:
    # SHGetFolderPathW is available on the frozen Windows 7 stack. Use the
    # current user's Shell folder when inherited environment hints are broken.
    try:
        import ctypes
        from ctypes import wintypes

        query = ctypes.WinDLL("shell32", use_last_error=True).SHGetFolderPathW
        query.argtypes = (wintypes.HWND, ctypes.c_int, wintypes.HANDLE, wintypes.DWORD, wintypes.LPWSTR)
        query.restype = ctypes.c_int32  # HRESULT, including on 64-bit Windows.
        buffer = ctypes.create_unicode_buffer(260)
        if query(None, csidl, None, 0, buffer) == 0:
            return absolute_path_hint(buffer.value)
    except (AttributeError, OSError, ValueError):
        pass
    return None


def _system_home_dir() -> Path | None:
    if sys.platform.startswith("win"):
        return _windows_profile_dir()
    try:
        import pwd

        return absolute_path_hint(pwd.getpwuid(os.getuid()).pw_dir)
    except (ImportError, KeyError, OSError):
        return None


def _windows_profile_dir() -> Path | None:
    # Query the account token, not another expansion of the damaged USERPROFILE
    # environment value. All functions used here are available on Windows 7.
    try:
        import ctypes
        from ctypes import wintypes

        kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
        current_process = kernel32.GetCurrentProcess
        current_process.argtypes = ()
        current_process.restype = wintypes.HANDLE
        close = kernel32.CloseHandle
        close.argtypes = (wintypes.HANDLE,)
        close.restype = wintypes.BOOL
        open_token = ctypes.WinDLL("advapi32", use_last_error=True).OpenProcessToken
        open_token.argtypes = (wintypes.HANDLE, wintypes.DWORD, ctypes.POINTER(wintypes.HANDLE))
        open_token.restype = wintypes.BOOL
        query = ctypes.WinDLL("userenv", use_last_error=True).GetUserProfileDirectoryW
        query.argtypes = (wintypes.HANDLE, wintypes.LPWSTR, ctypes.POINTER(wintypes.DWORD))
        query.restype = wintypes.BOOL
        token = wintypes.HANDLE()
        if not open_token(current_process(), 0x0008, ctypes.byref(token)):  # TOKEN_QUERY
            return None
        try:
            size = wintypes.DWORD(0)
            query(token, None, ctypes.byref(size))
            if not 0 < size.value <= 32768:
                return None
            buffer = ctypes.create_unicode_buffer(size.value)
            if query(token, buffer, ctypes.byref(size)):
                return absolute_path_hint(buffer.value)
        finally:
            close(token)
    except (AttributeError, OSError, ValueError):
        pass
    return None


def user_home_dir() -> Path:
    """Keep a valid configured home; recover malformed hints from the OS."""
    try:
        candidate = absolute_path_hint(Path.home())
        if candidate is not None and candidate.is_dir():
            return candidate
    except (OSError, RuntimeError, ValueError):
        pass
    candidate = _system_home_dir()
    if candidate is not None and candidate.is_dir():
        return candidate
    raise RuntimeError("无法读取当前账户的用户文件夹，请检查账户目录和磁盘连接。")


def user_app_data_dir(kind: str) -> Path:
    """Resolve settings/data/log bases without accepting relative env paths."""
    if kind not in {"config", "data", "state"}:
        raise ValueError(f"Unknown user directory kind: {kind}")
    if sys.platform.startswith("win"):
        candidate = absolute_path_hint(os.environ.get("LOCALAPPDATA", "").strip())
        if candidate is not None:
            return candidate
        candidate = _windows_shell_folder(0x1C)  # CSIDL_LOCAL_APPDATA
        return candidate if candidate is not None else user_home_dir() / "AppData" / "Local"
    if sys.platform == "darwin":
        suffix = "Logs" if kind == "state" else "Application Support"
        return user_home_dir() / "Library" / suffix
    variable, suffix = {
        "config": ("XDG_CONFIG_HOME", ".config"),
        "data": ("XDG_DATA_HOME", ".local/share"),
        "state": ("XDG_STATE_HOME", ".local/state"),
    }[kind]
    candidate = absolute_path_hint(os.environ.get(variable, "").strip())
    return candidate if candidate is not None else user_home_dir() / suffix


def path_is_relative_to(path: Path, root: Path) -> bool:
    """Python 3.8 compatible equivalent of ``Path.is_relative_to``."""
    try:
        path.relative_to(root)
    except ValueError:
        return False
    return True
