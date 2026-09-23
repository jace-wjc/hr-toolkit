pragma Singleton
import QtQuick 2.15
import "Palettes.js" as Palettes
QtObject {
    property var backend: null
    readonly property string theme: backend ? backend.theme : "light"
    readonly property string language: backend ? backend.language : "zh_CN"
    readonly property bool dark: theme === "dark"
    function chatFontSize(width) { return width >= 520 ? 15 : 14 }
    readonly property int chatCellPadding: 12
    function color(token) { return (Palettes.themes[theme] || Palettes.themes.light)[token] }
    function text(value) {
        var currentLanguage = language
        return backend ? backend.translate(String(value === undefined || value === null ? "" : value), currentLanguage) : String(value === undefined || value === null ? "" : value)
    }
}
