"""Decode drag metadata without filesystem access or virtual-file extraction."""
from __future__ import annotations

import ntpath
import os
import re
import struct
from pathlib import Path

from .compat import QUrl


def local_drop_paths(values, *, windows: bool | None = None) -> list[Path]:
    windows = os.name == "nt" if windows is None else windows
    paths = []
    for value in values:
        text = value.toString() if isinstance(value, QUrl) else str(value)
        native_windows = bool(re.match(r"^[A-Za-z]:[\\/]", text) or text.startswith("\\\\"))
        if native_windows and windows:
            local = text
        elif not isinstance(value, QUrl) and text.startswith("/") and not windows:
            local = text
        else:
            url = value if isinstance(value, QUrl) else QUrl(text)
            if not url.isValid() or not url.isLocalFile() or url.hasQuery() or url.hasFragment():
                raise ValueError("未取得可用的本地文件路径；网页或未下载附件请先保存到本地。")
            if url.host().lower() == "localhost":
                url = QUrl(url)
                url.setHost("")
            local = url.toLocalFile()
            if windows and re.match(r"^/[A-Za-z]:[\\/]", local):
                local = local[1:]
        absolute = ntpath.isabs(local) and bool(ntpath.splitdrive(local)[0]) if windows else Path(local).is_absolute()
        if not local or "\x00" in local or not absolute:
            raise ValueError("无法识别绝对文件路径，请重新选择文件。")
        if local.lower().endswith(".lnk"):
            raise ValueError("拖入的是快捷方式，请选择它指向的原文件。")
        paths.append(Path(local))
    return paths


def text_paths(text: str) -> list[str]:
    return [line.strip().strip('"') for line in text.replace("\x00", "\n").splitlines()
            if line.strip() and not line.lstrip().startswith("#")]


def native_mime_paths(mime) -> list[str]:
    """Prefer Qt's mapping; only decode advertised file paths, never FileContents."""
    urls = list(mime.urls())
    if urls:
        return [url.toString() for url in urls]
    formats = set(mime.formats())
    if "text/uri-list" in formats:
        paths = text_paths(bytes(mime.data("text/uri-list")).decode("utf-8", errors="strict"))
        if paths:
            return paths
    for name, encoding in (("FileNameW", "utf-16-le"), ("FileName", "mbcs")):
        key = 'application/x-qt-windows-mime;value="' + name + '"'
        if key in formats:
            paths = text_paths(bytes(mime.data(key)).decode(encoding, errors="strict"))
            if paths:
                return paths
    key = 'application/x-qt-windows-mime;value="CF_HDROP"'
    if key in formats:
        data = bytes(mime.data(key))
        if len(data) >= 20:
            offset = struct.unpack_from("<I", data, 0)[0]
            wide = struct.unpack_from("<I", data, 16)[0]
            if 20 <= offset < len(data):
                return text_paths(data[offset:].decode("utf-16-le" if wide else "mbcs", errors="strict"))
    return text_paths(mime.text()) if mime.hasText() else []
