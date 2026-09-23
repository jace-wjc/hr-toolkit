import QtQuick 2.15

// Conversation hosted in the shared right-hand column.
// The owner keeps this view alive after first use to retain draft and scroll.
FocusScope {
    id: panel
    objectName: "aiSidePanel"
    signal closeRequested()
    signal settingsRequested()
    signal detachRequested()
    property bool requestedOpen: false
    property bool initialized: false
    property real reveal: 0
    readonly property bool opened: requestedOpen
    visible: requestedOpen || reveal > 0
    enabled: requestedOpen
    opacity: reveal
    transform: Translate { x: (1 - panel.reveal) * 18 }

    function updateReveal() {
        if (!initialized) return
        if (requestedOpen) chatPanel.prepareToShow()
        else chatPanel.prepareToHide()
        reveal = requestedOpen ? 1 : 0
    }
    onRequestedOpenChanged: updateReveal()
    Component.onCompleted: {
        initialized = true
        Qt.callLater(updateReveal)
    }
    Behavior on reveal {
        NumberAnimation {
            duration: panel.requestedOpen ? 220 : 170
            easing.type: Easing.OutCubic
            onRunningChanged: if (!running && panel.requestedOpen && panel.reveal === 1) chatPanel.focusComposer()
        }
    }
    Keys.onEscapePressed: function(event) { panel.closeRequested(); event.accepted = true }

    Rectangle {
        objectName: "aiPanelSurface"
        anchors.fill: parent
        radius: 12
        color: Ui.color("surface")
        border.color: Ui.color("border")
        // Blank parts of the panel must not click through into a business form.
        MouseArea {
            anchors.fill: parent
            acceptedButtons: Qt.AllButtons
            onWheel: function(wheel) { wheel.accepted = true }
        }
    }
    AiChatPanel {
        id: chatPanel
        showCollapseButton: false
        anchors.fill: parent
        anchors.margins: 1
        onCloseRequested: panel.closeRequested()
        onSettingsRequested: panel.settingsRequested()
        onDetachRequested: { prepareToHide(); panel.detachRequested() }
        onCollapseRequested: panel.closeRequested()
    }
}
