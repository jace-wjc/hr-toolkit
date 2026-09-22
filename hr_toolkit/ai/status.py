"""等待首个字时轮流显示的状态文案。

文案必须贴着这一轮**实际发出去的东西**走：发了图就说「看图」，发了表格就说
「读表格」，两样都有就都说——否则用户粘一张截图，界面上却写着「正在读取表格」，
一眼就知道是写死的假提示。思考与成文阶段再从池子里抽样，让相邻两次提问的
提示不完全一样。

只依赖标准库：Win7 版是 Python 3.8 + 冻结标准库。
"""

from __future__ import annotations

import random
from typing import Iterable, List, Optional, Sequence

# 第一阶段：这一轮到底发了什么。键是附件类型组合（见 perception_key）。
_PERCEIVE = {
    "none": (
        "正在理解你的问题…",
        "正在看你问的是什么…",
        "正在拆解你的问题…",
    ),
    "image": (
        "正在看这张图…",
        "正在读你发的截图…",
        "正在辨认图里的内容…",
        "正在看图上的文字…",
    ),
    "sheet": (
        "正在读这份表格…",
        "正在核对表头…",
        "正在扫一遍数据…",
    ),
    "both": (
        "正在看图，同时翻表格…",
        "正在对着图核表格…",
        "正在把图和表格对上…",
    ),
}

# 第二阶段：思考。
_REASON = (
    "正在理思路…",
    "正在对比…",
    "正在推演…",
    "正在权衡几种说法…",
    "正在把线索串起来…",
    "正在找规律…",
)

# 第三阶段：落笔成文。
_COMPOSE = (
    "正在核对数字…",
    "正在整理结论…",
    "正在组织语言…",
    "正在写成答案…",
    "正在收束成结论…",
)

# 面板在拿不到上下文（例如刚启动还没发过消息）时的兜底。
_DEFAULT = ("正在思考…", "正在整理结论…")

# 一轮展示的总条数：1 条感知 + n 条思考 + 1 条成文。
DEFAULT_STEPS = 4


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


def build_status_phrases(
    kinds: Sequence[str] = (),
    *,
    seed: Optional[int] = None,
    steps: int = DEFAULT_STEPS,
) -> List[str]:
    """按附件类型生成一轮状态文案。

    ``seed`` 给定则结果可复现（测试用）；不给就用当前时间播种，让每次提问
    的措辞都不一样。``steps`` 是最少条数，池子不够时会自然变短。
    """
    rng = random.Random(seed) if seed is not None else random.Random()

    total = max(2, int(steps))
    phrases: List[str] = [rng.choice(_PERCEIVE[perception_key(kinds)])]

    # 思考阶段要抽 total-2 条不重复的；池子不够就有多少给多少。
    reason_count = min(total - 2, len(_REASON))
    if reason_count > 0:
        phrases.extend(rng.sample(_REASON, reason_count))

    phrases.append(rng.choice(_COMPOSE))
    return phrases


def default_status_phrases() -> List[str]:
    """还没发过消息时的兜底文案。"""
    return list(_DEFAULT)
