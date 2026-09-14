"""Versioned user-facing notes, shared by the app and release metadata.

The release command records the user's notes for each new version here and
keeps previous entries for offline review. Do not infer user-facing changes
from Git commit messages.
"""

from __future__ import annotations


RELEASE_NOTES: dict[str, tuple[str, ...]] = {
    "0.9.0": (
        "更新前可以查看本次新增和修复的内容。",
        "新版本第一次打开时显示更新内容，也可通过“更新记录”随时查看。",
        "统一更新提示、下载和安装进度窗口；下载、校验、安装分别显示当前状态。",
    ),
}


def notes_for_version(version: str) -> tuple[str, ...]:
    return RELEASE_NOTES.get(version.lstrip("v"), ())


def release_entries(current_version: str) -> list[dict[str, object]]:
    def version_key(value: str) -> tuple[int, ...]:
        return tuple(int(part) for part in value.lstrip("v").split("."))

    current = version_key(current_version)
    return [
        {"version": version, "notes": list(RELEASE_NOTES[version])}
        for version in sorted(RELEASE_NOTES, key=version_key, reverse=True)
        if version_key(version) <= current
    ]
