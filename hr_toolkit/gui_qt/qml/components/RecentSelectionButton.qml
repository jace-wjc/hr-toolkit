import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15

AppButton {
    id: control
    property var backend
    property string selectionRole: "input"
    property bool appendMode: false
    property bool filesAllowed: !!backend && (selectionRole === "input" ? backend.inputAllowsFiles : true)
    property bool foldersAllowed: !!backend && (selectionRole === "input" ? backend.inputAllowsFolder : backend.supportAllowsFolder)
    property string historyKind: "file"
    property var entries: []
    text: "最近使用"
    variant: "link"
    enabled: !!backend && backend.selectionEnabled
    function refresh() { entries = backend.recentSelectionItems(selectionRole, historyKind) }
    function useEntry(path, action) {
        menu.close()
        backend.useRecentSelection(selectionRole, path, action, appendMode)
    }
    function openEntry(path, action) {
        menu.close()
        backend.openRecentSelection(path, historyKind, action)
    }
    onEnabledChanged: if (!enabled) menu.close()
    onClicked: {
        if (!filesAllowed) historyKind = "folder"
        refresh()
        menu.open()
    }
    Connections {
        target: control.backend
        function onRecentSelectionsChanged() { if (menu.opened) control.refresh() }
        function onSpecChanged() { menu.close() }
    }
    Popup {
        id: menu
        objectName: "recentSelectionPopup"
        parent: Overlay.overlay
        width: Math.min(480, parent ? parent.width - 24 : 480)
        height: Math.min(390, parent ? parent.height - 24 : 390)
        padding: 12
        modal: true
        focus: true
        closePolicy: Popup.CloseOnEscape | Popup.CloseOnPressOutside
        onAboutToShow: {
            var point = control.mapToItem(parent, control.width, control.height)
            x = Math.max(12, Math.min(point.x - width, parent.width - width - 12))
            y = Math.max(12, Math.min(point.y + 4, parent.height - height - 12))
        }
        background: Rectangle { radius: 10; color: Ui.color("surface"); border.color: Ui.color("border") }
        contentItem: ColumnLayout {
            spacing: 8
            RowLayout {
                Layout.fillWidth: true
                AppButton {
                    text: "最近文件"; enabled: control.filesAllowed
                    variant: control.historyKind === "file" ? "tonal" : "link"
                    onClicked: { control.historyKind = "file"; control.refresh() }
                }
                AppButton {
                    text: "最近文件夹"
                    variant: control.historyKind === "folder" ? "tonal" : "link"
                    onClicked: { control.historyKind = "folder"; control.refresh() }
                }
                Item { Layout.fillWidth: true }
                AppButton {
                    id: closeButton
                    objectName: "recentSelectionCloseButton"
                    implicitWidth: 30; implicitHeight: 30
                    variant: "link"
                    Accessible.name: Ui.text("关闭")
                    ToolTip.visible: hovered || activeFocus
                    ToolTip.delay: 500
                    ToolTip.text: Ui.text("关闭")
                    contentItem: Item {
                        ToolIcon {
                            anchors.centerIn: parent
                            width: 16; height: 16
                            iconId: "close"
                            strokeColor: Ui.color("text")
                        }
                    }
                    onClicked: menu.close()
                }
            }
            ListView {
                id: recentList
                objectName: "recentSelectionList"
                Layout.fillWidth: true; Layout.fillHeight: true
                clip: true
                boundsBehavior: Flickable.StopAtBounds
                model: control.entries
                spacing: 4
                ScrollBar.vertical: ScrollBar { policy: ScrollBar.AsNeeded }
                delegate: Column {
                    width: recentList.width - 10
                    spacing: 4
                    Item {
                        width: parent.width; height: 34
                        Column {
                            anchors.verticalCenter: parent.verticalCenter; width: parent.width
                            Text { width: parent.width; text: modelData.name; textFormat: Text.PlainText; elide: Text.ElideMiddle; color: Ui.color("text"); font.pixelSize: 12 }
                            Text { width: parent.width; text: modelData.path; textFormat: Text.PlainText; elide: Text.ElideMiddle; color: Ui.color("muted"); font.pixelSize: 10 }
                        }
                        MouseArea {
                            anchors.fill: parent; hoverEnabled: true; acceptedButtons: Qt.NoButton
                            ToolTip.visible: containsMouse; ToolTip.delay: 500; ToolTip.text: modelData.path
                        }
                    }
                    Flow {
                        width: parent.width
                        spacing: 2
                        AppButton {
                            text: "选择"; variant: "link"; visible: control.historyKind === "file"
                            onClicked: control.useEntry(modelData.path, "file")
                        }
                        AppButton {
                            text: "浏览文件"; variant: "link"; visible: control.historyKind === "folder" && control.filesAllowed
                            onClicked: control.useEntry(modelData.path, "browse_files")
                        }
                        AppButton {
                            text: "选择文件夹"; variant: "link"; visible: control.historyKind === "folder" && control.foldersAllowed
                            onClicked: control.useEntry(modelData.path, "browse_folder")
                        }
                        AppButton {
                            text: control.historyKind === "file" ? "打开文件" : "打开文件夹"; variant: "link"
                            onClicked: control.openEntry(modelData.path, "open")
                        }
                        AppButton {
                            text: "打开所在文件夹"; variant: "link"; visible: control.historyKind === "file"
                            onClicked: control.openEntry(modelData.path, "location")
                        }
                        AppButton {
                            text: "移除"; variant: "link"
                            onClicked: control.backend.removeRecentSelection(modelData.path, control.historyKind)
                        }
                    }
                    Rectangle { width: parent.width; height: 1; color: Ui.color("divider") }
                }
                Text {
                    anchors.centerIn: parent
                    width: parent.width; wrapMode: Text.Wrap; horizontalAlignment: Text.AlignHCenter
                    visible: recentList.count === 0
                    text: Ui.text("暂无适用于此输入的最近记录。")
                    color: Ui.color("muted"); font.pixelSize: 12
                }
            }
            Text {
                Layout.fillWidth: true; wrapMode: Text.Wrap
                text: Ui.text("仅显示当前工具的记录；打开文件或位置不会添加资料或开始处理。")
                color: Ui.color("muted"); font.pixelSize: 11
            }
            RowLayout {
                Layout.fillWidth: true
                Text { Layout.fillWidth: true; wrapMode: Text.Wrap; text: Ui.text("移除或清空记录不会删除原文件。") ; color: Ui.color("muted"); font.pixelSize: 11 }
                AppButton { text: "清空本工具记录"; variant: "link"; onClicked: control.backend.clearRecentSelections() }
            }
        }
    }
}
