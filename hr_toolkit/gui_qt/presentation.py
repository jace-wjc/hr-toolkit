"""Display-only appearance and localization; never translate business inputs or outputs."""
from __future__ import annotations

import re
from functools import lru_cache
from pathlib import Path
from .compat import QObject, Property, Signal, Slot, QApplication, QT_MAJOR, constant_property

if QT_MAJOR == 6:
    from PySide6.QtCore import QTranslator
else:
    from PySide2.QtCore import QTranslator


def _qt_button_catalog(locale):
    return str(Path(__file__).parent / 'qml' / 'translations' / ('qt_buttons_' + locale + '.qm'))


def _english_catalog():
    # A static, lazy import lets PyInstaller discover the catalog without loading it at startup.
    from . import translations_en
    return translations_en


THEMES = {"light": "浅色", "dark": "深色"}
LANGUAGES = {
    "zh_CN": {"label": "简体中文", "catalog": None, "qt": "zh_CN"},
    "en_US": {"label": "English (US)", "catalog": _english_catalog, "qt": None},
}


class Presentation(QObject):
    changed = Signal()
    preferencesChanged = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._theme = 'light'
        self._language = 'zh_CN'
        self._catalogs = {}
        self._edited_preferences = set()
        self._qt_translators = []
        self._qt_language = None
        app = QApplication.instance()
        self._original_palette = app.palette() if app and hasattr(app, "palette") else None
        self._original_widget_style = app.style().objectName() if app and hasattr(app, "style") else None

    @Property(str, notify=changed)
    def theme(self):
        return self._theme

    @Property(str, notify=changed)
    def language(self):
        return self._language

    @constant_property("QVariantList")
    def themeOptions(self):
        return [{"label": label, "value": value} for value, label in THEMES.items()]

    @constant_property("QVariantList")
    def languageOptions(self):
        return [{"label": item["label"], "value": value} for value, item in LANGUAGES.items()]

    @Slot(str)
    def setTheme(self, value):
        if value not in THEMES or value == self._theme:
            return
        self._theme = value
        self._edited_preferences.add("theme")
        self._apply_palette()
        self.changed.emit()
        self.preferencesChanged.emit()

    @Slot(str)
    def setLanguage(self, value):
        if value not in LANGUAGES or value == self._language:
            return
        self._language = value
        self._edited_preferences.add("language")
        self._apply_language()
        self.changed.emit()
        self.preferencesChanged.emit()

    def restore(self, theme, language):
        if 'theme' not in self._edited_preferences:
            self._theme = theme if theme in THEMES else 'light'
        if 'language' not in self._edited_preferences:
            self._language = language if language in LANGUAGES else 'zh_CN'
        self._apply_palette()
        self._apply_language()
        self.changed.emit()

    def _apply_language(self):
        """Use Qt's already-shipped catalog for file dialogs and standard menus."""
        app = QApplication.instance()
        if not app or self._qt_language == self._language:
            return
        for translator in self._qt_translators:
            app.removeTranslator(translator)
            translator.deleteLater()
        self._qt_translators = []
        qt_locale = LANGUAGES[self._language]["qt"]
        if qt_locale:
            if QT_MAJOR == 5:
                # Use native translators only: Qt may request translations while
                # the Python interpreter is shutting down. Install the supplement
                # first so official catalog entries take precedence when present.
                translator = QTranslator(self)
                if translator.load(_qt_button_catalog(qt_locale)):
                    app.installTranslator(translator)
                    self._qt_translators.append(translator)
                else:
                    translator.deleteLater()
            if QT_MAJOR == 6:
                from PySide6.QtCore import QLibraryInfo
            else:
                from PySide2.QtCore import QLibraryInfo
            directory = (QLibraryInfo.path(QLibraryInfo.TranslationsPath) if QT_MAJOR == 6
                         else QLibraryInfo.location(QLibraryInfo.TranslationsPath))
            modules = ("qtbase", "qtdeclarative", "qtquickcontrols", "qtquickcontrols2")
            # The pinned Windows PySide2 wheel ships widget translations in
            # qt_zh_CN.qm, while newer Qt wheels use the split qtbase catalog.
            if QT_MAJOR == 5:
                modules = ("qt",) + modules
            for module in modules:
                translator = QTranslator(self)
                if translator.load(module + "_" + qt_locale, directory):
                    app.installTranslator(translator)
                    self._qt_translators.append(translator)
                else:
                    translator.deleteLater()
        self._qt_language = self._language

    def _apply_palette(self):
        app = QApplication.instance()
        if not app or self._original_palette is None:
            return
        # Native widget styles can ignore dark palette roles (notably on macOS).
        # Fusion is bundled with both Qt 5 and Qt 6 and honors the full palette.
        # Qt Quick continues to use its existing Default/Basic control style.
        style = 'Fusion' if self._theme == 'dark' else self._original_widget_style
        if style and app.style().objectName().casefold() != style.casefold():
            app.setStyle(style)
        if QT_MAJOR == 6:
            from PySide6.QtGui import QPalette, QColor
        else:
            from PySide2.QtGui import QPalette, QColor
        palette = QPalette(self._original_palette)
        colors = {'Window': '#181D23', 'WindowText': '#E6EBF0', 'Base': '#1C232B',
                  'AlternateBase': '#303943', 'Text': '#E6EBF0', 'Button': '#222931',
                  'ButtonText': '#E6EBF0', 'Highlight': '#78DBB9', 'HighlightedText': '#13251F',
                  'ToolTipBase': '#222931', 'ToolTipText': '#E6EBF0', 'Link': '#91BFFD',
                  'Light': '#56616E', 'Midlight': '#435261', 'Mid': '#39434F', 'Dark': '#181D23',
                  'PlaceholderText': '#ABB5C1'}
        if self._theme == "light":
            colors = {'Window': '#FCFCFB', 'WindowText': '#292825', 'Base': '#FAF9F6',
                      'AlternateBase': '#F2F0EA', 'Text': '#292825', 'Button': '#FFFFFF',
                      'ButtonText': '#292825', 'Highlight': '#17715B', 'HighlightedText': '#FFFFFF',
                      'ToolTipBase': '#FFFFFF', 'ToolTipText': '#292825', 'Link': '#005FCC',
                      'Light': '#FFFFFF', 'Midlight': '#E3E0D8', 'Mid': '#D0CBC0', 'Dark': '#B9B6AE',
                      'PlaceholderText': '#78766E'}
        for role, color in colors.items():
            palette.setColor(getattr(QPalette, role), QColor(color))
        for role in ('WindowText', 'Text', 'ButtonText'):
            palette.setColor(QPalette.Disabled, getattr(QPalette, role), QColor('#96A1AD' if self._theme == 'dark' else '#98958C'))
        app.setPalette(palette)

    def _load_catalog(self, language):
        if language in self._catalogs:
            return self._catalogs[language]
        module = LANGUAGES[language]["catalog"]()
        messages = module.MESSAGES
        patterns = {}
        # Prefer specific messages over overlapping generic templates.
        ordered = sorted(messages.items(), key=lambda item: len(re.sub(r"\{\d+\}", "", item[0])), reverse=True)
        for source, target in ordered:
            parts = re.split(r'(\{\d+\})', source)
            if len(parts) == 1:
                continue
            pattern = ''.join('(.*?)' if re.fullmatch(r'\{\d+\}', p) else re.escape(p) for p in parts)
            prefix = parts[0][:2]
            patterns.setdefault(prefix, []).append((re.compile('^' + pattern + '$', re.S), target))
        catalog = (messages, patterns, getattr(module, "TRANSLATED_ARGUMENTS", {}))
        self._catalogs[language] = catalog
        return catalog

    @Slot(str, str, result=str)
    def translate(self, text, language):
        if language not in LANGUAGES or LANGUAGES[language]["catalog"] is None:
            return text
        return self._localized(text, language)

    @lru_cache(maxsize=4096)
    def _localized(self, text, language):
        if not re.search(r'[\u3400-\u9fff]', text):
            return text
        messages, patterns, translated_arguments = self._load_catalog(language)
        if text in messages:
            return messages[text]
        for prefix in (text[:2], text[:1], ''):
            for pattern, target in patterns.get(prefix, ()):
                match = pattern.fullmatch(text)
                if match:
                    values = list(match.groups())
                    for index in translated_arguments.get(pattern.pattern, ()):
                        if values[index] != text:
                            values[index] = self._localized(values[index], language)
                    return target.format(*values)
        if ' · ' in text:
            return ' · '.join(self._localized(part, language) for part in text.split(' · '))
        if '\n' in text:
            return '\n'.join(self._localized(line, language) for line in text.split('\n'))
        return text

    def file_dialog(self, function, parent, title, directory, *args):
        title = self.translate(title, self._language)
        filters = tuple(self.translate(value, self._language) for value in args)
        # Keep Qt's native picker and each function's original options (notably
        # ShowDirsOnly for folder selection). OS controls follow the OS appearance
        # and language; only application-provided titles and filters are translated.
        self._apply_language()
        return function(parent, title, directory, *filters)
