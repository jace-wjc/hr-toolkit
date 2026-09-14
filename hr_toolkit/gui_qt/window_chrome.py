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
    import platform

    class Point(ctypes.Structure):
        _fields_ = [("x", ctypes.c_double), ("y", ctypes.c_double)]

    class Rect(ctypes.Structure):
        _fields_ = [("origin", Point), ("width", ctypes.c_double), ("height", ctypes.c_double)]

    objc = ctypes.CDLL("/usr/lib/libobjc.A.dylib")
    objc.sel_registerName.argtypes = [ctypes.c_char_p]
    objc.sel_registerName.restype = ctypes.c_void_p

    def send(receiver, selector, result, argtypes=(), args=()):
        if result is Rect and platform.machine() == "x86_64":
            frame = Rect()
            function = ctypes.CFUNCTYPE(None, ctypes.POINTER(Rect), ctypes.c_void_p, ctypes.c_void_p)(
                ctypes.cast(objc.objc_msgSend_stret, ctypes.c_void_p).value
            )
            function(ctypes.byref(frame), receiver, objc.sel_registerName(selector.encode("ascii")))
            return frame
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

    from .compat import QObject, QTimer

    def align_controls():
        # AppKit resets these frames during show/resize. Read their final
        # positions instead of accumulating a relative offset each time.
        current_view = int(window.winId())
        current_window = send(current_view, "window", ctypes.c_void_p)
        toggle = window.findChild(QObject, "sidebarToggleButton")
        if not current_window or toggle is None:
            return
        # Leave the system's full-screen titlebar placement intact.
        if send(current_window, "styleMask", ctypes.c_ulong) & (1 << 14):
            return
        target_y = float(toggle.property("y")) + float(toggle.property("height")) / 2
        bounds = send(current_view, "bounds", Rect)
        view_flipped = send(current_view, "isFlipped", ctypes.c_bool)
        for button_type in (0, 1, 2):
            button = send(current_window, "standardWindowButton:", ctypes.c_void_p,
                          (ctypes.c_ulong,), (button_type,))
            if not button:
                continue
            frame = send(button, "frame", Rect)
            parent = send(button, "superview", ctypes.c_void_p)
            if not parent:
                continue
            center = Point(frame.origin.x + frame.width / 2, frame.origin.y + frame.height / 2)
            location = send(parent, "convertPoint:toView:", Point,
                            (Point, ctypes.c_void_p), (center, current_view))
            current_y = location.y if view_flipped else bounds.height - location.y
            delta = target_y - current_y
            if abs(delta) < 0.1:
                continue
            parent_flipped = send(parent, "isFlipped", ctypes.c_bool)
            origin = Point(frame.origin.x, frame.origin.y + (delta if parent_flipped else -delta))
            send(button, "setFrameOrigin:", None, (Point,), (origin,))

    alignment_timer = QTimer(window)
    alignment_timer.setSingleShot(True)
    alignment_timer.setInterval(32)
    alignment_timer.timeout.connect(align_controls)
    window._mac_title_alignment_timer = alignment_timer

    def schedule_alignment(*_args):
        alignment_timer.start()

    for signal in (window.widthChanged, window.heightChanged, window.visibilityChanged,
                   window.activeChanged, window.screenChanged):
        signal.connect(schedule_alignment)
    schedule_alignment()
    return True
