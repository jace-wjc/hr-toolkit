import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15

Dialog {
    id: dialog
    property url iconSource
    property string phase: ""
    property string statusText: ""
    property real progress: -1
    property bool canCancel: false
    signal cancelRequested()
    modal: true
    closePolicy: Popup.NoAutoClose
    width: Math.min(400, parent ? parent.width - 32 : 400)
    height: Math.min(implicitHeight, parent ? parent.height - 32 : 240)
    x: parent ? (parent.width - width) / 2 : 0
    y: parent ? (parent.height - height) / 2 : 0
    padding: 20
    spacing: 12
    enter: Transition {}
    exit: Transition {}
    header: Item { implicitHeight: 0 }
    background: Rectangle { radius: 16; color: Ui.color("surface13"); border.color: Ui.color("border5") }
    Overlay.modal: Rectangle { color: Ui.color("overlay13") }
    contentItem: RowLayout {
        spacing: 16
        Image {
            Layout.preferredWidth: 56; Layout.preferredHeight: 56
            Layout.alignment: Qt.AlignTop
            source: dialog.iconSource; fillMode: Image.PreserveAspectFit
            sourceSize.width: 112; sourceSize.height: 112; smooth: true
        }
        ColumnLayout {
            Layout.fillWidth: true; spacing: 9
            Text {
                Layout.fillWidth: true
                text: Ui.text(dialog.phase === "verifying" ? "正在校验更新…"
                      : dialog.phase === "launching" ? "正在打开安装程序…"
                      : dialog.phase === "cancelling" ? "正在取消更新…"
                      : dialog.phase === "preparing" ? "正在准备更新…" : "正在下载更新…")
                font.pixelSize: 14; font.bold: true; color: Ui.color("textStrong"); wrapMode: Text.Wrap
            }
            ProgressBar {
                id: bar
                Layout.fillWidth: true
                indeterminate: dialog.progress < 0
                from: 0; to: 1; value: Math.max(0, dialog.progress)
                background: Rectangle { implicitHeight: 6; radius: 3; color: Ui.color("border7") }
                contentItem: Item {
                    implicitHeight: 6; clip: true
                    Rectangle {
                        id: fill
                        height: parent.height; radius: 3; color: Ui.color("link3")
                        width: bar.indeterminate ? parent.width * 0.28 : parent.width * bar.visualPosition
                        x: 0
                        SequentialAnimation on x {
                            running: dialog.visible && bar.indeterminate; loops: Animation.Infinite
                            NumberAnimation { from: -fill.width; to: bar.availableWidth; duration: 1200 }
                        }
                        onWidthChanged: { if (!bar.indeterminate) x = 0 }
                    }
                }
                onIndeterminateChanged: { if (!indeterminate) fill.x = 0 }
            }
            RowLayout {
                Layout.fillWidth: true; spacing: 10
                Text {
                    Layout.fillWidth: true; text: Ui.text(dialog.statusText)
                    font.pixelSize: 12; color: Ui.color("text4"); wrapMode: Text.Wrap; textFormat: Text.PlainText
                }
                Button {
                    id: cancel
                    Layout.preferredWidth: 88; Layout.preferredHeight: 26
                    visible: dialog.canCancel || dialog.phase === "cancelling"
                    enabled: dialog.canCancel
                    text: Ui.text(dialog.phase === "cancelling" ? "正在取消…" : "取消")
                    Accessible.name: Ui.text(text)
                    background: Rectangle { radius: 6; color: cancel.down ? Ui.color("border7") : Ui.color("surface1"); border.width: cancel.visualFocus ? 2 : 0; border.color: Ui.color("link6") }
                    contentItem: Text { text: Ui.text(cancel.text); font.pixelSize: 13; color: cancel.enabled ? Ui.color("textStrong") : Ui.color("muted5"); horizontalAlignment: Text.AlignHCenter; verticalAlignment: Text.AlignVCenter }
                    onClicked: dialog.cancelRequested()
                }
            }
        }
    }
    footer: Item { implicitHeight: 0 }
}
