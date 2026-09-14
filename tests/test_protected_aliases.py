"""内置名称只读、自定义名称增删改的持久化规则。"""
from __future__ import annotations

import json
import unittest

from hr_toolkit.common.header_aliases import protected_aliases, normalize_alias
from hr_toolkit.common.template_mapping import SUPPORTED_TOOLS, catalog, clean_rules, sections
from hr_toolkit.tools.salary_headers import ALIAS_PROFILE_KEY, ALIASES, SHEET_ALIASES, alias_rules


class ProtectedAliasesTest(unittest.TestCase):
    def test_builtin_cannot_be_removed_or_replaced(self):
        self.assertEqual(protected_aliases(["姓名"], []), ["姓名"])
        self.assertEqual(protected_aliases(["姓名"], ["名字", "name"]), ["姓名", "名字", "name"])
        self.assertEqual(protected_aliases(["name"], ["ＮＡＭＥ", "Name"]), ["name"])

    def test_salary_add_edit_delete_and_restart_roundtrip(self):
        def saved(values):
            return alias_rules({ALIAS_PROFILE_KEY: json.loads(json.dumps({"fields": {"name": values}}, ensure_ascii=False))})
        self.assertEqual(saved(["名字", "name"])["fields"]["name"], ["姓名", "名字", "name"])
        self.assertEqual(saved(["名字", "员工名称"])["fields"]["name"], ["姓名", "名字", "员工名称"])
        self.assertEqual(saved(["员工名称"])["fields"]["name"], ["姓名", "员工名称"])
        self.assertEqual(saved([])["fields"], {})  # 清空自定义名称，恢复内置优先级。

    def test_six_tools_preserve_every_builtin_field(self):
        for tool in SUPPORTED_TOOLS:
            for role, spec in catalog(tool).items():
                for field, builtins in spec["fields"].items():
                    with self.subTest(tool=tool, role=role, field=field):
                        key = role + "|" + field
                        custom = "__测试自定义列__"
                        rules = clean_rules(tool, {"fields": {key: [custom]}})
                        actual = {normalize_alias(v) for v in rules["fields"][key]}
                        self.assertTrue({normalize_alias(v) for v in builtins}.issubset(actual))
                        self.assertIn(custom, actual)
                        edited = clean_rules(tool, {"fields": {key: ["__修改后的列__"]}})
                        self.assertNotIn(custom, edited["fields"][key])
                        deleted = clean_rules(tool, {"fields": {key: []}})
                        self.assertNotIn(key, deleted["fields"])
                        section = next(s for s in sections(tool, deleted) if s["kind"] == "fields" and s["key"] == key)
                        self.assertEqual(section["selected"], section["builtins"])

    def test_builtin_sheet_names_cannot_be_removed(self):
        for role, builtins in SHEET_ALIASES.items():
            rules = alias_rules({ALIAS_PROFILE_KEY: {"sheets": {role: ["自定义工作表"]}}})
            self.assertTrue(set(builtins).issubset(rules["sheets"][role]))
            self.assertNotIn(role, alias_rules({ALIAS_PROFILE_KEY: {"sheets": {role: []}}})["sheets"])
        for tool in SUPPORTED_TOOLS:
            for role, spec in catalog(tool).items():
                rules = clean_rules(tool, {"sheets": {role: ["自定义工作表"]}})
                self.assertTrue(set(spec["sheets"]).issubset(rules["sheets"][role]))
                self.assertNotIn(role, clean_rules(tool, {"sheets": {role: []}})["sheets"])

    def test_defaults_only_do_not_make_optional_fields_required(self):
        for tool in SUPPORTED_TOOLS:
            payload = {"fields": {}, "sheets": {}}
            for section in sections(tool, {}):
                payload[section["kind"]][section["key"]] = section["selected"]
            actual = clean_rules(tool, payload)
            self.assertEqual(actual["fields"], {})
            self.assertEqual(actual["sheets"], {})

    def test_custom_name_cannot_hijack_another_builtin_field(self):
        with self.assertRaises(ValueError):
            clean_rules("archive_import", {"fields": {"transfer|姓名": ["身份证"]}})
        with self.assertRaises(ValueError):
            alias_rules({ALIAS_PROFILE_KEY: {"fields": {"name": ["身份证号码"]}}})


if __name__ == "__main__":
    unittest.main()
