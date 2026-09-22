"""Markdown → Qt 富文本（QTextDocument HTML 子集）渲染。

模型返回的是 Markdown，直接丢给 QML 会满屏 `##`、`**` 和竖线表格。
这里把它翻译成 Qt 富文本引擎真正支持的标签子集（h1-h6 / b / i / s /
pre / ul / ol / li / table / blockquote / hr / span），供 QML 的
``TextEdit { textFormat: RichText }`` 直接显示。

只有标准库：Win7 版是 Python 3.8 + 冻结标准库，不能引第三方 Markdown 库。
"""

from __future__ import annotations

import re
from typing import Dict, List, Tuple

# Qt 只认有限的 CSS 属性，且暗色主题下浅色底会把文字吃掉，所以底色/描边分主题给。
_THEMES: Dict[str, Dict[str, str]] = {
    "light": {
        "rule": "#E6E3DC",
        "code_bg": "#F3F2EE",
        # 表格靠 "cellspacing=1 + table 底色" 画出网格（QML 的富文本不认 td 的
        # border/padding）。底色定得越浅越好：原来的 #E6E3DC 在小面板里像 Excel
        # 截图，换成 #EFEDE8 后线还在，但不再抢文字。
        "grid": "#EFEDE8",
        "head_bg": "#F5F4F1",
        "cell_bg": "#FFFFFF",
        "quote_text": "#6F6D66",
        "link": "#17715B",
    },
    "dark": {
        "rule": "#333C47",
        "code_bg": "#1B2129",
        "grid": "#333C47",
        "head_bg": "#262E38",
        "cell_bg": "#222931",
        "quote_text": "#A3A8AE",
        "link": "#5FBFA0",
    },
}

_BODY_SIZE = 13.0
_CODE_SIZE = 12.0
# 单元格内边距，走 cellpadding 属性：CSS 的 padding 在 QML 富文本里只吃到横向，
# 纵向会被忽略，表格看着还是贴边。
_CELL_PAD = 6
# (font-size, margin-top, margin-bottom)
_HEADING_SCALE = {
    1: (16.0, 10, 5),
    2: (15.0, 9, 4),
    3: (14.0, 8, 4),
    4: (13.5, 7, 3),
    5: (13.0, 6, 3),
    6: (12.5, 6, 3),
}

_FENCE_RE = re.compile(r"^(```+|~~~+)\s*([\w+#-]*)\s*$")
_RULE_RE = re.compile(r"^([-*_])(?:\s*\1){2,}$")
_HEADING_RE = re.compile(r"^(#{1,6})\s+(.*?)\s*#*\s*$")
_LIST_RE = re.compile(r"^(\s*)([-*+]|\d{1,3}[.)])\s+(.*)$")
_QUOTE_RE = re.compile(r"^\s*>\s?(.*)$")
# 单个分隔格：`---` / `:---` / `---:` / `:---:`
_CELL_SEPARATOR_RE = re.compile(r"^:?-{2,}:?$")

_INLINE_CODE_RE = re.compile(r"`([^`\n]+)`")
_LINK_RE = re.compile(r"\[([^\]\n]*)\]\((https?://[^)\s]+)\)")
_BOLD_RE = re.compile(r"\*\*(?=\S)(.+?)(?<=\S)\*\*|__(?=\S)(.+?)(?<=\S)__")
_ITALIC_RE = re.compile(
    r"(?<!\*)\*(?=\S)([^*\n]+?)(?<=\S)\*(?!\*)|(?<![\w_])_(?=\S)([^_\n]+?)(?<=\S)_(?![\w_])"
)
_STRIKE_RE = re.compile(r"~~(?=\S)(.+?)(?<=\S)~~")
_TOKEN_RE = re.compile(r"\x00(\d+)\x00")


def render_markdown_html(text: str, *, dark: bool = False, font_family: str = "") -> str:
    """把 Markdown 转成 Qt 富文本 HTML；无法识别的部分按纯文本安全输出。

    ``font_family`` 是当前界面字体。Qt 富文本里的表格单元格**不会**继承控件的
    字体（段落会），不显式指定的话表里的中文会掉到另一套字族，看着像等宽宽体、
    跟正文完全不是一套字。传进来就写在 table/td 上，不传则保持继承行为。
    """
    return _Renderer(_THEMES["dark" if dark else "light"], font_family=font_family).render(text)


def markdown_to_plain(text: str) -> str:
    """去掉 Markdown 标记，用于日志/标题等不需要富文本的地方。"""
    body = str(text or "")
    body = _FENCE_RE.sub("", body)
    body = re.sub(r"`([^`\n]+)`", r"\1", body)
    body = re.sub(r"\*\*(.+?)\*\*", r"\1", body)
    body = _ITALIC_RE.sub(lambda match: match.group(1) or match.group(2) or "", body)
    body = _STRIKE_RE.sub(r"\1", body)
    body = re.sub(r"^#{1,6}\s*", "", body, flags=re.MULTILINE)
    return body.strip()


def _escape(raw: str) -> str:
    return str(raw).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


class _Renderer:
    def __init__(self, palette: Dict[str, str], font_family: str = "") -> None:
        self.palette = palette
        self.font_family = str(font_family or "").strip()

    # ------------------------------------------------------------------ 入口
    def render(self, text: str) -> str:
        lines = str(text or "").replace("\r\n", "\n").replace("\r", "\n").split("\n")
        blocks: List[str] = []
        index = 0
        total = len(lines)
        while index < total:
            line = lines[index]
            stripped = line.strip()
            if not stripped:
                index += 1
                continue

            fence = _FENCE_RE.match(stripped)
            if fence:
                block, index = self._read_fence(lines, index)
                blocks.append(block)
                continue
            if _RULE_RE.match(stripped):
                blocks.append(
                    '<p style="margin-top:6px; margin-bottom:6px">'
                    '<hr style="border:0; border-top:1px solid %s"></p>' % self.palette["rule"]
                )
                index += 1
                continue
            heading = _HEADING_RE.match(stripped)
            if heading:
                blocks.append(self._heading(len(heading.group(1)), heading.group(2)))
                index += 1
                continue
            if _QUOTE_RE.match(line):
                block, index = self._read_quote(lines, index)
                blocks.append(block)
                continue
            if self._starts_table(lines, index):
                block, index = self._read_table(lines, index)
                blocks.append(block)
                continue
            if _LIST_RE.match(line):
                block, index = self._read_list(lines, index)
                blocks.append(block)
                continue
            block, index = self._read_paragraph(lines, index)
            blocks.append(block)
        return "".join(blocks)

    # ------------------------------------------------------------------ 块级
    def _heading(self, level: int, body: str) -> str:
        size, margin_top, margin_bottom = _HEADING_SCALE.get(level, _HEADING_SCALE[6])
        tag = "h%d" % max(1, min(6, level))
        return (
            '<%s style="font-size:%gpx; font-weight:600; margin-top:%dpx; margin-bottom:%dpx">%s</%s>'
            % (tag, size, margin_top, margin_bottom, self._inline(body), tag)
        )

    def _read_fence(self, lines: List[str], index: int) -> Tuple[str, int]:
        marker = _FENCE_RE.match(lines[index].strip())
        fence = marker.group(1) if marker else "```"
        language = (marker.group(2) if marker else "") or ""
        index += 1
        body: List[str] = []
        while index < len(lines):
            candidate = lines[index].strip()
            if candidate.startswith(fence[:3]):
                index += 1
                break
            body.append(lines[index])
            index += 1
        label = (
            '<p style="font-size:11px; margin-bottom:0">%s</p>' % _escape(language)
            if language
            else ""
        )
        code = "\n".join(body)
        return (
            '%s<pre style="font-family:monospace; font-size:%gpx; background-color:%s; '
            'margin-top:4px; margin-bottom:6px">%s</pre>'
            % (label, _CODE_SIZE, self.palette["code_bg"], _escape(code)),
            index,
        )

    def _read_quote(self, lines: List[str], index: int) -> Tuple[str, int]:
        body: List[str] = []
        while index < len(lines):
            match = _QUOTE_RE.match(lines[index])
            if not match:
                break
            body.append(match.group(1))
            index += 1
        text = "<br>".join(self._inline(item) for item in body)
        return (
            '<blockquote style="color:%s; margin-left:8px">%s</blockquote>'
            % (self.palette["quote_text"], text)
        ), index

    def _starts_table(self, lines: List[str], index: int) -> bool:
        if index + 1 >= len(lines):
            return False
        head = lines[index].strip()
        if "|" not in head:
            return False
        return _is_table_separator(lines[index + 1].strip())

    def _read_table(self, lines: List[str], index: int) -> Tuple[str, int]:
        header = _split_row(lines[index])
        aligns = _row_alignments(lines[index + 1])
        index += 2
        rows: List[List[str]] = []
        while index < len(lines):
            current = lines[index].strip()
            if not current or "|" not in current:
                break
            rows.append(_split_row(lines[index]))
            index += 1

        columns = max([len(header)] + [len(row) for row in rows]) if (header or rows) else 0
        palette = self.palette
        # 单元格不继承控件字体，得显式写上去；没传字体就退回原来的继承行为。
        style = "background-color:%s" % palette["grid"]
        if self.font_family:
            style += "; font-family:%s" % self.font_family
        head_style = "background-color:%s" % palette["head_bg"]
        cell_style = "background-color:%s" % palette["cell_bg"]

        parts = ['<table width="100%%" cellspacing="1" cellpadding="%d" style="%s">'
                 % (_CELL_PAD, style)]
        if header:
            parts.append("<tr>")
            for column in range(columns):
                title = header[column] if column < len(header) else ""
                parts.append(
                    '<td align="%s" valign="top" style="%s"><b>%s</b></td>'
                    % (_align(aligns, column), head_style, self._inline(title) or "&nbsp;")
                )
            parts.append("</tr>")
        for row in rows:
            parts.append("<tr>")
            for column in range(columns):
                cell = row[column] if column < len(row) else ""
                parts.append(
                    '<td align="%s" valign="top" style="%s">%s</td>'
                    % (_align(aligns, column), cell_style, self._inline(cell) or "&nbsp;")
                )
            parts.append("</tr>")
        parts.append("</table>")
        return "".join(parts), index

    def _read_list(self, lines: List[str], index: int) -> Tuple[str, int]:
        items: List[Tuple[int, bool, str]] = []
        while index < len(lines):
            raw = lines[index]
            if not raw.strip():
                break
            match = _LIST_RE.match(raw)
            if match:
                indent = len(match.group(1).expandtabs(4))
                ordered = match.group(2)[0].isdigit()
                items.append((indent, ordered, match.group(3)))
                index += 1
                continue
            # 列表项的续行：比当前缩进更深、且不是新块起始
            if items and raw.startswith(" " * (items[-1][0] + 2)) and not _LIST_RE.match(raw):
                indent, ordered, text = items[-1]
                items[-1] = (indent, ordered, text + " " + raw.strip())
                index += 1
                continue
            break

        parts: List[str] = []
        stack: List[Tuple[int, str]] = []
        for indent, ordered, text in items:
            while stack and indent < stack[-1][0]:
                parts.append("</%s>" % stack.pop()[1])
            if not stack or indent > stack[-1][0]:
                tag = "ol" if ordered else "ul"
                parts.append('<%s style="-qt-list-indent:1; margin-top:2px; margin-bottom:2px">' % tag)
                stack.append((indent, tag))
            elif (stack[-1][1] == "ol") != ordered:
                parts.append("</%s>" % stack.pop()[1])
                tag = "ol" if ordered else "ul"
                parts.append('<%s style="-qt-list-indent:1; margin-top:2px; margin-bottom:2px">' % tag)
                stack.append((indent, tag))
            parts.append("<li>%s</li>" % self._inline(text))
        while stack:
            parts.append("</%s>" % stack.pop()[1])
        return "".join(parts), index

    def _read_paragraph(self, lines: List[str], index: int) -> Tuple[str, int]:
        body: List[str] = []
        while index < len(lines):
            raw = lines[index]
            stripped = raw.strip()
            if not stripped:
                break
            if (
                _FENCE_RE.match(stripped)
                or _HEADING_RE.match(stripped)
                or _LIST_RE.match(raw)
                or _QUOTE_RE.match(raw)
                or _RULE_RE.match(stripped)
                or self._starts_table(lines, index)
            ):
                break
            body.append(self._inline(stripped))
            index += 1
        return (
            '<p style="margin-top:0; margin-bottom:6px">%s</p>' % "<br>".join(body),
            index,
        )

    # ------------------------------------------------------------------ 行内
    def _inline(self, raw: str) -> str:
        palette = self.palette
        text = _escape(raw)
        codes: List[str] = []

        def stash(match: "re.Match[str]") -> str:
            codes.append(match.group(1))
            return "\x00%d\x00" % (len(codes) - 1)

        # 先抠出行内代码，免得里面的 * _ ~ 被当成强调标记
        text = _INLINE_CODE_RE.sub(stash, text)
        text = _LINK_RE.sub(
            lambda match: '<a href="%s" style="color:%s">%s</a>'
            % (match.group(2), palette["link"], match.group(1) or match.group(2)),
            text,
        )
        text = _BOLD_RE.sub(
            lambda match: "<b>%s</b>" % (match.group(1) or match.group(2) or ""), text
        )
        text = _ITALIC_RE.sub(
            lambda match: "<i>%s</i>" % (match.group(1) or match.group(2) or ""), text
        )
        text = _STRIKE_RE.sub(lambda match: "<s>%s</s>" % match.group(1), text)

        if codes:
            text = _TOKEN_RE.sub(
                lambda match: '<span style="font-family:monospace; font-size:%gpx; '
                'background-color:%s">%s</span>'
                % (_CODE_SIZE, palette["code_bg"], codes[int(match.group(1))]),
                text,
            )
        return text


def _is_table_separator(stripped: str) -> bool:
    if "-" not in stripped or "|" not in stripped:
        return False
    # 逐格判断：原来的整串正则要求「最后一个格子后面还有一段 `-{2,}`」，
    # 于是 `| 事项 |` + `| --- |` 这种单列表格会被判成普通段落、竖线原样露出来。
    cells = _split_row(stripped)
    if not cells:
        return False
    return all(_CELL_SEPARATOR_RE.match(cell.strip()) for cell in cells)


def _split_row(raw: str) -> List[str]:
    row = raw.strip()
    if row.startswith("|"):
        row = row[1:]
    if row.endswith("|"):
        row = row[:-1]
    return [cell.strip() for cell in row.split("|")]


def _row_alignments(separator: str) -> List[str]:
    alignments: List[str] = []
    for cell in _split_row(separator):
        body = cell.strip()
        left = body.startswith(":")
        right = body.endswith(":")
        if left and right:
            alignments.append("center")
        elif right:
            alignments.append("right")
        else:
            alignments.append("left")
    return alignments


def _align(alignments: List[str], column: int) -> str:
    if column < len(alignments) and alignments[column] in ("center", "right"):
        return alignments[column]
    return "left"
