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
    property int selectedCount: Object.keys(selected).length
    property int otherUnresolved: rows.filter(function(row) { return !!row.problem && !selected[row.id] }).length
    property bool advanced: false
    property var suggestedRule: backend ? backend.suggestAttendanceRule(company.value.trim(), location.value.trim(), JSON.stringify(config)) : ({})
    property int selectedMonths: customRule.checked && monthOptions[batchMonths.currentIndex]
        ? monthOptions[batchMonths.currentIndex] : Number(suggestedRule.valid_months || 0)
    property int selectedHours: customRule.checked && hourOptions[batchHours.currentIndex]
        ? hourOptions[batchHours.currentIndex] : Number(suggestedRule.hours_per_day || 0)
    property bool selectionReady: selectedCount > 0 && !!company.value.trim() && !!location.value.trim()
        && selectedMonths > 0 && selectedHours > 0
    property var monthOptions: [0, 3, 6, 12]
    property var hourOptions: [0, 7, 8]
    property var shownRows: buildRows()
    title: Ui.text(pending ? "补充考勤人员信息" : "考勤识别规则")
    width: Math.min(parent ? parent.width - 24 : 960, 960)
    height: Math.min(parent ? parent.height - 24 : 790, pending && page === "assign" ? 730 : 790)
    x: parent ? (parent.width - width) / 2 : 0
    y: parent ? (parent.height - height) / 2 : 0
    acceptText: pending ? (selectedCount ? "使用以上设置并继续" : "确认并继续处理") : "保存设置"
    rejectText: "返回"
    acceptButtonEnabled: !working && (!pending || (selectedCount ? selectionReady && otherUnresolved === 0 : unresolved === 0))

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
        company.value = ""
        location.value = ""
        keyword.text = ""
        customRule.checked = false
        batchMonths.currentIndex = 0
        batchHours.currentIndex = 0
        advanced = false
        remember.checked = true
        page = pending ? "assign" : "rules"
        // Select a single unresolved group, but never guess its company/location.
        var groups = buildRows(), needsInput = groups.filter(function(group) { return group.problem })
        if (pending && needsInput.length === 1) selectRows(needsInput[0].ids, true)
        open()
    }
    function showData(value) { initialize(value, true) }
    function showSettings(value) { initialize(value, false) }
    function locationLabel(value) { return value === "公司默认" ? Ui.text("按公司默认规则") : value }
    function assignmentLabel(item) {
        var suffix = " / 全组人员", label = String(item.label || "")
        return !item.name && label.slice(-suffix.length) === suffix
            ? label.slice(0, -suffix.length) + " / " + Ui.text("全组人员") : label
    }
    function ruleText(row) {
        if (!row.company && !row.location) return Ui.text("待补充：所属公司、工作地点")
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
        fillSelection()
    }
    function fillSelection() {
        var items = rows.filter(function(row) { return !!selected[row.id] })
        company.value = items.length && items.every(function(row) { return row.company === items[0].company }) ? items[0].company : ""
        location.value = items.length && items.every(function(row) { return row.location === items[0].location }) ? items[0].location : ""
        keyword.text = ""
        customRule.checked = false
        batchMonths.currentIndex = 0
        batchHours.currentIndex = 0
        errorText = ""
        // Preserve an existing individual rule when editing an assigned group.
        if (items.length && items.every(function(row) {
            return !row.problem && row.valid_months === items[0].valid_months && row.hours_per_day === items[0].hours_per_day
        })) {
            var matched = backend.suggestAttendanceRule(company.value, location.value, JSON.stringify(config))
            if (items[0].valid_months !== matched.valid_months || items[0].hours_per_day !== matched.hours_per_day) {
                customRule.checked = true
                batchMonths.currentIndex = Math.max(0, monthOptions.indexOf(Number(items[0].valid_months)))
                batchHours.currentIndex = Math.max(0, hourOptions.indexOf(Number(items[0].hours_per_day)))
                advanced = true
            }
        }
    }
    function selectionHint() {
        if (!selectedCount && !unresolved) return "当前人员均已匹配规则，可继续处理。"
        if (!selectedCount) return "先勾选上方要设置的人员。这里只修改勾选人员的规则，不改变统计名单。"
        if (!company.value.trim()) return "请选择所属公司；列表没有时，可直接填写公司名称。"
        if (!location.value.trim()) return "请选择实际办公城市；确认使用公司统一规则时，可选择“按公司默认规则”。"
        if (!selectedMonths || !selectedHours) return "还缺少有效期或每天工时。展开“更多设置”手动填写，或到“公司/驻地规则”中维护。"
        return "将使用：加班有效期 " + selectedMonths + " 个月，每天 " + selectedHours + " 小时。"
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
        if (!selectionReady) { errorText = selectionHint(); return false }
        var choice = {company: company.value.trim(), location: location.value.trim(), keyword: keyword.text.trim(),
            valid_months: customRule.checked ? monthOptions[batchMonths.currentIndex] : 0,
            hours_per_day: customRule.checked ? hourOptions[batchHours.currentIndex] : 0}
        var choices = {}
        ids.forEach(function(id) { choices[id] = choice })
        if (!checkConfig(config, choices)) return false
        selected = ({})
        return true
    }
    function names(field) {
        var values = field === "location" ? ["公司默认"] : []
        config.rules.forEach(function(rule) { if (rule[field] && values.indexOf(rule[field]) < 0) values.push(rule[field]) })
        config.assignments.forEach(function(item) { if (item[field] && values.indexOf(item[field]) < 0) values.push(item[field]) })
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
        savedLocation.value = item.location
        savedKeyword.text = item.keyword
        savedMonths.currentIndex = Math.max(0, monthOptions.indexOf(Number(item.valid_months || 0)))
        savedHours.currentIndex = Math.max(0, hourOptions.indexOf(Number(item.hours_per_day || 0)))
    }
    function saveAssignment() {
        var value = copy(config), item = value.assignments[editAssignmentIndex]
        item.company = savedCompany.text.trim()
        item.location = savedLocation.value.trim()
        item.keyword = savedKeyword.text.trim()
        item.source = item.keyword ? "" : (item.original_source || item.source)
        item.valid_months = monthOptions[savedMonths.currentIndex]
        item.hours_per_day = hourOptions[savedHours.currentIndex]
        if (checkConfig(value)) editAssignmentIndex = -1
    }
    onRejected: if (pending) backend.cancelAttendanceRuleReview()
    onAccepted: {
        // Direct confirmation uses the same preview and backend validation as Apply.
        if (pending && selectedCount && !applySelection()) {
            Qt.callLater(function() { dialog.open() })
            return
        }
        var error = backend.saveAttendanceRules(JSON.stringify({config: config, pending: pending, remember: remember.checked}))
        if (error) { errorText = error; Qt.callLater(function() { dialog.open() }) }
    }

    contentItem: ColumnLayout {
        spacing: 10
        RowLayout {
            Layout.fillWidth: true
            AppButton { text: "本次人员"; visible: dialog.pending; variant: dialog.page === "assign" ? "primary" : "secondary"; onClicked: dialog.page = "assign" }
            AppButton { text: "公司/驻地规则"; variant: dialog.page === "rules" ? "primary" : "secondary"; onClicked: dialog.page = "rules" }
            AppButton { text: "已保存的选择"; variant: dialog.page === "saved" ? "primary" : "secondary"; onClicked: dialog.page = "saved" }
        }
        StackLayout {
            Layout.fillWidth: true; Layout.fillHeight: true
            currentIndex: dialog.page === "assign" ? 0 : dialog.page === "rules" ? 1 : 2
            ScrollView {
                id: assignmentScroll
                clip: true
                contentWidth: availableWidth
                contentHeight: assignmentForm.implicitHeight
                ScrollBar.horizontal.policy: ScrollBar.AlwaysOff
                ColumnLayout {
                    id: assignmentForm
                    width: assignmentScroll.availableWidth
                    spacing: 10
                    Text {
                        Layout.fillWidth: true; wrapMode: Text.Wrap
                        text: Ui.text(dialog.unresolved
                            ? "部分人员缺少公司、工作地点，或尚未匹配加班规则。人员名单只决定统计谁，这里补充加班/调休的计算依据。"
                            : "本次人员的规则已确认。可以直接继续处理；需要修改时，勾选对应人员后调整。")
                        color: Ui.color("text"); font.pixelSize: 13
                    }
                    RowLayout {
                        Layout.fillWidth: true
                        Text { text: Ui.text("1. 选择要设置的人员"); color: Ui.color("text"); font.pixelSize: 13; font.weight: Font.DemiBold }
                        Item { Layout.fillWidth: true }
                        Text { text: Ui.text("已勾选 " + dialog.selectedCount + " 条人员记录"); color: Ui.color("muted"); font.pixelSize: 12 }
                    }
                    RowLayout {
                        Layout.fillWidth: true
                        AppTextField { id: search; Layout.fillWidth: true; placeholderText: Ui.text("搜索文件、公司或人员") }
                        AppComboBox { id: viewMode; model: ["按文件分组", "按人员"]; Layout.preferredWidth: 140 }
                        AppButton { text: "全选当前列表"; variant: "link"; onClicked: {
                            var ids = []
                            dialog.shownRows.forEach(function(row) { ids = ids.concat(row.ids) })
                            dialog.selectRows(ids, true)
                        } }
                        AppButton { text: "清除选择"; variant: "link"; onClicked: { dialog.selected = ({}); dialog.fillSelection() } }
                    }
                    ListView {
                        Layout.fillWidth: true
                        Layout.preferredHeight: Math.max(80, Math.min(210, dialog.shownRows.length * 81))
                        clip: true; spacing: 5; model: dialog.shownRows
                        ScrollBar.vertical: ScrollBar {}
                        delegate: Rectangle {
                            width: ListView.view.width; height: 76
                            color: dialog.allSelected(modelData.ids) ? Ui.color("selection") : Ui.color("input")
                            border.color: dialog.allSelected(modelData.ids) ? Ui.color("accent") : modelData.problem ? Ui.color("warning") : Ui.color("border"); radius: 6
                            MouseArea {
                                anchors.fill: parent; enabled: !dialog.working
                                cursorShape: Qt.PointingHandCursor
                                onClicked: dialog.selectRows(modelData.ids, !dialog.allSelected(modelData.ids))
                            }
                            RowLayout {
                                anchors.fill: parent; anchors.margins: 8; spacing: 8
                                AppCheckBox { checked: dialog.allSelected(modelData.ids); enabled: !dialog.working; onClicked: dialog.selectRows(modelData.ids, checked) }
                                ColumnLayout {
                                    Layout.fillWidth: true; spacing: 3
                                    Text { Layout.fillWidth: true; text: modelData.title + Ui.text("（" + modelData.ids.length + " 人，" + (modelData.kind === "history" ? "历史汇总" : "本次考勤") + "）"); textFormat: Text.PlainText; elide: Text.ElideMiddle; color: Ui.color("text"); font.pixelSize: 13 }
                                    Text {
                                        Layout.fillWidth: true; textFormat: Text.PlainText; elide: Text.ElideRight; font.pixelSize: 12
                                        property bool drafted: dialog.allSelected(modelData.ids) && dialog.selectionReady
                                        text: drafted ? Ui.text("将应用") + ": " + company.value + " / " + dialog.locationLabel(location.value)
                                            : modelData.rules.length === 1 ? modelData.rules[0] : Ui.text("组内人员规则不同，请切换“按人员”查看")
                                        color: drafted ? Ui.color("accent") : modelData.problem ? Ui.color("warning") : Ui.color("muted")
                                    }
                                    Text { Layout.fillWidth: true; text: modelData.labels.slice(0, 5).join(Ui.language === "en_US" ? ", " : "、") + (modelData.labels.length > 5 ? Ui.text("等") : ""); textFormat: Text.PlainText; elide: Text.ElideRight; color: Ui.color("muted"); font.pixelSize: 11 }
                                }
                            }
                        }
                    }
                    Text {
                        Layout.fillWidth: true; wrapMode: Text.Wrap
                        text: Ui.text("同一文件的人员属于不同公司或工作地点时，切换“按人员”分别设置。")
                        color: Ui.color("muted"); font.pixelSize: 11
                    }
                    Text { text: Ui.text("2. 选择所属公司和工作地点"); color: Ui.color("text"); font.pixelSize: 13; font.weight: Font.DemiBold }
                    GridLayout {
                        Layout.fillWidth: true
                        columns: width < 620 ? 1 : 2
                        columnSpacing: 12; rowSpacing: 8
                        ColumnLayout {
                            Layout.fillWidth: true
                            Text { text: Ui.text("所属公司"); color: Ui.color("text"); font.pixelSize: 12 }
                            AttendanceChoiceField {
                                id: company; Layout.fillWidth: true
                                choices: dialog.names("company")
                                placeholderText: Ui.text("选择或填写员工所属公司")
                                enabled: !dialog.working && dialog.selectedCount > 0
                            }
                        }
                        ColumnLayout {
                            Layout.fillWidth: true
                            Text { text: Ui.text("工作地点"); color: Ui.color("text"); font.pixelSize: 12 }
                            AttendanceChoiceField {
                                id: location; Layout.fillWidth: true
                                choices: dialog.names("location")
                                optionLabels: ({"公司默认": "按公司默认规则"})
                                placeholderText: Ui.text("选择或填写实际办公城市")
                                enabled: !dialog.working && dialog.selectedCount > 0
                            }
                        }
                    }
                    Text {
                        Layout.fillWidth: true; wrapMode: Text.Wrap; font.pixelSize: 11; color: Ui.color("muted")
                        text: Ui.text("工作地点按实际办公城市选择；只有确认使用公司统一规则时，才选“按公司默认规则”。")
                    }
                    Text { text: Ui.text("3. 核对将使用的规则"); color: Ui.color("text"); font.pixelSize: 13; font.weight: Font.DemiBold }
                    Text {
                        Layout.fillWidth: true; wrapMode: Text.Wrap; font.pixelSize: 13
                        text: Ui.text(dialog.selectionHint())
                        color: dialog.selectionReady ? Ui.color("accent") : Ui.color("muted")
                    }
                    AppButton {
                        text: dialog.advanced ? "收起更多设置" : "更多设置（单独规则、下次识别）"
                        variant: "link"; enabled: !dialog.working
                        onClicked: dialog.advanced = !dialog.advanced
                    }
                    ColumnLayout {
                        Layout.fillWidth: true; visible: dialog.advanced; spacing: 8
                        AppCheckBox { id: customRule; text: "手动设置有效期和每天工时"; enabled: !dialog.working && dialog.selectedCount > 0 }
                        GridLayout {
                            Layout.fillWidth: true
                            visible: customRule.checked
                            columns: width < 620 ? 1 : 2
                            AppComboBox { id: batchMonths; model: ["有效期自动匹配", "3 个月", "6 个月", "12 个月"]; Layout.fillWidth: true }
                            AppComboBox { id: batchHours; model: ["工时自动匹配", "7 小时/天", "8 小时/天"]; Layout.fillWidth: true }
                        }
                        Text {
                            Layout.fillWidth: true; wrapMode: Text.Wrap; font.pixelSize: 11; color: Ui.color("muted")
                            text: Ui.text("有效期用于历史加班结转；每天工时用于加班和调休的天数换算。请按人事确认的规则填写。")
                        }
                        AppTextField {
                            id: keyword; Layout.fillWidth: true
                            placeholderText: Ui.text("文件名固定关键词（可选）；留空只记住当前文件")
                        }
                        Text {
                            Layout.fillWidth: true; wrapMode: Text.Wrap; font.pixelSize: 11; color: Ui.color("muted")
                            text: Ui.text("下个月文件名会变化时，可填写不变的关键词；以后文件名包含该词、人员来源信息也相同时，才会使用这次选择。")
                        }
                    }
                    RowLayout {
                        Layout.fillWidth: true
                        visible: dialog.otherUnresolved > 0 && dialog.selectedCount > 0
                        AppButton { text: "应用到这组人员"; enabled: !dialog.working && dialog.selectionReady; onClicked: dialog.applySelection() }
                        Text {
                            Layout.fillWidth: true; wrapMode: Text.Wrap; font.pixelSize: 12; color: Ui.color("muted")
                            text: Ui.text("其他还有 " + dialog.otherUnresolved + " 条待确认，请先应用，再选择下一组。")
                        }
                    }
                    Text {
                        Layout.fillWidth: true; wrapMode: Text.Wrap; font.pixelSize: 12
                        text: Ui.text(dialog.selectedCount
                            ? (dialog.selectionReady && !dialog.otherUnresolved ? "信息已填完整，可点击“使用以上设置并继续”。" : "请按上面的步骤补齐信息；填完整后即可继续。")
                            : (dialog.unresolved ? "还有 " + dialog.unresolved + " 条人员记录待确认。" : "当前人员均已匹配规则，可继续处理。"))
                        color: dialog.selectionReady && !dialog.otherUnresolved ? Ui.color("accent") : dialog.unresolved ? Ui.color("warning") : Ui.color("muted")
                    }
                    AppCheckBox { id: remember; text: "记住本次选择（可在“已保存的选择”中修改或删除）"; checked: true }
                }
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
                        AttendanceChoiceField {
                            id: savedLocation; Layout.fillWidth: true
                            choices: dialog.names("location")
                            optionLabels: ({"公司默认": "按公司默认规则"})
                            placeholderText: Ui.text("选择工作地点或按公司默认规则")
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
