import QtQuick 2.15

Canvas {
    id: icon

    property string iconId: ""
    property color strokeColor: Ui.color("text1")
    property real lineWidth: 1.25

    implicitWidth: 16
    implicitHeight: 16
    renderTarget: Canvas.Image
    renderStrategy: Canvas.Cooperative

    onIconIdChanged: requestPaint()
    onStrokeColorChanged: requestPaint()
    onLineWidthChanged: requestPaint()
    onWidthChanged: requestPaint()
    onHeightChanged: requestPaint()

    property color themeRepaintColor: Ui.color("text")
    onThemeRepaintColorChanged: requestPaint()
    onPaint: {
        var context = getContext("2d")
        context.clearRect(0, 0, width, height)
        var scale = Math.min(width, height) / 14.0
        var offsetX = (width - 14.0 * scale) / 2.0
        var offsetY = (height - 14.0 * scale) / 2.0
        function px(value) { return offsetX + value * scale }
        function py(value) { return offsetY + value * scale }
        function line(points) {
            context.beginPath()
            context.moveTo(px(points[0]), py(points[1]))
            for (var i = 2; i < points.length; i += 2)
                context.lineTo(px(points[i]), py(points[i + 1]))
            context.stroke()
        }
        function oval(left, top, right, bottom) {
            context.beginPath()
            context.ellipse(px(left), py(top), (right - left) * scale, (bottom - top) * scale)
            context.stroke()
        }
        context.strokeStyle = strokeColor
        context.lineWidth = lineWidth
        context.lineCap = "round"
        context.lineJoin = "round"
        if (iconId === "social_security") {
            context.strokeRect(px(2.5), py(1.5), 9 * scale, 11 * scale)
            line([5, 5, 9, 5]); line([5, 8, 9, 8])
        } else if (iconId === "insurance_ledger") {
            oval(1.5, 1.5, 12.5, 12.5); line([4.6, 7, 6.3, 8.7, 9.6, 5.4])
        } else if (iconId === "data_statistics") {
            line([2.5, 12, 2.5, 7]); line([7, 12, 7, 2.5]); line([11.5, 12, 11.5, 5])
        } else if (iconId === "salary_split") {
            line([7, 2, 7, 6]); line([7, 6, 3, 11]); line([7, 6, 11, 11])
        } else if (iconId === "salary_merge") {
            line([3, 3, 7, 8]); line([11, 3, 7, 8]); line([7, 8, 7, 12])
        } else if (iconId === "personnel_change_merge") {
            line([2, 4.5, 10, 4.5]); line([8, 2, 10.5, 4.5, 8, 7])
            line([12, 9.5, 4, 9.5]); line([6, 7, 3.5, 9.5, 6, 12])
        } else if (iconId === "archive_import") {
            context.strokeRect(px(2), py(4.5), 10 * scale, 7.5 * scale)
            line([2, 7, 12, 7]); line([7, 4.5, 7, 2.5])
        } else if (iconId === "material_collector") {
            context.strokeRect(px(2.5), py(3), 9 * scale, 8.5 * scale)
            line([2.5, 6, 11.5, 6]); line([7, 6, 7, 11.5])
        } else if (iconId === "folder_rename") {
            line([2, 10.5, 2, 4, 3.5, 2.5, 6, 2.5, 7.2, 4, 10.5, 4, 12, 5.5, 12, 10.5, 10.5, 12, 3.5, 12, 2, 10.5])
        } else if (iconId === "tutorial") {
            oval(1.5, 1.5, 12.5, 12.5); line([7, 6.5, 7, 10]); line([7, 4, 7, 4.45])
        } else if (iconId === "clock") {
            oval(1.5, 1.5, 12.5, 12.5); line([7, 4, 7, 7.2, 9, 8.6])
        } else if (iconId === "plus_circle") {
            oval(1.5, 1.5, 12.5, 12.5); line([7, 4.2, 7, 9.8]); line([4.2, 7, 9.8, 7])
        } else if (iconId === "folder_open") {
            line([1.7, 11.5, 2.4, 5.4, 5.3, 5.4, 6.5, 3.5, 11.9, 3.5, 12.4, 5.4])
            line([2.4, 6.2, 12.4, 6.2, 11, 11.5, 1.7, 11.5])
        } else if (iconId === "chevron_down") {
            line([3.2, 5.2, 7, 8.9, 10.8, 5.2])
        } else if (iconId === "run_log") {
            context.strokeRect(px(2.4), py(1.8), 9.2 * scale, 10.4 * scale)
            line([4.5, 5, 9.5, 5]); line([4.5, 7.4, 9.5, 7.4]); line([4.5, 9.8, 8, 9.8])
        } else if (iconId === "ai_spark") {
            line([7, 1.5, 7, 12.5]); line([1.5, 7, 12.5, 7])
            line([4, 4, 10, 10]); line([10, 4, 4, 10])
        } else if (iconId === "plus") {
            line([7, 2.6, 7, 11.4]); line([2.6, 7, 11.4, 7])
        } else if (iconId === "new_chat") {
            line([4.4, 2.4, 9.6, 2.4, 11.6, 4.4, 11.6, 9.6, 9.6, 11.6, 4.4, 11.6, 2.4, 9.6, 2.4, 4.4, 4.4, 2.4])
            line([7, 5.2, 7, 8.8]); line([5.2, 7, 8.8, 7])
        } else if (iconId === "arrow_up") {
            line([7, 11.6, 7, 3.1]); line([3.2, 6.9, 7, 3.1, 10.8, 6.9])
        } else if (iconId === "gear") {
            line([2.2, 4.2, 11.8, 4.2]); line([5.4, 2.8, 5.4, 5.6])
            line([2.2, 7, 11.8, 7]); line([8.8, 5.6, 8.8, 8.4])
            line([2.2, 9.8, 11.8, 9.8]); line([6.2, 8.4, 6.2, 11.2])
        } else if (iconId === "expand") {
            line([8.7, 1.7, 12.2, 1.7, 12.2, 5.2]); line([12.2, 1.7, 5.8, 8.2])
            line([10.5, 7.6, 10.5, 11.1, 9.3, 12.2, 3, 12.2, 1.8, 11.1, 1.8, 4.7, 3, 3.5, 6.2, 3.5])
        } else if (iconId === "close") {
            line([3.4, 3.4, 10.6, 10.6]); line([10.6, 3.4, 3.4, 10.6])
        } else if (iconId === "check") {
            line([2.6, 7.4, 5.6, 10.4, 11.4, 3.8])
        } else if (iconId === "sheet") {
            context.strokeRect(px(2.4), py(1.8), 9.2 * scale, 10.4 * scale)
            line([2.4, 5.2, 11.6, 5.2]); line([2.4, 8.6, 11.6, 8.6])
            line([7, 5.2, 7, 12.2])
        } else if (iconId === "chevron_left") {
            line([9.9, 3.2, 5.1, 7, 9.9, 10.8])
        } else if (iconId === "chevron_right") {
            line([4.1, 3.2, 8.9, 7, 4.1, 10.8])
        } else if (iconId === "arrow_down") {
            line([7, 2.6, 7, 11.1]); line([3.2, 7.3, 7, 11.1, 10.8, 7.3])
        } else if (iconId === "image") {
            // 相框 + 远山 + 太阳：一眼能和「表格」图标区分开
            context.strokeRect(px(1.8), py(2.4), 10.4 * scale, 9.2 * scale)
            line([1.8, 9.4, 5.1, 6.0, 7.9, 8.4, 10.0, 6.5, 12.2, 8.5])
            oval(4.5, 4.9, 5.4, 5.8)
        } else if (iconId === "copy") {
            context.strokeRect(px(4.6), py(4.6), 7.0 * scale, 7.4 * scale)
            line([9.4, 2.2, 2.6, 2.2, 2.6, 9.0])
        } else if (iconId === "edit") {
            line([2.6, 11.4, 3.3, 8.9, 9.7, 2.5])
            line([3.3, 8.9, 5.1, 10.7, 2.6, 11.4])
            line([8.5, 3.7, 10.3, 5.5])
        } else if (iconId === "search") {
            oval(5.5, 5.5, 9.0, 9.0); line([8.3, 8.3, 11.9, 11.9])
        } else if (iconId === "trash") {
            line([2.4, 3.7, 11.6, 3.7])
            line([3.7, 3.7, 4.4, 11.6, 9.6, 11.6, 10.3, 3.7])
            line([5.5, 3.7, 5.5, 2.2, 8.5, 2.2, 8.5, 3.7])
        } else {
            oval(3, 3, 11, 11)
        }
    }
}
