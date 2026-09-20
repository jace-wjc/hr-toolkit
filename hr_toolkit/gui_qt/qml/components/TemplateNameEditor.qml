import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15

Item {
    id: dialog
    property var sections: []
    property int sectionIndex: 0
    property string kindFilter: "fields"
    property var filteredSections: sections.filter(function(s) { return s.kind === dialog.kindFilter })
    property int revision: 0
    property string editingName: ""
    property string editError: ""
    property var currentSection: sections.length ? sections[sectionIndex] : ({})
    signal rulesSubmitted(string payload)

    function normalized(value) {
        var text = String(value)
        if (text.normalize) text = text.normalize("NFKC")
        return text.replace(/\s/g, "").toLowerCase()
    }
    function uniqueNames(values) {
        var result = [], seen = []
        for (var i = 0; i < values.length; i++) {
            var key = normalized(values[i])
            if (seen.indexOf(key) < 0) { seen.push(key); result.push(values[i]) }
        }
        return result
    }
    function isBuiltin(value) {
        return (currentSection.builtins || []).map(normalized).indexOf(normalized(value)) >= 0
    }
    function cancelEdit() { editingName = ""; newName.text = ""; editError = "" }

    function showSections(value) {
        sections = JSON.parse(JSON.stringify(value))
        for (var i = 0; i < sections.length; i++) {
            var builtin = sections[i].builtins || []
            var names = builtin.concat(sections[i].options || [])
            var selected = uniqueNames(builtin.concat(sections[i].selected || []))
            sections[i].selected = selected
            for (var j = 0; j < selected.length; j++)
                if (names.indexOf(selected[j]) < 0) names.push(selected[j])
            sections[i].options = uniqueNames(names)
        }
        setKind("fields")
        search.text = ""
        cancelEdit()
        revision++
    }
    function setKind(kind) {
        kindFilter = kind
        for (var i = 0; i < sections.length; i++) if (sections[i].kind === kind) { sectionIndex = i; break }
        search.text = ""; cancelEdit()
    }
    function choices() {
        var tick = revision
        var query = search.text.toLowerCase().trim()
        return (currentSection.options || []).filter(function(value) {
            return !query || value.toLowerCase().indexOf(query) >= 0
        }).slice(0, 100)
    }
    function selected(value) {
        var tick = revision
        return (currentSection.selected || []).map(normalized).indexOf(normalized(value)) >= 0
    }
    function toggle(value, checked) {
        if (isBuiltin(value)) return
        var values = (currentSection.selected || []).slice()
        var i = values.indexOf(value)
        if (checked && i < 0) values.push(value)
        if (!checked && i >= 0) values.splice(i, 1)
        currentSection.selected = values
        revision++
    }
    function addName() {
        var value = newName.text.trim()
        if (!value || !sections.length) return
        if (isBuiltin(value)) { editError = "这是系统内置名称，不需要重复添加，也不能修改。"; return }
        if (selected(value) && normalized(value) !== normalized(editingName)) { editError = "此名称已经添加。"; return }
        if (editingName) removeName(editingName)
        if (currentSection.options.indexOf(value) < 0) currentSection.options.push(value)
        toggle(value, true)
        search.text = ""
        cancelEdit()
    }
    function editName(value) {
        if (isBuiltin(value) || !selected(value)) return
        editingName = value
        newName.text = value
        editError = ""
        newName.forceActiveFocus()
        newName.selectAll()
    }
    function removeName(value) {
        if (isBuiltin(value)) return
        var key = normalized(value)
        currentSection.selected = (currentSection.selected || []).filter(function(v) { return normalized(v) !== key })
        currentSection.options = (currentSection.options || []).filter(function(v) { return normalized(v) !== key })
        if (normalized(editingName) === key) cancelEdit()
        revision++
    }
    function submit() {
        var rules = {fields: {}, sheets: {}}
        for (var i = 0; i < sections.length; i++) {
            var item = sections[i]
            rules[item.kind][item.key] = item.selected || []
        }
        rulesSubmitted(JSON.stringify(rules))
    }
    ColumnLayout {
        anchors.fill: parent
        spacing: 10
        Text {
            Layout.fillWidth: true
            text: "系统内置名称始终保留，不能取消、修改或删除。你添加的名称可以修改、删除，点击底部保存后生效；取消则不保存本次修改。同一工具的不同项目共用，不改原文件。"
            wrapMode: Text.Wrap; color: "#55534D"; font.pixelSize: 12
        }
        RowLayout {
            AppButton { text: "列名设置"; variant: dialog.kindFilter === "fields" ? "primary" : "secondary"; onClicked: dialog.setKind("fields") }
            AppButton { text: "工作表设置"; variant: dialog.kindFilter === "sheets" ? "primary" : "secondary"; onClicked: dialog.setKind("sheets") }
        }
        AppComboBox {
            Layout.fillWidth: true
            model: dialog.filteredSections.map(function(s) { return s.label })
            currentIndex: dialog.filteredSections.indexOf(dialog.currentSection)
            onActivated: function(index) { dialog.sectionIndex = dialog.sections.indexOf(dialog.filteredSections[index]); search.text = ""; dialog.cancelEdit() }
        }
        Text {
            Layout.fillWidth: true
            text: dialog.revision >= 0 ? "生效名称：" + ((dialog.currentSection.selected || []).join("、") || "沿用系统自动识别") : ""
            color: "#187A65"; font.pixelSize: 12; wrapMode: Text.Wrap; textFormat: Text.PlainText
        }
        Text {
            Layout.fillWidth: true
            visible: dialog.currentSection.kind === "sheets"
            text: dialog.currentSection.builtinRule || "系统原有工作表识别始终保留；自定义名称作为补充。"
            wrapMode: Text.Wrap; color: "#77746D"; font.pixelSize: 11
        }
        RowLayout {
            Layout.fillWidth: true
            AppTextField { id: newName; Layout.fillWidth: true; placeholderText: dialog.editingName ? "输入修改后的名称" : (dialog.kindFilter === "sheets" ? "添加页名，例如1、2、增员表" : "添加自定义名称，例如名字、name"); onAccepted: dialog.addName() }
            AppButton { text: dialog.editingName ? "确认修改" : "添加"; onClicked: dialog.addName() }
            AppButton { text: "取消修改"; visible: !!dialog.editingName; onClicked: dialog.cancelEdit() }
        }
        Text { Layout.fillWidth: true; visible: !!dialog.editError; text: dialog.editError; color: "#A26713"; wrapMode: Text.Wrap; textFormat: Text.PlainText }
        AppTextField { id: search; Layout.fillWidth: true; placeholderText: "查找当前资料中的名称，最多显示 100 项" }
        ScrollView {
            Layout.fillWidth: true; Layout.fillHeight: true
            clip: true
            contentWidth: availableWidth
            Column {
                width: parent.width
                Repeater {
                    model: dialog.choices()
                    delegate: RowLayout {
                        property string aliasName: modelData
                        width: parent.width
                        AppCheckBox {
                            Layout.fillWidth: true
                            text: aliasName + (dialog.isBuiltin(aliasName) ? "（系统内置）" : dialog.selected(aliasName) ? "（自定义）" : "（原表候选，勾选添加）")
                            checked: dialog.isBuiltin(aliasName) || dialog.selected(aliasName)
                            enabled: !dialog.isBuiltin(aliasName) && !dialog.selected(aliasName)
                            onToggled: if (checked) dialog.toggle(aliasName, true)
                        }
                        AppButton { text: "修改"; visible: !dialog.isBuiltin(aliasName) && dialog.selected(aliasName); onClicked: dialog.editName(aliasName) }
                        AppButton { text: "删除"; visible: !dialog.isBuiltin(aliasName) && dialog.selected(aliasName); onClicked: dialog.removeName(aliasName) }
                    }
                }
            }
        }
    }
}
