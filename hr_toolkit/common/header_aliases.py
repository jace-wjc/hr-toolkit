"""用户确认的字段/工作表同义名称，只做精确归一匹配，不猜业务含义。"""
from __future__ import annotations

import re
import unicodedata
from typing import Any, Mapping, Sequence


def normalize_alias(value: Any) -> str:
    return re.sub(r"\s+", "", unicodedata.normalize("NFKC", str(value or ""))).casefold()


def protected_aliases(builtins: Sequence[str], values: Any) -> list[str]:
    """内置名称始终保留；兼容旧配置，只允许增删自定义部分。"""
    if not isinstance(values, list) or len(values) > 100:
        raise ValueError("每个字段或工作表最多设置 100 个名称")
    result = list(dict.fromkeys(builtins))
    seen = {normalize_alias(value) for value in result}
    for value in values:
        if not isinstance(value, str) or len(value) > 200 or not normalize_alias(value):
            raise ValueError("名称须为不超过 200 字的非空文字")
        if normalize_alias(value) not in seen:
            result.append(value.strip())
            seen.add(normalize_alias(value))
    if len(result) > 100:
        raise ValueError("内置和自定义名称合计不能超过 100 个")
    return result


def has_custom_aliases(builtins: Sequence[str], values: Sequence[str]) -> bool:
    known = {normalize_alias(value) for value in builtins}
    return any(normalize_alias(value) not in known for value in values)


def validate_alias_rules(
    payload: Any, *, field_labels: Mapping[str, str], sheet_labels: Mapping[str, str],
) -> dict[str, dict[str, list[str]]]:
    if not isinstance(payload, dict) or set(payload) - {"fields", "sheets"}:
        raise ValueError("名称规则格式无效，请重新设置")
    result = {}
    for kind, labels in (("fields", field_labels), ("sheets", sheet_labels)):
        items = payload.get(kind, {})
        if not isinstance(items, dict) or set(items) - set(labels):
            raise ValueError("名称规则包含当前工具不支持的字段或工作表")
        cleaned = {}
        owners = {}
        for key, values in items.items():
            if not isinstance(values, list) or len(values) > 100:
                raise ValueError(f"{labels[key]}最多设置 100 个名称")
            selected = []
            seen = set()
            for value in values:
                if not isinstance(value, str) or len(value) > 200:
                    raise ValueError(f"{labels[key]}的名称须为不超过 200 字的文字")
                value = value.strip()
                normalized = normalize_alias(value)
                if not normalized:
                    raise ValueError(f"{labels[key]}不能添加空名称")
                if kind == "fields" and normalized in owners and owners[normalized] != key:
                    raise ValueError(f"“{value}”不能同时对应{labels[owners[normalized]]}和{labels[key]}")
                owners[normalized] = key
                if normalized not in seen:
                    selected.append(value)
                    seen.add(normalized)
            if kind == "fields" and not selected:
                raise ValueError(f"请至少选择一个{labels[key]}的列名")
            if selected:
                cleaned[key] = selected
        result[kind] = cleaned
    return result


def matching_columns(columns: Sequence[Mapping[str, Any]], aliases: Sequence[str]) -> list[int]:
    wanted = {normalize_alias(value) for value in aliases}
    return [int(column["column"]) for column in columns
            if normalize_alias(column["label"]) in wanted
            or any(normalize_alias(leaf) in wanted for leaf in column.get("leaves", ()))]


def matching_sheets(names: Sequence[str], aliases: Sequence[str]) -> list[str]:
    wanted = {normalize_alias(value) for value in aliases}
    return [name for name in names if normalize_alias(name) in wanted]
