import QtQuick 2.15
import QtQuick.Controls 2.15

ToolTip {
    id: control
    delay: 600
    timeout: 8000
    padding: 8
    implicitWidth: Math.min(360, tipText.implicitWidth + leftPadding + rightPadding)
    contentItem: Text {
        id: tipText
        text: control.text
        textFormat: Text.PlainText
        wrapMode: Text.Wrap
        color: Ui.color("text")
        font.pixelSize: 12
    }
    background: Rectangle {
        color: Ui.color("surface")
        border.color: Ui.color("border")
        radius: 6
    }
}
