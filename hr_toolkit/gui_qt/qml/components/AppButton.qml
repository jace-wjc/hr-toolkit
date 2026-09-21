import QtQuick 2.15
import QtQuick.Controls 2.15

Button {
    id: control
    property string variant: "secondary"
    property color primaryColor: Ui.color("accent")
    property color primaryPressedColor: Ui.color("accentPressed")
    property color textColor: variant === "primary" ? Ui.color("onAccent") : (variant === "link" ? primaryColor : Ui.color("text"))

    implicitHeight: variant === "link" ? 30 : 34
    implicitWidth: Math.max(variant === "link" ? 52 : 82, contentItem.implicitWidth + (variant === "link" ? 12 : 26))
    leftPadding: variant === "link" ? 6 : 13
    rightPadding: variant === "link" ? 6 : 13
    hoverEnabled: true
    focusPolicy: Qt.StrongFocus
    HoverHandler { cursorShape: control.enabled ? Qt.PointingHandCursor : Qt.ArrowCursor }

    contentItem: Text {
        text: Ui.text(control.text)
        color: control.enabled ? control.textColor : Ui.color("disabledText")
        font.pixelSize: 13
        font.weight: control.variant === "primary" ? Font.DemiBold : Font.Normal
        horizontalAlignment: Text.AlignHCenter
        verticalAlignment: Text.AlignVCenter
        elide: Text.ElideRight
    }

    background: Rectangle {
        radius: 8
        color: {
            if (!control.enabled)
                return control.variant === "link" ? "transparent" : Ui.color("disabledSurface")
            if (control.variant === "primary")
                return control.down ? control.primaryPressedColor : (control.hovered ? Ui.color("accentHover") : control.primaryColor)
            if (control.variant === "tonal")
                return control.down ? Ui.color("selection6") : (control.hovered ? Ui.color("selection8") : Ui.color("selection"))
            if (control.variant === "link")
                return control.down ? Ui.color("selection") : (control.hovered ? Ui.color("hover") : "transparent")
            return control.down ? Ui.color("pressed") : (control.hovered ? Ui.color("disabledSurface") : Ui.color("surface"))
        }
        border.color: control.variant === "secondary" ? Ui.color("border") : "transparent"
        border.width: control.variant === "secondary" ? 1 : 0
    }
}
