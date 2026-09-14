"""Blend the macOS titlebar into the client area, retaining native controls.

Windows uses Qt's own system move/resize API in QML (also Qt 5.15 / Win7).
No global hooks, keyboard interception, or replacement native window procedure.
"""
from __future__ import annotations

import os
import sys


def integrate_mac_titlebar(window) -> bool:
    if sys.platform != "darwin" or os.environ.get("QT_QPA_PLATFORM", "").split(":")[0] in {"offscreen", "minimal"}:
        return False
    import ctypes

    objc = ctypes.CDLL("/usr/lib/libobjc.A.dylib")
    objc.sel_registerName.argtypes = [ctypes.c_char_p]
    objc.sel_registerName.restype = ctypes.c_void_p

    def send(receiver, selector, result, argtypes=(), args=()):
        function = ctypes.CFUNCTYPE(result, ctypes.c_void_p, ctypes.c_void_p, *argtypes)(
            ctypes.cast(objc.objc_msgSend, ctypes.c_void_p).value
        )
        return function(receiver, objc.sel_registerName(selector.encode("ascii")), *args)

    view = int(window.winId())
    native_window = send(view, "window", ctypes.c_void_p)
    if not native_window:
        return False
    mask = send(native_window, "styleMask", ctypes.c_ulong)
    send(native_window, "setStyleMask:", None, (ctypes.c_ulong,), (mask | (1 << 15),))
    send(native_window, "setTitleVisibility:", None, (ctypes.c_long,), (1,))
    send(native_window, "setTitlebarAppearsTransparent:", None, (ctypes.c_bool,), (True,))
    # Qt 6.9+ adds automatic safe-area padding to ApplicationWindow. Our
    # toolbar already reserves the native buttons; older Qt has no padding.
    if window.metaObject().indexOfProperty("topPadding") >= 0:
        window.setProperty("topPadding", 0)
    # Qt owns positioning of the content view and keeps Cocoa traffic lights.
    window.setProperty("nativeTitleIntegrated", True)
    return True
