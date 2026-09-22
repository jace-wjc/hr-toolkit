"""图片附件：识别、校验与 OpenAI 多模态请求体所需的编码。

只依赖标准库：Win7 版是 Python 3.8 + 冻结标准库，不能引图像处理库。
真正的解码/缩放由 Qt 侧在取图时完成（见 ``hr_toolkit.gui_qt.image_input``），
这里只处理「已经拿到字节」之后的纯逻辑：嗅探类型、限制体积、拼 data URI、
以及维护一份可清理的本地图片缓存目录。
"""

from __future__ import annotations

import base64
import os
import shutil
import time
from pathlib import Path
from typing import Iterable, List, Optional, Tuple

from hr_toolkit.common.paths import user_app_data_dir

# 面板里能附加的图片类型。刻意不含 svg：它是矢量文本，模型看到的是源码。
SUPPORTED_IMAGE_SUFFIXES = (".png", ".jpg", ".jpeg", ".webp", ".bmp", ".gif")

# 单张图上限（编码后约 +33%，仍远小于常见 20MB 请求体上限）。
MAX_IMAGE_BYTES = 4 * 1024 * 1024
# 一条消息里最多几张图：多图会显著增加 token 与延迟。
MAX_IMAGES = 4
# 一条消息里所有图片的合计上限。
MAX_TOTAL_IMAGE_BYTES = 12 * 1024 * 1024

# 长边超过它就先缩小再发：模型侧本身也会缩放，发原图只是白花 token 和流量。
MAX_IMAGE_EDGE = 1568

IMAGE_CACHE_DIRNAME = "ai-images"
# 缓存目录最多留这么多张；超出按修改时间删最旧的。粘贴的图片只有这里一份副本。
IMAGE_CACHE_LIMIT = 60


def is_image_filename(name: str) -> bool:
    """按后缀判断是否是受支持的图片（大小写不敏感）。"""
    lowered = str(name or "").strip().lower()
    return lowered.endswith(SUPPORTED_IMAGE_SUFFIXES)


def sniff_image_mime(data: bytes) -> str:
    """按魔数判定图片类型；认不出返回空串。

    不信任文件后缀：用户把 .png 改成 .jpg 很常见，而请求体里的 mime
    写错会让服务端直接拒收。
    """
    if not data:
        return ""
    if data.startswith(b"\x89PNG\r\n\x1a\n"):
        return "image/png"
    if data.startswith(b"\xff\xd8\xff"):
        return "image/jpeg"
    if data.startswith((b"GIF87a", b"GIF89a")):
        return "image/gif"
    if data.startswith(b"BM"):
        return "image/bmp"
    if len(data) >= 12 and data.startswith(b"RIFF") and data[8:12] == b"WEBP":
        return "image/webp"
    return ""


def image_data_uri(data: bytes, mime: str) -> str:
    """把图片字节编码成 ``data:`` URI（OpenAI 兼容接口的 image_url 用）。"""
    encoded = base64.b64encode(data).decode("ascii")
    return "data:%s;base64,%s" % (mime or "image/png", encoded)


def human_size(size: int) -> str:
    """给用户看的体积文案（附件摘要里用）。"""
    value = max(0, int(size))
    if value < 1024:
        return "%d B" % value
    if value < 1024 * 1024:
        return "%.0f KB" % (value / 1024.0)
    return "%.1f MB" % (value / (1024.0 * 1024.0))


def format_image_summary(width: int, height: int, size: int) -> str:
    """附件摘要：``1200×800 · 320 KB``。缺尺寸时只显示体积。"""
    parts: List[str] = []
    try:
        if int(width) > 0 and int(height) > 0:
            parts.append("%d×%d" % (int(width), int(height)))
    except (TypeError, ValueError):
        pass
    parts.append(human_size(size))
    return " · ".join(parts)


def check_image_payload(data: bytes, mime: str = "") -> Tuple[bytes, str]:
    """校验一张图片，返回 ``(字节, mime)``；不可用时抛 :class:`ValueError`。"""
    blob = bytes(data or b"")
    if not blob:
        raise ValueError("图片内容为空，请重新复制或选择。")
    resolved = mime or sniff_image_mime(blob)
    if not resolved:
        raise ValueError("无法识别的图片格式，请改用 PNG、JPG、WEBP、BMP 或 GIF。")
    if len(blob) > MAX_IMAGE_BYTES:
        raise ValueError(
            "单张图片过大（%s），请压缩到 %s 以内再试。"
            % (human_size(len(blob)), human_size(MAX_IMAGE_BYTES))
        )
    return blob, resolved


def image_cache_dir() -> Path:
    """粘贴/拖入的图片本地副本目录（QML 用 ``file://`` 显示缩略图）。"""
    return user_app_data_dir("data") / "HRToolkit" / IMAGE_CACHE_DIRNAME


def save_cached_image(data: bytes, suffix: str = ".png", *, directory: Optional[Path] = None) -> Path:
    """把图片落盘到缓存目录并返回路径。

    先写临时文件再 ``os.replace``：中途失败不会留下半张图让界面显示破图。
    """
    blob = bytes(data or b"")
    if not blob:
        raise ValueError("图片内容为空。")
    target_dir = Path(directory) if directory is not None else image_cache_dir()
    target_dir.mkdir(parents=True, exist_ok=True)
    extension = suffix if str(suffix).startswith(".") else "." + str(suffix)
    stamp = time.strftime("%Y%m%d-%H%M%S")
    name = "img-%s-%d%s" % (stamp, int(time.time() * 1000) % 1000000, extension)
    target = target_dir / name
    temp = target_dir / (".partial-" + name)
    try:
        temp.write_bytes(blob)
        os.replace(temp, target)
    except BaseException:
        try:
            temp.unlink()
        except OSError:
            pass
        raise
    return target


def prune_image_cache(
    keep: Iterable[object] = (),
    *,
    directory: Optional[Path] = None,
    limit: int = IMAGE_CACHE_LIMIT,
) -> int:
    """只保留最近 ``limit`` 张缓存图片，返回删除数量。

    ``keep`` 里是仍在用的路径（例如当前对话引用的图），永不删除。
    """
    target_dir = Path(directory) if directory is not None else image_cache_dir()
    if not target_dir.is_dir():
        return 0
    protected = set()
    for item in keep or ():
        try:
            protected.add(str(Path(str(item)).resolve()))
        except (OSError, ValueError, RuntimeError):
            continue
    entries = []
    try:
        for child in target_dir.iterdir():
            if not child.is_file() or child.name.startswith("."):
                continue
            try:
                entries.append((child.stat().st_mtime, child))
            except OSError:
                continue
    except OSError:
        return 0
    entries.sort(key=lambda pair: pair[0], reverse=True)
    removed = 0
    for index, (_, path) in enumerate(entries):
        if index < max(0, int(limit)):
            continue
        try:
            if str(path.resolve()) in protected:
                continue
        except (OSError, ValueError, RuntimeError):
            pass
        try:
            path.unlink()
            removed += 1
        except OSError:
            continue
    return removed


def clear_image_cache(*, directory: Optional[Path] = None) -> None:
    """删除整个缓存目录（用户主动清理时用）。"""
    target_dir = Path(directory) if directory is not None else image_cache_dir()
    shutil.rmtree(str(target_dir), ignore_errors=True)
