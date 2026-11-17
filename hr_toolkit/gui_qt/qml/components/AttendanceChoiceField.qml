import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15

Item {
    id: field

    // Keep company/location values verbatim; translate only explicit UI labels.
    property string value: ""
    property var choices: []
    property var optionLabels: ({})
    property string placeholderText: ""
    implicitWidth: 260
    implicitHeight: 40

    function labelFor(value) {
        return Object.prototype.hasOwnProperty.call(optionLabels, value) ? Ui.text(optionLabels[value]) : value
    }

    AppTextField {
        id: editor
        anchors.left: parent.left
        anchors.right: picker.left
        anchors.rightMargin: 4
        anchors.verticalCenter: parent.verticalCenter
        height: field.height
        font.pixelSize: 14
        text: field.labelFor(field.value)
        placeholderText: field.placeholderText
        placeholderTextColor: Ui.color("text1")
        Accessible.name: field.placeholderText
        background: Rectangle {
            radius: 6
            color: editor.enabled ? Ui.color("input") : Ui.color("disabledSurface")
            border.width: editor.activeFocus ? 2 : 1
            border.color: editor.activeFocus ? Ui.color("accent") : Ui.color("muted")
        }
        onTextEdited: {
            if (text !== field.labelFor(field.value)) field.value = text
        }
        Keys.onDownPressed: if (picker.count) picker.popup.open()
    }

    AppComboBox {
        id: picker
        anchors.right: parent.right
        anchors.verticalCenter: parent.verticalCenter
        height: field.height
        width: Math.max(76, Math.ceil(contentItem.implicitWidth) + leftPadding + rightPadding)
        leftPadding: 11
        rightPadding: 32
        font.pixelSize: 14
        model: field.choices.map(field.labelFor)
        translateOptions: false
        currentIndex: field.choices.indexOf(field.value)
        displayText: Ui.text("选择")
        enabled: field.enabled && count > 0
        Accessible.name: Ui.text("选择已有选项") + ": " + field.placeholderText
        popup.width: field.width
        popup.x: width - field.width
        popup.background: Rectangle {
            radius: 6
            color: Ui.color("surface")
            border.color: Ui.color("muted")
            border.width: 1
        }
        background: Rectangle {
            radius: 6
            color: picker.enabled ? (picker.down ? Ui.color("pressed") : Ui.color("selection")) : Ui.color("disabledSurface")
            border.width: picker.activeFocus || picker.popup.visible ? 2 : 1
            border.color: picker.activeFocus || picker.popup.visible ? Ui.color("accent") : Ui.color("muted")
        }
        indicator: Canvas {
            x: picker.width - width - 10
            y: (picker.height - height) / 2
            width: 14
            height: 10
            property color strokeColor: picker.enabled ? Ui.color("text") : Ui.color("muted")
            onStrokeColorChanged: requestPaint()
            onPaint: {
                var context = getContext("2d")
                context.clearRect(0, 0, width, height)
                context.strokeStyle = strokeColor
                context.lineWidth = 2
                context.lineCap = "round"
                context.lineJoin = "round"
                context.beginPath()
                context.moveTo(2, 3)
                context.lineTo(7, 7)
                context.lineTo(12, 3)
                context.stroke()
            }
        }
        delegate: ItemDelegate {
            id: optionDelegate
            readonly property bool currentChoice: index === picker.currentIndex
            readonly property color foreground: highlighted ? Ui.color("onAccent") : Ui.color("text")
            width: picker.popup.availableWidth
            height: 40
            leftPadding: 12
            rightPadding: 12
            hoverEnabled: true
            highlighted: picker.highlightedIndex === index
            text: field.labelFor(field.choices[index])
            Accessible.name: text
            contentItem: RowLayout {
                spacing: 10
                Text {
                    id: optionLabel
                    Layout.fillWidth: true
                    text: optionDelegate.text
                    textFormat: Text.PlainText
                    elide: Text.ElideRight
                    color: optionDelegate.foreground
                    font.pixelSize: 14
                    font.weight: optionDelegate.currentChoice ? Font.DemiBold : Font.Normal
                    verticalAlignment: Text.AlignVCenter
                }
                Text {
                    visible: optionDelegate.currentChoice
                    text: Ui.text("已选")
                    color: optionDelegate.foreground
                    font.pixelSize: 12
                }
            }
            background: Rectangle {
                radius: 4
                color: optionDelegate.highlighted ? Ui.color("accent")
                    : optionDelegate.currentChoice ? Ui.color("selection")
                    : optionDelegate.hovered ? Ui.color("hover") : Ui.color("surface")
                border.width: optionDelegate.currentChoice ? 1 : 0
                border.color: Ui.color("accent")
            }
            AppToolTip {
                visible: picker.popup.visible && optionDelegate.hovered && optionLabel.truncated
                text: optionDelegate.text
            }
        }
        onActivated: function(index) { field.value = field.choices[index] }
    }
}
