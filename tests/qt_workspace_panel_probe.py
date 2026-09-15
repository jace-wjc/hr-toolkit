"""Exercise production three-column geometry without opening saved projects."""
from __future__ import annotations
import os
from pathlib import Path
import sys
import json
import tempfile

os.environ.update(QT_QPA_PLATFORM="offscreen", QT_QUICK_BACKEND="software", QT_QUICK_CONTROLS_STYLE="Basic", HR_TOOLKIT_SKIP_UPDATE="1")
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from hr_toolkit.gui_qt.compat import QApplication, QObject, Property, Slot, QUrl, QT_MAJOR, Qt
from hr_toolkit.gui_qt.controller import AppController
if QT_MAJOR == 6:
    from PySide6.QtCore import QEventLoop, QPoint, QPointF, QTimer
    from PySide6.QtQml import QQmlApplicationEngine
    from PySide6.QtQuick import QQuickWindow
    from PySide6.QtTest import QTest
else:
    from PySide2.QtCore import QEventLoop, QPoint, QPointF, QTimer
    from PySide2.QtQml import QQmlApplicationEngine
    from PySide2.QtQuick import QQuickWindow
    from PySide2.QtTest import QTest

os.environ["QT_QUICK_CONTROLS_STYLE"] = "Default" if QT_MAJOR == 5 else "Basic"


def wait_for_events(milliseconds):
    # PySide2 5.15.2.1 does not expose QTest.qWait. A local event loop keeps
    # animations/timers running on both Qt versions without blocking sleep.
    loop = QEventLoop()
    QTimer.singleShot(milliseconds, loop.quit)
    execute = getattr(loop, "exec", None) or loop.exec_
    execute()


class Controller(AppController):
    @Slot()
    def start(self):
        pass

    @Property(bool, notify=AppController.projectChanged)
    def hasProject(self):
        return True

    @Property(str, notify=AppController.projectChanged)
    def projectName(self):
        return "2026年9月人事月度工作"


def main():
    application = QApplication([])
    controller = Controller()
    controller._save_workspace_preferences = lambda: True
    controller.refreshWorkspace = lambda: None
    controller._workspace_generation = 1
    controller._apply_workspace_items(1, [{"path": "/virtual/" + str(i), "name": "项目文件%d.xlsx" % i,
        "isDir": False, "depth": 0, "expanded": False, "hasChildren": False, "detail": "XLSX"} for i in range(100)])
    engine = QQmlApplicationEngine()
    errors = []
    engine.warnings.connect(lambda messages: errors.extend(error.toString() for error in messages))
    engine.rootContext().setContextProperty("controller", controller)
    engine.setInitialProperties({"width": 1400, "height": 820})
    qml = Path(__file__).resolve().parents[1] / "hr_toolkit/gui_qt/qml/Main.qml"
    engine.load(QUrl.fromLocalFile(str(qml)))
    assert engine.rootObjects(), errors
    root = engine.rootObjects()[0]
    panel = root.findChild(QObject, "workspaceDrawer")
    pane = root.findChild(QObject, "mainPane")
    sidebar = root.findChild(QObject, "sidebar")
    scroll = root.findChild(QObject, "mainScroll")
    content = root.findChild(QObject, "contentColumn")
    chrome_button = root.findChild(QObject, "workspaceToggleButton")
    form_scroll = root.findChild(QObject, "formScroll")
    frames = []

    def nodes(item):
        return [item] + [node for child in item.childItems() for node in nodes(child)]

    def check_controls():
        for item in nodes(pane):
            ancestor = item.parentItem()
            in_scrolling_form = False
            while ancestor:
                if ancestor == form_scroll and form_scroll.property("needsHorizontalScroll"):
                    in_scrolling_form = True
                    break
                ancestor = ancestor.parentItem()
            if in_scrolling_form:
                column = root.findChild(QObject, "formColumn")
                if item.isVisible() and item.inherits("QQuickControl"):
                    x = item.mapToItem(column, QPointF(0, 0)).x()
                    assert x >= -1 and x + item.width() <= column.width() + 1
                continue  # Offscreen children remain reachable by horizontal scrolling.
            if item.isVisible() and item.inherits("QQuickControl"):
                x = item.mapToItem(pane, QPointF(0, 0)).x()
                assert x >= -1 and x + item.width() <= pane.width() + 1, (
                    controller.currentTool, root.width(), item.metaObject().className(),
                    item.property("text"), x, item.width(), pane.width())

    def sample(duration=230):
        widths = []
        for _ in range(max(1, duration // 10)):
            wait_for_events(10)
            application.processEvents()
            assert pane.width() >= 0 and panel.width() >= 0
            assert panel.x() >= pane.x() + pane.width() - 1.5, "Right pane overlaps the core"
            assert abs(pane.x() + pane.width() + panel.width() - root.width()) < 2
            assert content.width() <= scroll.property("availableWidth") + 1
            if panel.width() > 1:
                assert pane.width() >= 639, "Right pane squeezed the core below its budget"
            assert chrome_button.x() + chrome_button.width() <= panel.x() + 1
            widths.append(panel.width())
        assert not errors, errors[:8]
        frames.append({"window": root.width(), "center": pane.width(), "right": panel.width(),
                       "opened": panel.property("opened"), "requested": controller.workspaceExpanded,
                       "tool": controller.currentTool})
        return widths

    sample(30)
    assert panel.width() == 0
    # The Windows failure was emitted by this initially hidden dialog. Keep
    # warnings fatal and also exercise its wrapped/scrolling content explicitly.
    update_prompt = root.findChild(QObject, "updatePromptDialog")
    for prompt in (
        {"available": False, "currentVersion": "0.9.7"},
        {"available": True, "version": "0.9.8", "currentVersion": "0.9.7", "notes": ["功能更新", "界面体验优化"]},
        {"available": True, "version": "0.9.8", "currentVersion": "0.9.7", "manual": True,
         "mandatory": True, "notes": ["用于检查更新说明换行及滚动。" * 6] * 80},
        {"available": True, "version": "0.9.8", "currentVersion": "0.9.7",
         "notes": ["用于检查更新说明换行及滚动。" * 6] * 80},
    ):
        update_prompt.showPrompt(prompt)
        for width, window_height in ((760, 600), (760, 820), (1400, 820)):
            root.setWidth(width)
            root.setHeight(window_height)
            sample(50)
            height = update_prompt.property("height")
            assert 0 < height <= min(520 if prompt["available"] else 320, root.height() * 0.84)
            sample(30)
            assert abs(update_prompt.property("height") - height) < 1
            primary = update_prompt.findChild(QObject, "updatePromptPrimary")
            assert primary is not None and primary.isVisible()
            body = update_prompt.property("contentItem")
            footer = update_prompt.property("footer")
            footer_top = footer.mapToScene(QPointF(0, 0)).y()
            for section in body.childItems():
                if section.isVisible():
                    bottom = section.y() + section.height()
                    assert bottom <= body.height() + 1, (
                        "Update prompt content exceeds its body", width, window_height,
                        section.metaObject().className(), bottom, body.height())
                    assert section.mapToScene(QPointF(0, section.height())).y() <= footer_top, (
                        "Update prompt content overlaps its buttons", width, window_height)
        update_prompt.close()
    sample(30)
    QTest.mouseClick(root, Qt.LeftButton, Qt.NoModifier,
        QPoint(int(chrome_button.x() + chrome_button.width() / 2), int(chrome_button.y() + chrome_button.height() / 2)))
    opening = sample()
    assert 320 <= panel.property("panelWidth") <= 360
    assert any(0 < width < opening[-1] - 1 for width in opening)
    assert all(a <= b + 1 for a, b in zip(opening, opening[1:]))
    root.setWidth(1240); sample()
    assert panel.property("opened")
    root.setWidth(1220); sample()
    assert not panel.property("opened") and controller.workspaceExpanded
    for width in (1230, 1280, 1226, 1298, 1280):
        root.setWidth(width); sample(30)
        assert not panel.property("opened"), "Hysteresis failed"
    root.setWidth(1304); sample()
    assert panel.property("opened")
    root.setWidth(760); root.setHeight(600); sample()
    assert panel.width() == 0 and controller.workspaceExpanded
    root.setWidth(1400); root.setHeight(820); sample()
    assert panel.property("opened")
    closing = None
    panel.close(); closing = sample()
    assert all(a >= b - 1 for a, b in zip(closing, closing[1:]))
    for width in (760, 1600):
        root.setWidth(width); sample()
        assert panel.width() == 0 and not controller.workspaceExpanded
    root.setWidth(1100); sidebar.setProperty("pinned", False)
    panel.open(); sample()
    assert panel.property("opened")
    sidebar.setProperty("pinned", True); sample()
    assert not panel.property("opened") and controller.workspaceExpanded
    sidebar.setProperty("pinned", False); sample()
    assert panel.property("opened")
    search = root.findChild(QObject, "workspaceSearchField")
    search.forceActiveFocus(Qt.TabFocusReason)
    QTest.keyClick(root, Qt.Key_Escape); sample()
    assert not controller.workspaceExpanded

    # Core forms use the same responsive width while the panel animates.
    sidebar.setProperty("pinned", True)
    output = Path(tempfile.mkdtemp(prefix="hr-workspace-responsive-"))
    tools = [item["id"] for group in controller.navGroups for item in group["items"]]
    for tool in tools:
        controller.selectTool(tool)
        controller._input_model.set_items([{"name": "待处理的较长文件名%d.xlsx" % i,
            "path": "/virtual/input/%d.xlsx" % i, "kind": "xlsx", "detail": "测试资料"} for i in range(100)])
        controller._log_model.append_batch([{"time": "12:00", "text": "用于检查窄窗口日志换行与滚动区域的长内容。" * 8,
            "level": "info"} for _ in range(5)])
        panel.open()
        for width in (1400, 1240, 760):
            root.setWidth(width); sample()
            check_controls()
            picture = root.grabWindow()
            assert not picture.isNull()
            picture.save(str(output / (tool + "-" + str(width) + ".png")))
    (output / "geometry.json").write_text(json.dumps(frames, ensure_ascii=False, indent=2), encoding="utf-8")
    print("responsive workspace: non-overlap, animation, hysteresis, restore, focus and core widths OK", flush=True)
    print(str(output), flush=True)
    controller.close()
    # This isolated process checks layout, not native application shutdown.
    os._exit(0)


if __name__ == "__main__":
    main()
