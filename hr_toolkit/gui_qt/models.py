"""Bounded and virtualized list models for the Qt Quick front end."""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from bisect import bisect_left
from typing import Any

from .compat import QAbstractListModel, QModelIndex, Qt, USER_ROLE


class ObjectListModel(QAbstractListModel):
    """A reset-efficient fixed-role model consumed by QML ``ListView``.

    Only visible delegates are instantiated by ListView, so tens of thousands
    of file records do not create tens of thousands of controls.
    """

    def __init__(self, roles: Iterable[str], parent=None) -> None:
        super().__init__(parent)
        self._roles = tuple(dict.fromkeys(str(role) for role in roles))
        self._role_numbers = {
            USER_ROLE + index + 1: role for index, role in enumerate(self._roles)
        }
        self._role_lookup = {role: number for number, role in self._role_numbers.items()}
        self._items: list[dict[str, Any]] = []

    def roleNames(self):  # noqa: N802 - Qt override
        return {
            number: role.encode("utf-8")
            for number, role in self._role_numbers.items()
        }

    def rowCount(self, parent=QModelIndex()):  # noqa: N802 - Qt override
        if parent.isValid():
            return 0
        return len(self._items)

    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid() or index.row() < 0 or index.row() >= len(self._items):
            return None
        role_name = self._role_numbers.get(int(role))
        if role_name is None:
            return None
        return self._items[index.row()].get(role_name)

    def set_items(self, items: Iterable[Mapping[str, Any]]) -> None:
        normalized = [
            {role: item.get(role) for role in self._roles}
            for item in items
        ]
        self.beginResetModel()
        self._items = normalized
        self.endResetModel()

    def append(self, item: Mapping[str, Any], *, maximum: int | None = None) -> None:
        if maximum is not None and maximum > 0 and len(self._items) >= maximum:
            remove_count = len(self._items) - maximum + 1
            self.beginRemoveRows(QModelIndex(), 0, remove_count - 1)
            del self._items[:remove_count]
            self.endRemoveRows()
        row = len(self._items)
        self.beginInsertRows(QModelIndex(), row, row)
        self._items.append({role: item.get(role) for role in self._roles})
        self.endInsertRows()

    def append_batch(
        self,
        items: Iterable[Mapping[str, Any]],
        *,
        maximum: int | None = None,
    ) -> None:
        normalized = [
            {role: item.get(role) for role in self._roles}
            for item in items
        ]
        if not normalized:
            return
        if maximum is not None and maximum > 0 and len(normalized) > maximum:
            normalized = normalized[-maximum:]
        if maximum is not None and maximum > 0:
            total_after = len(self._items) + len(normalized)
            if total_after > maximum:
                remove_count = min(total_after - maximum, len(self._items))
                if remove_count > 0:
                    self.beginRemoveRows(QModelIndex(), 0, remove_count - 1)
                    del self._items[:remove_count]
                    self.endRemoveRows()
        row = len(self._items)
        self.beginInsertRows(QModelIndex(), row, row + len(normalized) - 1)
        self._items.extend(normalized)
        self.endInsertRows()

    def remove_at(self, row: int) -> bool:
        if row < 0 or row >= len(self._items):
            return False
        self.beginRemoveRows(QModelIndex(), row, row)
        del self._items[row]
        self.endRemoveRows()
        return True

    def update_at(self, row: int, item: Mapping[str, Any]) -> bool:
        """Update one row without resetting the consuming ``ListView``."""

        if row < 0 or row >= len(self._items):
            return False
        self._items[row] = {role: item.get(role) for role in self._roles}
        model_index = self.index(row, 0)
        self.dataChanged.emit(
            model_index,
            model_index,
            list(self._role_numbers),
        )
        return True

    def splice(
        self,
        row: int,
        remove_count: int = 0,
        items: Iterable[Mapping[str, Any]] = (),
    ) -> None:
        """Replace a contiguous range while preserving view scroll state."""

        start = max(0, min(int(row), len(self._items)))
        removable = max(0, min(int(remove_count), len(self._items) - start))
        if removable:
            self.beginRemoveRows(QModelIndex(), start, start + removable - 1)
            del self._items[start : start + removable]
            self.endRemoveRows()
        normalized = [
            {role: item.get(role) for role in self._roles}
            for item in items
        ]
        if normalized:
            self.beginInsertRows(QModelIndex(), start, start + len(normalized) - 1)
            self._items[start:start] = normalized
            self.endInsertRows()

    def clear(self) -> None:
        if not self._items:
            return
        self.beginResetModel()
        self._items.clear()
        self.endResetModel()

    def item_at(self, row: int) -> dict[str, Any] | None:
        if 0 <= row < len(self._items):
            return dict(self._items[row])
        return None

    def items(self) -> list[dict[str, Any]]:
        return [dict(item) for item in self._items]

    def __len__(self) -> int:
        return len(self._items)


class InputFileModel(ObjectListModel):
    def __init__(self, parent=None) -> None:
        super().__init__(("name", "path", "kind", "detail"), parent)


class LogModel(ObjectListModel):
    def __init__(self, parent=None) -> None:
        super().__init__(("time", "text", "level"), parent)


class WorkspaceModel(ObjectListModel):
    def __init__(self, parent=None) -> None:
        super().__init__(
            ("name", "path", "isDir", "depth", "expanded", "hasChildren", "detail"),
            parent,
        )

    def sync_items(self, items: list[dict[str, Any]]) -> None:
        """Preserve unchanged path identities across directory refreshes.

        Unique paths permit an O(n log n) ordered match, including reorders.
        Apply gaps backwards so their old indices remain valid. A bounded
        number of bulk splices avoids a long stream of view notifications.
        """
        old_keys = [item.get("path") for item in self._items]
        new_keys = [item.get("path") for item in items]
        if (any(not isinstance(key, str) or not key for key in old_keys + new_keys)
                or len(set(old_keys)) != len(old_keys)
                or len(set(new_keys)) != len(new_keys)):
            self.set_items(items)
            return

        start = 0
        limit = min(len(old_keys), len(new_keys))
        while start < limit and old_keys[start] == new_keys[start]:
            start += 1
        old_end, new_end = len(old_keys), len(new_keys)
        while old_end > start and new_end > start and old_keys[old_end - 1] == new_keys[new_end - 1]:
            old_end -= 1
            new_end -= 1

        positions = {old_keys[row]: row for row in range(start, old_end)}
        common = [(positions[key], row) for row, key in enumerate(new_keys[start:new_end], start)
                  if key in positions]
        # Longest increasing subsequence of old positions: retain the largest
        # ordered set of existing rows, without quadratic sequence matching.
        tails, tail_indices, links = [], [], []
        for index, (old_row, _new_row) in enumerate(common):
            slot = bisect_left(tails, old_row)
            links.append(tail_indices[slot - 1] if slot else -1)
            if slot == len(tails):
                tails.append(old_row)
                tail_indices.append(index)
            else:
                tails[slot] = old_row
                tail_indices[slot] = index
        anchors = []
        index = tail_indices[-1] if tail_indices else -1
        while index >= 0:
            anchors.append(common[index])
            index = links[index]
        anchors.reverse()
        anchors.append((old_end, new_end))
        splices = []
        previous_old = previous_new = start - 1
        for old_row, new_row in anchors:
            remove_count = old_row - previous_old - 1
            insert_start, insert_end = previous_new + 1, new_row
            if remove_count or insert_start < insert_end:
                splices.append((previous_old + 1, remove_count, insert_start, insert_end))
            previous_old, previous_new = old_row, new_row
        if len(splices) > 64:
            self.set_items(items)
            return
        for row, remove_count, insert_start, insert_end in reversed(splices):
            self.splice(row, remove_count, items[insert_start:insert_end])

        # Retained paths can also have new names, expansion flags or details.
        # Coalesce adjacent metadata changes into one dataChanged range.
        changed_start = None
        for row, item in enumerate(items):
            changed = False
            if self._items[row] != item:
                normalized = {role: item.get(role) for role in self._roles}
                changed = self._items[row] != normalized
                if changed:
                    self._items[row] = normalized
            if changed and changed_start is None:
                changed_start = row
            elif not changed and changed_start is not None:
                self.dataChanged.emit(self.index(changed_start, 0), self.index(row - 1, 0), list(self._role_numbers))
                changed_start = None
        if changed_start is not None:
            self.dataChanged.emit(self.index(changed_start, 0), self.index(len(items) - 1, 0), list(self._role_numbers))


class HistoryModel(ObjectListModel):
    def __init__(self, parent=None) -> None:
        super().__init__(
            ("recordId", "time", "tool", "status", "inputs", "outputs", "detail"),
            parent,
        )


class TrashModel(ObjectListModel):
    def __init__(self, parent=None) -> None:
        super().__init__(
            (
                "batchId",
                "title",
                "tool",
                "status",
                "deletedAt",
                "counts",
                "restorePath",
                "size",
            ),
            parent,
        )


class AiChatModel(ObjectListModel):
    """一条消息一行。

    ``content`` 是模型原文（Markdown，复制时用它），``html`` 是渲染后的
    富文本（Qt 的 HTML 子集，见 :mod:`hr_toolkit.ai.markdown`），
    ``attachments`` 是这条消息携带的表格（随消息走，不再挂在待发区）。
    """

    def __init__(self, parent=None) -> None:
        super().__init__(
            ("role", "content", "html", "blocks", "streaming", "time", "attachments", "apiContent", "status"),
            parent,
        )
        self.timeline = AiTimelineModel(self)


class AiTimelineModel(ObjectListModel):
    """Viewport-sized presentation rows; canonical messages remain untouched.

    Virtualizing whole messages still lays out thousands of offscreen paragraphs
    inside one long reply. Project Markdown blocks into independent list rows,
    with a separate footer for message actions. Payloads are shared, not copied.
    """

    def __init__(self, messages: AiChatModel) -> None:
        super().__init__(
            ("role", "content", "blocks", "streaming", "attachments", "status",
             "part", "messageIndex", "rowKey", "lastBlock", "hasContent"),
            messages,
        )
        self._messages = messages
        self._counts: list[int] = []
        messages.modelReset.connect(self._reset)
        messages.rowsInserted.connect(self._inserted)
        messages.rowsRemoved.connect(self._removed)
        messages.dataChanged.connect(self._changed)

    def _rows(self, index: int) -> list[dict[str, Any]]:
        message = self._messages.item_at(index) or {}
        base = {"role": message.get("role"), "messageIndex": index,
                "streaming": bool(message.get("streaming")),
                "hasContent": bool(message.get("content")), "status": message.get("status")}
        if message.get("role") == "user":
            rows = [{**base, "part": "user", "rowKey": "%d:user" % index,
                     "content": message.get("content"), "attachments": message.get("attachments")}]
        else:
            blocks = message.get("blocks") or []
            if not blocks and message.get("html"):
                blocks = [{"kind": "text", "html": message["html"]}]
            rows = [{**base, "part": "block", "rowKey": "%d:block:%d" % (index, position),
                     "blocks": [block], "lastBlock": position == len(blocks) - 1}
                    for position, block in enumerate(blocks)]
            rows.append({**base, "part": "footer", "rowKey": "%d:footer" % index,
                         "content": message.get("content")})
        return [{role: row.get(role) for role in self._roles} for row in rows]

    def _reset(self) -> None:
        rows = []
        self._counts = []
        for index in range(len(self._messages)):
            projected = self._rows(index)
            self._counts.append(len(projected))
            rows.extend(projected)
        self.set_items(rows)

    def _inserted(self, parent, first: int, last: int) -> None:
        if first != len(self._counts):
            self._reset()
            return
        rows = []
        for index in range(first, last + 1):
            projected = self._rows(index)
            self._counts.append(len(projected))
            rows.extend(projected)
        self.append_batch(rows)

    def _removed(self, parent, first: int, last: int) -> None:
        if last != len(self._counts) - 1:
            self._reset()
            return
        start = sum(self._counts[:first])
        self.splice(start, len(self) - start)
        del self._counts[first:]

    def _changed(self, first, last, roles=None) -> None:
        for index in range(first.row(), last.row() + 1):
            start = sum(self._counts[:index])
            count = self._counts[index]
            previous = self._items[start:start + count]
            projected = self._rows(index)
            # Keep completed blocks and the footer alive during streaming.
            prefix = 0
            while prefix < min(count, len(projected)) and previous[prefix] == projected[prefix]:
                prefix += 1
            suffix = 0
            while (suffix < min(count, len(projected)) - prefix
                   and previous[count - suffix - 1]["rowKey"] == projected[len(projected) - suffix - 1]["rowKey"]):
                suffix += 1
            old_end, new_end = count - suffix, len(projected) - suffix
            # Match by stable key so a new paragraph never replaces the footer.
            while prefix < min(old_end, new_end) and previous[prefix]["rowKey"] == projected[prefix]["rowKey"]:
                if previous[prefix] != projected[prefix]:
                    self.update_at(start + prefix, projected[prefix])
                prefix += 1
            self.splice(start + prefix, old_end - prefix, projected[prefix:new_end])
            for offset in range(suffix):
                if previous[old_end + offset] != projected[new_end + offset]:
                    self.update_at(start + new_end + offset, projected[new_end + offset])
            self._counts[index] = len(projected)


class AiAttachmentModel(ObjectListModel):
    """待发附件一行。``kind`` 区分表格与图片，``preview`` 是图片的本地路径（QML 显示缩略图）。"""

    def __init__(self, parent=None) -> None:
        super().__init__(("name", "summary", "path", "kind", "preview"), parent)


class AiConversationModel(ObjectListModel):
    """对话历史列表（按更新时间倒序）。"""

    def __init__(self, parent=None) -> None:
        super().__init__(("id", "title", "updated", "preview", "active"), parent)
