"""Factual waiting status: provider-side reasoning stages are not observable."""
from typing import Iterable, List, Optional, Sequence

def perception_key(kinds: Iterable[str]) -> str:
    """把附件类型列表压成 ``none`` / ``image`` / ``sheet`` / ``both``。"""
    has_image = False
    has_sheet = False
    for kind in kinds:
        value = str(kind or "").strip()
        if value == "image":
            has_image = True
        elif value:
            has_sheet = True
    if has_image and has_sheet:
        return "both"
    if has_image:
        return "image"
    if has_sheet:
        return "sheet"
    return "none"


def build_status_phrases(kinds: Sequence[str] = (), *, seed: Optional[int] = None,
                         steps: int = 1) -> List[str]:
    return [{
        "none": "正在等待 AI 服务回复…",
        "sheet": "已附加表格，正在等待 AI 服务回复…",
        "image": "已附加图片，正在等待 AI 服务回复…",
        "both": "已附加表格和图片，正在等待 AI 服务回复…",
    }[perception_key(kinds)]]


def default_status_phrases() -> List[str]:
    return build_status_phrases()
