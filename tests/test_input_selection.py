from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from hr_toolkit.gui_qt.form_specs import SPECS, spec_for
from hr_toolkit.gui_qt.input_selection import selection_hint, selection_mode, validate_selection


class InputSelectionTests(unittest.TestCase):
    def test_all_tool_variants_have_explicit_policies(self):
        self.assertTrue(SPECS)
        self.assertEqual(len({(spec.nav_id, spec.variant) for spec in SPECS}), len(SPECS))
        for spec in SPECS:
            with self.subTest(tool=spec.tool_id):
                self.assertEqual(selection_mode(spec, "input"), spec.input_mode)
                self.assertTrue(selection_hint(spec.input_mode))
                if spec.support_id:
                    self.assertEqual(selection_mode(spec, "support"), spec.support_mode)
                else:
                    with self.assertRaises(ValueError):
                        selection_mode(spec, "support")
        self.assertEqual(selection_mode(spec_for("social_security"), "support"), "excel_file")
        self.assertEqual(selection_mode(spec_for("personnel_change_merge"), "support"), "excel_or_folder")
        self.assertEqual(selection_mode(spec_for("archive_import", "export"), "support"), "excel_archive_or_folder")
        self.assertEqual(selection_mode(spec_for("personnel_change_merge", "reconcile"), "support"), "excel_file")

    def test_types_counts_and_compound_archive_suffixes(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            folder = root / "资料.xlsx"
            folder.mkdir()
            excel, archive, invalid = root / "名册.XLSX", root / "资料.TAR.GZ", root / "资料.gz"
            for path in (excel, archive, invalid):
                path.write_bytes(b"not opened by selection validation")
            valid = validate_selection([excel, archive, folder], "excel_archive_multi", lambda: False)
            self.assertEqual(valid, [excel, archive, folder])
            for mode, paths in (("excel_file", [folder]), ("excel_file", [archive]),
                                ("directory_single", [excel]), ("excel_single", [excel, excel]),
                                ("excel_archive_multi", [invalid]), ("excel_or_folder", [archive])):
                with self.subTest(mode=mode, paths=paths), self.assertRaises(ValueError):
                    validate_selection(paths, mode, lambda: False)
            self.assertEqual(validate_selection([folder], "excel_or_folder", lambda: False), [folder])
            self.assertEqual(validate_selection([archive], "excel_archive_or_folder", lambda: False), [archive])

    def test_batch_is_atomic_and_does_not_read_contents_or_list_directories(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            excel, invalid = root / "工资.xlsx", root / "工资.pdf"
            excel.touch()
            invalid.touch()
            with patch.object(Path, "open", side_effect=AssertionError("must not read file")), \
                 patch.object(Path, "iterdir", side_effect=AssertionError("must not scan folder")):
                self.assertEqual(validate_selection([root], "directory_single", lambda: False), [root])
                with self.assertRaisesRegex(ValueError, "原选择保持不变"):
                    validate_selection([excel, invalid], "excel_archive_multi", lambda: False)

    def test_preserves_order_and_distinct_paths_and_honors_cancellation(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "另一个目录").mkdir()
            first, second = root / "工资.xlsx", root / "另一个目录" / "工资.xlsx"
            first.touch()
            second.touch()
            self.assertEqual(validate_selection([second, first, second], "excel_archive_multi", lambda: False), [second, first])
            with patch.object(Path, "is_dir", side_effect=AssertionError("cancel before IO")):
                self.assertEqual(validate_selection([first], "excel_file", lambda: True), [])


if __name__ == "__main__":
    unittest.main()
