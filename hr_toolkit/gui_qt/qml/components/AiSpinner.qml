import QtQuick 2.15

// 原型中的橙色日芒指示器：12 条射线，仅做旋转变换，不逐帧重绘画布。
Canvas {
    id: spinner

    property bool running: false
    property color rayColor: Ui.color("markRay")

    implicitWidth: 20
    implicitHeight: 20
    renderTarget: Canvas.Image
    renderStrategy: Canvas.Cooperative

    onRayColorChanged: requestPaint()
    onWidthChanged: requestPaint()
    onHeightChanged: requestPaint()

    property color themeRepaintColor: Ui.color("text")
    onThemeRepaintColorChanged: requestPaint()

    onPaint: {
        var context = getContext("2d")
        context.clearRect(0, 0, width, height)
        var centerX = width / 2
        var centerY = height / 2
        var radius = Math.min(width, height) / 2
        context.strokeStyle = rayColor
        context.lineCap = "round"
        for (var index = 0; index < 12; ++index) {
            var angle = index * Math.PI / 6
            var outer = index % 2 === 0 ? radius : radius * 0.78
            context.beginPath()
            context.lineWidth = index % 2 === 0 ? 1.7 : 1.15
            context.moveTo(centerX + Math.cos(angle) * radius * 0.26,
                           centerY + Math.sin(angle) * radius * 0.26)
            context.lineTo(centerX + Math.cos(angle) * outer,
                           centerY + Math.sin(angle) * outer)
            context.stroke()
        }
    }

    RotationAnimator on rotation {
        running: spinner.running && spinner.visible
        from: 0
        to: 360
        duration: 1150
        loops: Animation.Infinite
    }
}
