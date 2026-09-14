import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15

AppDialog {
    id: dialog
    property var backend
    property var mappingData: ({roles: [], sheets: []})
    property int roleIndex: 0
    property int sheetIndex: 0
    property int headerRow: 1
    property var chosen: ({})
    property var role: mappingData.roles.length ? mappingData.roles[roleIndex] : ({fields: {}, required: []})
    property var sheet: mappingData.sheets.length ? mappingData.sheets[sheetIndex] : ({rows: []})
    title: "请选择这份表的对应关系"
    width: Math.min(parent ? parent.width - 32 : 820, 820)
    height: Math.min(parent ? parent.height - 32 : 720, 720)
    x: parent ? (parent.width - width) / 2 : 0
    y: parent ? (parent.height - height) / 2 : 0
    rejectText: "暂不处理"
    acceptText: "保存对应关系"
    acceptButtonEnabled: backend && !backend.busy

    function normalized(value) { return String(value).replace(/\s/g, "").toLowerCase() }
    function columns() {
        var values = sheet.rows[headerRow - 1] || []
        var result = [{col: 0, label: "请选择；可选字段可留空"}]
        for (var i = 0; i < values.length; i++)
            if (values[i]) result.push({col: i + 1, label: "第 " + (i + 1) + " 列 · " + values[i]})
        return result
    }
    function resetChoices() {
        var values = sheet.rows[headerRow - 1] || []
        var result = {}
        Object.keys(role.fields).forEach(function(name) {
            var aliases = role.fields[name].map(normalized)
            var matches = []
            for (var i = 0; i < values.length; i++)
                if (aliases.indexOf(normalized(values[i])) >= 0) matches.push(i + 1)
            result[name] = (role.required.indexOf(name) >= 0 || (role.one_of || []).indexOf(name) >= 0) && matches.length === 1 ? matches[0] : 0
        })
        chosen = result
    }
    function showData(payload) {
        mappingData = payload
        roleIndex = 0; sheetIndex = 0; headerRow = payload.row || 1
        extra.checked = false
        resetChoices()
        open()
    }
    function columnIndex(name, model) {
        for (var i = 0; i < model.length; i++) if (model[i].col === chosen[name]) return i
        return 0
    }
    onAccepted: backend.saveTemplateChoice(JSON.stringify({role: role.key, sheet: sheet.name, row: headerRow, columns: chosen}))
    contentItem: Flickable {
        clip: true
        contentHeight: body.implicitHeight
        contentWidth: width
        ScrollBar.vertical: ScrollBar {}
        ColumnLayout {
            id: body
            width: parent.width
            spacing: 12
            Text { Layout.fillWidth: true; text: (dialog.mappingData.file || "") + "\n" + (dialog.mappingData.message || ""); textFormat: Text.PlainText; wrapMode: Text.Wrap; color: "#A26713" }
            Text { Layout.fillWidth: true; text: "这里只对应列名，不换算金额或时间单位。请确认两列的意思和单位相同。保存后请重新点击开始处理；不会修改原表。"; wrapMode: Text.Wrap; color: "#55534D"; font.pixelSize: 12 }
            AppComboBox {
                Layout.fillWidth: true
                model: dialog.mappingData.roles.map(function(r) { return r.label })
                currentIndex: dialog.roleIndex
                onActivated: function(index) { dialog.roleIndex = index; dialog.resetChoices() }
            }
            AppComboBox {
                Layout.fillWidth: true
                model: dialog.mappingData.sheets.map(function(s) { return s.name })
                currentIndex: dialog.sheetIndex
                onActivated: function(index) { dialog.sheetIndex = index; dialog.headerRow = 1; dialog.resetChoices() }
            }
            RowLayout {
                Text { text: "原表的表头在第" }
                SpinBox { from: 1; to: Math.max(1, dialog.sheet.rows.length); value: dialog.headerRow; editable: true; onValueModified: { dialog.headerRow = value; dialog.resetChoices() } }
                Text { text: "行（显示前30行、512列）"; font.pixelSize: 12 }
            }
            AppCheckBox { id: extra; text: "展开其他可选字段" }
            Repeater {
                model: Object.keys(dialog.role.fields)
                delegate: RowLayout {
                    property string fieldName: modelData
                    property bool requiredField: dialog.role.required.indexOf(fieldName) >= 0
                    visible: requiredField || (dialog.role.one_of || []).indexOf(fieldName) >= 0 || extra.checked
                    Layout.fillWidth: true
                    Text { Layout.preferredWidth: 180; text: fieldName + (requiredField ? "（必填）" : ""); wrapMode: Text.Wrap; textFormat: Text.PlainText; font.pixelSize: 12 }
                    AppComboBox {
                        Layout.fillWidth: true
                        model: dialog.columns(); textRole: "label"
                        currentIndex: dialog.columnIndex(fieldName, model)
                        onActivated: function(index) { var updated = Object.assign({}, dialog.chosen); updated[fieldName] = model[index].col; dialog.chosen = updated }
                    }
                }
            }
        }
    }
}
