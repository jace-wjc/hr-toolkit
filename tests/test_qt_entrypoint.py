from __future__ import annotations

import os
from contextlib import ExitStack
import subprocess
import sys
import tempfile
import types
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

import hr_toolkit_app
from hr_toolkit.gui_qt.live_resize import (
    LiveResizeUpdater,
    WindowsResizeBackdrop,
    _windows_colorref,
)
from hr_toolkit.gui_qt.main import _prepare_environment
from hr_toolkit.gui_qt import smoke as qt_smoke


class QtEntrypointTests(unittest.TestCase):
    def _qt_compat_or_skip(self):
        try:
            from hr_toolkit.gui_qt import compat as qt_compat
        except ImportError as exc:
            self.skipTest(f"Qt runtime is not installed in this CI lane: {exc}")
        return qt_compat

    def test_production_window_and_dialog_inherit_embedded_brand_icon(self) -> None:
        self._qt_compat_or_skip()
        probe = Path(__file__).with_name("qt_icon_probe.py")
        completed = subprocess.run(
            [sys.executable, "-X", "faulthandler", str(probe)],
            cwd=str(probe.resolve().parents[1]),
            env={**os.environ, "QT_QPA_PLATFORM": "offscreen", "HR_TOOLKIT_SKIP_UPDATE": "1"},
            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            encoding="utf-8", errors="replace", timeout=30, check=False,
        )
        self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)
        self.assertIn("brand icon: 6 sizes, main window and dialog OK", completed.stdout)

    def test_production_qml_connections_preserve_every_signal_argument(self) -> None:
        self._qt_compat_or_skip()
        probe = Path(__file__).with_name("qt_connections_probe.py")
        completed = subprocess.run(
            [sys.executable, "-X", "faulthandler", str(probe)],
            cwd=str(probe.resolve().parents[1]),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            encoding="utf-8",
            errors="replace",
            timeout=45,
            check=False,
        )
        self.assertEqual(
            completed.returncode,
            0,
            f"Native QML connection failure: {completed.stdout}\n{completed.stderr}",
        )
        self.assertIn("20/20 passed", completed.stdout)

    def test_long_update_notes_keep_exact_layout_with_bounded_delegates(self) -> None:
        self._qt_compat_or_skip()
        probe = Path(__file__).with_name("qt_update_notes_probe.py")
        completed = subprocess.run(
            [sys.executable, "-X", "faulthandler", str(probe)],
            cwd=str(probe.resolve().parents[1]),
            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            encoding="utf-8", errors="replace", timeout=45, check=False,
        )
        self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)
        self.assertIn("virtual notes: wrapping, resize, scroll, history and bounded delegates OK", completed.stdout)

    def test_workspace_panel_allocates_width_and_restores_after_narrow_resize(self) -> None:
        self._qt_compat_or_skip()
        probe = Path(__file__).with_name("qt_workspace_panel_probe.py")
        completed = subprocess.run(
            [sys.executable, "-X", "faulthandler", str(probe)],
            cwd=str(probe.resolve().parents[1]),
            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            encoding="utf-8", errors="replace", timeout=45, check=False,
        )
        self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)
        self.assertIn("responsive workspace: non-overlap, animation, hysteresis, restore, focus and core widths OK", completed.stdout)

    def test_qml_dialog_signals_have_named_parameters_on_both_qt_versions(self) -> None:
        self._qt_compat_or_skip()
        from hr_toolkit.gui_qt.controller import AppController

        expected = {
            "notificationRequested": ["title", "message", "level"],
            "confirmationRequested": ["title", "message", "token"],
            "projectCreationRequested": ["name", "parent"],
            "textInputRequested": ["title", "prompt", "initialValue", "token"],
        }
        meta = AppController.staticMetaObject
        for name, parameters in expected.items():
            with self.subTest(signal=name):
                signature = f"{name}({','.join(['QString'] * len(parameters))})"
                index = meta.indexOfSignal(signature)
                self.assertGreaterEqual(index, 0)
                self.assertEqual(
                    [bytes(value).decode("utf-8") for value in meta.method(index).parameterNames()],
                    parameters,
                )

    def test_qt_smoke_records_python_failure_and_keeps_native_log_open(self) -> None:
        self._qt_compat_or_skip()
        stages = []

        def install_fault_handler(*, file, all_threads):
            self.assertTrue(all_threads)
            self.assertFalse(file.closed)
            stages.append(file)

        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "qt-result.txt"
            with ExitStack() as patches:
                patches.enter_context(patch.dict(os.environ, {"HR_TOOLKIT_CHECK_OUTPUT": str(output)}))
                patches.enter_context(patch.object(sys, "argv", ["HRToolkit.exe", "--qt-smoke-test"]))
                patches.enter_context(patch.object(qt_smoke.faulthandler, "is_enabled", return_value=False))
                patches.enter_context(patch.object(qt_smoke.faulthandler, "enable", side_effect=install_fault_handler))
                disable = patches.enter_context(patch.object(qt_smoke.faulthandler, "disable"))
                patches.enter_context(patch("hr_toolkit.gui_qt.main.main", side_effect=RuntimeError("QML load failure")))
                patches.enter_context(patch.object(qt_smoke.sys, "stdout", None))
                result = qt_smoke.run()
            self.assertEqual(result, 1)
            self.assertEqual(len(stages), 1)
            self.assertTrue(stages[0].closed)
            disable.assert_called_once_with()
            self.assertTrue(Path(str(output) + ".native.log").is_file())
            detail = output.read_text(encoding="utf-8")
            self.assertIn("Traceback", detail)
            self.assertIn("QML load failure", detail)

    def test_qt_stage_diagnostics_do_not_run_in_normal_desktop_sessions(self) -> None:
        with patch.dict(os.environ, {}, clear=True):
            with patch.object(qt_smoke, "_emit") as emit:
                qt_smoke.mark_stage("qt-qml-load")
        emit.assert_not_called()

    def test_constant_property_avoids_pyside2_descriptor_copy(self) -> None:
        qt_compat = self._qt_compat_or_skip()
        calls = []

        def strict_property(value_type, getter=None, **options):
            if getter is None:
                raise TypeError("PySide2 decorator copy path was used")
            calls.append((value_type, getter, options))
            return (value_type, getter, options)

        def getter(_self):
            return "value"

        with patch.object(qt_compat, "Property", strict_property):
            descriptor = qt_compat.constant_property(str)(getter)

        self.assertEqual(descriptor, (str, getter, {"constant": True}))
        self.assertEqual(calls, [(str, getter, {"constant": True})])

    def test_controller_does_not_use_broken_pyside2_constant_decorator(self) -> None:
        source_path = (
            Path(__file__).resolve().parents[1]
            / "hr_toolkit"
            / "gui_qt"
            / "controller.py"
        )
        source = source_path.read_text(encoding="utf-8")

        self.assertNotRegex(
            source,
            r"@Property\([^\n]*constant\s*=\s*True",
        )

    def test_constant_property_keeps_qt_constant_metadata(self) -> None:
        qt_compat = self._qt_compat_or_skip()

        class ConstantProbe(qt_compat.QObject):
            @qt_compat.constant_property(str)
            def value(self) -> str:
                return "stable"

        probe = ConstantProbe()
        meta_property = probe.metaObject().property(
            probe.metaObject().indexOfProperty("value")
        )

        self.assertTrue(meta_property.isConstant())
        self.assertFalse(meta_property.isWritable())
        self.assertFalse(meta_property.hasNotifySignal())

    def test_windows_qt_environment_keeps_platform_render_defaults(self) -> None:
        with patch.object(sys, "platform", "win32"):
            with patch.dict(os.environ, {}, clear=True):
                _prepare_environment()
                self.assertNotIn("QSG_RENDER_LOOP", os.environ)
                self.assertNotIn("QSG_RHI_BACKEND", os.environ)
                self.assertEqual(os.environ["QML_DISABLE_DISK_CACHE"], "0")
                self.assertEqual(os.environ["QT_QPA_UPDATE_IDLE_TIME"], "0")

    def test_windows_qt_environment_preserves_explicit_update_delay(self) -> None:
        with patch.object(sys, "platform", "win32"):
            with patch.dict(
                os.environ,
                {"QT_QPA_UPDATE_IDLE_TIME": "4"},
                clear=True,
            ):
                _prepare_environment()
                self.assertEqual(os.environ["QT_QPA_UPDATE_IDLE_TIME"], "4")

    def test_live_resize_requests_coalescible_quick_window_updates(self) -> None:
        class FakeSignal:
            def __init__(self) -> None:
                self.callback = None

            def connect(self, callback) -> None:
                self.callback = callback

            def disconnect(self, callback) -> None:
                if self.callback == callback:
                    self.callback = None

            def emit(self) -> None:
                if self.callback is not None:
                    self.callback()

        class FakeWindow:
            def __init__(self) -> None:
                self.widthChanged = FakeSignal()
                self.heightChanged = FakeSignal()
                self.update_calls = 0
                self.persistent = []

            def setPersistentGraphics(self, value) -> None:
                self.persistent.append(("graphics", value))

            def setPersistentSceneGraph(self, value) -> None:
                self.persistent.append(("scene", value))

            def update(self) -> None:
                self.update_calls += 1

        window = FakeWindow()
        updater = LiveResizeUpdater(window)
        window.widthChanged.emit()
        window.heightChanged.emit()

        self.assertEqual(window.update_calls, 2)
        self.assertEqual(
            window.persistent,
            [("graphics", True), ("scene", True)],
        )
        updater.close()
        window.widthChanged.emit()
        self.assertEqual(window.update_calls, 2)

    def test_windows_resize_backdrop_is_inert_off_windows(self) -> None:
        with patch.object(sys, "platform", "darwin"):
            backdrop = WindowsResizeBackdrop.install(object())

        self.assertFalse(backdrop.active)
        self.assertEqual(_windows_colorref(0xF7, 0xF5, 0xF1), 0xF1F5F7)

    def test_windows_resize_backdrop_ignores_headless_qt_platforms(self) -> None:
        class HeadlessWindow:
            def winId(self):
                raise AssertionError("headless window must not be used as an HWND")

        # Python 3.8 parses ``with (a, b)`` as one tuple context manager.
        # Keep the Win7 lane on the older, explicit nested form.
        with patch.object(sys, "platform", "win32"):
            with patch.dict(
                os.environ,
                {"QT_QPA_PLATFORM": "offscreen"},
                clear=True,
            ):
                backdrop = WindowsResizeBackdrop.install(HeadlessWindow())

        self.assertFalse(backdrop.active)

    def test_macos_keeps_the_benchmarked_basic_render_loop(self) -> None:
        with patch.object(sys, "platform", "darwin"):
            with patch.dict(os.environ, {}, clear=True):
                _prepare_environment()
                self.assertEqual(os.environ["QSG_RENDER_LOOP"], "basic")
                self.assertNotIn("QSG_RHI_BACKEND", os.environ)

    def test_qt_environment_preserves_explicit_graphics_overrides(self) -> None:
        with patch.dict(
            os.environ,
            {
                "QSG_RENDER_LOOP": "threaded",
                "QSG_RHI_BACKEND": "opengl",
                "QML_DISABLE_DISK_CACHE": "1",
            },
            clear=True,
        ):
            with patch.object(sys, "platform", "darwin"):
                _prepare_environment()
                self.assertEqual(os.environ["QSG_RENDER_LOOP"], "threaded")
                self.assertEqual(os.environ["QSG_RHI_BACKEND"], "opengl")
                self.assertEqual(os.environ["QML_DISABLE_DISK_CACHE"], "1")

    def test_software_rendering_environment_sets_backend_and_basic_loop(self) -> None:
        with patch.dict(os.environ, {"HR_TOOLKIT_QT_SOFTWARE_RENDER": "1"}, clear=True):
            _prepare_environment()
            self.assertEqual(os.environ["QT_QUICK_BACKEND"], "software")
            self.assertEqual(os.environ["QSG_RENDER_LOOP"], "basic")

    def test_apply_software_rendering_flags(self) -> None:
        with patch.dict(os.environ, {}, clear=True):
            remaining = hr_toolkit_app._apply_software_rendering_flags(["--software-rendering", "foo"])
            self.assertEqual(remaining, ["foo"])
            self.assertEqual(os.environ.get("HR_TOOLKIT_QT_SOFTWARE_RENDER"), "1")

        with patch.dict(os.environ, {}, clear=True):
            remaining = hr_toolkit_app._apply_software_rendering_flags(["--software-render"])
            self.assertEqual(remaining, [])
            self.assertEqual(os.environ.get("HR_TOOLKIT_QT_SOFTWARE_RENDER"), "1")

        with patch.dict(os.environ, {}, clear=True):
            remaining = hr_toolkit_app._apply_software_rendering_flags(["--foo"])
            self.assertEqual(remaining, ["--foo"])
            self.assertNotIn("HR_TOOLKIT_QT_SOFTWARE_RENDER", os.environ)

    def test_qt_entrypoint_does_not_subclass_the_native_window(self) -> None:
        source_path = (
            Path(__file__).resolve().parents[1]
            / "hr_toolkit"
            / "gui_qt"
            / "main.py"
        )
        source = source_path.read_text(encoding="utf-8")

        self.assertNotIn("_WindowsSizingHook", source)
        self.assertNotIn("SetWindowLongPtrW", source)
        self.assertNotIn("WM_PAINT", source)

    def test_input_list_stops_at_content_boundaries(self) -> None:
        source = (Path(__file__).resolve().parents[1] / "hr_toolkit" / "gui_qt" / "qml" / "Main.qml").read_text(encoding="utf-8")
        input_list = source.split('objectName: "inputList"', 1)[1].split("delegate: Rectangle", 1)[0]
        self.assertIn("boundsBehavior: Flickable.StopAtBounds", input_list)
        self.assertIn("flickableDirection: Flickable.VerticalFlick", input_list)
        self.assertIn("interactive: contentHeight > height", input_list)

    def test_main_scroll_stops_at_content_boundaries(self) -> None:
        source = (Path(__file__).resolve().parents[1] / "hr_toolkit" / "gui_qt" / "qml" / "Main.qml").read_text(encoding="utf-8")
        viewport = source.split('objectName: "mainScroll"', 1)[1].split("ColumnLayout {", 1)[0]
        self.assertIn("target: mainScroll.contentItem", viewport)
        self.assertIn('property: "boundsBehavior"', viewport)
        self.assertIn("value: Flickable.StopAtBounds", viewport)
        vertical_bar = viewport.split("ScrollBar.vertical: ScrollBar {", 1)[1].split("}", 1)[0]
        self.assertIn("interactive: true", vertical_bar)
        self.assertIn("parent: mainPane", vertical_bar)
        self.assertIn("anchors.right: parent.right", vertical_bar)

    def test_support_label_reserves_its_full_text_width(self) -> None:
        source = (Path(__file__).resolve().parents[1] / "hr_toolkit" / "gui_qt" / "qml" / "Main.qml").read_text(encoding="utf-8")
        column = source.split("id: supportSelectionColumn", 1)[1].split("RowLayout {", 1)[0]
        self.assertIn("anchors.fill: parent", column)
        self.assertIn("anchors.topMargin: 8", column)
        self.assertIn("anchors.bottomMargin: 8", column)
        self.assertNotIn("anchors.margins:", column)
        self.assertNotIn("anchors.leftMargin:", column)
        self.assertNotIn("anchors.rightMargin:", column)
        label = source.split("id: supportFieldLabel", 1)[1].split("Item {", 1)[0]
        self.assertIn("Layout.minimumWidth: Math.max(145, implicitWidth)", label)
        self.assertIn("Layout.preferredWidth: Layout.minimumWidth", label)
        self.assertIn("text: controller.supportLabel", label)

    def test_workspace_drag_has_stable_proxy_copy_action_and_click_alternative(self) -> None:
        qml = Path(__file__).resolve().parents[1] / "hr_toolkit" / "gui_qt" / "qml"
        source = (qml / "Main.qml").read_text(encoding="utf-8")
        proxy = source.split("id: workspaceDragProxy", 1)[1].split("id: workspaceDrawer", 1)[0]
        self.assertIn("controller.beginWorkspaceTransfer(path)", proxy)
        self.assertIn("Drag.startDrag(Qt.CopyAction)", proxy)
        self.assertLess(proxy.index("Drag.active = true"), proxy.index("Drag.startDrag(Qt.CopyAction)"))
        self.assertIn("Drag.active = false", proxy)
        self.assertIn("finally {", proxy)
        self.assertIn("if (!dragging) return", proxy)
        self.assertIn("controller.endWorkspaceTransfer", proxy)
        self.assertNotIn("Qt.MoveAction", proxy)
        self.assertIn("Qt.styleHints.startDragDistance", source)
        self.assertIn("workspaceDragProxy.start(pressedPath)", source)
        mouse = source.split("id: workspaceMouse", 1)[1].split("onClicked:", 1)[0]
        self.assertIn("onPressed: function(mouse)", mouse)
        self.assertIn("onPositionChanged: function(mouse)", mouse)
        self.assertIn('controller.useWorkspaceSelection("support")', source)
        self.assertIn('controller.useWorkspaceSelection("input")', source)
        self.assertNotIn("workspaceDrawer.close()", proxy)
        self.assertNotIn("restoreDrawer", proxy)
        target = (qml / "components" / "FileDropTarget.qml").read_text(encoding="utf-8")
        self.assertIn('drag.getDataAsString("application/x-hr-toolkit-workspace")', target)
        self.assertIn("drag.urls, workspaceToken", target)

    def test_update_waves_pause_during_native_window_movement(self) -> None:
        qml = Path(__file__).resolve().parents[1] / "hr_toolkit" / "gui_qt" / "qml" / "Main.qml"
        source = qml.read_text(encoding="utf-8")
        self.assertIn("onXChanged: noteWindowMotion()", source)
        self.assertIn("onYChanged: noteWindowMotion()", source)
        self.assertIn("onTriggered: root.windowMoving = false", source)
        wave = source.split("id: updateFill", 1)[1].split("contentItem: RowLayout", 1)[0]
        self.assertIn("paintSuspended: root.windowMoving", wave)
        self.assertIn("wavesRunning: !paintSuspended", wave)
        self.assertIn("onPaintSuspendedChanged: if (!paintSuspended) requestPaint()", wave)
        self.assertIn("if (paintSuspended) return", wave)
        self.assertIn("interval: 50", wave)
        self.assertNotIn("Behavior on level", wave)

    def test_remaining_ux_controls_preserve_explicit_confirmation(self) -> None:
        qml = Path(__file__).resolve().parents[1] / "hr_toolkit" / "gui_qt" / "qml"
        source = (qml / "Main.qml").read_text(encoding="utf-8")
        self.assertEqual(source.count("PresetMenuButton { backend: controller;"), 2)
        self.assertIn("onEditingFinished: controller.normalizeDateField(field.startId, text)", source)
        self.assertIn("controller.resultNoticeCategories", source)
        menu = (qml / "components" / "PresetMenuButton.qml").read_text(encoding="utf-8")
        self.assertIn("requestDeleteMaterialPreset(control.menuPreset)", menu)
        self.assertIn("enabled: control.customPreset", menu)
        self.assertNotIn("applyMaterialPreset", menu)
        template = (qml / "components" / "TemplateChoiceDialog.qml").read_text(encoding="utf-8")
        locator = template.split("function focusProblemControl", 1)[1].split("onAccepted:", 1)[0]
        self.assertIn("forceActiveFocus(Qt.TabFocusReason)", locator)
        self.assertIn("fieldRepeater.itemAt(i)", locator)
        self.assertNotIn("confirmed.checked = true", locator)
        self.assertNotIn(".skip =", locator)
        self.assertNotIn("saveTemplateChoice", locator)
        self.assertIn("(!problem && confirmed.checked)", template)

    def test_result_feedback_and_safe_lightweight_controls(self) -> None:
        qml = Path(__file__).resolve().parents[1] / "hr_toolkit" / "gui_qt" / "qml"
        source = (qml / "Main.qml").read_text(encoding="utf-8")
        self.assertIn('variant: controller.busy ? "secondary" : "primary"', source)
        self.assertIn("controller.openPrimaryResult()", source)
        self.assertIn("controller.resultNoticeModel", source)
        self.assertIn("controller.copyResultNotices()", source)
        self.assertIn("controller.openProjectDialog()", source)
        self.assertIn("controller.openSelectedInput(path)", source)
        dialog = (qml / "components" / "AppDialog.qml").read_text(encoding="utf-8")
        self.assertIn("property bool showCloseButton: false", dialog)
        self.assertIn("if (control.rejectText) control.reject()", dialog)
        self.assertIn("control.closePolicy & Popup.CloseOnEscape", dialog)
        button = (qml / "components" / "AppButton.qml").read_text(encoding="utf-8")
        self.assertIn("HoverHandler { cursorShape:", button)
        self.assertNotIn("MouseArea", button)

    def test_file_drop_targets_are_separate_and_do_not_add_polling(self) -> None:
        qml_root = Path(__file__).resolve().parents[1] / "hr_toolkit" / "gui_qt" / "qml"
        source = (qml_root / "Main.qml").read_text(encoding="utf-8")
        target = (qml_root / "components" / "FileDropTarget.qml").read_text(encoding="utf-8")
        for name in ("primaryInputDropTarget", "supportInputDropTarget", "continueInputButton", "clearInputsButton"):
            self.assertIn('objectName: "' + name + '"', source)
        self.assertIn('backend: controller; role: "input"', source)
        self.assertIn('backend: controller; role: "support"', source)
        self.assertIn("controller.appendInputFiles()", source)
        self.assertIn("controller.appendInputFolder()", source)
        self.assertIn("drop.accept(Qt.CopyAction)", target)
        self.assertIn("dropTarget.enteredContext === dropTarget.contextKey", target)
        self.assertIn("beginDropPreview(dropTarget.role, drag.urls)", target)
        self.assertIn("finishDropPreview(dropTarget.feedback.token, dropTarget.role, drop.urls)", target)
        self.assertNotIn("addDroppedUrls", target)
        self.assertNotIn("Timer {", target)
        self.assertNotIn("ShaderEffect", target)

    def test_live_resize_keeps_layout_breakpoints_and_workspace_stable(self) -> None:
        qml_path = (
            Path(__file__).resolve().parents[1]
            / "hr_toolkit"
            / "gui_qt"
            / "qml"
            / "Main.qml"
        )
        source = qml_path.read_text(encoding="utf-8")

        # The core follows its allocated pane continuously, with no window-wide
        # inset breakpoint or overlay workspace popup.
        self.assertNotIn("wideContentInsets", source)
        self.assertIn("(mainPane.width - 480) / 8", source)
        self.assertIn("(mainPane.width - 480) / 5", source)
        self.assertIn("if (width <= 980) sidebar.pinned = false", source)
        self.assertIn("Layout.preferredWidth: sidebar.reservedWidth", source)
        self.assertIn("keepOpen: projectMenu.opened", source)
        self.assertNotIn("Behavior on Layout.preferredWidth", source)
        self.assertIn(
            "anchors.leftMargin: Math.max(12, Math.min(28, (mainPane.width - 480) / 8))",
            source,
        )
        self.assertIn("readonly property int contentMaxWidth: 820", source)
        chrome = (qml_path.parent / "components" / "WindowChrome.qml").read_text(encoding="utf-8")
        self.assertIn('objectName: "workspaceToggleButton"', chrome)
        self.assertIn("workspaceAvailable: controller.hasProject", source)
        self.assertIn("workspaceExpanded: workspaceDrawer.opened", source)
        self.assertIn("workspacePanelLeft: workspaceDrawer.x", source)
        self.assertIn("enabled: chrome.workspaceAvailable || chrome.workspaceExpanded", chrome)
        self.assertIn("onClicked: chrome.workspaceToggleRequested()", chrome)
        self.assertIn("onWorkspaceToggleRequested:", source)
        self.assertIn("if (controller.workspaceExpanded) workspaceDrawer.close()", source)
        self.assertIn("controller.setWorkspaceExpanded(true)", source)
        self.assertIn("workspaceDrawer.open()", source)
        self.assertIn('objectName: "runButton"', source)
        self.assertNotIn('objectName: "workspaceButtonMouse"', source)
        self.assertNotIn('text: "项\\n目\\n文\\n件"', source)
        self.assertIn("enabled: controller.busy || (!controller.workspaceBusy && !controller.updateBlocksTools && !controller.selectionChecking)", source)
        self.assertIn("text: controller.updateBlockMessage", source)
        self.assertNotIn("UpdateProgressDialog {", source)
        self.assertIn("readonly property int preferredWindowWidth: 1600", source)
        self.assertIn("readonly property int preferredWindowHeight: 900", source)
        self.assertIn("Math.min(Screen.width, Screen.desktopAvailableWidth)", source)
        self.assertIn("Math.min(Screen.height, Screen.desktopAvailableHeight)", source)
        self.assertIn("currentScreenAvailableWidth - initialWindowMargin", source)
        self.assertIn("currentScreenAvailableHeight - initialWindowMargin", source)
        # The open project-files panel must follow every native resize frame;
        # dialogs that are not being dragged can keep settled dimensions.
        self.assertIn("WorkspaceSidePanel {", source)
        self.assertIn("parent: workspaceLayout", source)
        self.assertIn("liveAvailableWidth: workspaceLayout.width - sidebar.reservedWidth", source)
        self.assertIn("height: Math.max(0, workspaceDrawer.height - 16)", source)
        panel = (qml_path.parent / "components" / "WorkspaceSidePanel.qml").read_text(encoding="utf-8")
        self.assertIn("restoreThreshold: collapseThreshold + 80", panel)
        self.assertIn("Layout.preferredWidth: reservedWidth", panel)
        self.assertIn("Behavior on reveal", panel)
        self.assertNotIn("settledWidth", panel)
        self.assertIn("chrome.width - chrome.workspacePanelLeft + 10", chrome)
        self.assertNotIn("width: Math.min(340, root.settledWidth - 24)", source)
        self.assertNotIn("Math.max(360, root.width * 0.38)", source)
        self.assertIn("enter: Transition {}", source)
        self.assertIn("exit: Transition {}", source)
        # Settled-width timer defers layout during native resize
        self.assertIn("settledWidth", source)
        self.assertIn("settleTimer", source)
        self.assertIn('objectName: "sidebarProjectCard"', source)
        self.assertIn('readonly property bool showLegacyHistoryEntry: false', source)
        self.assertIn('objectName: "runLogIconButton"', source)
        self.assertIn('ToolTip.text: "打开运行日志"', source)
        self.assertIn("model: controller.tutorialGroups", source)
        self.assertIn("workspaceList.positionViewAtIndex(safeRow, ListView.Contain)", source)

    def test_windows_keeps_native_frame_and_separate_panel_controls(self) -> None:
        qml_dir = Path(__file__).resolve().parents[1] / "hr_toolkit" / "gui_qt" / "qml"
        source = (qml_dir / "Main.qml").read_text(encoding="utf-8")
        chrome = (qml_dir / "components" / "WindowChrome.qml").read_text(encoding="utf-8")
        self.assertIn("flags: Qt.Window", source)
        self.assertNotIn("Qt.FramelessWindowHint", source)
        self.assertNotIn("WindowResizeEdges {", source)
        self.assertIn('nativeWindows: Qt.platform.os === "windows"', source)
        self.assertIn("systemButtons: false", source)
        self.assertIn("y: edgeInset", source)
        self.assertIn("chrome.nativeMac ? 82 : chrome.nativeWindows", chrome)
        self.assertIn("chrome.sidebar.pinned ? Math.max(16, chrome.sidebar.width - width - 16) : 16", chrome)
        self.assertIn("chrome.nativeMac || chrome.nativeWindows ? 5 : 9", chrome)
        bootstrap = (qml_dir.parent / "main.py").read_text(encoding="utf-8")
        self.assertIn("app.setWindowIcon(_application_icon())", bootstrap)
        self.assertIn("root_window.setIcon(app.windowIcon())", bootstrap)
        self.assertIn('title: "HR Workbench v" + controller.appVersion', source)

    def test_qt_is_the_default_desktop_renderer(self) -> None:
        with patch.dict(os.environ, {}, clear=False):
            os.environ.pop("HR_TOOLKIT_RENDERER", None)
            with patch("hr_toolkit.gui_qt.main", return_value=0) as qt_main:
                self.assertEqual(hr_toolkit_app._run_desktop(), 0)
        qt_main.assert_called_once_with()

    def test_launcher_main_dispatches_software_rendering_flag(self) -> None:
        from hr_toolkit import launcher

        with patch.dict(os.environ, {}, clear=True):
            with patch("hr_toolkit.launcher._run_desktop", return_value=0) as run_desktop:
                code = launcher.main(["--software-rendering"])
                self.assertEqual(code, 0)
                self.assertEqual(os.environ.get("HR_TOOLKIT_QT_SOFTWARE_RENDER"), "1")
                run_desktop.assert_called_once_with()

    def test_launcher_main_routes_cli_without_qt(self) -> None:
        from hr_toolkit import launcher

        with patch("hr_toolkit.cli.main", return_value=0) as cli_main:
            with patch("hr_toolkit.launcher._run_desktop") as run_desktop:
                code = launcher.main(["--help"])
                self.assertEqual(code, 0)
                cli_main.assert_called_once_with()
                run_desktop.assert_not_called()

    def test_missing_qt_runtime_reports_instructions_and_exits_code_2(self) -> None:
        from hr_toolkit import launcher

        missing_qt = ImportError("No module named 'shiboken6'", name="shiboken6")
        with patch("hr_toolkit.gui_qt.main", side_effect=missing_qt):
            with self.assertRaises(launcher.DesktopRuntimeUnavailable) as raised:
                launcher._run_desktop()

        self.assertIn("shiboken6", str(raised.exception))
        self.assertIn("requirements-gui.txt", str(raised.exception))

        # Test main() prints to stderr and returns code 2
        with patch("hr_toolkit.launcher._run_desktop", side_effect=launcher.DesktopRuntimeUnavailable("missing")):
            code = launcher.main([])
            self.assertEqual(code, 2)

    def test_non_qt_import_failure_is_not_misreported_as_missing_qt(self) -> None:
        missing_core = ImportError("No module named 'openpyxl'", name="openpyxl")

        with patch.dict(os.environ, {}, clear=False):
            os.environ.pop("HR_TOOLKIT_RENDERER", None)
            with patch("hr_toolkit.gui_qt.main", side_effect=missing_core):
                with self.assertRaises(ImportError) as raised:
                    hr_toolkit_app._run_desktop()

        self.assertIs(raised.exception, missing_core)

    def test_win7_source_install_uses_the_locked_qt5_constraints(self) -> None:
        with patch.object(hr_toolkit_app.sys, "platform", "win32"):
            with patch.object(hr_toolkit_app.sys, "version_info", (3, 8, 10)):
                command = hr_toolkit_app._qt_install_command()

        self.assertIn("requirements-gui.txt", command)
        self.assertIn("constraints/python38-win7.txt", command)


if __name__ == "__main__":
    unittest.main()
