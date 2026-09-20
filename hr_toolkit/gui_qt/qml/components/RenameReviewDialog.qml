import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15

AppDialog {
    id: dialog
    objectName: "renameReviewDialog"
    property var backend
    title: "批量改名 · 完整预览"
    width: Math.min(parent.width - 24, 1280)
    height: Math.min(parent.height - 24, 800)
    anchors.centerIn: parent
    // Confirmation is an explicit button below. Closing never executes a plan.
    onRejected: if (backend) backend.cancel()
    onClosed: if (backend) backend.cancel()
    Connections {
        target: dialog.backend
        function onOpened() {
            search.text = ""
            statusFilter.currentIndex = 0
            dialog.open()
        }
        function onClosed() { dialog.close() }
    }
    contentItem: ColumnLayout {
        spacing: 8
        Text {
            Layout.fillWidth: true
            text: "勾选需要处理的项目；直接编辑名称。文件扩展名保持不变。原件保留，结果另存至项目。"
            wrapMode: Text.Wrap; color: "#78766E"; font.pixelSize: 12
        }
        RowLayout {
            Layout.fillWidth: true
            TextField {
                id: search; objectName: "renameSearch"
                Layout.fillWidth: true
                placeholderText: "搜索原名称、新名称、路径或问题"
                onTextChanged: if (dialog.backend) dialog.backend.filterRows(text, statusFilter.currentValue || "all")
            }
            ComboBox {
                id: statusFilter; objectName: "renameStatusFilter"
                Layout.preferredWidth: 125
                textRole: "label"; valueRole: "value"
                model: [{label: "全部", value: "all"}, {label: "需处理", value: "conflict"},
                        {label: "待改名", value: "ready"}, {label: "已排除", value: "excluded"},
                        {label: "不变", value: "unchanged"}]
                onActivated: dialog.backend.filterRows(search.text, currentValue)
            }
            AppButton {
                text: "定位问题"; variant: "tonal"
                onClicked: { search.text = ""; statusFilter.currentIndex = 1; dialog.backend.filterRows("", "conflict"); reviewList.positionViewAtBeginning() }
            }
        }
        Text {
            Layout.fillWidth: true
            text: dialog.backend ? dialog.backend.summary + (dialog.backend.validating ? " · 正在校验…" : "") : ""
            color: "#17715B"; font.pixelSize: 12
        }
        ScrollView {
            Layout.fillWidth: true; Layout.preferredHeight: 55
            visible: dialog.backend && dialog.backend.warnings.length > 0
            clip: true
            TextArea {
                text: dialog.backend ? dialog.backend.warnings : ""
                readOnly: true; wrapMode: Text.Wrap; selectByMouse: true
                color: "#936218"; font.pixelSize: 12
            }
        }
        Text {
            Layout.fillWidth: true
            text: "当前项目 / 原名称                         拟用名称（可编辑）                         映射顺序"
            font.pixelSize: 12; color: "#78766E"
        }
        ListView {
            id: reviewList; objectName: "renameReviewList"
            Layout.fillWidth: true; Layout.fillHeight: true
            clip: true; spacing: 4; cacheBuffer: 180
            model: dialog.backend ? dialog.backend.model : null
            boundsBehavior: Flickable.StopAtBounds
            ScrollBar.vertical: ScrollBar { }
            delegate: Rectangle {
                id: row
                objectName: "renameReviewRow"
                property string rowId: model.row_id
                property string oldName: model.source_name
                property string newStem: model.editable_name
                width: reviewList.width - 16; height: 98
                color: model.status === "conflict" ? "#FFF3ED" : model.included ? "#FAF9F6" : "#F2F2F0"
                border.color: model.status === "conflict" ? "#E7B397" : "#ECEAE4"
                radius: 6
                ColumnLayout {
                    anchors.fill: parent; anchors.margins: 8; spacing: 4
                    RowLayout {
                        Layout.fillWidth: true
                        CheckBox {
                            checked: model.included
                            Accessible.name: "包含 " + row.oldName
                            onClicked: dialog.backend.includeRow(row.rowId, checked)
                        }
                        Text {
                            Layout.preferredWidth: Math.max(140, row.width * 0.30)
                            text: model.order + ". " + (model.is_dir ? "[文件夹] " : "[文件] ") + row.oldName
                            elide: Text.ElideMiddle; font.pixelSize: 12; color: "#292825"
                            ToolTip.visible: sourceHover.containsMouse
                            ToolTip.text: row.oldName
                            MouseArea { id: sourceHover; anchors.fill: parent; hoverEnabled: true; acceptedButtons: Qt.NoButton }
                        }
                        TextField {
                            objectName: "renameNameEditor"
                            Layout.fillWidth: true; Layout.minimumWidth: 90
                            text: row.newStem
                            selectByMouse: true; font.pixelSize: 12
                            Accessible.name: "拟用名称 " + row.oldName
                            onTextEdited: dialog.backend.editName(row.rowId, text)
                        }
                        Text { text: model.suffix; color: "#78766E"; font.pixelSize: 12 }
                        AppButton {
                            text: "上移"; variant: "link"; implicitWidth: 46
                            enabled: dialog.backend && dialog.backend.canReorder && model.order > 1
                            Accessible.name: "将此姓名映射上移"
                            onClicked: dialog.backend.moveMapping(row.rowId, -1)
                        }
                        AppButton {
                            text: "下移"; variant: "link"; implicitWidth: 46
                            enabled: dialog.backend && dialog.backend.canReorder
                            Accessible.name: "将此姓名映射下移"
                            onClicked: dialog.backend.moveMapping(row.rowId, 1)
                        }
                    }
                    Text {
                        Layout.fillWidth: true
                        text: "相对路径：" + model.relative_path
                        elide: Text.ElideMiddle; color: "#78766E"; font.pixelSize: 11
                    }
                    Text {
                        Layout.fillWidth: true
                        text: model.status_text + (model.issue ? " · " + model.issue : model.note ? " · " + model.note : "")
                        elide: Text.ElideRight; color: model.status === "conflict" ? "#A34325" : "#78766E"; font.pixelSize: 11
                        ToolTip.visible: issueHover.containsMouse
                        ToolTip.text: text
                        MouseArea { id: issueHover; anchors.fill: parent; hoverEnabled: true; acceptedButtons: Qt.NoButton }
                    }
                }
            }
        }
        Text {
            Layout.fillWidth: true
            text: "Excel 顺序映射：上移/下移只移动姓名，文件位置和扩展名不变；搜索或筛选时禁用移动。所有已选项目校验通过后才能执行。"
            wrapMode: Text.Wrap; font.pixelSize: 11; color: "#78766E"
        }
        RowLayout {
            Layout.fillWidth: true
            Item { Layout.fillWidth: true }
            AppButton { text: "取消"; onClicked: dialog.backend.cancel() }
            AppButton {
                objectName: "renameConfirmButton"
                text: "确认并执行此方案"; variant: "primary"
                enabled: dialog.backend && dialog.backend.canConfirm
                onClicked: dialog.backend.confirm()
            }
        }
    }
}
