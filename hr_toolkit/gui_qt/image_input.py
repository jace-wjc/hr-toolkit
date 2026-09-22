"""把「剪贴板 / 拖拽 / 文件选择」拿到的图片变成可直接发给模型的字节。

放在 GUI 层是因为解码与缩放用 Qt 的 QImage：``hr_toolkit/ai`` 必须保持
纯标准库（Win7 是 Python 3.8 + 冻结标准库），所以那边只接收已经准备好的字节。

发出去之前一定先压：模型侧还会再缩一次，直接发原图只是白花 token 和流量。
超过长边上限的图先等比缩小，再按「有透明通道用 PNG、否则用 JPEG」编码；
仍然超限就降 JPEG 质量，最后才放弃。
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional

from . import compat as qt_compat
from ..ai import images as image_support

IMAGE_FILE_FILTER = "图片 (*.png *.jpg *.jpeg *.webp *.bmp *.gif)"
ATTACH_FILE_FILTER = (
    "表格或图片 (*.xlsx *.xls *.png *.jpg *.jpeg *.webp *.bmp *.gif);;"
    "Excel 工作簿 (*.xlsx *.xls);;"
    "图片 (*.png *.jpg *.jpeg *.webp *.bmp *.gif);;"
    "所有文件 (*)"
)

# JPEG 质量阶梯：先试最好的，超限就往下走。
_JPEG_QUALITIES = (88, 78, 62)


def _qt():
    """按运行时版本取 QImage/QBuffer 与两个跨版本枚举。"""
    if qt_compat.QT_MAJOR == 6:
        from PySide6.QtCore import QBuffer, QIODevice
        from PySide6.QtGui import QGuiApplication, QImage
    else:
        from PySide2.QtCore import QBuffer, QIODevice  # type: ignore[no-redef]
        from PySide2.QtGui import QGuiApplication, QImage  # type: ignore[no-redef]

    qt = qt_compat.Qt
    keep_aspect = getattr(getattr(qt, "AspectRatioMode", qt), "KeepAspectRatio")
    smooth = getattr(getattr(qt, "TransformationMode", qt), "SmoothTransformation")
    write_only = getattr(getattr(QIODevice, "OpenModeFlag", QIODevice), "WriteOnly")
    return QImage, QBuffer, QIODevice, QGuiApplication, keep_aspect, smooth, write_only


def _encoded_bytes(image, *, prefer_png: bool, quality: int = 88) -> bytes:
    """把 QImage 编码成字节；空图或编码失败返回空串。"""
    QImage, QBuffer, QIODevice, _app, _keep, _smooth, write_only = _qt()
    if image is None or image.isNull():
        return b""
    buffer = QBuffer()
    buffer.open(write_only)
    if prefer_png:
        ok = image.save(buffer, "PNG")
    else:
        ok = image.save(buffer, "JPEG", int(quality))
    if not ok:
        buffer.close()
        return b""
    data = bytes(buffer.data())
    buffer.close()
    return data


def encode_image(image, *, max_edge: int = image_support.MAX_IMAGE_EDGE) -> Optional[Dict[str, Any]]:
    """缩放 + 编码；返回 ``{data, mime, width, height}``，不可用时 None。"""
    QImage, _buffer, _device, _app, keep_aspect, smooth, _write = _qt()
    if image is None or image.isNull():
        return None
    width = int(image.width())
    height = int(image.height())
    if width <= 0 or height <= 0:
        return None
    working = image
    limit = max(64, int(max_edge))
    if max(width, height) > limit:
        working = image.scaled(limit, limit, keep_aspect, smooth)
        if working.isNull():
            working = image
    # 有透明通道的图（截图、浏览器复制）用 PNG，否则 JPEG 体积小得多。
    prefer_png = bool(working.hasAlphaChannel())
    candidates: List[tuple] = []
    if prefer_png:
        candidates.append(("image/png", 0))
    for quality in _JPEG_QUALITIES:
        candidates.append(("image/jpeg", quality))
    for mime, quality in candidates:
        blob = _encoded_bytes(working, prefer_png=(mime == "image/png"), quality=quality)
        if not blob:
            continue
        if len(blob) <= image_support.MAX_IMAGE_BYTES:
            return {
                "data": blob,
                "mime": mime,
                "width": int(working.width()),
                "height": int(working.height()),
            }
    # 连最低质量都超限：再缩一半重来一次，不行就报错。
    if limit > 640:
        return encode_image(image, max_edge=limit // 2)
    return None


def prepare_image(image, name: str, *, source_path: Optional[Path] = None) -> Dict[str, Any]:
    """编码 + 落盘，返回可以直接交给 ``AiAssistantSession.add_image`` 的参数字典。"""
    encoded = encode_image(image)
    if encoded is None:
        raise ValueError("这张图片无法读取或压缩，请换一张再试（支持 PNG/JPG/WEBP/BMP/GIF）。")
    blob, mime = image_support.check_image_payload(encoded["data"], encoded["mime"])
    suffix = "." + mime.split("/")[-1].replace("jpeg", "jpg")
    try:
        cached = image_support.save_cached_image(blob, suffix)
    except OSError as exc:
        raise ValueError("无法保存图片副本：%s" % exc) from exc
    return {
        "name": str(name or "粘贴的图片"),
        "data": blob,
        "mime": mime,
        "width": encoded["width"],
        "height": encoded["height"],
        "cached_path": cached,
        "source_path": source_path,
    }


def load_image_file(path) -> Optional[Dict[str, Any]]:
    """读一个图片文件并压缩成可发送的字节。"""
    _image, _buffer, _device, _app, keep_aspect, _smooth, _write = _qt()
    if qt_compat.QT_MAJOR == 6:
        from PySide6.QtGui import QImageReader
    else:
        from PySide2.QtGui import QImageReader
    source = Path(path).expanduser()
    if source.stat().st_size > 40 * 1024 * 1024:
        raise ValueError("图片过大，请先缩小图片后再附加。")
    reader = QImageReader(str(source))
    size = reader.size()
    if not size.isValid() or size.width() * size.height() > 40000000:
        raise ValueError("图片尺寸过大或无法识别，请先缩小图片后再附加。")
    reader.setAutoTransform(True)
    if max(size.width(), size.height()) > image_support.MAX_IMAGE_EDGE:
        reader.setScaledSize(size.scaled(image_support.MAX_IMAGE_EDGE, image_support.MAX_IMAGE_EDGE, keep_aspect))
    image = reader.read()
    if image.isNull():
        raise ValueError("无法读取图片 %s，请确认文件未损坏。" % source.name)
    return prepare_image(image, source.name, source_path=source)


def clipboard_image_payload() -> Optional[Dict[str, Any]]:
    """从剪贴板取图。

    优先用「复制的图片文件」的原始文件（质量最好），其次才是剪贴板里的位图。
    剪贴板里没有图片时返回 None，调用方据此决定是否放行普通的文本粘贴。
    """
    _image, _buffer, _device, QGuiApplication, _keep, _smooth, _write = _qt()
    clipboard = QGuiApplication.clipboard()
    if clipboard is None:
        return None

    for path in clipboard_image_paths():
        try:
            return load_image_file(path)
        except (ValueError, OSError):
            continue

    mime_data = clipboard.mimeData()
    has_bitmap = bool(mime_data is not None and mime_data.hasImage())
    if not has_bitmap:
        image = clipboard.image()
        has_bitmap = image is not None and not image.isNull()
    if not has_bitmap:
        return None
    return prepare_image(clipboard.image(), "粘贴的图片.png")


def clipboard_image_paths() -> List[str]:
    """剪贴板里被复制的图片文件路径（在文件管理器里 Ctrl+C 一张图）。"""
    _image, _buffer, _device, QGuiApplication, _keep, _smooth, _write = _qt()
    clipboard = QGuiApplication.clipboard()
    if clipboard is None:
        return []
    mime_data = clipboard.mimeData()
    if mime_data is None or not mime_data.hasUrls():
        return []
    paths: List[str] = []
    for url in mime_data.urls():
        local = url.toLocalFile() if hasattr(url, "toLocalFile") else ""
        if local and image_support.is_image_filename(local) and Path(local).is_file():
            paths.append(local)
    return paths


def clipboard_has_image() -> bool:
    """剪贴板里是否有图（用来决定 Ctrl+V 是粘图还是粘文字）。"""
    _image, _buffer, _device, QGuiApplication, _keep, _smooth, _write = _qt()
    clipboard = QGuiApplication.clipboard()
    if clipboard is None:
        return False
    if clipboard_image_paths():
        return True
    mime_data = clipboard.mimeData()
    if mime_data is not None and mime_data.hasImage():
        return True
    image = clipboard.image()
    return image is not None and not image.isNull()
