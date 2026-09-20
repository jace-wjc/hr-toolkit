"""Exercise the real virtualized rename dialog without touching business files."""
from __future__ import annotations
import os
from pathlib import Path
import sys
import time
os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
os.environ.setdefault('QT_QUICK_BACKEND', 'software')
os.environ.setdefault('QT_QUICK_CONTROLS_STYLE', 'Basic')
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from hr_toolkit.gui_qt.compat import QApplication, QObject, QUrl, QT_MAJOR, Qt
from hr_toolkit.gui_qt.rename_review import RenameReview
from tests.test_rename_review import sample_plan
if QT_MAJOR == 6:
    from PySide6.QtQml import QQmlApplicationEngine
    from PySide6.QtTest import QTest
    from PySide6.QtQuick import QQuickItem
else:
    from PySide2.QtQml import QQmlApplicationEngine
    from PySide2.QtTest import QTest
    from PySide2.QtQuick import QQuickItem


def main():
    app = QApplication([])
    backend = RenameReview()
    engine = QQmlApplicationEngine()
    engine.rootContext().setContextProperty('reviewBackend', backend)
    errors = []
    engine.warnings.connect(lambda messages: errors.extend(error.toString() for error in messages))
    components = Path(__file__).resolve().parents[1] / 'hr_toolkit/gui_qt/qml/components'
    source = '''import QtQuick 2.15
import QtQuick.Controls 2.15
import "%s"
ApplicationWindow {
    width: 1200; height: 760; visible: true
    RenameReviewDialog { backend: reviewBackend }
}''' % components.as_uri()
    engine.loadData(source.encode(), QUrl.fromLocalFile(str(components / 'probe.qml')))
    assert engine.rootObjects(), errors
    window = engine.rootObjects()[0]
    dialog = window.findChild(QObject, 'renameReviewDialog')
    listview = window.findChild(QQuickItem, 'renameReviewList')
    start = time.monotonic()
    backend.load(sample_plan(5000))
    frames = 0
    deadline = time.monotonic() + 8
    while (backend.validating or frames < 12) and time.monotonic() < deadline:
        QTest.qWait(20)
        frames += 1
    assert backend.model.rowCount() == 5000
    assert dialog.property('visible')
    def nodes(item):
        return [item] + [node for child in item.childItems() for node in nodes(child)]
    rows = [item for item in nodes(listview) if item.objectName() == 'renameReviewRow']
    assert 0 < len(rows) < 30, len(rows)
    assert listview.property('contentHeight') > listview.height() * 100
    # Type through the real QML editor and keep focus across async validation.
    editor = next(item for item in nodes(listview) if item.objectName() == 'renameNameEditor')
    editor.setProperty('text', '')
    editor.forceActiveFocus()
    QTest.keyClick(window, Qt.Key_H)
    QTest.keyClick(window, Qt.Key_A)
    while backend.validating:
        QTest.qWait(20)
    assert editor.hasActiveFocus()
    QTest.keyClick(window, Qt.Key_N)
    while backend.validating:
        QTest.qWait(20)
    assert backend.model.item_at(0)['target_name'] == 'han.PDF'
    backend.moveMapping('0', 1)
    backend.editName('2', '韩信')
    while backend.validating:
        QTest.qWait(20)
    assert backend.model.item_at(2)['target_name'] == '韩信.PDF'
    backend.filterRows('4999.PDF', 'all')
    while backend.validating:
        QTest.qWait(20)
    assert backend.model.rowCount() == 1
    backend.filterRows('', 'all')
    while backend.validating:
        QTest.qWait(20)
    # The dialog must also fit the supported narrow desktop window.
    window.setWidth(760)
    window.setHeight(600)
    QTest.qWait(150)
    assert dialog.property('width') <= 760
    assert dialog.property('height') <= 600
    screenshot = os.environ.get('HR_RENAME_PROBE_SCREENSHOT')
    if screenshot:
        assert window.grabWindow().save(screenshot)
    assert not errors, errors
    print(f'rename review: 5,000 rows, {len(rows)} live delegates, editing/filtering/narrow layout OK; {time.monotonic()-start:.2f}s')
    backend.cancel()
    window.close()
    QTest.qWait(30)

if __name__ == '__main__':
    main()
