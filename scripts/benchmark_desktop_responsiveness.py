"""Reproduce file-metadata stalls without changing user files or settings."""
from __future__ import annotations

import argparse
import json
import os
import sys
import tempfile
import threading
import time
from pathlib import Path
from unittest.mock import patch


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--files", type=int, default=1000)
    parser.add_argument("--stat-delay-ms", type=float, default=5.0)
    args = parser.parse_args()
    sys.path.insert(0, str(args.source_root.resolve()))
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    os.environ.setdefault("HR_TOOLKIT_SKIP_UPDATE", "1")
    from hr_toolkit.gui_qt.compat import QCoreApplication, QTimer
    from hr_toolkit.gui_qt.controller import AppController

    app = QCoreApplication.instance() or QCoreApplication([])
    with tempfile.TemporaryDirectory(prefix="hr-input-latency-") as temporary:
        root = Path(temporary)
        controller = AppController()
        controller._save_workspace_preferences = lambda: True
        paths = [root / f"{index:05d}.xlsx" for index in range(args.files)]
        controller._input_states[("salary_merge", "default")] = paths
        actual_is_dir = Path.is_dir
        gui_ident = threading.get_ident()
        gui_stats = 0
        total_stats = 0

        def slow_is_dir(path):
            nonlocal gui_stats, total_stats
            if path.parent == root:
                total_stats += 1
                if threading.get_ident() == gui_ident:
                    gui_stats += 1
                time.sleep(max(0.0, args.stat_delay_ms) / 1000)
                return False
            return actual_is_dir(path)

        gaps = []
        last_tick = time.perf_counter()
        slot_ms = []
        started = time.perf_counter()
        done = False

        def tick():
            nonlocal last_tick, done
            now = time.perf_counter()
            gaps.append((now - last_tick) * 1000)
            last_tick = now
            if slot_ms and not getattr(controller, "_input_scan_running", False):
                done = True
                app.quit()

        def select():
            start = time.perf_counter()
            controller.selectTool("salary_merge")
            slot_ms.append((time.perf_counter() - start) * 1000)

        timer = QTimer()
        timer.setInterval(16)
        timer.timeout.connect(tick)
        timer.start()
        QTimer.singleShot(50, select)
        timeout = QTimer()
        timeout.setSingleShot(True)
        timeout.timeout.connect(app.quit)
        timeout.start(max(30000, int(args.files * args.stat_delay_ms * 3)))
        with patch.object(Path, "is_dir", slow_is_dir):
            (getattr(app, "exec", None) or app.exec_)()
        timer.stop()
        timeout.stop()
        app.processEvents()
        result = {
            "files": args.files, "injected_stat_delay_ms": args.stat_delay_ms,
            "tool_switch_slot_ms": round(slot_ms[0], 3),
            "heartbeat_max_gap_ms": round(max(gaps), 3),
            "gui_stat_calls": gui_stats, "total_stat_calls": total_stats,
            "completion_seconds": round(time.perf_counter() - started, 3),
            "completed": done, "displayed_rows": controller._input_model.rowCount(),
        }
        controller.close()
        print(json.dumps(result, ensure_ascii=False, indent=2))
        if not done or result["displayed_rows"] != args.files:
            raise SystemExit("Benchmark did not complete")


if __name__ == "__main__":
    main()
