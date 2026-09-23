"""Markdown → Qt 富文本（QTextDocument HTML 子集）渲染。

模型返回的是 Markdown，直接丢给 QML 会满屏 `##`、`**` 和竖线表格。
这里把它翻译成 Qt 富文本引擎真正支持的标签子集（h1-h6 / b / i / s /
pre / ul / ol / li / table / blockquote / hr / span），供 QML 的
``TextEdit { textFormat: RichText }`` 直接显示。

只有标准库：Win7 版是 Python 3.8 + 冻结标准库，不能引第三方 Markdown 库。
"""

from __future__ import annotations

import re
import unicodedata
from typing import Dict, List, Tuple

# Qt 只认有限的 CSS 属性，且暗色主题下浅色底会把文字吃掉，所以底色/描边分主题给。
_THEMES: Dict[str, Dict[str, str]] = {
    "light": {
        "rule": "#E6E3DC",
        "code_bg": "#F3F2EE",
        "grid": "#EFEDE8",
        "head_bg": "#F5F4F1",
        "cell_bg": "#FFFFFF",
        "stripe_bg": "#FAFAF8",
        "text": "#292825",
        "quote_text": "#6F6D66",
        "link": "#17715B",
    },
    "dark": {
        "rule": "#333C47",
        "code_bg": "#1B2129",
        "grid": "#333C47",
        "head_bg": "#262E38",
        "cell_bg": "#222931",
        "stripe_bg": "#262F39",
        "text": "#E6EBF0",
        "quote_text": "#A3A8AE",
        "link": "#5FBFA0",
    },
}

_BODY_SIZE = 14.0
_CODE_SIZE = 13.0
# Qt's table cell padding and collapsed borders are supported on Qt 5.15+.
_CELL_PAD = 8
# (font-size, margin-top, margin-bottom)
_HEADING_SCALE = {
    1: (20.0, 12, 8),
    2: (18.0, 10, 6),
    3: (16.0, 8, 6),
    4: (15.0, 8, 5),
    5: (14.0, 6, 4),
    6: (14.0, 6, 4),
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
    return _Renderer(_THEMES["dark" if dark else "light"], font_family=font_family).render(str(text or "").replace("\x00", ""))


def render_markdown_payload(text: str, *, dark: bool = False, font_family: str = "", streaming: bool = False) -> dict:
    """One parse supplies legacy HTML and native table blocks for the chat view."""
    renderer = _Renderer(_THEMES["dark" if dark else "light"], font_family=font_family, streaming=streaming)
    html = renderer.render(str(text or "").replace("\x00", ""))
    return {"html": html, "blocks": renderer.blocks}


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
    def __init__(self, palette: Dict[str, str], font_family: str = "", streaming: bool = False) -> None:
        self.streaming = streaming
        self.palette = palette
        self.font_family = str(font_family or "").strip()
        self.blocks: List[dict] = []
        self._last_table: dict = {}
        self._last_code: dict = {}

    # ------------------------------------------------------------------ 入口
    def render(self, text: str) -> str:
        lines = str(text or "").replace("\r\n", "\n").replace("\r", "\n").split("\n")
        blocks: List[str] = []
        native_blocks: Dict[int, dict] = {}
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
                native_blocks[len(blocks)] = self._last_code
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
                native_blocks[len(blocks)] = self._last_table
                blocks.append(block)
                continue
            if _LIST_RE.match(line):
                block, index = self._read_list(lines, index)
                blocks.append(block)
                continue
            block, index = self._read_paragraph(lines, index)
            blocks.append(block)
        # Each completed block retains its own native delegate while the tail
        # changes. Do not merge an entire answer into one relaid-out TextEdit.
        self.blocks = [native_blocks[position] if position in native_blocks else {"kind": "text", "html": block}
                       for position, block in enumerate(blocks)]
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
        self._last_code = {"kind": "code", "language": language, "text": code}
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
        widths = _column_widths(header, rows, columns)
        typography = "font-size:%gpx; color:%s" % (_BODY_SIZE, palette["text"])
        if self.font_family:
            typography += "; font-family:%s" % self.font_family
        typography = _escape(typography).replace('"', "&quot;")
        # Use actual cell backgrounds, not paragraph backgrounds on a colored
        # table. Wide tables retain readable columns and can scroll in the view.
        width = str(max(440, columns * 80)) if columns > 4 else "100%"
        parts = ['<table width="%s" cellspacing="0" cellpadding="%d" '
                 'style="border-collapse:collapse; margin-top:8px; margin-bottom:10px; %s">'
                 % (width, _CELL_PAD, typography)]
        rendered_rows: List[List[str]] = []
        for row_index, row in enumerate([header] + rows):
            rendered_cells: List[str] = []
            heading = row_index == 0
            background = palette["head_bg"] if heading else palette["cell_bg"] if row_index % 2 else palette["stripe_bg"]
            parts.append("<tr>")
            for column in range(columns):
                cell = row[column] if column < len(row) else ""
                value = self._inline(cell, table_cell=True)
                if heading:
                    value = "<b>%s</b>" % (value or "&nbsp;")
                elif not value:
                    value = '<span style="color:%s">—</span>' % palette["quote_text"]
                rendered_cells.append(value)
                parts.append(
                    '<td align="%s" valign="top" width="%d%%" bgcolor="%s" '
                    'style="border-bottom:1px solid %s; %s">'
                    '<p style="margin-top:0; margin-bottom:0; line-height:125%%; %s">%s</p></td>'
                    % (_align(aligns, column), widths[column], background,
                       palette["grid"], typography, typography, value)
                )
            parts.append("</tr>")
            rendered_rows.append(rendered_cells)
        self._last_table = {"kind": "table", "headers": rendered_rows[0], "rows": rendered_rows[1:],
                            "widths": widths, "alignments": [_align(aligns, c) for c in range(columns)]}
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
            # Qt's default list indent is 40px, excessive in a narrow chat.
            # Explicit margins accumulate for nested bullets; retain room for
            # multi-digit markers in numbered lists.
            list_indent = "-qt-list-indent:1" if ordered else "-qt-list-indent:0; margin-left:20px"
            if not stack or indent > stack[-1][0]:
                tag = "ol" if ordered else "ul"
                parts.append('<%s style="%s; margin-top:4px; margin-bottom:8px; line-height:145%%">' % (tag, list_indent))
                stack.append((indent, tag))
            elif (stack[-1][1] == "ol") != ordered:
                parts.append("</%s>" % stack.pop()[1])
                tag = "ol" if ordered else "ul"
                parts.append('<%s style="%s; margin-top:4px; margin-bottom:8px; line-height:145%%">' % (tag, list_indent))
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
            '<p style="margin-top:0; margin-bottom:8px; line-height:145%%">%s</p>' % "<br>".join(body),
            index,
        )

    # ------------------------------------------------------------------ 行内
    def _inline(self, raw: str, *, table_cell: bool = False) -> str:
        palette = self.palette
        if self.streaming and raw.count("`") % 2:
            raw = raw[:-1] if raw.endswith("`") else raw + "`"
        text = _escape(raw)
        codes: List[str] = []

        def stash(match: "re.Match[str]") -> str:
            codes.append(match.group(1))
            return "\x00%d\x00" % (len(codes) - 1)

        # 先抠出行内代码，免得里面的 * _ ~ 被当成强调标记
        text = _INLINE_CODE_RE.sub(stash, text)
        if self.streaming:
            # Complete temporary styling only outside protected code spans.
            for marker in ("**", "__", "~~"):
                if text.count(marker) % 2:
                    text = text[:-len(marker)] if text.endswith(marker) else text + marker
        if table_cell:
            # Only an exact line-break tag is allowed. Other HTML stays escaped,
            # and tags inside inline code remain literal.
            text = re.sub(r"&lt;br\s*/?&gt;", "<br>", text, flags=re.IGNORECASE)
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
    """Split unescaped pipes outside code spans; preserve empty cells."""
    row = raw.strip()
    cells, cell = [], []
    ticks = 0
    index = 0
    trailing_separator = False
    while index < len(row):
        char = row[index]
        trailing_separator = False
        if char == "\\" and index + 1 < len(row) and row[index + 1] in "\\|":
            cell.append(row[index + 1])
            index += 2
            continue
        if char == "`":
            end = index + 1
            while end < len(row) and row[end] == "`":
                end += 1
            run = end - index
            if not ticks:
                ticks = run
            elif ticks == run:
                ticks = 0
            cell.append(row[index:end])
            index = end
            continue
        if char == "|" and not ticks:
            cells.append("".join(cell).strip())
            cell = []
            trailing_separator = True
        else:
            cell.append(char)
        index += 1
    cells.append("".join(cell).strip())
    if row.startswith("|"):
        cells.pop(0)
    if trailing_separator:
        cells.pop()
    return cells


def _column_widths(header: List[str], rows: List[List[str]], columns: int) -> List[int]:
    # Bounded sampling keeps sizing cheap during streaming, even for long tables.
    # Count CJK characters as two units and cap outliers so one long note cannot
    # squeeze every other column. No text is truncated in the rendered cells.
    weights = [6] * columns
    for row in [header] + rows[:32]:
        for column, cell in enumerate(row[:columns]):
            lines = re.split(r"<br\s*/?>", cell, flags=re.IGNORECASE)
            for line in lines:
                units = sum(2 if unicodedata.east_asian_width(char) in "WF" else 1 for char in line[:160])
                weights[column] = max(weights[column], min(36, units))
    total = sum(weights) or 1
    # Largest-remainder allocation totals exactly 100 without zero-width columns
    # for normal HR tables. Extremely wide tables retain a minimum per column.
    if columns > 100:
        return [1] * columns
    widths = [max(1, int(100 * weight / total)) for weight in weights]
    while sum(widths) > 100:
        largest = max(range(columns), key=lambda c: widths[c])
        widths[largest] -= 1
    remainder = 100 - sum(widths)
    order = sorted(range(columns), key=lambda c: 100 * weights[c] / total - widths[c], reverse=True)
    for column in order[:remainder]:
        widths[column] += 1
    return widths


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
