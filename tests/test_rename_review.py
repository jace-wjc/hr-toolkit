from __future__ import annotations
import copy
import os
import subprocess
import sys
import time
import unittest
from pathlib import Path
os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
try:
    from hr_toolkit.gui_qt.compat import QCoreApplication
    from hr_toolkit.gui_qt.rename_review import RenameReview
except ImportError:
    RenameReview = None


def sample_plan(count=3):
    from hr_toolkit.tools.rename_plan import validate_plan
    rows = [{'row_id': str(index), 'order': index+1, 'source_name': f'{index}.PDF',
             'target_name': f'姓名{index}.PDF', 'suffix': '.PDF', 'included': True,
             'is_dir': False, 'relative_path': f'{index}.PDF', 'fingerprint': 'test',
             'source_error': '', 'note': ''} for index in range(count)]
    return validate_plan({'schema': 1, 'root_dir': '/tmp/source', 'mode': 'excel', 'file_type': 'pdf',
                          'existing_names': {row['source_name'].casefold(): [row['source_name']] for row in rows},
                          'rows': rows, 'warnings': []})


@unittest.skipUnless(RenameReview is not None, 'Qt unavailable')
class RenameReviewTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QCoreApplication.instance() or QCoreApplication([])

    def setUp(self):
        self.review = RenameReview()
        self.review.load(sample_plan())
        self.wait()

    def tearDown(self):
        self.review.cancel()
        limit = time.monotonic() + 3
        while self.review._running and time.monotonic() < limit:
            self.app.processEvents()
            time.sleep(.002)

    def wait(self):
        limit = time.monotonic() + 5
        while self.review.validating and time.monotonic() < limit:
            self.app.processEvents()
            time.sleep(.002)
        self.assertFalse(self.review.validating)

    def test_reorder_moves_names_only_and_keeps_original_file_positions(self):
        self.review.moveMapping('0', 1)
        self.review.moveMapping('1', 1)
        self.wait()
        rows = self.review.model.items()
        self.assertEqual([row['source_name'] for row in rows], ['0.PDF', '1.PDF', '2.PDF'])
        self.assertEqual([row['target_name'] for row in rows], ['姓名1.PDF', '姓名2.PDF', '姓名0.PDF'])
        self.assertTrue(self.review.canConfirm)

    def test_manual_edit_preserves_suffix_and_duplicate_disables_confirmation(self):
        self.review.editName('1', '韩信')
        self.assertFalse(self.review.canConfirm)
        self.wait()
        self.assertEqual(self.review.model.item_at(1)['target_name'], '韩信.PDF')
        self.review.editName('0', '韩信')
        self.wait()
        self.assertFalse(self.review.canConfirm)
        self.assertEqual(self.review._plan['conflict_count'], 2)
        self.review.includeRow('0', False)
        self.wait()
        self.assertTrue(self.review.canConfirm)
        self.assertEqual(self.review._plan['rows'][2]['target_name'], '姓名2.PDF')

    def test_filtering_does_not_exclude_hidden_rows_or_reorder_them(self):
        self.review.filterRows('姓名2', 'all')
        self.wait()
        self.assertEqual(self.review.model.rowCount(), 1)
        self.assertFalse(self.review.canReorder)
        self.review.moveMapping('2', -1)
        confirmed = []
        self.review.confirmed.connect(confirmed.append)
        self.review.confirm()
        self.assertEqual(len(confirmed[0]['rows']), 3)
        self.assertTrue(all(row['included'] for row in confirmed[0]['rows']))
        self.assertEqual(confirmed[0]['rows'][2]['target_name'], '姓名2.PDF')

    def test_latest_edit_wins_over_stale_background_validation(self):
        self.review.editName('0', 'old-edit')
        old_revision = self.review._revision
        old_plan = copy.deepcopy(self.review._plan)
        self.review.editName('0', 'latest')
        self.review._apply(old_revision, old_plan, [])
        self.wait()
        self.assertEqual(self.review.model.item_at(0)['target_name'], 'latest.PDF')

    def test_complete_large_model_and_search_last_row(self):
        start = time.monotonic()
        self.review.load(sample_plan(10000))
        self.wait()
        elapsed = time.monotonic() - start
        self.assertEqual(self.review.model.rowCount(), 10000)
        self.review.filterRows('9999.PDF', 'all')
        self.wait()
        self.assertEqual(self.review.model.rowCount(), 1)
        self.assertEqual(self.review.model.item_at(0)['row_id'], '9999')
        print(f'10,000-row review load + validation: {elapsed:.3f}s (local Qt model)')

    def test_cancel_never_confirms_and_late_results_cannot_reopen(self):
        confirmed = []
        self.review.confirmed.connect(confirmed.append)
        revision, plan = self.review._revision, copy.deepcopy(self.review._plan)
        self.review.cancel()
        self.review._apply(revision, plan, [])
        self.review.confirm()
        self.assertFalse(confirmed)
        self.assertEqual(self.review.model.rowCount(), 0)

    def test_rendered_preview_virtualizes_rows_and_supports_keyboard_editing(self):
        probe = Path(__file__).with_name('qt_rename_review_probe.py')
        result = subprocess.run([sys.executable, str(probe)], cwd=str(probe.parent.parent),
                                capture_output=True, text=True, timeout=30)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn('5,000 rows', result.stdout)
        self.assertIn('live delegates', result.stdout)

if __name__ == '__main__':
    unittest.main()
