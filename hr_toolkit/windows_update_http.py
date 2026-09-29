"""Bounded WinHTTP compatibility GET for the public Gitee release endpoint.

Not a general downloader: no redirects, cookies, authentication or insecure TLS.
Only used after an identified WAF response, never after a certificate failure.
"""

import ctypes
import io
import os
import sys
import time
import urllib.request


ENDPOINT = "https://gitee.com/api/v5/repos/optimistic-little-sunspot/hr-toolkit/releases/latest"
MAX_BYTES = 2 * 1024 * 1024
DWORD = ctypes.c_uint32
HANDLE = ctypes.c_void_p
BOOL = ctypes.c_int


class NativeHTTPError(OSError):
    def __init__(self, operation, code):
        super().__init__("WinHTTP " + operation)
        self.winerror = code


class Response(io.BytesIO):
    def __init__(self, body, status, headers):
        super().__init__(body)
        self.status = status
        self.headers = headers

    def geturl(self):
        return ENDPOINT


def direct_connection_allowed():
    """Do not switch around an explicit application/environment/PAC proxy."""
    if sys.platform != "win32":
        return False
    try:
        if any(urllib.request.getproxies().values()):
            return False
        if any(value for key, value in os.environ.items()
               if key.lower() in ("http_proxy", "https_proxy", "all_proxy", "no_proxy")):
            return False
        # A custom opener can carry application-specific network policy.
        if getattr(urllib.request, "_opener", None) is not None:
            return False
        import winreg
        try:
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER,
                                r"Software\Microsoft\Windows\CurrentVersion\Internet Settings") as key:
                try:
                    return not bool(winreg.QueryValueEx(key, "AutoConfigURL")[0])
                except FileNotFoundError:
                    return True
        except FileNotFoundError:
            return True
    except Exception:
        return False


def _load_api():
    if sys.platform != "win32":
        raise OSError("WinHTTP requires Windows")
    kernel = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel.GetSystemDirectoryW.argtypes = [ctypes.c_wchar_p, DWORD]
    kernel.GetSystemDirectoryW.restype = DWORD
    directory = ctypes.create_unicode_buffer(32768)
    size = kernel.GetSystemDirectoryW(directory, len(directory))
    if not size or size >= len(directory):
        raise OSError("System directory unavailable")
    api = ctypes.WinDLL(os.path.join(directory.value, "winhttp.dll"), use_last_error=True)
    signatures = {
        "WinHttpOpen": (HANDLE, [ctypes.c_wchar_p, DWORD, ctypes.c_wchar_p, ctypes.c_wchar_p, DWORD]),
        "WinHttpConnect": (HANDLE, [HANDLE, ctypes.c_wchar_p, ctypes.c_ushort, DWORD]),
        "WinHttpOpenRequest": (HANDLE, [HANDLE, ctypes.c_wchar_p, ctypes.c_wchar_p,
                                       ctypes.c_wchar_p, ctypes.c_wchar_p, HANDLE, DWORD]),
        "WinHttpSetOption": (BOOL, [HANDLE, DWORD, HANDLE, DWORD]),
        "WinHttpSetTimeouts": (BOOL, [HANDLE, ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int]),
        "WinHttpSendRequest": (BOOL, [HANDLE, ctypes.c_wchar_p, DWORD, HANDLE, DWORD, DWORD, ctypes.c_size_t]),
        "WinHttpReceiveResponse": (BOOL, [HANDLE, HANDLE]),
        "WinHttpQueryHeaders": (BOOL, [HANDLE, DWORD, ctypes.c_wchar_p, HANDLE,
                                       ctypes.POINTER(DWORD), ctypes.POINTER(DWORD)]),
        "WinHttpReadData": (BOOL, [HANDLE, HANDLE, DWORD, ctypes.POINTER(DWORD)]),
        "WinHttpCloseHandle": (BOOL, [HANDLE]),
    }
    for name, (result, arguments) in signatures.items():
        function = getattr(api, name)
        function.restype = result
        function.argtypes = arguments
    return api


def fetch_release(url, headers, timeout):
    """One direct HTTPS GET, Windows trust store, TLS 1.2, bounded reads.

    Per-operation timeouts use the remaining budget. OS DNS/connect timeout
    granularity may exceed that budget; there is no retry or subprocess here.
    """
    if url != ENDPOINT or not 0 < timeout <= 30:
        raise ValueError("Unsupported native update request")
    allowed = {"User-Agent", "Accept", "Cache-Control", "Pragma"}
    if set(headers) - allowed or any("\r" in value or "\n" in value for value in headers.values()):
        raise ValueError("Unsupported native request headers")
    api = _load_api()
    handles = []
    deadline = time.monotonic() + timeout

    def check(value, operation):
        if not value:
            raise NativeHTTPError(operation, ctypes.get_last_error())
        return value

    def handle(value, operation):
        check(value, operation)
        handles.append(value)
        return value

    def option(target, number, value):
        data = DWORD(value)
        check(api.WinHttpSetOption(target, number, ctypes.byref(data), ctypes.sizeof(data)), "option")

    def remaining(target):
        milliseconds = int((deadline - time.monotonic()) * 1000)
        if milliseconds <= 0:
            raise TimeoutError("Native update request timeout")
        check(api.WinHttpSetTimeouts(target, milliseconds, milliseconds, milliseconds, milliseconds), "timeout")

    def header(request, number):
        buffer = ctypes.create_unicode_buffer(1024)
        size = DWORD(ctypes.sizeof(buffer))
        if not api.WinHttpQueryHeaders(request, number, None, buffer, ctypes.byref(size), None):
            code = ctypes.get_last_error()
            if code == 12150:  # ERROR_WINHTTP_HEADER_NOT_FOUND
                return ""
            raise NativeHTTPError("header", code)
        return buffer.value

    try:
        session = handle(api.WinHttpOpen(headers.get("User-Agent", "HRToolkit-Updater/1.0"),
                                         1, None, None, 0), "open")  # NO_PROXY, synchronous
        option(session, 84, 0x800)  # SECURE_PROTOCOLS: TLS 1.2, including Windows 7
        option(session, 4, 1)  # CONNECT_RETRIES: only one address attempt
        remaining(session)
        connection = handle(api.WinHttpConnect(session, "gitee.com", 443, 0), "connect")
        request = handle(api.WinHttpOpenRequest(connection, "GET", url.split("gitee.com", 1)[1],
                                                None, None, None, 0x800000), "request")
        option(request, 63, 1 | 2 | 4)  # disable cookies, redirects, automatic authentication
        remaining(request)
        text = "".join(key + ": " + value + "\r\n" for key, value in headers.items())
        check(api.WinHttpSendRequest(request, text, len(text), None, 0, 0, 0), "send")
        remaining(request)
        check(api.WinHttpReceiveResponse(request, None), "receive")
        status, size = DWORD(), DWORD(ctypes.sizeof(DWORD))
        check(api.WinHttpQueryHeaders(request, 19 | 0x20000000, None,
                                      ctypes.byref(status), ctypes.byref(size), None), "status")
        response_headers = {"Content-Type": header(request, 1), "Content-Length": header(request, 5)}
        limit = MAX_BYTES if status.value == 200 else 4096
        length = response_headers["Content-Length"]
        if status.value == 200 and length and int(length) > limit:
            raise ValueError("Native update response too large")
        parts, total = [], 0
        while total <= limit:
            remaining(request)
            read_limit = limit + 1 if status.value == 200 else limit
            buffer = ctypes.create_string_buffer(min(65536, read_limit - total))
            read = DWORD()
            check(api.WinHttpReadData(request, buffer, len(buffer), ctypes.byref(read)), "read")
            if not read.value:
                break
            parts.append(buffer.raw[:read.value])
            total += read.value
            if status.value != 200 and total >= limit:
                break
        if status.value == 200 and total > limit:
            raise ValueError("Native update response too large")
        return Response(b"".join(parts)[:limit], status.value, response_headers)
    finally:
        for current in reversed(handles):
            api.WinHttpCloseHandle(current)
