"""Activate production choice controls and check the emitted values."""
from __future__ import annotations

import os
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
os.environ.setdefault("QT_QUICK_BACKEND", "software")

from hr_toolkit.gui_qt.compat import QApplication, QObject, QQmlApplicationEngine, QT_MAJOR, QUrl, delete_qobject
from hr_toolkit.gui_qt.presentation import Presentation

if QT_MAJOR == 6:
    from PySide6.QtQml import QQmlEngine, QQmlExpression
else:
    from PySide2.QtQml import QQmlEngine, QQmlExpression


def main():
    os.environ["QT_QUICK_CONTROLS_STYLE"] = "Default" if QT_MAJOR == 5 else "Basic"
    app = QApplication([])
    presentation = Presentation()
    engine = QQmlApplicationEngine()
    engine.rootContext().setContextProperty("presentation", presentation)
    errors = []
    engine.warnings.connect(lambda messages: errors.extend(error.toString() for error in messages))
    components = ROOT / "hr_toolkit/gui_qt/qml/components"
    source = '''import QtQuick 2.15
import QtQuick.Controls 2.15
import "%s"
ApplicationWindow {
    width: 600; height: 480; visible: true
    Component.onCompleted: Ui.backend = presentation
    AppearanceDialog { backend: presentation }
    AttendanceChoiceField {
        objectName: "attendanceChoice"
        choices: ["公司默认", "杭州"]
        optionLabels: ({"公司默认": "按公司默认规则"})
    }
}''' % components.as_uri()

    def activate(combo, index):
        assert combo is not None
        expression = QQmlExpression(QQmlEngine.contextForObject(combo), combo, "activated(%d)" % index)
        expression.evaluate()
        assert not expression.hasError(), expression.error().toString()
        app.processEvents()

    try:
        engine.loadData(source.encode("utf-8"), QUrl.fromLocalFile(str(components / "choice-probe.qml")))
        assert engine.rootObjects(), errors
        window = engine.rootObjects()[0]
        theme = window.findChild(QObject, "themeSelector")
        language = window.findChild(QObject, "languageSelector")
        field = window.findChild(QObject, "attendanceChoice")
        pickers = [item for item in field.findChildren(QObject) if item.inherits("QQuickComboBox")]
        assert len(pickers) == 1, len(pickers)
        for index in (1, 0):
            activate(theme, index)
            assert presentation.theme == presentation.themeOptions[index]["value"]
            activate(language, index)
            assert presentation.language == presentation.languageOptions[index]["value"]
            for choice_index, expected in ((0, "公司默认"), (1, "杭州"), (0, "公司默认")):
                activate(pickers[0], choice_index)
                assert field.property("value") == expected, field.property("value")
        assert not errors, errors
        print("choice activation: theme, language and raw attendance values OK")
    finally:
        delete_qobject(engine)
        presentation.setLanguage("en_US")


if __name__ == "__main__":
    main()
