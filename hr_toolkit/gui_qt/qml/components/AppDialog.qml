import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15

Dialog {
    id: control

    property string acceptText: ""
    property string rejectText: ""
    property string closeText: ""
    property bool acceptButtonEnabled: true
    property bool showCloseButton: false

    modal: true
    padding: 18
    closePolicy: Popup.CloseOnEscape
    enter: Transition {}
    exit: Transition {}

    Overlay.modal: Rectangle { color: Ui.color("overlay") }

    background: Rectangle {
        color: Ui.color("surface")
        radius: 12
        border.color: Ui.color("border")
        border.width: 1
    }

    header: Rectangle {
        implicitHeight: 54
        color: Ui.color("surface")
        radius: 12

        Text {
            anchors.left: parent.left
            anchors.right: parent.right
            anchors.leftMargin: 18
            anchors.rightMargin: control.showCloseButton ? 52 : 18
            anchors.verticalCenter: parent.verticalCenter
            text: Ui.text(control.title)
            color: Ui.color("text")
            font.pixelSize: 16
            font.weight: Font.DemiBold
            elide: Text.ElideRight
        }

        Rectangle {
            anchors.left: parent.left
            anchors.right: parent.right
            anchors.bottom: parent.bottom
            height: 1
            color: Ui.color("divider")
        }
        AppButton {
            anchors.right: parent.right; anchors.rightMargin: 10
            anchors.verticalCenter: parent.verticalCenter
            visible: control.showCloseButton
            enabled: (control.closePolicy & Popup.CloseOnEscape) !== 0
            implicitWidth: 30; implicitHeight: 30; variant: "link"
            Accessible.name: Ui.text("关闭")
            contentItem: ThemedImage { source: "x.png"; sourceSize.width: 28; sourceSize.height: 28; fillMode: Image.PreserveAspectFit }
            onClicked: {
                if (control.rejectText) control.reject()
                else control.close()
            }
        }
    }

    footer: Rectangle {
        visible: control.acceptText || control.rejectText || control.closeText
        implicitHeight: visible ? 58 : 0
        color: Ui.color("surface")
        radius: 12

        Rectangle {
            anchors.left: parent.left
            anchors.right: parent.right
            anchors.top: parent.top
            height: 1
            color: Ui.color("divider")
        }

        RowLayout {
            anchors.fill: parent
            anchors.leftMargin: 18
            anchors.rightMargin: 18
            spacing: 8

            Item { Layout.fillWidth: true }
            AppButton {
                visible: control.closeText.length > 0
                text: control.closeText
                onClicked: control.close()
            }
            AppButton {
                visible: control.rejectText.length > 0
                text: control.rejectText
                onClicked: control.reject()
            }
            AppButton {
                visible: control.acceptText.length > 0
                text: control.acceptText
                variant: "primary"
                enabled: control.acceptButtonEnabled
                onClicked: control.accept()
            }
        }
    }
}
