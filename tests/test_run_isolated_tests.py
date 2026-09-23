"""Exercise real child processes; never build or publish application assets."""

from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from scripts.ci_scope import select_scope


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
