import QtQuick 2.15
import QtQuick.Controls 2.15

TextField {
    id: control

    implicitHeight: 36
    leftPadding: 11
    rightPadding: 11
    // Compact inline editors must still fit a full line, including fallback
    // fonts used for Chinese. Keep the normal padding when space permits.
    topPadding: Math.max(0, Math.min(7, Math.floor((height - Math.max(contentHeight, lineMetrics.height) - 2) / 2)))
    bottomPadding: topPadding
    verticalAlignment: TextInput.AlignVCenter
    selectByMouse: true
    hoverEnabled: true
    color: enabled ? Ui.color("text") : Ui.color("disabledText")
    placeholderTextColor: Ui.color("faint")
    selectionColor: Ui.color("accent")
    selectedTextColor: Ui.color("surface")
    font.pixelSize: 13

    FontMetrics { id: lineMetrics; font: control.font }

    background: Rectangle {
        radius: 6
        color: control.enabled ? Ui.color("input") : Ui.color("disabledSurface")
        border.width: 1
        border.color: control.activeFocus ? Ui.color("accent") : control.enabled && control.hovered ? Ui.color("selection2") : Ui.color("border")
    }
}
