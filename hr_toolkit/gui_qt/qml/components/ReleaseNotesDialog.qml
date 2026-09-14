import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15

Dialog {
    id: dialog
    property url iconSource
    property var details: ({entries: []})
    signal dismissed()
    modal: true
    closePolicy: Popup.CloseOnEscape
    width: Math.min(580, parent ? parent.width - 32 : 580)
    height: Math.min(implicitHeight, parent ? parent.height - 32 : 620)
    x: parent ? (parent.width - width) / 2 : 0
    y: parent ? (parent.height - height) / 2 : 0
    padding: 20; spacing: 18
    enter: Transition {}
    exit: Transition {}
    background: Rectangle { color: "#F8F8F8"; radius: 16; border.color: "#D8D8D8" }
    Overlay.modal: Rectangle { color: "#33000000" }
    header: Item { implicitHeight: 0 }
    function showNotes(value) { details = value; open() }
    onOpened: done.forceActiveFocus()
    onClosed: dismissed()
    contentItem: ColumnLayout {
        spacing: 18
        RowLayout {
            Layout.fillWidth: true; spacing: 18
            Image { Layout.preferredWidth: 56; Layout.preferredHeight: 56; source: dialog.iconSource; sourceSize.width: 112; sourceSize.height: 112; fillMode: Image.PreserveAspectFit; smooth: true }
            ColumnLayout {
                Layout.fillWidth: true; spacing: 8
                Text { Layout.fillWidth: true; text: dialog.details.startup ? "本次更新" : "更新记录"; font.pixelSize: 18; font.bold: true; color: "#242424" }
                Text { Layout.fillWidth: true; text: "当前版本：HR Toolkit v" + (dialog.details.currentVersion || ""); font.pixelSize: 13; color: "#606060"; wrapMode: Text.Wrap }
            }
        }
        ScrollView {
            id: scroll
            Layout.fillWidth: true; Layout.fillHeight: true
            Layout.preferredHeight: Math.min(entriesColumn.implicitHeight, 360)
            contentWidth: availableWidth; clip: true
            ColumnLayout {
                id: entriesColumn
                width: scroll.availableWidth; spacing: 18
                Repeater {
                    model: dialog.details.entries || []
                    ColumnLayout {
                        Layout.fillWidth: true; spacing: 10
                        Text { Layout.fillWidth: true; text: "v" + modelData.version; font.pixelSize: 14; font.bold: true; color: "#242424" }
                        Text { Layout.fillWidth: true; text: (modelData.notes || []).map(function(note) { return "• " + note }).join("\n\n"); textFormat: Text.PlainText; font.pixelSize: 13; color: "#242424"; wrapMode: Text.Wrap }
                    }
                }
                Text { Layout.fillWidth: true; visible: !(dialog.details.entries || []).length; text: "此版本尚未提供更新记录。"; color: "#606060"; font.pixelSize: 13 }
            }
        }
    }
    footer: Item {
        implicitHeight: 50
        Button {
            id: done
            anchors.right: parent.right; anchors.rightMargin: 20
            width: 100; height: 30; text: "好"
            background: Rectangle { radius: 15; color: done.down ? "#005FCC" : "#007AFF"; border.width: done.activeFocus ? 2 : 0; border.color: "#004DA8" }
            contentItem: Text { text: done.text; color: "white"; font.pixelSize: 13; horizontalAlignment: Text.AlignHCenter; verticalAlignment: Text.AlignVCenter }
            onClicked: dialog.close()
        }
    }
}
