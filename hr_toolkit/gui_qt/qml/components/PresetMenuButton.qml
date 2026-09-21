import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15

AppButton {
    id: control
    property var backend
    property string presetName: ""
    property string menuPreset: ""
    property bool customPreset: false
    text: "预设管理"
    variant: "link"
    enabled: !!backend && backend.selectionEnabled
    onEnabledChanged: if (!enabled) menu.close()
    onClicked: {
        menuPreset = presetName
        customPreset = backend.isCustomMaterialPreset(menuPreset)
        menu.open()
    }
    Popup {
        id: menu
        y: control.height + 4
        width: 218; padding: 8
        closePolicy: Popup.CloseOnEscape | Popup.CloseOnPressOutside
        background: Rectangle { color: Ui.color("surface"); radius: 9; border.color: Ui.color("border") }
        contentItem: ColumnLayout {
            spacing: 3
            AppButton { Layout.fillWidth: true; text: "保存当前为新预设"; onClicked: { menu.close(); control.backend.requestCreateMaterialPreset() } }
            AppButton { Layout.fillWidth: true; text: "用当前勾选更新预设"; enabled: control.customPreset; onClicked: { menu.close(); control.backend.updateMaterialPreset(control.menuPreset) } }
            AppButton { Layout.fillWidth: true; text: "重命名预设"; enabled: control.customPreset; onClicked: { menu.close(); control.backend.requestRenameMaterialPreset(control.menuPreset) } }
            AppButton { Layout.fillWidth: true; text: "删除预设"; enabled: control.customPreset; onClicked: { menu.close(); control.backend.requestDeleteMaterialPreset(control.menuPreset) } }
            Text { Layout.fillWidth: true; wrapMode: Text.Wrap; font.pixelSize: 11; color: Ui.color("muted4"); text: Ui.text("内置预设保持不变；删除仍需确认。") }
        }
    }
}
