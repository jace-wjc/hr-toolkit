"""输入表的显式名称适配；视图只覆盖表头值，不写原工作簿或改正文。

规则随每次调用传入，ContextVar 隔离不同工具/后台线程；可经 JSON 传入独立进程。
"""
from __future__ import annotations

import hashlib
import json
import inspect
from contextvars import ContextVar
from copy import copy
from functools import wraps
from typing import Any

from .header_aliases import normalize_alias, validate_alias_rules, protected_aliases, has_custom_aliases

ERROR_PREFIX = "HR_TEMPLATE_SELECTION:"
SUPPORTED_TOOLS = ("salary_split", "personnel_change_merge", "archive_import",
                   "insurance_ledger", "data_statistics", "social_security")
_current = ContextVar("hr_input_template_mapping", default=None)


class TemplateSelectionRequired(Exception):
    """不能作为普通 ValueError 被旧的“非业务文件跳过”分支吞掉。"""
    def __init__(self, payload):
        self.payload = payload
        super().__init__(ERROR_PREFIX + json.dumps(payload, ensure_ascii=False, default=str))


def _role(label, required, fields, sheets=()):
    return {"label": label, "required": list(required),
            "fields": {name: list(values) for name, values in fields.items()}, "sheets": list(sheets)}


def catalog(tool):
    """各处理项分别声明实际读取的字段；可选字段未配置时不额外变成必填。"""
    if tool == "salary_split":
        from hr_toolkit.tools import salary_split as m
        fields = {"入职公司": m.HEADER_COMPANY_SYNONYMS, "姓名": m.HEADER_NAME_SYNONYMS,
                  "身份证号码": m.HEADER_ID_CARD_SYNONYMS, "序号": m.HEADER_SEQ_SYNONYMS,
                  "项目": m.HEADER_PROJECT_SYNONYMS}
        return {"detail": _role("工资明细", ("入职公司", "姓名", "身份证号码"), fields),
                "summary": _role("工资汇总", (), {})}
    if tool == "personnel_change_merge":
        from hr_toolkit.tools import personnel_change_merge as m
        return {role: _role(role, ("序号", "姓名", m.PERIOD_FIELD_BY_SHEET[role][0]),
                            {name: m.FIELD_ALIASES.get(name, (name,)) for name in m.DEFAULT_HEADERS_BY_SHEET[role]},
                            m.SOURCE_SHEET_ALIASES[role]) for role in m.TARGET_SHEETS}
    if tool == "archive_import":
        from hr_toolkit.tools import archive_import as m
        fields = {name: (name,) for name in dict.fromkeys(["公司", *m.DIRECT_FIELD_MAP, "其他", "离职时间"])}
        return {"transfer": _role("档案移交表", ("公司", "姓名", "身份证"), fields)}
    if tool == "insurance_ledger":
        return {
            "policy": _role("保单人员清单", ("姓名", "身份证号码"), {
                "姓名": ("雇员姓名", "姓名", "被保险人姓名"),
                "身份证号码": ("身份证号码", "证件号", "证件号码", "身份证号"),
                "每人伤残死亡限额": ("每人伤残死亡限额", "伤残死亡限额", "死亡伤残限额")}),
            "roster": _role("人力资源花名册", ("姓名", "身份证号码"), {
                "姓名": ("*姓名.简体中文", "姓名", "员工姓名", "人员姓名"),
                "身份证号码": ("*身份证", "身份证", "身份证号码", "证件号"),
                "部门/项目": ("部门/项目", "项目/部门", "部门（片区）", "部门片区", "成本中心.名称", "*责任部门.名称", "责任部门.名称", "部门名称", "部门", "项目.项目名称"),
                "状态": ("状态", "员工状态", "在职状态", "*参保状态", "参保状态")})}
    if tool == "data_statistics":
        from hr_toolkit.tools import data_statistics as m
        names = ("姓名", "日期", "部门名称", "事假", "病假天数", "婚假", "产假天数", "陪护假", "丧假", "探亲假", "工伤", "年假天数",
                 "调休", "加班计调休时长", "旷工天数", "迟到次数", "早退次数", "漏打卡次数", "迟到分钟数", "早退分钟数",
                 "公出", "外出", "工作日出差", "应出勤小时数", "实出勤小时数", "计划上下班时间", "当日刷卡记录", "缺卡记录", "带薪休假")
        fields = {name: (name,) for name in names}
        summary = {name: (name,) for name in (*names, *m._SUMMARY_ATTENDANCE_KEY_FIELDS, "公司", "部门（片区）", "部门", "实际出勤天数", "备注")}
        summary.update({
            "调休": ("调休", "调休（小时）", "总调休", "总调休\n(小时)", "总调休（小时）"),
            "加班计调休时长": ("加班计调休时长", "当月加班时长", "当月加班（小时）"),
            "事假": ("事假", "事假（天）", "事假\n(天)", "事假\n(小时)"),
            "病假天数": ("病假天数", "病假", "病假（天）", "病假\n(天)"),
            "迟到次数": ("迟到次数", "迟到", "迟到（次）"),
            "早退次数": ("早退次数", "早退", "早退（次）"),
            "漏打卡次数": ("漏打卡次数", "漏打卡", "漏打卡（次）"),
        })
        reports = {name: (name,) for name in ("汇报编号", "汇报人", "汇报时间", "汇报人部门")}
        return {"attendance": _role("每日考勤", ("姓名", "日期", "漏打卡次数", "应出勤小时数"), fields),
                "attendance_summary": _role("按人汇总的考勤", ("姓名",), summary),
                "weekly": _role("周报", ("汇报编号", "汇报时间", "汇报人"), reports),
                "monthly": _role("月报", ("汇报编号", "汇报时间", "汇报人"), reports),
                "staff": _role("应汇报人员名单", ("姓名",), {
                    "姓名": ("姓名", "汇报人", "员工姓名", "人员姓名"), "公司": ("公司", "所属公司", "单位"),
                    "部门": ("部门（片区）", "部门片区", "部门", "部门名称", "汇报人部门", "所属部门")})}
    if tool == "social_security":
        from hr_toolkit.tools import social_security as m
        roster = {name: (name,) for name in (m.ROSTER_NAME, m.ROSTER_ID, m.ROSTER_STATUS, m.ROSTER_START_DATE,
                  m.ROSTER_PLAN, m.ROSTER_UNIT, m.ROSTER_DEPARTMENT, m.ROSTER_PROJECT, m.ROSTER_COST_CENTER, m.ROSTER_MANAGEMENT_FEE)}
        payment = {name: (name,) for name in ("姓名", "缴费基数", "费率", "参保费种", "征收品目", "险种", "本人工资", "缴费工资",
                   *m.FEE_PERIOD_START_HEADERS, *m.FEE_PERIOD_END_HEADERS, *m.PAYMENT_NATURE_HEADERS)}
        payment["证件号码"] = ("身份证件号码", "证件号码")
        payment["应缴费额(元)"] = ("应缴费额(元)", "本期应缴费额")
        for insurance in ("养老", "医疗", "失业", "工伤"):
            for side in ("个人", "单位"):
                name = f"{insurance}保险({side}缴纳)应缴费额"
                payment[name] = (name,)
        return {"payment": _role("社保缴费清单", ("姓名", "证件号码"), payment),
                "roster": _role("参保人员花名册", (m.ROSTER_NAME, m.ROSTER_ID), roster)}
    return {}


def clean_rules(tool, payload):
    if not isinstance(payload, dict) or set(payload) - {"fields", "sheets", "profiles"}:
        raise ValueError("模板对应设置格式无效")
    specs = catalog(tool)
    fields = {role + "|" + name: spec["label"] + " · " + name for role, spec in specs.items() for name in spec["fields"]}
    # 不同处理项允许使用同一个列名，只在同一处理项内部校验冲突。
    result = {"fields": {}, "sheets": {}, "profiles": []}
    for kind in ("fields", "sheets"):
        values = payload.get(kind, {})
        labels = fields if kind == "fields" else {r: s["label"] for r, s in specs.items()}
        if not isinstance(values, dict) or set(values) - set(labels):
            raise ValueError("名称规则包含当前工具不支持的字段或工作表")
        for key, aliases in values.items():
            if kind == "fields":
                role, name = key.split("|", 1)
                builtins = specs[role]["fields"][name]
            else:
                builtins = specs[key]["sheets"]
            merged = protected_aliases(builtins, aliases)
            if has_custom_aliases(builtins, merged):
                cleaned = validate_alias_rules({kind: {key: merged}}, field_labels=labels, sheet_labels=labels)
                result[kind].update(cleaned[kind])
    for role, spec in specs.items():
        owners = {}
        for name in spec["fields"]:
            key = role + "|" + name
            for alias in result["fields"].get(key, []):
                normalized = normalize_alias(alias)
                # 原有字段的内置同义词可能交叉（如公司/入职公司），保留旧行为。
                if normalized in {normalize_alias(v) for v in spec["fields"][name]}:
                    continue
                if any(normalized in {normalize_alias(v) for v in defaults} for other, defaults in spec["fields"].items() if other != name):
                    raise ValueError(f"{spec['label']}：“{alias}”是其他字段的内置名称，不能改作{name}")
                if normalized in owners and owners[normalized] != name:
                    raise ValueError(f"{spec['label']}：“{alias}”不能同时对应{owners[normalized]}和{name}")
                owners[normalized] = name
    profiles = payload.get("profiles", [])
    if not isinstance(profiles, list) or len(profiles) > 200:
        raise ValueError("最多保存 200 套模板的手动对应关系")
    for profile in profiles:
        if not isinstance(profile, dict) or profile.get("role") not in {*specs, "_ignore"} or not isinstance(profile.get("key"), str):
            raise ValueError("已保存的模板对应关系无效")
        allowed_fields = specs[profile["role"]]["fields"] if profile["role"] != "_ignore" else {}
        if not isinstance(profile.get("columns"), dict) or set(profile["columns"]) - set(allowed_fields):
            raise ValueError("已保存的对应列无效")
        result["profiles"].append(profile)
    return result


def template_tool(tool):
    def decorate(function):
        @wraps(function)
        def wrapped(*args, template_rules=None, **kwargs):
            if template_rules is None:
                return function(*args, **kwargs)
            token = _current.set((tool, clean_rules(tool, template_rules)))
            try:
                return function(*args, **kwargs)
            finally:
                _current.reset(token)
        signature = inspect.signature(function)
        wrapped.__signature__ = signature.replace(parameters=[*signature.parameters.values(),
            inspect.Parameter("template_rules", inspect.Parameter.KEYWORD_ONLY, default=None)])
        return wrapped
    return decorate


def active():
    return _current.get() is not None


def _title(sheet):
    return getattr(sheet, "title", getattr(sheet, "name", ""))


def preview(sheet):
    if hasattr(sheet, "nrows"):
        rows = [sheet.row_values(r)[:512] for r in range(min(sheet.nrows, 30))]
    elif hasattr(sheet, "_rows"):
        rows = list(sheet._rows[:30])
    else:
        rows = list(sheet.iter_rows(min_row=1, max_row=min(sheet.max_row or 30, 30), max_col=min(sheet.max_column or 512, 512), values_only=True))
    return [[str(v)[:200] if v is not None else "" for v in row[:512]] for row in rows]


def profile_key(sheet, row, values):
    return hashlib.sha256(json.dumps([sheet, row, [normalize_alias(v) for v in values]], ensure_ascii=False).encode()).hexdigest()


def field_label(name):
    """只用于界面展示，不改变识别名称、保存的键或输出字段。"""
    return {"*姓名.简体中文": "姓名", "*身份证": "身份证号码",
            "*参保状态": "参保状态", "*参保日期": "参保日期",
            "*参保方案.名称": "参保方案", "*参保单位.名称": "参保单位",
            "*责任部门.名称": "责任部门", "项目.项目名称": "项目名称",
            "成本中心.名称": "成本中心"}.get(name, name)


def request_selection(sheets, roles, *, file="", message="请选择原表对应的列", row=1, allow_ignore=False, required_fields=None, one_of=None, selected_sheet=""):
    if not active():
        raise ValueError(message)
    tool, rules = _current.get()
    specs = catalog(tool)
    described = []
    for role in roles:
        spec = specs[role]
        fields = {name: rules["fields"].get(role + "|" + name, values) for name, values in spec["fields"].items()}
        required = list(dict.fromkeys([*spec["required"], *(required_fields or {}).get(role, []), *(name for name in fields if role + "|" + name in rules["fields"])]))
        described.append({"key": role, **spec, "fields": fields, "required": required,
                          "field_labels": {name: field_label(name) for name in fields},
                          "one_of": (one_of or {}).get(role, [])})
    if allow_ignore:
        described.append({"key": "_ignore", "label": "此工作表不是本次业务数据，不参与处理", "fields": {}, "required": []})
    raise TemplateSelectionRequired({"tool": tool, "file": str(file), "message": message, "row": row,
        "selected_sheet": selected_sheet,
        "roles": described,
        "sheets": [{"name": _title(ws), "rows": preview(ws)} for ws in sheets]})


def _ignore_key(file, name, rows):
    return hashlib.sha256(json.dumps([str(file), name, rows], ensure_ascii=False).encode()).hexdigest()


def ignored_sheet(sheet, file):
    if not active():
        return False
    profiles = [p for p in _current.get()[1]["profiles"] if p["role"] == "_ignore" and p.get("file") == str(file) and p.get("sheet") == _title(sheet)]
    return bool(profiles) and any(p["key"] == _ignore_key(file, _title(sheet), preview(sheet)) for p in profiles)


def assigned_role(sheet, roles, *, confirmed_only=False):
    if not active():
        return None
    tool, rules = _current.get()
    title = _title(sheet)
    candidates = [] if confirmed_only else [role for role in roles if normalize_alias(title) in {normalize_alias(s) for s in rules["sheets"].get(role, [])}]
    rows = None
    confirmed = []
    for profile in rules["profiles"]:
        if profile["role"] not in roles or profile.get("sheet") != title:
            continue
        rows = rows if rows is not None else preview(sheet)
        r = int(profile.get("row", 0))
        if 1 <= r <= len(rows) and profile_key(title, r, rows[r - 1]) == profile["key"]:
            confirmed.append(profile["role"])
    if confirmed:
        candidates = confirmed
    candidates = list(dict.fromkeys(candidates))
    if len(candidates) > 1:
        request_selection([sheet], roles, message="同一工作表匹配了多个用途，请确认")
    return candidates[0] if candidates else None


def choose_sheet(sheets, role, default=None, *, required=True, file="", allow_absent=False):
    if not active():
        return default
    rules = _current.get()[1]
    configured = rules["sheets"].get(role, [])
    confirmed = [ws for ws in sheets if assigned_role(ws, [role], confirmed_only=True) == role]
    if len(confirmed) == 1:
        return confirmed[0]
    if len(confirmed) > 1:
        request_selection(sheets, [role], file=file, message="多张工作表匹配手动对应关系，请确认本次工作表")
    candidates = [ws for ws in sheets if assigned_role(ws, [role]) == role]
    if len(candidates) == 1:
        return candidates[0]
    if configured and not candidates and (allow_absent or default is not None or not required):
        configured = []  # 未命中自定义名称时，仍允许原有的内置查找。
    if candidates or configured:
        request_selection(sheets, [role], file=file, message="工作表名称未匹配或匹配了多张，请选择本次处理的工作表")
    if default is not None:
        owner = assigned_role(default, list(catalog(_current.get()[0])))
        if owner and owner != role:
            if required:
                request_selection(sheets, [role], file=file, message="默认工作表已对应其他用途，请选择本次工作表")
            return None
        return default
    if required:
        request_selection(sheets, [role], file=file, message="未找到工作表，请选择它对应的处理项")
    return None


class HeaderView:
    def __init__(self, source, row, changes, role):
        self.source, self.header_row, self.changes, self.mapping_role = source, row, changes, role

    def __getattr__(self, name):
        return getattr(self.source, name)

    def cell(self, row, column):
        cell = self.source.cell(row, column)
        if row == self.header_row and column in self.changes:
            if hasattr(cell, "_replace"):
                return cell._replace(value=self.changes[column])
            cell = copy(cell)
            cell.value = self.changes[column]
        return cell

    def value(self, row, column):
        if row == self.header_row and column in self.changes:
            return self.changes[column]
        return self.source.value(row, column)

    def row_values(self, row, *args, **kwargs):
        values = self.source.row_values(row, *args, **kwargs)
        if row == self.header_row - 1:
            values = list(values)
            for col, value in self.changes.items():
                values[col - 1] = value
        return values

    def cell_value(self, row, col):
        if row == self.header_row - 1 and col + 1 in self.changes:
            return self.changes[col + 1]
        return self.source.cell_value(row, col)


def map_sheet(sheet, role, *, required=True, file="", source_sheets=None):
    if not active():
        return sheet
    tool, rules = _current.get()
    spec = catalog(tool)[role]
    if not spec["fields"]:
        return sheet
    rows = preview(sheet)
    configured = {name: rules["fields"][role + "|" + name] for name in spec["fields"] if role + "|" + name in rules["fields"]}
    required_names = set(spec["required"]) | set(configured)
    saved = {}
    selected_row = 0
    for profile in rules["profiles"]:
        r = int(profile.get("row", 0))
        if profile["role"] == role and 1 <= r <= len(rows) and profile_key(_title(sheet), r, rows[r - 1]) == profile["key"]:
            saved = profile["columns"]
            selected_row = r
            break
    # 自定义名称扩展识别范围，不禁用调用方原有的工作表内容识别。
    def matches(values, name):
        aliases = {normalize_alias(v) for v in configured.get(name, spec["fields"][name])}
        return [i for i, value in enumerate(values, 1) if normalize_alias(value) in aliases]
    scores = [sum(bool(matches(row, name)) for name in required_names) for row in rows]
    r = selected_row or (scores.index(max(scores)) + 1 if scores else 1)
    values = rows[r - 1] if rows else []
    if not required and not selected_row and (not scores or max(scores) < len(required_names)):
        return None
    changes, chosen, missing = {}, {}, []
    for name in spec["fields"]:
        options = matches(values, name)
        explicit = saved.get(name)
        if explicit:
            col = int(explicit)
            if not 1 <= col <= len(values) or not values[col - 1]:
                missing.append(name)
                continue
        elif name in configured:
            col = options[0] if len(options) == 1 else 0
        else:
            # 未配置的原模板保留既有的优先读取语义，不改可选字段。
            col = options[0] if options else 0
        if not col:
            if name in required_names:
                missing.append(name)
            continue
        if name in configured or explicit:
            if col in chosen and chosen[col] != name:
                missing.extend([chosen[col], name])
            chosen[col] = name
            changes[col] = name
    # 新映射不能占用另一个实际必需字段的列。
    for col, name in chosen.items():
        for other in spec["required"]:
            if other != name and col in matches(values, other) and not saved.get(other):
                missing.extend([name, other])
        # 明确选择的新列优先于原来的同义列，避免旧解析器随后又取回旧列。
        alternatives = {normalize_alias(v) for v in (*spec["fields"][name], name)}
        for other_col, value in enumerate(values, 1):
            if other_col != col and normalize_alias(value) in alternatives:
                if other_col in chosen:
                    missing.extend([name, chosen[other_col]])
                else:
                    changes[other_col] = ""
    if missing:
        request_selection(source_sheets or [sheet], [role], file=file, row=r, selected_sheet=_title(sheet),
                          message="请确认对应列：" + "、".join(field_label(n) for n in dict.fromkeys(missing)))
    return HeaderView(sheet, r, changes, role)


def sections(tool, rules):
    rules = clean_rules(tool, rules)
    result = []
    for role, spec in catalog(tool).items():
        for name, aliases in spec["fields"].items():
            key = role + "|" + name
            result.append({"kind": "fields", "key": key, "label": spec["label"] + " · " + field_label(name),
                           "selected": rules["fields"].get(key, aliases), "options": aliases, "builtins": aliases})
        result.append({"kind": "sheets", "key": role, "label": spec["label"] + " · 工作表名称",
                       "selected": rules["sheets"].get(role, spec["sheets"]), "options": spec["sheets"],
                       "builtins": spec["sheets"], "builtinRule": "原有工作表自动识别规则（始终保留）"})
    return result


def save_choice(tool, rules, issue, payload):
    rules = clean_rules(tool, rules)
    role = str(payload.get("role", ""))
    spec = next((r for r in issue["roles"] if r["key"] == role), None)
    sheet = next((s for s in issue["sheets"] if s["name"] == payload.get("sheet")), None)
    row = int(payload.get("row", 0))
    if spec is None or sheet is None or not 1 <= row <= len(sheet["rows"]):
        raise ValueError("请选择本次文件中的工作表与表头行")
    values = sheet["rows"][row - 1]
    if role == "_ignore":
        key = _ignore_key(issue["file"], sheet["name"], sheet["rows"])
        rules["profiles"] = [p for p in rules["profiles"] if p["key"] != key]
        rules["profiles"].append({"key": key, "role": role, "file": issue["file"], "sheet": sheet["name"], "row": row, "columns": {}})
        return clean_rules(tool, rules)
    columns = payload.get("columns", {})
    required = set(spec["required"]) | {k.split("|", 1)[1] for k in rules["fields"] if k.startswith(role + "|")}
    cleaned = {}
    for name in spec["fields"]:
        col = int(columns.get(name) or 0)
        if not col and name not in required:
            continue
        if not 1 <= col <= len(values) or not values[col - 1]:
            raise ValueError(f"请选择“{field_label(name)}”在原表中的列")
        if col in cleaned.values():
            raise ValueError("不同字段不能选择同一列")
        cleaned[name] = col
    if spec.get("one_of") and not any(name in cleaned for name in spec["one_of"]):
        raise ValueError("请至少选择一项金额对应列；个人、单位及险种不同的金额请分别选择")
    key = profile_key(sheet["name"], row, values)
    rules["profiles"] = [p for p in rules["profiles"] if p["key"] != key]
    rules["profiles"].append({"key": key, "role": role, "sheet": sheet["name"], "row": row, "columns": cleaned})
    return clean_rules(tool, rules)
