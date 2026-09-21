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
    property var rowLayout: []
    property var measuredHeights: ({})
    property real measuredWidth: -1
    readonly property bool virtualized: rows.length > 64
    property real measuredTotalHeight: 0
    readonly property real totalHeight: virtualized ? measuredTotalHeight : shortBody.implicitHeight
    property bool layoutReady: false
    readonly property var visibleRange: ({
        first: rowAt(Math.max(0, flick.contentY - 160), true),
        last: rowAt(flick.contentY + flick.height + 160, false)
    })
    property int renderSlotCount: 0
    onVisibleRangeChanged: growRenderPool()
    implicitHeight: Math.min(Math.ceil(totalHeight) + 28, 320)
    color: Ui.color("surface")
    border.color: Ui.color("border6")
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
                    result.push({text: text, heading: category === "功能更新" || category === "问题修复"
                                 || category === "界面与布局" || category === "性能优化"})
                }
            }
        }
        if (!result.length) result.push({text: "此版本尚未提供更新记录。", heading: false})
        return result
    }
    function resetPosition() {
        var initial = {}
        if (history && entries && entries.length) initial[String(entries[0].version)] = true
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
    Connections { target: Ui; function onLanguageChanged() { view.invalidateMeasurements() } }
    onEntriesChanged: resetPosition()
    onHistoryChanged: resetPosition()
    onRowsChanged: if (layoutReady) rebuildLayout()
    Component.onCompleted: {
        layoutReady = true
        rebuildLayout()
    }

    // Measure with the same Qt Text layout as the delegates, once per text
    // and width. Exact offsets avoid estimated scrollbar sizes and jumps.
    function rebuildLayout() {
        if (rows.length <= 64) {
            rowLayout = []
            measuredHeights = ({})
            measuredWidth = -1
            measuredTotalHeight = 0
            renderSlotCount = 0
            return
        }
        // Width-change handlers can run before dependent width bindings. Set
        // both probes explicitly before reading their wrapped implicit height.
        textMeasure.width = Math.max(0, body.width - 14)
        headingMeasure.width = body.width
        var previous = measuredWidth === body.width ? measuredHeights : ({})
        var cache = {}
        var layout = []
        var offset = 0
        for (var i = 0; i < rows.length; ++i) {
            var row = rows[i]
            var height = 34
            if (!row.versionHeader) {
                var key = (row.heading ? "h:" : "t:") + row.text
                var measured = cache[key]
                if (measured === undefined) measured = previous[key]
                if (measured === undefined) {
                    var probe = row.heading ? headingMeasure : textMeasure
                    probe.text = Ui.text(row.text)
                    measured = probe.implicitHeight
                }
                cache[key] = measured
                height = measured + (row.heading && i > 0 ? 8 : 0)
            }
            if (i > 0) offset += 12
            layout.push({row: row, rowIndex: i, top: offset, height: height})
            offset += height
        }
        measuredWidth = body.width
        measuredHeights = cache
        rowLayout = layout
        measuredTotalHeight = offset
        growRenderPool()
    }

    function growRenderPool() {
        renderSlotCount = Math.max(renderSlotCount, visibleRange.last - visibleRange.first)
    }

    function invalidateMeasurements() {
        if (!layoutReady) return
        measuredWidth = -1
        rebuildLayout()
    }

    function rowAt(position, useBottom) {
        var layout = rowLayout
        var low = 0
        var high = layout.length
        while (low < high) {
            var middle = (low + high) >> 1
            var edge = layout[middle].top + (useBottom ? layout[middle].height : 0)
            if (useBottom ? edge < position : edge <= position) low = middle + 1
            else high = middle
        }
        return low
    }

    Text {
        id: textMeasure
        visible: false
        textFormat: Text.PlainText
        font.pixelSize: 13
        onFontChanged: view.invalidateMeasurements()
        wrapMode: Text.Wrap
        lineHeight: 1.2
    }
    Text {
        id: headingMeasure
        visible: false
        textFormat: Text.PlainText
        font.pixelSize: 14
        font.bold: true
        onFontChanged: view.invalidateMeasurements()
        wrapMode: Text.Wrap
        lineHeight: 1.2
    }

    Flickable {
        id: flick
        objectName: "updateNotesFlickable"
        anchors.fill: parent
        anchors.margins: 14
        clip: true
        contentWidth: width
        contentHeight: view.totalHeight
        flickableDirection: Flickable.VerticalFlick
        boundsBehavior: Flickable.StopAtBounds
        activeFocusOnTab: true
        Accessible.role: Accessible.Pane
        Accessible.name: Ui.text("更新内容，可上下滚动")
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
        Item {
            id: body
            // Reserve a gutter so the scrollbar never covers the text.
            width: Math.max(0, flick.width - 16)
            height: view.totalHeight
            onWidthChanged: if (view.layoutReady) view.rebuildLayout()
            Column {
                id: shortBody
                width: parent.width
                spacing: 12
                Repeater {
                    model: view.virtualized ? [] : view.rows
                    UpdateNotesRow {
                        modelData: model.modelData
                        rowIndex: index
                        width: shortBody.width
                        onVersionClicked: function(version) { view.toggleVersion(version) }
                    }
                }
            }
            Repeater {
                // Keep version buttons alive, including offscreen headers, so
                // tab order and accessibility remain stable (at most 10 versions).
                model: view.rowLayout.filter(function(item) { return item.row.versionHeader })
                UpdateNotesRow {
                    property var entry: model.modelData
                    modelData: entry.row
                    rowIndex: entry.rowIndex
                    y: entry.top
                    width: body.width
                    height: entry.height
                    onVersionClicked: function(version) { view.toggleVersion(version) }
                }
            }
            Repeater {
                // Reassign a bounded pool as the viewport crosses rows. A
                // scroll must not destroy/recreate every visible text control.
                model: view.virtualized ? view.renderSlotCount : 0
                UpdateNotesRow {
                    property var entry: index < view.visibleRange.last - view.visibleRange.first
                        ? view.rowLayout[view.visibleRange.first + index] : null
                    visible: !!entry && !entry.row.versionHeader
                    modelData: entry && !entry.row.versionHeader ? entry.row : ({text: "", heading: false})
                    rowIndex: entry ? entry.rowIndex : -1
                    y: entry ? entry.top : 0
                    width: body.width
                    height: entry ? entry.height : 0
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
                color: bar.pressed ? Ui.color("muted1") : bar.hovered ? Ui.color("muted5") : Ui.color("border1")
            }
            background: Rectangle { color: Ui.color("surface7"); radius: width / 2 }
        }
    }
}
