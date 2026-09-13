import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15

AppDialog {
    id: dialog
    property var sections: []
    property int sectionIndex: 0
    property int revision: 0
    property var currentSection: sections.length ? sections[sectionIndex] : ({})
    signal rulesSubmitted(string payload)
    title: "字段与工作表的常用名称"
    width: Math.min(parent ? parent.width - 32 : 720, 720)
    height: Math.min(parent ? parent.height - 32 : 660, 660)
    x: parent ? (parent.width - width) / 2 : 0
    y: parent ? (parent.height - height) / 2 : 0
    acceptText: "保存名称规则并重新检查"
    rejectText: "取消"

    function showSections(value) {
        sections = JSON.parse(JSON.stringify(value))
        for (var i = 0; i < sections.length; i++) {
            var names = sections[i].options.slice()
            var selected = sections[i].selected || []
            for (var j = 0; j < selected.length; j++)
                if (names.indexOf(selected[j]) < 0) names.push(selected[j])
            sections[i].options = names
        }
        sectionIndex = 0
        search.text = ""
        newName.text = ""
        revision++
        open()
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
        return (currentSection.selected || []).indexOf(value) >= 0
    }
    function toggle(value, checked) {
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
        if (currentSection.options.indexOf(value) < 0) currentSection.options.push(value)
        toggle(value, true)
        search.text = ""
        newName.text = ""
    }
    onAccepted: {
        var rules = {fields: {}, sheets: {}}
        for (var i = 0; i < sections.length; i++) {
            var item = sections[i]
            rules[item.kind][item.key] = item.selected || []
        }
        rulesSubmitted(JSON.stringify(rules))
    }
    contentItem: ColumnLayout {
        spacing: 10
        Text {
            Layout.fillWidth: true
            text: "同一个意思可以勾选多个名称，例如姓名、名字、name。每份表命中一个即可；找不到或同时命中多列时，会请你确认。规则在本机同一工具的不同工作项目间通用，不改原文件。"
            wrapMode: Text.Wrap; color: "#55534D"; font.pixelSize: 12
        }
        AppComboBox {
            Layout.fillWidth: true
            model: dialog.sections.map(function(s) { return s.label })
            currentIndex: dialog.sectionIndex
            onActivated: function(index) { dialog.sectionIndex = index; search.text = ""; newName.text = "" }
        }
        Text {
            Layout.fillWidth: true
            text: dialog.revision >= 0 ? "已选择：" + ((dialog.currentSection.selected || []).join("、") || "无") : ""
            color: "#187A65"; font.pixelSize: 12; wrapMode: Text.Wrap; textFormat: Text.PlainText
        }
        Text {
            Layout.fillWidth: true
            visible: dialog.currentSection.kind === "sheets"
            text: "工作表名称未勾选时沿用原有自动识别；勾选后只匹配这些名称，不会把多张同名用途的表自动合并。"
            wrapMode: Text.Wrap; color: "#77746D"; font.pixelSize: 11
        }
        RowLayout {
            Layout.fillWidth: true
            AppTextField { id: newName; Layout.fillWidth: true; placeholderText: "也可以手动添加其他模板中的名称"; onAccepted: dialog.addName() }
            AppButton { text: "添加并选中"; onClicked: dialog.addName() }
        }
        AppTextField { id: search; Layout.fillWidth: true; placeholderText: "查找当前资料中的名称，最多显示 100 项" }
        ScrollView {
            Layout.fillWidth: true; Layout.fillHeight: true
            clip: true
            contentWidth: availableWidth
            Column {
                width: parent.width
                Repeater {
                    model: dialog.choices()
                    delegate: AppCheckBox {
                        width: parent.width
                        text: modelData
                        checked: dialog.selected(modelData)
                        onToggled: dialog.toggle(modelData, checked)
                    }
                }
            }
        }
    }
}
