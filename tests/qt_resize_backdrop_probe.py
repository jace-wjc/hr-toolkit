"""Exercise theme callbacks through a cold production Qt startup."""
from __future__ import annotations

from pathlib import Path
import sys
import tempfile
import traceback
from unittest.mock import Mock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


def main():
    # Do not preload QtQuick: production may expose the QML root as QWindow.
    from hr_toolkit.gui_qt.compat import QApplication, QTimer
    from hr_toolkit.gui_qt.controller import AppController
    from hr_toolkit.gui_qt.live_resize import WindowsResizeBackdrop, WINDOW_BACKGROUND_RGB
    from hr_toolkit.gui_qt.main import main as desktop_main

    colors, backdrops, callback_errors = [], [], []

    def install(window, background_rgb=WINDOW_BACKGROUND_RGB):
        colors.append(background_rgb)
        backdrop = Mock(spec=WindowsResizeBackdrop)
        backdrops.append(backdrop)
        return backdrop

    def verify(controller):
        app = QApplication.instance()
        try:
            for theme, expected in (("dark", (24, 29, 35)), ("light", (252, 252, 251))):
                before = len(colors)
                controller.presentation.setTheme(theme)
                app.processEvents()
                assert not callback_errors, callback_errors
                assert len(colors) == before + 1, colors
                assert colors[-1] == expected, colors
                backdrops[-2].close.assert_called_once_with()
            app.exit(0)
        except BaseException:
            traceback.print_exc()
            app.exit(1)

    def start(controller):
        QTimer.singleShot(50, lambda: verify(controller))

    def record_callback_error(exc_type, exc_value, exc_tb):
        callback_errors.append("".join(traceback.format_exception(exc_type, exc_value, exc_tb)))

    with tempfile.TemporaryDirectory(prefix="hr_backdrop_probe_") as temp:
        with patch.object(AppController, "_settings_path", return_value=Path(temp) / "workspace-ui.json"), \
             patch.object(AppController, "start", start), \
             patch.object(WindowsResizeBackdrop, "install", side_effect=install), \
             patch.object(sys, "excepthook", record_callback_error):
            result = desktop_main()
    assert result == 0 and not callback_errors, callback_errors
    assert len(backdrops) == 3, colors
    for backdrop in backdrops:
        backdrop.close.assert_called_once_with()
    print("resize backdrop: cold startup, theme colors and cleanup OK")


if __name__ == "__main__":
    main()
