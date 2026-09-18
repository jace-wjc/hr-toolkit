"""Task-scoped intermediates without changing the GUI process's global temp directory."""
from __future__ import annotations

import tempfile
from contextlib import contextmanager
from contextvars import ContextVar

_root = ContextVar("hr_toolkit_run_temp", default=None)


def current_temporary_root():
    return _root.get()


@contextmanager
def temporary_root(path):
    token = _root.set(str(path))
    try:
        yield
    finally:
        _root.reset(token)


def temporary_directory(*args, **kwargs):
    if len(args) < 3 and kwargs.get("dir") is None and _root.get() is not None:
        kwargs["dir"] = _root.get()
    return tempfile.TemporaryDirectory(*args, **kwargs)
