import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15

AppTextField {
    id: control
    property bool choosingDate: false
    signal datePicked(string value)
    rightPadding: 35
    inputMethodHints: Qt.ImhDate
    Accessible.description: Ui.text("可输入日期，或按 Alt+下方向键打开日历")

    // Calendar positioning only; the controller retains all input validation.
    // Construct local dates explicitly so UTC parsing never shifts a day.
    function makeDate(year, month, day) {
        var value = new Date(0)
        value.setHours(12, 0, 0, 0)
        value.setFullYear(year, month, day)
        return value
    }
    function parseDate(value) {
        var text = String(value || "").trim()
        if (/^\d{8}$/.test(text)) text = text.slice(0, 4) + "-" + text.slice(4, 6) + "-" + text.slice(6, 8)
        var parts = /^(\d{4})[-/.年]\s*(\d{1,2})[-/.月]\s*(\d{1,2})日?$/.exec(text)
        if (!parts) return null
        var year = Number(parts[1]), month = Number(parts[2]) - 1, day = Number(parts[3])
        var date = makeDate(year, month, day)
        return year >= 1 && year <= 9999 && date.getFullYear() === year
            && date.getMonth() === month && date.getDate() === day ? date : null
    }
    function sameDay(left, right) {
        return left && right && left.getFullYear() === right.getFullYear()
            && left.getMonth() === right.getMonth() && left.getDate() === right.getDate()
    }
    function dateText(value) {
        return ("0000" + value.getFullYear()).slice(-4) + "-"
            + ("0" + (value.getMonth() + 1)).slice(-2) + "-" + ("0" + value.getDate()).slice(-2)
    }
    function pickDate(value) {
        var text = value ? dateText(value) : ""
        control.text = text
        calendarPopup.close()
        // Emit last: updating the form can recreate this input component.
        datePicked(text)
    }
    function openCalendar() {
        if (!enabled) return
        calendarPopup.selectedDate = parseDate(text)
        calendarPopup.today = new Date()
        var initial = calendarPopup.selectedDate || calendarPopup.today
        calendarPopup.viewYear = initial.getFullYear()
        calendarPopup.viewMonth = initial.getMonth()
        var point = mapToItem(calendarPopup.parent, 0, 0)
        calendarPopup.x = Math.max(8, Math.min(point.x, calendarPopup.parent.width - calendarPopup.width - 8))
        var below = point.y + height + 5
        calendarPopup.y = below + calendarPopup.height <= calendarPopup.parent.height - 8
            ? below : Math.max(8, point.y - calendarPopup.height - 5)
        choosingDate = true
        calendarPopup.open()
    }
    Keys.onPressed: {
        if (event.key === Qt.Key_F4 || (event.key === Qt.Key_Down && (event.modifiers & Qt.AltModifier))) {
            event.accepted = true
            openCalendar()
        }
    }

    AppButton {
        id: calendarButton
        anchors.right: parent.right; anchors.rightMargin: 3
        anchors.verticalCenter: parent.verticalCenter
        width: 28; height: 28; variant: "link"
        focusPolicy: Qt.NoFocus
        Accessible.name: Ui.text("选择日期")
        onClicked: control.openCalendar()
        contentItem: Item {
            Rectangle {
                anchors.centerIn: parent; width: 14; height: 12; radius: 2
                color: "transparent"; border.width: 1
                border.color: control.enabled ? Ui.color("text") : Ui.color("disabledText")
                Rectangle { x: 1; y: 4; width: 12; height: 1; color: parent.border.color }
                Rectangle { x: 3; y: -2; width: 1; height: 4; color: parent.border.color }
                Rectangle { x: 10; y: -2; width: 1; height: 4; color: parent.border.color }
            }
        }
        AppToolTip { visible: calendarButton.hovered; text: Ui.text("选择日期") }
    }

    Popup {
        id: calendarPopup
        parent: Overlay.overlay
        width: Math.min(320, parent ? parent.width - 16 : 320)
        padding: 12
        focus: true
        closePolicy: Popup.CloseOnEscape | Popup.CloseOnPressOutside
        enter: Transition {}
        exit: Transition {}
        property int viewYear: new Date().getFullYear()
        property int viewMonth: new Date().getMonth()
        property var selectedDate: null
        property var today: new Date()
        readonly property int firstDayOffset: (control.makeDate(viewYear, viewMonth, 1).getDay() + 6) % 7
        onClosed: control.choosingDate = false

        function moveMonth(delta) {
            var value = control.makeDate(viewYear, viewMonth + delta, 1)
            if (value.getFullYear() < 1 || value.getFullYear() > 9999) return
            viewYear = value.getFullYear()
            viewMonth = value.getMonth()
        }
        background: Rectangle { radius: 8; color: Ui.color("surface"); border.color: Ui.color("border") }
        contentItem: ColumnLayout {
            spacing: 8
            RowLayout {
                Layout.fillWidth: true; spacing: 5
                AppButton {
                    implicitWidth: 28; implicitHeight: 30; variant: "link"
                    enabled: calendarPopup.viewYear > 1 || calendarPopup.viewMonth > 0
                    Accessible.name: Ui.text("上个月")
                    contentItem: ThemedImage { source: "arrow-right.png"; mirror: true; fillMode: Image.PreserveAspectFit }
                    onClicked: calendarPopup.moveMonth(-1)
                }
                SpinBox {
                    Layout.preferredWidth: 116; Layout.minimumWidth: 0
                    font.pixelSize: 13
                    from: 1; to: 9999; editable: true
                    // 年份不分组；校验器与 String/Number 必须使用相同的数字格式。
                    locale: Qt.locale("C")
                    value: calendarPopup.viewYear
                    textFromValue: function(value, locale) { return String(value) }
                    valueFromText: function(text, locale) { return Number(text) }
                    onValueModified: calendarPopup.viewYear = value
                    Accessible.name: Ui.text("年份")
                    palette.text: Ui.color("text"); palette.base: Ui.color("input")
                    palette.button: Ui.color("input"); palette.buttonText: Ui.color("text")
                }
                AppComboBox {
                    Layout.fillWidth: true; Layout.minimumWidth: 0; Layout.preferredWidth: 90
                    model: ["1月", "2月", "3月", "4月", "5月", "6月", "7月", "8月", "9月", "10月", "11月", "12月"]
                    currentIndex: calendarPopup.viewMonth
                    onActivated: calendarPopup.viewMonth = index
                    Accessible.name: Ui.text("月份")
                }
                AppButton {
                    implicitWidth: 28; implicitHeight: 30; variant: "link"
                    enabled: calendarPopup.viewYear < 9999 || calendarPopup.viewMonth < 11
                    Accessible.name: Ui.text("下个月")
                    contentItem: ThemedImage { source: "arrow-right.png"; fillMode: Image.PreserveAspectFit }
                    onClicked: calendarPopup.moveMonth(1)
                }
            }
            GridLayout {
                Layout.fillWidth: true; columns: 7; columnSpacing: 2; rowSpacing: 2
                Repeater {
                    model: ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]
                    delegate: Text {
                        Layout.fillWidth: true; Layout.preferredHeight: 24
                        text: Ui.text(modelData); color: Ui.color("muted"); font.pixelSize: 11
                        horizontalAlignment: Text.AlignHCenter; verticalAlignment: Text.AlignVCenter
                    }
                }
                Repeater {
                    model: 42
                    delegate: AppButton {
                        id: dayButton
                        readonly property var day: control.makeDate(calendarPopup.viewYear, calendarPopup.viewMonth, index - calendarPopup.firstDayOffset + 1)
                        readonly property bool selected: control.sameDay(day, calendarPopup.selectedDate)
                        readonly property bool isToday: control.sameDay(day, calendarPopup.today)
                        Layout.fillWidth: true; Layout.minimumWidth: 0
                        implicitWidth: 34; implicitHeight: 30
                        enabled: day.getFullYear() >= 1 && day.getFullYear() <= 9999
                        text: String(day.getDate()); variant: selected ? "primary" : "link"
                        textColor: selected ? Ui.color("onAccent") : day.getMonth() === calendarPopup.viewMonth ? Ui.color("text") : Ui.color("faint")
                        Accessible.name: control.dateText(day)
                        onClicked: control.pickDate(day)
                        background: Rectangle {
                            radius: 5
                            color: dayButton.selected ? Ui.color("accent") : dayButton.hovered ? Ui.color("hover") : "transparent"
                            border.width: dayButton.isToday ? 1 : 0; border.color: Ui.color("accent")
                        }
                    }
                }
            }
            Rectangle { Layout.fillWidth: true; height: 1; color: Ui.color("divider") }
            RowLayout {
                Layout.fillWidth: true
                AppButton { text: "今天"; implicitHeight: 28; onClicked: control.pickDate(new Date()) }
                Item { Layout.fillWidth: true }
                AppButton { text: "清空"; implicitHeight: 28; onClicked: control.pickDate(null) }
            }
        }
    }
}
