import QtQuick 2.15
import QtQuick.Controls 2.15

Item {
    id: table
    property var tableData: ({headers: [], rows: [], widths: [], alignments: []})
    readonly property var columnSizes: {
        var count = tableData.headers.length
        var minimum = count > 4 ? 110 : 72
        var base = Math.max(width, count * minimum)
        var sizes = [], total = 0, flexible = 0
        for (var i = 0; i < count; ++i) {
            var extra = Math.max(0, base * tableData.widths[i] / 100 - minimum)
            sizes.push(extra); flexible += extra
        }
        for (var c = 0; c < count; ++c) {
            sizes[c] = minimum + Math.floor((base - count * minimum) * (flexible ? sizes[c] / flexible : 1 / count))
            total += sizes[c]
        }
        if (count && total < base) sizes[count - 1] += base - total
        return sizes
    }
    readonly property real tableWidth: {
        var total = 0
        for (var i = 0; i < columnSizes.length; ++i) total += columnSizes[i]
        return total
    }
    function alignment(column) {
        var value = tableData.alignments[column]
        return value === "right" ? TextEdit.AlignRight : value === "center" ? TextEdit.AlignHCenter : TextEdit.AlignLeft
    }
    implicitHeight: header.implicitHeight + rows.height + (horizontal.contentWidth > horizontal.width + 1 ? 14 : 0) + 24
    height: implicitHeight

    Rectangle {
        width: table.width
        height: horizontal.height
        color: Ui.color("surface")
        border.color: Ui.color("border")
        radius: 5
    }
    Flickable {
        id: horizontal
        objectName: "aiTableHorizontal"
        width: parent.width
        height: header.implicitHeight + rows.height + (contentWidth > width + 1 ? 14 : 0)
        contentWidth: table.tableWidth
        contentHeight: height
        clip: true
        flickableDirection: Flickable.HorizontalFlick
        boundsBehavior: Flickable.StopAtBounds
        interactive: contentWidth > width + 1
        onContentWidthChanged: contentX = Math.max(0, Math.min(contentX, Math.max(0, contentWidth - width)))
        onWidthChanged: contentX = Math.max(0, Math.min(contentX, Math.max(0, contentWidth - width)))
        ScrollBar.horizontal: ScrollBar {
            policy: horizontal.contentWidth > horizontal.width + 1 ? ScrollBar.AlwaysOn : ScrollBar.AlwaysOff
        }
        Rectangle {
            width: table.tableWidth
            height: header.implicitHeight
            color: Ui.color("selection")
        }
        Row {
            id: header
            width: table.tableWidth
            Repeater {
                model: table.tableData.headers
                delegate: Item {
                    width: table.columnSizes[index]
                    height: Math.max(42, headerText.implicitHeight + 20)
                    TextEdit {
                        id: headerText
                        x: 12; y: 10; width: Math.max(20, parent.width - 24)
                        text: modelData
                        font.pixelSize: 13; font.weight: Font.DemiBold
                        color: Ui.color("text")
                        horizontalAlignment: table.alignment(index)
                        wrapMode: TextEdit.Wrap
                        textFormat: TextEdit.RichText
                        readOnly: true; selectByMouse: true; selectByKeyboard: true
                    }
                }
            }
        }
        ListView {
            id: rows
            objectName: "aiTableRows"
            y: header.implicitHeight
            width: table.tableWidth
            height: Math.max(0, Math.min(360, contentHeight))
            model: table.tableData.rows
            clip: true
            cacheBuffer: 80
            boundsBehavior: Flickable.StopAtBounds
            property int savedRow: 0
            property real savedWithinRow: 0
            function rememberPosition() {
                var first = indexAt(1, contentY + 1)
                var item = first >= 0 ? itemAtIndex(first) : null
                if (item) { savedRow = first; savedWithinRow = contentY - item.y }
            }
            function restorePosition() {
                var target = Math.max(0, Math.min(savedRow, count - 1))
                positionViewAtIndex(target, ListView.Beginning)
                forceLayout()
                var item = itemAtIndex(target)
                if (item) contentY = Math.max(originY, Math.min(item.y + savedWithinRow, originY + Math.max(0, contentHeight - height)))
            }
            onContentYChanged: if (moving || rowBar.pressed) rememberPosition()
            // Virtual lists estimate total height. Preserve a row anchor, not a
            // pixel offset that drifts when a streamed row wraps onto more lines.
            onModelChanged: Qt.callLater(restorePosition)
            ScrollBar.vertical: ScrollBar {
                id: rowBar
                parent: table
                policy: rows.contentHeight > rows.height + 1 ? ScrollBar.AlwaysOn : ScrollBar.AlwaysOff
                // Keep the scrollbar reachable even when wide columns are offscreen.
                anchors.right: parent.right
                y: header.implicitHeight
                height: rows.height
            }
            delegate: Rectangle {
                id: row
                objectName: "aiTableRow"
                width: rows.width
                height: Math.max(42, cellRow.implicitHeight)
                color: index % 2 ? Ui.color("surface15") : Ui.color("surface")
                Row {
                    id: cellRow
                    Repeater {
                        model: modelData
                        delegate: Item {
                            width: table.columnSizes[index]
                            height: cellText.implicitHeight + 20
                            TextEdit {
                                id: cellText
                                x: 12; y: 10; width: Math.max(20, parent.width - 24)
                                text: modelData
                                font.pixelSize: 13
                                color: Ui.color("text")
                                horizontalAlignment: table.alignment(index)
                                wrapMode: TextEdit.Wrap
                                textFormat: TextEdit.RichText
                                readOnly: true; selectByMouse: true; selectByKeyboard: true
                            }
                        }
                    }
                }
                Rectangle { anchors.bottom: parent.bottom; width: parent.width; height: 1; color: Ui.color("divider") }
            }
        }
    }
    Text {
        y: horizontal.height + 5
        width: parent.width
        text: Ui.text("表格：" + table.tableData.rows.length + " 行")
        color: Ui.color("muted"); font.pixelSize: 10
    }
}
