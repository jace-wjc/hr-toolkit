"""Display-only appearance and localization; never translate business inputs or outputs."""
from __future__ import annotations

import re
from functools import lru_cache
from .compat import QObject, Property, Signal, Slot, QApplication, QEvent, QT_MAJOR, constant_property


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
            if QT_MAJOR == 6:
                from PySide6.QtCore import QLibraryInfo, QTranslator
            else:
                from PySide2.QtCore import QLibraryInfo, QTranslator
            directory = (QLibraryInfo.path(QLibraryInfo.TranslationsPath) if QT_MAJOR == 6
                         else QLibraryInfo.location(QLibraryInfo.TranslationsPath))
            for module in ("qtbase", "qtdeclarative", "qtquickcontrols", "qtquickcontrols2"):
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
        from .compat import QFileDialog
        title = self.translate(title, self._language)
        filters = tuple(self.translate(value, self._language) for value in args)
        # Qt dialogs follow the selected palette and language, independent of OS locale.
        self._apply_language()
        app = QApplication.instance()
        if app is not None:
            app.installEventFilter(self)
        try:
            return function(parent, title, directory, *filters, options=QFileDialog.DontUseNativeDialog)
        finally:
            if app is not None:
                app.removeEventFilter(self)

    def eventFilter(self, watched, event):
        from .compat import QFileDialog
        if event.type() == QEvent.Show and isinstance(watched, QFileDialog):
            self._size_file_dialog(watched)
            if self._theme == 'dark':
                self._style_file_dialog_icons(watched)
        return False

    @staticmethod
    def _style_file_dialog_icons(dialog):
        # Platform navigation icons can remain black even with a dark Qt palette.
        # Draw only the six stock toolbar glyphs; folder/file icons stay untouched.
        if QT_MAJOR == 6:
            from PySide6.QtCore import Qt, QPointF, QRectF
            from PySide6.QtGui import QIcon, QPainter, QPalette, QPen, QPixmap, QPolygonF
            from PySide6.QtWidgets import QToolButton
        else:
            from PySide2.QtCore import Qt, QPointF, QRectF
            from PySide2.QtGui import QIcon, QPainter, QPalette, QPen, QPixmap, QPolygonF
            from PySide2.QtWidgets import QToolButton
        strokes = {
            'backButton': [[(10, 3), (5, 8), (10, 13)]],
            'forwardButton': [[(6, 3), (11, 8), (6, 13)]],
            'toParentButton': [[(3, 7), (8, 2), (13, 7)], [(8, 2), (8, 14)]],
            'newFolderButton': [[(2, 13), (2, 4), (6, 4), (8, 6), (14, 6), (14, 13), (2, 13)],
                                [(8, 8), (8, 12)], [(6, 10), (10, 10)]],
            'listModeButton': [[(6, y), (14, y)] for y in (4, 8, 12)],
            'detailModeButton': [[(6, y), (10, y)] for y in (4, 8, 12)],
        }
        for name, lines in strokes.items():
            button = dialog.findChild(QToolButton, name)
            if button is None:
                continue
            icon = QIcon()
            for mode, group in ((QIcon.Normal, QPalette.Active), (QIcon.Disabled, QPalette.Disabled)):
                pixmap = QPixmap(32, 32)
                pixmap.fill(Qt.transparent)
                painter = QPainter(pixmap)
                painter.setRenderHint(QPainter.Antialiasing)
                painter.scale(2, 2)
                painter.setPen(QPen(dialog.palette().color(group, QPalette.ButtonText), 1.4))
                for points in lines:
                    painter.drawPolyline(QPolygonF([QPointF(x, y) for x, y in points]))
                if name in ('listModeButton', 'detailModeButton'):
                    for y in (4, 8, 12):
                        painter.drawRect(QRectF(2, y - 1, 2, 2))
                        if name == 'detailModeButton':
                            painter.drawLine(QPointF(12, y), QPointF(14, y))
                painter.end()
                pixmap.setDevicePixelRatio(2)
                icon.addPixmap(pixmap, mode)
            button.setIcon(icon)

    @staticmethod
    def _size_file_dialog(dialog):
        # Size the stock picker; do not replace its selection/navigation behavior.
        if QT_MAJOR == 6:
            from PySide6.QtWidgets import QHeaderView, QSplitter, QTreeView
        else:
            from PySide2.QtWidgets import QHeaderView, QSplitter, QTreeView
        screen = dialog.screen() or QApplication.primaryScreen()
        available = screen.availableGeometry()
        dialog.resize(min(max(dialog.width(), 900), available.width() - 48),
                      min(max(dialog.height(), 540), available.height() - 64))
        splitter = dialog.findChild(QSplitter, 'splitter')
        if splitter is not None and len(splitter.sizes()) == 2:
            sidebar_width = max(160, splitter.sizes()[0])
            splitter.setSizes([sidebar_width, max(240, dialog.width() - sidebar_width - 48)])
        tree = dialog.findChild(QTreeView, 'treeView')
        if tree is not None and tree.header().count() >= 4:
            header = tree.header()
            header.setStretchLastSection(False)
            header.setSectionResizeMode(0, QHeaderView.Stretch)
            for column, width in ((1, 72), (2, 90), (3, 170)):
                header.setSectionResizeMode(column, QHeaderView.Interactive)
                header.resizeSection(column, width)
