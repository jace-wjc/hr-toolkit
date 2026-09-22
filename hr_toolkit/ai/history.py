"""AI 对话历史的落盘与查询。

历史保存在用户目录的 ``ai-conversations.json``（与 ``ai-assistant.json`` 同目录），
只有对话正文，不含 API Key。写入用「临时文件 + os.replace」保证原子性，
文件损坏时退化为空历史而不是让助手打不开。
"""

from __future__ import annotations

import json
import os
import tempfile
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from hr_toolkit.common.paths import user_app_data_dir

CONVERSATIONS_FILENAME = "ai-conversations.json"
CONVERSATION_LIMIT = 40
TITLE_MAX_CHARS = 22
DEFAULT_TITLE = "新对话"


@dataclass
class ConversationRecord:
    conversation_id: str
    title: str = DEFAULT_TITLE
    updated_at: float = 0.0
    messages: List[Dict[str, Any]] = field(default_factory=list)
    # 输入框里没发出去的草稿：切走再回来不该丢。
    draft: str = ""

    def as_summary(self, *, now: Optional[float] = None) -> Dict[str, Any]:
        return {
            "id": self.conversation_id,
            "title": self.title or DEFAULT_TITLE,
            "updated": format_updated(self.updated_at, now=now),
            "messageCount": len(self.messages),
            "preview": _preview(self.messages),
        }

    def as_payload(self) -> Dict[str, Any]:
        return {
            "id": self.conversation_id,
            "title": self.title,
            "updatedAt": self.updated_at,
            "messages": self.messages,
            "draft": self.draft,
        }

    def matches(self, needle: str) -> bool:
        """标题或正文命中即算匹配（历史搜索用）。"""
        query = str(needle or "").strip().lower()
        if not query:
            return True
        if query in (self.title or "").lower():
            return True
        for item in self.messages or ():
            if query in str(item.get("content") or "").lower():
                return True
            for part in item.get("attachments") or ():
                if isinstance(part, dict) and query in str(part.get("name") or "").lower():
                    return True
        return False


def default_conversations_path() -> Path:
    return user_app_data_dir("config") / "HRToolkit" / CONVERSATIONS_FILENAME


def make_title(text: str) -> str:
    """用首条用户消息生成标题，去掉 Markdown 标记并按字数截断。"""
    from .markdown import markdown_to_plain

    body = " ".join(markdown_to_plain(text).split())
    if not body:
        return DEFAULT_TITLE
    if len(body) <= TITLE_MAX_CHARS:
        return body
    return body[:TITLE_MAX_CHARS].rstrip() + "…"


def format_updated(stamp: float, *, now: Optional[float] = None) -> str:
    if not stamp:
        return ""
    reference = datetime.fromtimestamp(now if now is not None else time.time())
    moment = datetime.fromtimestamp(stamp)
    delta_days = (reference.date() - moment.date()).days
    if delta_days <= 0:
        return "今天 " + moment.strftime("%H:%M")
    if delta_days == 1:
        return "昨天 " + moment.strftime("%H:%M")
    if moment.year == reference.year:
        return moment.strftime("%m-%d %H:%M")
    return moment.strftime("%Y-%m-%d")


def _preview(messages: List[Dict[str, Any]]) -> str:
    for item in reversed(messages or []):
        if str(item.get("role")) != "assistant":
            continue
        body = " ".join(str(item.get("content") or "").split())
        if body:
            return body[:48] + ("…" if len(body) > 48 else "")
    return ""


class ConversationStore:
    """对话历史的读写门面；全部调用都在 GUI 主线程中完成。"""

    def __init__(self, path: Optional[Path] = None, *, limit: int = CONVERSATION_LIMIT) -> None:
        self._path = Path(path) if path is not None else default_conversations_path()
        self._limit = max(1, int(limit))
        self._items: List[ConversationRecord] = self._read()

    # --------------------------------------------------------------- 读取
    @property
    def path(self) -> Path:
        return self._path

    def _read(self) -> List[ConversationRecord]:
        try:
            raw = json.loads(self._path.read_text(encoding="utf-8"))
        except (FileNotFoundError, OSError, ValueError):
            return []
        if not isinstance(raw, dict):
            return []
        entries = raw.get("conversations")
        if not isinstance(entries, list):
            return []
        records: List[ConversationRecord] = []
        for entry in entries:
            record = _record_from_payload(entry)
            if record is not None:
                records.append(record)
        records.sort(key=lambda item: item.updated_at, reverse=True)
        return records[: self._limit]

    def summaries(self, *, now: Optional[float] = None, query: str = "") -> List[Dict[str, Any]]:
        needle = str(query or "").strip()
        items = self._items
        if needle:
            items = [item for item in items if item.matches(needle)]
        return [item.as_summary(now=now) for item in items]

    def get(self, conversation_id: str) -> Optional[ConversationRecord]:
        for item in self._items:
            if item.conversation_id == str(conversation_id):
                return item
        return None

    def latest(self) -> Optional[ConversationRecord]:
        return self._items[0] if self._items else None

    def rename(self, conversation_id: str, title: str) -> bool:
        record = self.get(conversation_id)
        if record is None:
            return False
        record.title = (str(title or "").strip() or DEFAULT_TITLE)[:120]
        self.save()
        return True

    def set_draft(self, conversation_id: str, draft: str) -> bool:
        """记录未发送的草稿；不更新 updated_at，免得草稿把对话顶到最前面。"""
        record = self.get(conversation_id)
        if record is None:
            return False
        record.draft = str(draft or "")
        self.save()
        return True

    # --------------------------------------------------------------- 写入
    def create(self, title: str = DEFAULT_TITLE) -> ConversationRecord:
        record = ConversationRecord(
            conversation_id=_new_id(),
            title=title or DEFAULT_TITLE,
            updated_at=time.time(),
        )
        self._items.insert(0, record)
        self._trim()
        self.save()
        return record

    def upsert(self, record: ConversationRecord) -> None:
        record.updated_at = time.time()
        for index, item in enumerate(self._items):
            if item.conversation_id == record.conversation_id:
                self._items[index] = record
                break
        else:
            self._items.insert(0, record)
        self._items.sort(key=lambda item: item.updated_at, reverse=True)
        self._trim()
        self.save()

    def remove(self, conversation_id: str) -> bool:
        for index, item in enumerate(self._items):
            if item.conversation_id == str(conversation_id):
                del self._items[index]
                self.save()
                return True
        return False

    def save(self) -> Path:
        payload = {"conversations": [item.as_payload() for item in self._items]}
        target = self._path
        target.parent.mkdir(parents=True, exist_ok=True)
        handle = tempfile.NamedTemporaryFile(
            "w", encoding="utf-8", dir=str(target.parent), prefix=".ai-chats-", delete=False
        )
        try:
            with handle:
                json.dump(payload, handle, ensure_ascii=False, indent=2)
                handle.write("\n")
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(handle.name, target)
        except BaseException:
            try:
                os.unlink(handle.name)
            except OSError:
                pass
            raise
        return target

    def _trim(self) -> None:
        if len(self._items) > self._limit:
            del self._items[self._limit :]


def _new_id() -> str:
    return time.strftime("%Y%m%d%H%M%S") + "-" + uuid.uuid4().hex[:6]


def _record_from_payload(entry: Any) -> Optional[ConversationRecord]:
    if not isinstance(entry, dict):
        return None
    conversation_id = str(entry.get("id") or "").strip()
    if not conversation_id:
        return None
    messages: List[Dict[str, Any]] = []
    raw_messages = entry.get("messages")
    if isinstance(raw_messages, list):
        for item in raw_messages:
            if not isinstance(item, dict):
                continue
            role = str(item.get("role") or "")
            if role not in ("user", "assistant"):
                continue
            attachments = item.get("attachments")
            messages.append(
                {
                    "role": role,
                    "content": str(item.get("content") or ""),
                    "time": str(item.get("time") or ""),
                    "apiContent": str(item.get("apiContent") or ""),
                    "attachments": [
                        {
                            "name": str(part.get("name") or ""),
                            "summary": str(part.get("summary") or ""),
                            "kind": str(part.get("kind") or "sheet"),
                            "mime": str(part.get("mime") or ""),
                            "path": str(part.get("path") or ""),
                            "preview": str(part.get("preview") or ""),
                        }
                        for part in (attachments if isinstance(attachments, list) else [])
                        if isinstance(part, dict)
                    ],
                }
            )
    try:
        updated_at = float(entry.get("updatedAt") or 0.0)
    except (TypeError, ValueError):
        updated_at = 0.0
    return ConversationRecord(
        conversation_id=conversation_id,
        title=str(entry.get("title") or DEFAULT_TITLE),
        updated_at=updated_at,
        messages=messages,
        draft=str(entry.get("draft") or ""),
    )
