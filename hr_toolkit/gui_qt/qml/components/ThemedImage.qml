import QtQuick 2.15
// Keep existing PNGs in light mode; draw crisp, palette-colored icons in dark mode.
Item {
    id: image
    property url source
    property alias sourceSize: original.sourceSize
    property int fillMode: Image.PreserveAspectFit
    property bool mirror: false
    implicitWidth: original.implicitWidth
    implicitHeight: original.implicitHeight
    Image {
        id: original
        anchors.fill: parent
        source: image.source
        fillMode: image.fillMode
        mirror: image.mirror
        visible: !Ui.dark
    }
    Canvas {
        anchors.fill: parent
        visible: Ui.dark
        transform: Scale { origin.x: image.width / 2; xScale: image.mirror ? -1 : 1 }
        property string asset: String(image.source).split("/").pop()
        property color ink: Ui.color("text")
        onAssetChanged: requestPaint()
        onInkChanged: requestPaint()
        onVisibleChanged: if (visible) requestPaint()
        onWidthChanged: requestPaint()
        onHeightChanged: requestPaint()
        onPaint: {
            var c = getContext("2d")
            c.clearRect(0, 0, width, height)
            c.save(); c.scale(width / 16, height / 16)
            c.strokeStyle = ink; c.lineWidth = 1.35; c.lineCap = "round"; c.lineJoin = "round"
            function line(a,b,x,y) { c.beginPath(); c.moveTo(a,b); c.lineTo(x,y); c.stroke() }
            if (asset === "x.png") { line(4,4,12,12); line(12,4,4,12) }
            else if (asset === "minus.png") line(3,8,13,8)
            else if (asset === "square.png") c.strokeRect(3,3,10,10)
            else if (asset === "copy-simple.png") { c.strokeRect(5,3,8,8); line(3,5,3,13); line(3,13,11,13) }
            else if (asset === "sidebar-simple.png") { c.strokeRect(2,3,12,10); line(6,3,6,13) }
            else if (asset === "magnifying-glass.png") { c.beginPath(); c.arc(7,7,4.5,0,Math.PI*2); c.stroke(); line(10.5,10.5,14,14) }
            else if (asset === "arrow-right.png") { line(3,8,13,8); line(9,4,13,8); line(13,8,9,12) }
            else if (asset.indexOf("plus-circle") === 0) { c.beginPath(); c.arc(8,8,6,0,Math.PI*2); c.stroke(); line(8,5,8,11); line(5,8,11,8) }
            else { c.beginPath(); c.arc(8,8,5.5,0.4,5.5); c.stroke(); line(12,2.5,12.7,6.5); line(12.7,6.5,9,5.5) }
            c.restore()
        }
    }
}
