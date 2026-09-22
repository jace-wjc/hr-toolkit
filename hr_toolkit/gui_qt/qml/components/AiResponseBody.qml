import QtQuick 2.15

Column {
    id: body
    property var blocks: []
    property string fallbackHtml: ""
    property bool streaming: false
    spacing: 8
    Repeater {
        // A stable count keeps table scroll positions while streamed content changes.
        model: Math.max(1, body.blocks.length)
        delegate: Loader {
            id: blockLoader
            property var blockData: body.blocks.length ? body.blocks[index] : ({kind: "text", html: body.fallbackHtml})
            width: body.width
            sourceComponent: blockData.kind === "table" ? tableBlock : textBlock
            Component {
                id: tableBlock
                AiMarkdownTable { width: blockLoader.width; tableData: blockLoader.blockData }
            }
            Component {
                id: textBlock
                TextEdit {
                    width: blockLoader.width
                    text: blockLoader.blockData.html || ""
                    color: Ui.color("text"); font.pixelSize: 13
                    wrapMode: TextEdit.Wrap; textFormat: TextEdit.RichText
                    readOnly: true; selectByMouse: true; selectByKeyboard: true
                }
            }
        }
    }
    Text { visible: body.streaming; text: "▍"; color: Ui.color("accent"); font.pixelSize: 13 }
}
