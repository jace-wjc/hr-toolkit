"""Exercise year editing with the same QML component on Qt 5 and Qt 6."""
from __future__ import annotations

import os
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
os.environ.setdefault("QT_QUICK_BACKEND", "software")

from hr_toolkit.gui_qt.compat import QApplication, QObject, QQmlApplicationEngine, QT_MAJOR, QUrl, Qt, delete_qobject

if QT_MAJOR == 6:
    from PySide6.QtCore import QLocale
    from PySide6.QtQuick import QQuickItem
    from PySide6.QtTest import QTest
else:
    from PySide2.QtCore import QLocale
    from PySide2.QtQuick import QQuickItem
    from PySide2.QtTest import QTest


def main():
    os.environ["QT_QUICK_CONTROLS_STYLE"] = "Default" if QT_MAJOR == 5 else "Basic"
    app = QApplication([])
    engine = QQmlApplicationEngine()
    errors = []
    engine.warnings.connect(lambda messages: errors.extend(error.toString() for error in messages))
    components = ROOT / "hr_toolkit/gui_qt/qml/components"
    source = '''import QtQuick 2.15
import QtQuick.Controls 2.15
import "%s"
ApplicationWindow {
    width: 500; height: 400; visible: true
    AppDateField {
        objectName: "dateField"
        width: 180; text: "2026-11-17"
    }
}''' % components.as_uri()
    try:
        for locale in ("en_US", "zh_CN"):
            QLocale.setDefault(QLocale(locale))
            engine.loadData(source.encode(), QUrl.fromLocalFile(str(components / "date-probe.qml")))
            assert engine.rootObjects(), errors
            window = engine.rootObjects()[-1]
            try:
                field = window.findChild(QObject, "dateField")
                field.openCalendar()
                app.processEvents()
                years = [item for item in field.findChildren(QObject) if item.inherits("QQuickSpinBox")]
                assert len(years) == 1, len(years)
                year = years[0]
                editor = year.property("contentItem")
                assert isinstance(editor, QQuickItem)
                assert year.property("value") == 2026
                assert editor.property("text") == "2026", editor.property("text")
                for expected in (1, 9999, 2027):
                    editor.forceActiveFocus()
                    QTest.keyClick(window, Qt.Key_A, Qt.ControlModifier)
                    for digit in str(expected):
                        QTest.keyClick(window, ord(digit))
                    QTest.keyClick(window, Qt.Key_Return)
                    app.processEvents()
                    assert year.property("value") == expected, (locale, expected, year.property("value"))
                    assert editor.property("text") == str(expected), editor.property("text")
                    if expected in (1, 9999):
                        QTest.keyClick(window, Qt.Key_Down if expected == 1 else Qt.Key_Up)
                        app.processEvents()
                        assert year.property("value") == expected, "Year escaped calendar bounds"
                assert field.property("text") == "2026-11-17", "Browsing changed the selected date"
                assert not errors, errors
            finally:
                delete_qobject(window)
        print("date field: localized year editing, bounds and warning-free bindings OK")
    finally:
        delete_qobject(engine)


if __name__ == "__main__":
    main()
