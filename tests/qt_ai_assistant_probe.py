"""Compile and instantiate the docked Sage panel, its popups and the detached window."""
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
from hr_toolkit.gui_qt.compat import QApplication, QObject, Property, Slot, QUrl, QT_MAJOR
from hr_toolkit.gui_qt.controller import AppController

# 探针绝不能碰用户真实的设置 / 对话历史：模型增删、切换与历史同步都会落盘。
# （曾经因为没隔离，把 probe-* 模型写进了用户自己的 ai-assistant.json。）
_PROBE_DIR = Path(tempfile.mkdtemp(prefix="hr-toolkit-ai-probe-"))
ai_config.default_settings_path = lambda: _PROBE_DIR / "ai-assistant.json"
ai_history.default_conversations_path = lambda: _PROBE_DIR / "ai-conversations.json"

if QT_MAJOR == 6:
    from PySide6.QtCore import Q_ARG, QEventLoop, QMetaObject, QPoint, Qt, QTimer
    from PySide6.QtQml import QQmlApplicationEngine, QQmlExpression
    from PySide6.QtTest import QTest
else:
    from PySide2.QtCore import Q_ARG, QEventLoop, QMetaObject, QPoint, Qt, QTimer
    from PySide2.QtQml import QQmlApplicationEngine, QQmlExpression
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


def main() -> int:
    application = QApplication([])
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

    # 给足宽度，否则停靠面板会按设计自动收起，后面的断言就没有意义了。
    root.setProperty("width", 1560)
    root.setProperty("height", 940)
    wait_for_events(400)

    main_pane = root.findChild(QObject, "mainPane")
    require(main_pane is not None, "mainPane missing", failures)
    pane_width_before = float(main_pane.property("width")) if main_pane is not None else 0.0

    # 打开 Sage：它是 RowLayout 的子项，应该「占住」宽度而不是浮在内容上面。
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
    require(side_panel is not None, "AI docked panel failed to instantiate", failures)
    require(root.findChild(QObject, "aiSidePanel") is not None, "aiSidePanel missing", failures)
    surface = root.findChild(QObject, "aiPanelSurface")
    require(surface is not None, "aiPanelSurface missing", failures)

    reserved = float(panel_loader.property("reserved"))
    require(reserved > 100, "docked panel reserved no width (%.1f)" % reserved, failures)
    pane_width_after = float(main_pane.property("width")) if main_pane is not None else 0.0
    require(
        pane_width_before - pane_width_after >= reserved - 1.0,
        "middle content was covered instead of narrowed: %.1f -> %.1f, reserved %.1f"
        % (pane_width_before, pane_width_after, reserved),
        failures,
    )
    require(
        side_panel.property("opened") is True,
        "docked panel reported itself closed",
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
            float(chat_panel.property("x")) >= 4, "AI panel lost its floating gutter", failures
        )
    if surface is not None and chat_panel is not None:
        require(
            abs(float(surface.property("width")) - float(chat_panel.property("width"))) <= 0.5,
            "AI panel width drifted from the docked card",
            failures,
        )
        require(
            abs(float(surface.property("x")) - float(chat_panel.property("x"))) <= 0.5,
            "AI panel is not aligned with the docked card",
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
            ai_window.setProperty("visible", True)
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
            activated = QMetaObject.invokeMethod(combo, "activated", Q_ARG("int", target))
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
                model_field is not None and str(model_field.property("text")) == "deepseek-chat",
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
                hint is not None and "deepseek-reasoner" in str(hint.property("text")),
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
                "deepseek-reasoner" in [row["value"] for row in controller.aiModelOptions],
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

    # 收起：留一条窄轨，中间内容把宽度拿回去；再展开回到完整面板。
    if side_panel is not None:
        side_panel.setProperty("collapsed", True)
        wait_for_events(300)
        collapsed_reserved = float(panel_loader.property("reserved"))
        rail = root.findChild(QObject, "aiPanelRail")
        require(
            collapsed_reserved < reserved,
            "collapsing did not release width (%.1f -> %.1f)"
            % (reserved, collapsed_reserved),
            failures,
        )
        require(rail is not None, "aiPanelRail missing", failures)
        if rail is not None:
            require(rail.property("visible") is True, "collapsed rail is not visible", failures)
        require(
            float(main_pane.property("width")) > pane_width_after,
            "middle content did not widen back after collapsing",
            failures,
        )
        QMetaObject.invokeMethod(side_panel, "expand")
        wait_for_events(300)
        require(
            abs(float(panel_loader.property("reserved")) - reserved) <= 1.0,
            "expanding did not restore the reserved width",
            failures,
        )
        if chat_panel is not None:
            require(
                chat_panel.property("visible") is True,
                "chat panel stayed hidden after expanding",
                failures,
            )

    if window_loader is not None and window_loader.property("item") is not None:
        window_loader.property("item").setProperty("visible", False)

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

    # 关闭面板：Loader 失活，AiSidePanel / AiChatPanel 全部销毁，不应崩。
    root.setProperty("aiPanelRequested", False)
    wait_for_events(250)

    if failures:
        print("AI probe FAILED:")
        for failure in failures:
            print(failure)
        controller.close()
        return 1
    controller.close()
    print(
        "AI probe OK: docked panel reserves width (%.0f px), collapses to a rail, the input box "
        "does not rubber-band, and the "
        "chat delegates, pending attachments, drop area, vision hint, image preview, "
        "history/model popups, settings dialog and detached window all instantiate cleanly"
        % reserved
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
