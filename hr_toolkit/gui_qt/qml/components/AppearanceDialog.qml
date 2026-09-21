import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15
AppDialog {
    id: dialog
    objectName: "appearanceDialog"
    property var backend
    function optionIndex(options, value) {
        for (var i = 0; i < options.length; i++) if (options[i].value === value) return i
        return 0
    }
    anchors.centerIn: Overlay.overlay
    width: Math.min(460, parent ? parent.width - 32 : 460)
    title: Ui.text("外观与语言")
    closeText: "完成"
    showCloseButton: true
    contentItem: ColumnLayout {
        spacing: 14
        Label { text: Ui.text("主题"); color: Ui.color("text") }
        AppComboBox {
            objectName: "themeSelector"
            Layout.fillWidth: true
            model: dialog.backend ? dialog.backend.themeOptions : []
            textRole: "label"
            currentIndex: dialog.optionIndex(model, dialog.backend ? dialog.backend.theme : "light")
            onActivated: dialog.backend.setTheme(model[index].value)
        }
        Label { text: Ui.text("语言"); color: Ui.color("text") }
        AppComboBox {
            objectName: "languageSelector"
            Layout.fillWidth: true
            model: dialog.backend ? dialog.backend.languageOptions : []
            textRole: "label"
            currentIndex: dialog.optionIndex(model, dialog.backend ? dialog.backend.language : "zh_CN")
            onActivated: dialog.backend.setLanguage(model[index].value)
        }
        Label {
            Layout.fillWidth: true; wrapMode: Text.Wrap
            text: Ui.text("设置立即生效并自动保存。资料名称、Excel 列名和生成结果保持原样。")
            color: Ui.color("muted")
        }
    }
}
