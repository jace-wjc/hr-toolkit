from __future__ import annotations
import copy
import json
import tempfile
import threading
import unittest
from pathlib import Path
from unittest.mock import patch
from openpyxl import Workbook

from hr_toolkit.tools.rename_plan import build_rename_plan, execute_rename_plan, validate_plan
from hr_toolkit.tools.folder_rename import _rename_text_no_replace, rename_person_folders, rename_files_by_excel


class RenamePlanTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name)
        self.root = self.base / 'items'
        self.root.mkdir()

    def files(self, *names):
        for name in names:
            (self.root / name).write_bytes(name.encode())

    def excel(self, rows):
        path = self.base / 'mapping.xlsx'
        workbook = Workbook()
        for row in rows:
            workbook.active.append(row)
        workbook.save(path)
        workbook.close()
        return path

    def build(self, **kwargs):
        return build_rename_plan(self.root, **kwargs)

    def execute(self, plan, **kwargs):
        return execute_rename_plan(self.root, plan=plan, output_dir=self.base / 'results', **kwargs)

    def test_user_edits_override_excel_order_and_excel_is_not_reread(self):
        self.files('1.PDF', '2.jpg', '3.xlsx')
        excel = self.excel([['姓名'], ['张三'], ['李四'], ['王五']])
        plan = self.build(mode='excel', file_type='all', excel_path=excel)
        for row, name in zip(plan['rows'], ['王五', '韩信', '张三']):
            row['target_name'] = name + row['suffix']
        excel.unlink()  # Execution is independent of the roster after review.
        result = self.execute(plan)
        for name, original in [('王五.PDF', '1.PDF'), ('韩信.jpg', '2.jpg'), ('张三.xlsx', '3.xlsx')]:
            self.assertEqual((self.root / name).read_bytes(), original.encode())
        self.assertEqual(result['operation_count'], 3)
        events = [json.loads(line) for line in Path(result['rename_ledger']).read_text().splitlines()]
        self.assertEqual(events[0]['plan']['rows'][1]['target_name'], '韩信.jpg')
        self.assertEqual(events[-1]['status'], 'success')
        self.assertTrue(Path(result['rename_receipt']).is_file())

    def test_name_swap_and_case_only_change_are_safe(self):
        self.files('A.pdf', 'B.pdf', 'Case.pdf')
        plan = self.build(mode='replace_text', text='unmatched', replacement_name='x', file_type='pdf')
        targets = {'A.pdf': 'B.pdf', 'B.pdf': 'A.pdf', 'Case.pdf': 'case.pdf'}
        for row in plan['rows']:
            row['target_name'] = targets[row['source_name']]
        result = self.execute(plan)
        self.assertEqual(result['operation_count'], 3)
        self.assertEqual((self.root / 'A.pdf').read_bytes(), b'B.pdf')
        self.assertEqual((self.root / 'B.pdf').read_bytes(), b'A.pdf')
        self.assertEqual((self.root / 'case.pdf').read_bytes(), b'Case.pdf')
        self.assertFalse(any(p.name.startswith('.hr-rename-') for p in self.root.iterdir()))

    def test_folder_cycle_preserves_nested_contents(self):
        for name in ('A', 'B'):
            (self.root / name).mkdir()
            (self.root / name / 'nested.txt').write_bytes(name.encode())
        plan = self.build(mode='replace_text', text='unused', replacement_name='x')
        plan['rows'][0]['target_name'], plan['rows'][1]['target_name'] = 'B', 'A'
        self.execute(plan)
        self.assertEqual((self.root / 'A/nested.txt').read_bytes(), b'B')
        self.assertEqual((self.root / 'B/nested.txt').read_bytes(), b'A')

    def test_all_conflicts_are_visible_and_exclusions_release_duplicates(self):
        self.files('1.pdf', '2.pdf', '3.pdf', '4.pdf')
        plan = self.build(mode='excel', file_type='pdf', excel_path=self.excel([['姓名'], ['same'], ['SAME'], ['CON'], ['bad/name']]))
        self.assertEqual(plan['conflict_count'], 4)
        self.assertEqual(len(plan['rows']), 4)
        with self.assertRaisesRegex(ValueError, '冲突'):
            self.execute(plan)
        for row in plan['rows'][1:]:
            row['included'] = False
        self.execute(plan)
        self.assertTrue((self.root / 'same.pdf').is_file())
        self.assertTrue((self.root / '2.pdf').is_file())

    def test_excluded_source_cannot_be_used_as_destination(self):
        self.files('A.pdf', 'B.pdf')
        plan = self.build(mode='replace_text', text='A', replacement_name='B', file_type='pdf')
        plan['rows'][1]['included'] = False
        self.assertEqual(validate_plan(plan)['conflict_count'], 1)
        with self.assertRaises(ValueError):
            self.execute(plan)
        self.assertEqual((self.root / 'A.pdf').read_bytes(), b'A.pdf')

    def test_manual_edits_cannot_escape_paths_or_change_extensions(self):
        self.files('old.PDF')
        original = self.build(mode='replace_text', text='old', replacement_name='new', file_type='pdf')
        for target in ('../outside.PDF', 'bad/name.PDF', 'CON.PDF', 'new.pdf', 'new.PDF ', '', 'x\x00.PDF', 'x' * 256 + '.PDF'):
            with self.subTest(target=target):
                plan = copy.deepcopy(original)
                plan['rows'][0]['target_name'] = target
                self.assertGreater(validate_plan(plan)['conflict_count'], 0)
                with self.assertRaises(ValueError):
                    self.execute(plan)
        self.assertEqual((self.root / 'old.PDF').read_bytes(), b'old.PDF')

    def test_source_content_changes_after_preview_are_blocked(self):
        self.files('old.pdf')
        plan = self.build(mode='replace_text', text='old', replacement_name='new', file_type='pdf')
        (self.root / 'old.pdf').write_bytes(b'changed')
        with self.assertRaisesRegex(ValueError, '预览后已变化'):
            self.execute(plan)
        self.assertFalse((self.root / 'new.pdf').exists())

    def test_new_target_after_preview_is_blocked_before_staging(self):
        self.files('old.pdf')
        plan = self.build(mode='replace_text', text='old', replacement_name='new', file_type='pdf')
        (self.root / 'NEW.PDF').write_bytes(b'external')
        with self.assertRaisesRegex(ValueError, '冲突'):
            self.execute(plan)
        self.assertEqual((self.root / 'NEW.PDF').read_bytes(), b'external')
        self.assertEqual((self.root / 'old.pdf').read_bytes(), b'old.pdf')

    def test_runtime_race_restores_sources_without_overwriting_intruder(self):
        self.files('1.pdf', '2.pdf')
        plan = self.build(mode='append', text='_new', file_type='pdf')
        def race(source, target):
            if target.name == '2_new.pdf':
                target.write_bytes(b'external')
            _rename_text_no_replace(source, target)
        with patch('hr_toolkit.tools.rename_plan.legacy._rename_text_no_replace', side_effect=race):
            with self.assertRaisesRegex(RuntimeError, '安全恢复'):
                self.execute(plan)
        self.assertEqual((self.root / '1.pdf').read_bytes(), b'1.pdf')
        self.assertEqual((self.root / '2.pdf').read_bytes(), b'2.pdf')
        self.assertEqual((self.root / '2_new.pdf').read_bytes(), b'external')
        self.assertFalse((self.root / '1_new.pdf').exists())
        events = [json.loads(line) for line in next((self.base / 'results').glob('*.jsonl')).read_text().splitlines()]
        self.assertEqual(events[-1]['status'], 'failed')
        self.assertEqual(set(events[-1]['states'].values()), {'restored'})

    def test_cancellation_during_staging_restores_all_sources(self):
        self.files('1.pdf', '2.pdf')
        plan = self.build(mode='append', text='_new', file_type='pdf')
        stop = threading.Event()
        def progress(current, total, message):
            stop.set()
        with self.assertRaisesRegex(RuntimeError, '已停止'):
            self.execute(plan, cancelled=stop.is_set, progress_callback=progress)
        self.assertEqual({p.name for p in self.root.iterdir()}, {'1.pdf', '2.pdf'})

    def test_explicit_mapping_matches_by_name_not_order(self):
        self.files('scan1.pdf', 'scan2.pdf', 'other.pdf')
        excel = self.excel([['原文件名', '新名称'], ['scan2.pdf', '张三'], ['scan1.pdf', '李四.pdf'], ['absent.pdf', '王五']])
        plan = self.build(mode='excel_map', file_type='pdf', excel_path=excel)
        self.assertEqual(plan['change_count'], 2)
        self.assertEqual(sum(not row['included'] for row in plan['rows']), 1)
        self.assertIn('absent.pdf', plan['warnings'][0])
        self.execute(plan)
        self.assertEqual((self.root / '张三.pdf').read_bytes(), b'scan2.pdf')
        self.assertEqual((self.root / '李四.pdf').read_bytes(), b'scan1.pdf')
        self.assertTrue((self.root / 'other.pdf').is_file())

    def test_explicit_mapping_duplicate_keys_never_fall_back_to_order(self):
        self.files('1.pdf')
        excel = self.excel([['原文件名', '新名称'], ['1.pdf', '张三'], ['1.PDF', '李四']])
        with self.assertRaisesRegex(ValueError, '重复'):
            self.build(mode='excel_map', file_type='pdf', excel_path=excel)

    def test_cleanup_is_opt_in_and_keeps_content_extension_and_semantic_words(self):
        self.files(' 张三　__劳动合同__作废.PDF')
        plan = self.build(mode='normalize', file_type='pdf', normalize_separators=True)
        self.assertEqual(plan['rows'][0]['target_name'], '张三 _劳动合同_作废.PDF')
        self.execute(plan)
        self.assertEqual((self.root / '张三 _劳动合同_作废.PDF').read_bytes(), ' 张三　__劳动合同__作废.PDF'.encode())

    def test_initial_plans_match_existing_modes_for_valid_operations(self):
        self.files('张三.pdf', '李四.pdf', '其他.txt')
        for mode, args in [('append', {'text': '_资料'}), ('remove', {'text': '三'}),
                           ('replace', {'target_name': '张三.pdf', 'replacement_name': '王五'}),
                           ('replace_text', {'text': '张三', 'replacement_name': '王五'})]:
            with self.subTest(mode=mode):
                legacy = rename_person_folders(self.root, mode=mode, file_type='pdf', dry_run=True, **args)
                plan = self.build(mode=mode, file_type='pdf', **args)
                self.assertEqual([(row['source_name'], row['target_name']) for row in plan['rows'] if row['status'] == 'ready'],
                                 [(op.source.name, op.target.name) for op in legacy.operations])
        excel = self.excel([['姓名'], ['张三'], ['王五'], ['赵六']])
        legacy = rename_files_by_excel(self.root, excel, file_type='all', dry_run=True)
        plan = self.build(mode='excel', excel_path=excel, file_type='all')
        # Conflicts are deliberately kept for interactive resolution, not silently omitted.
        self.assertEqual([(row['source_name'], row['target_name']) for row in plan['rows'] if row['status'] == 'ready'],
                         [(op.source.name, op.target.name) for op in legacy.operations])

    def test_all_rows_are_kept_and_validation_reports_every_duplicate(self):
        # Large review without manufacturing thousands of business files.
        self.files('old.pdf')
        plan = self.build(mode='append', text='_new', file_type='pdf')
        template = plan['rows'][0]
        plan['rows'] = [dict(template, row_id=str(i), source_name=f'{i}.pdf', target_name='same.pdf', order=i+1) for i in range(10000)]
        plan['existing_names'] = {}
        result = validate_plan(plan)
        self.assertEqual(len(result['rows']), 10000)
        self.assertEqual(result['conflict_count'], 10000)

    def test_receipt_escapes_formulas_without_changing_actual_name(self):
        self.files('old.pdf')
        result = self.execute(self.build(mode='replace_text', text='old', replacement_name='=SUM(1)', file_type='pdf'))
        self.assertTrue((self.root / '=SUM(1).pdf').exists())
        self.assertIn("'=SUM(1).pdf", Path(result['rename_receipt']).read_text(encoding='utf-8-sig'))

    def test_review_and_execution_use_all_existing_type_filters(self):
        from hr_toolkit.tools.folder_rename import FILE_TYPE_EXTENSIONS
        for file_type in FILE_TYPE_EXTENSIONS:
            with self.subTest(file_type=file_type), tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp) / 'items'
                root.mkdir()
                (root / 'old-folder').mkdir()
                (root / 'old-folder/nested.txt').write_bytes(b'nested')
                names = ['old.PDF', 'old.jpg', 'old.xlsx', 'old.bin', 'unmatched.txt']
                for name in names:
                    (root / name).write_bytes(name.encode())
                expected = rename_person_folders(root, mode='replace_text', text='old', replacement_name='new',
                                                file_type=file_type, dry_run=True)
                plan = build_rename_plan(root, mode='replace_text', text='old', replacement_name='new', file_type=file_type)
                result = execute_rename_plan(root, plan=plan)
                self.assertEqual(result['operation_count'], expected.operation_count)
                changes = {op.source.name: op.target.name for op in expected.operations}
                for name in names:
                    target = root / changes.get(name, name)
                    self.assertEqual(target.read_bytes(), name.encode())
                    self.assertEqual(target.suffix, Path(name).suffix)
                self.assertEqual((root / changes.get('old-folder', 'old-folder') / 'nested.txt').read_bytes(), b'nested')

    def test_journal_failure_preserves_staged_data_and_identifies_recovery_record(self):
        import hr_toolkit.tools.rename_plan as module
        self.files('old.pdf')
        plan = self.build(mode='append', text='_new', file_type='pdf')
        journal = module._journal
        def disk_full(stream, event):
            if event['event'] == 'plan' or event['event'] == 'intent' and event['state'] == 'staged':
                return journal(stream, event)
            raise OSError('simulated journal disk full')
        with patch.object(module, '_journal', side_effect=disk_full):
            with self.assertRaisesRegex(RuntimeError, '1 项尚未恢复.*改名记录'):
                self.execute(plan)
        staged = list(self.root.glob('.hr-rename-*/0'))
        self.assertEqual(len(staged), 1)
        self.assertEqual(staged[0].read_bytes(), b'old.pdf')
        events = [json.loads(line) for line in next((self.base / 'results').glob('*.jsonl')).read_text().splitlines()]
        self.assertEqual(events[-1]['event'], 'intent')
        self.assertEqual(events[-1]['from'], 'old.pdf')

    def test_unsafe_row_identifiers_are_rejected(self):
        self.files('old.pdf')
        plan = self.build(mode='append', text='_new', file_type='pdf')
        plan['rows'][0]['row_id'] = '../escape'
        with self.assertRaisesRegex(ValueError, '编号无效'):
            self.execute(plan)

    def test_thousand_item_execution_keeps_exact_confirmed_names_and_contents(self):
        import time
        names = [f'{index:04d}.pdf' for index in range(1000)]
        self.files(*names)
        plan = self.build(mode='append', text='_合同', file_type='pdf')
        start = time.monotonic()
        result = self.execute(plan)
        elapsed = time.monotonic() - start
        self.assertEqual(result['operation_count'], 1000)
        for name in names:
            self.assertEqual((self.root / (Path(name).stem + '_合同.pdf')).read_bytes(), name.encode())
        print(f'1,000-item confirmed rename + durable journal: {elapsed:.3f}s (local filesystem)')

if __name__ == '__main__':
    unittest.main()
