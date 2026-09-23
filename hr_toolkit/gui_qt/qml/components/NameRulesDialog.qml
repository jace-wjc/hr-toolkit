import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15

AppDialog {
    id: dialog
    property var backend
    property bool confirmation: false
    property string errorText: ""
    property int editingIndex: -1
    title: Ui.text(confirmation ? "这些名称是否表示同一含义？" : "地区 / 项目名称对应规则")
    width: Math.min(760, parent.width - 32)
    height: Math.min(620, parent.height - 32)
    showCloseButton: true
    ListModel { id: ruleModel }
    function reload(rows) {
        ruleModel.clear()
        for (var i = 0; i < rows.length; i++) {
            var row = rows[i]
            ruleModel.append({ company: row.company, fieldName: row.field, leftName: row.left,
                                 rightName: row.right, occurrences: row.count || 0, chosen: false })
        }
    }
    function resetEditor() {
        editingIndex = -1; companyInput.text = ""; leftInput.text = ""; rightInput.text = ""; errorText = ""
    }
    function showConfirmation() {
        confirmation = true; resetEditor(); reload(backend.pendingNameRules); open()
    }
    function showRules() {
        confirmation = false; resetEditor(); reload(backend.nameRuleRows()); open()
    }
    onClosed: if (confirmation) backend.cancelNameConfirmation()
    contentItem: ColumnLayout {
        spacing: 10
        Label {
            Layout.fillWidth: true; wrapMode: Text.Wrap
            text: Ui.text(dialog.confirmation
                ? "请只勾选含义相同的名称。确认后自动保存，并用于本次及以后核对。未勾选的仍按差异输出，下次遇到会再次询问。关闭窗口将取消本次核对。"
                : "规则按公司和字段区分，本机各项目可复用，只影响比较，不改写原表名称。同义名称请指向同一个最终名称。")
        }
        ColumnLayout {
            visible: !dialog.confirmation; Layout.fillWidth: true
            RowLayout {
                Layout.fillWidth: true
                AppTextField { id: companyInput; Layout.fillWidth: true; Layout.minimumWidth: 80; placeholderText: Ui.text("流程表公司全称") }
                AppComboBox { id: fieldInput; Layout.preferredWidth: 130; model: ["地市", "所属专业", "项目"] }
            }
            RowLayout {
                Layout.fillWidth: true
                AppTextField { id: leftInput; Layout.fillWidth: true; Layout.minimumWidth: 60; placeholderText: Ui.text("汇总表中的名称") }
                AppTextField { id: rightInput; Layout.fillWidth: true; Layout.minimumWidth: 60; placeholderText: Ui.text("对应的流程表名称") }
                AppButton {
                    text: dialog.editingIndex < 0 ? "添加" : "保存修改"
                    enabled: backend.selectionEnabled
                    onClicked: {
                        var error = backend.saveNameRule(dialog.editingIndex, JSON.stringify({company: companyInput.text,
                            field: fieldInput.currentText, left: leftInput.text, right: rightInput.text}), false)
                        if (error) dialog.errorText = error
                        else { dialog.resetEditor(); dialog.reload(backend.nameRuleRows()) }
                    }
                }
            }
            AppButton { visible: dialog.editingIndex >= 0; text: "取消修改"; variant: "link"; onClicked: dialog.resetEditor() }
        }
        Label { visible: !!dialog.errorText; text: dialog.errorText; color: Ui.color("error"); Layout.fillWidth: true; wrapMode: Text.Wrap }
        Label { visible: ruleModel.count === 0; text: Ui.text("暂无自定义名称对应规则。") }
        ListView {
            Layout.fillWidth: true; Layout.fillHeight: true; clip: true
            model: ruleModel; boundsBehavior: Flickable.StopAtBounds
            ScrollBar.vertical: ScrollBar {}
            delegate: RowLayout {
                width: ListView.view.width; height: Math.max(72, nameText.implicitHeight + 20)
                AppCheckBox {
                    visible: dialog.confirmation; checked: chosen
                    Accessible.name: company + " / " + fieldName + "：" + leftName + " 与 " + rightName + " 含义相同"
                    onToggled: ruleModel.setProperty(index, "chosen", checked)
                }
                Label {
                    id: nameText; Layout.fillWidth: true; wrapMode: Text.Wrap; textFormat: Text.PlainText
                    text: company + " / " + fieldName + (dialog.confirmation ? " · " + occurrences + " 处" : "")
                          + "\n汇总表：" + leftName + "\n流程表：" + rightName
                }
                AppButton {
                    visible: !dialog.confirmation; text: "修改"; variant: "link"; enabled: backend.selectionEnabled
                    onClicked: {
                        dialog.editingIndex = index; companyInput.text = company; leftInput.text = leftName; rightInput.text = rightName
                        fieldInput.currentIndex = ["地市", "所属专业", "项目"].indexOf(fieldName); dialog.errorText = ""
                    }
                }
                AppButton {
                    visible: !dialog.confirmation; text: "删除"; variant: "link"; enabled: backend.selectionEnabled
                    onClicked: {
                        var error = backend.saveNameRule(index, "{}", true)
                        if (error) dialog.errorText = error
                        else { dialog.resetEditor(); dialog.reload(backend.nameRuleRows()) }
                    }
                }
            }
        }
    }
    footer: RowLayout {
        spacing: 10
        Item { Layout.fillWidth: true }
        AppButton { text: dialog.confirmation ? "取消本次核对" : "关闭"; onClicked: dialog.close() }
        AppButton {
            visible: dialog.confirmation; text: "确认并继续核对"; variant: "primary"; enabled: backend.selectionEnabled
            onClicked: {
                var selected = []
                for (var i = 0; i < ruleModel.count; i++) if (ruleModel.get(i).chosen) selected.push(i)
                var error = backend.confirmNameRules(JSON.stringify(selected))
                if (error) dialog.errorText = error
                else dialog.close()
            }
        }
    }
}
