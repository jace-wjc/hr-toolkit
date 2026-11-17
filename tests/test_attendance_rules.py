from __future__ import annotations

import unittest

from hr_toolkit.attendance_rules import assign_records, clean_config, match_rule, record_id, resolve_records


def source(name="张三", company="", location="", **changes):
    row = dict(source="/资料/几维9月日报.xlsx", file="几维9月日报.xlsx", sheet="日结果",
               raw_company=company, raw_location=location, name=name, department="运营部", kind="current")
    row.update(changes)
    return row


def selection(company="几维", location="公司默认", **changes):
    return dict(company=company, location=location, **changes)


class AttendanceRulesTests(unittest.TestCase):
    def test_company_location_and_more_specific_rule_precedence(self):
        config = clean_config()
        self.assertEqual(match_rule(config, "几维", "公司默认"), (6, 7))
        self.assertEqual(match_rule(config, "几维", "南昌"), (3, 7))
        self.assertEqual(match_rule(config, "几维", "深圳"), (6, 8))
        self.assertEqual(match_rule(config, "未配置公司", "深圳"), (0, 8))
        config["rules"].append(dict(company="几维", location="深圳", valid_months=12, hours_per_day=0))
        self.assertEqual(match_rule(config, "几维", "深圳"), (12, 8))

    def test_unknown_company_or_location_is_not_guessed_from_filename(self):
        rows = resolve_records([source(), source(company="几维"), source(company="其他公司", location="深圳")], clean_config())
        self.assertTrue(all(row["problem"] for row in rows))
        self.assertEqual(rows[0]["company"], "")
        spelled_out = resolve_records([source(company="几维", location="江西省南昌市")], clean_config())[0]
        self.assertTrue(spelled_out["problem"])

    def test_bulk_assignment_applies_to_new_people_but_not_changed_source_fields(self):
        rows = [source(), source("李四")]
        config = assign_records(clean_config(), rows, {record_id(row): selection(location="南昌") for row in rows})
        self.assertEqual(len(config["assignments"]), 1)
        self.assertEqual(config["assignments"][0]["name"], "")
        new_person = resolve_records([source("王五")], config)[0]
        self.assertEqual((new_person["company"], new_person["valid_months"]), ("几维", 3))
        self.assertFalse(new_person["problem"])
        changed = resolve_records([source(company="唐人", location="")], config)[0]
        self.assertTrue(changed["problem"])
        self.assertEqual(changed["company"], "唐人")

    def test_person_exception_and_whole_group_reassignment(self):
        rows = [source(), source("李四")]
        config = assign_records(clean_config(), rows, {record_id(row): selection() for row in rows})
        config = assign_records(config, rows, {record_id(rows[0]): selection(location="深圳", valid_months=12)})
        resolved = resolve_records(rows, config)
        self.assertEqual([(row["valid_months"], row["hours_per_day"]) for row in resolved], [(12, 8), (6, 7)])
        config = assign_records(config, rows, {record_id(row): selection(location="南昌", keyword="几维") for row in rows})
        self.assertEqual(len(config["assignments"]), 1)
        self.assertEqual([row["valid_months"] for row in resolve_records(rows, config)], [3, 3])
        next_month = source(file="几维10月日报.xlsx", source="/资料/几维10月日报.xlsx")
        self.assertFalse(resolve_records([next_month], config)[0]["problem"])

    def test_edit_or_delete_remembered_assignment_takes_effect(self):
        row = source()
        config = assign_records(clean_config(), [row], {record_id(row): selection()})
        config["assignments"][0]["location"] = "南昌"
        self.assertEqual(resolve_records([row], config)[0]["valid_months"], 3)
        config["assignments"] = []
        self.assertTrue(resolve_records([row], config)[0]["problem"])

    def test_same_name_in_different_companies_is_independent(self):
        rows = [source(company="几维", location="公司默认"), source(company="唐人", location="公司默认")]
        resolved = resolve_records(rows, clean_config())
        self.assertFalse(any(row["problem"] for row in resolved))
        self.assertEqual([row["valid_months"] for row in resolved], [6, 3])

    def test_conflicting_filename_rules_are_not_hidden_by_history_inheritance(self):
        old = source(company="几维", kind="history")
        config = assign_records(clean_config(), [old], {record_id(old): selection(keyword="几维")})
        other = dict(config["assignments"][0], keyword="日报", location="深圳")
        config["assignments"].append(other)
        current = source(company="几维", location="南昌")
        resolved = resolve_records([current, old], config)
        self.assertTrue(resolved[1]["problem"])
        self.assertIn("多条", resolved[1]["problem"])

    def test_history_inherits_current_policy_but_retains_original_day_conversion(self):
        current = source(company="几维", location="南昌")
        old = source(company="几维", kind="history", saved_rule={"valid_months": 6, "hours_per_day": 8})
        row = resolve_records([current, old], clean_config())[1]
        self.assertFalse(row["problem"])
        self.assertEqual((row["valid_months"], row["hours_per_day"], row["source_hours_per_day"]), (3, 7, 8))

    def test_invalid_keyword_and_duplicate_rules_are_rejected(self):
        row = source()
        with self.assertRaises(ValueError):
            assign_records(clean_config(), [row], {record_id(row): selection(keyword="不匹配")})
        config = clean_config()
        config["rules"].append(dict(config["rules"][0]))
        with self.assertRaises(ValueError):
            clean_config(config)
