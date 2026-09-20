import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15

AppDialog {
    id: dialog
    objectName: "templateChoiceDialog"
    property var backend
    property var mappingData: ({roles: [], sheets: []})
    property int roleIndex: 0
    property int sheetIndex: 0
    property int headerRow: 0
    property int columnPage: 0
    property var chosen: ({})
    property var sheetSelections: ({})
    property bool sheetMode: !salaryMode && mappingData.kind === "worksheets"
    property string lastPayload: ""
    property bool rulesPage: false
    property bool profilesPage: false
    property bool detailsExpanded: false
    property bool roleDetailsExpanded: false
    property var attentionFields: []
    property bool editingSaved: !!mappingData.editing_profile && !salaryMode
    property bool hasDocument: false
    property bool salaryMode: false
    property bool closingFromBackend: false
    property var salaryGroups: []
    property var salaryIssues: []
    property int salaryIndex: 0
    property int salaryRevision: 0
    property int headerBottom: 0
    property var salaryGroup: salaryGroups[salaryIndex] || ({})
    property var role: mappingData.roles[roleIndex] || ({fields: {}, required: []})
    property var sheet: mappingData.sheets[sheetIndex] || ({rows: []})
    property bool skipping: role.key === "_ignore" || (salaryMode && salaryRevision >= 0 && !!salaryGroup.skip)
    property bool working: backend ? backend.busy : false
    property int pageSize: width < 650 ? 3 : 5
    property int columnCount: Math.max(1, sheet.rows.reduce(function(n, row) {
        for (var i = row.length - 1; i >= 0; i--) if (row[i]) return Math.max(n, i + 1)
        return n
    }, 0))
    property var columnChoices: makeColumns()
    property string problem: salaryMode ? salaryProblem() : selectionProblem()
    title: profilesPage ? "已记住的选择" : rulesPage ? "模板设置" : sheetMode ? "确认工作表" : editingSaved ? "修改已记住的选择" : "确认列名"
    width: Math.min(parent ? parent.width - 24 : 900, 900)
    height: Math.min(parent ? parent.height - 24 : 790, 790)
    x: parent ? (parent.width - width) / 2 : 0
    y: parent ? (parent.height - height) / 2 : 0
    rejectText: profilesPage ? "关闭" : "返回"
    acceptText: profilesPage ? "完成" : rulesPage ? (hasDocument ? "保存名称并重新检查" : "保存常用名称") : editingSaved ? "保存修改" : !hasDocument ? "开始检查并处理" : salaryMode ? "确认全部并继续处理" : skipping ? "确认跳过并继续" : "确认并继续处理"
    acceptButtonEnabled: !working && (profilesPage || rulesPage || !hasDocument || (!problem && confirmed.checked))
    onPageSizeChanged: columnPage = 0
    onOpened: Qt.callLater(function() { if (dialog.opened && !dialog.working) dialog.locateProblem() })

    function normalized(value) {
        var text = String(value)
        if (text.normalize) text = text.normalize("NFKC")
        return text.replace(/\s/g, "").toLowerCase()
    }
    function fieldLabel(name) { return (role.field_labels || {})[name] || name }
    function readingModeLabel(option) {
        var labels = {attendance_summary: "每人一行", attendance: "每天一条考勤记录",
                      weekly: "按周报记录读取", monthly: "按月报记录读取", _ignore: "本次不读取"}
        return labels[option.key] || option.label || ""
    }
    function columnConfirmationHeading() {
        if (editingSaved) return "修改列对应关系"
        if (salaryMode) return "请核对工资表对应列"
        if (skipping) return "确认本次跳过"
        if (!role.key) return "请确认数据的读取方式"
        var names = (role.required || []).filter(function(name) {
            return attentionFields.indexOf(name) >= 0
        }).map(fieldLabel)
        if (names.length === 1) return "请确认“" + names[0] + "”在哪一列"
        if (names.length > 1) return "请确认这些内容对应的列：" + names.join("、")
        return "请核对列对应关系"
    }
    function letter(col) {
        var result = ""
        while (col > 0) { col--; result = String.fromCharCode(65 + col % 26) + result; col = Math.floor(col / 26) }
        return result
    }
    function sample(col) {
        if (salaryMode) {
            var columns = salaryGroup.columns || []
            for (var c = 0; c < columns.length; c++) if (columns[c].column === col)
                return columns[c].samples || "下方几行没有内容，请核对原表"
        }
        var values = []
        for (var i = headerRow; i < Math.min(sheet.rows.length, headerRow + 5); i++) {
            var value = sheet.rows[i][col - 1]
            if (value && values.indexOf(value) < 0) values.push(value)
            if (values.length === 2) break
        }
        return values.length ? values.join("、") : "下方几行没有内容，请核对原表"
    }
    function makeColumns() {
        if (salaryMode) return [{col: 0, label: "请选择原表中的列"}].concat((salaryGroup.columns || []).map(function(c) {
            return {col: c.column, label: c.display + " · " + c.samples}
        }))
        var values = sheet.rows[headerRow - 1] || []
        var result = [{col: 0, label: "请选择原表中的列"}]
        for (var i = 0; i < values.length; i++)
            if (values[i]) result.push({col: i + 1, label: letter(i + 1) + "列 · " + values[i] + (editingSaved ? "" : " · " + sample(i + 1))})
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
        attentionFields = fieldNames().filter(function(name) {
            return ((role.required || []).indexOf(name) >= 0 && !result[name]) || (role.one_of || []).indexOf(name) >= 0
        })
        confirmed.checked = false
        search.text = ""
        columnSearch.text = ""
    }
    function fieldNames() {
        var names = (role.required || []).concat(role.one_of || []).concat(Object.keys(role.fields))
        return names.filter(function(name, index) { return names.indexOf(name) === index })
    }
    function recognizedCount() {
        return Object.keys(chosen).filter(function(name) { return !!chosen[name] && attentionFields.indexOf(name) < 0 }).length
    }
    function suggestRow() {
        var best = 0, rows = []
        for (var r = 0; r < sheet.rows.length; r++) {
            var values = sheet.rows[r].map(normalized), score = 0
            Object.keys(role.fields).forEach(function(name) {
                if (role.fields[name].some(function(a) { return values.indexOf(normalized(a)) >= 0 }))
                    score += role.required.indexOf(name) >= 0 ? 2 : 1
            })
            if (score > best) { best = score; rows = [r + 1] }
            else if (score === best && score > 0) rows.push(r + 1)
        }
        // 仅建议位置；无匹配或并列时不默认第一行，不扩展业务识别规则。
        headerRow = best > 0 && rows.length === 1 ? rows[0] : 0
        resetChoices()
        preview.positionViewAtIndex(Math.max(0, headerRow - 1), ListView.Beginning)
    }
    function selectRow(row) {
        headerRow = row; headerBottom = row
        if (salaryMode) confirmed.checked = false
        else resetChoices()
    }
    function showData(payload) {
        salaryMode = false; hasDocument = true; rulesPage = false; profilesPage = false
        roleDetailsExpanded = false
        confirmed.checked = false
        rememberChoice.checked = false
        sheetSelections = ({})
        var signature = JSON.stringify(payload)
        if (signature !== lastPayload || !opened || payload.editing_profile) {
            mappingData = payload
            roleIndex = payload.roles.length === 1 ? 0 : -1; sheetIndex = 0; columnPage = 0
            for (var r = 0; r < payload.roles.length; r++)
                if (payload.roles[r].key === payload.suggested_role) roleIndex = r
            for (var i = 0; i < payload.sheets.length; i++)
                if (payload.sheets[i].name === payload.selected_sheet) sheetIndex = i
            extra.checked = false
            suggestRow()
            if (payload.editing_profile) {
                headerRow = payload.row
                chosen = Object.assign({}, payload.selected_columns || {})
                attentionFields = fieldNames().filter(function(name) { return !!chosen[name] || role.required.indexOf(name) >= 0 })
            }
            detailsExpanded = !headerRow
            lastPayload = signature
        }
        open()
    }
    function showRules(sections) {
        if (!opened) { hasDocument = false; salaryMode = false }
        nameEditor.showSections(sections)
        rulesPage = true; profilesPage = false
        open()
    }
    function showSalaryData(payload) {
        var previousFile = salaryMode && hasDocument && (salaryGroup.files || []).length ? salaryGroup.files[0].key : ""
        var skippedIssues = salaryMode && hasDocument ? salaryIssues.filter(function(i) { return !!i.skip }).map(function(i) { return i.key }) : []
        salaryMode = true; hasDocument = true; rulesPage = false; profilesPage = false
        salaryGroups = JSON.parse(JSON.stringify(payload.groups || []))
        salaryIssues = JSON.parse(JSON.stringify(payload.issues || []))
        salaryIndex = 0
        for (var i = 0; i < salaryGroups.length; i++)
            if (!salaryGroups[i].ready && !salaryGroups[i].skip) { salaryIndex = i; break }
        if (previousFile) for (var j = 0; j < salaryGroups.length; j++)
            if (salaryGroups[j].files.some(function(f) { return f.key === previousFile })) { salaryIndex = j; break }
        salaryIssues.forEach(function(i) { i.skip = !!i.skippable && skippedIssues.indexOf(i.key) >= 0 })
        salaryRevision++
        loadSalaryGroup()
        open()
    }
    function loadSalaryGroup() {
        roleDetailsExpanded = false
        var g = salaryGroup, keys = g.role === "summary" ? ["name", "id_card"] : ["name", "id_card", "amount"]
        var fields = {}, labels = {name: "姓名", id_card: "身份证号码", amount: "应发工资"}
        keys.forEach(function(k) { fields[k] = (g.field_aliases || {})[k] || [labels[k]] })
        mappingData = {file: (g.files || []).map(function(f) { return f.name }).join("、"),
            roles: [{key: g.role || "detail", label: g.role === "summary" ? "已有工资汇总表" : "工资明细表", fields: fields, required: keys, field_labels: labels}],
            sheets: (g.sheet_names || []).map(function(n) { return {name: n, rows: n === g.sheet ? (g.preview_rows || []) : []} })}
        roleIndex = 0; sheetIndex = Math.max(0, (g.sheet_names || []).indexOf(g.sheet)); columnPage = 0
        headerRow = g.header_row || 0; headerBottom = g.header_bottom || headerRow
        chosen = Object.assign({}, g.selections || {})
        confirmed.checked = false; search.text = ""; columnSearch.text = ""; extra.checked = false
        preview.positionViewAtIndex(Math.max(0, headerRow - 1), ListView.Beginning)
    }
    function salaryPayload() {
        return JSON.stringify({groups: salaryGroups.map(function(g) { return {group_id: g.group_id, selections: g.selections, skip: !!g.skip} }),
            skipped_issues: salaryIssues.filter(function(i) { return !!i.skip }).map(function(i) { return i.key })})
    }
    function salaryNeedsRead() {
        return salaryMode && (sheet.name !== salaryGroup.sheet || headerRow !== salaryGroup.header_row
            || headerBottom !== salaryGroup.header_bottom || !!salaryGroup.sheet_needs_confirmation)
    }
    function salaryProblem() {
        var tick = salaryRevision
        if (!salaryGroups.length) return "没有可确认的工资模板，请检查下方文件提示，或返回重新选文件。"
        if (!salaryGroup.skip && salaryNeedsRead()) return "工作表或列名行已改变，请先点击“读取这些列名”。"
        if (!salaryGroup.skip) {
            var missing = role.required.filter(function(k) { return !chosen[k] }).map(fieldLabel)
            if (missing.length) return "当前模板还需要选择：" + missing.join("、")
            var selected = role.required.map(function(k) { return chosen[k] })
            if (selected.some(function(col, i) { return selected.indexOf(col) !== i })) return "当前模板重复选择了同一列，姓名、身份证和金额必须分别选择。"
        }
        var pending = 0, included = 0
        for (var i = 0; i < salaryGroups.length; i++) {
            var g = salaryGroups[i]
            if (g.skip) continue
            if (g.role === "detail") included++
            var values = Object.keys(g.selections || {}).map(function(k) { return g.selections[k] })
            if (g.sheet_needs_confirmation || !values.length || values.some(function(v) { return !v })
                || values.some(function(v, index) { return values.indexOf(v) !== index })) pending++
        }
        if (pending) return "还有 " + pending + " 类模板需要确认。请在上方模板列表中逐个选择。"
        if (salaryIssues.some(function(i) { return !i.skippable || !i.skip })) return "还有文件问题未处理，请查看文件提示；可跳过的文件需要明确勾选。"
        if (!included) return "至少保留一份工资明细表参与合并。"
        return ""
    }
    function chooseColumn(name, col) {
        var updated = Object.assign({}, chosen); updated[name] = col; chosen = updated
        if (salaryMode) { salaryGroup.selections = updated; salaryRevision++ }
        confirmed.checked = false
    }
    function changeSheet(index) {
        sheetIndex = index; columnPage = 0
        if (salaryMode) backend.rescanSalaryHeader(salaryGroup.group_id, sheet.name, 0, 0, salaryPayload())
        else suggestRow()
    }
    function dismissSalary() {
        if (!salaryMode) return
        closingFromBackend = true; close(); closingFromBackend = false
    }
    function applyChoices() {
        if (profilesPage) { close(); return }
        if (rulesPage) { nameEditor.submit(); return }
        if (!hasDocument) {
            close()
            if (backend.currentTool === "salary_merge") backend.reviewSalaryHeaders()
            else backend.runOrCancel()
            return
        }
        if (salaryMode) { backend.applySalaryMappings(salaryPayload(), rememberSalary.checked); return }
        accept()
    }
    function filteredColumns(name) {
        var needle = normalized(columnSearch.text)
        return columnChoices.filter(function(c) {
            return !c.col || c.col === chosen[name] || !needle || normalized(c.label).indexOf(needle) >= 0
        })
    }
    function filteredIndex(name, options) {
        for (var i = 0; i < options.length; i++) if (options[i].col === chosen[name]) return i
        return 0
    }
    function sheetRequests() {
        var requests = mappingData.sheet_requests || []
        return mappingData.alternatives ? requests.filter(function(r) { return r.key === dialog.role.key }) : requests
    }
    function selectSheetForRole(key, value) {
        var updated = Object.assign({}, sheetSelections); updated[key] = value; sheetSelections = updated
        confirmed.checked = false
    }
    function selectionProblem() {
        if (sheetMode) {
            var requests = sheetRequests(), used = []
            if (!requests.length) return "请选择需要读取的资料类型。"
            var resolved = mappingData.resolved_sheets || {}
            Object.keys(resolved).forEach(function(key) { if (resolved[key] !== null) used.push(resolved[key]) })
            for (var n = 0; n < requests.length; n++) {
                var item = requests[n], value = sheetSelections[item.key]
                if (value === undefined) return "请选择“" + item.label + "”对应的工作表。"
                if (value === null && !item.optional) return "请补充“" + item.label + "”工作表。"
                if (value !== null && used.indexOf(value) >= 0) return "不同资料不能选择同一工作表。"
                if (value !== null) used.push(value)
            }
            return ""
        }
        if (!role.key) return "请选择数据的读取方式。"
        if (!sheet.rows.length) return "这张工作表没有可预览的内容，请换一张工作表或返回重新选文件。"
        if (skipping) return ""
        if (!headerRow) return "还不能确定哪一行写着列名，请在原表预览中点选；如果文件选错了，请返回重新选择。"
        var missing = role.required.filter(function(name) { return !chosen[name] }).map(fieldLabel)
        if (missing.length) return "还需要选择：" + missing.join("、")
        var used = {}, keys = Object.keys(chosen)
        for (var i = 0; i < keys.length; i++) {
            var col = chosen[keys[i]]
            if (!col) continue
            if (used[col]) return "“" + fieldLabel(used[col]) + "”和“" + fieldLabel(keys[i]) + "”不能选同一列。"
            used[col] = keys[i]
        }
        if ((role.one_of || []).length && !role.one_of.some(function(name) { return chosen[name] > 0 }))
            return "还需要至少选择一项金额；个人和单位的金额不能混用。"
        return ""
    }
    function focusProblemControl(control) {
        if (!control) return
        // Use the real laid-out position, without changing any selections.
        var point = control.mapToItem(body, 0, 0)
        problemViewport.contentY = Math.max(0, Math.min(point.y - 18,
            problemViewport.contentHeight - problemViewport.height))
        control.forceActiveFocus(Qt.TabFocusReason)
    }
    function focusField(name) {
        search.text = ""; columnSearch.text = ""
        if (attentionFields.indexOf(name) < 0) attentionFields = attentionFields.concat([name])
        Qt.callLater(function() {
            if (!dialog.opened || dialog.working) return
            for (var i = 0; i < fieldRepeater.count; i++) {
                var item = fieldRepeater.itemAt(i)
                if (item && item.fieldName === name) {
                    dialog.focusProblemControl(item.editor)
                    return
                }
            }
        })
    }
    function locateProblem() {
        if (working || rulesPage || profilesPage || !hasDocument) return
        if (sheetMode) { focusProblemControl(sheetConfirmation); return }
        if (!role.key) { focusProblemControl(rolePicker); return }
        if (salaryMode && !salaryGroups.length) { focusProblemControl(salaryFilesSection); return }
        if (!skipping && salaryNeedsRead()) { focusProblemControl(readHeadersButton); return }
        if (!sheet.rows.length) { focusProblemControl(sheetPicker.visible ? sheetPicker : sourceSection); return }
        if (!skipping && !headerRow) { detailsExpanded = true; focusProblemControl(preview); return }
        if (!skipping) {
            var required = role.required || []
            for (var i = 0; i < required.length; i++)
                if (!chosen[required[i]]) { focusField(required[i]); return }
            var used = {}, keys = salaryMode ? required : Object.keys(chosen)
            for (var j = 0; j < keys.length; j++) {
                var col = chosen[keys[j]]
                if (!col) continue
                if (used[col]) { focusField(keys[j]); return }
                used[col] = true
            }
            var oneOf = role.one_of || []
            if (!salaryMode && oneOf.length && !oneOf.some(function(k) { return chosen[k] > 0 })) {
                focusField(oneOf[0]); return
            }
        }
        if (salaryMode) {
            for (var g = 0; g < salaryGroups.length; g++) {
                var group = salaryGroups[g]
                if (group.skip) continue
                var values = Object.keys(group.selections || {}).map(function(k) { return group.selections[k] })
                if (group.sheet_needs_confirmation || !values.length || values.some(function(v) { return !v })
                        || values.some(function(v, n) { return values.indexOf(v) !== n })) {
                    if (salaryIndex !== g) {
                        salaryIndex = g; loadSalaryGroup()
                        Qt.callLater(function() { if (dialog.opened && !dialog.working) dialog.locateProblem() })
                    } else focusProblemControl(templatePicker)
                    return
                }
            }
            for (var n = 0; n < salaryIssues.length; n++) {
                if (!salaryIssues[n].skippable || !salaryIssues[n].skip) {
                    var issue = issueRepeater.itemAt(n)
                    focusProblemControl(issue ? issue.focusControl : salaryFilesSection)
                    return
                }
            }
            if (problem) { focusProblemControl(templatePicker); return }
        }
        // The fixed footer is already visible. Focusing never checks this box.
        confirmed.forceActiveFocus(Qt.TabFocusReason)
    }
    onAccepted: backend.saveTemplateChoice(JSON.stringify({role: role.key, sheet: sheet.name,
        row: skipping ? 1 : headerRow, columns: chosen, sheet_selections: sheetSelections, remember: rememberChoice.checked}))
    onRejected: { lastPayload = ""; confirmed.checked = false }
    onClosed: {
        if (salaryMode && !closingFromBackend && backend) backend.cancelSalaryMappings()
        hasDocument = false
    }
    contentItem: ColumnLayout {
        spacing: 12
        RowLayout {
            Layout.fillWidth: true
            AppButton { text: "本次文件确认"; variant: dialog.rulesPage || dialog.profilesPage ? "secondary" : "primary"; onClicked: { dialog.rulesPage = false; dialog.profilesPage = false } }
            AppButton { text: "已记住的选择（" + (dialog.backend ? dialog.backend.templateSavedProfileCount : 0) + "）"; visible: dialog.backend && dialog.backend.currentTool !== "salary_merge"; variant: dialog.profilesPage ? "primary" : "secondary"; enabled: !dialog.working; onClicked: { dialog.rulesPage = false; dialog.profilesPage = true } }
            AppButton { text: "列名 / 工作表设置"; variant: dialog.rulesPage ? "primary" : "secondary"; enabled: !dialog.working; onClicked: dialog.backend.reviewTemplateRules() }
            Item { Layout.fillWidth: true }
        }
        TemplateNameEditor {
            id: nameEditor
            Layout.fillWidth: true; Layout.fillHeight: true; visible: dialog.rulesPage
            enabled: !dialog.working
            onRulesSubmitted: function(payload) {
                if (!dialog.backend.saveTemplateRules(payload)) return
                if (dialog.salaryMode && dialog.working) { dialog.rulesPage = false; return }
                var resume = dialog.hasDocument
                dialog.close()
                if (resume) dialog.backend.runOrCancel()
            }
        }
        ColumnLayout {
            Layout.fillWidth: true; Layout.fillHeight: true; visible: dialog.profilesPage
            Label {
                Layout.fillWidth: true; wrapMode: Text.Wrap
                text: "这些选择会用于当前工具中工作表名和表头相同的文件。列的含义变了，请修改或删除；删除后按原有名称识别，不认识的列会重新询问。"
            }
            Label { visible: dialog.backend && !dialog.backend.templateSavedProfileCount; text: "还没有记住任何选择。确认列名时默认仅本次使用。"; wrapMode: Text.Wrap; Layout.fillWidth: true }
            ScrollView {
                Layout.fillWidth: true; Layout.fillHeight: true; clip: true; contentWidth: availableWidth
                Column {
                    width: parent.width; spacing: 12
                    Repeater {
                        model: dialog.profilesPage && dialog.backend ? dialog.backend.templateSavedProfiles : []
                        delegate: ColumnLayout {
                            property var savedProfile: modelData
                            width: parent.width; spacing: 6
                            Label { Layout.fillWidth: true; text: savedProfile.label + " · " + savedProfile.sheet + " · 第 " + savedProfile.row + " 行"; font.bold: true; textFormat: Text.PlainText; wrapMode: Text.Wrap }
                            Label { Layout.fillWidth: true; visible: !!savedProfile.file; text: "首次确认文件：" + savedProfile.file; textFormat: Text.PlainText; wrapMode: Text.Wrap; color: "#77746D" }
                            Label { Layout.fillWidth: true; text: savedProfile.description; textFormat: Text.PlainText; wrapMode: Text.Wrap }
                            Label { Layout.fillWidth: true; visible: !savedProfile.editable; text: "旧版或跳过记录可直接删除；重新处理文件时再选择。"; color: "#77746D"; wrapMode: Text.Wrap }
                            RowLayout {
                                AppButton { text: "修改"; visible: savedProfile.editable; enabled: !dialog.working; onClicked: dialog.backend.editTemplateProfile(savedProfile.key) }
                                AppButton { text: "删除"; enabled: !dialog.working; onClicked: dialog.backend.deleteTemplateProfile(savedProfile.key) }
                            }
                            Rectangle { Layout.fillWidth: true; implicitHeight: 1; color: "#E3E0D8" }
                        }
                    }
                }
            }
        }
        Label {
            Layout.fillWidth: true; Layout.fillHeight: true; visible: !dialog.rulesPage && !dialog.profilesPage && !dialog.hasDocument
            wrapMode: Text.Wrap
            text: "开始处理时，工具会自动检查已选择的资料。能识别的直接使用，需要你确认的会显示在这里。\n\n如果只是想添加、修改或删除列名，请切换到“常用名称管理”。"
        }
        Flickable {
        id: problemViewport
        Layout.fillWidth: true; Layout.fillHeight: true; visible: !dialog.rulesPage && !dialog.profilesPage && dialog.hasDocument
        clip: true
        contentHeight: body.implicitHeight
        contentWidth: width
        boundsBehavior: Flickable.StopAtBounds
        ScrollBar.vertical: ScrollBar {}
        ColumnLayout {
            id: body
            width: parent.width
            spacing: 10
            enabled: !dialog.working
            ColumnLayout {
                id: salaryFilesSection
                Layout.fillWidth: true; visible: dialog.salaryMode
                Label { text: "本次模板（相同模板只需确认一次）"; font.bold: true; font.pixelSize: 14 }
                AppComboBox {
                    id: templatePicker
                    Layout.fillWidth: true
                    Accessible.name: "选择本次需要确认的模板"
                    model: dialog.salaryRevision >= 0 ? dialog.salaryGroups.map(function(g, i) {
                        var ready = !g.sheet_needs_confirmation && Object.keys(g.selections || {}).every(function(k) { return !!g.selections[k] })
                        return "模板 " + (i + 1) + " · " + (g.role === "summary" ? "已有汇总表" : "工资明细") + " · " + g.files.length + " 个文件 · " + (g.skip ? "已跳过" : ready ? "已选齐" : "待确认")
                    }) : []
                    currentIndex: dialog.salaryIndex
                    onActivated: function(index) { dialog.salaryIndex = index; dialog.loadSalaryGroup() }
                }
                Repeater {
                    id: issueRepeater
                    model: dialog.salaryIssues
                    delegate: ColumnLayout {
                        property var focusControl: modelData.skippable ? issueCheck : issueText
                        Layout.fillWidth: true
                        Label { id: issueText; Layout.fillWidth: true; wrapMode: Text.Wrap; text: modelData.name + "：" + modelData.message; textFormat: Text.PlainText; color: "#A26713" }
                        AppCheckBox {
                            id: issueCheck
                            text: modelData.skippable ? "本次跳过这个文件（结果中会列明）" : "此文件需要处理后重新选择，不能跳过"
                            enabled: modelData.skippable; checked: !!modelData.skip
                            onToggled: { dialog.salaryIssues[index].skip = checked; dialog.salaryRevision++; confirmed.checked = false }
                        }
                    }
                }
                AppCheckBox {
                    visible: dialog.salaryGroup.role === "detail"
                    text: "本次不合并这一类文件（结果中会列明）"
                    checked: dialog.salaryRevision >= 0 && !!dialog.salaryGroup.skip
                    onToggled: { dialog.salaryGroup.skip = checked; dialog.salaryRevision++; confirmed.checked = false }
                }
            }
            ColumnLayout {
                id: sheetConfirmation
                Layout.fillWidth: true; visible: dialog.sheetMode; spacing: 12
                Label { Layout.fillWidth: true; text: "请选择需要读取的工作表"; font.bold: true; wrapMode: Text.Wrap }
                Label { Layout.fillWidth: true; text: "文件：" + (dialog.mappingData.file || "当前文件"); textFormat: Text.PlainText; wrapMode: Text.Wrap }
                Label { Layout.fillWidth: true; text: dialog.mappingData.message || ""; textFormat: Text.PlainText; wrapMode: Text.Wrap }
                AppComboBox {
                    Layout.fillWidth: true; visible: !!dialog.mappingData.alternatives
                    model: dialog.mappingData.roles.map(function(r) { return r.label })
                    currentIndex: dialog.roleIndex
                    displayText: currentIndex >= 0 ? currentText : "请选择需要读取的资料类型"
                    onActivated: function(index) { dialog.roleIndex = index; confirmed.checked = false }
                }
                Repeater {
                    model: dialog.sheetRequests()
                    delegate: ColumnLayout {
                        property var requestItem: modelData
                        property var options: [{label: "请选择 Excel 底部的工作表", value: undefined}].concat(
                            dialog.mappingData.sheets.map(function(s) { return {label: s.name, value: s.name} }),
                            requestItem.optional ? [{label: "本次没有这类工作表", value: null}] : [])
                        property int selectedIndex: {
                            for (var i = 1; i < options.length; i++)
                                if (options[i].value === dialog.sheetSelections[requestItem.key]) return i
                            return 0
                        }
                        Layout.fillWidth: true
                        Label { text: requestItem.label + "数据所在页"; textFormat: Text.PlainText }
                        AppComboBox {
                            Layout.fillWidth: true; model: parent.options; textRole: "label"
                            currentIndex: parent.selectedIndex
                            onActivated: function(index) { dialog.selectSheetForRole(requestItem.key, model[index].value) }
                        }
                        Label {
                            Layout.fillWidth: true; wrapMode: Text.Wrap; textFormat: Text.PlainText; color: "#77746D"
                            text: {
                                var name = dialog.sheetSelections[requestItem.key]
                                var pages = dialog.mappingData.sheets.filter(function(s) { return s.name === name })
                                return pages.length ? "内容预览：" + pages[0].rows.slice(0, 5).map(function(row) {
                                    return row.filter(function(v) { return !!v }).slice(0, 6).join(" · ")
                                }).filter(function(row) { return !!row }).join("\n") : ""
                            }
                        }
                    }
                }
                Label { Layout.fillWidth: true; wrapMode: Text.Wrap; text: "只确认工作表位置，不修改原文件。确认后会检查对应列；缺少资料的选择仅本次有效。"; color: "#77746D" }
            }
            ColumnLayout {
                Layout.fillWidth: true; visible: !dialog.sheetMode
            Label {
                Layout.fillWidth: true; wrapMode: Text.Wrap; textFormat: Text.PlainText
                text: dialog.columnConfirmationHeading()
                font.bold: true; font.pixelSize: 16
            }
            Text {
                Layout.fillWidth: true
                text: dialog.editingSaved ? "修改后仅保存选择，不会开始处理文件。" : "请选出未识别内容所在的列。下拉选项里有原表内容，方便核对。"
                color: "#55534D"; font.pixelSize: 13; wrapMode: Text.Wrap
            }
            Text {
                Layout.fillWidth: true
                text: "文件：" + (dialog.mappingData.file || "本次选择的资料")
                textFormat: Text.PlainText; wrapMode: Text.Wrap; font.pixelSize: 12; color: "#77746D"
            }
            Label {
                Layout.fillWidth: true; wrapMode: Text.Wrap; textFormat: Text.PlainText
                text: "所在工作表：" + (dialog.sheet.name || "未选择")
                font.pixelSize: 12; color: "#77746D"
            }
            RowLayout {
                Layout.fillWidth: true; visible: !!dialog.role.key
                Label {
                    Layout.fillWidth: true; wrapMode: Text.Wrap; textFormat: Text.PlainText
                    text: (dialog.role.key === "attendance_summary" || dialog.role.key === "attendance" ? "数据排列方式：" : "读取方式：") + dialog.readingModeLabel(dialog.role)
                    font.pixelSize: 12; color: "#55534D"
                }
                AppButton {
                    text: dialog.roleDetailsExpanded ? "收起" : "修改"
                    variant: "link"; visible: dialog.mappingData.roles.length > 1
                    Accessible.name: "修改数据读取方式"
                    onClicked: dialog.roleDetailsExpanded = !dialog.roleDetailsExpanded
                }
            }
            ColumnLayout {
                Layout.fillWidth: true
                visible: dialog.mappingData.roles.length > 1 && (dialog.roleDetailsExpanded || !dialog.role.key)
                Label { text: "按数据的排列方式选择" }
                AppComboBox {
                    id: rolePicker
                    Layout.fillWidth: true
                    Accessible.name: "数据读取方式"
                    model: dialog.mappingData.roles.map(function(r) { return dialog.readingModeLabel(r) })
                    currentIndex: dialog.roleIndex
                    displayText: currentIndex >= 0 ? currentText : "请选择数据的读取方式"
                    onActivated: function(index) { dialog.roleIndex = index; dialog.suggestRow(); dialog.roleDetailsExpanded = false }
                }
            }
            Label { visible: dialog.mappingData.sheets.length > 1; text: "读取哪个工作表（Excel 底部的标签）" }
            AppComboBox {
                id: sheetPicker
                Layout.fillWidth: true; visible: dialog.mappingData.sheets.length > 1
                Accessible.name: "读取哪个工作表"
                model: dialog.mappingData.sheets.map(function(s) { return s.name })
                currentIndex: dialog.sheetIndex
                onActivated: function(index) { dialog.changeSheet(index) }
            }
            Label {
                Layout.fillWidth: true; wrapMode: Text.Wrap; visible: dialog.skipping; color: "#A26713"
                text: "这张工作表将不参与本次处理。请确认它不是需要统计的业务数据。"
            }
            ColumnLayout {
                id: sourceSection
                visible: !dialog.skipping && !!dialog.role.key; Layout.fillWidth: true; spacing: 8
                AppButton {
                    visible: !dialog.salaryMode && dialog.headerRow > 0
                    text: "列名在第 " + dialog.headerRow + " 行 · " + (dialog.detailsExpanded ? "收起原表" : "查看原表 / 调整行号")
                    variant: "link"
                    onClicked: dialog.detailsExpanded = !dialog.detailsExpanded
                }
                ColumnLayout {
                Layout.fillWidth: true; spacing: 8
                visible: dialog.salaryMode || dialog.detailsExpanded || !dialog.headerRow
                Label { text: "点选写着列名的那一行"; font.bold: true; font.pixelSize: 14 }
                Label {
                    Layout.fillWidth: true; wrapMode: Text.Wrap
                    text: dialog.headerRow ? "当前选中第 " + dialog.headerRow + " 行，请核对。选错了，点另一行即可。"
                                           : "例如写着“姓名、身份证号码、公司”的那一行，不是标题或人员数据。"
                    color: dialog.headerRow ? "#17715B" : "#A26713"; font.pixelSize: 12
                }
                RowLayout {
                    Layout.fillWidth: true
                    AppButton { text: "前几列"; enabled: dialog.columnPage > 0; onClicked: dialog.columnPage-- }
                    Label { Layout.fillWidth: true; horizontalAlignment: Text.AlignHCenter; text: dialog.letter(dialog.columnPage * dialog.pageSize + 1) + "—" + dialog.letter(Math.min(dialog.columnCount, (dialog.columnPage + 1) * dialog.pageSize)) + "列" }
                    AppButton { text: "后几列"; enabled: (dialog.columnPage + 1) * dialog.pageSize < dialog.columnCount; onClicked: dialog.columnPage++ }
                }
                // 只创建可见行和少量列，避免老电脑一次绘制上万格。
                ListView {
                    id: preview
                    objectName: "templateSourcePreview"
                    Layout.fillWidth: true; Layout.preferredHeight: 180
                    clip: true; model: dialog.sheet.rows
                    boundsBehavior: Flickable.StopAtBounds
                    ScrollBar.vertical: ScrollBar {}
                    delegate: Button {
                        id: previewRow
                        property int sourceRow: index + 1
                        property var values: modelData
                        property bool selectedRow: sourceRow >= dialog.headerRow && sourceRow <= (dialog.salaryMode ? dialog.headerBottom : dialog.headerRow)
                        width: preview.width - 12; height: 36; padding: 0
                        Accessible.name: "第 " + sourceRow + " 行，点击设为列名行"
                        onClicked: dialog.selectRow(sourceRow)
                        background: Rectangle { color: previewRow.selectedRow ? "#E4EFEA" : (previewRow.hovered ? "#F0EEE8" : "#FAF9F6"); border.color: "#E3E0D8" }
                        contentItem: Row {
                            Text { width: 42; height: 36; text: previewRow.sourceRow; font.bold: dialog.headerRow === previewRow.sourceRow; verticalAlignment: Text.AlignVCenter; horizontalAlignment: Text.AlignHCenter; color: "#17715B" }
                            Repeater {
                                model: dialog.pageSize
                                Text {
                                    width: Math.max(1, (previewRow.width - 42) / dialog.pageSize); height: 36
                                    text: previewRow.values[dialog.columnPage * dialog.pageSize + index] || ""
                                    textFormat: Text.PlainText; elide: Text.ElideRight; leftPadding: 6; rightPadding: 6
                                    verticalAlignment: Text.AlignVCenter; color: "#292825"; font.pixelSize: 12
                                }
                            }
                        }
                    }
                }
                Label { Layout.fillWidth: true; wrapMode: Text.Wrap; text: dialog.salaryMode ? "预览为已读取的前几行。列名占多行或位置更靠后时，可在下面调整后读取。" : "预览仅显示前 30 行、前 512 列。这里找不到列名时，请返回检查原文件；不会修改原表。"; color: "#77746D"; font.pixelSize: 11 }
                Flow {
                    Layout.fillWidth: true; Layout.preferredHeight: childrenRect.height
                    visible: dialog.salaryMode; spacing: 6
                    Label { text: "列名从第"; height: 36; verticalAlignment: Text.AlignVCenter }
                    SpinBox { from: 1; to: 200; value: dialog.headerRow || 1; editable: true; width: 110; height: 36; onValueModified: { dialog.headerRow = value; dialog.headerBottom = Math.max(value, Math.min(dialog.headerBottom, value + 5)); confirmed.checked = false } }
                    Label { text: "行，到第"; height: 36; verticalAlignment: Text.AlignVCenter }
                    SpinBox { from: Math.max(1, dialog.headerRow); to: Math.min(200, from + 5); value: dialog.headerBottom || 1; editable: true; width: 110; height: 36; onValueModified: { dialog.headerBottom = value; confirmed.checked = false } }
                    Label { text: "行"; height: 36; verticalAlignment: Text.AlignVCenter }
                    AppButton { id: readHeadersButton; text: "读取这些列名"; onClicked: dialog.backend.rescanSalaryHeader(dialog.salaryGroup.group_id, dialog.sheet.name, dialog.headerRow, dialog.headerBottom, dialog.salaryPayload()) }
                    AppButton { text: "恢复自动识别"; onClicked: dialog.backend.resetSalaryHeader(dialog.salaryGroup.group_id, dialog.salaryPayload()) }
                }
                }
                Label { text: dialog.editingSaved ? "修改对应列" : "需要你确认的列"; font.bold: true; font.pixelSize: 14 }
                Label { Layout.fillWidth: true; wrapMode: Text.Wrap; visible: !dialog.salaryMode && dialog.recognizedCount() > 0; text: "另有 " + dialog.recognizedCount() + " 项已识别，可展开下方选项查看或修改。"; color: "#17715B"; font.pixelSize: 12 }
                AppTextField { id: search; Layout.fillWidth: true; visible: extra.checked && Object.keys(dialog.role.fields).length > 8; placeholderText: "要找哪一项？例如：公司、金额"; Accessible.name: "查找需要对应的内容" }
                AppTextField { id: columnSearch; Layout.fillWidth: true; visible: dialog.columnChoices.length > 16; placeholderText: "原表列太多？输入列名或内容，缩小下拉选项范围"; Accessible.name: "筛选原表中的列" }
                AppCheckBox { id: extra; text: "查看已识别和其他可选列"; onToggled: if (!checked) search.text = "" }
                Repeater {
                    id: fieldRepeater
                    model: dialog.fieldNames()
                    delegate: ColumnLayout {
                        property var editor: fieldEditor
                        property string fieldName: modelData
                        property bool requiredField: dialog.role.required.indexOf(fieldName) >= 0
                        visible: ((dialog.salaryMode && requiredField) || dialog.attentionFields.indexOf(fieldName) >= 0 || extra.checked || search.text.length > 0)
                                 && (!search.text || dialog.fieldLabel(fieldName).toLowerCase().indexOf(search.text.toLowerCase()) >= 0)
                        Layout.fillWidth: true; spacing: 4
                        Label { text: dialog.fieldLabel(fieldName) + "对应列" + (requiredField ? "（必须选择）" : "（可不选）"); textFormat: Text.PlainText; font.pixelSize: 13 }
                        AppComboBox {
                            id: fieldEditor
                            Layout.fillWidth: true; enabled: dialog.headerRow > 0 && !dialog.salaryNeedsRead()
                            Accessible.name: "选择“" + dialog.fieldLabel(fieldName) + "”在原表中的列"
                            model: dialog.filteredColumns(fieldName); textRole: "label"
                            currentIndex: dialog.filteredIndex(fieldName, model)
                            displayText: currentIndex > 0 ? currentText : (requiredField ? "请选择“" + dialog.fieldLabel(fieldName) + "”所在列" : "不指定，保留原来的读取方式")
                            onActivated: function(index) { dialog.chooseColumn(fieldName, model[index].col) }
                        }
                        Label { Layout.fillWidth: true; wrapMode: Text.Wrap; visible: !!dialog.chosen[fieldName] && !dialog.editingSaved; text: "原表内容示例：" + dialog.sample(dialog.chosen[fieldName]); textFormat: Text.PlainText; color: "#77746D"; font.pixelSize: 12; maximumLineCount: 2; elide: Text.ElideRight }
                    }
                }
            }
            }
            Label {
                Layout.fillWidth: true; wrapMode: Text.Wrap; textFormat: Text.PlainText
                text: dialog.problem || (dialog.editingSaved ? "请核对后保存修改。" : "选择已齐全，请核对后继续。")
                color: dialog.problem ? "#A26713" : "#17715B"; font.pixelSize: 13
            }
        }
    }
    }
    footer: Rectangle {
        implicitHeight: actions.implicitHeight + 24
        color: "#FAF9F6"; radius: 12
        ColumnLayout {
            id: actions
            anchors.left: parent.left; anchors.right: parent.right; anchors.top: parent.top
            anchors.margins: 12; spacing: 6
            Label {
                Layout.fillWidth: true; wrapMode: Text.Wrap; maximumLineCount: 2; elide: Text.ElideRight
                text: dialog.working ? "正在读取，请稍候…" : dialog.profilesPage ? "修改或删除已记住的选择，不会修改原文件和已有结果。" : dialog.rulesPage ? "常用名称对当前工具长期生效；如“222”含义会变，请使用本次文件确认。" : !dialog.hasDocument ? "原文件不会被修改。" : dialog.problem || (!confirmed.checked ? (dialog.sheetMode ? "请核对工作表选择。" : "请核对所选列的含义。") : "已完成核对，可以继续。")
                textFormat: Text.PlainText; color: dialog.problem ? "#A26713" : "#17715B"; font.pixelSize: 12
            }
            AppCheckBox {
                id: confirmed
                Layout.fillWidth: true
                visible: !dialog.rulesPage && !dialog.profilesPage && dialog.hasDocument
                text: dialog.sheetMode ? "已核对工作表选择及本次缺少的资料" : dialog.salaryMode ? "已核对本次全部模板及跳过的文件" : dialog.skipping ? "确认这张工作表不需要处理" : "已核对：读取方式和所选列的含义正确"
                enabled: !dialog.working && !dialog.problem
            }
            AppCheckBox { id: rememberSalary; visible: dialog.salaryMode && dialog.hasDocument && !dialog.rulesPage; text: "记住本项目的选择"; checked: true; enabled: !dialog.working }
            AppCheckBox { id: rememberChoice; visible: !dialog.salaryMode && !dialog.editingSaved && dialog.hasDocument && !dialog.rulesPage && !dialog.profilesPage; text: dialog.sheetMode ? "记住所选页名，下次自动识别（可在工作表设置中修改、删除）" : "记住相同表头的选择（不勾选仅本次，可随时撤销）"; checked: false; enabled: !dialog.working }
            Flow {
                Layout.fillWidth: true; Layout.preferredHeight: childrenRect.height
                layoutDirection: Qt.RightToLeft; spacing: 8
                AppButton { text: dialog.problem ? "查看未完成项" : "核对选择"; variant: "link"; visible: dialog.hasDocument && !dialog.rulesPage && !dialog.profilesPage; enabled: !dialog.working; onClicked: dialog.locateProblem() }
                AppButton { text: dialog.acceptText; variant: "primary"; enabled: dialog.acceptButtonEnabled; onClicked: dialog.applyChoices() }
                AppButton { visible: dialog.salaryMode && !dialog.rulesPage; text: "仅保存"; enabled: !dialog.working && rememberSalary.checked && !dialog.problem; onClicked: dialog.backend.applySalaryMappings(dialog.salaryPayload(), true, false) }
                AppButton { text: dialog.rejectText; onClicked: dialog.reject() }
            }
        }
    }
}
