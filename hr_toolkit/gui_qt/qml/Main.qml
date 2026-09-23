import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15
import QtQuick.Window 2.15
import "components"

ApplicationWindow {
    id: root
    objectName: "mainWindow"
    Binding { target: Ui; property: "backend"; value: controller.presentation }
    minimumWidth: 760
    minimumHeight: 600
    readonly property int preferredWindowWidth: 1600
    readonly property int preferredWindowHeight: 900
    readonly property int initialWindowMargin: 16
    readonly property int currentScreenAvailableWidth: Math.min(Screen.width, Screen.desktopAvailableWidth)
    readonly property int currentScreenAvailableHeight: Math.min(Screen.height, Screen.desktopAvailableHeight)
    width: Math.min(preferredWindowWidth,
                    Math.max(minimumWidth, currentScreenAvailableWidth - initialWindowMargin))
    height: Math.min(preferredWindowHeight,
                     Math.max(minimumHeight, currentScreenAvailableHeight - initialWindowMargin
                              - (Qt.platform.os === "windows" ? 48 : 0)))
    visible: true
    color: Ui.color("window")
    title: "HR Workbench v" + controller.appVersion
    // Keep Windows' native caption, resize frame and DWM decorations. macOS
    // still integrates its existing native titlebar through window_chrome.py.
    flags: Qt.Window
    property bool nativeTitleIntegrated: false
    readonly property alias sidebarPanel: sidebar
    Binding {
        target: root.contentItem
        property: "enabled"
        value: !controller.updateRestarting
    }

    readonly property color primary: Ui.color("accent")
    readonly property color primaryActive: Ui.color("accentPressed")
    readonly property color primarySoft: Ui.color("selection")
    readonly property color textMain: Ui.color("text")
    readonly property color textMuted: Ui.color("muted")
    readonly property color textFaint: Ui.color("faint")
    readonly property color textDisabled: Ui.color("disabledText")
    readonly property color border: Ui.color("border")
    readonly property color borderFaint: Ui.color("divider")
    readonly property color surface: Ui.color("surface")
    readonly property color surfaceAlt: Ui.color("input")
    readonly property color navSelected: Ui.color("pressed")
    readonly property color navHover: Ui.color("hover")
    readonly property int contentMaxWidth: 820
    readonly property bool showLegacyHistoryEntry: false
    // Navigation stays full-width when shown; small windows start collapsed.
    readonly property bool compactSidebar: false

    // Native window movement needs no new content frame. Suspend only the
    // decorative download water while moving; never pause the downloader.
    property bool windowMoving: false
    function noteWindowMotion() {
        if (controller.updateBusy && controller.updatePhase !== "checking") {
            windowMoving = true
            windowMoveSettle.restart()
        }
    }
    property bool aiPanelRequested: false
    property bool aiPanelCreated: false
    property string rightPanelTab: "files"
    readonly property bool sidePanelFits: !workspaceDrawer.autoCollapsed && height >= 640
    onSidePanelFitsChanged: if (!sidePanelFits) closeRightPanel()
    function closeRightPanel() {
        aiPanelRequested = false
        controller.setWorkspaceExpanded(false)
    }
    function openProjectPanel() {
        if (!controller.hasProject) return
        rightPanelTab = "files"
        aiPanelRequested = false
        controller.setWorkspaceExpanded(true)
    }
    function openSagePanel() {
        if (!sidePanelFits || aiWindowOpen) { openAiWindow(); return }
        rightPanelTab = "sage"
        aiPanelRequested = true
    }
    readonly property bool aiWindowOpen: aiWindowLoader.item ? aiWindowLoader.item.requestedOpen : false
    readonly property bool aiAssistantOpen: aiPanelRequested || aiWindowOpen
    function toggleAiPanel() {
        if (aiWindowLoader.item && aiWindowLoader.item.visible) {
            aiWindowLoader.item.requestedOpen = !aiWindowLoader.item.requestedOpen
            return
        }
        if (aiPanelRequested) closeRightPanel()
        else openSagePanel()
    }
    function openAiWindow() {
        aiPanelRequested = false
        // Detaching leaves the shared column available for project files.
        if (controller.hasProject && sidePanelFits) openProjectPanel()
        aiWindowLoader.active = true
        if (aiWindowLoader.item) {
            aiWindowLoader.item.requestedOpen = true
            aiWindowLoader.item.raise()
            aiWindowLoader.item.requestActivate()
        }
    }
    Shortcut { sequence: "Ctrl+K"; onActivated: root.toggleAiPanel() }
    onAiPanelRequestedChanged: {
        if (aiPanelRequested && !sidePanelFits) openAiWindow()
        else if (aiPanelRequested) {
            rightPanelTab = "sage"
            workspaceAddMenu.close()
            workspaceUseMenu.close()
            aiPanelCreated = true
        }
        else if (rightPanelTab === "sage") sageLauncher.forceActiveFocus()
    }
    onXChanged: noteWindowMotion()
    onYChanged: noteWindowMotion()
    Timer {
        id: windowMoveSettle
        interval: 180
        repeat: false
        onTriggered: root.windowMoving = false
    }

    // Modal dialogs can wait briefly for settled dimensions. The main layout
    // and docked project-files panel follow live dimensions on every frame.
    property int settledWidth: width
    property int settledHeight: height
    Timer {
        id: settleTimer
        interval: 32   // ~2 frames; fast enough to feel instant
        running: false
        repeat: false
        onTriggered: {
            root.settledWidth = root.width
            root.settledHeight = root.height
        }
    }
    onWidthChanged: settleTimer.restart()
    onHeightChanged: settleTimer.restart()

    readonly property var formSnapshot: {
        // Own one plain-JS snapshot per revision. Consumers must not each
        // rebuild the Python QVariantList or retain a property-backed sequence.
        var revision = controller.formRevision
        var fields = JSON.parse(JSON.stringify(controller.formFields))
        var byId = {}
        for (var index = 0; index < fields.length; ++index) {
            byId[String(fields[index].id)] = fields[index]
        }
        return ({ "fields": fields, "byId": byId })
    }

    function fieldById(fieldId) {
        return formSnapshot.byId[fieldId]
            || ({ "id": fieldId, "value": "", "options": [], "visible": false })
    }

    function choiceIndex(field) {
        var options = field.options || []
        for (var index = 0; index < options.length; ++index) {
            if (String(options[index].value) === String(field.value))
                return index
        }
        return 0
    }

    onClosing: function(closeEvent) {
        closeEvent.accepted = controller.requestClose()
    }
    Component.onCompleted: {
        if (width <= 980) sidebar.pinned = false
        controller.start()
    }

    AppButton {
        id: appearanceButton
        objectName: "appearanceButton"
        anchors.top: parent.top; anchors.topMargin: 8
        anchors.right: parent.right
        anchors.rightMargin: root.width - workspaceDrawer.x + 54
        z: 31
        text: "设置"; variant: "link"
        ToolTip.visible: hovered
        ToolTip.text: Ui.text("外观与语言")
        onClicked: appearanceDialog.open()
    }

    Rectangle {
        objectName: "sidebarTitleBackground"
        x: sidebar.x
        width: sidebar.width
        height: windowChrome.height
        visible: sidebar.visible
        color: sidebar.color
        z: 19
    }
    WindowChrome {
        id: windowChrome
        objectName: "windowChrome"
        width: parent.width
        window: root
        sidebar: root.sidebarPanel
        workspaceAvailable: true
        workspaceExpanded: workspaceDrawer.opened
        workspaceAutoHidden: false
        workspacePanelLeft: workspaceDrawer.x
        aiPanelLeft: root.width
        sharedPanel: true
        onWorkspaceToggleRequested: {
            if (workspaceDrawer.opened) root.closeRightPanel()
            else if (root.rightPanelTab === "sage" || !controller.hasProject) root.openSagePanel()
            else workspaceDrawer.open()
        }
        nativeMac: root.nativeTitleIntegrated
        nativeWindows: Qt.platform.os === "windows"
        systemButtons: false
        z: 30
    }
    Rectangle {
        objectName: "sidebarDivider"
        x: sidebar.x + sidebar.width - width
        y: 0
        width: 1
        height: parent.height
        visible: sidebar.visible
        color: Ui.color("border12")
        z: 31
    }

    RowLayout {
        id: workspaceLayout
        anchors.fill: parent
        spacing: 0

        Item {
            Layout.fillHeight: true
            Layout.preferredWidth: sidebar.reservedWidth
            Layout.minimumWidth: Layout.preferredWidth
            Layout.maximumWidth: Layout.preferredWidth
        }
        HoverSidebar {
            id: sidebar
            objectName: "sidebar"
            parent: root.contentItem
            y: windowChrome.height
            width: 248
            height: parent.height - y
            z: 20
            triggerHovered: windowChrome.triggerHovered
            keepOpen: projectMenu.opened
            windowActive: root.active

            ColumnLayout {
                anchors.fill: parent
                anchors.leftMargin: root.compactSidebar ? 10 : 12
                anchors.rightMargin: root.compactSidebar ? 10 : 12
                anchors.topMargin: 6
                anchors.bottomMargin: 14
                spacing: 0

                Card {
                    id: sidebarProjectCard
                    objectName: "sidebarProjectCard"
                    Layout.fillWidth: true
                    Layout.leftMargin: root.compactSidebar ? 0 : 3
                    Layout.rightMargin: root.compactSidebar ? 0 : 3
                    Layout.bottomMargin: root.compactSidebar ? 8 : 12
                    Layout.preferredHeight: root.compactSidebar ? 54 : 154
                    color: root.surface

                    Item {
                        anchors.fill: parent
                        visible: root.compactSidebar
                        Button {
                            anchors.fill: parent
                            hoverEnabled: true
                            focusPolicy: Qt.StrongFocus
                            onClicked: projectMenu.open()
                            contentItem: Text {
                                text: Ui.text("项目")
                                color: root.textMain
                                font.pixelSize: 11
                                font.weight: Font.DemiBold
                                horizontalAlignment: Text.AlignHCenter
                                verticalAlignment: Text.AlignVCenter
                            }
                            background: Rectangle { color: "transparent"; radius: 8 }
                        }
                    }

                    ColumnLayout {
                        visible: !root.compactSidebar
                        anchors.fill: parent
                        anchors.margins: 10
                        spacing: 0

                        Item {
                            Layout.fillWidth: true
                            Layout.preferredHeight: 25
                            RowLayout {
                                anchors.fill: parent
                                spacing: 4
                                Text {
                                    text: Ui.text("工作项目")
                                    color: root.textFaint
                                    font.pixelSize: 11
                                    font.weight: Font.DemiBold
                                }
                                Item { Layout.fillWidth: true }
                            }
                        }

                        Button {
                            objectName: "projectSelectorButton"
                            Layout.fillWidth: true
                            Layout.preferredHeight: 60
                            hoverEnabled: true
                            focusPolicy: Qt.StrongFocus
                            onClicked: projectMenu.open()
                            leftPadding: 10
                            rightPadding: 9
                            contentItem: RowLayout {
                                spacing: 7
                                ColumnLayout {
                                    Layout.fillWidth: true
                                    spacing: 4
                                    Text {
                                        Layout.fillWidth: true
                                        text: controller.hasProject ? controller.projectName : Ui.text("尚未打开项目")
                                        color: root.textMain
                                        font.pixelSize: 13
                                        font.weight: Font.DemiBold
                                        elide: Text.ElideRight
                                    }
                                    Text {
                                        Layout.fillWidth: true
                                        text: Ui.text(controller.hasProject ? (controller.projectWritable ? "当前项目" : "当前项目 · 只读") : "新建或打开项目后开始处理")
                                        color: root.textFaint
                                        font.pixelSize: 10
                                        elide: Text.ElideRight
                                    }
                                }
                                ToolIcon { Layout.preferredWidth: 13; Layout.preferredHeight: 13; iconId: "chevron_down"; strokeColor: root.textMuted; lineWidth: 1.25 }
                            }
                            background: Rectangle {
                                radius: 8
                                color: parent.hovered ? Ui.color("surface14") : Ui.color("surface17")
                                border.color: parent.activeFocus ? root.primary : root.border
                            }
                        }

                        RowLayout {
                            Layout.fillWidth: true
                            Layout.fillHeight: true
                            Layout.topMargin: 5
                            spacing: 0
                            Button {
                                objectName: "newProjectAction"
                                Accessible.name: Ui.text("新建项目")
                                ToolTip.visible: hovered
                                ToolTip.text: Ui.text("新建项目")
                                Layout.fillWidth: true
                                Layout.fillHeight: true
                                hoverEnabled: true
                                focusPolicy: Qt.StrongFocus
                                onClicked: controller.requestCreateProject()
                                contentItem: Item {
                                    Row {
                                        anchors.centerIn: parent
                                        spacing: 7
                                        ToolIcon { width: 16; height: 16; iconId: "plus_circle"; strokeColor: Ui.color("text1"); lineWidth: 1.25 }
                                        Text { text: Ui.text("新建"); color: root.textMain; font.pixelSize: 12 }
                                    }
                                }
                                background: Rectangle { radius: 7; color: parent.down ? root.navSelected : (parent.hovered ? root.navHover : "transparent") }
                            }
                            Rectangle { Layout.preferredWidth: 1; Layout.preferredHeight: 18; color: root.border }
                            Button {
                                objectName: "openProjectAction"
                                Accessible.name: Ui.text("打开项目")
                                ToolTip.visible: hovered
                                ToolTip.text: Ui.text("打开项目")
                                Layout.fillWidth: true
                                Layout.fillHeight: true
                                hoverEnabled: true
                                focusPolicy: Qt.StrongFocus
                                onClicked: controller.openProjectDialog()
                                contentItem: Item {
                                    Row {
                                        anchors.centerIn: parent
                                        spacing: 7
                                        ToolIcon { width: 16; height: 16; iconId: "folder_open"; strokeColor: Ui.color("text1"); lineWidth: 1.25 }
                                        Text { text: Ui.text("打开"); color: root.textMain; font.pixelSize: 12 }
                                    }
                                }
                                background: Rectangle { radius: 7; color: parent.down ? root.navSelected : (parent.hovered ? root.navHover : "transparent") }
                            }
                        }
                    }
                }

                ScrollView {
                    id: navScroll
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    clip: true
                    ScrollBar.horizontal.policy: ScrollBar.AlwaysOff
                    contentWidth: availableWidth

                    Column {
                        width: navScroll.availableWidth
                        spacing: 10
                        Repeater {
                            model: controller.navGroups
                            delegate: Column {
                                width: parent.width
                                spacing: 3
                                Text {
                                    visible: !root.compactSidebar
                                    width: parent.width
                                    leftPadding: 7
                                    text: Ui.text(modelData.name)
                                    color: root.textDisabled
                                    font.pixelSize: 11
                                    font.weight: Font.DemiBold
                                }
                                Repeater {
                                    model: modelData.items
                                    delegate: Rectangle {
                                        width: parent.width
                                        height: 33
                                        radius: 8
                                        color: controller.currentTool === modelData.id ? root.navSelected : (navMouse.containsMouse ? root.navHover : "transparent")
                                        Row {
                                            anchors.fill: parent
                                            anchors.leftMargin: root.compactSidebar ? 0 : 9
                                            spacing: 8
                                            Item {
                                                width: root.compactSidebar ? parent.width : 18
                                                height: parent.height
                                                ToolIcon {
                                                    anchors.centerIn: parent
                                                    width: 16
                                                    height: 16
                                                    iconId: modelData.id
                                                    strokeColor: controller.currentTool === modelData.id ? root.primary : Ui.color("text1")
                                                    lineWidth: 1.25
                                                }
                                            }
                                            Text {
                                                id: navLabel
                                                visible: !root.compactSidebar
                                                width: parent.width - 34
                                                height: parent.height
                                                text: Ui.text(modelData.id === "social_security" ? "社保汇总" : modelData.label)
                                                color: controller.currentTool === modelData.id ? root.primary : Ui.color("text1")
                                                font.pixelSize: 13
                                                font.weight: controller.currentTool === modelData.id ? Font.DemiBold : Font.Normal
                                                verticalAlignment: Text.AlignVCenter
                                                elide: Text.ElideRight
                                            }
                                        }
                                        MouseArea {
                                            id: navMouse
                                            anchors.fill: parent
                                            hoverEnabled: true
                                            cursorShape: Qt.PointingHandCursor
                                            onClicked: controller.selectTool(modelData.id)
                                            ToolTip {
                                                id: navTooltip
                                                objectName: "navigationTooltip_" + modelData.id
                                                visible: navMouse.containsMouse && !navMouse.pressed
                                                         && (root.compactSidebar || navLabel.truncated
                                                             || navLabel.text !== Ui.text(modelData.label))
                                                text: Ui.text(modelData.label)
                                                delay: 600
                                                timeout: 5000
                                                padding: 8
                                                contentItem: Text {
                                                    text: navTooltip.text
                                                    color: Ui.color("text")
                                                    font.pixelSize: 12
                                                }
                                                background: Rectangle {
                                                    color: Ui.color("surface")
                                                    border.color: Ui.color("border")
                                                    radius: 6
                                                }
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                }

                Rectangle { visible: root.showLegacyHistoryEntry; Layout.fillWidth: true; Layout.preferredHeight: 1; Layout.bottomMargin: 6; color: Ui.color("border12") }
                Rectangle {
                    visible: root.showLegacyHistoryEntry
                    Layout.fillWidth: true; Layout.preferredHeight: visible ? 32 : 0; radius: 8; color: historyNavMouse.containsMouse ? root.navHover : "transparent"
                    Row { anchors.fill: parent; anchors.leftMargin: root.compactSidebar ? 0 : 9; spacing: 8
                        Item { width: root.compactSidebar ? parent.width : 18; height: parent.height; ToolIcon { anchors.centerIn: parent; width: 16; height: 16; iconId: "clock"; strokeColor: Ui.color("text1") } }
                        Text { visible: !root.compactSidebar; width: parent.width - 34; height: parent.height; text: Ui.text("旧版记录"); color: Ui.color("text1"); font.pixelSize: 13; verticalAlignment: Text.AlignVCenter }
                    }
                    MouseArea { id: historyNavMouse; anchors.fill: parent; hoverEnabled: true; cursorShape: Qt.PointingHandCursor; onClicked: { controller.requestHistory(); historyDrawer.open() } }
                }
                Rectangle { Layout.fillWidth: true; Layout.preferredHeight: 1; Layout.topMargin: 4; Layout.bottomMargin: 6; color: Ui.color("border12") }
                AppButton {
                    id: sidebarUpdateCheckButton
                    objectName: "sidebarUpdateCheckButton"
                    Layout.fillWidth: true
                    Layout.preferredHeight: 32
                    visible: !controller.updateReady && !(controller.updateBusy && controller.updatePhase !== "checking")
                    text: controller.updateBusy ? "正在检查更新…" : "检查更新"
                    variant: "link"
                    leftPadding: 9
                    rightPadding: 9
                    enabled: !controller.updateBusy
                    onClicked: controller.requestUpdateCheck()
                    contentItem: RowLayout {
                        spacing: 8
                        Item {
                            Layout.preferredWidth: 18
                            Layout.fillHeight: true
                            ThemedImage {
                                anchors.centerIn: parent
                                width: 16; height: 16
                                source: Qt.resolvedUrl("components/arrows-clockwise.png")
                                sourceSize.width: 32; sourceSize.height: 32
                                opacity: sidebarUpdateCheckButton.enabled ? 0.65 : 0.3
                            }
                        }
                        Text {
                            Layout.fillWidth: true
                            text: Ui.text(sidebarUpdateCheckButton.text)
                            color: sidebarUpdateCheckButton.enabled ? root.textMain : root.textDisabled
                            font.pixelSize: 13
                            elide: Text.ElideRight
                            verticalAlignment: Text.AlignVCenter
                        }
                    }
                }
                Button {
                    id: sidebarUpdateCard
                    objectName: "sidebarUpdateCard"
                    Layout.fillWidth: true
                    Layout.preferredHeight: 48
                    Layout.leftMargin: -4
                    Layout.rightMargin: -4
                    visible: controller.updateReady || (controller.updateBusy && controller.updatePhase !== "checking")
                    enabled: controller.updateReady && !controller.updateBusy
                    hoverEnabled: true
                    padding: 10
                    Accessible.name: Ui.text(controller.updateReady ? "重启以更新，版本" + controller.updateVersion : "正在下载更新")
                    onClicked: controller.restartToUpdate()
                    background: Item {
                        Rectangle { anchors.fill: parent; anchors.topMargin: 2; anchors.bottomMargin: -2; color: Ui.color("overlay3"); radius: 10 }
                        Rectangle {
                            anchors.fill: parent; radius: 10
                            color: sidebarUpdateCard.down ? Ui.color("surface6") : Ui.color("surface")
                        }
                        // Small CPU-painted waves also work with Qt 5's software
                        // renderer. No shader, blur layer or continuous idle work.
                        Canvas {
                            id: updateFill
                            readonly property real fraction: controller.updateReady ? 0 : controller.updatePhase === "verifying" ? 1 : Math.max(0, Math.min(1, controller.updateProgress))
                            readonly property real level: fraction
                            property real wavePhase: 0
                            readonly property bool paintSuspended: root.windowMoving || !visible || !root.visible
                                || root.visibility === Window.Minimized || Qt.application.state !== Qt.ApplicationActive
                            readonly property bool wavesRunning: !paintSuspended
                                && controller.updateBusy && controller.updatePhase === "downloading"
                                && level > 0 && level < 1
                            anchors.fill: parent; anchors.margins: 1
                            visible: !controller.updateReady
                            renderTarget: Canvas.Image
                            renderStrategy: Canvas.Cooperative
                            // Do not stack a per-frame level animation on top
                            // of the wave timer. Repaint latest progress on resume.
                            onLevelChanged: if (!paintSuspended) requestPaint()
                            onWidthChanged: if (!paintSuspended) requestPaint()
                            onHeightChanged: if (!paintSuspended) requestPaint()
                            onPaintSuspendedChanged: if (!paintSuspended) requestPaint()
                            Timer {
                                interval: 50
                                repeat: true
                                running: updateFill.wavesRunning
                                onTriggered: {
                                    updateFill.wavePhase = (updateFill.wavePhase + 0.068) % (Math.PI * 2)
                                    updateFill.requestPaint()
                                }
                            }
                            property color themeRepaintColor: Ui.color("text")
            onThemeRepaintColorChanged: requestPaint()
            onPaint: {
                                if (paintSuspended) return
                                // Geometry and phase stay constant throughout
                                // this paint; avoid QML property lookups per point.
                                var paintWidth = width
                                var paintHeight = height
                                var paintLevel = level
                                var paintPhase = wavePhase
                                var ctx = getContext("2d")
                                ctx.clearRect(0, 0, paintWidth, paintHeight)
                                if (paintWidth <= 0 || paintHeight <= 0 || paintLevel <= 0)
                                    return
                                ctx.save()
                                ctx.beginPath()
                                ctx.roundedRect(0, 0, paintWidth, paintHeight, Math.min(9, paintWidth / 2, paintHeight / 2), Math.min(9, paintWidth / 2, paintHeight / 2))
                                ctx.clip()
                                var waterline = paintHeight * (1 - paintLevel)
                                // Taper at both ends: 0% stays empty; 100% is full.
                                var amplitude = Math.min(2.4, paintHeight * paintLevel * 0.45, waterline * 0.45)
                                function drawWave(offset, direction, scale, color) {
                                    ctx.beginPath()
                                    ctx.moveTo(0, paintHeight)
                                    for (var x = 0; x <= paintWidth + 5; x += 5) {
                                        var px = Math.min(x, paintWidth)
                                        var angle = px / paintWidth * Math.PI * 2 + paintPhase * direction + offset
                                        ctx.lineTo(px, waterline + Math.sin(angle) * amplitude * scale)
                                    }
                                    ctx.lineTo(paintWidth, paintHeight)
                                    ctx.closePath()
                                    ctx.fillStyle = color
                                    ctx.fill()
                                }
                                drawWave(1.4, -1, 0.7, "rgba(173, 200, 209, 0.22)")
                                drawWave(0, 1, 1, "rgba(194, 215, 221, 0.42)")
                                ctx.restore()
                            }
                        }
                        Rectangle {
                            anchors.fill: parent; anchors.margins: 1; radius: 9
                            color: "transparent"; border.color: Ui.color("overlay43")
                        }
                        Rectangle {
                            anchors.fill: parent; radius: 10; color: "transparent"
                            border.color: sidebarUpdateCard.visualFocus ? Ui.color("link6") : Ui.color("border8")
                        }
                    }
                    contentItem: RowLayout {
                        spacing: 10
                        Image {
                            Layout.preferredWidth: 28; Layout.preferredHeight: 28
                            source: Qt.resolvedUrl("components/update-feather.png")
                            fillMode: Image.PreserveAspectFit; smooth: true
                        }
                        ColumnLayout {
                            Layout.fillWidth: true; spacing: 3
                            Text {
                                Layout.fillWidth: true; font.pixelSize: 12; font.bold: true; color: root.textMain
                                text: Ui.text(controller.updateReady ? (controller.updateRestarting ? "正在重启…" : "重启以更新") : controller.updatePhase === "verifying" ? "正在检查更新文件…" : "正在下载更新")
                                elide: Text.ElideRight
                            }
                            Text {
                                Layout.fillWidth: true; font.pixelSize: 10; color: root.textMuted
                                text: Ui.text(controller.updateVersion ? "v" + controller.updateVersion : controller.updateStatus)
                                elide: Text.ElideRight
                            }
                        }
                        Text {
                            visible: !controller.updateReady && controller.updateProgress >= 0
                            text: Ui.text(Math.floor(controller.updateProgress * 100) + "%")
                            font.pixelSize: 13; color: root.textMain
                        }
                        ThemedImage {
                            visible: controller.updateReady
                            Layout.preferredWidth: 14; Layout.preferredHeight: 14
                            source: Qt.resolvedUrl("components/arrow-right.png"); sourceSize.width: 28; sourceSize.height: 28; opacity: 0.45
                        }
                    }
                }
                Rectangle { Layout.fillWidth: true; Layout.preferredHeight: 1; Layout.topMargin: 6; Layout.bottomMargin: 8; color: Ui.color("border12") }
                RowLayout {
                    Layout.fillWidth: true
                    Layout.preferredHeight: Math.max(24, sidebarPrivacyText.implicitHeight)
                    spacing: 5
                    BrandMark { Layout.preferredWidth: 16; Layout.preferredHeight: 16 }
                    Text { visible: !root.compactSidebar; text: Ui.text("v" + controller.appVersion); color: root.textDisabled; font.pixelSize: 10 }
                    Rectangle { visible: !root.compactSidebar; Layout.preferredWidth: 4; Layout.preferredHeight: 4; radius: 2; color: Ui.color("accent6") }
                    Text {
                        id: sidebarPrivacyText
                        visible: !root.compactSidebar
                        Layout.fillWidth: true; Layout.minimumWidth: 0
                        text: Ui.text("本地处理 · 不上传数据")
                        color: root.textMuted; font.pixelSize: 11; wrapMode: Text.Wrap
                    }
                    Button {
                        id: runLogIconButton
                        objectName: "runLogIconButton"
                        Layout.preferredWidth: 24
                        Layout.preferredHeight: 24
                        hoverEnabled: true
                        focusPolicy: Qt.StrongFocus
                        onClicked: controller.openRunLog()
                        contentItem: Item {
                            ToolIcon { anchors.centerIn: parent; width: 14; height: 14; iconId: "run_log"; strokeColor: runLogIconButton.hovered ? root.textMuted : root.textDisabled; lineWidth: 1.15 }
                        }
                        background: Rectangle { radius: 6; color: parent.hovered ? root.navHover : "transparent" }
                        ToolTip.visible: hovered
                        ToolTip.text: Ui.text("打开运行日志")
                    }
                }
            }
        }

        Item {
            id: mainPane
            objectName: "mainPane"
            Layout.topMargin: windowChrome.height
            Layout.fillWidth: true
            Layout.minimumWidth: 0
            Layout.fillHeight: true
            clip: true

            ColumnLayout {
                id: mainLayout
                objectName: "mainLayout"
                anchors.fill: parent
                anchors.leftMargin: Math.max(12, Math.min(28, (mainPane.width - 480) / 8))
                anchors.rightMargin: Math.max(16, Math.min(66, (mainPane.width - 480) / 5))
                anchors.topMargin: 8
                anchors.bottomMargin: 14
                spacing: 14

                RowLayout {
                    Layout.preferredWidth: Math.min(root.contentMaxWidth, mainLayout.width)
                    Layout.maximumWidth: root.contentMaxWidth
                    Layout.alignment: Qt.AlignHCenter
                    spacing: 10
                    // A plain Column keeps the header a one-way size flow: the
                    // row assigns this width, the wrapped texts report their
                    // natural heights back. As a nested ColumnLayout it also
                    // wrote Layout.* hints while mainLayout was assigning
                    // sizes, so a header button whose visibility follows the
                    // selected tool re-entered the polish pass until Qt
                    // aborted it (Layout polish loop detected).
                    Column {
                        Layout.fillWidth: true
                        spacing: 14
                        Text { width: parent.width; text: Ui.text(controller.toolGroup); color: root.primary; font.pixelSize: 12; font.weight: Font.DemiBold }
                        Text {
                            width: parent.width
                            text: Ui.text(controller.toolTitle)
                            color: root.textMain
                            font.pixelSize: 24
                            font.weight: Font.Bold
                            wrapMode: Text.Wrap
                        }
                        Text {
                            width: parent.width
                            text: Ui.text(controller.toolDescription)
                            color: root.textMuted
                            font.pixelSize: 13
                            wrapMode: Text.Wrap
                        }
                    }
                    AppButton {
                        objectName: "tutorialButton"
                        text: "使用教程"
                        variant: "link"
                        onClicked: helpDialog.open()
                    }
                    AppButton {
                        text: "地区编号维护"
                        visible: controller.currentTool === "archive_import" || controller.currentTool === "personnel_change_merge"
                        enabled: controller.hasProject && controller.selectionEnabled
                        variant: "link"
                        onClicked: regionCodeDialog.open()
                    }
                    AppButton {
                        objectName: "releaseNotesButton"
                        text: "更新记录"
                        variant: "link"
                        enabled: !controller.updateBusy
                        onClicked: controller.showReleaseNotes()
                    }
                    AppButton {
                        id: downloadLinkButton
                        objectName: "downloadLinkButton"
                        text: controller.downloadLinkBusy ? "正在获取地址…" : "复制下载地址"
                        variant: "link"
                        enabled: !controller.downloadLinkBusy
                        onClicked: downloadLinkMenu.open()
                        ToolTip.visible: hovered
                        ToolTip.text: Ui.text("复制最新版安装包地址，发给同事下载")
                        Popup {
                            id: downloadLinkMenu
                            x: downloadLinkButton.width - width
                            y: downloadLinkButton.height + 4
                            width: 304
                            padding: 12
                            closePolicy: Popup.CloseOnEscape | Popup.CloseOnPressOutside
                            background: Rectangle { color: Ui.color("surface"); radius: 9; border.color: Ui.color("border") }
                            contentItem: ColumnLayout {
                                spacing: 8
                                Text {
                                    Layout.fillWidth: true
                                    text: Ui.text("选择同事电脑的系统")
                                    font.pixelSize: 12
                                    color: root.textMuted
                                }
                                AppButton {
                                    Layout.fillWidth: true
                                    text: "Windows 7（64 位）"
                                    onClicked: { downloadLinkMenu.close(); controller.copyLatestDownloadUrl("win7") }
                                }
                                AppButton {
                                    Layout.fillWidth: true
                                    text: "Windows 10 / 11（64 位）"
                                    onClicked: { downloadLinkMenu.close(); controller.copyLatestDownloadUrl("windows") }
                                }
                                Text {
                                    Layout.fillWidth: true
                                    text: Ui.text("请务必按接收方电脑的系统选择链接：Windows 7 必须使用 Win7 安装包，切勿下载或安装 Win10/11 安装包；Windows 10/11 请使用对应的 Win10/11 安装包。")
                                    wrapMode: Text.Wrap
                                    font.pixelSize: 12
                                    color: Ui.color("warning4")
                                }
                                Text {
                                    Layout.fillWidth: true
                                    text: Ui.text("此处仅提供 Windows 安装包；Mac 及其他系统的安装包，请联系管理员获取。\n每次获取最新版地址，复制后可直接分享。")
                                    wrapMode: Text.Wrap
                                    font.pixelSize: 11
                                    color: root.textMuted
                                }
                            }
                        }
                    }
                }

                RowLayout {
                    Layout.preferredWidth: Math.min(root.contentMaxWidth, mainLayout.width)
                    Layout.maximumWidth: root.contentMaxWidth
                    Layout.alignment: Qt.AlignHCenter
                    visible: controller.variants.length > 0
                    spacing: 8
                    Repeater {
                        model: controller.variants
                        delegate: AppButton {
                            text: modelData.label
                            variant: controller.currentVariant === modelData.id ? "primary" : "secondary"
                            onClicked: controller.selectVariant(modelData.id)
                        }
                    }
                    Item { Layout.fillWidth: true }
                }

                ScrollView {
                    id: mainScroll
                    objectName: "mainScroll"
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    Layout.minimumHeight: 0
                    // The viewport takes the space left by the header. Its
                    // intrinsic size must not feed the scrolling content's
                    // height-for-width back into the surrounding layout.
                    implicitWidth: 0
                    implicitHeight: 0
                    Layout.topMargin: 0
                    clip: true
                    contentWidth: availableWidth
                    contentHeight: contentColumn.implicitHeight
                    ScrollBar.horizontal.policy: ScrollBar.AlwaysOff
                    ScrollBar.vertical: ScrollBar {
                        objectName: "mainVerticalScrollBar"
                        // Keep the reading-width insets, but place the attached
                        // scrollbar at the pane edge, outside the clipped view.
                        parent: mainPane
                        anchors.right: parent.right
                        anchors.rightMargin: 6
                        y: mainLayout.y + mainScroll.y
                        height: mainScroll.height
                        policy: ScrollBar.AsNeeded
                        interactive: true
                    }

                    // ScrollView owns the Flickable; constrain that viewport
                    // rather than the scrollbar, preserving normal scrolling.
                    Binding {
                        target: mainScroll.contentItem
                        property: "boundsBehavior"
                        value: Flickable.StopAtBounds
                    }

                    Column {
                        id: contentColumn
                        objectName: "contentColumn"
                        width: Math.min(root.contentMaxWidth, mainScroll.availableWidth)
                        x: Math.max(0, (mainScroll.availableWidth - width) / 2)
                        spacing: 14

                        Card {
                            id: primaryUploadCard
                            width: contentColumn.width
                            height: uploadColumn.implicitHeight + 32
                            Column {
                                id: uploadColumn
                                anchors.left: parent.left
                                anchors.right: parent.right
                                anchors.top: parent.top
                                anchors.leftMargin: 20
                                anchors.rightMargin: 20
                                anchors.topMargin: 16
                                spacing: 10
                                RowLayout {
                                    width: uploadColumn.width
                                    height: Math.max(26, implicitHeight)
                                    Text { text: Ui.text(controller.inputLabel); color: root.textMain; font.pixelSize: 15; font.weight: Font.DemiBold }
                                    Text { Layout.fillWidth: true; text: Ui.text(controller.inputHint); color: root.textFaint; font.pixelSize: 11; wrapMode: Text.Wrap }
                                }
                                RowLayout {
                                    width: uploadColumn.width
                                    Text { Layout.fillWidth: true; text: Ui.text(controller.inputDropHint); color: root.textMuted; font.pixelSize: 11; wrapMode: Text.Wrap }
                                    AppButton {
                                        objectName: "continueInputButton"
                                        visible: inputList.count > 0
                                        enabled: controller.selectionEnabled
                                        text: controller.inputAllowsMultiple ? "继续添加" : "更换"
                                        variant: "link"
                                        onClicked: {
                                            if (controller.inputAllowsFolder && controller.inputAllowsFiles) {
                                                addInputPopup.appendMode = true
                                                addInputPopup.open()
                                            } else if (controller.inputAllowsFolder) controller.appendInputFolder()
                                            else controller.appendInputFiles()
                                        }
                                    }
                                    RecentSelectionButton {
                                        objectName: "inputRecentButton"
                                        backend: controller; selectionRole: "input"
                                        appendMode: inputList.count > 0
                                    }
                                    AppButton { objectName: "clearInputsButton"; visible: inputList.count > 0; enabled: controller.selectionEnabled; text: "清空"; variant: "link"; onClicked: controller.clearInputs() }
                                }
                                Rectangle {
                                    width: uploadColumn.width
                                    height: inputList.count > 0 ? Math.min(260, Math.max(54, inputList.count * 46)) : 118
                                    radius: 12
                                    color: Ui.color("surface15")
                                    border.width: 0

                                    DashedBorder { anchors.fill: parent }

                                    Column {
                                        anchors.centerIn: parent
                                        visible: inputList.count === 0
                                        spacing: 6
                                        FolderDropIcon { anchors.horizontalCenter: parent.horizontalCenter }
                                        Text { anchors.horizontalCenter: parent.horizontalCenter; text: Ui.text(controller.inputDropTitle); color: root.textMain; font.pixelSize: 13; font.weight: Font.DemiBold }
                                        Text {
                                            anchors.horizontalCenter: parent.horizontalCenter
                                            text: Ui.text(controller.inputAllowsFolder && !controller.inputAllowsFiles
                                                ? "点击浏览文件夹路径"
                                                : (controller.inputAllowsFolder ? "浏览文件 · 选择文件夹" : "点击浏览文件"))
                                            color: root.primary
                                            font.pixelSize: 11
                                            font.weight: Font.DemiBold
                                        }
                                    }

                                    ListView {
                                        id: inputList
                                        objectName: "inputList"
                                        boundsBehavior: Flickable.StopAtBounds
                                        flickableDirection: Flickable.VerticalFlick
                                        interactive: contentHeight > height
                                        anchors.fill: parent
                                        anchors.margins: 7
                                        visible: count > 0
                                        clip: true
                                        model: controller.inputModel
                                        reuseItems: true
                                        cacheBuffer: 92
                                        property int activeDelegateCount: 0
                                        spacing: 2
                                        ScrollBar.vertical: ScrollBar { policy: inputList.contentHeight > inputList.height ? ScrollBar.AsNeeded : ScrollBar.AlwaysOff }
                                        delegate: Rectangle {
                                            Component.onCompleted: inputList.activeDelegateCount += 1
                                            Component.onDestruction: inputList.activeDelegateCount -= 1
                                            width: inputList.width
                                            height: 44
                                            radius: 8
                                            color: fileMouse.containsMouse ? Ui.color("surface5") : "transparent"
                                            RowLayout {
                                                anchors.fill: parent
                                                anchors.leftMargin: 10
                                                anchors.rightMargin: 6
                                                spacing: 9
                                                Rectangle {
                                                    Layout.preferredWidth: 30; Layout.preferredHeight: 26; radius: 6
                                                    color: kind === "folder" ? Ui.color("selection10") : Ui.color("selection11")
                                                    Text { anchors.centerIn: parent; text: Ui.text(kind === "folder" ? "夹" : detail.slice(0, 3)); color: kind === "folder" ? root.primary : Ui.color("link4"); font.pixelSize: 10; font.weight: Font.DemiBold }
                                                }
                                                Item {
                                                    Layout.fillWidth: true
                                                    Layout.preferredHeight: inputFileDetails.implicitHeight
                                                    ColumnLayout {
                                                        id: inputFileDetails
                                                        anchors.fill: parent; spacing: 1
                                                        Text { Layout.fillWidth: true; text: name; color: root.textMain; font.pixelSize: 12; elide: Text.ElideMiddle }
                                                        Text { Layout.fillWidth: true; text: path; color: root.textMuted; font.pixelSize: 10; elide: Text.ElideMiddle }
                                                    }
                                                    MouseArea {
                                                        anchors.fill: parent; hoverEnabled: true
                                                        enabled: controller.selectionEnabled
                                                        onDoubleClicked: controller.openSelectedInput(path)
                                                        ToolTip.visible: containsMouse; ToolTip.delay: 600
                                                        ToolTip.text: Ui.text(path + "\n双击打开")
                                                    }
                                                }
                                                AppButton { text: "移除"; variant: "link"; enabled: controller.selectionEnabled; implicitWidth: Math.max(54, contentItem.implicitWidth + 12); implicitHeight: 30; onClicked: controller.removeInput(index) }
                                            }
                                            MouseArea { id: fileMouse; anchors.fill: parent; hoverEnabled: true; acceptedButtons: Qt.NoButton }
                                        }
                                    }

                                    MouseArea {
                                        anchors.fill: parent
                                        visible: inputList.count === 0
                                        enabled: controller.selectionEnabled
                                        cursorShape: Qt.PointingHandCursor
                                        onClicked: {
                                            if (controller.inputAllowsFiles && controller.inputAllowsFolder) {
                                                addInputPopup.appendMode = false
                                                addInputPopup.open()
                                            } else if (controller.inputAllowsFolder)
                                                controller.chooseInputFolder()
                                            else
                                                controller.chooseInputFiles()
                                        }
                                    }

                                    Popup {
                                        id: addInputPopup
                                        property bool appendMode: false
                                        x: Math.max(8, (parent.width - width) / 2)
                                        y: Math.max(8, (parent.height - height) / 2)
                                        width: 230
                                        padding: 8
                                        closePolicy: Popup.CloseOnEscape | Popup.CloseOnPressOutside
                                        background: Rectangle { radius: 10; color: Ui.color("surface"); border.color: root.border }
                                        contentItem: ColumnLayout {
                                            spacing: 4
                                            AppButton { Layout.fillWidth: true; enabled: controller.selectionEnabled; text: "添加文件 / 压缩包"; onClicked: { addInputPopup.close(); if (addInputPopup.appendMode) controller.appendInputFiles(); else controller.chooseInputFiles() } }
                                            AppButton { Layout.fillWidth: true; enabled: controller.selectionEnabled; text: "添加文件夹"; onClicked: { addInputPopup.close(); if (addInputPopup.appendMode) controller.appendInputFolder(); else controller.chooseInputFolder() } }
                                        }
                                    }
                                }
                                Text {
                                    id: inputSelectionFeedback
                                    width: uploadColumn.width
                                    property var feedback: controller.selectionFeedback.input || ({})
                                    visible: !!feedback.text
                                    text: Ui.text(feedback.text || "")
                                    textFormat: Text.PlainText; wrapMode: Text.Wrap
                                    maximumLineCount: 6; elide: Text.ElideRight
                                    font.pixelSize: 12; color: feedback.error ? Ui.color("error") : root.textMuted
                                    ToolTip.visible: inputFeedbackHover.hovered && truncated
                                    ToolTip.text: Ui.text(text)
                                    HoverHandler { id: inputFeedbackHover }
                                }
                                AppButton { visible: controller.selectionChecking; text: "取消资料检查"; variant: "link"; onClicked: controller.cancelSelectionCheck() }
                            }
                            FileDropTarget {
                                objectName: "primaryInputDropTarget"
                                anchors.fill: parent; z: 2
                                backend: controller; role: "input"
                                canReceive: controller.selectionEnabled
                                contextKey: controller.currentTool + ":" + controller.currentVariant
                            }
                        }

                        Card {
                            id: formCard
                            width: contentColumn.width
                            height: formColumn.implicitHeight + 54 + (formScroll.needsHorizontalScroll ? 14 : 0)
                            Flickable {
                                id: formScroll
                                objectName: "formScroll"
                                anchors.fill: parent
                                anchors.leftMargin: 24
                                anchors.rightMargin: 24
                                anchors.topMargin: 32
                                anchors.bottomMargin: 22 + (needsHorizontalScroll ? 14 : 0)
                                // Keep dates and the complete attendance options
                                // row reachable without squeezing their controls.
                                readonly property real minimumFormWidth: controller.currentTool === "data_statistics" ? Math.max(520, attendanceOptions.minimumContentWidth) : 0
                                readonly property bool needsHorizontalScroll: width < minimumFormWidth
                                contentWidth: Math.max(width, minimumFormWidth)
                                contentHeight: formColumn.implicitHeight
                                flickableDirection: Flickable.HorizontalFlick
                                boundsBehavior: Flickable.StopAtBounds
                                interactive: needsHorizontalScroll
                                clip: true
                                onWidthChanged: contentX = Math.max(0, Math.min(contentX, contentWidth - width))
                                onMinimumFormWidthChanged: contentX = 0
                                ScrollBar.horizontal: ScrollBar {
                                    objectName: "formHorizontalScrollBar"
                                    parent: formCard
                                    anchors.left: parent.left
                                    anchors.right: parent.right
                                    anchors.leftMargin: 24
                                    anchors.rightMargin: 24
                                    anchors.bottom: parent.bottom
                                    anchors.bottomMargin: 12
                                    policy: formScroll.needsHorizontalScroll ? ScrollBar.AlwaysOn : ScrollBar.AlwaysOff
                                    interactive: true
                                }
                            }
                            Column {
                                id: formColumn
                                objectName: "formColumn"
                                parent: formScroll.contentItem
                                width: formScroll.contentWidth
                                spacing: 11

                                Item {
                                    width: formColumn.width
                                    height: supportSelectionColumn.implicitHeight + 16
                                    visible: controller.hasSupportField
                                    ColumnLayout {
                                        id: supportSelectionColumn
                                        anchors.fill: parent
                                        anchors.topMargin: 8
                                        anchors.bottomMargin: 8
                                        spacing: 4
                                        RowLayout {
                                            Layout.fillWidth: true; spacing: 10
                                            Text {
                                                id: supportFieldLabel
                                                Layout.minimumWidth: Math.max(145, implicitWidth)
                                                Layout.preferredWidth: Layout.minimumWidth
                                                text: Ui.text(controller.supportLabel)
                                                color: root.textMain; font.pixelSize: 13
                                            }
                                            Item {
                                                Layout.fillWidth: true
                                                Layout.preferredHeight: 30
                                                Text { anchors.fill: parent; text: Ui.text(controller.supportPath || "未选择"); color: controller.supportPath ? root.textMain : root.textFaint; font.pixelSize: 12; verticalAlignment: Text.AlignVCenter; elide: Text.ElideMiddle }
                                                MouseArea {
                                                    anchors.fill: parent; hoverEnabled: true
                                                    enabled: controller.selectionEnabled && !!controller.supportPath
                                                    onDoubleClicked: controller.openSelectedInput(controller.supportPath)
                                                    ToolTip.visible: containsMouse; ToolTip.delay: 600
                                                    ToolTip.text: Ui.text(controller.supportPath + "\n双击打开")
                                                }
                                            }
                                            AppButton { enabled: controller.selectionEnabled; text: controller.currentTool === "material_collector" ? "选择文件" : controller.supportButtonText; variant: "link"; onClicked: controller.chooseSupportFile() }
                                            AppButton { enabled: controller.selectionEnabled; visible: controller.supportAllowsFolder; text: "选择文件夹"; variant: "link"; onClicked: controller.chooseSupportFolder() }
                                            RecentSelectionButton { objectName: "supportRecentButton"; backend: controller; selectionRole: "support" }
                                            AppButton { enabled: controller.selectionEnabled; visible: !!controller.supportPath; text: "清除"; variant: "link"; onClicked: controller.clearSupport() }
                                        }
                                        Text { Layout.fillWidth: true; text: Ui.text(controller.supportDropHint); color: root.textMuted; font.pixelSize: 11; wrapMode: Text.Wrap }
                                        Text {
                                            id: supportSelectionFeedback
                                            Layout.fillWidth: true
                                            property var feedback: controller.selectionFeedback.support || ({})
                                            visible: !!feedback.text
                                            text: Ui.text(feedback.text || "")
                                            textFormat: Text.PlainText; wrapMode: Text.Wrap
                                            maximumLineCount: 6; elide: Text.ElideRight
                                            font.pixelSize: 12; color: feedback.error ? Ui.color("error") : root.textMuted
                                            ToolTip.visible: supportFeedbackHover.hovered && truncated
                                            ToolTip.text: Ui.text(text)
                                            HoverHandler { id: supportFeedbackHover }
                                        }
                                    }
                                    FileDropTarget {
                                        objectName: "supportInputDropTarget"
                                        anchors.fill: parent; z: 2
                                        backend: controller; role: "support"
                                        canReceive: controller.selectionEnabled && controller.hasSupportField
                                        contextKey: controller.currentTool + ":" + controller.currentVariant
                                    }
                                }

                                RowLayout {
                                    width: formColumn.width
                                    visible: controller.currentTool !== "folder_rename"
                                    spacing: 10
                                    Text { Layout.preferredWidth: 145; wrapMode: Text.Wrap; text: Ui.text("结果位置"); color: root.textMain; font.pixelSize: 13 }
                                    Rectangle {
                                        Layout.fillWidth: true
                                        Layout.preferredHeight: 36
                                        color: root.surfaceAlt
                                        radius: 6
                                        border.width: 1
                                        border.color: root.border
                                        Text { anchors.fill: parent; anchors.leftMargin: 11; anchors.rightMargin: 11; text: Ui.text(controller.hasProject ? "当前项目 / 本次处理结果" : "请先新建或打开工作项目"); color: controller.hasProject ? root.textFaint : root.textDisabled; font.pixelSize: 12; verticalAlignment: Text.AlignVCenter; elide: Text.ElideMiddle }
                                    }
                                    AppButton { text: "打开项目"; variant: "link"; visible: controller.hasProject; onClicked: controller.openProjectFolder() }
                                    AppButton { text: "新建项目"; variant: "link"; visible: !controller.hasProject; enabled: controller.selectionEnabled; onClicked: controller.requestCreateProject() }
                                    AppButton { text: "打开已有"; variant: "link"; visible: !controller.hasProject; enabled: controller.selectionEnabled; onClicked: controller.openProjectDialog() }
                                }

                                Column {
                                    id: materialOptions
                                    width: formColumn.width
                                    topPadding: 9
                                    visible: controller.currentTool === "material_collector"
                                    spacing: 5
                                    readonly property var libraryField: root.fieldById("library_mode")
                                    readonly property var targetField: root.fieldById("target_input")
                                    readonly property var collectAllField: root.fieldById("collect_all")
                                    readonly property var zipField: root.fieldById("create_zip")
                                    readonly property var cacheField: root.fieldById("use_ocr_cache")
                                    readonly property bool flatOcr: String(libraryField.value) === "flat_ocr"

                                    Text {
                                        width: materialOptions.width
                                        text: Ui.text("资料检索与打包设置")
                                        color: root.textMain
                                        font.pixelSize: 13
                                        font.weight: Font.DemiBold
                                    }

                                    Rectangle {
                                        width: materialOptions.width
                                        height: materialOptionsColumn.implicitHeight + 28
                                        color: root.surface
                                        border.width: 1
                                        border.color: root.border

                                        Column {
                                            id: materialOptionsColumn
                                            anchors.left: parent.left
                                            anchors.right: parent.right
                                            anchors.top: parent.top
                                            anchors.margins: 14
                                            spacing: 10

                                            RowLayout {
                                                width: materialOptionsColumn.width
                                                spacing: 8
                                                Text { Layout.preferredWidth: 66; wrapMode: Text.Wrap; text: Ui.text("资料库形式"); color: root.textMain; font.pixelSize: 13 }
                                                AppComboBox {
                                                    id: materialLibraryMode
                                                    Layout.preferredWidth: Math.min(290, Math.max(160, (contentColumn.width - 76) * 0.5))
                                                    model: materialOptions.libraryField.options || []
                                                    textRole: "label"
                                                    currentIndex: root.choiceIndex(materialOptions.libraryField)
                                                    onActivated: controller.setFieldValue("library_mode", materialOptions.libraryField.options[index].value)
                                                }
                                                Text {
                                                    Layout.fillWidth: true
                                                    text: Ui.text(materialOptions.flatOcr ? "源文件不改；首次建立隐藏索引，未变化文件直接复用" : "原模式按姓名文件夹查找")
                                                    color: root.textFaint
                                                    font.pixelSize: 11
                                                    wrapMode: Text.Wrap
                                                }
                                            }

                                            RowLayout {
                                                width: materialOptionsColumn.width
                                                spacing: 8
                                                Text { Layout.preferredWidth: 66; wrapMode: Text.Wrap; text: Ui.text("目标人员"); color: root.textMain; font.pixelSize: 13 }
                                                AppTextField {
                                                    id: materialTargetInput
                                                    Layout.fillWidth: true
                                                    text: materialOptions.targetField.value === undefined || materialOptions.targetField.value === null ? "" : String(materialOptions.targetField.value)
                                                    placeholderText: Ui.text("姓名或身份证，多人用逗号隔开")
                                                    onTextEdited: controller.setFieldValue("target_input", text)
                                                }
                                                AppButton {
                                                    text: "✕ 清空"
                                                    variant: "link"
                                                    onClicked: {
                                                        materialTargetInput.text = ""
                                                        controller.setFieldValue("target_input", "")
                                                    }
                                                }
                                            }

                                            Text {
                                                x: 74
                                                width: Math.max(0, materialOptionsColumn.width - x)
                                                text: Ui.text("可选：留空时使用员工名单 Excel；填写时以此处人员为准")
                                                color: root.textFaint
                                                font.pixelSize: 11
                                                wrapMode: Text.Wrap
                                            }

                                            RowLayout {
                                                width: materialOptionsColumn.width
                                                spacing: 8
                                                Text { Layout.preferredWidth: 66; wrapMode: Text.Wrap; text: Ui.text("打包设置"); color: root.textMain; font.pixelSize: 13; Layout.alignment: Qt.AlignTop; topPadding: 5 }
                                                Flow {
                                                    Layout.fillWidth: true
                                                    spacing: 15
                                                    AppCheckBox {
                                                        text: materialOptions.flatOcr ? "全部（提取 OCR 识别到的该人员全部材料）" : "全部（直接拷贝匹配到的人员整个文件夹）"
                                                        width: Math.min(implicitWidth, parent.width)
                                                        height: Math.max(implicitHeight, contentItem.implicitHeight + topPadding + bottomPadding)
                                                        checked: !!materialOptions.collectAllField.value
                                                        onToggled: controller.setFieldValue("collect_all", checked)
                                                    }
                                                    AppCheckBox {
                                                        text: "生成 ZIP 压缩包"
                                                        checked: !!materialOptions.zipField.value
                                                        onToggled: controller.setFieldValue("create_zip", checked)
                                                    }
                                                    AppCheckBox {
                                                        text: "启用缓存"
                                                        checked: !!materialOptions.cacheField.value
                                                        enabled: !materialOptions.flatOcr
                                                        onToggled: controller.setFieldValue("use_ocr_cache", checked)
                                                    }
                                                }
                                            }

                                            Text {
                                                x: 74
                                                width: Math.max(0, materialOptionsColumn.width - x)
                                                visible: !!materialOptions.collectAllField.value
                                                text: Ui.text(materialOptions.flatOcr ? "取消勾选「全部」后，可只提取指定材料；索引仍会覆盖整个资料库" : "取消勾选「全部」后可按需勾选材料类型（如身份证、劳动合同等）")
                                                color: root.textFaint
                                                font.pixelSize: 11
                                                wrapMode: Text.Wrap
                                            }

                                            Loader {
                                                width: materialOptionsColumn.width
                                                visible: !materialOptions.collectAllField.value
                                                active: visible
                                                property var field: root.fieldById("material_types")
                                                sourceComponent: materialCollectorTypesComponent
                                            }
                                            Text {
                                                width: materialOptionsColumn.width
                                                readonly property var feedback: controller.selectionFeedback.material_types || ({})
                                                visible: !!feedback.text; text: Ui.text(feedback.text || "")
                                                textFormat: Text.PlainText; wrapMode: Text.Wrap
                                                color: Ui.color("error"); font.pixelSize: 12
                                            }
                                        }
                                    }
                                }

                                Repeater {
                                    model: controller.currentTool === "material_collector" ? [] : root.formSnapshot.fields
                                    delegate: Loader {
                                        width: formColumn.width
                                        readonly property bool groupedAttendanceField: controller.currentTool === "data_statistics"
                                            && (modelData.id === "remark_unit" || modelData.id === "include_business_trip" || modelData.id === "include_workday_business_trip")
                                        visible: modelData.visible && !groupedAttendanceField
                                        active: visible
                                        property var field: modelData
                                        sourceComponent: field.kind === "text" ? textFieldComponent
                                                       : field.kind === "choice" ? choiceFieldComponent
                                                       : field.kind === "check" ? checkFieldComponent
                                                       : field.kind === "date_range" ? dateRangeFieldComponent
                                                       : field.kind === "materials" ? materialsFieldComponent
                                                       : null
                                    }
                                }

                                RowLayout {
                                    id: attendanceOptions
                                    objectName: "attendanceOptions"
                                    width: formColumn.width
                                    visible: controller.currentTool === "data_statistics"
                                    spacing: 10
                                    readonly property var unitField: root.fieldById("remark_unit")
                                    readonly property var businessTripField: root.fieldById("include_business_trip")
                                    readonly property var workdayTripField: root.fieldById("include_workday_business_trip")
                                    // Measure unwrapped labels, not the RowLayout's
                                    // width-dependent size hint, to avoid feeding
                                    // Flickable.contentWidth back into itself.
                                    readonly property real minimumContentWidth: Math.max(145, unitLabel.implicitWidth)
                                        + 220 + businessTrip.Layout.minimumWidth + workdayTrip.Layout.minimumWidth
                                        + spacing * 4 + 40
                                    Text {
                                        id: unitLabel
                                        Layout.minimumWidth: Math.max(145, implicitWidth)
                                        text: Ui.text(attendanceOptions.unitField.label || "")
                                        color: root.textMain; font.pixelSize: 13
                                    }
                                    AppComboBox {
                                        objectName: "attendanceUnit"
                                        Layout.minimumWidth: 220
                                        Layout.preferredWidth: 220
                                        model: attendanceOptions.unitField.options || []
                                        textRole: "label"
                                        currentIndex: root.choiceIndex(attendanceOptions.unitField)
                                        onActivated: controller.setFieldValue("remark_unit", attendanceOptions.unitField.options[index].value)
                                    }
                                    Item { Layout.fillWidth: true }
                                    AppCheckBox {
                                        id: businessTrip
                                        objectName: "attendanceBusinessTrip"
                                        Layout.minimumWidth: Math.ceil(businessTripMetrics.width) + indicator.implicitWidth + spacing
                                        Layout.preferredWidth: Layout.minimumWidth
                                        text: attendanceOptions.businessTripField.label || ""
                                        checked: !!attendanceOptions.businessTripField.value
                                        onToggled: controller.setFieldValue("include_business_trip", checked)
                                    }
                                    AppCheckBox {
                                        id: workdayTrip
                                        objectName: "attendanceWorkdayTrip"
                                        Layout.minimumWidth: Math.ceil(workdayTripMetrics.width) + indicator.implicitWidth + spacing
                                        Layout.preferredWidth: Layout.minimumWidth
                                        Layout.rightMargin: 40
                                        text: attendanceOptions.workdayTripField.label || ""
                                        checked: !!attendanceOptions.workdayTripField.value
                                        onToggled: controller.setFieldValue("include_workday_business_trip", checked)
                                    }
                                    TextMetrics { id: businessTripMetrics; font: businessTrip.contentItem.font; text: Ui.text(businessTrip.text) }
                                    TextMetrics { id: workdayTripMetrics; font: workdayTrip.contentItem.font; text: Ui.text(workdayTrip.text) }
                                }

                            }
                        }

                        RowLayout {
                            width: contentColumn.width
                            spacing: 12
                            AppButton {
                                objectName: "runButton"
                                text: controller.runButtonText
                                variant: controller.busy ? "secondary" : "primary"
                                // Match the Tk workflow: the primary action remains
                                // clickable before a project is open, then the
                                // controller explains the required next step.  A
                                // running action must also stay clickable so it can
                                // always be stopped safely.
                                enabled: controller.busy || (!controller.workspaceBusy && !controller.updateBlocksTools && !controller.selectionChecking)
                                implicitWidth: Math.max(132, contentItem.implicitWidth + 26)
                                implicitHeight: 40
                                onClicked: controller.runOrCancel()
                            }
                            AppButton { text: "打开结果目录"; enabled: controller.canOpenLastResult; implicitWidth: Math.max(138, contentItem.implicitWidth + 26); implicitHeight: 40; onClicked: controller.openLastResult() }
                            AppButton { text: "打开报表"; visible: controller.canOpenPrimaryResult; enabled: !controller.busy; onClicked: controller.openPrimaryResult() }
                            AppButton { objectName: "templateNameSettings"; text: "模板设置" + (controller.templateSavedProfileCount ? "（已记住 " + controller.templateSavedProfileCount + " 项）" : ""); visible: controller.supportsTemplateRules; enabled: !controller.busy && !controller.workspaceBusy; onClicked: controller.reviewTemplateRules() }
                            Text { visible: !!controller.lastRunText; text: Ui.text(controller.lastRunText); color: root.textMuted; font.pixelSize: 12 }
                            Item { Layout.fillWidth: true }
                        }

                        Text {
                            visible: controller.updateBlocksTools
                            width: contentColumn.width; wrapMode: Text.Wrap
                            text: Ui.text(controller.updateBlockMessage)
                            color: root.primary; font.pixelSize: 12
                        }

                        Text {
                            objectName: "taskStageText"
                            width: contentColumn.width
                            visible: controller.busy && controller.currentTool !== "material_collector"
                            text: Ui.text(controller.runProgressMessage + (controller.runProgressTotal > 0
                                ? "（当前阶段 " + controller.runProgressCurrent + "/" + controller.runProgressTotal + "）" : ""))
                            textFormat: Text.PlainText; wrapMode: Text.Wrap
                            color: root.primary; font.pixelSize: 13
                        }

                        Card {
                            objectName: "resultNoticesCard"
                            visible: controller.resultNoticeCount > 0
                            width: contentColumn.width; height: 218
                            ColumnLayout {
                                anchors.fill: parent; anchors.margins: 14
                                RowLayout {
                                    Layout.fillWidth: true
                                    Text { text: Ui.text("处理完成 · " + controller.resultNoticeCount + " 条提醒/运行信息"); color: root.textMain; font.pixelSize: 13 }
                                    Item { Layout.fillWidth: true }
                                    AppButton { text: "复制全部"; variant: "link"; onClicked: controller.copyResultNotices() }
                                }
                                Text { Layout.fillWidth: true; text: Ui.text("请按原文核对；条数不代表异常人数。"); color: root.textMuted; font.pixelSize: 11 }
                                Flow {
                                    Layout.fillWidth: true; Layout.preferredHeight: childrenRect.height
                                    spacing: 4
                                    Repeater {
                                        model: controller.resultNoticeCategories
                                        AppButton {
                                            text: Ui.text(modelData.name) + " " + modelData.count
                                            variant: controller.resultNoticeFilter === modelData.name ? "tonal" : "link"
                                            onClicked: controller.setResultNoticeFilter(modelData.name)
                                        }
                                    }
                                }
                                ListView {
                                    Layout.fillWidth: true; Layout.fillHeight: true
                                    clip: true; reuseItems: true; cacheBuffer: 100
                                    boundsBehavior: Flickable.StopAtBounds
                                    model: controller.resultNoticeModel
                                    ScrollBar.vertical: ScrollBar { policy: ScrollBar.AsNeeded }
                                    delegate: Text {
                                        width: ListView.view.width; height: implicitHeight + 6
                                        text: Ui.text("【" + model.category + "】" + model.text); textFormat: Text.PlainText
                                        wrapMode: Text.Wrap; maximumLineCount: 3; elide: Text.ElideRight
                                        color: root.textMain; font.pixelSize: 12
                                        ToolTip.visible: noticeHover.hovered && truncated
                                        ToolTip.text: Ui.text(text)
                                        HoverHandler { id: noticeHover }
                                    }
                                }
                            }
                        }

                        MaterialRunProgress {
                            width: contentColumn.width
                            visible: controller.currentTool === "material_collector" && controller.runProgressVisible
                            completed: controller.runProgressCurrent
                            total: controller.runProgressTotal
                            message: controller.runProgressMessage
                            elapsedSeconds: controller.runProgressElapsed
                            waitSeconds: controller.runProgressWaitSeconds
                            active: controller.busy
                        }

                        Card {
                            width: contentColumn.width
                            height: 220
                            ColumnLayout {
                                anchors.fill: parent
                                anchors.margins: 17
                                spacing: 8
                                RowLayout {
                                    Layout.fillWidth: true
                                    Text { text: Ui.text("运行记录"); color: root.textMain; font.pixelSize: 15; font.weight: Font.DemiBold }
                                    Item { Layout.fillWidth: true }
                                    AppButton {
                                        objectName: "copyRunLogsButton"
                                        text: "复制全部"
                                        variant: "link"
                                        onClicked: controller.copyRunLogs()
                                    }
                                }
                                ListView {
                                    id: logList
                                    objectName: "logList"
                                    Layout.fillWidth: true
                                    Layout.fillHeight: true
                                    clip: true
                                    model: controller.logModel
                                    reuseItems: true
                                    cacheBuffer: 120
                                    spacing: 3
                                    onCountChanged: positionViewAtEnd()
                                    ScrollBar.vertical: ScrollBar { policy: ScrollBar.AsNeeded }
                                    delegate: Item {
                                        id: logEntry
                                        objectName: "logRow"
                                        readonly property bool emphasized: level === "warning_emphasis"
                                        readonly property int inset: emphasized ? 6 : 0
                                        width: logList.width
                                        height: Math.max(25, logText.implicitHeight + (emphasized ? 12 : 4))
                                        Rectangle {
                                            objectName: "logWarningBackground"
                                            anchors.fill: parent
                                            visible: logEntry.emphasized
                                            radius: 4
                                            color: Ui.color("warning7")
                                            opacity: 0.14
                                        }
                                        // Width flows from the list to the text; text height
                                        // flows back only to this row. A RowLayout here would
                                        // re-enter height calculation while assigning widths.
                                        Text {
                                            id: logBullet
                                            x: logEntry.inset
                                            width: Math.ceil(implicitWidth)
                                            y: Math.round((parent.height - height) / 2)
                                            text: Ui.text(level === "muted" ? "" : "●")
                                            color: level === "error" ? Ui.color("error1") : level === "warning" || logEntry.emphasized ? Ui.color("warning7") : level === "success" ? Ui.color("accent2") : root.primary
                                            font.pixelSize: 9
                                        }
                                        Text {
                                            id: logTime
                                            x: logBullet.x + logBullet.width + 7
                                            width: Math.ceil(implicitWidth)
                                            y: Math.round((parent.height - height) / 2)
                                            text: Ui.text(time); color: Ui.color("muted7"); font.pixelSize: 10
                                            verticalAlignment: Text.AlignTop
                                        }
                                        TextEdit {
                                            id: logText
                                            objectName: "logText"
                                            x: logTime.x + logTime.width + 7
                                            y: Math.round((parent.height - height) / 2)
                                            width: Math.max(0, parent.width - x - logEntry.inset)
                                            text: Ui.text(model.text)
                                            color: logEntry.emphasized ? Ui.color("warning1") : level === "muted" ? root.textMuted : root.textMain
                                            font.pixelSize: 12
                                            font.weight: logEntry.emphasized ? Font.DemiBold : Font.Normal
                                            wrapMode: TextEdit.Wrap
                                            textFormat: TextEdit.PlainText
                                            readOnly: true
                                            selectByMouse: true
                                            selectByKeyboard: true
                                            persistentSelection: true
                                            selectionColor: Ui.color("selection4")
                                            selectedTextColor: root.textMain
                                            MouseArea {
                                                anchors.fill: parent
                                                acceptedButtons: Qt.RightButton
                                                onClicked: logContextMenu.popup()
                                            }
                                            Menu {
                                                id: logContextMenu
                                                objectName: "logContextMenu"
                                                MenuItem { text: Ui.text("复制"); enabled: logText.selectedText.length > 0; onTriggered: logText.copy() }
                                                MenuItem { text: Ui.text("选择本条"); onTriggered: { logText.forceActiveFocus(); logText.selectAll() } }
                                                MenuItem { text: Ui.text("复制全部记录"); onTriggered: controller.copyRunLogs() }
                                            }
                                        }
                                    }
                                }
                            }
                        }
                        Item { width: contentColumn.width; height: 4 }
                    }
                }
            }

        }
    }

    // Keep the conversation loaded while the shared column shows project files.
    Loader {
        id: aiPanelLoader
        objectName: "aiPanelLoader"
        active: root.aiPanelCreated
        parent: workspaceDrawer
        visible: root.rightPanelTab === "sage" && workspaceDrawer.reservedWidth > 0
        x: 8
        y: utilityTabs.y + utilityTabs.height + 8
        width: workspaceDrawer.panelWidth
        height: Math.max(0, workspaceDrawer.height - y - 8)
        z: 1
        sourceComponent: AiSidePanel {
            requestedOpen: root.aiPanelRequested && workspaceDrawer.opened
            onCloseRequested: root.closeRightPanel()
            onSettingsRequested: aiSettingsDialog.open()
            onDetachRequested: root.openAiWindow()
        }
    }

    Button {
        id: sageLauncher
        objectName: "sageLauncher"
        readonly property real minX: 12
        readonly property real minY: windowChrome.height + 8
        readonly property real rangeX: Math.max(0, root.width - width - minX - 12)
        readonly property real rangeY: Math.max(0, root.height - height - minY - 12)
        // Keep the launcher outside the conversation, including its closing
        // transition. Only an explicit drag changes the saved resting position.
        readonly property bool besidePanel: aiPanelLoader.visible && aiPanelLoader.item !== null && aiPanelLoader.item.visible
        readonly property real maxX: besidePanel ? Math.max(minX, workspaceDrawer.x + aiPanelLoader.x - width - 12) : minX + rangeX
        readonly property real maxY: besidePanel ? Math.max(minY, aiPanelLoader.y + aiPanelLoader.height - height - 12) : minY + rangeY
        property bool moving: false
        property real dragX: 0
        property real dragY: 0
        x: Math.max(minX, Math.min(maxX, moving ? dragX : minX + rangeX * controller.aiLauncherPosition[0]))
        y: Math.max(minY, Math.min(maxY, moving ? dragY : minY + rangeY * controller.aiLauncherPosition[1]))
        width: 68
        height: 76
        z: 25
        padding: 0
        focusPolicy: Qt.StrongFocus
        hoverEnabled: true
        Accessible.name: Ui.text(root.aiAssistantOpen ? "收起 Sage" : "询问 Sage")
        Accessible.description: Ui.text("拖动可移动位置；右键可重置位置。")
        onClicked: root.toggleAiPanel()
        background: Rectangle {
            radius: 12
            color: "transparent"
            border.width: sageLauncher.visualFocus ? 1 : 0
            border.color: root.primary
        }
        contentItem: Column {
            opacity: launcherMouse.pressed && !sageLauncher.moving ? 0.85 : 1
            Image {
                objectName: "sageMascotImage"
                width: 68; height: 60
                source: Qt.resolvedUrl("components/sage-companion.png")
                sourceSize.width: 160; sourceSize.height: 160
                fillMode: Image.PreserveAspectFit
                smooth: true
            }
            Text {
                width: 68; height: 16
                text: "Sage"
                color: root.aiAssistantOpen || launcherMouse.containsMouse ? root.primary : root.textMuted
                font.pixelSize: 11
                horizontalAlignment: Text.AlignHCenter
            }
        }
        MouseArea {
            id: launcherMouse
            objectName: "sageLauncherMouse"
            anchors.fill: parent
            hoverEnabled: true
            acceptedButtons: Qt.LeftButton | Qt.RightButton
            preventStealing: true
            cursorShape: sageLauncher.moving ? Qt.ClosedHandCursor : Qt.PointingHandCursor
            property point startPoint
            property point startPosition
            onPressed: function(mouse) {
                if (mouse.button !== Qt.LeftButton) return
                startPoint = mapToItem(root.contentItem, mouse.x, mouse.y)
                startPosition = Qt.point(sageLauncher.x, sageLauncher.y)
            }
            onPositionChanged: function(mouse) {
                if (!(pressedButtons & Qt.LeftButton)) return
                var point = mapToItem(root.contentItem, mouse.x, mouse.y)
                var dx = point.x - startPoint.x
                var dy = point.y - startPoint.y
                if (!sageLauncher.moving && Math.sqrt(dx * dx + dy * dy) < Qt.styleHints.startDragDistance) return
                sageLauncher.dragX = startPosition.x + dx
                sageLauncher.dragY = startPosition.y + dy
                sageLauncher.moving = true
            }
            onReleased: function(mouse) {
                if (mouse.button === Qt.RightButton) { launcherMenu.popup(mouse.x, mouse.y); return }
                if (sageLauncher.moving) {
                    controller.setAiLauncherPosition(
                        sageLauncher.rangeX > 0 ? (sageLauncher.x - sageLauncher.minX) / sageLauncher.rangeX : 1,
                        sageLauncher.rangeY > 0 ? (sageLauncher.y - sageLauncher.minY) / sageLauncher.rangeY : 1)
                    sageLauncher.moving = false
                } else sageLauncher.clicked()
            }
            onCanceled: sageLauncher.moving = false
        }
        Menu {
            id: launcherMenu
            objectName: "sageLauncherMenu"
            MenuItem {
                objectName: "resetSagePosition"
                text: Ui.text("重置位置")
                onTriggered: controller.setAiLauncherPosition(1, 1)
            }
        }
        ToolTip {
            id: sageTooltip
            visible: !sageLauncher.moving && !launcherMouse.pressed && (launcherMouse.containsMouse || sageLauncher.visualFocus)
            delay: 450
            text: Ui.text(root.aiAssistantOpen ? "收起 Sage" : "询问 Sage") + " (Ctrl+K)"
            x: Math.max(-sageLauncher.x + 4, Math.min((sageLauncher.width - width) / 2, root.width - sageLauncher.x - width - 4))
            y: sageLauncher.y >= height + 8 ? -height - 4 : sageLauncher.height + 4
            padding: 10
            contentItem: Text { text: sageTooltip.text; color: root.textMain; font.pixelSize: 12 }
            background: Rectangle { radius: 12; color: root.surface; border.color: root.border }
        }
    }

    Popup {
        id: projectMenu
        objectName: "projectMenu"
        x: Math.min(root.settledWidth - width - 12, sidebar.width + 8)
        y: 112
        width: 250
        padding: 9
        closePolicy: Popup.CloseOnEscape | Popup.CloseOnPressOutside
        background: Rectangle { radius: 11; color: Ui.color("surface"); border.color: root.border }
        contentItem: ColumnLayout {
            spacing: 4
            AppButton {
                Layout.fillWidth: true
                text: "新建工作项目"
                onClicked: { projectMenu.close(); controller.requestCreateProject() }
            }
            AppButton {
                Layout.fillWidth: true
                text: "打开已有项目"
                onClicked: { projectMenu.close(); controller.openProjectDialog() }
            }
            Rectangle {
                visible: controller.recentProjects.length > 0
                Layout.fillWidth: true
                Layout.preferredHeight: 1
                color: root.border
            }
            Text {
                visible: controller.recentProjects.length > 0
                Layout.fillWidth: true
                text: Ui.text("最近项目")
                color: root.textMuted
                font.pixelSize: 11
                leftPadding: 8
            }
            Repeater {
                model: controller.recentProjects
                delegate: AppButton {
                    Layout.fillWidth: true
                    text: modelData.name
                    variant: "link"
                    onClicked: { projectMenu.close(); controller.openProject(modelData.path) }
                }
            }
        }
    }

    Component {
        id: textFieldComponent
        RowLayout {
            spacing: 10
            Text { Layout.preferredWidth: 145; wrapMode: Text.Wrap; text: Ui.text(field.label); color: root.textMain; font.pixelSize: 13 }
            AppTextField {
                Layout.fillWidth: true
                text: field.value === undefined || field.value === null ? "" : String(field.value)
                placeholderText: Ui.text(field.placeholder || "")
                onTextEdited: controller.setFieldValue(field.id, text)
            }
        }
    }

    Component {
        id: choiceFieldComponent
        RowLayout {
            spacing: 10
            Text { Layout.preferredWidth: 145; wrapMode: Text.Wrap; text: Ui.text(field.label); color: root.textMain; font.pixelSize: 13 }
            AppComboBox {
                id: combo
                Layout.preferredWidth: Math.min(360, Math.max(220, implicitWidth))
                model: field.options || []
                textRole: "label"
                optionDescriptions: field.id === "rename_mode" ? {
                    "按 Excel 原文件名匹配": "将文件的完整原名称与 Excel 中的原文件名列匹配，使用同一行的新名称。",
                    "按 Excel 人名顺序批量重命名": "按 Excel 行顺序分配名称，可在预览中调整对应关系。"
                } : ({})
                currentIndex: root.choiceIndex(field)
                onActivated: controller.setFieldValue(field.id, field.options[index].value)
            }
            Item { Layout.fillWidth: true }
        }
    }

    Component {
        id: checkFieldComponent
        RowLayout {
            spacing: 10
            Item { Layout.preferredWidth: 145; Layout.preferredHeight: 1 }
            AppCheckBox {
                text: field.label
                Layout.fillWidth: true
                Layout.minimumWidth: 0
                implicitHeight: Math.max(28, contentItem.implicitHeight + topPadding + bottomPadding)
                checked: !!field.value
                enabled: !(field.id === "use_ocr_cache" && root.fieldById("library_mode").value === "flat_ocr")
                onToggled: controller.setFieldValue(field.id, checked)
            }
            Item { Layout.fillWidth: true }
        }
    }

    Component {
        id: dateRangeFieldComponent
        RowLayout {
            spacing: 10
            Text { Layout.preferredWidth: 145; wrapMode: Text.Wrap; text: Ui.text(field.label); color: root.textMain; font.pixelSize: 13; Layout.alignment: Qt.AlignTop }
            ColumnLayout {
                Layout.fillWidth: true
                spacing: 6
                RowLayout {
                    Layout.fillWidth: true
                    spacing: 7
                    AppTextField {
                        Layout.preferredWidth: 138
                        text: field.startValue === undefined || field.startValue === null ? "" : String(field.startValue)
                        placeholderText: Ui.text(field.startPlaceholder || "")
                        onTextEdited: controller.setFieldValue(field.startId, text)
                        onEditingFinished: controller.normalizeDateField(field.startId, text)
                    }
                    Text { text: Ui.text("至"); color: root.textMuted; font.pixelSize: 12 }
                    AppTextField {
                        Layout.preferredWidth: 138
                        text: field.endValue === undefined || field.endValue === null ? "" : String(field.endValue)
                        placeholderText: Ui.text(field.endPlaceholder || "")
                        onTextEdited: controller.setFieldValue(field.endId, text)
                        onEditingFinished: controller.normalizeDateField(field.endId, text)
                    }
                    Text { Layout.fillWidth: true; text: Ui.text(field.hint || ""); color: root.textMuted; font.pixelSize: 11; wrapMode: Text.Wrap }
                }
                Flow {
                    Layout.fillWidth: true
                    spacing: 5
                    Repeater {
                        model: field.presets || []
                        delegate: AppButton {
                            text: modelData.label
                            variant: "link"
                            implicitWidth: Math.max(58, contentItem.implicitWidth + 12)
                            implicitHeight: 28
                            onClicked: controller.applyDatePreset(field.presetGroup, modelData.value)
                        }
                    }
                }
                Text {
                    Layout.fillWidth: true
                    readonly property var feedback: controller.selectionFeedback[field.presetGroup + "_range"] || ({})
                    visible: !!feedback.text; text: Ui.text(feedback.text || "")
                    textFormat: Text.PlainText; wrapMode: Text.Wrap
                    color: Ui.color("error"); font.pixelSize: 12
                }
            }
        }
    }

    Component {
        id: materialCollectorTypesComponent
        ColumnLayout {
            spacing: 5

            Rectangle { Layout.fillWidth: true; Layout.preferredHeight: 1; color: root.borderFaint }
            RowLayout {
                Layout.fillWidth: true
                spacing: 8
                Text { Layout.preferredWidth: 66; wrapMode: Text.Wrap; text: Ui.text("指定材料"); color: root.textMain; font.pixelSize: 13 }
                AppButton { text: "全选"; variant: "link"; onClicked: controller.selectAllMaterials() }
                AppButton { text: "取消全选"; variant: "link"; onClicked: controller.clearMaterials() }
                Item { Layout.fillWidth: true }
            }
            RowLayout {
                Layout.fillWidth: true
                Layout.leftMargin: 74
                spacing: 6
                Text { text: Ui.text("常用组合"); color: root.textFaint; font.pixelSize: 11 }
                AppComboBox {
                    id: materialCollectorPresetCombo
                    Layout.preferredWidth: 160
                    model: controller.materialPresets
                    currentIndex: Math.max(0, controller.materialPresets.indexOf(controller.materialPresetName))
                    onActivated: controller.setMaterialPresetName(currentText)
                }
                AppButton { text: "应用"; variant: "link"; onClicked: controller.applyMaterialPreset(materialCollectorPresetCombo.currentText) }
                PresetMenuButton { backend: controller; presetName: materialCollectorPresetCombo.currentText }
                Item { Layout.fillWidth: true }
            }
            Text { Layout.fillWidth: true; Layout.leftMargin: 74; text: Ui.text("选择组合后，点击“应用”才会更改材料勾选。"); color: root.textFaint; font.pixelSize: 11; wrapMode: Text.Wrap }
            Flow {
                Layout.fillWidth: true
                Layout.leftMargin: 74
                spacing: 10
                Repeater {
                    model: field.options || []
                    delegate: AppCheckBox {
                        text: modelData.label
                        checked: modelData.selected
                        onToggled: controller.toggleMaterial(modelData.value, checked)
                    }
                }
            }
            RowLayout {
                Layout.fillWidth: true
                Layout.leftMargin: 74
                spacing: 6
                Text { text: Ui.text("自定义材料"); color: root.textFaint; font.pixelSize: 11 }
                AppComboBox {
                    id: materialCollectorCustomCombo
                    visible: controller.customMaterials.length > 0
                    Layout.preferredWidth: 160
                    model: controller.customMaterials
                }
                AppButton { text: "添加材料"; variant: "link"; onClicked: controller.requestAddCustomMaterial() }
                AppButton {
                    visible: controller.customMaterials.length > 0
                    text: "删除材料"
                    variant: "link"
                    onClicked: controller.requestDeleteCustomMaterial(materialCollectorCustomCombo.currentText)
                }
                Item { Layout.fillWidth: true }
            }
            Text {
                Layout.fillWidth: true
                Layout.leftMargin: 74
                text: Ui.text("自定义材料和预设会保存在本机；应用组合后仍可继续增减勾选。")
                color: root.textFaint
                font.pixelSize: 11
                wrapMode: Text.Wrap
            }
        }
    }

    Component {
        id: materialsFieldComponent
        ColumnLayout {
            spacing: 7
            RowLayout {
                Layout.fillWidth: true
                Text { Layout.preferredWidth: 145; wrapMode: Text.Wrap; text: Ui.text("常用组合"); color: root.textMain; font.pixelSize: 13 }
                AppComboBox {
                    id: presetCombo
                    Layout.preferredWidth: 190
                    model: controller.materialPresets
                    currentIndex: Math.max(0, controller.materialPresets.indexOf(controller.materialPresetName))
                    onActivated: controller.setMaterialPresetName(currentText)
                }
                AppButton { text: "应用"; variant: "link"; onClicked: controller.applyMaterialPreset(presetCombo.currentText) }
                PresetMenuButton { backend: controller; presetName: presetCombo.currentText }
                Item { Layout.fillWidth: true }
            }
            Text { Layout.fillWidth: true; Layout.leftMargin: 145; text: Ui.text("选择组合后，点击“应用”才会更改材料勾选。"); color: root.textFaint; font.pixelSize: 11; wrapMode: Text.Wrap }
            RowLayout {
                Layout.fillWidth: true
                Text { Layout.preferredWidth: 145; wrapMode: Text.Wrap; text: Ui.text(field.label); color: root.textMain; font.pixelSize: 13 }
                AppButton { text: "全选"; variant: "link"; onClicked: controller.selectAllMaterials() }
                AppButton { text: "取消全选"; variant: "link"; onClicked: controller.clearMaterials() }
                Item { Layout.fillWidth: true }
            }
            RowLayout {
                Layout.fillWidth: true
                Item { Layout.preferredWidth: 145; Layout.preferredHeight: 1 }
                AppButton { text: "添加材料"; variant: "link"; onClicked: controller.requestAddCustomMaterial() }
                AppComboBox {
                    id: customMaterialCombo
                    visible: controller.customMaterials.length > 0
                    Layout.preferredWidth: 150
                    model: controller.customMaterials
                }
                AppButton {
                    visible: controller.customMaterials.length > 0
                    text: "删除自定义材料"
                    variant: "link"
                    onClicked: controller.requestDeleteCustomMaterial(customMaterialCombo.currentText)
                }
                Item { Layout.fillWidth: true }
            }
            Flow {
                Layout.fillWidth: true
                spacing: 4
                Repeater {
                    model: field.options || []
                    delegate: AppCheckBox {
                        text: modelData.label
                        checked: modelData.selected
                        onToggled: controller.toggleMaterial(modelData.value, checked)
                    }
                }
            }
        }
    }

    // Stable native drag source, independent of virtualized rows and the popup.
    Item {
        id: workspaceDragProxy
        property var transfer: ({})
        property bool dragging: false
        Drag.dragType: Drag.None
        Drag.supportedActions: Qt.CopyAction
        Drag.proposedAction: Qt.CopyAction
        Drag.mimeData: ({"text/uri-list": transfer.url || "",
                         "application/x-hr-toolkit-workspace": transfer.token || ""})
        Drag.imageSource: "components/copy-simple.png"
        function start(path) {
            if (dragging) return
            transfer = controller.beginWorkspaceTransfer(path)
            if (!transfer.token) return
            dragging = true
            // Drag.None disables automatic startup, but startDrag still
            // requires the attached drag source to be active first.
            Drag.active = true
            try {
                Drag.startDrag(Qt.CopyAction)
            } finally {
                // Also recover if native startup fails without dragFinished.
                finish()
            }
        }
        function finish() {
            if (!dragging) return
            Drag.active = false
            controller.endWorkspaceTransfer(transfer.token || "")
            transfer = ({})
            dragging = false
        }
        Drag.onDragFinished: finish()
    }

    WorkspaceSidePanel {
        id: workspaceDrawer
        objectName: "workspaceDrawer"
        parent: workspaceLayout
        requestedOpen: root.aiPanelRequested || (root.rightPanelTab === "files" && controller.workspaceExpanded && controller.hasProject)
        onRequestedOpenChanged: if (requestedOpen && !root.sidePanelFits) root.closeRightPanel()
        minimumPanelWidth: 400
        maximumPanelWidth: 480
        preferredPanelWidth: 480
        availableWidth: workspaceLayout.width - (sidebar.pinned ? sidebar.width : 0)
        liveAvailableWidth: workspaceLayout.width - sidebar.reservedWidth
        onOpenRequested: root.openProjectPanel()
        onCloseRequested: root.closeRightPanel()
        onOpenedChanged: {
            if (!opened && autoCollapsed && requestedOpen) root.closeRightPanel()
            if (!opened) {
                workspaceAddMenu.close()
                workspaceUseMenu.close()
                if (activeFocus) mainScroll.forceActiveFocus()
            }
        }
        RowLayout {
            id: utilityTabs
            objectName: "utilityTabs"
            x: 8; y: 8
            width: workspaceDrawer.panelWidth
            height: 34
            spacing: 4
            visible: workspaceDrawer.reservedWidth > 0
            AppButton {
                objectName: "projectFilesTab"
                Layout.fillWidth: true
                text: "项目文件"
                enabled: controller.hasProject
                variant: root.rightPanelTab === "files" ? "tonal" : "link"
                Accessible.checkable: true
                Accessible.checked: root.rightPanelTab === "files"
                onClicked: root.openProjectPanel()
            }
            AppButton {
                objectName: "sageTab"
                Layout.fillWidth: true
                text: "Sage"
                variant: root.rightPanelTab === "sage" ? "tonal" : "link"
                Accessible.checkable: true
                Accessible.checked: root.rightPanelTab === "sage"
                onClicked: root.openSagePanel()
            }
        }
        Rectangle {
            id: workspaceSurface
            objectName: "workspaceSurface"
            visible: workspaceDrawer.reservedWidth > 0 && root.rightPanelTab === "files"
            x: 8; y: utilityTabs.y + utilityTabs.height + 8
            width: workspaceDrawer.panelWidth
            height: Math.max(0, workspaceDrawer.height - y - 8)
            color: root.surface; border.color: root.border; radius: 12
            ColumnLayout {
                anchors.fill: parent
                anchors.leftMargin: 16
                anchors.rightMargin: 16
                anchors.topMargin: 18
                anchors.bottomMargin: 14
                spacing: 8
                Text { Layout.fillWidth: true; text: controller.projectName; color: root.primary; font.pixelSize: 14; font.weight: Font.DemiBold; elide: Text.ElideRight; horizontalAlignment: Text.AlignHCenter }
                Rectangle {
                    Layout.fillWidth: true
                    Layout.preferredHeight: 34
                    radius: 8
                    color: Ui.color("surface")
                    border.color: root.border
                    RowLayout {
                        anchors.fill: parent
                        anchors.margins: 2
                        spacing: 2
                        Repeater {
                            model: [{value: "all", label: "全部文件"}, {value: "tool", label: "当前功能"}]
                            Button {
                                id: scopeButton
                                readonly property bool selected: controller.workspaceScope === modelData.value
                                Layout.fillWidth: true
                                Layout.fillHeight: true
                                Layout.preferredWidth: 1
                                text: Ui.text(modelData.label)
                                hoverEnabled: true
                                focusPolicy: Qt.StrongFocus
                                Accessible.checkable: true
                                Accessible.checked: selected
                                onClicked: controller.setWorkspaceScope(modelData.value)
                                contentItem: Text {
                                    text: Ui.text(scopeButton.text)
                                    color: scopeButton.selected ? root.primary : root.textMuted
                                    font.pixelSize: 13
                                    font.weight: scopeButton.selected ? Font.DemiBold : Font.Normal
                                    horizontalAlignment: Text.AlignHCenter
                                    verticalAlignment: Text.AlignVCenter
                                }
                                background: Rectangle {
                                    radius: 6
                                    color: scopeButton.selected ? root.primarySoft : scopeButton.hovered ? root.navHover : "transparent"
                                    border.width: scopeButton.visualFocus ? 1 : 0
                                    border.color: root.primary
                                }
                            }
                        }
                    }
                }
                AppTextField {
                    id: workspaceSearchField
                    objectName: "workspaceSearchField"
                    Layout.fillWidth: true
                    Layout.preferredHeight: 38
                    leftPadding: 38
                    placeholderText: Ui.text("输入文件名")
                    Accessible.name: Ui.text("按文件名查找")
                    onTextEdited: controller.setWorkspaceSearch(text)
                    background: Rectangle {
                        radius: 9
                        color: Ui.color("surface11")
                        border.color: workspaceSearchField.activeFocus ? root.primary : Ui.color("surface2")
                    }
                    ThemedImage {
                        anchors.left: parent.left
                        anchors.leftMargin: 12
                        anchors.verticalCenter: parent.verticalCenter
                        width: 16; height: 16
                        source: Qt.resolvedUrl("components/magnifying-glass.png")
                        sourceSize.width: 32; sourceSize.height: 32
                        opacity: 0.45
                    }
                }
                RowLayout {
                    Layout.fillWidth: true
                    Layout.topMargin: 2
                    spacing: 7
                    AppButton {
                        id: workspaceAddButton
                        text: "添加"
                        variant: "link"
                        Layout.preferredWidth: Math.max(66, implicitWidth)
                        Accessible.name: Ui.text(text)
                        enabled: controller.projectWritable && !controller.busy && !controller.workspaceBusy
                        onClicked: workspaceAddMenu.open()
                        contentItem: RowLayout {
                            spacing: 7
                            ThemedImage { Layout.preferredWidth: 14; Layout.preferredHeight: 14; source: Qt.resolvedUrl("components/plus-circle-green.png"); sourceSize.width: 28; sourceSize.height: 28; opacity: workspaceAddButton.enabled ? 1 : 0.3 }
                            Text { Layout.fillWidth: true; text: Ui.text(workspaceAddButton.text); color: workspaceAddButton.enabled ? root.primary : root.textDisabled; font.pixelSize: 13; verticalAlignment: Text.AlignVCenter }
                        }
                    }
                    AppButton { visible: controller.workspaceBusy; text: "取消导入"; variant: "link"; onClicked: controller.cancelWorkspaceImport() }
                    Item { Layout.fillWidth: true }
                    AppButton {
                        id: workspaceRefreshButton
                        text: "刷新"
                        variant: "link"
                        Layout.preferredWidth: Math.max(66, implicitWidth)
                        Accessible.name: Ui.text(text)
                        onClicked: controller.refreshWorkspace()
                        contentItem: RowLayout {
                            spacing: 7
                            ThemedImage { Layout.preferredWidth: 14; Layout.preferredHeight: 14; source: Qt.resolvedUrl("components/arrows-clockwise-green.png"); sourceSize.width: 28; sourceSize.height: 28 }
                            Text { Layout.fillWidth: true; text: Ui.text(workspaceRefreshButton.text); color: root.primary; font.pixelSize: 13; verticalAlignment: Text.AlignVCenter }
                        }
                    }
                }
                Rectangle { Layout.fillWidth: true; Layout.preferredHeight: 1; color: root.borderFaint }
                Item {
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    ListView {
                        id: workspaceList
                        objectName: "workspaceList"
                        anchors.fill: parent
                        clip: true
                        model: controller.workspaceModel
                        reuseItems: true
                        cacheBuffer: 128
                        boundsBehavior: Flickable.StopAtBounds
                        currentIndex: -1
                        property int activeDelegateCount: 0
                        function keepRowVisible(row) {
                            Qt.callLater(function() {
                                if (workspaceList.count <= 0)
                                    return
                                var safeRow = Math.max(0, Math.min(row, workspaceList.count - 1))
                                workspaceList.positionViewAtIndex(safeRow, ListView.Contain)
                            })
                        }
                        ScrollBar.vertical: ScrollBar { policy: ScrollBar.AsNeeded }
                        delegate: Rectangle {
                            Component.onCompleted: workspaceList.activeDelegateCount += 1
                            Component.onDestruction: workspaceList.activeDelegateCount -= 1
                            width: workspaceList.width
                            height: 32
                            radius: 6
                            color: controller.workspaceSelectedPath === path ? root.primarySoft : (workspaceMouse.containsMouse ? root.navHover : "transparent")
                            RowLayout {
                                anchors.fill: parent
                                anchors.leftMargin: 5 + depth * 15
                                anchors.rightMargin: 5
                                spacing: 4
                                Text { Layout.preferredWidth: 12; text: Ui.text(isDir ? (expanded ? "▾" : "▸") : ""); color: root.textMuted; font.pixelSize: 10 }
                                ToolIcon { Layout.preferredWidth: 16; Layout.preferredHeight: 16; iconId: isDir ? "folder_rename" : "social_security"; strokeColor: isDir ? root.primary : Ui.color("link5"); lineWidth: 1.15 }
                                Text { Layout.fillWidth: true; text: name; color: root.textMain; font.pixelSize: 12; elide: Text.ElideMiddle; verticalAlignment: Text.AlignVCenter }
                            }
                            MouseArea {
                                id: workspaceMouse
                                anchors.fill: parent
                                hoverEnabled: true
                                acceptedButtons: Qt.LeftButton
                                property point pressPoint
                                property string pressedPath: ""
                                property bool startedDrag: false
                                onPressed: function(mouse) {
                                    pressPoint = Qt.point(mouse.x, mouse.y)
                                    pressedPath = path
                                    startedDrag = false
                                }
                                onPositionChanged: function(mouse) {
                                    if (!pressed || startedDrag) return
                                    var dx = Math.abs(mouse.x - pressPoint.x)
                                    var dy = Math.abs(mouse.y - pressPoint.y)
                                    // Vertical gestures remain available to the list.
                                    if (dx > Qt.styleHints.startDragDistance && dx > dy) {
                                        startedDrag = true
                                        workspaceDragProxy.start(pressedPath)
                                    }
                                }
                                onClicked: {
                                    if (startedDrag) return
                                    controller.selectWorkspaceRow(index)
                                }
                                onDoubleClicked: if (!startedDrag) controller.openWorkspaceRow(index)
                                ToolTip.visible: containsMouse && !pressed
                                ToolTip.text: Ui.text(path + "\n向左拖入资料区；单击选中，双击打开")
                                ToolTip.delay: 600
                            }
                            MouseArea {
                                x: 3 + depth * 15; width: 20; height: parent.height
                                visible: isDir
                                cursorShape: Qt.PointingHandCursor
                                onClicked: {
                                    controller.toggleWorkspaceRow(index)
                                    workspaceList.keepRowVisible(index)
                                }
                            }
                        }
                    }
                    Text {
                        anchors.centerIn: parent
                        visible: workspaceList.count === 0
                        text: Ui.text(controller.hasProject ? "当前范围还没有项目文件" : "请先打开工作项目")
                        color: root.textFaint
                        font.pixelSize: 12
                        horizontalAlignment: Text.AlignHCenter
                    }
                }
                Card {
                    Layout.fillWidth: true
                    Layout.preferredHeight: Math.max(126, workspaceSelectionContent.implicitHeight + 20)
                    color: root.surface
                    ColumnLayout {
                        id: workspaceSelectionContent
                        anchors.fill: parent
                        anchors.margins: 10
                        spacing: 3
                        Text { Layout.fillWidth: true; text: Ui.text(controller.workspaceSelectionAvailable ? controller.workspaceSelectedName : "选择项目文件"); color: root.textMain; font.pixelSize: 13; font.weight: Font.DemiBold; elide: Text.ElideMiddle }
                        Text { Layout.fillWidth: true; text: Ui.text(controller.workspaceSelectedDetail); color: root.textMuted; font.pixelSize: 11; wrapMode: Text.Wrap; maximumLineCount: 3; elide: Text.ElideRight }
                        AppButton {
                            text: "带入当前工具"; variant: "link"
                            enabled: controller.selectionEnabled && controller.workspaceSelectionAvailable
                            onClicked: {
                                workspaceUseMenu.inputAllowed = controller.canUseWorkspaceSelection("input")
                                workspaceUseMenu.supportAllowed = controller.canUseWorkspaceSelection("support")
                                workspaceUseMenu.open()
                            }
                        }
                        RowLayout {
                            Layout.fillWidth: true
                            AppButton { text: "打开"; variant: "link"; enabled: controller.workspaceSelectionAvailable; onClicked: controller.launchWorkspaceSelection() }
                            AppButton { text: "定位"; variant: "link"; enabled: controller.workspaceSelectionAvailable; onClicked: controller.revealWorkspaceSelection() }
                            AppButton { text: "移到回收站"; variant: "link"; enabled: controller.workspaceSelectionAvailable && controller.projectWritable && !controller.busy && !controller.workspaceBusy; onClicked: controller.requestMoveSelectedBatchToTrash() }
                            Item { Layout.fillWidth: true }
                            AppButton { text: "回收站"; variant: "link"; enabled: controller.hasProject; onClicked: { controller.requestProjectTrash(); trashDialog.open() } }
                        }
                    }
                }
            }
        }
    }

    Popup {
        id: workspaceUseMenu
        property bool inputAllowed: false
        property bool supportAllowed: false
        x: Math.min(root.width - width - 8, workspaceDrawer.x + 24)
        y: Math.max(8, root.height - height - 130)
        width: Math.min(308, root.width - 32); padding: 8
        closePolicy: Popup.CloseOnEscape | Popup.CloseOnPressOutside
        background: Rectangle { color: root.surface; radius: 9; border.color: root.border }
        contentItem: ColumnLayout {
            AppButton { Layout.fillWidth: true; text: "添加为待处理资料"; enabled: workspaceUseMenu.inputAllowed && controller.selectionEnabled; onClicked: { workspaceUseMenu.close(); controller.useWorkspaceSelection("input") } }
            AppButton { Layout.fillWidth: true; text: "设为" + controller.supportLabel; visible: controller.hasSupportField; enabled: workspaceUseMenu.supportAllowed && controller.selectionEnabled; onClicked: { workspaceUseMenu.close(); controller.useWorkspaceSelection("support") } }
            Text { Layout.fillWidth: true; wrapMode: Text.Wrap; font.pixelSize: 11; color: root.textMuted; text: Ui.text("仅带入选择，不移动原件。灰色选项表示该区域不支持此项。") }
        }
    }

    Popup {
        id: workspaceAddMenu
        x: Math.min(root.width - width - 8, workspaceAddButton.mapToItem(root.contentItem, 0, 0).x)
        y: Math.min(root.height - height - 8, workspaceAddButton.mapToItem(root.contentItem, 0, workspaceAddButton.height).y)
        width: 210
        padding: 8
        closePolicy: Popup.CloseOnEscape | Popup.CloseOnPressOutside
        enter: Transition {}
        exit: Transition {}
        background: Rectangle { color: root.surface; radius: 9; border.color: root.border }
        contentItem: ColumnLayout {
            spacing: 3
            AppButton { Layout.fillWidth: true; text: "选择处理文件"; onClicked: { workspaceAddMenu.close(); controller.importWorkspaceFiles() } }
            AppButton { Layout.fillWidth: true; text: "选择处理文件夹"; onClicked: { workspaceAddMenu.close(); controller.importWorkspaceFolder() } }
        }
    }

    Drawer {
        id: historyDrawer
        edge: Qt.RightEdge
        width: Math.min(900, Math.max(650, root.settledWidth * 0.82))
        height: root.settledHeight
        modal: true
        interactive: true
        closePolicy: Popup.CloseOnEscape | Popup.CloseOnPressOutside
        background: Rectangle { color: Ui.color("surface15"); border.color: root.border }

        ColumnLayout {
            anchors.fill: parent
            anchors.margins: 16
            spacing: 10
            RowLayout {
                Layout.fillWidth: true
                ColumnLayout {
                    Layout.fillWidth: true; spacing: 2
                    Text { text: Ui.text("旧版记录"); color: root.textMain; font.pixelSize: 19; font.weight: Font.DemiBold }
                    Text { text: Ui.text("查看升级前保存的上传资料和结果；新处理记录请在项目文件中查看。"); color: root.textMuted; font.pixelSize: 11; wrapMode: Text.Wrap; Layout.fillWidth: true }
                }
                AppButton { text: "关闭"; variant: "link"; onClicked: historyDrawer.close() }
            }
            RowLayout {
                Layout.fillWidth: true; spacing: 7
                AppTextField {
                    id: historySearch
                    Layout.fillWidth: true
                    placeholderText: Ui.text("按功能或文件名查找")
                    selectByMouse: true
                    onAccepted: controller.refreshHistory(text, historyTool.currentValue, historyDate.currentText)
                }
                AppComboBox {
                    id: historyTool
                    Layout.preferredWidth: 155
                    model: controller.historyToolOptions
                    textRole: "label"
                    valueRole: "value"
                }
                AppComboBox { id: historyDate; Layout.preferredWidth: 125; model: controller.historyDateOptions }
                AppButton { text: "查找"; onClicked: controller.refreshHistory(historySearch.text, historyTool.currentValue, historyDate.currentText) }
            }
            Text { Layout.fillWidth: true; text: Ui.text(controller.historyMessage); color: root.textMuted; font.pixelSize: 11; wrapMode: Text.Wrap }
            RowLayout {
                Layout.fillWidth: true
                Layout.fillHeight: true
                spacing: 10
                Card {
                    Layout.preferredWidth: Math.max(300, historyDrawer.width * 0.47)
                    Layout.fillHeight: true
                    color: Ui.color("surface12")
                    ListView {
                        id: historyList
                        anchors.fill: parent
                        anchors.margins: 8
                        clip: true
                        model: controller.historyModel
                        reuseItems: true
                        cacheBuffer: 168
                        currentIndex: count > 0 ? 0 : -1
                        ScrollBar.vertical: ScrollBar { policy: ScrollBar.AsNeeded }
                        delegate: Rectangle {
                            width: historyList.width
                            height: 76
                            radius: 8
                            color: historyList.currentIndex === index ? Ui.color("selection9") : (historyMouse.containsMouse ? Ui.color("border14") : "transparent")
                            ColumnLayout {
                                anchors.fill: parent; anchors.margins: 8; spacing: 2
                                RowLayout {
                                    Layout.fillWidth: true
                                    Text { Layout.fillWidth: true; text: Ui.text(tool); color: root.textMain; font.pixelSize: 13; font.weight: Font.DemiBold; elide: Text.ElideRight }
                                    Text { text: Ui.text(status); color: status === "已完成" ? root.primary : Ui.color("warning3"); font.pixelSize: 10 }
                                }
                                Text { Layout.fillWidth: true; text: Ui.text(time + " · " + inputs); color: root.textMuted; font.pixelSize: 10; elide: Text.ElideMiddle }
                                Text { Layout.fillWidth: true; text: Ui.text("结果：" + outputs); color: root.textMuted; font.pixelSize: 10; elide: Text.ElideMiddle }
                            }
                            MouseArea {
                                id: historyMouse; anchors.fill: parent; hoverEnabled: true; cursorShape: Qt.PointingHandCursor
                                onClicked: { historyList.currentIndex = index; controller.selectHistoryRow(index) }
                            }
                        }
                    }
                }
                Card {
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    ColumnLayout {
                        anchors.fill: parent; anchors.margins: 16; spacing: 10
                        Text { Layout.fillWidth: true; text: Ui.text(controller.historyDetail.title || "选择一条记录查看详情"); color: root.textMain; font.pixelSize: 15; font.weight: Font.DemiBold; wrapMode: Text.Wrap }
                        Text { Layout.fillWidth: true; Layout.fillHeight: true; text: Ui.text(controller.historyDetail.body || "这里用于查看升级前由旧版本保存的处理记录。"); color: root.textMuted; font.pixelSize: 12; wrapMode: Text.Wrap; verticalAlignment: Text.AlignTop }
                        Flow {
                            Layout.fillWidth: true; spacing: 6
                            AppButton { text: "打开结果"; enabled: !!controller.historyDetail.canOpenOutput; onClicked: controller.openHistoryOutput() }
                            AppButton { text: "打开上传资料"; enabled: !!controller.historyDetail.canOpenInput; onClicked: controller.openHistoryInput() }
                            AppButton { text: "再次使用"; enabled: !!controller.historyDetail.canReuse; onClicked: controller.reuseHistory() }
                            AppButton { text: "移到回收站"; enabled: !!controller.historyDetail.canDelete; variant: "link"; onClicked: controller.requestMoveHistoryToTrash() }
                        }
                    }
                }
            }
            RowLayout {
                Layout.fillWidth: true
                AppButton { text: "打开归档资料"; variant: "link"; onClicked: controller.openHistoryRoot() }
                AppButton { text: "打开回收站"; variant: "link"; onClicked: controller.openHistoryTrash() }
                AppButton { text: "重新整理记录"; enabled: !controller.historyBusy; variant: "link"; onClicked: controller.rebuildHistoryIndex() }
                Item { Layout.fillWidth: true }
                AppButton { text: "上一页"; enabled: controller.historyHasPrevious && !controller.historyBusy; onClicked: controller.changeHistoryPage(-1) }
                Text { text: Ui.text(controller.historyPageText); color: root.textMuted; font.pixelSize: 11 }
                AppButton { text: "下一页"; enabled: controller.historyHasNext && !controller.historyBusy; onClicked: controller.changeHistoryPage(1) }
            }
        }
    }

    AppDialog {
        id: trashDialog
        modal: true
        anchors.centerIn: Overlay.overlay
        width: Math.min(780, root.settledWidth - 42)
        height: Math.min(610, root.settledHeight - 42)
        title: Ui.text("项目回收站")
        closePolicy: controller.trashBusy ? Popup.NoAutoClose : Popup.CloseOnEscape
        closeText: "关闭"
        contentItem: ColumnLayout {
            spacing: 9
            Text { Layout.fillWidth: true; text: Ui.text("这里保存从当前项目移走的完整处理批次；恢复时不会覆盖已有资料。"); color: root.textMuted; font.pixelSize: 11; wrapMode: Text.Wrap }
            AppTextField {
                Layout.fillWidth: true; placeholderText: Ui.text("查找已移除的批次"); selectByMouse: true
                onTextEdited: controller.setTrashSearch(text)
            }
            RowLayout {
                Layout.fillWidth: true; Layout.fillHeight: true; spacing: 10
                Card {
                    Layout.preferredWidth: Math.max(290, trashDialog.availableWidth * 0.48)
                    Layout.fillHeight: true; color: Ui.color("surface12")
                    ListView {
                        id: trashList
                        anchors.fill: parent; anchors.margins: 8; clip: true
                        model: controller.trashModel; reuseItems: true; cacheBuffer: 150
                        currentIndex: controller.trashSelectedRow
                        ScrollBar.vertical: ScrollBar { policy: ScrollBar.AsNeeded }
                        delegate: Rectangle {
                            width: trashList.width; height: 86; radius: 8
                            color: trashList.currentIndex === index ? Ui.color("selection9") : (trashMouse.containsMouse ? Ui.color("border14") : "transparent")
                            ColumnLayout {
                                anchors.fill: parent; anchors.margins: 8; spacing: 2
                                Text { Layout.fillWidth: true; text: Ui.text(title); color: root.textMain; font.pixelSize: 12; font.weight: Font.DemiBold; elide: Text.ElideRight }
                                Text { Layout.fillWidth: true; text: Ui.text(tool) + " · " + Ui.text(status); color: root.textMuted; font.pixelSize: 10; elide: Text.ElideRight }
                                Text { Layout.fillWidth: true; text: Ui.text("移入：" + deletedAt); color: root.textMuted; font.pixelSize: 10 }
                                Text { Layout.fillWidth: true; text: Ui.text(counts + " · " + size); color: root.textMuted; font.pixelSize: 10; elide: Text.ElideRight }
                            }
                            MouseArea { id: trashMouse; anchors.fill: parent; hoverEnabled: true; cursorShape: Qt.PointingHandCursor; onClicked: controller.selectTrashRow(index) }
                        }
                    }
                }
                Card {
                    Layout.fillWidth: true; Layout.fillHeight: true
                    ColumnLayout {
                        anchors.fill: parent; anchors.margins: 16; spacing: 10
                        Text { text: Ui.text(controller.trashSelectedId ? "恢复到当前项目" : "请选择处理批次"); color: root.textMain; font.pixelSize: 15; font.weight: Font.DemiBold }
                        Text { Layout.fillWidth: true; text: Ui.text(controller.trashSelectedId ? "系统会核对完整清单并恢复到原业务目录；如有同名批次会自动使用新名称。" : "回收站为空，或当前筛选没有匹配结果。"); color: root.textMuted; font.pixelSize: 12; wrapMode: Text.Wrap }
                        Item { Layout.fillHeight: true }
                        AppButton { Layout.fillWidth: true; text: controller.trashBusy ? "正在处理…" : "恢复到项目"; enabled: !!controller.trashSelectedId && controller.projectWritable && !controller.trashBusy && !controller.busy && !controller.workspaceBusy; variant: "primary"; onClicked: controller.restoreSelectedTrash() }
                    }
                }
            }
        }
    }

    AppDialog {
        id: helpDialog
        showCloseButton: true
        objectName: "helpDialog"
        modal: true
        anchors.centerIn: Overlay.overlay
        width: Math.min(860, root.settledWidth - 48)
        height: Math.min(620, root.settledHeight - 48)
        title: Ui.text("使用教程")
        closeText: "关闭"
        property var selectedItem: ({ "toolId": "", "mode": "", "label": "", "lines": [] })

        function selectCurrentTutorial() {
            var wantedTool = controller.currentTool
            var wantedMode = (wantedTool === "personnel_change_merge" || wantedTool === "archive_import") ? controller.currentVariant : ""
            var firstItem = null
            for (var groupIndex = 0; groupIndex < controller.tutorialGroups.length; ++groupIndex) {
                var items = controller.tutorialGroups[groupIndex].items || []
                for (var itemIndex = 0; itemIndex < items.length; ++itemIndex) {
                    var item = items[itemIndex]
                    if (firstItem === null)
                        firstItem = item
                    if (String(item.toolId) === wantedTool && String(item.mode || "") === wantedMode) {
                        selectedItem = item
                        return
                    }
                }
            }
            if (firstItem !== null)
                selectedItem = firstItem
        }

        function isSelected(item) {
            return String(selectedItem.toolId || "") === String(item.toolId || "")
                    && String(selectedItem.mode || "") === String(item.mode || "")
        }

        onOpened: selectCurrentTutorial()

        contentItem: RowLayout {
            spacing: 16

            Rectangle {
                Layout.preferredWidth: 190
                Layout.fillHeight: true
                radius: 9
                color: root.surfaceAlt
                border.color: root.borderFaint

                ScrollView {
                    id: tutorialNavigation
                    anchors.fill: parent
                    anchors.margins: 8
                    clip: true
                    contentWidth: availableWidth
                    ScrollBar.horizontal.policy: ScrollBar.AlwaysOff

                    Column {
                        width: tutorialNavigation.availableWidth
                        spacing: 8
                        Repeater {
                            model: controller.tutorialGroups
                            delegate: Column {
                                property var groupData: modelData
                                width: parent.width
                                spacing: 2
                                Text {
                                    width: parent.width
                                    leftPadding: 8
                                    topPadding: 5
                                    bottomPadding: 3
                                    text: Ui.text(groupData.name)
                                    color: root.textDisabled
                                    font.pixelSize: 11
                                    font.weight: Font.DemiBold
                                }
                                Repeater {
                                    model: groupData.items
                                    delegate: Rectangle {
                                        width: parent.width
                                        height: 31
                                        radius: 7
                                        color: helpDialog.isSelected(modelData) ? root.navSelected : (tutorialItemMouse.containsMouse ? root.navHover : "transparent")
                                        Row {
                                            anchors.fill: parent
                                            anchors.leftMargin: 8
                                            spacing: 7
                                            Item {
                                                width: 17
                                                height: parent.height
                                                ToolIcon {
                                                    anchors.centerIn: parent
                                                    width: 15
                                                    height: 15
                                                    iconId: modelData.toolId
                                                    strokeColor: helpDialog.isSelected(modelData) ? root.primary : root.textMuted
                                                    lineWidth: 1.15
                                                }
                                            }
                                            Text {
                                                width: parent.width - 32
                                                height: parent.height
                                                text: Ui.text(modelData.label)
                                                color: helpDialog.isSelected(modelData) ? root.primary : root.textMain
                                                font.pixelSize: 12
                                                font.weight: helpDialog.isSelected(modelData) ? Font.DemiBold : Font.Normal
                                                verticalAlignment: Text.AlignVCenter
                                                elide: Text.ElideRight
                                            }
                                        }
                                        MouseArea {
                                            id: tutorialItemMouse
                                            anchors.fill: parent
                                            hoverEnabled: true
                                            cursorShape: Qt.PointingHandCursor
                                            onClicked: helpDialog.selectedItem = modelData
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }

            Card {
                Layout.fillWidth: true
                Layout.fillHeight: true
                color: root.surface

                ScrollView {
                    id: tutorialContentScroll
                    anchors.fill: parent
                    anchors.margins: 18
                    clip: true
                    contentWidth: availableWidth
                    ScrollBar.horizontal.policy: ScrollBar.AlwaysOff

                    Column {
                        width: tutorialContentScroll.availableWidth
                        spacing: 11
                        Text {
                            width: parent.width
                            text: Ui.text(helpDialog.selectedItem.label || "")
                            color: root.textMain
                            font.pixelSize: 17
                            font.weight: Font.DemiBold
                            bottomPadding: 3
                        }
                        Repeater {
                            model: helpDialog.selectedItem.lines || []
                            delegate: Text {
                                width: parent.width
                                text: Ui.text(modelData.text)
                                color: modelData.style === "warning" ? Ui.color("warning5") : root.textMain
                                font.pixelSize: 13
                                font.weight: modelData.style === "strong" || modelData.style === "warning" ? Font.DemiBold : Font.Normal
                                wrapMode: Text.Wrap
                                textFormat: Text.PlainText
                                lineHeight: 1.22
                            }
                        }
                    }
                }
            }
        }
    }

    AppDialog {
        id: textInputDialog
        modal: true
        anchors.centerIn: Overlay.overlay
        width: Math.min(500, root.settledWidth - 48)
        property string promptText: ""
        property string actionToken: ""
        title: Ui.text("输入")
        acceptText: "确定"
        rejectText: "取消"
        onAccepted: controller.submitTextAction(actionToken, textInputField.text)
        contentItem: ColumnLayout {
            spacing: 9
            Text { Layout.fillWidth: true; text: Ui.text(textInputDialog.promptText); color: root.textMuted; font.pixelSize: 12; wrapMode: Text.Wrap }
            AppTextField { id: textInputField; Layout.fillWidth: true; selectByMouse: true }
        }
        function request(titleText, prompt, initialValue, token) {
            title = titleText
            promptText = prompt
            actionToken = token
            textInputField.text = initialValue
            open()
            textInputField.forceActiveFocus()
            textInputField.selectAll()
        }
    }

    ReleaseNotesDialog {
        id: releaseNotesDialog
        iconSource: controller.updateIconSource
        onDismissed: controller.closeReleaseNotes()
    }

    UpdatePromptDialog {
        id: updatePromptDialog
        iconSource: controller.updateIconSource
        onDecision: function(token, accepted) { controller.confirmAction(token, accepted) }
    }

    AppDialog {
        id: notificationDialog
        showCloseButton: true
        modal: true
        anchors.centerIn: Overlay.overlay
        width: Math.min(520, root.settledWidth - 48)
        property string bodyText: ""
        property string level: "info"
        title: Ui.text("提示")
        closeText: "知道了"
        contentItem: Text { text: Ui.text(notificationDialog.bodyText); color: root.textMain; font.pixelSize: 13; wrapMode: Text.Wrap; textFormat: Text.PlainText; width: notificationDialog.availableWidth }
        function showMessage(titleText, messageText, levelText) {
            title = titleText
            bodyText = messageText
            level = levelText
            open()
        }
    }

    AppDialog {
        id: confirmationDialog
        modal: true
        anchors.centerIn: Overlay.overlay
        width: Math.min(540, root.settledWidth - 48)
        property string bodyText: ""
        property string actionToken: ""
        title: Ui.text("确认")
        acceptText: "确定"
        rejectText: "取消"
        contentItem: Text { text: Ui.text(confirmationDialog.bodyText); color: root.textMain; font.pixelSize: 13; wrapMode: Text.Wrap; textFormat: Text.PlainText; width: confirmationDialog.availableWidth }
        onAccepted: controller.confirmAction(actionToken, true)
        onRejected: controller.confirmAction(actionToken, false)
    }

    AppDialog {
        id: createProjectDialog
        showCloseButton: true
        modal: true
        anchors.centerIn: Overlay.overlay
        width: Math.min(590, root.settledWidth - 48)
        title: Ui.text("新建工作项目")
        acceptText: "创建并打开"
        rejectText: "取消"
        property alias projectName: projectNameField.text
        property alias projectParent: projectParentField.text
        onAccepted: controller.createProject(projectName, projectParent)
        contentItem: ColumnLayout {
            spacing: 10
            Text { text: Ui.text("项目是一套可随时打开、完整留存资料的工作文件夹。"); color: root.textMuted; font.pixelSize: 12; wrapMode: Text.Wrap; Layout.fillWidth: true }
            Text { text: Ui.text("项目名称"); color: root.textMain; font.pixelSize: 13; font.weight: Font.DemiBold }
            AppTextField { id: projectNameField; Layout.fillWidth: true; selectByMouse: true }
            Text { text: Ui.text("保存位置"); color: root.textMain; font.pixelSize: 13; font.weight: Font.DemiBold }
            RowLayout {
                Layout.fillWidth: true
                AppTextField { id: projectParentField; Layout.fillWidth: true; selectByMouse: true }
                AppButton { text: "选择其他位置"; onClicked: { var chosen = controller.chooseProjectParent(projectParentField.text); if (chosen) projectParentField.text = chosen } }
            }
            Text { Layout.fillWidth: true; text: projectParentField.text && projectNameField.text ? (projectParentField.text + "/" + projectNameField.text) : ""; color: root.primary; font.pixelSize: 11; elide: Text.ElideMiddle }
        }
    }

    AppearanceDialog { id: appearanceDialog; backend: controller.presentation }
    AiSettingsDialog { id: aiSettingsDialog; objectName: "aiSettingsDialog" }

    Loader {
        id: aiWindowLoader
        objectName: "aiWindowLoader"
        active: false
        sourceComponent: Window {
            id: aiWindow
            width: Math.min(620, root.currentScreenAvailableWidth - 40)
            height: Math.min(800, root.currentScreenAvailableHeight - 40)
            minimumWidth: 360
            minimumHeight: 460
            title: "Sage"
            color: Ui.color("window")
            property bool requestedOpen: false
            property real reveal: 0
            visible: requestedOpen || reveal > 0
            onRequestedOpenChanged: {
                if (requestedOpen) detachedChat.prepareToShow()
                else detachedChat.prepareToHide()
                reveal = requestedOpen ? 1 : 0
            }
            Behavior on reveal {
                NumberAnimation {
                    duration: aiWindow.requestedOpen ? 200 : 160
                    easing.type: Easing.OutCubic
                    onRunningChanged: if (!running && aiWindow.requestedOpen) detachedChat.focusComposer()
                }
            }
            onClosing: function(close) { close.accepted = false; requestedOpen = false }
            AiChatPanel {
                id: detachedChat
                opacity: aiWindow.reveal
                enabled: aiWindow.requestedOpen
                transform: Translate { y: (1 - aiWindow.reveal) * 12 }
                anchors.fill: parent
                showDetachButton: false
                // 独立窗口里没有「停靠列」可收，收起按钮没有意义。
                showCollapseButton: false
                onCloseRequested: aiWindow.requestedOpen = false
                onSettingsRequested: aiSettingsDialog.open()
            }
        }
    }

    RegionCodeDialog { id: regionCodeDialog; backend: controller; anchors.centerIn: parent }
    TemplateChoiceDialog { id: templateChoiceDialog; backend: controller }
    RenameReviewDialog { backend: controller.renameReview }

    Connections {
        target: controller
        function onSalaryMappingRequested() { templateChoiceDialog.showSalaryData(controller.salaryMappingData) }
        function onSalaryMappingClosed() { templateChoiceDialog.dismissSalary() }
        function onTemplateRulesRequested() { templateChoiceDialog.showRules(controller.templateRuleSections) }
        function onTemplateSelectionRequested() { templateChoiceDialog.showData(controller.templateSelectionData) }
        function onNotificationRequested(title, message, level) { notificationDialog.showMessage(title, message, level) }
        function onUpdatePromptRequested(prompt) { updatePromptDialog.showPrompt(prompt) }
        function onReleaseNotesRequested(details) { releaseNotesDialog.showNotes(details) }
        function onConfirmationRequested(title, message, token) {
            confirmationDialog.title = title
            confirmationDialog.bodyText = message
            confirmationDialog.actionToken = token
            confirmationDialog.open()
        }
        function onProjectCreationRequested(name, parent) {
            createProjectDialog.projectName = name
            createProjectDialog.projectParent = parent
            createProjectDialog.open()
        }
        function onTextInputRequested(title, prompt, initialValue, token) {
            textInputDialog.request(title, prompt, initialValue, token)
        }
    }
}
