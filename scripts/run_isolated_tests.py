"""Run selected or discovered tests without sharing native state across modules."""

import argparse
import math
import os
from pathlib import Path
import re
import signal
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]
CHILD = """
import faulthandler
import sys
faulthandler.enable(all_threads=True)
delay = float(sys.argv[1])
# Arm before importing tests and leave armed through interpreter shutdown.
faulthandler.dump_traceback_later(delay, repeat=True)
import unittest

class DiagnosticResult(unittest.TextTestResult):
    def startTest(self, test):
        # Reset for each test, but not after it: a hang between two tests must
        # still dump all threads even when the last printed result was "ok".
        faulthandler.dump_traceback_later(delay, repeat=True)
        super().startTest(test)

class DiagnosticRunner(unittest.TextTestRunner):
    resultclass = DiagnosticResult

unittest.main(module=None, argv=['unittest'] + sys.argv[2:],
              testRunner=DiagnosticRunner)
"""


def stop_process_tree(process):
    # A hung GUI probe may have children. Kill only this module's process tree.
    if os.name == "nt":
        try:
            subprocess.run(['taskkill', '/PID', str(process.pid), '/T', '/F'],
                           timeout=10, check=False)
        except (OSError, subprocess.TimeoutExpired):
            pass
        if process.poll() is None:
            process.kill()
    else:
        try:
            os.killpg(process.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
    process.wait(timeout=10)


def _run_group(name, arguments, timeout):
    command = [sys.executable, '-u', '-X', 'faulthandler', '-c', CHILD,
               str(min(60, max(0.1, timeout * 0.8))), *arguments]
    process = subprocess.Popen(command, cwd=str(ROOT),
                               start_new_session=(os.name != "nt"))
    try:
        code = process.wait(timeout=timeout)
    except subprocess.TimeoutExpired:
        print("TIMEOUT: " + name + "; stopping its process tree",
              file=sys.stderr, flush=True)
        stop_process_tree(process)
        return 1
    if code:
        print("FAILED: {} (exit {})".format(name, code), file=sys.stderr, flush=True)
        return 1
    return 0


def run_modules(directory, pattern="test_*.py", timeout=300):
    directory = Path(directory).resolve()
    # Match unittest discovery's default file pattern, including future packages.
    patterns = sorted({path.name for path in directory.rglob(pattern) if path.is_file()})
    if not patterns:
        print("No test modules found in " + str(directory), file=sys.stderr, flush=True)
        return 1
    for index, name in enumerate(patterns, 1):
        print("[{}/{}] {} (isolated; timeout {}s)".format(
            index, len(patterns), name, timeout), flush=True)
        code = _run_group(name, ['discover', '-s', str(directory), '-p', name, '-v'], timeout)
        if code:
            return code
    print("All {} isolated module groups passed.".format(len(patterns)), flush=True)
    return 0


def run_targets(targets, timeout=300):
    groups = {}
    for target in targets:
        if not re.fullmatch(r"tests\.test_\w+(?:\.\w+)*", target):
            raise ValueError("Invalid unittest target: " + target)
        module = '.'.join(target.split('.')[:2])
        groups.setdefault(module, []).append(target)
    if not groups:
        print("No test targets selected", file=sys.stderr, flush=True)
        return 1
    for index, (module, selected) in enumerate(groups.items(), 1):
        print("[{}/{}] {} (isolated; timeout {}s)".format(
            index, len(groups), module, timeout), flush=True)
        # Preserve class/method selections; never expand one selected check to
        # its entire module or fall back to full discovery.
        code = _run_group(module, ['-v', *selected], timeout)
        if code:
            return code
    print("All {} isolated module groups passed.".format(len(groups)), flush=True)
    return 0


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--directory', type=Path, default=ROOT / 'tests')
    parser.add_argument('--pattern', default='test_*.py')
    parser.add_argument('--timeout', type=float, default=300)
    parser.add_argument('--targets', nargs='+', help='Exact unittest modules, classes or methods selected by CI')
    args = parser.parse_args()
    if not math.isfinite(args.timeout) or args.timeout <= 0:
        parser.error('--timeout must be a finite positive number')
    if args.targets is not None:
        return run_targets(args.targets, args.timeout)
    return run_modules(args.directory, args.pattern, args.timeout)


if __name__ == '__main__':
    raise SystemExit(main())
