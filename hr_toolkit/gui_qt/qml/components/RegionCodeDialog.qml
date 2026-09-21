import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15

AppDialog {
    id: dialog
    property var backend
    property string project: ""
    property string errorText: ""
    property var rows: []
    title: Ui.text("地区编号维护")
    width: Math.min(560, parent.width - 32)
    height: Math.min(560, parent.height - 32)
    closeText: "关闭"
    showCloseButton: true
    function reload() {
        var state = backend.regionCodeSettings()
        project = state.project
        rows = state.rows
        errorText = state.error
    }
    onOpened: { regionName.text = ""; regionCode.text = ""; reload() }
    contentItem: ColumnLayout {
        spacing: 10
        Label { Layout.fillWidth: true; wrapMode: Text.Wrap; text: Ui.text("仅保存当前项目的自定义配置。同编号或同地区优先使用自定义配置，删除后恢复内置规则。") }
        RowLayout {
            AppTextField { id: regionName; Layout.fillWidth: true; placeholderText: Ui.text("地区名称") }
            AppTextField { id: regionCode; Layout.preferredWidth: 100; placeholderText: Ui.text("编号，如 01") }
            AppButton {
                text: "保存"
                enabled: !!dialog.project && backend.selectionEnabled
                onClicked: {
                    var error = backend.saveRegionCode(dialog.project, regionName.text, regionCode.text, false)
                    if (error) dialog.errorText = error
                    else { dialog.reload(); regionName.text = ""; regionCode.text = "" }
                }
            }
        }
        Label { visible: !!dialog.errorText; text: Ui.text(dialog.errorText); color: Ui.color("error"); wrapMode: Text.Wrap; Layout.fillWidth: true }
        ListView {
            Layout.fillWidth: true; Layout.fillHeight: true; clip: true
            model: dialog.rows
            ScrollBar.vertical: ScrollBar {}
            delegate: RowLayout {
                width: ListView.view.width; height: 42
                Label { text: modelData.name; Layout.fillWidth: true; elide: Text.ElideRight }
                Label { text: Ui.text(modelData.code); Layout.preferredWidth: 70 }
                Label { text: Ui.text(modelData.custom ? "自定义" : "内置"); Layout.preferredWidth: 52 }
                AppButton { text: "修改"; variant: "link"; onClicked: { regionName.text = modelData.name; regionCode.text = modelData.code } }
                AppButton {
                    text: "删除"; variant: "link"; enabled: modelData.custom && backend.selectionEnabled
                    onClicked: {
                        var error = backend.saveRegionCode(dialog.project, modelData.name, modelData.code, true)
                        if (error) dialog.errorText = error
                        else dialog.reload()
                    }
                }
            }
        }
    }
}
