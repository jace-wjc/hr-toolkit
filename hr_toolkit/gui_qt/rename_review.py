"""Virtualized, revision-checked editing of a frozen rename plan."""
from __future__ import annotations

import copy
import threading

from .compat import QObject, Property, QTimer, Signal, Slot, constant_property
from .models import ObjectListModel
from hr_toolkit.tools.rename_plan import validate_plan


class RenameReview(QObject):
    changed = Signal()
    opened = Signal()
    closed = Signal()
    confirmed = Signal(object)
    _ready = Signal(int, object, object)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._model = ObjectListModel(('row_id', 'order', 'source_name', 'target_name', 'relative_path',
            'is_dir', 'suffix', 'included', 'status', 'status_text', 'issue', 'note', 'editable_name'), self)
        self._plan = None
        self._revision = 0
        self._running = False
        self._pending = False
        self._valid = False
        self._search = ''
        self._filter = 'all'
        self._timer = QTimer(self)
        self._timer.setSingleShot(True)
        self._timer.setInterval(160)
        self._timer.timeout.connect(self._launch)
        self._ready.connect(self._apply)

    @constant_property(QObject)
    def model(self):
        return self._model

    @Property(bool, notify=changed)
    def validating(self):
        return self._pending or self._running

    @Property(bool, notify=changed)
    def canConfirm(self):
        return bool(self._plan and self._valid and not self.validating and
                    self._plan['change_count'] and not self._plan['conflict_count'])

    @Property(bool, notify=changed)
    def canReorder(self):
        return bool(self._plan and self._plan['mode'] == 'excel' and not self._search and self._filter == 'all')

    @Property(str, notify=changed)
    def summary(self):
        if not self._plan:
            return ''
        rows = self._plan['rows']
        return (f'共 {len(rows)} 项 · 待改名 {self._plan["change_count"]} · '
                f'需处理 {self._plan["conflict_count"]} · 已排除 {sum(not row["included"] for row in rows)}'
                f' · 当前显示 {len(self._model)}')

    @Property(str, notify=changed)
    def warnings(self):
        return '\n'.join(self._plan.get('warnings', [])) if self._plan else ''

    def load(self, plan):
        self._revision += 1
        self._plan = copy.deepcopy(plan)
        self._search, self._filter = '', 'all'
        self._valid, self._pending = False, True
        self._model.clear()
        self.opened.emit()
        self._launch()

    def _schedule(self):
        self._revision += 1
        self._valid, self._pending = False, True
        self.changed.emit()
        self._timer.start()

    def _row(self, row_id):
        if self._plan:
            index = int(row_id) if row_id.isdigit() else -1
            if 0 <= index < len(self._plan['rows']):
                return self._plan['rows'][index]
        return None

    @Slot(str, str)
    def editName(self, row_id, text):
        row = self._row(row_id)
        if row is not None:
            target = text + row['suffix']
            if target != row['target_name']:
                row['target_name'] = target
                self._schedule()

    @Slot(str, bool)
    def includeRow(self, row_id, included):
        row = self._row(row_id)
        if row is not None and row['included'] != included:
            row['included'] = included
            self._schedule()

    @Slot(str, int)
    def moveMapping(self, row_id, delta):
        if not self.canReorder or delta not in (-1, 1):
            return
        row = self._row(row_id)
        if row is None:
            return
        index = int(row_id)
        other_index = index + delta
        if not 0 <= other_index < len(self._plan['rows']):
            return
        other = self._plan['rows'][other_index]
        # Move assigned names, never source files or their extensions.
        def name(item):
            suffix = item['suffix']
            return item['target_name'][:-len(suffix)] if suffix and item['target_name'].endswith(suffix) else item['target_name']
        current_name, other_name = name(row), name(other)
        row['target_name'], other['target_name'] = other_name + row['suffix'], current_name + other['suffix']
        self._schedule()

    @Slot(str, str)
    def filterRows(self, search, status):
        if status not in ('all', 'conflict', 'ready', 'excluded', 'unchanged'):
            return
        if search != self._search or status != self._filter:
            self._search, self._filter = search, status
            self._schedule()

    def _launch(self):
        if self._plan is None or not self._pending or self._running:
            return
        revision = self._revision
        # Row values are immutable scalars. Avoid a deep copy of thousands of
        # records on the UI thread; the worker owns these shallow row copies.
        snapshot = {**self._plan, 'rows': [dict(row) for row in self._plan['rows']]}
        search, status = self._search.casefold(), self._filter
        self._running, self._pending = True, False
        self.changed.emit()
        def work():
            checked = validate_plan(snapshot)
            visible = []
            for row in checked['rows']:
                if status != 'all' and row['status'] != status:
                    continue
                if search and search not in (' '.join(str(row[key]) for key in
                          ('source_name', 'target_name', 'relative_path', 'issue'))).casefold():
                    continue
                item = dict(row)
                suffix = item['suffix']
                item['editable_name'] = item['target_name'][:-len(suffix)] if suffix and item['target_name'].endswith(suffix) else item['target_name']
                visible.append(item)
            try:
                self._ready.emit(revision, checked, visible)
            except RuntimeError:
                pass  # Qt parent was destroyed while this read-only worker finished.
        threading.Thread(target=work, daemon=True, name='HRToolkit-rename-review').start()

    @Slot(int, object, object)
    def _apply(self, revision, plan, visible):
        self._running = False
        if self._plan is None:
            return
        if revision != self._revision:
            self._launch()
            return
        self._plan, self._valid = plan, True
        old = self._model.items()
        roles = tuple(self._model._roles)
        normalized = [{key: row.get(key) for key in roles} for row in visible]
        if [row['row_id'] for row in old] == [row['row_id'] for row in visible]:
            for index, row in enumerate(normalized):
                if row != old[index]:
                    self._model.update_at(index, row)
        else:
            self._model.set_items(normalized)
        self.changed.emit()

    @Slot()
    def confirm(self):
        if self.canConfirm:
            frozen = copy.deepcopy(self._plan)
            self.cancel()
            self.confirmed.emit(frozen)

    @Slot()
    def cancel(self):
        if self._plan is None and not self._pending:
            return
        self._revision += 1
        self._timer.stop()
        self._plan = None
        self._pending = self._valid = False
        self._model.clear()
        self.closed.emit()
        self.changed.emit()
