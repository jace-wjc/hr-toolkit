import QtQuick 2.15
import QtQuick.Controls 2.15

Column {
    id: body
    property var blocks: []
    property string fallbackHtml: ""
    property bool streaming: false
    property bool showActivity: streaming
    property int fontSize: Ui.chatFontSize(width)
    spacing: 6
    // Integer Repeater models recreate every block when the count changes.
    // Diff serialized payloads instead, retaining completed text/table objects.
    ListModel { id: blockRows }
    function syncBlocks() {
        if (!blockRows) return
        var source = blocks.length ? blocks : fallbackHtml ? [{kind: "text", html: fallbackHtml}] : []
        while (blockRows.count > source.length) blockRows.remove(blockRows.count - 1)
        for (var i = 0; i < source.length; ++i) {
            var value = JSON.stringify(source[i])
            if (i >= blockRows.count) blockRows.append({serialized: value})
            else if (blockRows.get(i).serialized !== value) blockRows.setProperty(i, "serialized", value)
        }
    }
    onBlocksChanged: syncBlocks()
    onFallbackHtmlChanged: if (!blocks.length) syncBlocks()
    Component.onCompleted: syncBlocks()
    Repeater {
        model: blockRows
        delegate: Loader {
            id: blockLoader
            property var blockData: JSON.parse(serialized)
            width: body.width
            sourceComponent: blockData.kind === "table" ? tableBlock : blockData.kind === "code" ? codeBlock : textBlock
            Component {
                id: tableBlock
                AiMarkdownTable { width: blockLoader.width; tableData: blockLoader.blockData; streaming: body.streaming; fontSize: body.fontSize }
            }
            Component {
                id: codeBlock
                Rectangle {
                    width: blockLoader.width
                    height: codeScroll.height + 24 + codeLabel.height
                    color: Ui.color("surface1")
                    border.color: Ui.color("border")
                    radius: 8
                    Text {
                        id: codeLabel
                        x: 12; y: 8
                        height: text ? 24 : 0
                        text: blockLoader.blockData.language || ""
                        color: Ui.color("muted"); font.pixelSize: 11
                    }
                    Flickable {
                        id: codeScroll
                        objectName: "aiCodeScroll"
                        x: 12; y: 12 + codeLabel.height
                        width: parent.width - 24
                        height: Math.min(320, codeText.implicitHeight + (contentWidth > width ? 12 : 0))
                        contentWidth: Math.max(width, codeText.implicitWidth)
                        contentHeight: codeText.implicitHeight
                        clip: true
                        boundsBehavior: Flickable.StopAtBounds
                        ScrollBar.horizontal: ScrollBar { policy: codeScroll.contentWidth > codeScroll.width ? ScrollBar.AlwaysOn : ScrollBar.AlwaysOff }
                        ScrollBar.vertical: ScrollBar { policy: ScrollBar.AsNeeded }
                        TextEdit {
                            id: codeText
                            text: blockLoader.blockData.text || ""
                            color: Ui.color("text")
                            font.family: Qt.platform.os === "windows" ? "Consolas" : "Menlo"
                            font.pixelSize: body.fontSize - 1
                            textFormat: TextEdit.PlainText
                            readOnly: true; selectByMouse: true; selectByKeyboard: true
                        }
                    }
                }
            }
            Component {
                id: textBlock
                TextEdit {
                    objectName: "aiMarkdownText"
                    width: blockLoader.width
                    text: blockLoader.blockData.html || ""
                    color: Ui.color("text"); font.pixelSize: body.fontSize
                    wrapMode: TextEdit.Wrap; textFormat: TextEdit.RichText
                    readOnly: true; selectByMouse: true; selectByKeyboard: true
                }
            }
        }
    }
    // Fixed, subtle activity marker; no extra text line or blinking cursor.
    Rectangle { visible: body.showActivity; width: 6; height: 6; radius: 3; color: Ui.color("accent") }
}
