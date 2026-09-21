"""Focused contracts for display-only theme and locale preferences."""
from __future__ import annotations

import json
import os
from pathlib import Path
import re
import subprocess
import sys
import unittest
from types import ModuleType
from unittest.mock import Mock, patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
try:
    from hr_toolkit.gui_qt.compat import QCoreApplication, QFileDialog
    from hr_toolkit.gui_qt.presentation import Presentation
except ImportError:
    Presentation = None

ROOT = Path(__file__).resolve().parents[1]


@unittest.skipIf(Presentation is None, "Qt is not installed")
class PresentationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QCoreApplication.instance() or QCoreApplication([])

    def test_preferences_validate_and_do_not_override_early_user_choice(self):
        view = Presentation()
        self.assertEqual((view.theme, view.language), ("light", "zh_CN"))
        view.restore("unknown", "unknown")
        self.assertEqual((view.theme, view.language), ("light", "zh_CN"))
        view.setTheme("dark")
        view.setLanguage("en_US")
        view.restore("light", "zh_CN")
        view.setTheme("unknown")
        view.setLanguage("unknown")
        self.assertEqual((view.theme, view.language), ("dark", "en_US"))
        view.setTheme("light")
        view.setLanguage("zh_CN")

    def test_catalog_placeholders_are_valid_and_cover_form_labels(self):
        from hr_toolkit.gui_qt.translations_en import MESSAGES
        from hr_toolkit.gui_qt.form_specs import _SPEC_MAP
        view = Presentation()
        for source, target in MESSAGES.items():
            with self.subTest(source=source):
                slots = set(re.findall(r"\{\d+\}", source))
                self.assertEqual(slots, set(re.findall(r"\{\d+\}", target)))
                self.assertEqual(view.translate(source, "zh_CN"), source)
                self.assertEqual(view.translate(source, "en_US"), target)
                if slots:
                    values = ["VALUE" + str(i) for i in range(max(int(s[1:-1]) for s in slots) + 1)]
                    message = source.format(*values)
                    translated = view.translate(message, "en_US")
                    self.assertFalse(re.search(r"[\u3400-\u9fff]", translated), translated)
                    for value in values:
                        self.assertIn(value, translated)
        def strings(value):
            if isinstance(value, str):
                yield value
            elif isinstance(value, dict):
                for item in value.values():
                    yield from strings(item)
            elif isinstance(value, (list, tuple)):
                for item in value:
                    yield from strings(item)
        for spec in _SPEC_MAP.values():
            for source in strings(spec.as_dict()):
                if re.search(r"[\u3400-\u9fff]", source):
                    self.assertNotEqual(view.translate(source, "en_US"), source, source)

    def test_display_translation_preserves_data_and_nested_messages(self):
        view = Presentation()
        from hr_toolkit.gui_qt.form_specs import SPECS
        for spec in SPECS:
            for instruction in (spec.input_drop_title, spec.support_button):
                if instruction:
                    message = '请先' + instruction + '。'
                    self.assertEqual(view.translate(message, 'zh_CN'), message)
                    self.assertNotRegex(view.translate(message, 'en_US'), r'[\u3400-\u9fff]')
        self.assertEqual(view.translate('请先选择缴费清单、压缩包或文件夹。', 'en_US'),
                         'Select payment lists, archives, or a folder first.')
        self.assertEqual(view.translate('请先选择考勤 / 周报 / 月报文件、压缩包或文件夹。', 'en_US'),
                         'Select attendance files, weekly or monthly reports, archives, or a folder first.')
        for source in ("Zhang San.pdf", "王五-合同.PDF", r"C:\档案\张三.xlsx"):
            self.assertEqual(view.translate(source, "en_US"), source)
            self.assertEqual(view.translate("文件：" + source, "en_US"), "File: " + source)
        self.assertEqual(view.translate("原表内容示例：姓名 · 张三", "en_US"), "Source sample: 姓名 · 张三")
        self.assertEqual(view.translate("上次运行 09:20 · 成功", "en_US"), "Last run 09:20 · Success")
        self.assertEqual(view.translate("处理失败：目标名称重复", "en_US"), "Processing failed: Duplicate target name")
        nested = view.translate("张三.pdf 改名失败：文件扩展名必须保持不变", "en_US")
        self.assertIn("张三.pdf", nested)
        self.assertNotRegex(nested.replace("张三.pdf", ""), r"[\u3400-\u9fff]")

    def test_file_picker_uses_current_language_and_preserves_paths(self):
        view = Presentation()
        view.setLanguage("en_US")
        picker = Mock(return_value=("C:/资料/姓名.xlsx", ""))
        result = view.file_dialog(picker, None, "选择文件", "C:/资料", "Excel 文件 (*.xlsx *.xls)")
        self.assertEqual(result[0], "C:/资料/姓名.xlsx")
        self.assertEqual(picker.call_args[0][2], "C:/资料")
        self.assertEqual(picker.call_args[1]["options"], QFileDialog.DontUseNativeDialog)
        self.assertNotRegex(picker.call_args[0][1], r"[\u3400-\u9fff]")

    def test_qt_catalog_layouts_load_and_unload_on_language_switch(self):
        from hr_toolkit.gui_qt import presentation
        # Model the actual catalog names shipped by the pinned Qt5 Windows
        # wheel and modern Qt6 wheels without requiring both bindings at once.
        for major, catalog in ((5, 'qt_zh_CN'), (6, 'qtbase_zh_CN')):
            with self.subTest(qt=major):
                view = Presentation()
                app = Mock()
                translators = []

                def translator_factory(parent):
                    translator = Mock()
                    translator.load.side_effect = lambda name, *args: name == catalog or name.endswith('qt_buttons_zh_CN.qm')
                    translators.append(translator)
                    return translator

                library = Mock()
                library.location.return_value = library.path.return_value = 'bundled-translations'
                package = 'PySide2' if major == 5 else 'PySide6'
                qt_core = ModuleType(package + '.QtCore')
                qt_core.QLibraryInfo = library
                qt_core.QTranslator = translator_factory
                qt_package = ModuleType(package)
                qt_package.__path__ = []
                qt_package.QtCore = qt_core
                with patch.object(presentation, 'QT_MAJOR', major), \
                     patch.object(presentation, 'QTranslator', side_effect=translator_factory), \
                     patch.object(presentation, 'QApplication') as application, \
                     patch.dict(sys.modules, {
                         package: qt_package,
                         package + '.QtCore': qt_core,
                     }):
                    application.instance.return_value = app
                    view.setLanguage('en_US')
                    view.setLanguage('zh_CN')
                    loaded = [t for t in translators if t.load.call_args[0][0] == catalog]
                    self.assertEqual(len(loaded), 1)
                    expected = ([translators[0]] if major == 5 else []) + loaded
                    self.assertEqual([call.args[0] for call in app.installTranslator.call_args_list], expected)
                    self.assertEqual(view._qt_translators, expected)
                    view.setLanguage('en_US')
                    self.assertEqual([call.args[0] for call in app.removeTranslator.call_args_list], expected)
                    for translator in expected:
                        translator.deleteLater.assert_called_once_with()
                    self.assertEqual(view._qt_translators, [])

    def test_legacy_catalog_translates_platform_buttons_without_hiding_other_text(self):
        from hr_toolkit.gui_qt.presentation import QTranslator, _qt_button_catalog
        supplement = QTranslator()
        self.assertTrue(supplement.load(_qt_button_catalog('zh_CN')))
        self.assertTrue(self.app.installTranslator(supplement))
        translator = QTranslator()
        fixture = ROOT / 'tests/fixtures/qt_legacy_context_zh_CN.qm'
        self.assertTrue(translator.load(str(fixture)))
        self.assertTrue(self.app.installTranslator(translator))
        try:
            self.assertEqual(QCoreApplication.translate('QPlatformTheme', 'Cancel'), '取消')
            self.assertEqual(QCoreApplication.translate('QPlatformTheme', 'Save'), '保存')
            self.assertEqual(QCoreApplication.translate('QFileDialog', 'Open'), '打开')
            self.assertEqual(QCoreApplication.translate('QPlatformTheme', 'Unknown'), 'Unknown')
            self.assertEqual(QCoreApplication.translate('SourceData', 'Cancel'), 'Cancel')
        finally:
            self.app.removeTranslator(translator)
            self.app.removeTranslator(supplement)
        self.assertEqual(QCoreApplication.translate('QPlatformTheme', 'Cancel'), 'Cancel')

    def test_installed_qt_catalog_translates_real_standard_buttons(self):
        # Exercise the production loader and the catalog shipped with the CI
        # runtime. File existence or a mocked successful load is insufficient.
        view = Presentation()
        try:
            for locale in ('en_US', 'zh_CN', 'en_US', 'zh_CN'):
                view.setLanguage(locale)
                for source, chinese in (('Cancel', '取消'), ('Save', '保存'), ('OK', '确定')):
                    expected = chinese if locale == 'zh_CN' else source
                    self.assertEqual(
                        QCoreApplication.translate('QPlatformTheme', source), expected,
                        'Installed Qt catalog: %s / %s' % (locale, source),
                    )
        finally:
            view.setLanguage('en_US')

    def test_language_translators_allow_clean_process_shutdown(self):
        # Keep translators alive until interpreter shutdown, as can happen in
        # the CI core-test process. Native crashes must fail this isolated check.
        source = '''
from hr_toolkit.gui_qt.compat import QCoreApplication
from hr_toolkit.gui_qt.presentation import Presentation
app = QCoreApplication([])
views = [Presentation() for _ in range(5)]
for view in views:
    for language in ('en_US', 'zh_CN', 'en_US', 'zh_CN'):
        view.setLanguage(language)
assert QCoreApplication.translate('QPlatformTheme', 'Cancel') == '取消'
print('translation shutdown probe reached exit', flush=True)
'''
        completed = subprocess.run(
            [sys.executable, '-X', 'faulthandler', '-c', source], cwd=str(ROOT),
            capture_output=True, text=True, encoding='utf-8', errors='replace', timeout=30,
        )
        self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)
        self.assertIn('translation shutdown probe reached exit', completed.stdout)

    def test_real_ui_themes_languages_dialogs_and_persistence(self):
        completed = subprocess.run(
            [sys.executable, '-X', 'faulthandler', str(ROOT / "tests/qt_presentation_probe.py")], cwd=str(ROOT),
            env={**os.environ, "QT_QPA_PLATFORM": "offscreen", "QT_QUICK_BACKEND": "software", "QT_QUICK_CONTROLS_STYLE": "Basic", "HR_TOOLKIT_SKIP_UPDATE": "1"},
            capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=90,
        )
        if completed.returncode:
            # Print immediately: a later native crash can prevent unittest from
            # reaching its final summary and otherwise hide this probe's error.
            sys.stderr.write(completed.stdout + completed.stderr)
            sys.stderr.flush()
        self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)
        self.assertIn("presentation probe OK", completed.stdout)


class PaletteContracts(unittest.TestCase):
    def test_palette_tokens_and_contrast(self):
        source = (ROOT / "hr_toolkit/gui_qt/qml/components/Palettes.js").read_text(encoding="utf-8")
        palettes = json.loads(source[source.index('{'):source.rindex('}') + 1])
        self.assertEqual(set(palettes['light']), set(palettes['dark']))
        def luminance(color):
            rgb = [int(color[i:i+2], 16) / 255 for i in (1, 3, 5)]
            rgb = [v / 12.92 if v <= .04045 else ((v + .055) / 1.055) ** 2.4 for v in rgb]
            return sum(a * b for a, b in zip(rgb, (.2126, .7152, .0722)))
        for theme, palette in palettes.items():
            for foreground, background in [('text', 'surface'), ('text', 'input'), ('text', 'window'), ('onAccent', 'accent'), ('onLink', 'link3')]:
                a, b = sorted([luminance(palette[foreground]), luminance(palette[background])])
                # Existing blue update buttons use 13px text; do not weaken their baseline.
                minimum = 4.0 if theme == 'light' and foreground == 'onLink' else 4.5
                self.assertGreaterEqual((b + .05) / (a + .05), minimum, (theme, foreground, background))
        for file in (ROOT / 'hr_toolkit/gui_qt/qml').rglob('*.qml'):
            text = file.read_text(encoding='utf-8')
            self.assertNotRegex(text, r'#[0-9a-fA-F]{6}', str(file))
            for token in re.findall(r'Ui.color\("(.*?)"\)', text):
                self.assertIn(token, palettes['light'], str(file))

    def test_ci_routes_new_display_files_on_both_qt_lanes(self):
        from scripts.ci_scope import select_scope
        for path in ['hr_toolkit/gui_qt/presentation.py', 'hr_toolkit/gui_qt/translations_en.py', 'hr_toolkit/gui_qt/qml/translations/qt_buttons_zh_CN.qm', 'hr_toolkit/gui_qt/qml/components/Palettes.js', 'hr_toolkit/gui_qt/qml/components/qmldir', 'tests/qt_presentation_probe.py']:
            scope = select_scope([path])
            self.assertIn('tests.test_presentation', scope['targets'])
            self.assertIn('tests.test_presentation', scope['win7_targets'])


if __name__ == '__main__':
    unittest.main()
