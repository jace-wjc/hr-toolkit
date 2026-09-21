import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Window 2.15

Item {
    id: chrome
    property var window
    property var sidebar
    property bool nativeMac: false
    property bool nativeWindows: false
    property bool systemButtons: false
    property bool workspaceAvailable: false
    property bool workspaceExpanded: false
    property bool workspaceAutoHidden: false
    property real workspacePanelLeft: 0
    signal workspaceToggleRequested()
    readonly property bool triggerHovered: sidebarButton.hovered
    height: 40

    function toggleMaximized() {
        if (window.visibility === Window.Maximized) window.showNormal()
        else window.showMaximized()
    }
    MouseArea {
        anchors.fill: parent
        anchors.leftMargin: chrome.nativeMac ? 80 : 0
        onPressed: chrome.window.startSystemMove()
        onDoubleClicked: chrome.toggleMaximized()
    }
    Button {
        id: sidebarButton
        objectName: "sidebarToggleButton"
        // Keep hover-preview's trigger stationary; only a pinned Windows
        // sidebar places its collapse control beside the right divider.
        x: chrome.nativeMac ? 82 : chrome.nativeWindows
           ? (chrome.sidebar.pinned ? Math.max(16, chrome.sidebar.width - width - 16) : 16)
           : 10
        Behavior on x {
            enabled: chrome.nativeWindows
            NumberAnimation { duration: 190; easing.type: Easing.OutCubic }
        }
        y: chrome.nativeMac || chrome.nativeWindows ? 5 : 9; width: 32; height: 30
        hoverEnabled: true
        focusPolicy: Qt.StrongFocus
        Accessible.name: Ui.text(chrome.sidebar.pinned ? "收起左侧栏" : "固定展开左侧栏")
        onClicked: chrome.sidebar.togglePinned()
        background: Rectangle {
            radius: 6
            color: sidebarButton.down ? Ui.color("border10") : sidebarButton.hovered ? Ui.color("pressed") : "transparent"
            border.width: sidebarButton.visualFocus ? 1 : 0
            border.color: Ui.color("muted")
        }
        contentItem: Item { ThemedImage { anchors.centerIn: parent; width: 17; height: 17; source: "sidebar-simple.png"; opacity: 0.65; sourceSize.width: 34; sourceSize.height: 34 } }
        ToolTip.visible: hovered
        ToolTip.delay: 700
        ToolTip.text: Ui.text(chrome.sidebar.pinned ? "收起左侧栏" : "悬停展开，点击固定")
    }
    Button {
        id: workspaceButton
        objectName: "workspaceToggleButton"
        anchors.right: parent.right
        anchors.rightMargin: Math.max(chrome.systemButtons ? 148 : chrome.nativeWindows ? 16 : 10,
                                      chrome.width - chrome.workspacePanelLeft + 10)
        y: chrome.nativeMac || chrome.nativeWindows ? 5 : 9; width: 32; height: 30
        hoverEnabled: true
        focusPolicy: Qt.StrongFocus
        enabled: chrome.workspaceAvailable || chrome.workspaceExpanded
        Accessible.name: Ui.text(chrome.workspaceAutoHidden ? "取消项目文件自动恢复"
                         : chrome.workspaceExpanded ? "收起项目文件" : "展开项目文件")
        onClicked: chrome.workspaceToggleRequested()
        background: Rectangle {
            radius: 6
            color: chrome.workspaceExpanded
                   ? (workspaceButton.down ? Ui.color("selection1") : Ui.color("selection3"))
                   : (workspaceButton.down ? Ui.color("border10") : workspaceButton.hovered ? Ui.color("pressed") : "transparent")
            border.width: workspaceButton.visualFocus ? 1 : 0
            border.color: Ui.color("muted")
        }
        contentItem: Item {
            ThemedImage {
                anchors.centerIn: parent; width: 17; height: 17
                source: "sidebar-simple.png"
                mirror: true
                opacity: workspaceButton.enabled ? 0.65 : 0.3
                sourceSize.width: 34; sourceSize.height: 34
            }
        }
        ToolTip.visible: hovered
        ToolTip.delay: 700
        ToolTip.text: Ui.text(chrome.workspaceAutoHidden ? "窗口较窄，项目文件将在放大后恢复；点击取消恢复"
                      : chrome.workspaceExpanded ? "收起项目文件" : "展开项目文件")
    }
    Row {
        anchors.right: parent.right
        height: parent.height
        visible: chrome.systemButtons
        Repeater {
            model: ["最小化", "最大化或还原", "关闭"]
            Button {
                id: windowButton
                objectName: "windowControl" + index
                width: 46; height: chrome.height
                hoverEnabled: true
                Accessible.name: Ui.text(modelData)
                onClicked: {
                    if (index === 0) chrome.window.showMinimized()
                    else if (index === 1) chrome.toggleMaximized()
                    else chrome.window.close()
                }
                background: Rectangle { color: windowButton.hovered ? (index === 2 ? Ui.color("error2") : Ui.color("pressed")) : "transparent" }
                contentItem: Item {
                    ThemedImage {
                        anchors.centerIn: parent; width: 13; height: 13
                        anchors.verticalCenterOffset: 4
                        source: index === 0 ? "minus.png" : index === 2 ? "x.png" : chrome.window.visibility === Window.Maximized ? "copy-simple.png" : "square.png"
                        opacity: 0.7; sourceSize.width: 26; sourceSize.height: 26
                    }
                }
            }
        }
    }
}
