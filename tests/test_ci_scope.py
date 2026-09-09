"""Regression coverage for CI selection; never run application builds here."""

import importlib.util
import json
import os
from pathlib import Path
import unittest
from unittest.mock import patch


SPEC = importlib.util.spec_from_file_location(
    "ci_scope", Path(__file__).resolve().parents[1] / "scripts" / "ci_scope.py"
)
ci_scope = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(ci_scope)


class CIScopeTests(unittest.TestCase):
    def test_documentation_only_skips_runtime_jobs(self):
        scope = ci_scope.select_scope(["README.md", "AGENTS.md"])
        self.assertFalse(scope["run"])
        self.assertFalse(scope["audit"])
        self.assertFalse(scope["full"])

    def test_paths_include_callers_without_material_collection_suite(self):
        scope = ci_scope.select_scope(["hr_toolkit/common/paths.py"])
        for name in ("paths", "project_store", "history_store", "background_process", "qt_controller"):
            self.assertIn("tests.test_" + name, scope["targets"])
        self.assertNotIn("tests.test_material_collector", scope["targets"])
        self.assertFalse(scope["full"])

    def test_material_change_includes_related_tests(self):
        scope = ci_scope.select_scope(["hr_toolkit/tools/material_collector.py"])
        self.assertIn("tests.test_material_collector", scope["targets"])
        self.assertIn("tests.test_material_document_groups", scope["targets"])
        self.assertTrue(scope["ocr_smoke"])
        self.assertNotIn("tests.test_material_collector", scope["win7_targets"])

    def test_ci_workflow_change_uses_focused_contract_test(self):
        scope = ci_scope.select_scope([".github/workflows/ci.yml"])
        self.assertEqual(set(scope["targets"]), {"tests.test_ci_scope", ci_scope.PIN_TEST})
        self.assertFalse(scope["audit"])

    def test_dependencies_enable_audit_and_smoke_without_full_discovery(self):
        scope = ci_scope.select_scope(["requirements-win7.txt"])
        self.assertTrue(scope["audit"])
        self.assertTrue(scope["qt_smoke"])
        self.assertTrue(scope["ocr_smoke"])
        self.assertFalse(scope["full"])

    def test_unknown_application_code_requires_mapping(self):
        with self.assertRaisesRegex(ValueError, "Add CI test routing"):
            ci_scope.select_scope(["hr_toolkit/tools/new_unknown_tool.py"])

    def test_deleted_test_is_not_imported(self):
        scope = ci_scope.select_scope(["tests/test_deleted_case.py"])
        self.assertEqual(scope["targets"], [])
        self.assertEqual(scope["python_files"], [])

    def test_explicit_full_mode_preserves_legacy_compatibility_filter(self):
        scope = ci_scope.select_scope([], full=True)
        self.assertTrue(scope["full"])
        self.assertTrue(scope["run"])
        self.assertIn("tests.test_project_store", scope["win7_targets"])
        self.assertNotIn("tests.test_material_collector", scope["win7_targets"])

    def test_push_range_covers_all_commits_since_before_sha(self):
        self.assertEqual(ci_scope.diff_range("push", {"before": "a" * 40, "after": "b" * 40}), "a" * 40 + ".." + "b" * 40)

    def test_pull_request_uses_merge_base(self):
        event = {"pull_request": {"base": {"sha": "a" * 40}, "head": {"sha": "b" * 40}}}
        self.assertEqual(ci_scope.diff_range("pull_request", event), "a" * 40 + "..." + "b" * 40)

    def test_empty_selection_does_not_invoke_unittest_discovery(self):
        scope = ci_scope.select_scope(["README.md"])
        with patch.dict(os.environ, {"CI_SCOPE": json.dumps(scope), "CI_WIN7": "false"}), patch.object(ci_scope.subprocess, "run") as run:
            ci_scope.run_tests()
        run.assert_not_called()

    def test_full_discovery_requires_explicit_scope_flag(self):
        scope = ci_scope.select_scope(["scripts/ci_scope.py"])
        with patch.dict(os.environ, {"CI_SCOPE": json.dumps(scope), "CI_WIN7": "false"}), patch.object(ci_scope.subprocess, "run") as run:
            ci_scope.run_tests()
        self.assertNotIn("discover", run.call_args[0][0])
        self.assertIn("tests.test_ci_scope", run.call_args[0][0])
        scope["full"] = True
        with patch.dict(os.environ, {"CI_SCOPE": json.dumps(scope), "CI_WIN7": "false"}), patch.object(ci_scope.subprocess, "run") as run:
            ci_scope.run_tests()
        self.assertIn("discover", run.call_args[0][0])


if __name__ == "__main__":
    unittest.main()
