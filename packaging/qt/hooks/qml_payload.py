"""Narrow QML collection for the pinned PyInstaller 6.21 release runtime."""
from pathlib import Path, PurePath


def collect_required_qml_files(info, required):
    if info.version is None:
        return [], []
    source = info.location.get("QmlImportsPath") or info.location.get("Qml2ImportsPath")
    if not source or not Path(source).is_dir():
        raise RuntimeError("Qt Quick release runtime has no QML import directory")
    source = Path(source).resolve()
    destination = PurePath(info.qt_rel_dir) / "qml"
    binaries, datas = [], []
    for qmldir in sorted(source.rglob("qmldir")):
        plugin_destination = destination / qmldir.parent.relative_to(source)
        if not required((str(qmldir), str(plugin_destination))):
            continue
        # Keep PyInstaller's plugin dependency checks; run them only for the
        # modules we ship, rather than inspecting every unused Qt plugin first.
        plugin_binaries, plugin_datas = info._process_qml_plugin(qmldir)
        for entries, result in ((plugin_binaries, binaries), (plugin_datas, datas)):
            for entry in entries:
                if entry.suffix == ".qmltypes":
                    continue  # IDE type descriptions, never QML runtime code.
                relative = entry.relative_to(source) if entry.is_dir() else entry.parent.relative_to(source)
                result.append((str(entry), str(destination / relative)))
    return binaries, datas
