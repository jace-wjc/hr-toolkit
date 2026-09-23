import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15

// Sage 对话面板：抽屉与独立窗口共用的内容。
// 数据全部来自 controller 的懒加载模型；面板本身不持有会话状态。
//
// 版式约定：用户消息靠右的浅灰气泡（附件挂在气泡里），助手消息靠左、
// 头部带日芒标记，正文渲染 Markdown 富文本，底部是一张圆角输入卡片。
// 注意：消息代理与外层 ColumnLayout 都不做「由父布局定尺寸、又回写依赖该尺寸的尺寸提示」，
// 以免触发 QQuickLayout 的 invalidate 递归（见 docs/qt-layout-ci-fix.md）。
Item {
    id: panel

    objectName: "aiChatPanel"

    signal closeRequested()
    signal settingsRequested()
    signal detachRequested()
    signal collapseRequested()

    property bool showDetachButton: true
    property bool showCloseButton: true
    property bool showCollapseButton: true
    // 图片放大预览用的路径（空串表示不显示）
    property string previewImage: ""
    // 正在编辑的用户消息行号；-1 表示正常发送
    property int editingRow: -1
    property string editingBackup: ""
    // 有文件正拖在面板上方（用来决定要不要显示「松手即可附加」）
    property bool dropActive: false
    property string conversationId: ""

    readonly property color textMain: Ui.color("text")
    readonly property color textMuted: Ui.color("muted")
    readonly property color textFaint: Ui.color("faint")
    readonly property color accent: Ui.color("accent")
    readonly property color cardBorder: Ui.color("border")
    readonly property color markColor: Ui.color("markRay")

    readonly property var statusPhrases: controller.aiStatusPhrases
    readonly property int statusIndex: 0

    // 草稿防抖落盘：每敲一个字都写文件没必要，停手 600ms 再存。
    Timer {
        id: draftTimer
        interval: 600
        repeat: false
        onTriggered: controller.aiSaveDraft(inputArea.text)
    }

    function saveDraftNow() {
        draftTimer.stop()
        if (panel.editingRow < 0) controller.aiSaveDraft(inputArea.text)
    }

    function submitInput() {
        if (!controller.aiReady)
            return
        if (controller.aiBusy) return
        draftTimer.stop()
        var text = inputArea.text.trim()
        if (text.length > 10000) {
            controller.aiSendMessage(text)
            return
        }
        if (!text && aiAttachmentRepeater.count === 0)
            return
        if (panel.editingRow >= 0) {
            var row = panel.editingRow
            panel.cancelEdit()
            inputArea.text = ""
            controller.aiEditMessage(row, text)
            return
        }
        inputArea.text = ""
        controller.aiSaveDraft("")
        controller.aiSendMessage(text)
    }

    function cancelEdit() {
        panel.editingRow = -1
        if (panel.editingBackup.length > 0) {
            inputArea.text = panel.editingBackup
            panel.editingBackup = ""
        }
        inputArea.forceActiveFocus()
    }

    function beginEdit(row, text) {
        if (controller.aiBusy) return
        panel.editingBackup = inputArea.text
        panel.editingRow = row
        inputArea.text = text
        inputArea.forceActiveFocus()
    }

    // 缩略图点开看大图；没有可用路径时什么都不做（缓存被清掉的图只剩文件名）。
    function openPreview(url) {
        if (!url) return
        panel.previewImage = url
        imagePreviewPopup.open()
    }

    Component.onCompleted: {
        controller.aiActivate()
        panel.conversationId = controller.aiConversationId
        inputArea.text = controller.aiDraft
    }

    Component.onDestruction: {
        draftTimer.stop()
        if (controller && panel.editingRow < 0 && panel.conversationId === controller.aiConversationId)
            controller.aiSaveDraft(inputArea.text)
    }

    // 切换对话时换回那条对话自己的草稿（发送后 aiDraft 会被清空）。
    Connections {
        target: controller
        function onAiChanged() {
            if (panel.conversationId !== controller.aiConversationId) {
                draftTimer.stop()
                panel.conversationId = controller.aiConversationId
                panel.editingRow = -1
                panel.editingBackup = ""
                inputArea.text = controller.aiDraft
                return
            }
            if (!inputArea.activeFocus || inputArea.text.length === 0)
                inputArea.text = controller.aiDraft
        }
    }

    ColumnLayout {
        anchors.fill: parent
        spacing: 0

        // ---------- 头部 ----------
        Rectangle {
            Layout.fillWidth: true
            Layout.preferredHeight: 52
            color: "transparent"
            RowLayout {
                anchors.fill: parent
                anchors.leftMargin: 14
                anchors.rightMargin: 6
                spacing: 2
                ColumnLayout {
                    Layout.fillWidth: true
                    spacing: 1
                    Text {
                        text: "Sage"
                        color: panel.textMain
                        font.pixelSize: 15
                        font.weight: Font.DemiBold
                    }
                    Text {
                        Layout.fillWidth: true
                        text: Ui.text(controller.aiActiveProviderLabel)
                        color: panel.textFaint
                        font.pixelSize: 10
                        elide: Text.ElideRight
                    }
                }
                IconAction {
                    id: historyButton
                    objectName: "aiHistoryButton"
                    iconId: "clock"
                    tip: "历史对话"
                    onClicked: historyPopup.opened ? historyPopup.close() : historyPopup.open()
                }
                IconAction {
                    iconId: "new_chat"
                    tip: "新对话"
                    enabled: !controller.aiBusy
                    onClicked: { panel.saveDraftNow(); controller.aiNewConversation() }
                }
                IconAction {
                    iconId: "gear"
                    tip: "设置"
                    onClicked: panel.settingsRequested()
                }
                IconAction {
                    iconId: "expand"
                    tip: "独立窗口打开"
                    visible: panel.showDetachButton
                    onClicked: panel.detachRequested()
                }
                IconAction {
                    iconId: "chevron_right"
                    tip: "收起（只留一条窄轨）"
                    visible: panel.showCollapseButton
                    onClicked: panel.collapseRequested()
                }
                IconAction {
                    iconId: "close"
                    tip: "关闭"
                    visible: panel.showCloseButton
                    onClicked: panel.closeRequested()
                }
            }
            Rectangle {
                anchors.left: parent.left
                anchors.right: parent.right
                anchors.bottom: parent.bottom
                height: 1
                color: Ui.color("divider")
            }
        }

        // ---------- 未配置提示 ----------
        Rectangle {
            Layout.fillWidth: true
            Layout.preferredHeight: controller.aiReady ? 0 : notReadyColumn.height + 20
            visible: !controller.aiReady
            color: Ui.color("surface")
            Column {
                id: notReadyColumn
                anchors.left: parent.left
                anchors.right: parent.right
                anchors.top: parent.top
                anchors.margins: 10
                spacing: 6
                Text {
                    width: parent.width
                    text: Ui.text(controller.aiSetupMessage || "尚未配置 AI 服务。")
                    color: Ui.color("warning3")
                    font.pixelSize: 12
                    wrapMode: Text.Wrap
                }
                AppButton {
                    variant: "tonal"
                    text: "去配置 API Key"
                    onClicked: panel.settingsRequested()
                }
            }
            Rectangle {
                anchors.left: parent.left
                anchors.right: parent.right
                anchors.bottom: parent.bottom
                height: 1
                color: Ui.color("divider")
            }
        }

        // ---------- 消息区 ----------
        // 外面套一层 Item 是为了在视图上叠一个「回到底部」按钮：
        Text {
            Layout.fillWidth: true
            Layout.leftMargin: 14
            Layout.rightMargin: 14
            text: Ui.text(controller.aiPreparing ? "正在准备附件，可点击停止取消。" : "发送后，问题、历史上下文和所附文件内容会传给所选 AI 服务。项目文件不会自动发送。")
            color: panel.textMuted
            font.pixelSize: 11
            wrapMode: Text.Wrap
        }

        // ListView 的直接子项会变成内容项跟着滚，浮层必须放在它外面。
        Item {
            Layout.fillWidth: true
            Layout.fillHeight: true

            ListView {
                id: aiChatView
                objectName: "aiChatView"
                anchors.fill: parent
                clip: true
                boundsBehavior: Flickable.StopAtBounds
                model: controller.aiChatModel
                spacing: 12
                topMargin: 14
                // Keep breathing room inside the scrollable content so
                // positionViewAtEnd includes it after streamed text/actions.
                bottomMargin: 0
                footer: Item {
                    width: aiChatView.width
                    height: aiChatView.count > 0 ? 24 : 0
                }
                // 流式输出时跟着最新内容走；用户手动上滚就暂停跟随，回到底部再恢复。
                property bool followTail: true
                // Virtualized rows must retain their measured size when they
                // leave the viewport. Recreating a long response at 60px can
                // make ListView discard/recreate it repeatedly as it expands.
                property var measuredHeights: ({})
                property int measurementEpoch: 0
                Connections {
                    target: controller.aiChatModel
                    function onModelAboutToBeReset() {
                        aiChatView.measurementEpoch += 1
                        aiChatView.measuredHeights = ({})
                    }
                }
                // A restored response may change height while Qt is creating
                // its table/text delegates. Scrolling inside that layout pass
                // can recreate delegates indefinitely (notably with CJK fonts).
                // Coalesce requests onto the next event-loop turn instead.
                function scheduleTail() { if (followTail) tailTimer.restart() }
                Timer {
                    id: tailTimer
                    interval: 16
                    repeat: false
                    onTriggered: if (aiChatView.followTail) aiChatView.positionViewAtEnd()
                }
                ScrollBar.vertical: ScrollBar { policy: ScrollBar.AsNeeded }
                onCountChanged: {
                    followTail = true
                    scheduleTail()
                }
                onContentHeightChanged: scheduleTail()
                // The composer can grow or shrink without changing messages.
                // Preserve the bottom gap only while following new replies.
                onHeightChanged: scheduleTail()
                onMovementStarted: { followTail = false; tailTimer.stop() }
                onMovementEnded: followTail = atYEnd
                Component.onCompleted: scheduleTail()

                // 空状态：一句说明 + 几个建议问题。
                // 注意这些子项都是布局子项，只能写 Layout.* 不能写 anchors，
                // 否则 anchors 会盖掉布局结果、把几行字和按钮叠在一起。
                ColumnLayout {
                    anchors.horizontalCenter: parent.horizontalCenter
                    y: 28
                    width: Math.min(parent ? parent.width - 32 : 300, 300)
                    spacing: 10
                    visible: aiChatView.count === 0
                    Text {
                        Layout.fillWidth: true
                        text: Ui.text("可以直接提问，也可以把表格或截图粘贴／拖进来让我分析。")
                        color: panel.textMuted
                        font.pixelSize: 13
                        wrapMode: Text.Wrap
                        horizontalAlignment: Text.AlignHCenter
                    }
                    Repeater {
                        model: controller.aiSuggestions
                        delegate: Button {
                            id: suggestionButton
                            Layout.fillWidth: true
                            padding: 10
                            hoverEnabled: true
                            text: modelData
                            onClicked: {
                                inputArea.text = ""
                                controller.aiSendMessage(Ui.text(modelData))
                            }
                            contentItem: Text {
                                text: Ui.text(suggestionButton.text)
                                color: panel.accent
                                font.pixelSize: 12
                                horizontalAlignment: Text.AlignHCenter
                                verticalAlignment: Text.AlignVCenter
                                elide: Text.ElideRight
                            }
                            background: Rectangle {
                                radius: 8
                                color: suggestionButton.hovered ? Ui.color("selection8") : Ui.color("selection")
                            }
                        }
                    }
                }

                delegate: Item {
                    id: messageDelegate

                readonly property bool isUser: model.role === "user"
                readonly property string body: model.content || ""
                readonly property var files: model.attachments || []
                readonly property bool isLast: index === aiChatView.count - 1
                // 图片与表格分开渲染：图片给缩略图，表格给一行文件条。
                readonly property var imageFiles: {
                    var out = []
                    for (var i = 0; i < files.length; ++i)
                        if (String(files[i].kind || "sheet") === "image") out.push(files[i])
                    return out
                }
                readonly property var sheetFiles: {
                    var out = []
                    for (var i = 0; i < files.length; ++i)
                        if (String(files[i].kind || "sheet") !== "image") out.push(files[i])
                    return out
                }
                readonly property bool showUserActions: isUser && body.length > 0
                    readonly property real sideGap: 12
                    readonly property real maxBubbleWidth: Math.max(120, width - sideGap * 2 - 20)

                    width: aiChatView.width
                    // Rich text starts with a provisional width while nested
                    // components are created. Publish the final row height only
                    // after that layout pass, so ListView cannot repeatedly
                    // recreate a tall offscreen row as it shrinks into place.
                    property real settledHeight: aiChatView.measuredHeights[index] || 60
                    property int measurementEpoch: -1
                    height: settledHeight
                    clip: true
                    function rememberHeight() {
                        if (measurementEpoch === aiChatView.measurementEpoch && index >= 0 && implicitHeight > 0)
                            aiChatView.measuredHeights[index] = implicitHeight
                    }
                    onImplicitHeightChanged: messageSizeTimer.restart()
                    Component.onCompleted: {
                        measurementEpoch = aiChatView.measurementEpoch
                        messageSizeTimer.restart()
                    }
                    Component.onDestruction: rememberHeight()
                    Timer {
                        id: messageSizeTimer
                        interval: 16
                        repeat: false
                        onTriggered: {
                            messageDelegate.rememberHeight()
                            messageDelegate.settledHeight = messageDelegate.implicitHeight
                        }
                    }
                    implicitHeight: isUser
                    ? userBubble.height + (showUserActions ? 20 : 0)
                    : assistantBlock.height

                    HoverHandler { id: messageHover }

                    // ---- 用户消息：靠右浅灰气泡（附件在气泡里） ----
                    Rectangle {
                        id: userBubble
                        visible: messageDelegate.isUser
                        anchors.right: parent.right
                        anchors.rightMargin: messageDelegate.sideGap
                        anchors.top: parent.top
                        width: Math.min(messageDelegate.maxBubbleWidth,
                                        Math.max(messageDelegate.files.length > 0 ? 178 : 52,
                                                 userMetrics.width + 26))
                        height: userColumn.height + 20
                        radius: 12
                        color: Ui.color("surface1")

                        TextMetrics {
                            id: userMetrics
                            font: userBody.font
                            text: messageDelegate.body.length > 0 ? messageDelegate.body : " "
                        }

                        Column {
                            id: userColumn
                            anchors.left: parent.left
                            anchors.right: parent.right
                            anchors.top: parent.top
                            anchors.margins: 10
                            spacing: 6

                            // 图片附件：气泡里直接看到缩略图，点开原图。
                            Row {
                                id: userThumbs
                                width: parent.width
                                height: visible ? 66 : 0
                                spacing: 6
                                visible: messageDelegate.imageFiles.length > 0

                                Repeater {
                                    model: messageDelegate.imageFiles
                                    delegate: Rectangle {
                                        width: 88
                                        height: 66
                                        radius: 8
                                        color: Ui.color("surface2")
                                        border.width: 1
                                        border.color: thumbMouse.containsMouse
                                                      ? panel.accent : panel.cardBorder
                                        Image {
                                            anchors.fill: parent
                                            anchors.margins: 2
                                            source: modelData.preview || ""
                                            sourceSize.width: 176
                                            fillMode: Image.PreserveAspectCrop
                                            asynchronous: true
                                            clip: true
                                            visible: status === Image.Ready
                                        }
                                        // 图被缓存清理掉时不留一片空白，退化成文件名。
                                        Text {
                                            anchors.centerIn: parent
                                            width: parent.width - 10
                                            visible: !modelData.preview
                                            text: modelData.name
                                            color: panel.textFaint
                                            font.pixelSize: 10
                                            elide: Text.ElideMiddle
                                            horizontalAlignment: Text.AlignHCenter
                                        }
                                        MouseArea {
                                            id: thumbMouse
                                            anchors.fill: parent
                                            hoverEnabled: true
                                            cursorShape: Qt.PointingHandCursor
                                            onClicked: panel.openPreview(modelData.preview || modelData.path || "")
                                        }
                                    }
                                }
                            }

                            Repeater {
                                model: messageDelegate.sheetFiles
                                delegate: Rectangle {
                                    width: userColumn.width
                                    height: 24
                                    radius: 6
                                    color: Ui.color("surface2")
                                    Row {
                                        anchors.fill: parent
                                        anchors.leftMargin: 8
                                        anchors.rightMargin: 8
                                        spacing: 5
                                        ToolIcon {
                                            anchors.verticalCenter: parent.verticalCenter
                                            width: 12
                                            height: 12
                                            iconId: "sheet"
                                            strokeColor: panel.textMuted
                                            lineWidth: 1
                                        }
                                        Text {
                                            anchors.verticalCenter: parent.verticalCenter
                                            width: parent.width - 17
                                            text: modelData.name
                                            color: panel.textMuted
                                            font.pixelSize: 11
                                            elide: Text.ElideMiddle
                                        }
                                    }
                                }
                            }

                            TextEdit {
                                id: userBody
                                width: parent.width
                                visible: messageDelegate.body.length > 0
                                text: messageDelegate.body
                                color: panel.textMain
                                font.pixelSize: 13
                                wrapMode: TextEdit.Wrap
                                textFormat: TextEdit.PlainText
                                readOnly: true
                                selectByMouse: true
                                selectByKeyboard: true
                            }
                        }
                    }

                    // 用户消息的操作行：改完重发，不用重新打一遍。
                    Row {
                        id: userActions
                        x: messageDelegate.width - messageDelegate.sideGap - width
                        y: userBubble.height + 4
                        height: 16
                        spacing: 14
                        visible: messageDelegate.showUserActions
                        opacity: (messageHover.hovered || messageDelegate.isLast) ? 1 : 0
                        enabled: opacity > 0
                        ActionLink {
                            label: "编辑并重发"
                            onClicked: panel.beginEdit(index, messageDelegate.body)
                        }
                        ActionLink {
                            label: userActions.copied ? "已复制" : "复制"
                            property bool copied: false
                            onClicked: {
                                controller.aiCopyMessage(messageDelegate.body)
                                userActions.copied = true
                                userCopyReset.restart()
                            }
                        }
                    }
                    Timer {
                        id: userCopyReset
                        interval: 1600
                        onTriggered: userActions.copied = false
                    }

                    // ---- 助手消息：靠左，日芒标记 + Markdown 正文 ----
                    Item {
                        id: assistantBlock
                        visible: !messageDelegate.isUser
                        anchors.left: parent.left
                        anchors.right: parent.right
                        anchors.leftMargin: messageDelegate.sideGap
                        anchors.rightMargin: messageDelegate.sideGap + 6
                        anchors.top: parent.top

                        readonly property bool waiting: model.streaming && messageDelegate.body.length === 0
                        readonly property real bodyHeight: waiting
                            ? 18
                            : Math.max(assistantMark.height, assistantViewport.height)
                        // 操作行的位置固定留出来，避免鼠标悬浮时消息高度跳变（列表会跟着抖）。
                        readonly property bool showActions: !model.streaming && messageDelegate.body.length > 0
                        height: bodyHeight + (showActions ? 24 : 0)

                        AiSpinner {
                            id: assistantMark
                            anchors.left: parent.left
                            anchors.top: parent.top
                            anchors.topMargin: 2
                            width: 16
                            height: 16
                            running: model.streaming
                            rayColor: panel.markColor
                        }

                        Text {
                            id: statusLabel
                            objectName: "aiStatusLabel"
                            anchors.left: assistantMark.right
                            anchors.leftMargin: 10
                            anchors.verticalCenter: assistantMark.verticalCenter
                            visible: assistantBlock.waiting
                            text: Ui.text(panel.statusPhrases[panel.statusIndex % panel.statusPhrases.length])
                            color: panel.textMuted
                            font.pixelSize: 12
                        }

                        AiResponseBody {
                            id: assistantViewport
                            objectName: "aiResponseViewport"
                            x: assistantMark.width + 10
                            width: Math.max(40, assistantBlock.width - assistantMark.width - 10)
                            visible: !assistantBlock.waiting
                            blocks: model.blocks || []
                            fallbackHtml: model.html || ""
                            streaming: model.streaming
                        }

                        Row {
                            id: assistantActions
                            property bool copied: false
                            x: assistantMark.width + 10
                            y: assistantBlock.bodyHeight + 4
                            height: 16
                            spacing: 14
                            visible: assistantBlock.showActions
                            // 悬浮才显形，最后一条常驻；高度已预留，不引起重排。
                            opacity: (messageHover.hovered || messageDelegate.isLast) ? 1 : 0
                            enabled: opacity > 0

                            ActionLink {
                                label: assistantActions.copied ? "已复制" : "复制"
                                onClicked: {
                                    controller.aiCopyMessage(messageDelegate.body)
                                    assistantActions.copied = true
                                    copyResetTimer.restart()
                                }
                            }
                            ActionLink {
                                visible: messageDelegate.isLast
                                label: "重新生成"
                                onClicked: controller.aiRegenerate()
                            }
                        }
                    }

                    Timer {
                        id: copyResetTimer
                        interval: 1600
                        onTriggered: assistantActions.copied = false
                    }
                }
            }

            // 上滑看历史时出现；点一下回到最新一条。
            Rectangle {
                id: scrollToBottom
                objectName: "aiScrollToBottom"
                anchors.right: parent.right
                anchors.rightMargin: 14
                anchors.bottom: parent.bottom
                anchors.bottomMargin: 12
                width: 30
                height: 30
                radius: 15
                visible: aiChatView.count > 0 && !aiChatView.followTail
                color: Ui.color("surface")
                border.width: 1
                border.color: panel.cardBorder
                ToolIcon {
                    anchors.centerIn: parent
                    width: 14
                    height: 14
                    iconId: "arrow_down"
                    strokeColor: scrollMouse.containsMouse ? panel.accent : panel.textMuted
                    lineWidth: 1.4
                }
                MouseArea {
                    id: scrollMouse
                    anchors.fill: parent
                    hoverEnabled: true
                    cursorShape: Qt.PointingHandCursor
                    onClicked: {
                        aiChatView.followTail = true
                        aiChatView.positionViewAtEnd()
                    }
                }
            }
        }

        Rectangle { Layout.fillWidth: true; Layout.preferredHeight: 1; color: Ui.color("divider") }

        // ---------- 待发附件 ----------
        // 图片给缩略图、表格给小胶囊：两类附件一眼能分清，也方便点开原图。
        // 两种形态写在同一个代理里用 visible 切换，而不是 Loader + Component：
        // 代理直接写在 Repeater 下才一定拿得到 model.xxx 这些角色。
        Flow {
            objectName: "aiPendingAttachments"
            Layout.fillWidth: true
            Layout.margins: 10
            Layout.bottomMargin: 0
            spacing: 6
            visible: aiAttachmentRepeater.count > 0
            Repeater {
                id: aiAttachmentRepeater
                model: controller.aiAttachmentModel
                delegate: Rectangle {
                    id: pendingChip
                    objectName: "aiAttachmentChip"
                    readonly property bool isImage: model.kind === "image"
                    // 表格胶囊右侧留出 24px 给悬停才出现的删除按钮，否则删除会压住文件名。
                    width: isImage ? 96 : sheetRow.implicitWidth + 32
                    height: isImage ? 72 : 28
                    radius: isImage ? 9 : 7
                    color: isImage ? Ui.color("surface2") : Ui.color("selection")
                    border.width: isImage ? 1 : 0
                    border.color: chipMouse.containsMouse ? panel.accent : panel.cardBorder

                    Image {
                        id: chipThumb
                        anchors.fill: parent
                        anchors.margins: 3
                        visible: pendingChip.isImage
                        source: model.preview || ""
                        sourceSize.width: 192
                        fillMode: Image.PreserveAspectCrop
                        asynchronous: true
                        clip: true
                    }
                    // 缓存被清掉时不留一片空白，退化成文件名。
                    Text {
                        anchors.centerIn: parent
                        width: parent.width - 12
                        visible: pendingChip.isImage && chipThumb.status !== Image.Ready
                        text: model.name
                        color: panel.textFaint
                        font.pixelSize: 10
                        elide: Text.ElideMiddle
                        horizontalAlignment: Text.AlignHCenter
                    }
                    RowLayout {
                        id: sheetRow
                        anchors.left: parent.left
                        anchors.leftMargin: 8
                        anchors.verticalCenter: parent.verticalCenter
                        visible: !pendingChip.isImage
                        spacing: 6
                        Text {
                            text: model.name + "（" + Ui.text(model.summary) + "）"
                            color: panel.accent
                            font.pixelSize: 11
                            Layout.maximumWidth: 210
                            elide: Text.ElideMiddle
                        }
                    }
                    MouseArea {
                        id: chipMouse
                        objectName: "aiAttachmentChipArea"
                        anchors.fill: parent
                        hoverEnabled: true
                        cursorShape: Qt.PointingHandCursor
                        onClicked: if (pendingChip.isImage) panel.openPreview(model.preview || "")
                    }
                    // 移除按钮悬停才显形，平时不压住缩略图。
                    // 这段必须写在铺满整块的 chipMouse **之后**：命中测试按声明顺序
                    // （不是 z）从后往前找，反过来的话点击会被 chipMouse 吃掉——
                    // 图片会变成「打开预览」、表格则毫无反应，× 形同虚设。
                    Rectangle {
                        z: 2
                        visible: chipMouse.containsMouse
                        anchors.right: parent.right
                        anchors.top: parent.top
                        anchors.margins: 3
                        width: 18
                        height: 18
                        radius: 9
                        color: Ui.color("surface")
                        border.width: 1
                        border.color: panel.cardBorder
                        Text {
                            anchors.centerIn: parent
                            text: "×"
                            color: pendingChip.isImage ? panel.textMuted : panel.accent
                            font.pixelSize: 12
                        }
                        MouseArea {
                            objectName: "aiAttachmentRemove"
                            anchors.fill: parent
                            cursorShape: Qt.PointingHandCursor
                            onClicked: controller.aiRemoveAttachment(index)
                        }
                    }
                }
            }
        }

        // 待发里有图、而当前模型读不了图：提前说一句，别等请求打回来才报错。
        Rectangle {
            objectName: "aiVisionHint"
            Layout.fillWidth: true
            Layout.leftMargin: 10
            Layout.rightMargin: 10
            Layout.topMargin: 6
            Layout.preferredHeight: visionHintRow.implicitHeight + 12
            visible: controller.aiHasPendingImage && controller.aiVisionHint.length > 0
            radius: 9
            color: Ui.color("surface19")
            border.width: 1
            border.color: Ui.color("warning6")

            RowLayout {
                id: visionHintRow
                anchors.fill: parent
                anchors.margins: 6
                spacing: 6
                ToolIcon {
                    Layout.alignment: Qt.AlignVCenter
                    width: 14
                    height: 14
                    iconId: "image"
                    strokeColor: Ui.color("warning3")
                    lineWidth: 1.2
                }
                Text {
                    Layout.fillWidth: true
                    text: Ui.text(controller.aiVisionHint)
                    color: Ui.color("warning3")
                    font.pixelSize: 11
                    wrapMode: Text.Wrap
                }
                ActionLink {
                    Layout.alignment: Qt.AlignVCenter
                    label: "换模型"
                    onClicked: modelPopup.opened ? modelPopup.close() : modelPopup.open()
                }
            }
        }

        // ---------- 底部输入卡片 ----------
        Rectangle {
            id: composerCard
            Layout.fillWidth: true
            Layout.leftMargin: 10
            Layout.rightMargin: 10
            Layout.topMargin: 6
            Layout.bottomMargin: 2
            Layout.preferredHeight: composerColumn.implicitHeight + 18
            radius: 14
            // 抽屉卡片本身就是 surface（白），输入卡片改用 input 的略暗调，
            // 亮色下是浅灰、暗色下更暗，都能和卡片区分开。
            color: Ui.color("input")
            border.width: 1
            border.color: inputArea.activeFocus ? panel.accent : panel.cardBorder

            Column {
                id: composerColumn
                anchors.left: parent.left
                anchors.right: parent.right
                anchors.top: parent.top
                anchors.margins: 9
                spacing: 6

                ScrollView {
                    id: inputScroll
                    objectName: "aiInputScroll"
                    width: parent.width
                    height: Math.min(inputArea.implicitHeight + 6, 108)
                    clip: true
                    ScrollBar.vertical.policy: (inputArea.implicitHeight + 6 > 108) ? ScrollBar.AsNeeded : ScrollBar.AlwaysOff
                    // 输入框不要两端回弹。ScrollView 内部那个 Flickable 默认是
                    // DragAndOvershootBounds，滚到顶/底会橡皮筋一下；TextArea 自己不持有
                    // boundsBehavior，ScrollView 也没把它代理出来，所以只能拿 contentItem
                    // 这个内部 Flickable 赋值（它也是只读属性，写不成绑定）。
                    Component.onCompleted: contentItem.boundsBehavior = Flickable.StopAtBounds

                    TextArea {
                        id: inputArea
                        objectName: "aiInputArea"
                        wrapMode: TextEdit.Wrap
                        placeholderText: Ui.text("今天帮你做些什么？")
                        placeholderTextColor: panel.textFaint
                        color: panel.textMain
                        font.pixelSize: 13
                        selectByMouse: true
                        leftPadding: 0
                        rightPadding: 0
                        topPadding: 2
                        bottomPadding: 2
                        background: Rectangle { color: "transparent" }
                        onTextChanged: if (activeFocus && panel.editingRow < 0) draftTimer.restart()

                        // 剪贴板里是图就先粘图；不是图就放行，让 TextArea 粘文字。
                        Keys.onPressed: function(event) {
                            var pasteKey = (event.key === Qt.Key_V)
                            var withModifier = (event.modifiers & Qt.ControlModifier)
                                || (event.modifiers & Qt.MetaModifier)
                            if (pasteKey && withModifier && controller.aiClipboardHasImage()) {
                                event.accepted = true
                                controller.aiPasteImage()
                            }
                        }
                        Keys.onReturnPressed: function(event) {
                            if (event.modifiers & Qt.ShiftModifier) {
                                event.accepted = false
                                return
                            }
                            event.accepted = true
                            panel.submitInput()
                        }
                        Keys.onEnterPressed: function(event) {
                            if (event.modifiers & Qt.ShiftModifier) {
                                event.accepted = false
                                return
                            }
                            event.accepted = true
                            panel.submitInput()
                        }
                        // Esc：编辑态先退出编辑，否则停止生成。
                        Keys.onEscapePressed: function(event) {
                            event.accepted = true
                            if (panel.editingRow >= 0) panel.cancelEdit()
                            else if (controller.aiBusy) controller.aiStopGenerating()
                        }
                    }
                }

                Item {
                    id: composerTools
                    width: parent.width
                    height: 34

                    // 左：附加表格
                    Rectangle {
                        id: attachButton
                        anchors.left: parent.left
                        anchors.verticalCenter: parent.verticalCenter
                        width: 34
                        height: 34
                        radius: 9
                        color: attachMouse.containsMouse ? Ui.color("hover") : "transparent"
                        enabled: !controller.aiBusy
                        opacity: enabled ? 1.0 : 0.45
                        ToolIcon {
                            anchors.centerIn: parent
                            width: 17
                            height: 17
                            iconId: "plus"
                            strokeColor: attachMouse.containsMouse ? panel.accent : panel.textMuted
                            lineWidth: 1.4
                        }
                        MouseArea {
                            id: attachMouse
                            anchors.fill: parent
                            hoverEnabled: true
                            cursorShape: Qt.PointingHandCursor
                            onClicked: controller.aiChooseAttachments()
                        }
                        AppToolTip { text: Ui.text("附加表格或图片（也可以直接粘贴、拖入）"); visible: attachMouse.containsMouse }
                    }

                    // 左：新对话
                    Rectangle {
                        id: newChatButton
                        anchors.left: attachButton.right
                        anchors.leftMargin: 4
                        anchors.verticalCenter: parent.verticalCenter
                        width: 34
                        height: 34
                        radius: 9
                        color: newChatMouse.containsMouse ? Ui.color("hover") : "transparent"
                        enabled: !controller.aiBusy
                        opacity: enabled ? 1.0 : 0.45
                        ToolIcon {
                            anchors.centerIn: parent
                            width: 16
                            height: 16
                            iconId: "new_chat"
                            strokeColor: newChatMouse.containsMouse ? panel.accent : panel.textMuted
                            lineWidth: 1.3
                        }
                        MouseArea {
                            id: newChatMouse
                            anchors.fill: parent
                            hoverEnabled: true
                            cursorShape: Qt.PointingHandCursor
                            onClicked: { panel.saveDraftNow(); controller.aiNewConversation() }
                        }
                        AppToolTip { text: Ui.text("开始新对话（当前对话会存入历史）"); visible: newChatMouse.containsMouse }
                    }

                    // 中：当前模型，点开切换
                    Item {
                        id: modelChip
                        objectName: "aiModelChip"
                        anchors.left: newChatButton.right
                        anchors.leftMargin: 6
                        anchors.right: sendButton.left
                        anchors.rightMargin: 8
                        anchors.verticalCenter: parent.verticalCenter
                        height: 24
                        clip: true
                        Row {
                            anchors.verticalCenter: parent.verticalCenter
                            spacing: 3
                            Text {
                                anchors.verticalCenter: parent.verticalCenter
                                width: Math.min(implicitWidth, modelChip.width - 10)
                                text: Ui.text(controller.aiReady ? controller.aiActiveModel : "未配置")
                                color: modelChipMouse.containsMouse ? panel.accent : panel.textFaint
                                font.pixelSize: 10
                                elide: Text.ElideMiddle
                            }
                            ToolIcon {
                                anchors.verticalCenter: parent.verticalCenter
                                width: 9
                                height: 9
                                iconId: "chevron_down"
                                strokeColor: modelChipMouse.containsMouse ? panel.accent : panel.textFaint
                                lineWidth: 1.1
                            }
                        }
                        MouseArea {
                            id: modelChipMouse
                            anchors.fill: parent
                            hoverEnabled: true
                            cursorShape: Qt.PointingHandCursor
                            onClicked: modelPopup.opened ? modelPopup.close() : modelPopup.open()
                        }
                    }

                    // 右：发送 / 停止
                    Rectangle {
                        id: sendButton
                        anchors.right: parent.right
                        anchors.verticalCenter: parent.verticalCenter
                        width: 34
                        height: 34
                        radius: 9
                        readonly property bool ready: inputArea.text.trim().length > 0 || aiAttachmentRepeater.count > 0
                        color: controller.aiBusy
                               ? panel.accent
                               : (sendMouse.containsMouse && ready ? Ui.color("hover") : "transparent")
                        border.width: 1
                        border.color: controller.aiBusy
                                      ? panel.accent
                                      : (ready ? panel.accent : panel.cardBorder)
                        ToolIcon {
                            anchors.centerIn: parent
                            width: 16
                            height: 16
                            visible: !controller.aiBusy
                            iconId: "arrow_up"
                            strokeColor: sendButton.ready ? panel.accent : panel.textFaint
                            lineWidth: 1.5
                        }
                        Rectangle {
                            anchors.centerIn: parent
                            visible: controller.aiBusy
                            width: 9
                            height: 9
                            radius: 2
                            color: Ui.color("onAccent")
                        }
                        MouseArea {
                            id: sendMouse
                            anchors.fill: parent
                            hoverEnabled: true
                            cursorShape: (sendButton.ready || controller.aiBusy) ? Qt.PointingHandCursor : Qt.ArrowCursor
                            onClicked: {
                                if (controller.aiBusy) controller.aiStopGenerating()
                                else panel.submitInput()
                            }
                        }
                    }
                }
            }
        }

        Text {
            Layout.fillWidth: true
            Layout.leftMargin: 12
            Layout.rightMargin: 12
            Layout.bottomMargin: 8
            text: Ui.text("Enter 发送 · Shift+Enter 换行 · Ctrl+K 开关助手")
            color: panel.textFaint
            font.pixelSize: 9
            horizontalAlignment: Text.AlignHCenter
            elide: Text.ElideRight
        }
    }

    // ---------- 拖入即附加 ----------
    // 放在内容之上（z 最高），和主界面 FileDropTarget 同一套做法：
    // DropArea 不吃鼠标事件，所以按钮照常可点。
    DropArea {
        id: aiDropArea
        objectName: "aiDropArea"
        anchors.fill: parent
        z: 3
        onEntered: function(drag) {
            // 只接受带文件路径的拖拽；纯文本交回给输入框自己处理。
            panel.dropActive = drag.hasUrls === true
            drag.accepted = panel.dropActive
        }
        onExited: panel.dropActive = false
        onDropped: function(drop) {
            panel.dropActive = false
            if (!drop.hasUrls) return
            // 走和主界面同一条解析链：text/uri-list 与 Windows 的
            // 「松手后才给出路径」都能兜住。
            var uri = drop.formats.indexOf("text/uri-list") >= 0
                    ? drop.getDataAsString("text/uri-list") : ""
            var urls = controller.resolveDropUrls(drop.urls, uri,
                                                  drop.hasText ? drop.text : "")
            controller.aiAttachPaths(urls)
            drop.accept(Qt.CopyAction)
        }

        Rectangle {
            anchors.fill: parent
            anchors.margins: 6
            radius: 12
            visible: panel.dropActive
            color: Ui.color("surface9")
            border.width: 2
            border.color: panel.accent
            Text {
                anchors.centerIn: parent
                width: parent.width - 24
                text: Ui.text("松手即可附加：表格直接解析，图片先压缩再读")
                color: panel.accent
                font.pixelSize: 12
                font.bold: true
                wrapMode: Text.Wrap
                horizontalAlignment: Text.AlignHCenter
            }
        }
    }

    // ---------- 图片放大预览 ----------
    Popup {
        id: imagePreviewPopup
        objectName: "aiImagePreviewPopup"
        parent: panel
        // 用显式 x/y 居中，和本文件其它弹层一致：Popup 不是 Item，不靠 anchors。
        x: Math.max(0, (panel.width - width) / 2)
        y: Math.max(0, (panel.height - height) / 2)
        width: Math.min(panel.width - 24, 560)
        height: Math.min(panel.height - 80, 460)
        padding: 0
        modal: true
        focus: true
        closePolicy: Popup.CloseOnEscape | Popup.CloseOnPressOutside
        onClosed: panel.previewImage = ""
        background: Rectangle {
            radius: 12
            color: Ui.color("surface")
            border.width: 1
            border.color: panel.cardBorder
        }
        contentItem: Column {
            spacing: 0
            width: imagePreviewPopup.width

            Item {
                width: parent.width
                height: 36
                Text {
                    anchors.left: parent.left
                    anchors.leftMargin: 12
                    anchors.verticalCenter: parent.verticalCenter
                    text: Ui.text("图片预览")
                    color: panel.textMuted
                    font.pixelSize: 11
                }
                Row {
                    anchors.right: parent.right
                    anchors.rightMargin: 12
                    anchors.verticalCenter: parent.verticalCenter
                    spacing: 14
                    ActionLink {
                        label: "用系统程序打开"
                        onClicked: controller.aiOpenImage(panel.previewImage)
                    }
                    ActionLink {
                        label: "关闭"
                        onClicked: imagePreviewPopup.close()
                    }
                }
            }
            Rectangle { width: parent.width; height: 1; color: Ui.color("divider") }

            Item {
                id: previewStage
                width: parent.width
                height: imagePreviewPopup.height - 37
                clip: true
                Image {
                    id: previewPicture
                    anchors.fill: parent
                    anchors.margins: 10
                    source: panel.previewImage
                    fillMode: Image.PreserveAspectFit
                    asynchronous: true
                    visible: status === Image.Ready
                }
                Text {
                    anchors.centerIn: parent
                    visible: previewPicture.status !== Image.Ready
                    text: Ui.text("图片已不在本地缓存中，无法预览")
                    color: panel.textFaint
                    font.pixelSize: 11
                }
                MouseArea {
                    anchors.fill: parent
                    onClicked: imagePreviewPopup.close()
                }
            }
        }
    }

    // ---------- 历史对话 ----------
    Popup {
        id: historyPopup
        objectName: "aiHistoryPopup"
        // 挂在面板上而不是按钮上：面板右侧那一排图标最右会挤出面板外，
        // 以按钮为锚点弹层会跑到抽屉左边去。
        parent: panel
        x: panel.width - width - 8
        y: 48
        width: Math.min(288, panel.width - 20)
        height: Math.min(340, historyColumn.implicitHeight + 8)
        padding: 0
        modal: false
        focus: true
        closePolicy: Popup.CloseOnEscape | Popup.CloseOnPressOutside
        background: Rectangle {
            radius: 12
            color: Ui.color("surface")
            border.width: 1
            border.color: panel.cardBorder
        }
        contentItem: Column {
            id: historyColumn
            spacing: 0
            width: historyPopup.width

            Item {
                width: parent.width
                height: 34
                Text {
                    x: 12
                    width: parent.width - 12
                    anchors.verticalCenter: parent.verticalCenter
                    text: Ui.text("历史对话")
                    color: panel.textFaint
                    font.pixelSize: 11
                    elide: Text.ElideRight
                }
                ActionLink {
                    anchors.right: parent.right
                    anchors.rightMargin: 12
                    anchors.verticalCenter: parent.verticalCenter
                    label: "新对话"
                    onClicked: {
                        panel.saveDraftNow()
                        controller.aiNewConversation()
                        historyPopup.close()
                    }
                }
            }

            // 搜索：标题和正文都能命中，对话多了才翻得动。
            AppTextField {
                id: historySearch
                width: parent.width - 16
                x: 8
                implicitHeight: 30
                font.pixelSize: 12
                placeholderText: Ui.text("搜索对话…")
                onTextChanged: historySearchTimer.restart()
            }
            Item { width: parent.width; height: 8 }
            Rectangle { width: parent.width; height: 1; color: Ui.color("divider") }

            Timer {
                id: historySearchTimer
                interval: 220
                repeat: false
                onTriggered: controller.aiSearchHistory(historySearch.text)
            }

            ListView {
                id: historyList
                width: parent.width
                height: Math.min(288, contentHeight)
                model: controller.aiConversationModel
                clip: true
                boundsBehavior: Flickable.StopAtBounds
                ScrollBar.vertical: ScrollBar { policy: ScrollBar.AsNeeded }
                // 正在改名的那条；空串表示没有。
                property string renamingId: ""
                delegate: Rectangle {
                    id: historyRow
                    width: historyList.width
                    height: 52
                    readonly property bool renaming: historyList.renamingId === String(model.id)
                    color: historyMouse.containsMouse ? Ui.color("hover") : "transparent"
                    Rectangle {
                        anchors.bottom: parent.bottom
                        width: parent.width
                        height: 1
                        color: Ui.color("divider")
                    }
                    MouseArea {
                        id: historyMouse
                        anchors.fill: parent
                        hoverEnabled: true
                        cursorShape: Qt.PointingHandCursor
                        // 改名时让点击落在输入框上，别顺手把对话切走。
                        enabled: !historyRow.renaming
                        onClicked: {
                            panel.saveDraftNow()
                            controller.aiOpenConversation(model.id)
                            historyPopup.close()
                        }
                    }
                    Column {
                        // 右边留出 76px 给悬停才出现的「改名 / 删除」，否则会压住标题。
                        anchors.left: parent.left
                        anchors.right: parent.right
                        anchors.verticalCenter: parent.verticalCenter
                        anchors.leftMargin: 12
                        anchors.rightMargin: 76
                        spacing: 2
                        // 标题与改名输入框二选一：原地改，不开对话框。
                        AppTextField {
                            id: renameField
                            width: parent.width
                            implicitHeight: 26
                            visible: historyRow.renaming
                            font.pixelSize: 12
                            placeholderText: Ui.text("对话名称")
                            onAccepted: commitRename()
                            Keys.onEscapePressed: function(event) {
                                event.accepted = true
                                historyList.renamingId = ""
                            }
                            // 失焦即取消：点别处不该意外改名。
                            onActiveFocusChanged: if (!activeFocus && historyRow.renaming)
                                                      historyList.renamingId = ""
                            function commitRename() {
                                var value = renameField.text.trim()
                                if (value.length > 0)
                                    controller.aiRenameConversation(String(model.id), value)
                                historyList.renamingId = ""
                            }
                        }
                        Text {
                            width: parent.width
                            visible: !historyRow.renaming
                            text: model.title === "新对话" ? Ui.text("新对话") : model.title
                            color: model.active ? panel.accent : panel.textMain
                            font.pixelSize: 12
                            font.weight: model.active ? Font.DemiBold : Font.Normal
                            elide: Text.ElideRight
                        }
                        Text {
                            width: parent.width
                            text: Ui.text(model.updated)
                            color: panel.textFaint
                            font.pixelSize: 10
                            elide: Text.ElideRight
                        }
                    }
                    // 放在 MouseArea 之后，压在它上面，否则链接点不动。
                    Row {
                        anchors.right: parent.right
                        anchors.rightMargin: 10
                        anchors.verticalCenter: parent.verticalCenter
                        spacing: 10
                        ActionLink {
                            label: "改名"
                            visible: historyMouse.containsMouse && !historyRow.renaming
                            onClicked: {
                                historyList.renamingId = String(model.id)
                                renameField.text = String(model.title)
                                renameField.forceActiveFocus()
                                renameField.selectAll()
                            }
                        }
                        ActionLink {
                            label: "删除"
                            visible: historyMouse.containsMouse
                            onClicked: controller.aiDeleteConversation(model.id)
                        }
                    }
                }
            }

            // 搜不到时给一句，避免看起来像坏了。
            Item {
                width: parent.width
                height: 34
                visible: historyList.count === 0 && historySearch.text.length > 0
                Text {
                    anchors.centerIn: parent
                    text: Ui.text("没有匹配的对话")
                    color: panel.textFaint
                    font.pixelSize: 11
                }
            }
        }
        // 关掉就恢复全部，下次打开不会只剩上次的搜索结果。
        onClosed: {
            historySearch.text = ""
            historyList.renamingId = ""
            controller.aiSearchHistory("")
        }
    }

    // ---------- 模型切换 ----------
    Popup {
        id: modelPopup
        objectName: "aiModelPopup"
        parent: modelChip
        x: 0
        y: -height - 6
        width: Math.min(panel.width - 40, 224)
        height: modelColumn.implicitHeight
        padding: 0
        modal: false
        focus: true
        closePolicy: Popup.CloseOnEscape | Popup.CloseOnPressOutside
        // 用户在浮层里内联添加模型；关闭时一定要复位，否则下次打开还停在输入态。
        property bool adding: false
        function commitNewModel() {
            var name = newModelField.text.trim()
            if (!name) { adding = false; return }
            if (!controller.aiAddModel(name)) {
                // 失败（重名/非法）时留在输入态，让用户改，别把内容吞掉。
                newModelField.forceActiveFocus()
                return
            }
            adding = false
            close()
        }
        function cancelNewModel() {
            adding = false
            newModelField.text = ""
        }
        onClosed: cancelNewModel()
        background: Rectangle {
            radius: 12
            color: Ui.color("surface")
            border.width: 1
            border.color: panel.cardBorder
        }
        contentItem: Column {
            id: modelColumn
            // 必须写死宽度：Column 的隐式宽度来自子项，而子项又要 parent.width，
            // 两者相扣会形成绑定环（列表会一直重新 polish，界面直接卡死）。
            width: modelPopup.width
            spacing: 0
            topPadding: 6
            bottomPadding: 6

            // —— 服务商 ——：在这里就能切，不必再回设置里翻。
            Repeater {
                model: controller.aiProviderMenuOptions
                delegate: Rectangle {
                    objectName: "aiProviderRow"
                    width: modelColumn.width
                    height: 30
                    radius: 8
                    color: providerRowMouse.containsMouse ? Ui.color("hover") : "transparent"
                    Text {
                        anchors.left: parent.left
                        anchors.leftMargin: 12
                        anchors.right: parent.right
                        anchors.rightMargin: 26
                        anchors.verticalCenter: parent.verticalCenter
                        text: Ui.text(modelData.label)
                        color: modelData.selected ? panel.accent : panel.textMain
                        font.pixelSize: 12
                        elide: Text.ElideRight
                    }
                    ToolIcon {
                        anchors.right: parent.right
                        anchors.rightMargin: 10
                        anchors.verticalCenter: parent.verticalCenter
                        width: 12
                        height: 12
                        visible: modelData.selected
                        iconId: "check"
                        strokeColor: panel.accent
                        lineWidth: 1.5
                    }
                    MouseArea {
                        id: providerRowMouse
                        objectName: "aiProviderRowArea"
                        anchors.fill: parent
                        hoverEnabled: true
                        cursorShape: Qt.PointingHandCursor
                        // 切完不关浮层：下面那串模型要换成新这家的，让用户接着挑。
                        onClicked: controller.aiSelectProvider(modelData.value)
                    }
                }
            }
            Rectangle { width: modelColumn.width; height: 1; color: Ui.color("divider") }
            Text {
                width: modelColumn.width
                height: 22
                leftPadding: 12
                text: Ui.text("模型")
                color: panel.textMuted
                font.pixelSize: 10
                verticalAlignment: Text.AlignVCenter
            }
            // 模型多了要能滚：高度写死上限（8 行足够放下四家的预置清单），
            // 别把浮层撑到屏幕外；右侧细滚动条提示「下面还有」。
            ListView {
                id: modelList
                objectName: "aiModelList"
                width: modelColumn.width
                height: Math.min(contentHeight, 8 * 32)
                implicitHeight: height
                clip: true
                boundsBehavior: Flickable.StopAtBounds
                model: controller.aiModelOptions
                ScrollIndicator.vertical: ScrollIndicator { }
                delegate: Rectangle {
                    width: modelColumn.width
                    height: 32
                    radius: 8
                    color: modelRowMouse.containsMouse ? Ui.color("hover") : "transparent"
                    RowLayout {
                        anchors.fill: parent
                        anchors.leftMargin: 12
                        // 右侧留 26 给悬停才出现的移除按钮，否则会压住选中勾。
                        anchors.rightMargin: 26
                        spacing: 6
                        Text {
                            Layout.fillWidth: true
                            text: Ui.text(modelData.label)
                            color: modelData.selected ? panel.accent : panel.textMain
                            font.pixelSize: 12
                            elide: Text.ElideMiddle
                        }
                        // 能读图的模型挂个「看图」小标：不用去记模型名。
                        Rectangle {
                            Layout.alignment: Qt.AlignVCenter
                            visible: modelData.vision === true
                            width: visionTag.implicitWidth + 10
                            height: 15
                            radius: 5
                            color: Ui.color("selection")
                            Text {
                                id: visionTag
                                anchors.centerIn: parent
                                text: Ui.text("看图")
                                color: panel.accent
                                font.pixelSize: 9
                            }
                        }
                        ToolIcon {
                            Layout.alignment: Qt.AlignVCenter
                            width: 12
                            height: 12
                            visible: modelData.selected
                            iconId: "check"
                            strokeColor: panel.accent
                            lineWidth: 1.5
                        }
                    }
                    MouseArea {
                        id: modelRowMouse
                        objectName: "aiModelRow"
                        anchors.fill: parent
                        hoverEnabled: true
                        cursorShape: Qt.PointingHandCursor
                        onClicked: {
                            controller.aiSelectModel(modelData.value)
                            modelPopup.close()
                        }
                    }
                    // 必须排在铺满整行的 modelRowMouse 之后，否则点击会被它吃掉。
                    Item {
                        objectName: "aiModelRemove"
                        z: 2
                        visible: modelData.removable === true && modelRowMouse.containsMouse
                        anchors.right: parent.right
                        anchors.verticalCenter: parent.verticalCenter
                        anchors.rightMargin: 8
                        width: 18
                        height: 18
                        ToolIcon {
                            anchors.centerIn: parent
                            width: 11
                            height: 11
                            iconId: "close"
                            strokeColor: removeMouse.containsMouse ? Ui.color("error2") : panel.textFaint
                            lineWidth: 1.4
                        }
                        MouseArea {
                            id: removeMouse
                            objectName: "aiModelRemoveArea"
                            anchors.fill: parent
                            hoverEnabled: true
                            cursorShape: Qt.PointingHandCursor
                            onClicked: controller.aiRemoveModel(modelData.value)
                        }
                    }
                }
            }
            Rectangle { width: modelColumn.width; height: 1; color: Ui.color("divider") }
            // 自己加模型：回车提交、Esc 取消。加完立即切过去。
            Item {
                width: modelColumn.width
                height: modelPopup.adding ? 40 : 32
                AppTextField {
                    id: newModelField
                    objectName: "aiNewModelField"
                    anchors.left: parent.left
                    anchors.right: parent.right
                    anchors.verticalCenter: parent.verticalCenter
                    anchors.leftMargin: 10
                    anchors.rightMargin: 10
                    height: 28
                    font.pixelSize: 12
                    visible: modelPopup.adding
                    // 示例跟着当前服务商走，别拿 MiniMax 的模型名去提示 GLM 用户。
                    placeholderText: Ui.text("模型名称，例如 ") + controller.aiProviderDefaultModel
                    onAccepted: modelPopup.commitNewModel()
                    Keys.onEscapePressed: modelPopup.cancelNewModel()
                }
                Text {
                    anchors.left: parent.left
                    anchors.leftMargin: 12
                    anchors.right: parent.right
                    anchors.rightMargin: 10
                    anchors.verticalCenter: parent.verticalCenter
                    visible: !modelPopup.adding
                    text: Ui.text("添加模型…")
                    color: addModelMouse.containsMouse ? panel.accent : panel.textMain
                    font.pixelSize: 12
                    elide: Text.ElideRight
                }
                MouseArea {
                    id: addModelMouse
                    anchors.fill: parent
                    visible: !modelPopup.adding
                    hoverEnabled: true
                    cursorShape: Qt.PointingHandCursor
                    onClicked: {
                        modelPopup.adding = true
                        newModelField.text = ""
                        newModelField.forceActiveFocus()
                    }
                }
            }
            Rectangle { width: modelColumn.width; height: 1; color: Ui.color("divider") }
            // 这串模型名是从服务商预置来的，不是用户加的，所以要说清出处。
            Text {
                width: modelColumn.width - 24
                leftPadding: 12
                rightPadding: 12
                topPadding: 6
                bottomPadding: 2
                visible: controller.aiModelsNote.length > 0
                text: Ui.text(controller.aiModelsNote)
                color: panel.textFaint
                font.pixelSize: 9
                wrapMode: Text.Wrap
            }
            Item {
                width: modelColumn.width
                height: 34
                ActionLink {
                    anchors.centerIn: parent
                    label: "其他设置…"
                    onClicked: {
                        modelPopup.close()
                        panel.settingsRequested()
                    }
                }
            }
        }
    }

    // ---------- 小组件 ----------
    component IconAction: Item {
        id: iconAction
        property string iconId: ""
        property string tip: ""
        signal clicked()
        width: 26
        height: 26
        Layout.alignment: Qt.AlignVCenter
        opacity: enabled ? 1.0 : 0.4
        ToolIcon {
            anchors.centerIn: parent
            width: 15
            height: 15
            iconId: iconAction.iconId
            strokeColor: iconMouse.containsMouse ? panel.accent : panel.textMuted
            lineWidth: 1.3
        }
        MouseArea {
            id: iconMouse
            anchors.fill: parent
            hoverEnabled: true
            cursorShape: Qt.PointingHandCursor
            onClicked: iconAction.clicked()
        }
        AppToolTip { text: Ui.text(iconAction.tip); visible: iconMouse.containsMouse && iconAction.tip.length > 0 }
    }

    component ActionLink: Item {
        id: actionLink
        property string label: ""
        signal clicked()
        width: actionLabel.implicitWidth
        height: 16
        Text {
            id: actionLabel
            anchors.centerIn: parent
            text: Ui.text(actionLink.label)
            color: actionMouse.containsMouse ? panel.accent : panel.textFaint
            font.pixelSize: 11
        }
        MouseArea {
            id: actionMouse
            anchors.fill: parent
            hoverEnabled: true
            cursorShape: Qt.PointingHandCursor
            onClicked: actionLink.clicked()
        }
    }
}
