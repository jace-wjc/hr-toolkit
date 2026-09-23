import QtQuick 2.15
import QtQuick.Layouts 1.15

FocusScope {
    id: panel
    property bool requestedOpen: false
    // Target left-sidebar width drives hysteresis; its live animated width
    // supplies the hard budget. Neither depends on this panel's own width.
    property real availableWidth: 0
    property real liveAvailableWidth: availableWidth
    readonly property real coreMinimumWidth: 640
    property real minimumPanelWidth: 320
    property real maximumPanelWidth: 360
    property real preferredPanelWidth: liveAvailableWidth * 0.29
    readonly property real gutter: 16
    readonly property real collapseThreshold: coreMinimumWidth + minimumPanelWidth + gutter
    readonly property real restoreThreshold: collapseThreshold + 80
    property bool autoCollapsed: false
    readonly property bool opened: requestedOpen && !autoCollapsed
    readonly property real panelWidth: Math.max(minimumPanelWidth,
        Math.min(maximumPanelWidth, preferredPanelWidth, liveAvailableWidth - coreMinimumWidth - gutter))
    property real reveal: opened ? 1 : 0
    readonly property real reservedWidth: Math.max(0, Math.min(
        reveal * (panelWidth + gutter), liveAvailableWidth - coreMinimumWidth))
    signal openRequested()
    signal closeRequested()
    function open() { openRequested() }
    function close() { closeRequested() }
    function updateAvailability() {
        if (!autoCollapsed && availableWidth <= collapseThreshold) autoCollapsed = true
        else if (autoCollapsed && availableWidth >= restoreThreshold) autoCollapsed = false
    }
    onAvailableWidthChanged: updateAvailability()
    Component.onCompleted: updateAvailability()
    Layout.fillHeight: true
    Layout.minimumWidth: reservedWidth
    Layout.preferredWidth: reservedWidth
    Layout.maximumWidth: reservedWidth
    clip: true
    enabled: reservedWidth > 0
    Keys.onEscapePressed: function(event) { close(); event.accepted = true }
    Behavior on reveal {
        NumberAnimation { duration: 190; easing.type: Easing.OutCubic }
    }
}
