import QtQuick 2.15
import QtQuick.Window 2.15

Item {
    id: edges
    property var window
    visible: window.visibility !== Window.Maximized && window.visibility !== Window.FullScreen
    Repeater {
        model: [Qt.LeftEdge, Qt.RightEdge, Qt.TopEdge, Qt.BottomEdge,
                Qt.LeftEdge | Qt.TopEdge, Qt.RightEdge | Qt.TopEdge,
                Qt.LeftEdge | Qt.BottomEdge, Qt.RightEdge | Qt.BottomEdge]
        MouseArea {
            readonly property bool atLeft: (modelData & Qt.LeftEdge) !== 0
            readonly property bool atTop: (modelData & Qt.TopEdge) !== 0
            readonly property bool atRight: (modelData & Qt.RightEdge) !== 0
            readonly property bool atBottom: (modelData & Qt.BottomEdge) !== 0
            width: atLeft || atRight ? 6 : edges.width - 12
            height: atTop || atBottom ? 6 : edges.height - 12
            x: atLeft ? 0 : atRight ? edges.width - 6 : 6
            y: atTop ? 0 : atBottom ? edges.height - 6 : 6
            cursorShape: index < 2 ? Qt.SizeHorCursor : index < 4 ? Qt.SizeVerCursor : index === 4 || index === 7 ? Qt.SizeFDiagCursor : Qt.SizeBDiagCursor
            onPressed: edges.window.startSystemResize(modelData)
        }
    }
}
