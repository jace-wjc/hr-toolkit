"""Selection-only validation. Never reads workbooks or expands directories."""

from __future__ import annotations

import os
from pathlib import Path

from hr_toolkit.common.inputs import is_supported_archive_file
from .form_specs import EXCEL_SUFFIXES, ToolUiSpec


def selection_mode(spec: ToolUiSpec, role: str) -> str:
    if role == "input":
        return spec.input_mode
    if role == "support" and spec.support_id:
        return spec.support_mode
    raise ValueError("这里没有可接收资料的区域。")


def selection_hint(mode: str) -> str:
    return {
        "excel_archive_multi": "Excel、压缩包或文件夹，可多个",
        "excel_single": "1 个 Excel 文件",
        "directory_single": "1 个文件夹",
        "excel_file": "1 个 Excel 文件",
        "excel_or_folder": "1 个 Excel 文件或文件夹",
        "excel_archive_or_folder": "1 个 Excel、压缩包或文件夹",
    }[mode]


def validate_selection(paths: list[Path], mode: str, cancelled) -> list[Path]:
    """Run on a worker: stat may block on an unavailable network share.

    Reject the entire batch on error. Preserve source order and distinguish
    equal filenames in different directories. pathlib uses platform case rules.
    """
    if not paths:
        raise ValueError("没有可添加的本地资料，请先保存到本地后再拖入。")
    if mode != "excel_archive_multi" and len(paths) != 1:
        raise ValueError("这里只能接收一个位置，请一次选择一项资料。")
    result, seen, errors = [], set(), []
    error_count = 0
    for raw in paths:
        if cancelled():
            return []
        path = Path(os.path.abspath(os.path.expanduser(str(raw))))
        try:
            if path.is_dir():
                valid = mode in {"directory_single", "excel_archive_multi", "excel_or_folder", "excel_archive_or_folder"}
            elif path.is_file():
                valid = mode != "directory_single" and (
                    path.suffix.lower() in EXCEL_SUFFIXES
                    or (mode in {"excel_archive_multi", "excel_archive_or_folder"} and is_supported_archive_file(path))
                )
            else:
                raise ValueError("不存在、无法访问或不是普通文件/文件夹")
            if not valid:
                raise ValueError("这里只接收" + selection_hint(mode))
        except (OSError, ValueError) as exc:
            error_count += 1
            if len(errors) < 5:
                errors.append(f"{path.name[:100]}：{str(exc)[:180]}")
            continue
        if path not in seen:
            result.append(path)
            seen.add(path)
    if cancelled():
        return []
    if errors:
        suffix = f"\n另有 {error_count - len(errors)} 项不符合要求。" if error_count > len(errors) else ""
        raise ValueError("本次未添加，原选择保持不变。\n" + "\n".join(errors) + suffix)
    return result
