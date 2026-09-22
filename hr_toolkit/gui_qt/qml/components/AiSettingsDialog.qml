import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15

// Sage 设置：服务商、API Key、模型、服务地址。
// Key 只写入本机设置文件，不进入日志；界面上不允许切换成明文查看。
AppDialog {
    id: dialog
    title: "Sage 设置"
    width: 480
    closeText: "关闭"
    showCloseButton: true
    movable: true
    // Popup 的默认位置在左上角，这里按仓库里其它对话框的做法显式居中。
    x: parent ? (parent.width - width) / 2 : 0
    y: parent ? (parent.height - height) / 2 : 0

    property string statusText: ""
    property bool statusOk: false
    // 当前选中的服务商有哪些模型可选，显示在「模型」下面省得用户去翻文档。
    property var modelChoices: []

    // 切服务商时只把字段内容换成那一家自己的值。
    // 这里**不能**去动 providerCombo.currentIndex —— 之前的 reloadFields() 会把
    // currentIndex 设回 controller.aiActiveProvider，于是点 DeepSeek 立刻又弹回
    // MiniMax，看起来就是「切换无效」。
    function loadFields(provider) {
        keyField.text = controller.aiApiKeyFor(provider)
        modelField.text = controller.aiModelFor(provider)
        endpointField.text = controller.aiEndpointFor(provider)
        dialog.modelChoices = controller.aiModelChoicesFor(provider)
        statusText = ""
    }

    function reloadFields() {
        providerCombo.currentIndex = Math.max(0, providerCombo.indexOfValue(controller.aiActiveProvider))
        dialog.loadFields(providerCombo.currentValue)
    }

    onOpened: reloadFields()

    Connections {
        target: controller
        function onAiTestFinished(ok, message) {
            dialog.statusOk = ok
            dialog.statusText = message
        }
    }

    contentItem: ColumnLayout {
        spacing: 10
        RowLayout {
            Layout.fillWidth: true
            spacing: 10
            Text { Layout.preferredWidth: 74; text: Ui.text("服务商"); color: Ui.color("text"); font.pixelSize: 13 }
            AppComboBox {
                id: providerCombo
                objectName: "aiProviderCombo"
                Layout.fillWidth: true
                model: controller.aiProviderOptions
                textRole: "label"
                valueRole: "value"
                onActivated: dialog.loadFields(providerCombo.currentValue)
            }
        }
        RowLayout {
            Layout.fillWidth: true
            spacing: 10
            Text { Layout.preferredWidth: 74; text: Ui.text("API Key"); color: Ui.color("text"); font.pixelSize: 13 }
            AppTextField {
                id: keyField
                objectName: "aiApiKeyField"
                Layout.fillWidth: true
                placeholderText: Ui.text("粘贴 API Key")
                // 明文一律不展示：Key 只以掩码形态出现在界面上。
                echoMode: TextInput.Password
                selectByMouse: true
            }
        }
        RowLayout {
            Layout.fillWidth: true
            spacing: 10
            Text { Layout.preferredWidth: 74; text: Ui.text("模型"); color: Ui.color("text"); font.pixelSize: 13 }
            AppTextField {
                id: modelField
                objectName: "aiModelField"
                Layout.fillWidth: true
                placeholderText: Ui.text("留空使用默认模型")
                selectByMouse: true
            }
        }
        // 这一家的可选模型，列出来省得用户照着文档手打；
        // 想用清单以外的模型，直接清空「模型」栏自己填也行（自建网关/自建模型）。
        Text {
            objectName: "aiModelChoicesHint"
            Layout.fillWidth: true
            Layout.leftMargin: 84
            visible: dialog.modelChoices.length > 0
            // 模型名是接口里的标识符，原样展示、不做翻译。
            text: Ui.text("可选：") + dialog.modelChoices.join("、")
            color: Ui.color("muted")
            font.pixelSize: 11
            wrapMode: Text.Wrap
        }
        RowLayout {
            Layout.fillWidth: true
            spacing: 10
            Text { Layout.preferredWidth: 74; text: Ui.text("服务地址"); color: Ui.color("text"); font.pixelSize: 13 }
            AppTextField {
                id: endpointField
                objectName: "aiEndpointField"
                Layout.fillWidth: true
                placeholderText: Ui.text("留空使用默认地址")
                selectByMouse: true
            }
        }
        Text {
            Layout.fillWidth: true
            text: Ui.text("Key 仅保存在本机，不会写入日志或随项目文件分发；为避免泄露，界面不提供明文查看。")
            color: Ui.color("muted")
            font.pixelSize: 11
            wrapMode: Text.Wrap
        }
        Text {
            Layout.fillWidth: true
            text: Ui.text("服务地址已按服务商内置，留空即用官方接口；只有自建网关时才需要改，只填域名会自动补全路径。")
            color: Ui.color("muted")
            font.pixelSize: 11
            wrapMode: Text.Wrap
        }
        Text {
            Layout.fillWidth: true
            visible: dialog.statusText.length > 0
            text: Ui.text(dialog.statusText)
            color: dialog.statusOk ? Ui.color("accent") : Ui.color("warning3")
            font.pixelSize: 12
            wrapMode: Text.Wrap
        }
        RowLayout {
            Layout.fillWidth: true
            spacing: 10
            Item { Layout.fillWidth: true }
            AppButton {
                text: "测试连接"
                onClicked: {
                    dialog.statusText = Ui.text("正在测试…")
                    dialog.statusOk = false
                    controller.aiTestConnection()
                }
            }
            AppButton {
                objectName: "aiSettingsSave"
                variant: "primary"
                text: "保存"
                onClicked: {
                    var saved = controller.aiSaveSettings(
                        providerCombo.currentValue,
                        keyField.text,
                        modelField.text,
                        endpointField.text
                    )
                    if (saved) {
                        dialog.statusOk = true
                        dialog.statusText = Ui.text("已保存。")
                    }
                }
            }
        }
    }
}
