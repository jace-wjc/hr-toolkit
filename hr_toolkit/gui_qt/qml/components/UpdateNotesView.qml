import QtQuick 2.15
import QtQuick.Controls 2.15

// One scrolling surface shared by the update prompt and offline history.
Rectangle {
    id: view
    property var notes: []
    property var entries: []
    property bool history: false
    property var expandedVersions: ({})
    readonly property var rows: buildRows()
    readonly property real contentHeight: flick.contentHeight
    readonly property real viewportHeight: flick.height
    property alias contentY: flick.contentY
    implicitHeight: Math.min(Math.ceil(body.implicitHeight) + 28, 320)
    color: "#FFFFFF"
    border.color: "#DDDDDD"
    radius: 8

    function buildRows() {
        var result = []
        var groups = history ? entries : [{notes: notes}]
        for (var i = 0; i < groups.length; ++i) {
            if (history) {
                var version = String(groups[i].version)
                var expanded = expandedVersions[version] === true
                result.push({text: "v" + version, heading: true, versionHeader: true,
                             version: version, expanded: expanded})
                if (!expanded) continue
            }
            var lines = groups[i].notes || []
            for (var j = 0; j < lines.length; ++j) {
                var parts = String(lines[j]).split(/\r?\n/)
                for (var k = 0; k < parts.length; ++k) {
                    var text = parts[k].trim().replace(/^#{1,6}\s+/, "").replace(/^[-*•]\s+/, "")
                    if (!text) continue
                    var category = text.replace(/[：:]$/, "")
                    result.push({text: text, heading: category === "功能更新" || category === "问题修复"})
                }
            }
        }
        if (!result.length) result.push({text: "此版本尚未提供更新记录。", heading: false})
        return result
    }
    function resetPosition() {
        var initial = {}
        if (history && entries.length) initial[String(entries[0].version)] = true
        expandedVersions = initial
        flick.contentY = 0
    }
    function toggleVersion(version) {
        var next = {}
        for (var key in expandedVersions) next[key] = expandedVersions[key]
        next[version] = !next[version]
        expandedVersions = next
        Qt.callLater(function() {
            flick.contentY = Math.max(0, Math.min(flick.contentY, flick.contentHeight - flick.height))
        })
    }
    onEntriesChanged: resetPosition()
    onHistoryChanged: resetPosition()

    Flickable {
        id: flick
        objectName: "updateNotesFlickable"
        anchors.fill: parent
        anchors.margins: 14
        clip: true
        contentWidth: width
        contentHeight: body.implicitHeight
        flickableDirection: Flickable.VerticalFlick
        boundsBehavior: Flickable.StopAtBounds
        activeFocusOnTab: true
        Accessible.role: Accessible.Pane
        Accessible.name: "更新内容，可上下滚动"
        Keys.onPressed: function(event) {
            var next = contentY
            if (event.key === Qt.Key_Down) next += 40
            else if (event.key === Qt.Key_Up) next -= 40
            else if (event.key === Qt.Key_PageDown) next += height * 0.9
            else if (event.key === Qt.Key_PageUp) next -= height * 0.9
            else if (event.key === Qt.Key_Home) next = 0
            else if (event.key === Qt.Key_End) next = contentHeight
            else return
            contentY = Math.max(0, Math.min(next, contentHeight - height))
            event.accepted = true
        }
        Column {
            id: body
            // Reserve a gutter so the scrollbar never covers the text.
            width: Math.max(0, flick.width - 16)
            spacing: 12
            Repeater {
                model: view.rows
                Item {
                    readonly property bool versionHeader: modelData.versionHeader === true
                    width: body.width
                    implicitHeight: versionHeader ? 34 : rowText.implicitHeight + (modelData.heading && index > 0 ? 8 : 0)
                    height: implicitHeight
                    Button {
                        id: versionButton
                        anchors.fill: parent
                        visible: parent.versionHeader
                        text: modelData.text
                        Accessible.name: text + (modelData.expanded ? "，收起更新内容" : "，展开更新内容")
                        onClicked: view.toggleVersion(modelData.version)
                        background: Rectangle {
                            radius: 5
                            color: versionButton.hovered ? "#EEEEEB" : "#F6F6F4"
                            border.width: versionButton.visualFocus ? 1 : 0
                            border.color: "#99C7FF"
                        }
                        contentItem: Item {
                            Text {
                                anchors.left: parent.left; anchors.leftMargin: 8
                                anchors.verticalCenter: parent.verticalCenter
                                text: versionButton.text
                                font.pixelSize: 14; font.bold: true; color: "#242424"
                            }
                            Item {
                                anchors.right: parent.right; anchors.rightMargin: 10
                                anchors.verticalCenter: parent.verticalCenter
                                width: 8; height: 8
                                rotation: modelData.expanded ? 90 : 0
                                Rectangle { x: 3; y: 0; width: 1; height: 5; color: "#606060"; rotation: -45 }
                                Rectangle { x: 3; y: 3; width: 1; height: 5; color: "#606060"; rotation: 45 }
                            }
                        }
                    }
                    Text {
                        y: rowText.y
                        visible: !modelData.heading
                        text: "•"; color: "#606060"; font.pixelSize: 13
                    }
                    Text {
                        id: rowText
                        visible: !parent.versionHeader
                        x: modelData.heading ? 0 : 14
                        y: modelData.heading && index > 0 ? 8 : 0
                        width: Math.max(0, parent.width - x)
                        text: modelData.text
                        textFormat: Text.PlainText
                        font.pixelSize: modelData.heading ? 14 : 13
                        font.bold: modelData.heading
                        color: "#242424"
                        wrapMode: Text.Wrap
                        lineHeight: 1.2
                    }
                }
            }
        }
        ScrollBar.vertical: ScrollBar {
            id: bar
            policy: ScrollBar.AsNeeded
            visible: flick.contentHeight > flick.height + 1
            width: 8
            minimumSize: 0.08
            contentItem: Rectangle {
                implicitWidth: 6
                radius: width / 2
                color: bar.pressed ? "#707070" : bar.hovered ? "#888888" : "#B5B5B5"
            }
            background: Rectangle { color: "#F3F3F3"; radius: width / 2 }
        }
    }
}
