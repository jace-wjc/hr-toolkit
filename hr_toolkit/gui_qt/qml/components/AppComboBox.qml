import QtQuick 2.15
import QtQuick.Controls 2.15

ComboBox {
    id: control

    // Source filenames, worksheet names and cell values must remain verbatim.
    property bool translateOptions: true
    // Optional UI explanations keyed by the original option label, never its value.
    property var optionDescriptions: ({})
    function descriptionFor(label) {
        return Ui.text(optionDescriptions[String(label)] || "")
    }

    implicitHeight: 36
    implicitWidth: 220
    leftPadding: 11
    rightPadding: 34
    topPadding: 7
    bottomPadding: 7
    hoverEnabled: true
    HoverHandler { enabled: !control.editable; cursorShape: control.enabled ? Qt.PointingHandCursor : Qt.ArrowCursor }
    font.pixelSize: 13

    contentItem: Text {
        id: selectedLabel
        leftPadding: 0
        rightPadding: 0
        text: control.translateOptions ? Ui.text(control.displayText) : control.displayText
        color: control.enabled ? Ui.color("text") : Ui.color("disabledText")
        font: control.font
        verticalAlignment: Text.AlignVCenter
        elide: Text.ElideRight
    }

    AppToolTip {
        visible: control.hovered && !control.down && !control.popup.visible
                 && (selectedLabel.truncated || control.descriptionFor(control.displayText).length > 0)
        text: selectedLabel.text + (control.descriptionFor(control.displayText)
                                   ? "\n" + control.descriptionFor(control.displayText) : "")
    }

    indicator: Canvas {
        x: control.width - width - 11
        y: (control.height - height) / 2
        width: 12
        height: 8
        property color themeRepaintColor: Ui.color("text")
        onThemeRepaintColorChanged: requestPaint()
        onPaint: {
            var context = getContext("2d")
            context.clearRect(0, 0, width, height)
            context.strokeStyle = control.enabled ? Ui.color("muted") : Ui.color("disabledText")
            context.lineWidth = 1.4
            context.lineCap = "round"
            context.lineJoin = "round"
            context.beginPath()
            context.moveTo(1.5, 2)
            context.lineTo(6, 6)
            context.lineTo(10.5, 2)
            context.stroke()
        }
    }

    background: Rectangle {
        radius: 6
        color: control.enabled ? Ui.color("input") : Ui.color("disabledSurface")
        border.width: 1
        border.color: control.activeFocus ? Ui.color("accent") : Ui.color("border")
    }

    delegate: ItemDelegate {
        id: optionDelegate
        readonly property string originalLabel: control.textRole ? modelData[control.textRole] : modelData
        readonly property string description: control.descriptionFor(originalLabel)
        width: control.popup.availableWidth
        height: 34
        hoverEnabled: true
        highlighted: control.highlightedIndex === index
        contentItem: Text {
            id: optionLabel
            text: control.translateOptions ? Ui.text(control.textRole ? modelData[control.textRole] : modelData) : (control.textRole ? modelData[control.textRole] : modelData)
            color: Ui.color("text")
            font.pixelSize: 13
            verticalAlignment: Text.AlignVCenter
            elide: Text.ElideRight
        }
        AppToolTip {
            visible: control.popup.visible && optionDelegate.hovered && !optionDelegate.down
                     && (optionLabel.truncated || optionDelegate.description.length > 0)
            text: optionLabel.text + (optionDelegate.description ? "\n" + optionDelegate.description : "")
        }
        background: Rectangle {
            radius: 4
            color: parent.highlighted ? Ui.color("selection") : (parent.hovered ? Ui.color("hover") : Ui.color("surface"))
        }
    }

    popup: Popup {
        y: control.height - 1
        width: control.width
        implicitHeight: Math.min(contentItem.implicitHeight + topPadding + bottomPadding, 260)
        // Inset the list so scrolling rows cannot cover the rounded corners.
        padding: 6
        contentItem: ListView {
            clip: true
            implicitHeight: contentHeight
            model: control.popup.visible ? control.delegateModel : null
            currentIndex: control.highlightedIndex
            ScrollIndicator.vertical: ScrollIndicator {}
        }
        background: Rectangle {
            radius: 6
            color: Ui.color("surface")
            border.color: Ui.color("border")
            border.width: 1
        }
    }
}
