import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15

AppDialog {
    id: dialog
    property var backend
    property var rows: []
    property string original: ""
    property string errorText: ""
    title: Ui.text("公司对应规则")
    width: Math.min(680, parent.width - 32)
    height: Math.min(560, parent.height - 32)
    closeText: "关闭"
    showCloseButton: true
    function reload() { rows = backend.companyRuleRows() }
    function resetEditor() { original = ""; aliasInput.text = ""; companyInput.text = ""; errorText = "" }
    onOpened: { resetEditor(); reload() }
    contentItem: ColumnLayout {
        spacing: 10
        Label {
            Layout.fillWidth: true; wrapMode: Text.Wrap
            text: Ui.text("将汇总表的公司简称与流程表全称对应，例如“唐人”对应其公司全称。只用于核对，不修改原表。保存后本机各项目自动复用；一个全称可以添加多个简称。")
        }
        RowLayout {
            Layout.fillWidth: true
            AppTextField { id: aliasInput; Layout.fillWidth: true; Layout.minimumWidth: 60; placeholderText: Ui.text("汇总表公司简称") }
            AppTextField { id: companyInput; Layout.fillWidth: true; Layout.minimumWidth: 100; placeholderText: Ui.text("流程表公司全称") }
            AppButton {
                text: dialog.original ? "保存修改" : "添加"
                enabled: backend.selectionEnabled
                onClicked: {
                    var error = backend.saveCompanyRule(dialog.original, aliasInput.text, companyInput.text, false)
                    if (error) dialog.errorText = error
                    else { dialog.resetEditor(); dialog.reload() }
                }
            }
            AppButton { visible: !!dialog.original; text: "取消修改"; variant: "link"; onClicked: dialog.resetEditor() }
        }
        Label { Layout.fillWidth: true; visible: !!dialog.errorText; text: dialog.errorText; wrapMode: Text.Wrap; color: Ui.color("error") }
        Label { visible: dialog.rows.length === 0; text: Ui.text("暂无自定义规则，仍会使用原有的唯一名称匹配。") }
        ListView {
            Layout.fillWidth: true; Layout.fillHeight: true; clip: true
            model: dialog.rows; boundsBehavior: Flickable.StopAtBounds
            ScrollBar.vertical: ScrollBar {}
            delegate: RowLayout {
                width: ListView.view.width; height: Math.max(44, ruleText.implicitHeight + 12)
                Label { id: ruleText; Layout.fillWidth: true; wrapMode: Text.Wrap; text: modelData.alias + " → " + modelData.company }
                AppButton { text: "修改"; variant: "link"; enabled: backend.selectionEnabled; onClicked: { dialog.original = modelData.alias; aliasInput.text = modelData.alias; companyInput.text = modelData.company; dialog.errorText = "" } }
                AppButton {
                    text: "删除"; variant: "link"; enabled: backend.selectionEnabled
                    onClicked: {
                        var error = backend.saveCompanyRule(modelData.alias, "", "", true)
                        if (error) dialog.errorText = error
                        else { dialog.resetEditor(); dialog.reload() }
                    }
                }
            }
        }
    }
}
