"""Compile and instantiate the Sage shared panel, its popups and the detached window."""
from __future__ import annotations
import os
import struct
import tempfile
import zlib
from pathlib import Path
import sys

os.environ.update(
    QT_QPA_PLATFORM="offscreen",
    QT_QUICK_BACKEND="software",
    QT_QUICK_CONTROLS_STYLE="Basic",
    HR_TOOLKIT_SKIP_UPDATE="1",
)
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from hr_toolkit.ai import config as ai_config
from hr_toolkit.ai import history as ai_history
from hr_toolkit.ai import images as ai_images
from hr_toolkit.gui_qt.compat import QApplication, QObject, Property, Slot, QUrl, QT_MAJOR
from hr_toolkit.gui_qt.controller import AppController

# 探针绝不能碰用户真实的设置 / 对话历史：模型增删、切换与历史同步都会落盘。
# （曾经因为没隔离，把 probe-* 模型写进了用户自己的 ai-assistant.json。）
_PROBE_DIR = Path(tempfile.mkdtemp(prefix="hr-toolkit-ai-probe-"))
ai_config.default_settings_path = lambda: _PROBE_DIR / "ai-assistant.json"
ai_history.default_conversations_path = lambda: _PROBE_DIR / "ai-conversations.json"
ai_images.image_cache_dir = lambda: _PROBE_DIR / "ai-images"

if QT_MAJOR == 6:
    from PySide6.QtCore import QEventLoop, QMetaObject, QPoint, Qt, QTimer
    from PySide6.QtQuick import QQuickWindow
    from PySide6.QtQml import QQmlApplicationEngine, QQmlComponent, QQmlExpression
    from PySide6.QtTest import QTest
else:
    from PySide2.QtCore import QEventLoop, QMetaObject, QPoint, Qt, QTimer
    from PySide2.QtQuick import QQuickWindow
    from PySide2.QtQml import QQmlApplicationEngine, QQmlComponent, QQmlExpression
    from PySide2.QtTest import QTest

os.environ["QT_QUICK_CONTROLS_STYLE"] = "Default" if QT_MAJOR == 5 else "Basic"


def qml_number(engine, scope, expression):
    """Read a numeric value out of QML, avoiding Shiboken's type converters.

    ``ScrollView.contentItem`` is declared as ``QQuickItem*`` and the flickable's
    ``boundsBehavior`` is a ``QFlags<QQuickFlickable::BoundsBehaviorFlag>``; neither
    can be wrapped from Python ("Can't find converter").  Evaluating the same path
    inside QML returns a plain number.  Returns ``None`` when the expression fails.
    """
    result = QQmlExpression(engine.rootContext(), scope, expression).evaluate()
    undefined = False
    if isinstance(result, tuple):  # PySide6 returns (value, isUndefined)
        result, undefined = result
    if undefined or result is None:
        return None
    return int(result)


def wait_for_events(milliseconds):
    loop = QEventLoop()
    QTimer.singleShot(milliseconds, loop.quit)
    execute = getattr(loop, "exec", None) or loop.exec_
    execute()


def click_item(engine, window, item):
    """Click the centre of a QML item, in real window coordinates."""
    spot = QQmlExpression(
        engine.rootContext(), item,
        "(function(){var p=mapToItem(null,width/2,height/2);return ''+p.x+','+p.y;})()",
    ).evaluate()
    if isinstance(spot, tuple):
        spot = spot[0]
    if not isinstance(spot, str) or spot.count(",") != 1:
        return False
    x, y = (float(value) for value in spot.split(","))
    QTest.mouseClick(window, Qt.LeftButton, Qt.NoModifier, QPoint(int(x), int(y)))
    return True


def provider_row_spots(engine, popup):
    """模型菜单里那几行服务商的窗口坐标，按预设顺序返回 [(x, y), …]。

    注意 Popup 不是 Item，没有 ``children`` 属性——要从 ``contentItem`` 往下递归。
    """
    value = QQmlExpression(
        engine.rootContext(), popup,
        "(function(){"
        "function collect(it,n,out){if(it.objectName===n)out.push(it);"
        "var c=it.children;for(var i=0;i<c.length;++i)collect(c[i],n,out);}"
        "var rows=[];collect(contentItem,'aiProviderRow',rows);"
        "var out=[];"
        "for(var i=0;i<rows.length;++i){"
        "var p=rows[i].mapToItem(null,rows[i].width/2,rows[i].height/2);"
        "out.push(Math.round(p.x)+':'+Math.round(p.y));}"
        "return out.join(',');})()",
    ).evaluate()
    if isinstance(value, tuple):
        value = value[0]
    if not isinstance(value, str) or not value:
        return []
    return [tuple(int(part) for part in item.split(":")) for item in value.split(",")]


class Controller(AppController):
    @Slot()
    def start(self):
        pass


def tiny_png(width=6, height=6):
    """Minimal truecolor PNG so the image pipeline runs without test fixtures."""

    def chunk(tag, payload):
        return (
            struct.pack(">I", len(payload))
            + tag
            + payload
            + struct.pack(">I", zlib.crc32(tag + payload) & 0xFFFFFFFF)
        )

    raw = b"".join(b"\x00" + b"\x2e\x6f\x9e" * width for _ in range(height))
    header = struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)
    return (
        b"\x89PNG\r\n\x1a\n"
        + chunk(b"IHDR", header)
        + chunk(b"IDAT", zlib.compress(raw))
        + chunk(b"IEND", b"")
    )


def require(condition, message, failures):
    if not condition:
        failures.append(message)
    return bool(condition)


def markdown_probe() -> int:
    """Load only response blocks; no project, network, settings or main window."""
    import json
    import time
    from hr_toolkit.ai.markdown import render_markdown_payload

    application = QApplication.instance() or QApplication([])
    engine = QQmlApplicationEngine()
    warnings = []
    engine.warnings.connect(lambda messages: warnings.extend(m.toString() for m in messages))
    source = "## Records\n\n| ID | Name | Department | Date | Status | Notes |\n| ---: | --- | --- | --- | --- | --- |\n"
    source += "\n".join("| %d | Employee | HR | 2026-09-22 | Pending | First<br>Second |" % i for i in range(2000))
    started = time.perf_counter()
    engine.rootContext().setContextProperty("responseBlocks", render_markdown_payload(source)["blocks"])
    qml = '''import QtQuick 2.15
import QtQuick.Window 2.15
import "."
Window {
    id: win; visible: true; width: 400; height: 600
    QtObject { id: appearance; property string theme: "light"; property string language: "en_US"
        function translate(t, l) { return t } }
    Component.onCompleted: Ui.backend = appearance
    AiResponseBody { id: response; width: win.width; blocks: responseBlocks }
    function named(name) {
        function scan(o) {
            if (o.objectName === name) return o
            var children = o.children || []
            for (var i=0; i<children.length; ++i) { var found=scan(children[i]); if(found) return found }
            return null
        }
        return scan(contentItem)
    }
    function metrics() {
        var r=named("aiTableRows"), h=named("aiTableHorizontal"), live=0
        for(var i=0;i<r.contentItem.children.length;++i)
            if(r.contentItem.children[i].objectName === "aiTableRow") ++live
        return JSON.stringify({count:r.count,live:live,height:r.height,total:r.contentHeight,
            last:r.itemAtIndex(r.count-1)!==null,x:h.contentX,maxX:h.contentWidth-h.width,
            first:r.indexAt(1,r.contentY+1)})
    }
    function scrollLast() { var r=named("aiTableRows"); r.positionViewAtEnd(); r.rememberPosition() }
    function pan() { var h=named("aiTableHorizontal"); h.contentX=h.contentWidth-h.width }
    function dark() { appearance.theme="dark" }
}'''
    base = Path(__file__).resolve().parents[1] / "hr_toolkit/gui_qt/qml/components/MarkdownProbe.qml"
    panel = QQmlComponent(engine, QUrl.fromLocalFile(str(base.with_name("AiChatPanel.qml"))))
    assert not panel.isError(), [error.toString() for error in panel.errors()]
    engine.loadData(qml.encode(), QUrl.fromLocalFile(str(base)))
    if not engine.rootObjects():
        raise AssertionError("Markdown QML failed: " + "\n".join(warnings))
    root = engine.rootObjects()[0]

    def evaluate(expression):
        result = QQmlExpression(engine.rootContext(), root, expression).evaluate()
        return result[0] if isinstance(result, tuple) else result

    wait_for_events(150)
    metrics = json.loads(evaluate("metrics()"))
    assert metrics["count"] == 2000 and metrics["live"] < 40, metrics
    assert metrics["height"] == 360 and metrics["total"] > metrics["height"], metrics
    evaluate("scrollLast(); pan()")
    wait_for_events(100)
    before = json.loads(evaluate("metrics()"))
    assert before["last"] and before["x"] > 0, before
    # Updating the streamed response must preserve the existing table viewport.
    engine.rootContext().setContextProperty("responseBlocks", render_markdown_payload(source + "\n| 2000 | Added | HR | | | |", dark=True)["blocks"])
    evaluate("dark()")
    wait_for_events(150)
    after = json.loads(evaluate("metrics()"))
    assert after["count"] == 2001 and after["live"] < 40, after
    assert abs(after["x"] - before["x"]) < 1 and after["first"] == before["first"], (before, after)
    root.setProperty("width", 900)
    wait_for_events(80)
    assert json.loads(evaluate("metrics()"))["x"] == 0
    assert not warnings, warnings
    print("Markdown probe OK (Qt %d): 2,001 rows, %d live rows; resize, theme and stream update passed (%.2fs including waits)"
          % (QT_MAJOR, after["live"], time.perf_counter() - started))
    root.close()
    return 0


def sage_open_probe() -> int:
    """Exercise the sidebar entry with restored, variable-height CJK messages."""
    from hr_toolkit.gui_qt.compat import delete_qobject
    application = QApplication.instance() or QApplication([])
    original_font = application.font()
    font = application.font()
    if sys.platform == "darwin":
        font.setFamily("PingFang SC")
    elif sys.platform.startswith("win"):
        font.setFamily("Microsoft YaHei" if QT_MAJOR == 5 else "Microsoft YaHei UI")
    application.setFont(font)
    controller = Controller()
    controller._save_workspace_preferences = lambda: True
    store = ai_history.ConversationStore(_PROBE_DIR / "sage-open-history.json")
    record = store.create("Synthetic layout regression")
    for i in range(9):
        record.messages.extend([
            {"role": "user", "content": "请查看工作表" * (1 + i % 3)},
            {"role": "assistant", "content": "### 工作表说明\n\n" + "待核对资料说明。" * (120 if i == 4 else i * 3)
             + "\n\n| 序号 | 工作表 | 备注 |\n| --- | --- | --- |\n"
             + "\n".join("| %d | 归档资料 | %s |" % (j, "待确认<br>" * (1 + j % 3)) for j in range(1 + i % 4))}
        ])
    store.upsert(record)
    controller._ai_conversation_store = store
    engine = QQmlApplicationEngine()
    errors = []
    engine.warnings.connect(lambda messages: errors.extend(error.toString() for error in messages))
    engine.rootContext().setContextProperty("controller", controller)
    qml = Path(__file__).resolve().parents[1] / "hr_toolkit/gui_qt/qml/Main.qml"
    engine.load(QUrl.fromLocalFile(str(qml)))
    assert engine.rootObjects(), errors
    root = engine.rootObjects()[0]
    button = root.findChild(QObject, "sageLauncher")
    assert button is not None
    for width in (1560, 1024, 1560):
        print("Sage open: width %d" % width, flush=True)
        root.setProperty("width", width)
        wait_for_events(100)
        QMetaObject.invokeMethod(button, "clicked")
        # If layout re-enters tail scrolling, even this event-loop timer cannot
        # fire; the parent entrypoint test's process timeout catches the freeze.
        wait_for_events(350)
        assert len(controller.aiChatModel) == 18
        panel = root.findChild(QObject, "aiPanelLoader")
        detached = root.findChild(QObject, "aiWindowLoader").property("item")
        view_root = detached if detached is not None and detached.property("visible") else panel.property("item")
        assert view_root is not None
        view = view_root.findChild(QObject, "aiChatView")
        assert view is not None
        # Qt 5/6 differ in whether positionViewAtEnd includes bottomMargin.
        def tail_gap():
            return float(view.property("originY")) + float(view.property("contentHeight")) - float(view.property("contentY")) - float(view.property("height"))
        for _ in range(15):
            if abs(tail_gap()) <= float(view.property("bottomMargin")) + 1:
                break
            wait_for_events(100)
        gap = tail_gap()
        assert abs(gap) <= float(view.property("bottomMargin")) + 1, {
            key: view.property(key) for key in ("count", "height", "contentHeight", "contentY", "originY", "followTail", "atYEnd")}
        # Move past a response taller than the viewport, then hover. Previously
        # it was repeatedly recreated at 60px, shifting its neighbors forever.
        def evaluate(expression):
            query = QQmlExpression(engine.rootContext(), view, expression)
            value = query.evaluate()
            assert not query.hasError(), query.error().toString()
            value = value[0] if isinstance(value, tuple) else value
            return value.toVariant() if hasattr(value, "toVariant") else value

        window = detached if detached is not None and detached.property("visible") else root
        evaluate("followTail=false; positionViewAtBeginning()")
        wait_for_events(200)
        for row in (9, 10, 9, 10):
            evaluate("positionViewAtIndex(%d, 0)" % row)
            wait_for_events(300)
        snapshot = "JSON.stringify([contentY, originY, contentHeight])"
        before = evaluate(snapshot)
        for offset in (30, 100, 200, 50):
            coordinates = evaluate("(function(){var p=mapToItem(null,20,%d);return [p.x,p.y]})()" % offset)
            QTest.mouseMove(window, QPoint(int(coordinates[0]), int(coordinates[1])))
            wait_for_events(80)
            assert evaluate(snapshot) == before, "Hover changed the settled conversation layout"
        assert evaluate("(function(){var a=Array.prototype.filter.call(contentItem.children,function(c){return c.settledHeight!==undefined && !c.pooled});"
                        "a.sort(function(a,b){return a.y-b.y});for(var i=0;i<a.length;++i){"
                        "if(Math.abs(a[i].height-a[i].implicitHeight)>1)return false;"
                        "if(i && a[i].y<a[i-1].y+a[i-1].height-1)return false;}return a.length>0;})()"), "Message rows overlap or retain provisional heights"
        # This probe checks tail-following on reopening. Reading-position
        # retention while followTail is false is covered by interaction_probe.
        evaluate("followTail=true; positionViewAtEnd()")
        wait_for_events(80)
        root.setProperty("aiPanelRequested", False)
        if detached is not None:
            detached.setProperty("requestedOpen", False)
        wait_for_events(50)
    assert not errors, errors
    delete_qobject(root)
    delete_qobject(engine)
    controller.close()
    application.setFont(original_font)
    print("Sage open probe OK: restored CJK tables, tail following, overlay reopening, and stable hover/navigation")
    return 0


def design_probe() -> int:
    """Compare both reading widths/themes/languages using synthetic local data."""
    from hr_toolkit.gui_qt.compat import delete_qobject
    application = QApplication.instance() or QApplication([])
    font = application.font()
    if sys.platform == "darwin":
        font.setFamily("PingFang SC")
        application.setFont(font)
    controller = Controller()
    controller._save_workspace_preferences = lambda: None
    controller._ai_settings = ai_config.AiSettings()
    controller._ai_settings.provider_config().api_key = "offline-ui-fixture"
    store = ai_history.ConversationStore(_PROBE_DIR / "design-history.json")
    record = store.create("字段核对 / Review fields")
    answer = ("## 字段差异\n\n**什么是字段差异：** 同一人、同一事件，汇总表和流程文件中某个字段的内容不一样。\n\n"
              "本次核对有 **1 处**：\n\n| 姓名 | 字段 | 汇总表内容 | 流程内容 |\n| --- | --- | --- | --- |\n"
              "| 示例员工 | 婚否 | 未婚 | 已婚 |\n\n## 如何处理\n\n"
              "**系统行为：** 发现差异时，保留汇总表已有内容，不自动覆盖。\n\n"
              "1. 确认哪个来源正确（询问本人、查原始档案）。\n2. 流程正确：在汇总表中手动更正。\n"
              "3. 汇总表正确：保留原值，确认流程是否填写错误。\n\n"
              "可核对 `employee_id` 与日期，避免同名人员混淆。")
    record.messages = [{"role": "user", "content": "字段差异是什么意思？"}, {"role": "assistant", "content": answer}]
    store.upsert(record)
    controller._ai_conversation_store = store
    controller._ai_restore_record(record)
    engine = QQmlApplicationEngine()
    errors = []
    engine.warnings.connect(lambda messages: errors.extend(e.toString() for e in messages))
    engine.rootContext().setContextProperty("controller", controller)
    engine.rootContext().setContextProperty("appearance", controller.presentation)
    source = '''import QtQuick 2.15
import QtQuick.Window 2.15
import "."
Window {
    width: 620; height: 920; visible: true; color: Ui.color("window")
    property var savedHeading: null
    function named(name) {
        function scan(o) {
            if (o.objectName === name) return o
            var children = o.children || []
            for (var i=0; i<children.length; ++i) { var found=scan(children[i]); if(found) return found }
            return null
        }
        return scan(contentItem)
    }
    Component.onCompleted: Ui.backend = appearance
    AiChatPanel { anchors.fill: parent; showDetachButton: false; showCollapseButton: false }
}'''
    base = Path(__file__).resolve().parents[1] / "hr_toolkit/gui_qt/qml/components/DesignProbe.qml"
    engine.loadData(source.encode(), QUrl.fromLocalFile(str(base)))
    assert engine.rootObjects(), errors
    root = engine.rootObjects()[0]
    panel = root.findChild(QObject, "aiChatPanel")
    view = root.findChild(QObject, "aiChatView")
    def evaluate(obj, expression):
        query = QQmlExpression(engine.rootContext(), obj, expression)
        value = query.evaluate()
        assert not query.hasError(), query.error().toString()
        return value[0] if isinstance(value, tuple) else value
    for width in (400, 620):
        root.setProperty("width", width)
        for language in ("zh_CN", "en_US"):
            controller.presentation.setLanguage(language)
            for theme in ("light", "dark"):
                controller.presentation.setTheme(theme)
                wait_for_events(120)
                evaluate(view, "followTail=false; positionViewAtBeginning()")
                wait_for_events(60)
                # Qt 5's offscreen platform cannot always read back a window.
                # Geometry/state checks run in CI; image capture is opt-in locally.
                if "--screenshots" in sys.argv:
                    image = root.grabWindow()
                    assert not image.isNull()
                    image.save(str(_PROBE_DIR / ("sage-%d-%s-%s.png" % (width, language, theme))))
                assert float(view.property("height")) > 400
                assert evaluate(view, "(function(){var a=contentItem.children;for(var i=0;i<a.length;++i)if(a[i].settledHeight!==undefined && !a[i].pooled && Math.abs(a[i].height-a[i].implicitHeight)>1)return false;return true})()")
    root.setProperty("width", 400)
    root.setProperty("height", 520)
    wait_for_events(100)
    assert float(view.property("height")) > 200
    assert evaluate(root, "(function(){var input=named('aiInputArea');return input.mapToItem(contentItem,0,input.height).y < height;})()")
    root.setProperty("height", 920)
    wait_for_events(100)
    copied = []
    controller.aiCopyMessage = lambda text: copied.append(text)
    assert evaluate(root, "named('aiUserCopy')!==null")
    evaluate(root, "named('aiUserCopy').forceActiveFocus(); named('aiUserCopy').clicked()")
    assert copied == ["字段差异是什么意思？"]
    assert evaluate(root, "named('aiUserCopy').label==='已复制'")
    more = root.findChild(QObject, "aiMoreButton")
    evaluate(more, "forceActiveFocus()")
    QTest.keyClick(root, Qt.Key_Return)
    wait_for_events(50)
    menu = root.findChild(QObject, "aiMorePopup")
    assert menu.property("opened")
    privacy_button = root.findChild(QObject, "aiPrivacyButton")
    assert click_item(engine, root, privacy_button)
    wait_for_events(80)
    privacy = root.findChild(QObject, "aiPrivacyPopup")
    assert privacy.property("opened") and not menu.property("opened")
    QTest.keyClick(root, Qt.Key_Escape)
    wait_for_events(50)
    assert not privacy.property("opened")
    # Completed blocks must keep their native objects as streaming appends blocks.
    controller._ai_chat_model.set_items([])
    controller._ai_busy = True
    controller._ai_chat_model.append({"role": "assistant", "content": "", "streaming": True})
    controller._apply_ai_delta("## Stable heading\n\n")
    controller._drain_ai_text(immediate=True)
    wait_for_events(100)
    assert evaluate(root, "savedHeading=named('aiMarkdownText'); savedHeading!==null")
    for chunk in ("A short paragraph.\n\n", "**Another paragraph** with `code`.\n\n"):
        controller._apply_ai_delta(chunk)
        wait_for_events(250)
        assert evaluate(root, "named('aiMarkdownText')===savedHeading")
    controller._apply_ai_finished(True, "")
    wait_for_events(350)
    assert not controller.aiBusy and not controller._ai_text_timer.isActive()
    # Long code stays selectable inside a bounded, horizontally scrollable block.
    controller._ai_chat_model.set_items([{"role": "assistant", "content": "code",
        **controller._ai_rendered("```text\n" + "employee_field_" * 100 + "\n```"), "streaming": False}])
    wait_for_events(100)
    assert evaluate(root, "named('aiCodeScroll').contentWidth > named('aiCodeScroll').width")
    long_reply = "Paragraph for reading earlier content.\n\n" * 60
    controller._ai_chat_model.set_items([{"role": "assistant", "content": long_reply,
        **controller._ai_rendered(long_reply), "streaming": True}])
    controller._ai_busy = True
    wait_for_events(100)
    evaluate(view, "followTail=false; positionViewAtBeginning()")
    wait_for_events(60)
    reading_y = float(view.property("contentY"))
    controller._apply_ai_delta("A newly received ending.")
    wait_for_events(300)
    assert not view.property("followTail")
    assert abs(float(view.property("contentY")) - reading_y) < 1
    controller._apply_ai_finished(True, "")
    wait_for_events(350)
    # A reply without content shows a separate stopped status and no copy link.
    controller._ai_chat_model.set_items([{"role": "assistant", "content": "", "streaming": False, "status": "stopped"}])
    wait_for_events(100)
    assert evaluate(panel, "(function scan(o){if(o.label==='复制' && o.visible)return false;var a=o.children||[];for(var i=0;i<a.length;++i)if(!scan(a[i]))return false;return true})(this)")
    assert not errors, errors
    print("Design probe OK: 400/620 px, Chinese/English, light/dark; stable streaming blocks and empty stopped state.%s" % ((" Screenshots: " + str(_PROBE_DIR)) if "--screenshots" in sys.argv else ""))
    delete_qobject(root)
    delete_qobject(engine)
    controller.close()
    return 0


def long_scroll_probe() -> int:
    """Reproduce scrollbar scrubbing with 2,400 paragraphs, without an API call.

    Assert bounded live renderers, not machine-dependent timing thresholds.
    Report event-loop timings for local before/after comparisons.
    """
    import time
    from hr_toolkit.gui_qt.compat import delete_qobject
    application = QApplication.instance() or QApplication([])
    controller = Controller()
    controller._save_workspace_preferences = lambda: None
    engine = QQmlApplicationEngine()
    engine.rootContext().setContextProperty("controller", controller)
    engine.rootContext().setContextProperty("appearance", controller.presentation)
    errors = []
    engine.warnings.connect(lambda messages: errors.extend(e.toString() for e in messages))
    source = '''import QtQuick 2.15
import QtQuick.Window 2.15
import "."
Window {
    width: 520; height: 800; visible: true
    Component.onCompleted: Ui.backend = appearance
    AiChatPanel { anchors.fill: parent }
    function countText() {
        function scan(o) {
            var n=o.objectName === "aiMarkdownText" ? 1 : 0
            var c=o.children || []
            for(var i=0;i<c.length;++i) n+=scan(c[i])
            return n
        }
        return scan(contentItem)
    }
}'''
    base = Path(__file__).resolve().parents[1] / "hr_toolkit/gui_qt/qml/components/LongScrollProbe.qml"
    engine.loadData(source.encode(), QUrl.fromLocalFile(str(base)))
    assert engine.rootObjects(), errors
    root = engine.rootObjects()[0]
    view = root.findChild(QObject, "aiChatView")
    bar = root.findChild(QObject, "aiConversationScrollBar")

    def evaluate(obj, expression):
        query = QQmlExpression(engine.rootContext(), obj, expression)
        value = query.evaluate()
        assert not query.hasError(), query.error().toString()
        return value[0] if isinstance(value, tuple) else value

    try:
        answer = "\n\n".join("**段落 %d**：这是员工资料核对说明，请确认姓名、部门和入职日期。 Review employee records and verify dates." % i for i in range(300))
        rows = []
        for i in range(8):
            rows.extend([
                {"role": "user", "content": "Review batch %d" % i, "streaming": False},
                {"role": "assistant", "content": answer, "streaming": False, **controller._ai_rendered(answer)},
            ])
        controller._ai_chat_model.set_items(rows)
        wait_for_events(300)
        assert int(view.property("count")) == 2416
        peak = evaluate(root, "countText()")
        timings = []
        evaluate(view, "followTail=false")
        for fraction in (0, .8, .2, .9, .1, 1, .5, 0, 1):
            start = time.perf_counter()
            evaluate(view, "contentY=originY+(contentHeight-height)*%s" % fraction)
            wait_for_events(30)
            timings.append(round((time.perf_counter() - start) * 1000))
            peak = max(peak, evaluate(root, "countText()"))
        assert peak < 80, "Offscreen paragraphs still eagerly rendered: %s" % peak

        # Exercise the actual thumb, including while new blocks are inserted.
        evaluate(view, "followTail=true; positionViewAtEnd()")
        wait_for_events(100)
        coords = evaluate(bar, "(function(){var p=mapToItem(null,width/2,topPadding+(visualPosition+visualSize/2)*availableHeight);return p.x+','+p.y})()")
        x, y = [round(float(value)) for value in coords.split(",")]
        QTest.mousePress(root, Qt.LeftButton, Qt.NoModifier, QPoint(x, y))
        assert bar.property("pressed") and not view.property("followTail")
        top = evaluate(bar, "mapToItem(null,0,topPadding).y")
        height = float(bar.property("availableHeight"))
        for fraction in (.1, .8, .2, .9, .4):
            QTest.mouseMove(root, QPoint(x, round(top + height * fraction)))
            wait_for_events(40)
            assert bar.property("pressed") and not view.property("followTail")
        before_y = float(view.property("contentY"))
        last = controller._ai_chat_model.item_at(15)
        content = last["content"] + "\n\nNew ending while reading."
        controller._ai_chat_model.update_at(15, {**last, "content": content, "streaming": True, **controller._ai_rendered(content, streaming=True)})
        wait_for_events(80)
        assert not view.property("followTail")
        assert abs(float(view.property("contentY")) - before_y) < 1
        QTest.mouseRelease(root, Qt.LeftButton, Qt.NoModifier, QPoint(x, round(top + height * .4)))
        assert not view.property("followTail")
        # Recycled rows retain correct heights at both narrow and wide widths.
        for width in (400, 620, 520):
            root.setProperty("width", width)
            wait_for_events(100)
            evaluate(view, "positionViewAtBeginning()")
            wait_for_events(100)
            assert evaluate(view, "(function(){var last=null;for(var i=0;i<30;i++){var r=itemAtIndex(i);if(!r)continue;if(Math.abs(r.height-r.implicitHeight)>1)return false;if(last&&r.y<last.y+last.height-1)return false;last=r}return true})()")
        evaluate(view, "followTail=true; positionViewAtEnd()")
        wait_for_events(100)
        assert evaluate(view, "atYEnd")
        # The second user message follows 300 content rows; its Edit action
        # must still address canonical message 2, not visual row 302.
        evaluate(view, "followTail=false; positionViewAtIndex(302,0)")
        wait_for_events(100)
        assert evaluate(view, "(function(){function edit(o){if(o.label==='编辑并重发'){o.clicked();return true}var c=o.children||[];for(var i=0;i<c.length;++i)if(edit(c[i]))return true;return false}return edit(itemAtIndex(302))})()")
        panel = root.findChild(QObject, "aiChatPanel")
        assert int(panel.property("editingRow")) == 2
        evaluate(panel, "cancelEdit()")
        assert not errors, errors
        print("Long scroll probe OK: 2400 paragraphs, peak %d live text blocks; scroll steps including 30 ms wait: %s ms; real thumb drag and streaming anchor preserved." % (peak, timings))
    finally:
        delete_qobject(root)
        delete_qobject(engine)
        controller.close()
    return 0


def interaction_probe() -> int:
    """Sage shared panel/drag lifecycle, using local synthetic conversation data."""
    from unittest.mock import Mock
    from types import SimpleNamespace
    from hr_toolkit.gui_qt.compat import delete_qobject
    application = QApplication.instance() or QApplication([])
    controller = Controller()
    controller._save_workspace_preferences = Mock(return_value=True)
    controller.refreshWorkspace = lambda: None
    controller._project_store = SimpleNamespace(
        workspace=SimpleNamespace(name="Local UI fixture"), writable=True, close=lambda: None)
    controller._ai_settings = ai_config.AiSettings()
    controller._ai_settings.provider_config().api_key = "offline-ui-fixture"
    engine = QQmlApplicationEngine()
    errors = []
    engine.warnings.connect(lambda messages: errors.extend(e.toString() for e in messages))
    engine.rootContext().setContextProperty("controller", controller)
    qml = Path(__file__).resolve().parents[1] / "hr_toolkit/gui_qt/qml/Main.qml"
    engine.load(QUrl.fromLocalFile(str(qml)))
    assert engine.rootObjects(), errors
    root = engine.rootObjects()[0]

    def evaluate(obj, expression):
        query = QQmlExpression(engine.rootContext(), obj, expression)
        value = query.evaluate()
        assert not query.hasError(), query.error().toString()
        return value[0] if isinstance(value, tuple) else value

    try:
        root.setProperty("width", 1200)
        root.setProperty("height", 800)
        evaluate(root, "sidebarPanel.pinned=false")
        wait_for_events(300)
        launcher = root.findChild(QObject, "sageLauncher")
        pane = root.findChild(QObject, "mainPane")
        layout = root.findChild(QObject, "mainLayout")
        geometry = (pane.property("width"), layout.property("height"))
        assert click_item(engine, root, launcher)
        wait_for_events(60)
        panel = root.findChild(QObject, "aiSidePanel")
        assert 0 < float(panel.property("reveal")) < 1, "Opening skipped the transition"
        assert click_item(engine, root, launcher)
        wait_for_events(35)
        assert not root.property("aiPanelRequested")
        assert click_item(engine, root, launcher)
        wait_for_events(260)
        assert float(panel.property("reveal")) == 1
        assert pane.property("width") >= 640 and layout.property("height") == geometry[1]
        assert abs(pane.property("width") + root.findChild(QObject, "workspaceDrawer").property("width") - geometry[0]) < 2
        assert launcher.property("visible")

        chat = root.findChild(QObject, "aiChatPanel")
        draft = chat.findChild(QObject, "aiInputArea")
        draft.setProperty("text", "Unsent draft / 未发送草稿")
        content = "Review older records.\n\n" * 60
        controller._ai_chat_model.set_items([
            {"role": "user", "content": "Review"},
            {"role": "assistant", "content": content, "streaming": True, **controller._ai_rendered(content)},
        ])
        controller._ai_busy = True
        wait_for_events(120)
        view = chat.findChild(QObject, "aiChatView")
        evaluate(view, "followTail=false; positionViewAtBeginning()")
        wait_for_events(60)
        reading_y = float(view.property("contentY"))
        # Both tabs retain their view state and use the same reserved column.
        reserved = root.findChild(QObject, "workspaceDrawer").property("width")
        settings_x = root.findChild(QObject, "appearanceButton").property("x")
        assert click_item(engine, root, root.findChild(QObject, "projectFilesTab"))
        wait_for_events(300)
        assert not root.findChild(QObject, "aiPanelLoader").property("visible")
        search = root.findChild(QObject, "workspaceSearchField")
        search.setProperty("text", "Retained search")
        assert root.findChild(QObject, "workspaceSurface").property("visible")
        assert root.findChild(QObject, "workspaceDrawer").property("width") == reserved
        assert click_item(engine, root, root.findChild(QObject, "sageTab"))
        wait_for_events(300)
        assert root.findChild(QObject, "aiChatPanel") == chat
        assert search.property("text") == "Retained search"
        assert draft.property("text") == "Unsent draft / 未发送草稿"
        assert abs(float(view.property("contentY")) - reading_y) < 1
        assert root.findChild(QObject, "appearanceButton").property("x") == settings_x
        assert click_item(engine, root, launcher)
        for _ in range(25):
            wait_for_events(20)
            if not panel.property("visible"): break
        assert not panel.property("visible") and not panel.property("enabled"), (root.property("aiPanelRequested"), panel.property("requestedOpen"), panel.property("reveal"), launcher.property("x"), launcher.property("y"), root.property("aiWindowOpen"))
        assert controller.aiBusy
        controller._apply_ai_delta("A new paragraph while collapsed.")
        controller._drain_ai_text(immediate=True)
        assert click_item(engine, root, launcher)
        wait_for_events(260)
        assert root.findChild(QObject, "aiChatPanel") == chat
        assert draft.property("text") == "Unsent draft / 未发送草稿"
        assert abs(float(view.property("contentY")) - reading_y) < 1
        assert controller._ai_chat_model.item_at(1)["content"].endswith("while collapsed.")
        controller._apply_ai_finished(True, "")
        wait_for_events(60)
        assert click_item(engine, root, launcher)
        wait_for_events(220)

        # Drag uses global coordinates, persists once, and never toggles Sage.
        before = (float(launcher.property("x")), float(launcher.property("y")))
        start = QPoint(round(before[0] + 34), round(before[1] + 30))
        destination = QPoint(start.x() - 180, start.y() - 90)
        controller._save_workspace_preferences.reset_mock()
        QTest.mousePress(root, Qt.LeftButton, Qt.NoModifier, start)
        QTest.mouseMove(root, start + QPoint(2, 1))
        assert not launcher.property("moving")
        QTest.mouseMove(root, destination)
        wait_for_events(40)
        assert launcher.property("moving")
        assert not controller._save_workspace_preferences.called
        QTest.mouseRelease(root, Qt.LeftButton, Qt.NoModifier, destination)
        wait_for_events(30)
        assert not root.property("aiPanelRequested")
        assert abs(float(launcher.property("x")) - (before[0] - 180)) < 2
        assert abs(float(launcher.property("y")) - (before[1] - 90)) < 2
        assert controller._save_workspace_preferences.call_count == 1
        saved_position = controller.aiLauncherPosition
        assert click_item(engine, root, launcher)
        wait_for_events(260)
        assert controller.aiLauncherPosition == saved_position
        assert root.property("aiPanelRequested")
        # Click outside the shared side panel should not dismiss it.
        QTest.mouseClick(root, Qt.LeftButton, Qt.NoModifier, QPoint(300, 50))
        assert root.property("aiPanelRequested")
        evaluate(chat, "focusComposer()")
        QTest.keyClick(root, Qt.Key_Escape)
        wait_for_events(220)
        assert not root.property("aiPanelRequested")
        evaluate(launcher, "forceActiveFocus()")
        QTest.keyClick(root, Qt.Key_Space)
        wait_for_events(260)
        assert root.property("aiPanelRequested")
        assert click_item(engine, root, launcher)
        wait_for_events(220)

        # Shrinking collapses the overlay once; growing never reopens it.
        QMetaObject.invokeMethod(launcher, "clicked")
        wait_for_events(300)
        assert root.property("aiPanelRequested")
        root.setProperty("width", 760)
        root.setProperty("height", 600)
        wait_for_events(300)
        assert not root.property("aiPanelRequested") and not panel.property("visible")
        assert draft.property("text") == "Unsent draft / 未发送草稿"
        QMetaObject.invokeMethod(launcher, "clicked")
        wait_for_events(300)
        compact_window = root.findChild(QObject, "aiWindowLoader").property("item")
        assert compact_window.property("visible") and not panel.property("visible")
        assert compact_window.findChild(QObject, "aiInputArea").property("text") == "Unsent draft / 未发送草稿"
        QMetaObject.invokeMethod(launcher, "clicked")
        wait_for_events(300)
        assert not compact_window.property("visible")
        for width, height in ((1200, 800), (1600, 900)):
            root.setProperty("width", width); root.setProperty("height", height)
            wait_for_events(300)
            assert not root.property("aiPanelRequested"), "Growing reopened Sage without a user action"
            assert evaluate(launcher, "x>=0 && y>=0 && x+width<=parent.width && y+height<=parent.height")
            before_geometry = (pane.property("width"), layout.property("height"))
            assert click_item(engine, root, launcher)
            wait_for_events(260)
            assert pane.property("width") >= 640 and layout.property("height") == before_geometry[1]
            assert click_item(engine, root, launcher)
            wait_for_events(220)
        # Qt 5's offscreen cursor is constrained by its virtual desktop; keep
        # real mouse events within that desktop after checking wide layouts.
        root.setProperty("width", 1200)
        root.setProperty("height", 800)
        wait_for_events(300)
        menu_point = QPoint(round(float(launcher.property("x"))+30), round(float(launcher.property("y"))+30))
        QTest.mouseMove(root, menu_point)
        QTest.mousePress(root, Qt.RightButton, Qt.NoModifier, menu_point)
        wait_for_events(30)
        QTest.mouseRelease(root, Qt.RightButton, Qt.NoModifier, menu_point)
        wait_for_events(250)
        menu = root.findChild(QObject, "sageLauncherMenu")
        assert menu.property("opened"), {key: menu.property(key) for key in ("visible", "opened", "x", "y")}
        QMetaObject.invokeMethod(root.findChild(QObject, "resetSagePosition"), "triggered")
        QMetaObject.invokeMethod(menu, "close")
        assert controller.aiLauncherPosition == [1.0, 1.0]
        # Explicit detach remains available; the same pet closes that window.
        QMetaObject.invokeMethod(root, "openAiWindow")
        wait_for_events(260)
        detached = root.findChild(QObject, "aiWindowLoader").property("item")
        assert detached.property("visible")
        assert detached.findChild(QObject, "aiInputArea").property("text") == "Unsent draft / 未发送草稿"
        detached.findChild(QObject, "aiInputArea").setProperty("text", "Draft changed in detached window")
        QMetaObject.invokeMethod(launcher, "clicked")
        wait_for_events(300)
        assert not detached.property("visible")
        QMetaObject.invokeMethod(launcher, "clicked")
        wait_for_events(300)
        assert draft.property("text") == "Draft changed in detached window"
        assert not errors, errors
        print("Sage interaction probe OK: shared tabs, reversible transition, protected workspace, drag/click separation, reset, keyboard, retained draft/scroll/search, hidden streaming, and explicit detach.")
    finally:
        delete_qobject(root)
        delete_qobject(engine)
        controller.close()
    return 0


def main() -> int:
    application = QApplication([])
    markdown_probe()
    sage_open_probe()
    design_probe()
    long_scroll_probe()
    interaction_probe()
    controller = Controller()
    controller._save_workspace_preferences = lambda: True
    engine = QQmlApplicationEngine()
    errors = []
    engine.warnings.connect(lambda messages: errors.extend(error.toString() for error in messages))
    engine.rootContext().setContextProperty("controller", controller)
    qml_path = Path(__file__).resolve().parents[1] / "hr_toolkit" / "gui_qt" / "qml" / "Main.qml"
    engine.load(QUrl.fromLocalFile(str(qml_path)))
    if not engine.rootObjects():
        print("AI probe FAILED: Main.qml did not load")
        for error in errors:
            print(error)
        return 1
    root = engine.rootObjects()[0]
    failures = []

    # Start with a settled workspace before comparing overlay geometry.
    root.setProperty("width", 1560)
    root.setProperty("height", 940)
    wait_for_events(400)

    main_pane = root.findChild(QObject, "mainPane")
    require(main_pane is not None, "mainPane missing", failures)
    pane_width_before = float(main_pane.property("width")) if main_pane is not None else 0.0

    # Opening the shared column must reserve width without overlapping the tool.
    panel_loader = root.findChild(QObject, "aiPanelLoader")
    require(panel_loader is not None, "aiPanelLoader missing", failures)
    if panel_loader is None:
        print("AI probe FAILED: " + "\n".join(failures))
        controller.close()
        return 1
    # 走真实入口：主窗口的开关状态，而不是直接激活 Loader。
    root.setProperty("aiPanelRequested", True)
    wait_for_events(600)

    require(panel_loader.property("active") is True, "aiPanelLoader did not activate", failures)

    side_panel = panel_loader.property("item")
    require(side_panel is not None, "AI overlay failed to instantiate", failures)
    require(root.findChild(QObject, "aiSidePanel") is not None, "aiSidePanel missing", failures)
    surface = root.findChild(QObject, "aiPanelSurface")
    require(surface is not None, "aiPanelSurface missing", failures)

    pane_width_after = float(main_pane.property("width")) if main_pane is not None else 0.0
    drawer = root.findChild(QObject, "workspaceDrawer")
    require(pane_width_after >= 640 and abs(pane_width_before - pane_width_after - float(drawer.property("width"))) < 2,
            "Sage did not reserve a separate column with a usable main workspace", failures)
    require(
        side_panel.property("opened") is True,
        "overlay reported itself closed",
        failures,
    )

    chat_panel = root.findChild(QObject, "aiChatPanel")
    require(chat_panel is not None, "aiChatPanel is not reachable by objectName", failures)
    if chat_panel is not None:
        require(
            float(chat_panel.property("width")) > 200, "AI chat panel collapsed", failures
        )
        require(
            float(chat_panel.property("height")) > 200, "AI chat panel lost its height", failures
        )
        require(
            float(chat_panel.property("x")) == 1, "AI panel lost its border inset", failures
        )
    if surface is not None and chat_panel is not None:
        require(
            abs(float(surface.property("width")) - float(chat_panel.property("width")) - 2) <= 0.5,
            "AI panel width drifted from the overlay surface",
            failures,
        )
        require(
            abs(float(chat_panel.property("x")) - float(surface.property("x")) - 1) <= 0.5,
            "AI panel is not aligned with the overlay surface",
            failures,
        )

    # 输入框不能两端回弹：ScrollView 内部那个 Flickable 必须是 StopAtBounds(0)。
    # 默认的 DragAndOvershootBounds(3) 就是 macOS 上滚到顶/底会橡皮筋的原因。
    input_scroll = root.findChild(QObject, "aiInputScroll")
    require(input_scroll is not None, "aiInputScroll missing", failures)
    if input_scroll is not None:
        bounds = qml_number(engine, input_scroll, "contentItem.boundsBehavior")
        require(
            bounds == 0,
            "input box still rubber-bands (boundsBehavior=%s, want StopAtBounds)" % bounds,
            failures,
        )

    # 拖拽接收区与「待发附件」区都要落地（新的拖入/粘贴路径）。
    require(root.findChild(QObject, "aiDropArea") is not None, "aiDropArea missing", failures)
    pending = root.findChild(QObject, "aiPendingAttachments")
    require(pending is not None, "aiPendingAttachments missing", failures)

    # 注入三条消息，把用户气泡（含图片缩略图）、助手 Markdown、加载态三条委托路径都跑一遍。
    chat_model = controller.aiChatModel
    chat_model.append(
        {
            "role": "user",
            "content": "这张考勤截图里的加班时长对吗？",
            "streaming": False,
            "time": "10:01",
            "attachments": [
                {"name": "keqin.png", "summary": "6×6 · 120 B", "path": "",
                 "kind": "image", "preview": ""},
                {"name": "九月工资表.xlsx", "summary": "3 个工作表", "path": "",
                 "kind": "sheet", "preview": ""},
            ],
        }
    )
    chat_model.append({"role": "assistant", "content": "**结论**：第 3 行少算 2 小时。",
                       "streaming": False, "time": "10:01"})
    chat_model.append({"role": "assistant", "content": "正在分析…", "streaming": True,
                       "time": "10:02"})
    wait_for_events(250)

    # 等待首个字的那句提示必须由 controller 按这一轮的附件给出来。
    # 早期版本是在 QML 里写死一串（第一句还是「正在读取表格…」），于是粘一张截图
    # 也会提示「正在读取表格」——那是假的，用户一眼就能看出来。
    if chat_panel is not None:
        label = QQmlExpression(
            engine.rootContext(), chat_panel,
            "(function(){"
            "function walk(it,n){if(it.objectName===n)return it;"
            "var c=it.children;for(var i=0;i<c.length;++i){var r=walk(c[i],n);if(r)return r;}"
            "return null;}"
            "var c=children;"
            "for(var i=0;i<c.length;++i){var r=walk(c[i],'aiStatusLabel');if(r)return ''+r.text;}"
            "return '<no status label>';})()",
        ).evaluate()
        if isinstance(label, tuple):
            label = label[0]
        presentation = controller._presentation
        phrases = [
            presentation.translate(value, presentation.language)
            for value in controller.aiStatusPhrases
        ]
        require(
            isinstance(label, str) and label in phrases,
            "the waiting hint is not driven by the controller (%r not in %r)"
            % (label, phrases),
            failures,
        )

    # 模型返回的表格在 QML 富文本里不继承控件字体，得由 controller 把当前界面字体
    # 写进 table 上；这里在真 QApplication 下确认那条链路没悄悄断掉。
    table_html = controller._ai_render("| 名称 | 金额 |\n| --- | --- |\n| 张三 | 100 |")
    require(
        "font-family:" in table_html,
        "the rendered markdown table lost the UI font family",
        failures,
    )

    # 待发区：真加一张图 + 一份表格（图片走缓存与降采样管线，顺带验证视觉提示横幅）。
    attached = controller._ai_attach_image_payload(
        name="probe.png", data=tiny_png(), mime="image/png", width=6, height=6
    )
    require(attached is True, "pasting an image into the session failed", failures)
    controller.aiAttachmentModel.append(
        {"name": "工资表.xlsx", "summary": "2 个工作表", "path": "", "kind": "sheet",
         "preview": ""}
    )
    wait_for_events(250)
    if pending is not None:
        require(
            float(pending.property("height")) > 40,
            "pending attachment chips did not lay out",
            failures,
        )
    hint = root.findChild(QObject, "aiVisionHint")
    require(hint is not None, "aiVisionHint missing", failures)
    if hint is not None and not controller.aiVisionCapable:
        require(
            hint.property("visible") is True and float(hint.property("height")) > 20,
            "vision hint did not show for a non-vision model with a pending image",
            failures,
        )

    # 附件右侧那个 × 必须真的能删掉东西：铺满整块的 chipMouse 如果压在它上面，
    # 点击会被它吃掉（图片变成「打开预览」、表格则毫无反应），× 形同虚设。
    # × 是悬停才显形的，所以走真实路径：先把指针移进附件块，再点 ×。
    if pending is not None:
        spot = QQmlExpression(
            engine.rootContext(), pending,
            "(function(){"
            "function walk(it,n){if(it.objectName===n)return it;"
            "var c=it.children;for(var i=0;i<c.length;++i){var r=walk(c[i],n);if(r)return r;}"
            "return null;}"
            "var chip=null,c=children;"
            "for(var i=0;i<c.length;++i){var r=walk(c[i],'aiAttachmentChip');if(r){chip=r;break;}}"
            "if(!chip)return '<no chip>';"
            "var btn=walk(chip,'aiAttachmentRemove');"
            "if(!btn)return '<no x button>';"
            "var h=chip.mapToItem(null,chip.width/2,chip.height/2);"
            "var b=btn.mapToItem(null,btn.width/2,btn.height/2);"
            "return ''+h.x+','+h.y+','+b.x+','+b.y;})()",
        ).evaluate()
        if isinstance(spot, tuple):
            spot = spot[0]
        require(
            isinstance(spot, str) and spot.count(",") == 3,
            "could not locate the attachment chip and its x button (%r)" % spot,
            failures,
        )
        if isinstance(spot, str) and spot.count(",") == 3:
            hover_x, hover_y, click_x, click_y = (float(value) for value in spot.split(","))
            before = controller.aiAttachmentModel.rowCount()
            QTest.mouseMove(root, QPoint(int(hover_x), int(hover_y)))
            wait_for_events(150)
            QTest.mouseMove(root, QPoint(int(click_x), int(click_y)))
            wait_for_events(150)
            QTest.mouseClick(root, Qt.LeftButton, Qt.NoModifier,
                             QPoint(int(click_x), int(click_y)))
            wait_for_events(250)
            after = controller.aiAttachmentModel.rowCount()
            require(
                after == before - 1,
                "clicking the x on a pending attachment did nothing (%d -> %d)"
                % (before, after),
                failures,
            )

    # 图片放大预览
    preview_popup = root.findChild(QObject, "aiImagePreviewPopup")
    require(preview_popup is not None, "aiImagePreviewPopup missing", failures)
    if preview_popup is not None:
        QMetaObject.invokeMethod(preview_popup, "open")
        wait_for_events(200)
        require(preview_popup.property("opened") is True, "image preview failed to open", failures)
        require(
            float(preview_popup.property("width")) > 100, "image preview collapsed", failures
        )
        QMetaObject.invokeMethod(preview_popup, "close")
        wait_for_events(120)

    # 独立窗口
    window_loader = root.findChild(QObject, "aiWindowLoader")
    require(window_loader is not None, "aiWindowLoader missing", failures)
    if window_loader is not None:
        window_loader.setProperty("active", True)
        wait_for_events(60)
        ai_window = window_loader.property("item")
        require(ai_window is not None, "AI window failed to instantiate", failures)
        if ai_window is not None:
            ai_window.setProperty("requestedOpen", True)
            wait_for_events(350)

    # 设置对话框：切服务商必须真的切过去。
    # 早期 reloadFields() 会把 providerCombo.currentIndex 拨回 controller.aiActiveProvider，
    # 于是点 DeepSeek 立刻又弹回 MiniMax —— 用户看到的就是「切换无效」。
    dialog = root.findChild(QObject, "aiSettingsDialog")
    require(dialog is not None, "aiSettingsDialog missing", failures)
    if dialog is not None:
        QMetaObject.invokeMethod(dialog, "open")
        wait_for_events(300)
        combo = root.findChild(QObject, "aiProviderCombo")
        require(combo is not None, "aiProviderCombo missing", failures)
        if combo is not None:
            provider_ids = [row["value"] for row in controller.aiProviderOptions]
            require(
                [value for value in ("deepseek", "minimax", "glm", "qwen") if value in provider_ids]
                == ["deepseek", "minimax", "glm", "qwen"],
                "内置服务商不全：%r" % provider_ids,
                failures,
            )
            target = provider_ids.index("deepseek")
            combo.setProperty("currentIndex", target)
            # 走真实激活路径：光设 currentIndex 不会触发 onActivated，测不出那个 bug。
            activation = QQmlExpression(engine.rootContext(), combo, "activated(%d)" % target)
            activation.evaluate()
            activated = not activation.hasError()
            wait_for_events(200)
            require(activated, "could not activate the provider combo", failures)
            require(
                int(combo.property("currentIndex")) == target,
                "选中的服务商又弹回去了（切换无效）",
                failures,
            )
            model_field = root.findChild(QObject, "aiModelField")
            endpoint_field = root.findChild(QObject, "aiEndpointField")
            require(
                model_field is not None and str(model_field.property("text")) == "deepseek-flash",
                "切到 DeepSeek 后模型栏没跟着换（%r）"
                % (model_field.property("text") if model_field is not None else None),
                failures,
            )
            require(
                endpoint_field is not None
                and "api.deepseek.com" in str(endpoint_field.property("text")),
                "切到 DeepSeek 后服务地址没跟着换（%r）"
                % (endpoint_field.property("text") if endpoint_field is not None else None),
                failures,
            )
            hint = root.findChild(QObject, "aiModelChoicesHint")
            require(
                hint is not None and "deepseek-v4-pro" in str(hint.property("text")),
                "模型候选提示没跟着服务商换",
                failures,
            )
            # 保存之后要真的生效，而不是只改了界面。
            save_button = root.findChild(QObject, "aiSettingsSave")
            require(
                save_button is not None and click_item(engine, root, save_button),
                "could not click the settings save button",
                failures,
            )
            wait_for_events(250)
            require(
                controller.aiActiveProvider == "deepseek",
                "保存后当前服务商仍是 %r" % controller.aiActiveProvider,
                failures,
            )
            # 换回 MiniMax：后面的用例继续按原状态跑。
            require(controller.aiSelectProvider("minimax"), "cannot switch back", failures)
            wait_for_events(150)
        QMetaObject.invokeMethod(dialog, "close")

    # 两个浮层：历史对话与模型切换。二者的宽度都必须写死，
    # 一旦宽度依赖「子项隐式宽 ← 子项又要 parent.width」，会在打开瞬间形成绑定环把界面卡死。
    controller.aiConversationModel.append(
        {
            "id": "probe-conv",
            "title": "对比两张薪资表的总额差异",
            "updated": "今天 10:01",
            "preview": "问题4 整体应发更高…",
            "active": True,
        }
    )
    controller.aiSearchHistory("薪资")
    wait_for_events(120)
    # 表头按钮得真能点：WindowChrome 是 z:30 的全宽浮条，它的拖拽 MouseArea
    # 只要还铺满整宽，就会把面板表头（正落在那 40px 里）的点击全部吃掉。
    history_button = root.findChild(QObject, "aiHistoryButton")
    history_popup = root.findChild(QObject, "aiHistoryPopup")
    require(history_button is not None, "aiHistoryButton missing", failures)
    if history_button is not None and history_popup is not None:
        require(
            click_item(engine, root, history_button),
            "could not resolve the history button's window position",
            failures,
        )
        wait_for_events(300)
        require(
            history_popup.property("opened") is True,
            "clicking the header's history button did not open the popup "
            "(something covers the panel header)",
            failures,
        )
        # 只验证「点得开」：再点一次能否关掉是浮层自己的 closePolicy 与
        # 按钮 toggle 的逻辑之争，跟「表头被盖住」这件事无关。
        QMetaObject.invokeMethod(history_popup, "close")
        wait_for_events(200)
    for popup_name in ("aiHistoryPopup", "aiModelPopup"):
        popup = root.findChild(QObject, popup_name)
        require(popup is not None, "%s is not reachable by objectName" % popup_name, failures)
        if popup is None:
            continue
        QMetaObject.invokeMethod(popup, "open")
        wait_for_events(250)
        require(popup.property("opened") is True, "%s failed to open" % popup_name, failures)
        require(float(popup.property("width")) > 80, "%s collapsed" % popup_name, failures)
        require(float(popup.property("height")) > 20, "%s lost its height" % popup_name, failures)
        QMetaObject.invokeMethod(popup, "close")
        wait_for_events(120)
    controller.aiSearchHistory("")

    # 模型菜单：自己加模型（可加多个）、以及把列表里的模型删掉。
    model_popup = root.findChild(QObject, "aiModelPopup")
    require(model_popup is not None, "aiModelPopup missing", failures)
    if model_popup is not None:
        before_models = len(controller.aiModelOptions)
        QMetaObject.invokeMethod(model_popup, "open")
        wait_for_events(250)

        # 服务商在面板里也能切（不必回设置里翻）；切完下面那串模型跟着换。
        spots = provider_row_spots(engine, model_popup)
        require(
            len(spots) == 4,
            "模型菜单里没有四个服务商入口（%r）" % (spots,),
            failures,
        )
        if len(spots) == 4:
            require(
                controller.aiActiveProvider == "minimax",
                "探针起始服务商不对（%r）" % controller.aiActiveProvider,
                failures,
            )
            QTest.mouseClick(root, Qt.LeftButton, Qt.NoModifier, QPoint(*spots[0]))
            wait_for_events(250)
            require(
                controller.aiActiveProvider == "deepseek",
                "在模型菜单里点 DeepSeek 没切过去（%r）" % controller.aiActiveProvider,
                failures,
            )
            require(
                "deepseek-v4-pro" in [row["value"] for row in controller.aiModelOptions],
                "切了服务商，模型列表没跟着换",
                failures,
            )
            # 浮层高度跟着模型条数变，位置会挪 —— 每次点之前重新取坐标。
            spots = provider_row_spots(engine, model_popup)
            if len(spots) == 4:
                QTest.mouseClick(root, Qt.LeftButton, Qt.NoModifier, QPoint(*spots[1]))
                wait_for_events(250)
            require(
                controller.aiActiveProvider == "minimax",
                "切回 MiniMax 失败（%r）" % controller.aiActiveProvider,
                failures,
            )

        # 1) 点「添加模型…」→ 输入框出现；填名字提交后应当直接切过去，并进列表。
        add_row = root.findChild(QObject, "aiNewModelField")
        require(add_row is not None, "aiNewModelField missing", failures)
        field = add_row
        if field is not None:
            field.setProperty("text", "probe-custom-vl")
            QMetaObject.invokeMethod(model_popup, "commitNewModel")
            wait_for_events(250)
            require(
                controller.aiActiveModel == "probe-custom-vl",
                "adding a model did not switch to it (active=%r)" % controller.aiActiveModel,
                failures,
            )
            require(
                len(controller.aiModelOptions) == before_models + 1,
                "the model list did not grow (%d -> %d)"
                % (before_models, len(controller.aiModelOptions)),
                failures,
            )

        # 2) 再加一个，确认「支持多个」而不只是替换掉上一个。
        QMetaObject.invokeMethod(model_popup, "open")
        wait_for_events(150)
        QMetaObject.invokeMethod(model_popup, "cancelNewModel")
        if field is not None:
            model_popup.setProperty("adding", True)
            field.setProperty("text", "probe-second-model")
            QMetaObject.invokeMethod(model_popup, "commitNewModel")
            wait_for_events(200)
        names = [row.get("value") for row in controller.aiModelOptions]
        require(
            "probe-custom-vl" in names and "probe-second-model" in names,
            "the model list kept only one custom model: %r" % names,
            failures,
        )

        # 3) 删掉一个不是当前在用的（在用的那个必须拒绝删，否则配置会被删空）。
        removed = controller.aiRemoveModel("probe-custom-vl")
        wait_for_events(150)
        names = [row.get("value") for row in controller.aiModelOptions]
        require(removed, "aiRemoveModel refused a custom model", failures)
        require(
            "probe-custom-vl" not in names,
            "the removed model is still in the list: %r" % names,
            failures,
        )
        require(
            controller.aiRemoveModel(controller.aiActiveModel) is False,
            "removing the model in use should be refused",
            failures,
        )
        QMetaObject.invokeMethod(model_popup, "close")
        wait_for_events(120)

    # Collapsing hides the overlay after its exit transition, retaining the view.
    root.setProperty("aiPanelRequested", False)
    wait_for_events(250)
    require(panel_loader.property("active") is True, "collapsed overlay was destroyed", failures)
    require(not side_panel.property("visible"), "collapsed overlay stayed visible", failures)
    require(abs(float(main_pane.property("width")) - pane_width_before) < 1,
            "collapsing changed the workspace width", failures)
    root.setProperty("aiPanelRequested", True)
    wait_for_events(300)
    require(side_panel.property("visible") is True, "overlay did not reopen", failures)

    if window_loader is not None and window_loader.property("item") is not None:
        window_loader.property("item").setProperty("requestedOpen", False)

    # Exercise both catalogs/palettes and the small-window entry point.
    for language, theme in (("en_US", "dark"), ("zh_CN", "light"), ("en_US", "light"), ("zh_CN", "dark")):
        controller.presentation.setLanguage(language)
        controller.presentation.setTheme(theme)
        wait_for_events(80)
        if os.environ.get("HR_AI_REVIEW_CAPTURE") and language == "en_US":
            root.grabWindow().save(os.environ["HR_AI_REVIEW_CAPTURE"] + "-" + theme + ".png")
    root.setProperty("aiPanelRequested", False)
    if window_loader is not None and window_loader.property("item") is not None:
        window_loader.property("item").setProperty("requestedOpen", False)
    root.setProperty("width", 1024)
    wait_for_events(250)
    QMetaObject.invokeMethod(root, "toggleAiPanel")
    wait_for_events(250)
    require(not root.property("aiPanelRequested") and not side_panel.property("visible")
            and window_loader.property("item").property("requestedOpen"),
            "small-window entry did not use the detached assistant", failures)
    require(float(side_panel.property("width")) <= float(root.property("width")) - 24,
            "small-window overlay exceeds the window", failures)

    chat_model.clear()

    # 先算断言失败和运行期错误；销毁整个面板会在 QML 里产生一批
    # 「controller 已置空」的告警，那是 QML 自身的释放顺序，不算失败。
    runtime = [
        error
        for error in errors
        if "TypeError" in error
        or "ReferenceError" in error
        or "is not defined" in error
        or "Cannot read" in error
        or "Unable to assign" in error
        or "Cannot assign" in error
        or "binding loop" in error.lower()
    ]
    failures.extend(runtime)

    # Close without destroying the retained conversation view.
    root.setProperty("aiPanelRequested", False)
    wait_for_events(250)

    if failures:
        print("AI probe FAILED:")
        for failure in failures:
            print(failure)
        controller.close()
        return 1
    from hr_toolkit.gui_qt.compat import delete_qobject
    delete_qobject(root)
    delete_qobject(engine)
    controller.close()
    print(
        "AI probe OK: shared column protects workspace geometry and survives collapse, the input box "
        "does not rubber-band, and the "
        "chat delegates, pending attachments, drop area, vision hint, image preview, "
        "history/model popups, settings dialog and detached window all instantiate cleanly"
    )
    return 0


if __name__ == "__main__":
    sys.exit(interaction_probe() if "--interaction-only" in sys.argv else long_scroll_probe() if "--long-scroll-only" in sys.argv else design_probe() if "--design-only" in sys.argv else sage_open_probe() if "--sage-open-only" in sys.argv else markdown_probe() if "--markdown-only" in sys.argv else main())
