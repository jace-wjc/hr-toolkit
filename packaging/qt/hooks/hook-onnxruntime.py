"""Keep provider plugins; omit the unused standalone macOS C API library."""
import sys
from pathlib import Path

from PyInstaller.utils.hooks import collect_dynamic_libs


binaries = collect_dynamic_libs("onnxruntime")
if sys.platform == "darwin":
    # The pinned Python binding embeds ORT and does not link the standalone
    # C API dylib. If a future binding links it, PyInstaller's dependency scan
    # will collect it again. Provider dylibs and all Windows DLLs stay intact.
    binaries = [
        entry for entry in binaries
        if not (Path(entry[0]).name.startswith("libonnxruntime.")
                and Path(entry[0]).suffix == ".dylib")
    ]
