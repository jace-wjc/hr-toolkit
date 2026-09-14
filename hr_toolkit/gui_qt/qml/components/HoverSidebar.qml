import QtQuick 2.15

Rectangle {
    id: panel
    property bool pinned: true
    property bool preview: false
    property bool triggerHovered: false
    property bool keepOpen: false
    property bool windowActive: true
    property bool suppressPreview: false
    readonly property bool expanded: pinned || preview
    readonly property bool pointerInside: pointer.hovered
    property real reservedWidth: pinned ? width : 0
    x: expanded ? 0 : -width
    visible: expanded || slide.running
    enabled: expanded
    color: "#F7F5F1"
    border.color: "#EBE9E4"
    clip: true

    function togglePinned() {
        openDelay.stop(); closeDelay.stop()
        pinned = !pinned
        preview = false
        // A click to collapse must not immediately retrigger hover-open.
        suppressPreview = !pinned && triggerHovered
    }
    function updateHover() {
        if (!windowActive || pinned) {
            openDelay.stop(); closeDelay.stop()
            if (!windowActive) preview = false
            return
        }
        if (triggerHovered && !suppressPreview) {
            closeDelay.stop()
            if (!preview) openDelay.restart()
        } else if (preview && (pointerInside || keepOpen)) {
            openDelay.stop(); closeDelay.stop()
        } else {
            openDelay.stop()
            if (preview) closeDelay.restart()
        }
    }
    onTriggerHoveredChanged: {
        if (!triggerHovered) suppressPreview = false
        updateHover()
    }
    onPointerInsideChanged: updateHover()
    onKeepOpenChanged: updateHover()
    onWindowActiveChanged: updateHover()
    HoverHandler { id: pointer }
    Timer {
        id: openDelay
        interval: 110
        onTriggered: if (!panel.pinned && panel.windowActive && panel.triggerHovered && !panel.suppressPreview) panel.preview = true
    }
    Timer {
        id: closeDelay
        interval: 220
        onTriggered: if (!panel.pinned && !panel.triggerHovered && !panel.pointerInside && !panel.keepOpen) panel.preview = false
    }
    Behavior on x { NumberAnimation { id: slide; duration: 190; easing.type: Easing.OutCubic } }
    Behavior on reservedWidth { NumberAnimation { duration: 190; easing.type: Easing.OutCubic } }
}
