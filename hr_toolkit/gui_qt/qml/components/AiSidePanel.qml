import QtQuick 2.15
import QtQuick.Layouts 1.15

// Sage 停靠面板：和 WorkspaceSidePanel 同一套机制——作为主 RowLayout 的子项
// 「占住」一块宽度，中间内容区随之收窄，而不是被浮层盖住。
//
// 与浮层的区别（也是这次改版的原因）：
//   * 宽度由 reservedWidth 参与布局分配，宽度从视口向下传；
//   * 空间不够时自动收起（autoCollapsed），不会把中间内容挤没；
//   * 收起（collapsed）只留一条窄轨，点一下就能回来，和「关闭」是两件事。
//
// 版式沿用之前的「浮起卡片」：四周留 gutter，圆角与外发光画在间隙里。
FocusScope {
    id: panel

    objectName: "aiSidePanel"

    signal closeRequested()
    signal settingsRequested()
    signal detachRequested()
    signal collapseRequested()

    property bool requestedOpen: false
    // 收起：保留一条窄轨，中间内容立刻把宽度拿回去
    property bool collapsed: false
    // 目标可用宽度（由左侧栏的「目标」宽度推导）与实时宽度（动画中的实际值）。
    property real availableWidth: 0
    property real liveAvailableWidth: availableWidth

    // 中间内容区的最小宽度：低于它就自动收起，避免把正文挤没。
    readonly property real coreMinimumWidth: 640
    readonly property real minimumPanelWidth: 320
    readonly property real maximumPanelWidth: 400
    readonly property real gutter: 8
    readonly property real cardRadius: 12
    readonly property real railWidth: 46
    readonly property real collapseThreshold: coreMinimumWidth + minimumPanelWidth + gutter
    readonly property real restoreThreshold: collapseThreshold + 80
    property bool autoCollapsed: false

    readonly property bool opened: requestedOpen && !autoCollapsed
    readonly property real panelWidth: Math.max(minimumPanelWidth,
        Math.min(maximumPanelWidth, liveAvailableWidth * 0.30))
    // 收起的窄轨宽度 + gutter 就是这一列实际占的位置。
    readonly property real shownWidth: collapsed ? railWidth : panelWidth
    // reveal 是纯属性而不是绑定：它由 16ms 定时器从 0 推到 1，
    // Behavior 才有得可动（首次绑定赋值不会触发动画）。
    property real reveal: 0
    readonly property real reservedWidth: Math.max(0, Math.min(
        reveal * (shownWidth + gutter), liveAvailableWidth - coreMinimumWidth))
    readonly property real cardHeight: Math.max(0, height - gutter * 2)
    // 阴影整体下移 2px：上方光晕窄、下方宽，看起来才是「浮」起来。
    readonly property real haloDrop: 2
    readonly property real haloBase: Ui.dark ? 0.38 : 0.09

    readonly property color markColor: Ui.color("markRay")

    function close() { closeRequested() }
    function expand() { collapsed = false }
    function updateAvailability() {
        if (!autoCollapsed && availableWidth <= collapseThreshold) autoCollapsed = true
        else if (autoCollapsed && availableWidth >= restoreThreshold) autoCollapsed = false
    }
    onAvailableWidthChanged: updateAvailability()
    onOpenedChanged: {
        reveal = opened ? 1 : 0
        if (!opened) collapsed = false
    }
    Component.onCompleted: {
        updateAvailability()
        revealTimer.start()
    }

    // 等首次布局落定再拉起 reveal，打开时才有滑入动画。
    Timer {
        id: revealTimer
        interval: 16
        repeat: false
        onTriggered: panel.reveal = panel.opened ? 1 : 0
    }

    // 预留宽度挂在 Loader 上（它是布局子项），这里不再写 Layout.*，
    // 否则就是「父项不是布局却带布局附加值」的无效声明。
    clip: true
    enabled: reservedWidth > 0
    Keys.onEscapePressed: function(event) { close(); event.accepted = true }

    Behavior on reveal {
        NumberAnimation { duration: 190; easing.type: Easing.OutCubic }
    }

    // 外发光：6 层 1px 描边由内向外扩散，用普通 Rectangle 模拟（不用 QtGraphicalEffects，
    // Win7 的 Qt5 与 Qt6 要共用同一份 QML）。
    Item {
        id: cardChrome
        x: 0
        y: 0
        width: panel.width
        height: panel.height
        visible: panel.opened

        Repeater {
            model: 6
            delegate: Rectangle {
                readonly property int step: index + 1
                x: panel.gutter - step
                y: panel.gutter - step + panel.haloDrop
                width: panel.shownWidth + step * 2
                height: panel.cardHeight + step * 2
                radius: panel.cardRadius + step
                color: "transparent"
                border.width: 1
                border.color: Qt.rgba(0, 0, 0, panel.haloBase * Math.pow(0.78, index))
            }
        }

        Rectangle {
            objectName: "aiPanelSurface"
            x: panel.gutter
            y: panel.gutter
            width: panel.shownWidth
            height: panel.cardHeight
            radius: panel.cardRadius
            color: Ui.color("surface")
            border.width: 1
            border.color: Ui.color("border")
        }
    }

    // 展开态：对话面板始终按完整宽度布局，收起时靠裁剪隐藏，
    // 这样内部布局不会在 46px 宽下被压出告警。
    AiChatPanel {
        id: chatPanel
        x: panel.gutter
        y: panel.gutter
        width: panel.panelWidth
        height: panel.cardHeight
        visible: panel.opened && !panel.collapsed
        onCloseRequested: panel.closeRequested()
        onSettingsRequested: panel.settingsRequested()
        onDetachRequested: panel.detachRequested()
        onCollapseRequested: panel.collapseRequested()
    }

    // 收起态：一条窄轨，点任意位置回来。
    Rectangle {
        id: rail
        objectName: "aiPanelRail"
        x: panel.gutter
        y: panel.gutter
        width: panel.railWidth
        height: panel.cardHeight
        radius: panel.cardRadius
        color: "transparent"
        visible: panel.opened && panel.collapsed

        Column {
            anchors.horizontalCenter: parent.horizontalCenter
            anchors.top: parent.top
            anchors.topMargin: 14
            spacing: 10

            AiSpinner {
                anchors.horizontalCenter: parent.horizontalCenter
                width: 18
                height: 18
                running: false
                rayColor: panel.markColor
            }

            Rectangle {
                anchors.horizontalCenter: parent.horizontalCenter
                width: 26
                height: 26
                radius: 8
                color: railMouse.containsMouse ? Ui.color("hover") : "transparent"
                ToolIcon {
                    anchors.centerIn: parent
                    width: 13
                    height: 13
                    iconId: "chevron_left"
                    strokeColor: railMouse.containsMouse ? Ui.color("accent") : Ui.color("muted")
                    lineWidth: 1.4
                }
            }
        }

        MouseArea {
            id: railMouse
            anchors.fill: parent
            hoverEnabled: true
            cursorShape: Qt.PointingHandCursor
            onClicked: panel.expand()
        }
        AppToolTip { text: Ui.text("展开 Sage"); visible: railMouse.containsMouse }
    }
}
