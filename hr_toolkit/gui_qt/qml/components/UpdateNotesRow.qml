import QtQuick 2.15
import QtQuick.Controls 2.15

Item {
    id: row
    property var modelData: ({text: "", heading: false})
    property int rowIndex: -1
    signal versionClicked(string version)
    readonly property bool versionHeader: modelData.versionHeader === true
    implicitHeight: versionHeader ? 34 : rowText.implicitHeight + (modelData.heading && rowIndex > 0 ? 8 : 0)
    height: implicitHeight
    // Ordinary note rows never show a version button. Create
    // its controls only for headers, keeping row geometry exact.
    Loader {
        anchors.fill: parent
        active: parent.versionHeader
        sourceComponent: Button {
            id: versionButton
            anchors.fill: parent
            text: Ui.text(modelData.text)
            Accessible.name: Ui.text(text + (modelData.expanded ? "，收起更新内容" : "，展开更新内容"))
            onClicked: row.versionClicked(modelData.version)
            background: Rectangle {
                radius: 5
                color: versionButton.hovered ? Ui.color("border13") : Ui.color("surface10")
                border.width: versionButton.visualFocus ? 1 : 0
                border.color: Ui.color("link6")
            }
            contentItem: Item {
                Text {
                    anchors.left: parent.left; anchors.leftMargin: 8
                    anchors.verticalCenter: parent.verticalCenter
                    text: Ui.text(versionButton.text)
                    font.pixelSize: 14; font.bold: true; color: Ui.color("textStrong")
                }
                Item {
                    anchors.right: parent.right; anchors.rightMargin: 10
                    anchors.verticalCenter: parent.verticalCenter
                    width: 8; height: 8
                    rotation: modelData.expanded ? 90 : 0
                    Rectangle { x: 3; y: 0; width: 1; height: 5; color: Ui.color("text4"); rotation: -45 }
                    Rectangle { x: 3; y: 3; width: 1; height: 5; color: Ui.color("text4"); rotation: 45 }
                }
            }
        }
    }
    Text {
        y: rowText.y
        visible: !modelData.heading
        text: Ui.text("•"); color: Ui.color("text4"); font.pixelSize: 13
    }
    Text {
        id: rowText
        visible: !parent.versionHeader
        x: modelData.heading ? 0 : 14
        y: modelData.heading && rowIndex > 0 ? 8 : 0
        width: Math.max(0, parent.width - x)
        text: Ui.text(modelData.text)
        textFormat: Text.PlainText
        font.pixelSize: modelData.heading ? 14 : 13
        font.bold: modelData.heading
        color: Ui.color("textStrong")
        wrapMode: Text.Wrap
        lineHeight: 1.2
    }
}
