"""Check virtual note geometry against a fully laid-out reference Column."""
from __future__ import annotations

import os
from pathlib import Path
import sys

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
os.environ.setdefault("QT_QUICK_BACKEND", "software")
os.environ.setdefault("QT_QUICK_CONTROLS_STYLE", "Basic")
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from hr_toolkit.gui_qt.compat import QApplication, QObject, QT_MAJOR, QUrl, Qt

if QT_MAJOR == 6:
    from PySide6.QtQml import QQmlComponent, QQmlEngine
    from PySide6.QtQuick import QQuickWindow
    from PySide6.QtTest import QTest
else:
    from PySide2.QtQml import QQmlComponent, QQmlEngine
    from PySide2.QtQuick import QQuickWindow
    from PySide2.QtTest import QTest


def visual_nodes(item):
    return [item] + [node for child in item.childItems() for node in visual_nodes(child)]


def main() -> None:
    application = QApplication([])
    engine = QQmlEngine()
    errors = []
    engine.warnings.connect(lambda messages: errors.extend(error.toString() for error in messages))
    component = QQmlComponent(engine)
    components = Path(__file__).resolve().parents[1] / "hr_toolkit/gui_qt/qml/components"
    source = '''import QtQuick 2.15
import QtQuick.Window 2.15
import "%s"
Window {
    width: 640; height: 380; visible: true
    property var testNotes: []
    UpdateNotesView {
        id: view; objectName: "notes"
        anchors.fill: parent; anchors.margins: 10
        notes: testNotes
    }
    Column {
        objectName: "reference"; visible: false
        width: Math.max(0, view.width - 28 - 16); spacing: 12
        Repeater {
            model: view.rows
            UpdateNotesRow {
                modelData: model.modelData
                rowIndex: index; width: parent.width
            }
        }
    }
}''' % components.as_uri()
    component.setData(source.encode(), QUrl.fromLocalFile(str(components / "probe.qml")))
    assert component.isReady(), [error.toString() for error in component.errors()]
    notes = ["功能更新" if i % 51 == 0 else ("第%d条：" % i) + "长段落需要保持精确换行。" * (i % 5 + 1)
             for i in range(1000)]
    window = component.createWithInitialProperties({"testNotes": notes})
    assert isinstance(window, QQuickWindow)
    view = window.findChild(QObject, "notes")
    reference = window.findChild(QObject, "reference")
    flick = window.findChild(QObject, "updateNotesFlickable")

    def verify():
        for _ in range(5):
            application.processEvents()
        assert abs(view.property("contentHeight") - reference.property("implicitHeight")) < 1e-6
        assert len(visual_nodes(view)) < 300, "Virtual delegates grew with total content"
        assert not errors, errors[:5]

    verify()
    for width in (360, 900, 640):
        window.setWidth(width)
        verify()
    for fraction in (0.2, 0.5, 1, 0):
        view.setProperty("contentY", max(0, view.property("contentHeight") - view.property("viewportHeight")) * fraction)
        verify()
    flick.forceActiveFocus(Qt.TabFocusReason)
    QTest.keyClick(window, Qt.Key_End)
    verify()
    assert view.property("contentY") > 0
    QTest.keyClick(window, Qt.Key_Home)
    verify()
    assert view.property("contentY") == 0
    view.setProperty("entries", [{"version": str(i), "notes": notes[:100]} for i in range(10, 0, -1)])
    view.setProperty("history", True)
    verify()
    for version in range(9, 0, -1):
        view.toggleVersion(str(version))
        verify()
    buttons = [node for node in visual_nodes(view) if node.inherits("QQuickButton") and node.isVisible()]
    assert len(buttons) == 10
    before = view.property("contentHeight")
    buttons[0].forceActiveFocus(Qt.TabFocusReason)
    QTest.keyClick(window, Qt.Key_Space)
    verify()
    assert view.property("contentHeight") < before
    view.setProperty("history", False)
    window.setProperty("testNotes", ["短内容"])
    verify()
    window.setProperty("testNotes", notes)
    verify()
    print("virtual notes: wrapping, resize, scroll, history and bounded delegates OK", flush=True)
    # This process tests rendering, not native application shutdown. Keep the
    # engine, window and reference alive through the last assertion.
    os._exit(0)


if __name__ == "__main__":
    main()
