"""六个输入适配入口及只读映射的回归用例；不依赖业务原始数据。"""
from __future__ import annotations

import inspect
import json
import tempfile
import unittest
from unittest.mock import patch
from datetime import datetime
from pathlib import Path

from openpyxl import Workbook

from hr_toolkit.common.excel import SheetGrid
from hr_toolkit.common.template_mapping import (
    SUPPORTED_TOOLS, TemplateSelectionRequired, active, catalog, choose_sheet,
    clean_rules, ignored_sheet, map_sheet, request_selection, save_choice, template_tool,
)


def sheet(headers, data=None, name="Sheet1"):
    wb = Workbook()
    ws = wb.active
    ws.title = name
    ws.append(headers)
    if data is not None:
        ws.append(data)
    return ws


def invoke(tool, callback, rules=None):
    return template_tool(tool)(callback)(template_rules={} if rules is None else rules)


class TemplateMappingTest(unittest.TestCase):
    def test_summary_with_renamed_name_suggests_summary_without_changing_parser(self):
        from hr_toolkit.tools.data_statistics import _adapt_statistics_grid
        ws = sheet(["222", "应出勤天数", "实际出勤天数", "请假天数"], ["张三", 19, 19, 0], name="考勤表")
        self.addCleanup(ws.parent.close)
        grid = SheetGrid(ws)
        self.assertIsNone(invoke("data_statistics", lambda: _adapt_statistics_grid(grid, "考勤.xlsx")))
        with self.assertRaises(TemplateSelectionRequired) as caught:
            invoke("data_statistics", lambda: request_selection([grid], ["attendance", "attendance_summary", "weekly", "monthly"], file="考勤.xlsx"))
        issue = caught.exception.payload
        self.assertEqual(issue["suggested_role"], "attendance_summary")
        spec = next(role for role in issue["roles"] if role["key"] == issue["suggested_role"])
        self.assertEqual(spec["required"], ["姓名"])
        rules = save_choice("data_statistics", {}, issue,
                            {"role": "attendance_summary", "sheet": "考勤表", "row": 1, "columns": {"姓名": 1}})
        mapped = invoke("data_statistics", lambda: _adapt_statistics_grid(grid, "考勤.xlsx"), rules)
        self.assertEqual(mapped.mapping_role, "attendance_summary")
        self.assertEqual(mapped.cell(2, 1).value, "张三")
        self.assertEqual(ws.cell(1, 1).value, "222")

    def test_role_suggestion_does_not_guess_ambiguous_weekly_monthly(self):
        ws = sheet(["汇报编号", "汇报人", "汇报时间"])
        self.addCleanup(ws.parent.close)
        with self.assertRaises(TemplateSelectionRequired) as caught:
            invoke("data_statistics", lambda: request_selection([ws], ["weekly", "monthly"]))
        self.assertEqual(caught.exception.payload["suggested_role"], "")

    def test_saved_choice_can_be_edited_using_headers_without_saving_personal_rows(self):
        from hr_toolkit.common.template_mapping import profile_issue, saved_choices
        ws = sheet(["222", "名字", "应出勤天数"], [28, "测试人员", 20], name="考勤表")
        self.addCleanup(ws.parent.close)
        with self.assertRaises(TemplateSelectionRequired) as caught:
            invoke("data_statistics", lambda: map_sheet(ws, "attendance_summary"))
        rules = save_choice("data_statistics", {}, caught.exception.payload,
                            {"role": "attendance_summary", "sheet": "考勤表", "row": 1, "columns": {"姓名": 1}})
        profile = rules["profiles"][0]
        self.assertNotIn("测试人员", json.dumps(profile, ensure_ascii=False))
        self.assertIn("姓名 ← 222", saved_choices("data_statistics", rules)[0]["description"])
        issue = profile_issue("data_statistics", rules, profile["key"])
        updated = save_choice("data_statistics", rules, issue,
                              {"role": "attendance_summary", "sheet": "考勤表", "row": 1, "columns": {"姓名": 2}})
        self.assertEqual(len(updated["profiles"]), 1)
        mapped = invoke("data_statistics", lambda: map_sheet(ws, "attendance_summary"), updated)
        self.assertEqual(mapped.cell(1, 1).value, "222")
        self.assertEqual(mapped.cell(1, 2).value, "姓名")
        self.assertEqual(mapped.cell(2, 2).value, "测试人员")
        legacy = {"profiles": [{k: v for k, v in profile.items() if k not in {"headers", "required", "one_of", "file"}}]}
        self.assertFalse(saved_choices("data_statistics", legacy)[0]["editable"])
        self.assertEqual(invoke("data_statistics", lambda: map_sheet(ws, "attendance_summary"), legacy).cell(1, 1).value, "姓名")
        with self.assertRaisesRegex(ValueError, "删除后重新处理"):
            profile_issue("data_statistics", legacy, profile["key"])

    def test_normalization_is_reused_without_changing_source_or_column_priority(self):
        from hr_toolkit.common import template_mapping as mapping
        marker = " 唯一未使用表头 "
        ws = sheet(["公司", "姓名", "姓名", "身份证", marker], ["甲", "原姓名", "后姓名", "TEST-001", "值"])
        with patch.object(mapping, "normalize_alias", wraps=mapping.normalize_alias) as normalize:
            mapped = invoke("archive_import", lambda: map_sheet(ws, "transfer"))
        self.assertEqual(sum(call.args == (marker,) for call in normalize.call_args_list), 1)
        self.assertEqual(mapped.header_row, 1)
        self.assertEqual(mapped.changes, {})
        self.assertEqual(ws.cell(1, 5).value, marker)
        self.assertEqual(mapped.cell(2, 2).value, "原姓名")
        self.assertEqual(mapped.cell(2, 3).value, "后姓名")
        ws.parent.close()

    def test_prompt_labels_do_not_change_internal_fields_or_source(self):
        ws = sheet(["名字", "证件编号"], ["示例人员", "TEST-001"], name="增员")
        ws.parent.create_sheet("说明", 0)
        with self.assertRaises(TemplateSelectionRequired) as caught:
            invoke("social_security", lambda: map_sheet(ws, "roster", file="异动表.xlsx", source_sheets=ws.parent.worksheets))
        payload = caught.exception.payload
        self.assertEqual(payload["selected_sheet"], "增员")
        self.assertEqual(payload["sheets"][0]["name"], "说明")
        role = payload["roles"][0]
        self.assertEqual(role["field_labels"]["*姓名.简体中文"], "姓名")
        self.assertEqual(role["field_labels"]["*身份证"], "身份证号码")
        self.assertIn("*姓名.简体中文", role["required"])
        self.assertEqual(role["fields"]["*姓名.简体中文"], ["*姓名.简体中文"])
        self.assertNotIn("简体中文", payload["message"])
        self.assertEqual(ws.cell(1, 1).value, "名字")

    def test_prompt_still_rejects_missing_and_duplicate_required_columns(self):
        ws = sheet(["名字", "证件编号"], ["示例人员", "TEST-001"])
        with self.assertRaises(TemplateSelectionRequired) as caught:
            invoke("social_security", lambda: map_sheet(ws, "roster"))
        payload = caught.exception.payload
        base = {"role": "roster", "sheet": "Sheet1", "row": 1}
        with self.assertRaisesRegex(ValueError, "身份证号码"):
            save_choice("social_security", {}, payload, {**base, "columns": {"*姓名.简体中文": 1}})
        with self.assertRaisesRegex(ValueError, "同一列"):
            save_choice("social_security", {}, payload, {**base, "columns": {"*姓名.简体中文": 1, "*身份证": 1}})

    def test_all_six_entrypoints_accept_serializable_rules(self):
        from hr_toolkit.tools.registry import get_tool_by_id
        self.assertEqual(len(SUPPORTED_TOOLS), 6)
        for tool in SUPPORTED_TOOLS:
            with self.subTest(tool=tool):
                function = get_tool_by_id(tool).entry_point
                self.assertIn("template_rules", inspect.signature(function).parameters)
                self.assertTrue(catalog(tool))
                self.assertEqual(clean_rules(tool, {}), {"fields": {}, "sheets": {}, "profiles": []})

    def test_three_alternative_names_and_read_only_grid_view(self):
        rules = {"fields": {"transfer|姓名": ["姓名", "名字", "name"]}}
        for name in ("姓名", "名字", "ＮＡＭＥ"):
            ws = sheet(["公司", name, "身份证"], ["甲公司", "测试人员", "TEST-001"])
            grid = SheetGrid(ws)
            mapped = invoke("archive_import", lambda: map_sheet(grid, "transfer"), rules)
            self.assertEqual(mapped.cell(1, 2).value, "姓名")
            self.assertEqual(mapped.value(2, 2), "测试人员")
            self.assertEqual(grid.cell(1, 2).value, name)
            self.assertEqual(ws.cell(1, 2).value, name)

    def test_missing_name_cannot_be_swallowed_as_nonbusiness_value_error(self):
        ws = sheet(["公司", "新称呼", "身份证"])
        with self.assertRaises(TemplateSelectionRequired) as caught:
            invoke("archive_import", lambda: map_sheet(ws, "transfer"))
        self.assertNotIsInstance(caught.exception, ValueError)
        self.assertEqual(caught.exception.payload["roles"][0]["required"], ["公司", "姓名", "身份证"])
        self.assertFalse(active())

    def test_ambiguous_columns_require_choice_and_saved_choice_is_structural(self):
        ws = sheet(["公司", "姓名", "名字", "身份证"], ["甲公司", "甲", "乙", "TEST-001"])
        rules = {"fields": {"transfer|姓名": ["姓名", "名字"]}}
        with self.assertRaises(TemplateSelectionRequired) as caught:
            invoke("archive_import", lambda: map_sheet(ws, "transfer"), rules)
        saved = save_choice("archive_import", rules, caught.exception.payload,
                            {"role": "transfer", "sheet": "Sheet1", "row": 1,
                             "columns": {"公司": 1, "姓名": 3, "身份证": 4}})
        mapped = invoke("archive_import", lambda: map_sheet(ws, "transfer"), saved)
        self.assertEqual(mapped.cell(1, 3).value, "姓名")
        self.assertEqual(mapped.cell(1, 2).value, "")
        self.assertEqual(mapped.cell(2, 3).value, "乙")
        self.assertEqual(ws.cell(1, 2).value, "姓名")
        ws.cell(1, 4).value = "更换证件列"
        with self.assertRaises(TemplateSelectionRequired):
            invoke("archive_import", lambda: map_sheet(ws, "transfer"), saved)

    def test_optional_fields_only_become_required_when_configured(self):
        ws = sheet(["姓名", "身份证号码"])
        self.assertIsNotNone(invoke("insurance_ledger", lambda: map_sheet(ws, "policy")))
        with self.assertRaises(TemplateSelectionRequired):
            invoke("insurance_ledger", lambda: map_sheet(ws, "policy"),
                   {"fields": {"policy|每人伤残死亡限额": ["保额"]}})

    def test_missing_and_multiple_sheets_prompt_and_single_alias_matches(self):
        ws = sheet(["公司", "姓名", "身份证"], name="明细A")
        wb = ws.parent
        rules = {"sheets": {"transfer": ["明细A", "明细B"]}}
        self.assertIs(invoke("archive_import", lambda: choose_sheet(wb.worksheets, "transfer"), rules), ws)
        wb.create_sheet("明细B")
        with self.assertRaises(TemplateSelectionRequired):
            invoke("archive_import", lambda: choose_sheet(wb.worksheets, "transfer"), rules)
        with self.assertRaises(TemplateSelectionRequired):
            invoke("archive_import", lambda: choose_sheet(wb.worksheets, "transfer"), {"sheets": {"transfer": ["不存在"]}})

    def test_optional_change_type_absent_does_not_require_all_four_sheets(self):
        ws = sheet(["序号", "姓名", "离职日期"], name="减员")
        self.assertIsNone(invoke("personnel_change_merge", lambda: choose_sheet(ws.parent.worksheets, "增员", required=False, allow_absent=True),
                                 {"sheets": {"增员": ["入职人员"]}}))

    def test_xls_and_grid_header_values_are_equal(self):
        class XlsSheet:
            name = "Sheet1"
            nrows, ncols = 2, 3
            rows = [["名字", "证件号码", "缴费基数"], ["测试人员", "TEST-001", 500]]
            def row_values(self, r): return list(self.rows[r])
            def cell_value(self, r, c): return self.rows[r][c]
        rules = {"fields": {"payment|姓名": ["名字"]}}
        old = XlsSheet()
        xls = invoke("social_security", lambda: map_sheet(old, "payment"), rules)
        grid = SheetGrid(sheet(old.rows[0], old.rows[1]))
        xlsx = invoke("social_security", lambda: map_sheet(grid, "payment"), rules)
        self.assertEqual(xls.row_values(0), [xlsx.cell(1, c).value for c in range(1, 4)])
        self.assertEqual(xls.cell_value(1, 2), xlsx.cell(2, 3).value)
        self.assertEqual(old.rows[0][0], "名字")

    def test_context_resets_even_when_mapping_fails(self):
        with self.assertRaises(RuntimeError):
            invoke("archive_import", lambda: (_ for _ in ()).throw(RuntimeError("stop")))
        self.assertFalse(active())
        ws = sheet(["任意列"])
        self.assertIs(map_sheet(ws, "transfer"), ws)

    def test_name_aliases_do_not_change_salary_layout_or_source_headers(self):
        from hr_toolkit.tools.salary_split import _detect_layout
        ws = sheet(["序号", "入职公司", "姓名", "身份证号码", "应发小计"], name="明细")
        ws.parent.create_sheet("汇总")
        before = _detect_layout(ws.parent)
        self.assertEqual(invoke("salary_split", lambda: _detect_layout(ws.parent)), before)
        ws.cell(1, 3).value = "name"
        after = invoke("salary_split", lambda: _detect_layout(ws.parent), {"fields": {"detail|姓名": ["name"]}})
        self.assertEqual(after, before)
        self.assertEqual(ws.cell(1, 3).value, "name")

    def test_reader_results_equal_with_empty_rules(self):
        from hr_toolkit.tools.archive_import import _read_transfer_file
        from hr_toolkit.tools.insurance_ledger import _read_policy_file
        from hr_toolkit.tools.personnel_change_merge import _read_change_file
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            examples = [
                ("archive_import", _read_transfer_file, sheet(["公司", "姓名", "身份证"], ["甲公司", "测试人员", "TEST-001"])),
                ("insurance_ledger", lambda p: _read_policy_file(p, []), sheet(["姓名", "身份证号码", "每人伤残死亡限额"], ["测试人员", "TEST-001", 600000])),
                ("personnel_change_merge", _read_change_file, sheet(["序号", "姓名", "入职日期"], [1, "测试人员", datetime(2026, 8, 1)], name="增员")),
            ]
            for tool, reader, ws in examples:
                path = root / (tool + "_202608.xlsx")
                ws.parent.save(path)
                original = path.read_bytes()
                baseline = reader(path)
                self.assertEqual(invoke(tool, lambda: reader(path)), baseline)
                self.assertEqual(path.read_bytes(), original)

    def test_report_sheet_renaming_does_not_guess_weekly_or_monthly(self):
        from hr_toolkit.tools.data_statistics import _adapt_statistics_grid
        grid = SheetGrid(sheet(["汇报编号", "汇报人", "汇报时间"], ["R001", "测试人员", datetime(2026, 8, 1)], name="数据"))
        with self.assertRaises(TemplateSelectionRequired) as caught:
            invoke("data_statistics", lambda: _adapt_statistics_grid(grid, "数据.xlsx"))
        self.assertEqual([r["key"] for r in caught.exception.payload["roles"]], ["weekly", "monthly"])

    def test_ignore_is_explicit_and_bound_to_file_and_preview(self):
        ws = sheet(["填写说明"], ["说明文字"])
        with self.assertRaises(TemplateSelectionRequired) as caught:
            invoke("data_statistics", lambda: request_selection([ws], ["weekly"], file="说明.xlsx", allow_ignore=True))
        saved = save_choice("data_statistics", {}, caught.exception.payload,
                            {"role": "_ignore", "sheet": "Sheet1", "row": 1, "columns": {}})
        saved = json.loads(json.dumps(saved))
        self.assertTrue(invoke("data_statistics", lambda: ignored_sheet(ws, "说明.xlsx"), saved))
        self.assertFalse(invoke("data_statistics", lambda: ignored_sheet(ws, "别的文件.xlsx"), saved))
        ws.cell(1, 1).value = "汇报人"
        self.assertFalse(invoke("data_statistics", lambda: ignored_sheet(ws, "说明.xlsx"), saved))


if __name__ == "__main__":
    unittest.main()
