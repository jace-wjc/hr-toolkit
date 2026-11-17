import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15

AppDialog {
    id: dialog
    objectName: "attendanceRulesDialog"
    property var backend
    property var config: ({rules: [], assignments: []})
    property var rows: []
    property var selected: ({})
    property bool pending: false
    property string page: "assign"
    property string errorText: ""
    property int editRuleIndex: -1
    property int editAssignmentIndex: -1
    property bool working: backend ? backend.busy : false
    property int unresolved: rows.filter(function(row) { return !!row.problem }).length
    property var monthOptions: [0, 3, 6, 12]
    property var hourOptions: [0, 7, 8]
    property var shownRows: buildRows()
    title: Ui.text(pending ? "确认考勤公司、驻地和规则" : "考勤识别规则")
    width: Math.min(parent ? parent.width - 24 : 960, 960)
    height: Math.min(parent ? parent.height - 24 : 790, 790)
    x: parent ? (parent.width - width) / 2 : 0
    y: parent ? (parent.height - height) / 2 : 0
    acceptText: pending ? "确认并继续处理" : "保存设置"
    rejectText: "返回"
    acceptButtonEnabled: !working && (!pending || unresolved === 0)

    function copy(value) { return JSON.parse(JSON.stringify(value)) }
    function initialize(value, isPending) {
        pending = isPending
        config = copy(value.config || value)
        rows = copy(value.rows || [])
        selected = ({})
        errorText = ""
        editRuleIndex = -1
        editAssignmentIndex = -1
        editRule(-1)
        search.text = ""
        viewMode.currentIndex = 0
        company.editText = ""
        location.selectedRawValue = ""
        location.editText = ""
        keyword.text = ""
        customRule.checked = false
        remember.checked = true
        page = pending ? "assign" : "rules"
        open()
    }
    function showData(value) { initialize(value, true) }
    function showSettings(value) { initialize(value, false) }
    function locationLabel(value) { return value === "公司默认" ? Ui.text("公司默认") : value }
    function locationValue(combo) {
        var value = combo.editText.trim(), index = combo.currentIndex
        // Translate the reserved option's label, never a stored location name.
        if (combo.selectedRawValue && value === locationLabel(combo.selectedRawValue)) return combo.selectedRawValue
        return index >= 0 && index < combo.rawValues.length && value === locationLabel(combo.rawValues[index])
            ? combo.rawValues[index] : value
    }
    function assignmentLabel(item) {
        var suffix = " / 全组人员", label = String(item.label || "")
        return !item.name && label.slice(-suffix.length) === suffix
            ? label.slice(0, -suffix.length) + " / " + Ui.text("全组人员") : label
    }
    function ruleText(row) {
        if (row.problem) return (row.company || Ui.text("未指定公司")) + " / "
            + (locationLabel(row.location) || Ui.text("未指定驻地")) + ": " + Ui.text(row.problem)
        return (row.company || Ui.text("未指定公司")) + " / " + (locationLabel(row.location) || Ui.text("旧表已确认"))
            + " · " + Ui.text(row.valid_months + " 个月") + " · " + Ui.text(row.hours_per_day + " 小时/天")
    }
    function buildRows() {
        var groups = {}, result = [], needle = String(search.text || "").toLowerCase()
        for (var i = 0; i < rows.length; ++i) {
            var row = rows[i]
            var haystack = [row.name, row.department, row.file, row.sheet, row.company, row.location, locationLabel(row.location)].join(" ").toLowerCase()
            if (needle && haystack.indexOf(needle) < 0) continue
            var key = viewMode.currentIndex === 1 ? row.id : JSON.stringify([row.source, row.sheet, row.raw_company, row.raw_location, row.kind])
            if (!groups[key]) {
                groups[key] = {ids: [], labels: [], rules: [], problem: false,
                    title: viewMode.currentIndex === 1 ? row.name + " / " + row.department : row.file + " / " + row.sheet,
                    kind: row.kind, source: row.source}
                result.push(groups[key])
            }
            var group = groups[key], text = ruleText(row)
            group.ids.push(row.id)
            group.labels.push(row.name)
            if (group.rules.indexOf(text) < 0) group.rules.push(text)
            group.problem = group.problem || !!row.problem
        }
        return result
    }
    function allSelected(ids) { return ids.every(function(id) { return !!selected[id] }) }
    function selectRows(ids, checked) {
        var value = copy(selected)
        ids.forEach(function(id) { if (checked) value[id] = true; else delete value[id] })
        selected = value
    }
    function checkConfig(value, choices) {
        var response = backend.previewAttendanceRules(JSON.stringify({config: value, pending: pending, selections: choices || ({})}))
        errorText = response.error || ""
        if (errorText) return false
        config = copy(response.config)
        if (pending) rows = copy(response.rows)
        return true
    }
    function applySelection() {
        var ids = Object.keys(selected)
        if (!ids.length) { errorText = "请先勾选要设置的文件组或人员。"; return }
        var choice = {company: company.editText.trim(), location: locationValue(location), keyword: keyword.text.trim(),
            valid_months: customRule.checked ? monthOptions[batchMonths.currentIndex] : 0,
            hours_per_day: customRule.checked ? hourOptions[batchHours.currentIndex] : 0}
        if (!choice.company || !choice.location) { errorText = "请选择或填写公司和驻地。"; return }
        var choices = {}
        ids.forEach(function(id) { choices[id] = choice })
        if (checkConfig(config, choices)) selected = ({})
    }
    function names(field) {
        var values = field === "location" ? ["南昌", "深圳", "北京", "公司默认"] : []
        config.rules.forEach(function(rule) { if (rule[field] && values.indexOf(rule[field]) < 0) values.push(rule[field]) })
        rows.forEach(function(row) { if (row[field] && values.indexOf(row[field]) < 0) values.push(row[field]) })
        return values
    }
    function editRule(index) {
        editRuleIndex = index
        var item = index < 0 ? ({}) : config.rules[index]
        ruleCompany.text = item.company || ""
        ruleLocation.text = item.location || ""
        ruleMonths.currentIndex = Math.max(0, monthOptions.indexOf(Number(item.valid_months || 0)))
        ruleHours.currentIndex = Math.max(0, hourOptions.indexOf(Number(item.hours_per_day || 0)))
    }
    function saveRule() {
        var value = copy(config)
        var item = {company: ruleCompany.text.trim(), location: ruleLocation.text.trim(),
            valid_months: monthOptions[ruleMonths.currentIndex], hours_per_day: hourOptions[ruleHours.currentIndex]}
        if (editRuleIndex < 0) value.rules.push(item); else value.rules[editRuleIndex] = item
        if (checkConfig(value)) editRule(-1)
    }
    function editAssignment(index) {
        editAssignmentIndex = index
        var item = config.assignments[index]
        savedCompany.text = item.company
        savedLocation.selectedRawValue = item.location
        savedLocation.currentIndex = savedLocation.rawValues.indexOf(item.location)
        savedLocation.editText = locationLabel(item.location)
        savedKeyword.text = item.keyword
        savedMonths.currentIndex = Math.max(0, monthOptions.indexOf(Number(item.valid_months || 0)))
        savedHours.currentIndex = Math.max(0, hourOptions.indexOf(Number(item.hours_per_day || 0)))
    }
    function saveAssignment() {
        var value = copy(config), item = value.assignments[editAssignmentIndex]
        item.company = savedCompany.text.trim()
        item.location = locationValue(savedLocation)
        item.keyword = savedKeyword.text.trim()
        item.source = item.keyword ? "" : (item.original_source || item.source)
        item.valid_months = monthOptions[savedMonths.currentIndex]
        item.hours_per_day = hourOptions[savedHours.currentIndex]
        if (checkConfig(value)) editAssignmentIndex = -1
    }
    onRejected: if (pending) backend.cancelAttendanceRuleReview()
    onAccepted: {
        var error = backend.saveAttendanceRules(JSON.stringify({config: config, pending: pending, remember: remember.checked}))
        if (error) { errorText = error; Qt.callLater(function() { dialog.open() }) }
    }

    contentItem: ColumnLayout {
        spacing: 10
        RowLayout {
            Layout.fillWidth: true
            AppButton { text: "本次分配"; visible: dialog.pending; variant: dialog.page === "assign" ? "primary" : "secondary"; onClicked: dialog.page = "assign" }
            AppButton { text: "公司/驻地规则"; variant: dialog.page === "rules" ? "primary" : "secondary"; onClicked: dialog.page = "rules" }
            AppButton { text: "已记住的归属"; variant: dialog.page === "saved" ? "primary" : "secondary"; onClicked: dialog.page = "saved" }
        }
        StackLayout {
            Layout.fillWidth: true; Layout.fillHeight: true
            currentIndex: dialog.page === "assign" ? 0 : dialog.page === "rules" ? 1 : 2
            ColumnLayout {
                spacing: 8
                Text { Layout.fillWidth: true; text: Ui.text("先勾选资料，再批量指定公司和驻地。组内有例外时切换“按人员”；识别不清的人员会标出原因。"); wrapMode: Text.Wrap; color: Ui.color("muted"); font.pixelSize: 12 }
                RowLayout {
                    Layout.fillWidth: true
                    AppTextField { id: search; Layout.fillWidth: true; placeholderText: Ui.text("搜索文件、公司或人员") }
                    AppComboBox { id: viewMode; model: ["按文件分组", "按人员"]; Layout.preferredWidth: 140 }
                    AppButton { text: "全选当前列表"; variant: "link"; onClicked: dialog.shownRows.forEach(function(row) { dialog.selectRows(row.ids, true) }) }
                    AppButton { text: "清除选择"; variant: "link"; onClicked: dialog.selected = ({}) }
                }
                ListView {
                    Layout.fillWidth: true; Layout.fillHeight: true; Layout.minimumHeight: 80
                    clip: true; spacing: 5; model: dialog.shownRows
                    ScrollBar.vertical: ScrollBar {}
                    delegate: Rectangle {
                        width: ListView.view.width; height: 76
                        color: modelData.problem ? Ui.color("input") : Ui.color("surface")
                        border.color: modelData.problem ? Ui.color("warning") : Ui.color("border"); radius: 6
                        RowLayout {
                            anchors.fill: parent; anchors.margins: 8; spacing: 8
                            AppCheckBox { checked: dialog.allSelected(modelData.ids); enabled: !dialog.working; onClicked: dialog.selectRows(modelData.ids, checked) }
                            ColumnLayout {
                                Layout.fillWidth: true; spacing: 3
                                Text { Layout.fillWidth: true; text: modelData.title + Ui.text("（" + modelData.ids.length + " 人，" + (modelData.kind === "history" ? "历史汇总" : "本次考勤") + "）"); textFormat: Text.PlainText; elide: Text.ElideMiddle; color: Ui.color("text"); font.pixelSize: 13 }
                                Text { Layout.fillWidth: true; text: modelData.rules.length === 1 ? modelData.rules[0] : Ui.text("组内人员规则不同，请切换“按人员”查看"); textFormat: Text.PlainText; elide: Text.ElideRight; color: modelData.problem ? Ui.color("warning") : Ui.color("muted"); font.pixelSize: 12 }
                                Text { Layout.fillWidth: true; text: modelData.labels.slice(0, 5).join(Ui.language === "en_US" ? ", " : "、") + (modelData.labels.length > 5 ? Ui.text("等") : ""); textFormat: Text.PlainText; elide: Text.ElideRight; color: Ui.color("muted"); font.pixelSize: 11 }
                            }
                        }
                    }
                }
                RowLayout {
                    Layout.fillWidth: true
                    Text { text: Ui.text("公司"); color: Ui.color("text") }
                    ComboBox {
                        id: company; implicitHeight: 36; font.pixelSize: 13
                        Layout.fillWidth: true; editable: true; model: dialog.names("company"); currentIndex: -1
                        palette.text: Ui.color("text"); palette.base: Ui.color("input")
                        palette.button: Ui.color("input"); palette.buttonText: Ui.color("text")
                    }
                    Text { text: Ui.text("驻地"); color: Ui.color("text") }
                    ComboBox {
                        id: location; implicitHeight: 36; font.pixelSize: 13
                        property var rawValues: dialog.names("location")
                        property string selectedRawValue: ""
                        Layout.fillWidth: true; editable: true; model: rawValues.map(dialog.locationLabel); currentIndex: -1
                        onActivated: selectedRawValue = rawValues[index]
                        palette.text: Ui.color("text"); palette.base: Ui.color("input")
                        palette.button: Ui.color("input"); palette.buttonText: Ui.color("text")
                    }
                }
                Text {
                    Layout.fillWidth: true; wrapMode: Text.Wrap; font.pixelSize: 11; color: Ui.color("muted")
                    property var suggested: backend ? backend.suggestAttendanceRule(company.editText, dialog.locationValue(location), JSON.stringify(dialog.config)) : ({})
                    text: Ui.text(suggested.valid_months && suggested.hours_per_day ? "匹配规则：" + suggested.valid_months + " 个月，" + suggested.hours_per_day + " 小时/天。驻地按公司安排时，可明确选择“公司默认”。" : "未能完整匹配规则，可在“公司/驻地规则”中维护，或勾选下方的单独指定。")
                }
                RowLayout {
                    Layout.fillWidth: true
                    AppCheckBox { id: customRule; text: "为选中人员单独指定" }
                    AppComboBox { id: batchMonths; visible: customRule.checked; model: ["有效期自动匹配", "3 个月", "6 个月", "12 个月"]; Layout.fillWidth: true }
                    AppComboBox { id: batchHours; visible: customRule.checked; model: ["工时自动匹配", "7 小时/天", "8 小时/天"]; Layout.fillWidth: true }
                }
                RowLayout {
                    Layout.fillWidth: true
                    AppTextField { id: keyword; Layout.fillWidth: true; placeholderText: Ui.text("文件名固定关键词（可选）：如“几维日报”；留空仅记住当前文件") }
                    AppButton { text: "应用到选中人员"; variant: "primary"; enabled: !dialog.working; onClicked: dialog.applySelection() }
                }
                Text { Layout.fillWidth: true; text: Ui.text(dialog.unresolved ? "还有 " + dialog.unresolved + " 条人员记录待确认。" : "当前人员均已匹配规则，可继续处理。"); color: dialog.unresolved ? Ui.color("warning") : Ui.color("muted"); font.pixelSize: 12 }
                AppCheckBox { id: remember; text: "记住这次分配，下次自动应用（可修改或删除）"; checked: true }
            }
            ColumnLayout {
                spacing: 8
                Text { Layout.fillWidth: true; text: Ui.text("公司规则作为默认，驻地规则优先；同时指定公司和驻地的规则更具体。明确指定的人员例外优先于以上规则。公司名称按原表完整名称填写。"); wrapMode: Text.Wrap; color: Ui.color("muted"); font.pixelSize: 12 }
                ListView {
                    Layout.fillWidth: true; Layout.fillHeight: true; clip: true; spacing: 4; model: dialog.config.rules
                    ScrollBar.vertical: ScrollBar {}
                    delegate: RowLayout {
                        width: ListView.view.width; height: 48
                        Text { Layout.fillWidth: true; text: (modelData.company || Ui.text("所有公司")) + " / " + dialog.locationLabel(modelData.location || "公司默认") + ": " + Ui.text(modelData.valid_months ? modelData.valid_months + " 个月" : "有效期沿用") + ", " + Ui.text(modelData.hours_per_day ? modelData.hours_per_day + " 小时/天" : "工时沿用"); textFormat: Text.PlainText; elide: Text.ElideRight; color: Ui.color("text"); font.pixelSize: 12 }
                        AppButton { text: "修改"; variant: "link"; onClicked: dialog.editRule(index) }
                        AppButton { text: "删除"; variant: "link"; onClicked: { var value = dialog.copy(dialog.config); value.rules.splice(index, 1); if (dialog.checkConfig(value)) dialog.editRule(-1) } }
                    }
                }
                RowLayout {
                    Layout.fillWidth: true
                    AppTextField { id: ruleCompany; Layout.fillWidth: true; placeholderText: Ui.text("公司名称；留空表示所有公司") }
                    AppTextField { id: ruleLocation; Layout.fillWidth: true; placeholderText: Ui.text("驻地；留空表示公司默认") }
                }
                RowLayout {
                    Layout.fillWidth: true
                    AppComboBox { id: ruleMonths; Layout.fillWidth: true; model: ["有效期沿用其他规则", "3 个月", "6 个月", "12 个月"] }
                    AppComboBox { id: ruleHours; Layout.fillWidth: true; model: ["工时沿用其他规则", "7 小时/天", "8 小时/天"] }
                    AppButton { text: dialog.editRuleIndex < 0 ? "添加规则" : "保存此条修改"; onClicked: dialog.saveRule() }
                    AppButton { text: "清空"; variant: "link"; onClicked: dialog.editRule(-1) }
                }
            }
            ColumnLayout {
                spacing: 8
                Text { Layout.fillWidth: true; text: Ui.text("这里保存文件或人员对应的公司、驻地。文件名关键词只在明确设置后使用；原表公司或驻地改变时，旧归属不会直接套用。"); wrapMode: Text.Wrap; color: Ui.color("muted"); font.pixelSize: 12 }
                ListView {
                    Layout.fillWidth: true; Layout.fillHeight: true; clip: true; spacing: 6; model: dialog.config.assignments
                    ScrollBar.vertical: ScrollBar {}
                    delegate: RowLayout {
                        width: ListView.view.width; height: 64
                        ColumnLayout {
                            Layout.fillWidth: true
                            Text { Layout.fillWidth: true; text: dialog.assignmentLabel(modelData); textFormat: Text.PlainText; elide: Text.ElideMiddle; color: Ui.color("text"); font.pixelSize: 12 }
                            Text { Layout.fillWidth: true; text: modelData.company + " / " + dialog.locationLabel(modelData.location) + " · " + Ui.text(modelData.keyword ? "文件名含“" + modelData.keyword + "”" : "当前文件") + (modelData.valid_months || modelData.hours_per_day ? " · " + Ui.text("含单独指定规则") : ""); textFormat: Text.PlainText; elide: Text.ElideRight; color: Ui.color("muted"); font.pixelSize: 11 }
                        }
                        AppButton { text: "修改"; variant: "link"; onClicked: dialog.editAssignment(index) }
                        AppButton { text: "删除"; variant: "link"; onClicked: { var value = dialog.copy(dialog.config); value.assignments.splice(index, 1); if (dialog.checkConfig(value)) dialog.editAssignmentIndex = -1 } }
                    }
                }
                Text { visible: !dialog.config.assignments.length; text: Ui.text("暂无已记住的归属。首次处理时可批量指定并保存。"); color: Ui.color("muted"); font.pixelSize: 12 }
                ColumnLayout {
                    Layout.fillWidth: true; visible: dialog.editAssignmentIndex >= 0
                    RowLayout {
                        Layout.fillWidth: true
                        AppTextField { id: savedCompany; Layout.fillWidth: true; placeholderText: Ui.text("公司") }
                        ComboBox {
                            id: savedLocation; implicitHeight: 36; font.pixelSize: 13
                            property var rawValues: dialog.names("location")
                            property string selectedRawValue: ""
                            Layout.fillWidth: true; editable: true; model: rawValues.map(dialog.locationLabel); currentIndex: -1
                            onActivated: selectedRawValue = rawValues[index]
                            Accessible.name: Ui.text("驻地或公司默认")
                            palette.text: Ui.color("text"); palette.base: Ui.color("input")
                            palette.button: Ui.color("input"); palette.buttonText: Ui.color("text")
                        }
                        AppTextField { id: savedKeyword; Layout.fillWidth: true; placeholderText: Ui.text("文件名关键词；留空限定原文件") }
                    }
                    RowLayout {
                        Layout.fillWidth: true
                        AppComboBox { id: savedMonths; Layout.fillWidth: true; model: ["有效期自动匹配", "3 个月", "6 个月", "12 个月"] }
                        AppComboBox { id: savedHours; Layout.fillWidth: true; model: ["工时自动匹配", "7 小时/天", "8 小时/天"] }
                        AppButton { text: "保存此条修改"; onClicked: dialog.saveAssignment() }
                    }
                }
            }
        }
        Text { Layout.fillWidth: true; visible: !!dialog.errorText; text: Ui.text(dialog.errorText); textFormat: Text.PlainText; color: Ui.color("error"); wrapMode: Text.Wrap; font.pixelSize: 12 }
    }
}
