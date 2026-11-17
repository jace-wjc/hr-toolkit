"""Explicit company/location rules and remembered attendance source assignments.

Matching is exact unless the user supplies a filename keyword. No company or
location is inferred from an unconfirmed filename or from the legacy HQ fallback.
"""
from __future__ import annotations

from copy import deepcopy
import hashlib
import json
import re
import unicodedata


COMPANY_DEFAULT = "公司默认"
DEFAULT_RULES = [
    {"company": "总部", "location": "", "valid_months": 3, "hours_per_day": 7},
    {"company": "唐人", "location": "", "valid_months": 3, "hours_per_day": 7},
    {"company": "几维", "location": "", "valid_months": 6, "hours_per_day": 7},
    {"company": "北京", "location": "", "valid_months": 12, "hours_per_day": 7},
    {"company": "", "location": "南昌", "valid_months": 3, "hours_per_day": 7},
    # Shenzhen's hours are confirmed; its expiry still comes from the company.
    {"company": "", "location": "深圳", "valid_months": 0, "hours_per_day": 8},
]


def normalized(value):
    return re.sub(r"\s+", "", unicodedata.normalize("NFKC", str(value or ""))).casefold()


def _number(value, options, label):
    try:
        if isinstance(value, bool) or float(value) not in options:
            raise ValueError
        return int(float(value))
    except (ValueError, TypeError):
        raise ValueError(f"{label}设置有误，请重新选择。") from None


def assignment_key(item):
    return tuple(str(item.get(key) or "") for key in (
        "source", "keyword", "sheet", "raw_company", "raw_location", "name", "department"))


def clean_config(payload=None):
    if payload is None:
        return {"version": 1, "rules": deepcopy(DEFAULT_RULES), "assignments": []}
    if not isinstance(payload, dict):
        raise ValueError("考勤识别规则格式有误。")
    result = {"version": 1, "rules": [], "assignments": []}
    seen = set()
    rules = payload.get("rules", DEFAULT_RULES)
    assignments = payload.get("assignments", [])
    if not isinstance(rules, list) or not isinstance(assignments, list):
        raise ValueError("考勤识别规则格式有误。")
    for rule in rules:
        if not isinstance(rule, dict):
            raise ValueError("公司/驻地规则格式有误。")
        company, location = str(rule.get("company") or "").strip(), str(rule.get("location") or "").strip()
        key = normalized(company), normalized(location)
        if not any(key) or key in seen:
            raise ValueError("公司/驻地规则为空或重复，请合并为一条。")
        seen.add(key)
        months = _number(rule.get("valid_months", 0), {0, 3, 6, 12}, "有效期")
        hours = _number(rule.get("hours_per_day", 0), {0, 7, 8}, "每天工时")
        if not months and not hours:
            raise ValueError("每条规则至少需要指定有效期或每天工时。")
        result["rules"].append(dict(company=company, location=location, valid_months=months, hours_per_day=hours))
    seen = set()
    for item in assignments:
        if not isinstance(item, dict):
            raise ValueError("已记住的资料归属格式有误。")
        entry = {key: str(item.get(key) or "").strip() for key in (
            "source", "original_source", "keyword", "sheet", "raw_company", "raw_location", "name", "department", "company", "location", "label")}
        entry["original_source"] = entry["original_source"] or entry["source"]
        if bool(entry["source"]) == bool(entry["keyword"]) or not entry["company"] or not entry["location"]:
            raise ValueError("资料归属需要指定文件、公司和驻地。")
        key = assignment_key(entry)
        if key in seen:
            raise ValueError("资料归属设置重复，请只保留一条。")
        seen.add(key)
        entry["valid_months"] = _number(item.get("valid_months", 0), {0, 3, 6, 12}, "有效期")
        entry["hours_per_day"] = _number(item.get("hours_per_day", 0), {0, 7, 8}, "每天工时")
        result["assignments"].append(entry)
    return result


def record_id(record):
    values = [record.get(key, "") for key in ("source", "sheet", "raw_company", "raw_location", "name", "department", "kind")]
    return hashlib.sha256(json.dumps(values, ensure_ascii=False).encode()).hexdigest()


def match_rule(config, company, location):
    # An unfamiliar spelling of 南昌 must not silently receive 几维's six-month
    # company default. Users can select a known location or 公司默认 explicitly.
    if (location and normalized(location) != normalized(COMPANY_DEFAULT)
            and not any(normalized(rule["location"]) == normalized(location)
                        and normalized(rule["company"]) in {"", normalized(company)} for rule in config["rules"])):
        return 0, 0
    months, hours = 0, 0
    matched = []
    for wanted in ((normalized(company), ""), ("", normalized(location)), (normalized(company), normalized(location))):
        if not any(wanted) or wanted in matched:
            continue
        matched.append(wanted)
        for rule in config["rules"]:
            if (normalized(rule["company"]), normalized(rule["location"])) == wanted:
                months = rule["valid_months"] or months
                hours = rule["hours_per_day"] or hours
    return months, hours


def _assignment(record, config):
    matches = []
    for item in config["assignments"]:
        if item["sheet"] != record["sheet"] or item["raw_company"] != record["raw_company"] or item["raw_location"] != record["raw_location"]:
            continue
        if item["source"]:
            if item["source"] != record["source"]:
                continue
        elif normalized(item["keyword"]) not in normalized(record["file"]):
            continue
        if item["name"] and (item["name"], item["department"]) != (record["name"], record["department"]):
            continue
        matches.append((2 * bool(item["name"]) + bool(item["source"]), item))
    if not matches:
        return None, ""
    priority = max(rank for rank, _ in matches)
    best = [item for rank, item in matches if rank == priority]
    targets = {(item["company"], item["location"], item["valid_months"], item["hours_per_day"]) for item in best}
    if len(targets) > 1:
        return None, "命中多条不同的资料归属，请修改已记住的规则"
    return best[0], ""


def resolve_records(records, config):
    config = clean_config(config)
    result = []
    for original in records:
        row = dict(original)
        row["id"] = record_id(row)
        saved, problem = _assignment(row, config)
        row["company"] = saved["company"] if saved else row["raw_company"]
        row["location"] = saved["location"] if saved else row["raw_location"]
        months, hours = match_rule(config, row["company"], row["location"])
        if saved:
            months, hours = saved["valid_months"] or months, saved["hours_per_day"] or hours
        row["matched_by"] = "已记住的资料归属" if saved else "原表公司/驻地"
        row["assignment_conflict"] = bool(problem)
        old_rule = row.get("saved_rule")
        if row["kind"] == "history" and old_rule and not saved and not row["location"]:
            months, hours = old_rule["valid_months"], old_rule["hours_per_day"]
            row["matched_by"] = "旧表已确认的规则"
        if not problem:
            if not row["company"]:
                problem = "请指定公司"
            elif not row["location"] and not (row["kind"] == "history" and old_rule):
                problem = "请指定驻地，或明确使用公司默认规则"
            elif not months or not hours:
                problem = "公司/驻地尚未匹配完整规则，请重新选择或维护规则"
        row.update(valid_months=months, hours_per_day=hours, problem=problem)
        if row["kind"] == "history":
            row["source_hours_per_day"] = (old_rule or {}).get("hours_per_day") or hours
        result.append(row)
    # A current employee's confirmed location supplies the carryover policy.
    # Historical day values still use the historical hours/day when being read.
    current = {}
    for row in result:
        if row["kind"] == "current" and not row["problem"]:
            key = row["company"], row["department"], row["name"]
            current.setdefault(key, set()).add((row["valid_months"], row["hours_per_day"], row["location"]))
    for row in result:
        key = row["company"], row["department"], row["name"]
        matches = current.get(key, set())
        if len(matches) > 1:
            row["problem"] = "同一公司、部门和姓名匹配到不同规则，请核对人员归属"
        elif row["kind"] == "history" and len(matches) == 1 and not row["assignment_conflict"]:
            row["valid_months"], row["hours_per_day"], row["location"] = next(iter(matches))
            row["problem"] = ""
            row["matched_by"] = "沿用本次同一人员的规则"
    return result


def assign_records(config, records, selections):
    """Bulk file assignments collapse to one rule; partial selections remain person-specific."""
    config = clean_config(config)
    if not isinstance(selections, dict):
        raise ValueError("人员选择格式有误。")
    indexed = {record_id(row): row for row in records}
    if set(selections) - set(indexed):
        raise ValueError("资料已变化，请重新查看本次分配。")
    groups = {}
    for row in records:
        group = tuple(row[key] for key in ("source", "sheet", "raw_company", "raw_location"))
        groups.setdefault(group, []).append(row)
    entries = {assignment_key(item): item for item in config["assignments"]}
    for group, members in groups.items():
        chosen = [(row, selections[record_id(row)]) for row in members if record_id(row) in selections]
        if not chosen:
            continue
        for row, value in chosen:
            if not isinstance(value, dict):
                raise ValueError("人员分配格式有误。")
            keyword = str(value.get("keyword") or "").strip()
            if keyword and normalized(keyword) not in normalized(row["file"]):
                raise ValueError(f"文件“{row['file']}”不含关键词“{keyword}”，请核对。")
        signatures = {json.dumps(value, sort_keys=True, ensure_ascii=False) for _, value in chosen}
        whole_file = len(chosen) == len(members) and len(signatures) == 1
        for row, value in chosen[:1] if whole_file else chosen:
            keyword = str(value.get("keyword") or "").strip()
            entry = dict(source="" if keyword else row["source"], original_source=row["source"], keyword=keyword, sheet=row["sheet"],
                         raw_company=row["raw_company"], raw_location=row["raw_location"],
                         name="" if whole_file else row["name"], department="" if whole_file else row["department"],
                         company=str(value.get("company") or "").strip(), location=str(value.get("location") or "").strip(),
                         valid_months=value.get("valid_months", 0), hours_per_day=value.get("hours_per_day", 0),
                         label=row["file"] + " / " + row["sheet"] + (" / 全组人员" if whole_file else " / " + row["name"]))
            # Reassigning also replaces this source's old exact-path/keyword choice.
            # A person-only change keeps the group's default for everyone else.
            entries = {key: item for key, item in entries.items() if not (
                (item["source"] == row["source"] or item["original_source"] == row["source"]
                 or bool(keyword) and item["keyword"] == keyword)
                and item["sheet"] == entry["sheet"] and item["raw_company"] == entry["raw_company"]
                and item["raw_location"] == entry["raw_location"]
                and (whole_file or (item["name"], item["department"]) == (entry["name"], entry["department"])))}
            entries[assignment_key(entry)] = entry
    config["assignments"] = list(entries.values())
    return clean_config(config)
