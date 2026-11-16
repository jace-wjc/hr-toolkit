"""Exercise real child processes; never build or publish application assets."""

from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from scripts.ci_scope import select_scope
from scripts import run_isolated_tests


ROOT = Path(__file__).resolve().parents[1]
RUNNER = ROOT / 'scripts' / 'run_isolated_tests.py'


class IsolatedTestsRunnerTests(unittest.TestCase):
    def run_fixture(self, files, timeout=5):
        with tempfile.TemporaryDirectory() as temp:
            directory = Path(temp)
            for name, source in files.items():
                path = directory / name
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(source, encoding='utf-8')
            return subprocess.run(
                [sys.executable, str(RUNNER), '--directory', temp,
                 '--timeout', str(timeout)], cwd=str(ROOT), capture_output=True,
                text=True, encoding='utf-8', errors='replace', timeout=15)

    def test_all_modules_are_discovered_in_fresh_processes(self):
        result = self.run_fixture({
            'test_a.py': "import os, unittest\nos.environ['HR_ISOLATION_FIXTURE'] = 'leaked'\n"
                         "class Case(unittest.TestCase):\n def test_a(self): pass\n",
            '__init__.py': '',
            'nested/__init__.py': '',
            'nested/test_b.py': "import os, unittest\nclass Case(unittest.TestCase):\n"
                                " def test_b(self): self.assertNotIn('HR_ISOLATION_FIXTURE', os.environ)\n",
        })
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn('test_a', result.stderr)
        self.assertIn('test_b', result.stderr)
        self.assertIn('All 2 isolated module groups passed.', result.stdout)

    def test_failure_blocks_success_and_reports_module(self):
        result = self.run_fixture({
            'test_failure.py': 'import unittest\nclass Case(unittest.TestCase):\n'
                               ' def test_failure(self): self.fail("intentional failure")\n',
        })
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('intentional failure', result.stderr)
        self.assertIn('FAILED: test_failure.py', result.stderr)
        self.assertNotIn('module groups passed', result.stdout)

    def test_hang_dumps_stack_and_terminates_without_waiting_indefinitely(self):
        result = self.run_fixture({
            'test_hang.py': 'import time\ntime.sleep(120)\n',
        }, timeout=2)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('test_hang.py', result.stderr)
        self.assertIn('Timeout', result.stderr)
        self.assertIn('TIMEOUT: test_hang.py', result.stderr)

    def test_hang_after_ok_dumps_main_and_worker_stacks(self):
        result = self.run_fixture({
            'test_cleanup_hang.py': (
                'import threading, time, unittest\n'
                'def worker_wait(): time.sleep(120)\n'
                'class Case(unittest.TestCase):\n'
                ' def test_a(self):\n'
                '  threading.Thread(target=worker_wait, daemon=True).start()\n'
                ' def test_b(self): pass\n'
                ' def __del__(self): time.sleep(120)\n'
            ),
        }, timeout=2)
        self.assertNotEqual(result.returncode, 0)
        self.assertRegex(result.stderr, r'test_a .* \.\.\. ok')
        self.assertIn('worker_wait', result.stderr)
        self.assertIn('__del__', result.stderr)
        self.assertIn('TIMEOUT: test_cleanup_hang.py', result.stderr)

    def test_hang_at_process_exit_is_not_reported_as_success(self):
        result = self.run_fixture({
            'test_exit_hang.py': (
                'import atexit, time, unittest\n'
                'def wait_at_exit(): time.sleep(120)\n'
                'atexit.register(wait_at_exit)\n'
                'class Case(unittest.TestCase):\n'
                ' def test_a(self): pass\n'
            ),
        }, timeout=2)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('Ran 1 test', result.stderr)
        self.assertIn('wait_at_exit', result.stderr)
        self.assertIn('TIMEOUT: test_exit_hang.py', result.stderr)

    def test_named_targets_preserve_method_selection_and_module_isolation(self):
        targets = [
            'tests.test_alpha.Case.test_a', 'tests.test_alpha.Case.test_b',
            'tests.test_beta',
        ]
        with patch.object(run_isolated_tests, '_run_group', return_value=0) as run:
            self.assertEqual(run_isolated_tests.run_targets(targets, timeout=12), 0)
        self.assertEqual(run.call_count, 2)
        self.assertEqual(run.call_args_list[0].args,
                         ('tests.test_alpha', ['-v', *targets[:2]], 12))
        self.assertEqual(run.call_args_list[1].args,
                         ('tests.test_beta', ['-v', targets[2]], 12))

    def test_named_target_runs_only_the_selected_method(self):
        target = 'tests.test_ci_scope.CIScopeTests.test_empty_selection_does_not_invoke_unittest_discovery'
        result = subprocess.run(
            [sys.executable, str(RUNNER), '--targets', target, '--timeout', '5'],
            cwd=str(ROOT), capture_output=True, text=True, encoding='utf-8',
            errors='replace', timeout=15,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn('Ran 1 test', result.stderr)
        self.assertIn(target.rsplit('.', 1)[1], result.stderr)
        self.assertNotIn('test_full_discovery', result.stderr)

    def test_named_target_failure_stops_later_groups(self):
        with patch.object(run_isolated_tests, '_run_group', return_value=1) as run:
            self.assertEqual(run_isolated_tests.run_targets(
                ['tests.test_alpha', 'tests.test_beta']), 1)
        run.assert_called_once()

    def test_invalid_or_empty_named_targets_never_start_processes(self):
        with patch.object(run_isolated_tests, '_run_group') as run:
            self.assertEqual(run_isolated_tests.run_targets([]), 1)
            with self.assertRaisesRegex(ValueError, 'Invalid unittest target'):
                run_isolated_tests.run_targets(['tests.test_alpha', 'discover'])
        run.assert_not_called()

    def test_import_error_blocks_success(self):
        result = self.run_fixture({'test_import.py': 'raise RuntimeError("broken import")\n'})
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('broken import', result.stderr)

    def test_empty_selection_fails_closed(self):
        result = self.run_fixture({})
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('No test modules found', result.stderr)

    def test_ci_routes_cover_runner_and_release_contract(self):
        targets = select_scope(['scripts/run_isolated_tests.py'])['targets']
        self.assertTrue({'tests.test_run_isolated_tests', 'tests.test_windows_packaging',
                         'tests.test_ci_scope'}.issubset(targets))


if __name__ == '__main__':
    unittest.main()
