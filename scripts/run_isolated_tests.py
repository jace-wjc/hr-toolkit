"""Run the complete release suite without sharing native state across modules."""

import argparse
import math
import os
from pathlib import Path
import signal
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]
CHILD = """
import faulthandler
import sys
faulthandler.enable()
faulthandler.dump_traceback_later(float(sys.argv[1]), repeat=True)
import unittest
unittest.main(module=None, argv=['unittest', 'discover', '-s', sys.argv[2],
                              '-p', sys.argv[3], '-v'])
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
        command = [sys.executable, '-u', '-X', 'faulthandler', '-c', CHILD,
                   str(max(0.1, timeout * 0.8)), str(directory), name]
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
    print("All {} isolated module groups passed.".format(len(patterns)), flush=True)
    return 0


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--directory', type=Path, default=ROOT / 'tests')
    parser.add_argument('--pattern', default='test_*.py')
    parser.add_argument('--timeout', type=float, default=300)
    args = parser.parse_args()
    if not math.isfinite(args.timeout) or args.timeout <= 0:
        parser.error('--timeout must be a finite positive number')
    return run_modules(args.directory, args.pattern, args.timeout)


if __name__ == '__main__':
    raise SystemExit(main())
