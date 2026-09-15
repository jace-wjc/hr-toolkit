import QtQuick 2.15

Item {
    id: dropTarget
    property var backend
    property string role: "input"
    property bool canReceive: false
    property string contextKey: ""
    property string enteredContext: ""
    property var feedback: ({accepted: false, message: ""})
    readonly property bool highlighted: receiver.containsDrag && canReceive && !!feedback.message

    function resetPreview() {
        if (backend && feedback.token) backend.cancelDropPreview(feedback.token)
        feedback = ({accepted: false, message: ""})
    }
    onContextKeyChanged: resetPreview()
    onCanReceiveChanged: if (!canReceive) resetPreview()
    onVisibleChanged: if (!visible) resetPreview()
    Component.onDestruction: resetPreview()

    Connections {
        target: dropTarget.backend
        function onDropPreviewReady(preview) {
            if (receiver.containsDrag && preview.token === dropTarget.feedback.token)
                dropTarget.feedback = preview
        }
    }

    // A single passive surface per input region, not one per file delegate.
    // Keep rejected candidates tracked until exit so their reason is visible
    // without leaving a stale highlight. Only valid drops accept CopyAction.
    Rectangle {
        anchors.fill: parent
        radius: 12
        visible: dropTarget.highlighted
        color: dropTarget.feedback.pending ? "#F5F6F6" : dropTarget.feedback.accepted ? "#F0F7F3" : "#FFF4F1"
        border.width: 2
        border.color: dropTarget.feedback.pending ? "#929B9B" : dropTarget.feedback.accepted ? "#17715B" : "#B34A36"
        Text {
            anchors.fill: parent; anchors.margins: 12
            text: dropTarget.feedback.message
            textFormat: Text.PlainText
            color: dropTarget.feedback.pending ? "#555D5D" : dropTarget.feedback.accepted ? "#17715B" : "#A63C2C"
            font.pixelSize: 13; font.bold: true
            wrapMode: Text.Wrap
            maximumLineCount: 3; elide: Text.ElideRight
            horizontalAlignment: Text.AlignHCenter
            verticalAlignment: Text.AlignVCenter
        }
    }
    DropArea {
        id: receiver
        anchors.fill: parent
        enabled: dropTarget.canReceive
        onEntered: {
            dropTarget.enteredContext = dropTarget.contextKey
            dropTarget.feedback = dropTarget.backend.beginDropPreview(dropTarget.role, drag.urls)
            drag.accepted = true
        }
        onExited: dropTarget.resetPreview()
        onDropped: {
            if (dropTarget.enteredContext === dropTarget.contextKey
                    && dropTarget.feedback.accepted && !dropTarget.feedback.pending
                    && dropTarget.backend.finishDropPreview(dropTarget.feedback.token, dropTarget.role, drop.urls))
                drop.accept(Qt.CopyAction)
            else
                drop.accepted = false
            dropTarget.resetPreview()
        }
    }
}
