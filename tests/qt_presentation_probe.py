"""Render every tool and review dialogs in both themes/locales, in isolation."""
from __future__ import annotations

import copy
import json
import os
from pathlib import Path
import re
import sys
import tempfile
import time
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
os.environ.setdefault('QT_QUICK_BACKEND', 'software')
os.environ.setdefault('QT_QUICK_CONTROLS_STYLE', 'Basic')
os.environ['HR_TOOLKIT_SKIP_UPDATE'] = '1'
from hr_toolkit import __version__
from hr_toolkit.gui_qt.compat import QApplication, QQmlApplicationEngine, QUrl, QT_MAJOR, Qt, QObject, delete_qobject
from hr_toolkit.gui_qt.controller import AppController, NAV_GROUPS
from hr_toolkit.gui_qt.form_specs import variants_for
from tests.test_rename_review import sample_plan
if QT_MAJOR == 6:
    from PySide6.QtQml import QQmlExpression, QQmlEngine
    from PySide6.QtQuick import QQuickItem
    from PySide6.QtTest import QTest
    from PySide6.QtWidgets import QFileDialog, QPushButton
    from PySide6.QtCore import QEventLoop, QTimer
else:
    from PySide2.QtQml import QQmlExpression, QQmlEngine
    from PySide2.QtQuick import QQuickItem
    from PySide2.QtTest import QTest
    from PySide2.QtWidgets import QFileDialog, QPushButton
    from PySide2.QtCore import QEventLoop, QTimer


def wait(milliseconds):
    # QTest.qWait is not exposed by the Win7 PySide2 release.
    loop = QEventLoop()
    QTimer.singleShot(milliseconds, loop.quit)
    (getattr(loop, "exec", None) or loop.exec_)()


def main():
    os.environ['QT_QUICK_CONTROLS_STYLE'] = 'Default' if QT_MAJOR == 5 else 'Basic'
    app = QApplication([])
    errors = []
    with tempfile.TemporaryDirectory() as temp:
        settings = Path(temp) / 'workspace-ui.json'
        settings.write_text(json.dumps({'release_notes_seen_version': __version__}), encoding='utf-8')
        with patch.object(AppController, '_settings_path', return_value=settings):
            controller = AppController()
            engine = QQmlApplicationEngine()
            engine.rootContext().setContextProperty('controller', controller)
            engine.warnings.connect(lambda messages: errors.extend(item.toString() for item in messages))
            engine.load(QUrl.fromLocalFile(str(ROOT / 'hr_toolkit/gui_qt/qml/Main.qml')))
            assert engine.rootObjects(), errors
            window = engine.rootObjects()[0]
            window.setWidth(1280); window.setHeight(900)
            deadline = time.monotonic() + 8
            while controller._startup_loading and time.monotonic() < deadline:
                wait(20)
            assert not controller._startup_loading

            def js(expression):
                value = QQmlExpression(QQmlEngine.contextForObject(window), window, expression)
                result = value.evaluate()
                assert not value.hasError(), value.error().toString()
                return result[0] if isinstance(result, tuple) else result

            def nodes(item):
                yield item
                if isinstance(item, QQuickItem):
                    for child in item.childItems():
                        yield from nodes(child)

            def visible_texts():
                result = []
                for item in nodes(window.contentItem()):
                    if not item.isVisible():
                        continue
                    classname = item.metaObject().className()
                    if 'QQuickText' in classname or 'QQuickLabel' in classname:
                        text = item.property('text')
                        if isinstance(text, str) and text:
                            result.append(text)
                return result

            def english_complete(where, allowed=()):
                leftovers = []
                for text in visible_texts():
                    for data in sorted(allowed, key=len, reverse=True):
                        text = text.replace(data, '')
                    if re.search('[\u3400-\u9fff]', text):
                        leftovers.append(text)
                assert not leftovers, (where, leftovers)

            settings_button = window.findChild(QObject, 'appearanceButton')
            position = settings_button.mapToScene(settings_button.boundingRect().center()).toPoint()
            QTest.mouseClick(window, Qt.LeftButton, Qt.NoModifier, position)
            wait(30)
            assert js('appearanceDialog.opened'), 'Settings button is covered by window drag area'
            js('appearanceDialog.close()')
            timings = []
            for theme in ('light', 'dark', 'light', 'dark'):
                for locale in ('en_US', 'zh_CN'):
                    started = time.perf_counter()
                    controller.presentation.setTheme(theme)
                    controller.presentation.setLanguage(locale)
                    wait(20)
                    timings.append(time.perf_counter() - started)
                    assert window.color().name() == ('#181d23' if theme == 'dark' else '#fcfcfb')
                    for _, tools in NAV_GROUPS:
                        for tool, _ in tools:
                            controller.selectTool(tool)
                            for spec in variants_for(tool):
                                controller.selectVariant(spec.variant)
                                wait(15)
                                if locale == 'en_US':
                                    english_complete((theme, tool, spec.variant))
                    controller.selectTool('folder_rename')
                    for mode in ('append', 'remove', 'replace', 'replace_text', 'excel'):
                        controller.setFieldValue('rename_mode', mode)
                        for kind in ('folder', 'pdf', 'image', 'document', 'all'):
                            controller.setFieldValue('file_type', kind)
                            before = copy.deepcopy(controller.formFields)
                            controller.presentation.setLanguage('zh_CN' if locale == 'en_US' else 'en_US')
                            controller.presentation.setLanguage(locale)
                            assert controller.formFields == before, 'Localization changed business form data'
                        wait(15)
                        if locale == 'en_US':
                            english_complete((theme, mode))
                    js('appearanceDialog.open()'); wait(30)
                    if locale == 'en_US':
                        english_complete('settings')
                    if os.environ.get('HR_PRESENTATION_SCREENSHOTS'):
                        destination = Path(os.environ['HR_PRESENTATION_SCREENSHOTS'])
                        destination.mkdir(parents=True, exist_ok=True)
                        window.grabWindow().save(str(destination / ('settings-' + theme + '-' + locale + '.png')))
                    js('appearanceDialog.close()')
                    if os.environ.get('HR_PRESENTATION_SCREENSHOTS'):
                        destination = Path(os.environ['HR_PRESENTATION_SCREENSHOTS'])
                        destination.mkdir(parents=True, exist_ok=True)
                        window.grabWindow().save(str(destination / (theme + '-' + locale + '.png')))

            controller.presentation.setLanguage('en_US')
            for dialog in ('helpDialog', 'regionCodeDialog', 'createProjectDialog', 'projectMenu'):
                js(dialog + '.open()'); wait(50)
                english_complete(dialog, ('温州', '杭州', '宁波', '其他地区'))
                js(dialog + '.close()')
            js('updatePromptDialog.showPrompt({available: false, currentVersion: "0.9.13"})')
            wait(40)
            english_complete('no update message')
            js('updatePromptDialog.close()')
            controller.notificationRequested.emit('提示', '目标名称重复', 'warning')
            wait(30); english_complete('notification'); js('notificationDialog.close()')
            controller.confirmationRequested.emit('确认', '原文件不会被修改。', 'test')
            wait(30); english_complete('confirmation'); js('confirmationDialog.close()')
            controller.releaseNotesRequested.emit({'currentVersion': __version__, 'entries': [{'version': __version__, 'notes': ['功能更新', '- 新增替换指定文字，支持按文件类型筛选。']}]})
            wait(30)
            # The fixture's arbitrary external release note is not an application catalog entry.
            english_complete('release notes', ('新增替换指定文字，支持按文件类型筛选。',))
            js('releaseNotesDialog.close()')
            from hr_toolkit.common.template_mapping import catalog
            payload = {'tool': 'data_statistics', 'file': '员工.xlsx',
                       'roles': [{'key': 'attendance_summary', **catalog('data_statistics')['attendance_summary']}],
                       'sheets': [{'name': '考勤表', 'rows': [['姓名', '应出勤天数'], ['张三', '20']]}]}
            controller.selectTool('data_statistics')
            js('templateChoiceDialog.showData(' + json.dumps(payload, ensure_ascii=False) + ')')
            wait(60)
            english_complete('column mapping', ('员工.xlsx', '考勤表', '姓名', '应出勤天数', '张三'))
            js('templateChoiceDialog.close()')
            js('templateChoiceDialog.showRules(controller.templateRuleSections)')
            wait(60)
            aliases = tuple(value for section in controller.templateRuleSections for value in section.get('options', []) + section.get('builtins', []) + section.get('selected', []))
            english_complete('template rules', aliases)
            js('templateChoiceDialog.close()')
            controller.selectTool('folder_rename')
            plan = sample_plan(5000)
            controller.renameReview.load(plan)
            deadline = time.monotonic() + 8
            while controller.renameReview.validating and time.monotonic() < deadline:
                wait(20)
            wait(50)
            english_complete('rename review', ('姓名',))
            rows = [item for item in nodes(window.contentItem()) if item.objectName() == 'renameReviewRow']
            assert 0 < len(rows) < 30, len(rows)
            if os.environ.get('HR_PRESENTATION_SCREENSHOTS'):
                window.grabWindow().save(str(Path(os.environ['HR_PRESENTATION_SCREENSHOTS']) / 'rename-review-dark-en.png'))
            before = copy.deepcopy(controller.renameReview.model.item_at(0))
            for i in range(10):
                controller.presentation.setTheme('light' if i % 2 else 'dark')
                controller.presentation.setLanguage('zh_CN' if i % 2 else 'en_US')
                wait(10)
            assert controller.renameReview.model.item_at(0) == before
            controller.renameReview.cancel()
            window.setWidth(760); window.setHeight(600); wait(180)
            js('appearanceDialog.open()'); wait(30)
            assert js('appearanceDialog.width <= root.width')
            js('appearanceDialog.close()')
            # Qt fallback dialogs follow the app locale; native pickers use the OS locale.
            for locale, expected in [('zh_CN', '取消'), ('en_US', 'Cancel')]:
                controller.presentation.setLanguage(locale)
                picker = QFileDialog()
                picker.setOption(QFileDialog.DontUseNativeDialog)
                picker.show(); wait(20)
                captions = [button.text().replace('&', '') for button in picker.findChildren(QPushButton)]
                assert expected in captions, captions
                picker.close(); delete_qobject(picker)
            controller.presentation.setTheme('dark')
            controller.presentation.setLanguage('en_US')
            from hr_toolkit.project_store import ProjectStore
            controller._project_store = ProjectStore.create(Path(temp) / 'project', '2026年9月人事月度工作01')
            controller._project_path = controller._project_store.root
            controller.projectChanged.emit()
            # Opening/restoring a project in a narrow window must clear the
            # request without changing a binding's source during evaluation.
            controller.setWorkspaceExpanded(True)
            wait(30)
            assert not controller.workspaceExpanded
            assert not js('workspaceDrawer.opened')
            assert not errors, errors
            window.setWidth(1600); window.setHeight(900)
            wait(30)
            assert not js('workspaceDrawer.opened'), 'Resize reopened the collapsed panel'
            js('sidebar.pinned = true')
            controller.selectTool('social_security')
            controller.setWorkspaceExpanded(True)
            wait(250)
            assert js('workspaceDrawer.opened'), 'Explicit project panel reopen failed'
            assert js('sidebarProjectCard.width <= sidebar.width - 24'), 'Sidebar contents overflow'
            assert js('navScroll.width <= sidebar.width - 24'), 'Sidebar navigation overflows'
            assert js('workspaceRefreshButton.contentItem.implicitWidth <= workspaceRefreshButton.availableWidth'), 'Refresh label overflows'
            assert js('appearanceButton.x + appearanceButton.width < workspaceDrawer.x'), 'Settings overlaps project panel'
            assert 'Current Project' in visible_texts()
            assert 'Current Project · Read-only' not in visible_texts()
            if os.environ.get('HR_PRESENTATION_SCREENSHOTS'):
                window.grabWindow().save(str(Path(os.environ['HR_PRESENTATION_SCREENSHOTS']) / 'fixed-dark-workspace.png'))
            # Native dialogs cannot be inspected as Qt widgets in a headless probe.
            # Check delegation and cancellation without opening a real OS picker.
            for theme in ('light', 'dark'):
                controller.presentation.setTheme(theme)
                with patch.object(QFileDialog, 'getExistingDirectory', return_value='') as picker:
                    selected = controller.presentation.file_dialog(
                        QFileDialog.getExistingDirectory, None, '选择文件夹', temp)
                    assert selected == '', 'Picker cancellation changed'
                    picker.assert_called_once_with(None, 'Select Folder', temp)
            saved = json.loads(settings.read_text(encoding='utf-8'))
            assert saved['theme'] == 'dark' and saved['language'] == 'en_US'
            assert not errors, errors
            controller._project_store.close()
            controller._project_store = None
            controller._project_path = None
            controller.close()
            delete_qobject(window); engine.deleteLater(); wait(20)
            second = AppController()
            second.start()
            deadline = time.monotonic() + 8
            while second._startup_loading and time.monotonic() < deadline:
                wait(20)
            assert second.presentation.theme == 'dark' and second.presentation.language == 'en_US'
            second.close()
            print('presentation probe OK; tools, modes, dialogs, 5000 rows, persistence; switch max %.3fs' % max(timings))


if __name__ == '__main__':
    main()
