"""Measure real offline OCR cold initialization and warm model reuse."""
from __future__ import annotations

import argparse
import hashlib
import json
import statistics
import sys
import time
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--images", type=Path, required=True)
    parser.add_argument("--expected-text", default="")
    args = parser.parse_args()
    sys.path.insert(0, str(args.source_root.resolve()))
    from hr_toolkit.tools import material_collector as mc
    import psutil

    images = sorted(args.images.resolve().glob("*.png"))
    if not images:
        raise ValueError("No PNG fixtures")
    sources = {path.name: hashlib.sha256(path.read_bytes()).hexdigest() for path in images}
    start = time.perf_counter()
    engine = mc._get_ocr_engine()
    initialization = time.perf_counter() - start
    times, texts = [], []
    process = psutil.Process()
    rss = []
    for path in images:
        start = time.perf_counter()
        text, _lines, complete = mc._read_ocr_text(path)
        times.append(time.perf_counter() - start)
        texts.append(text)
        rss.append(process.memory_info().rss)
        if not complete or (args.expected_text and args.expected_text not in text):
            raise RuntimeError(f"OCR fixture failed: {path.name}")
        if mc._get_ocr_engine() is not engine:
            raise RuntimeError("OCR model was unnecessarily reinitialized")
    assert sources == {path.name: hashlib.sha256(path.read_bytes()).hexdigest() for path in images}
    print(json.dumps({"images": len(images), "initialization_seconds": initialization,
                      "first_inference_seconds": times[0], "warm_median_seconds": statistics.median(times[1:] or times),
                      "total_inference_seconds": sum(times), "rss_after_each_image": rss,
                      "texts": texts, "source_sha256": sources, "engine_reused": True}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
