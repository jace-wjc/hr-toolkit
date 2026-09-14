import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15

Dialog {
    id: dialog
    objectName: "updatePromptDialog"
    property var prompt: ({available: false, currentVersion: ""})
    property url iconSource
    property bool answered: false
    property bool hasUpdate: !!prompt.available
    signal decision(string token, bool accepted)
    modal: true
    closePolicy: hasUpdate ? Popup.NoAutoClose : Popup.CloseOnEscape
    width: Math.min(hasUpdate ? 580 : 260, parent ? parent.width - 32 : 580)
    height: Math.min(implicitHeight, hasUpdate ? 520 : 320, parent ? parent.height * 0.84 : 520)
    x: parent ? (parent.width - width) / 2 : 0
    y: parent ? (parent.height - height) / 2 : 0
    padding: 20
    bottomPadding: 16
    topPadding: hasUpdate ? 24 : 22
    spacing: 16
    enter: Transition {}
    exit: Transition {}
    Overlay.modal: Rectangle { color: "#33000000" }
    background: Rectangle { color: "#F8F8F8"; radius: dialog.hasUpdate ? 16 : 24; border.color: "#D8D8D8" }
    header: Item { implicitHeight: 0 }

    function showPrompt(value) { prompt = value; answered = false; open() }
    onOpened: { notesView.resetPosition(); primary.forceActiveFocus() }
    function choose(accepted) {
        if (answered) return
        answered = true
        var token = prompt.token || ""
        close()
        if (hasUpdate && token) decision(token, accepted)
    }

    contentItem: ColumnLayout {
            spacing: 18
            ColumnLayout {
                Layout.fillWidth: true; visible: !dialog.hasUpdate; spacing: 12
                Image { Layout.preferredWidth: 56; Layout.preferredHeight: 56; source: dialog.iconSource; fillMode: Image.PreserveAspectFit; smooth: true; sourceSize.width: 112; sourceSize.height: 112 }
                Item { Layout.preferredHeight: 2 }
                Text { Layout.fillWidth: true; text: "没有新版本"; font.pixelSize: 14; font.bold: true; color: "#242424"; wrapMode: Text.Wrap }
                Text { Layout.fillWidth: true; text: "HR Toolkit v" + (dialog.prompt.currentVersion || "") + "\n目前没有可用的新版本。"; textFormat: Text.PlainText; font.pixelSize: 13; color: "#242424"; wrapMode: Text.Wrap }
            }
            RowLayout {
                Layout.fillWidth: true; visible: dialog.hasUpdate; spacing: 18
                Image { Layout.preferredWidth: 64; Layout.preferredHeight: 64; Layout.alignment: Qt.AlignTop; source: dialog.iconSource; fillMode: Image.PreserveAspectFit; smooth: true; sourceSize.width: 128; sourceSize.height: 128 }
                ColumnLayout {
                    Layout.fillWidth: true; spacing: 10
                    Text { Layout.fillWidth: true; text: "HR Toolkit 有新版本可用！"; font.pixelSize: 16; font.bold: true; color: "#242424"; wrapMode: Text.Wrap }
                    Text { Layout.fillWidth: true; text: "新版本为 v" + (dialog.prompt.version || "") + "，你当前使用的是 v" + (dialog.prompt.currentVersion || "") + "。是否现在更新？"; textFormat: Text.PlainText; font.pixelSize: 13; color: "#242424"; wrapMode: Text.Wrap }
                }
            }
            UpdateNotesView {
                id: notesView
                objectName: "promptNotesView"
                Layout.fillWidth: true
                Layout.fillHeight: true
                Layout.minimumHeight: 0
                Layout.preferredHeight: implicitHeight
                visible: dialog.hasUpdate && (dialog.prompt.notes || []).length > 0
                notes: dialog.prompt.notes || []
            }
            Text {
                Layout.fillWidth: true; visible: dialog.hasUpdate && (!!dialog.prompt.mandatory || !!dialog.prompt.manual)
                text: (dialog.prompt.manual ? "点击“下载更新”后会打开下载地址，请按安装提示完成更新。" : "")
                      + (dialog.prompt.manual && dialog.prompt.mandatory ? "\n" : "")
                      + (dialog.prompt.mandatory ? "本次为必要更新；不更新将退出程序。" : "")
                color: "#606060"; font.pixelSize: 12; wrapMode: Text.Wrap
            }
    }
    footer: Item {
        implicitHeight: buttonFlow.implicitHeight + 26
        Flow {
            id: buttonFlow
            anchors.left: parent.left; anchors.right: parent.right; anchors.top: parent.top
            anchors.leftMargin: dialog.hasUpdate ? 20 : 13
            anchors.rightMargin: dialog.hasUpdate ? 20 : 13
            spacing: 10; layoutDirection: Qt.RightToLeft
            Button {
                id: primary
                objectName: "updatePromptPrimary"
                width: dialog.hasUpdate ? 124 : buttonFlow.width
                height: 30
                text: !dialog.hasUpdate ? "好" : dialog.prompt.manual ? "下载更新" : "安装更新"
                Accessible.name: text
                background: Rectangle { radius: height / 2; color: primary.down ? "#005FCC" : primary.hovered ? "#0070E8" : "#007AFF"; border.width: primary.activeFocus ? 2 : 0; border.color: "#004DA8" }
                contentItem: Text { text: primary.text; color: "white"; font.pixelSize: 13; horizontalAlignment: Text.AlignHCenter; verticalAlignment: Text.AlignVCenter }
                onClicked: dialog.choose(true)
            }
            Button {
                id: secondary
                objectName: "updatePromptSecondary"
                visible: dialog.hasUpdate
                width: 124; height: 30
                text: dialog.prompt.mandatory ? "退出程序" : "暂不更新"
                Accessible.name: text
                background: Rectangle { radius: height / 2; color: secondary.down ? "#DEDEDE" : secondary.hovered ? "#E9E9E9" : "#EEEEEE"; border.width: secondary.activeFocus ? 2 : 0; border.color: "#007AFF" }
                contentItem: Text { text: secondary.text; color: "#242424"; font.pixelSize: 13; horizontalAlignment: Text.AlignHCenter; verticalAlignment: Text.AlignVCenter }
                onClicked: dialog.choose(false)
            }
        }
    }
}
