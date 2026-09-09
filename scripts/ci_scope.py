"""Select daily CI checks; full discovery requires an explicit manual request.

Keep this routing table with changes to shared code and its callers. Unknown
application code fails planning instead of silently skipping tests or running
the full suite. This module uses only the Python 3.8 standard library.
"""

import argparse
import json
import os
from pathlib import Path
import re
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]
GUI = "qt_controller qt_entrypoint qt_form_specs material_collector_gui project_creation_gui"
STORE = "project_store project_store_lite history_store project_run run_coordinator " + GUI
PROCESS = "background_process run_coordinator project_run performance_regressions " + GUI
BUSINESS = (
    "archive_import data_statistics salary_merge salary_split social_security "
    "insurance_ledger personnel_change_merge folder_rename material_collector "
    "output_regression tool_cancellation"
)
MATERIAL = (
    "material_collector material_document_groups material_ocr_progress "
    "material_preferences material_collector_gui performance_regressions"
)
RUNTIME = "runtime_checks paths pdf_backend_compat tool_registry background_process " + GUI
# Preserve the existing frozen-stack coverage ceiling in manual full mode.
WIN7 = set((
    "archive_import data_statistics project_store runtime_checks salary_merge "
    "salary_split social_security tool_registry paths pdf_backend_compat "
    "release_metadata background_process qt_controller qt_entrypoint qt_form_specs "
    "run_coordinator material_preferences material_collector_gui project_creation_gui "
    "ci_scope"
).split())
PIN_TEST = (
    "tests.test_windows_packaging.WindowsPackagingTests."
    "test_ci_actions_are_immutable_and_production_dependencies_are_locked"
)

# Entries add caller coverage to the matching test_<filename>.py, when it exists.
ROUTES = {
    "hr_toolkit/common/paths.py": "paths app_update runlog runtime_checks " + STORE + " " + PROCESS,
    "hr_toolkit/common/inputs.py": "inputs " + BUSINESS + " " + STORE,
    "hr_toolkit/common/excel.py": "excel_helpers " + BUSINESS,
    "hr_toolkit/common/excel_compat.py": "excel_helpers pdf_backend_compat " + BUSINESS,
    "hr_toolkit/common/filenames.py": BUSINESS + " " + STORE,
    "hr_toolkit/common/resources.py": "excel_helpers runtime_checks app_icons " + BUSINESS + " " + GUI,
    "hr_toolkit/common/__init__.py": BUSINESS + " " + STORE,
    "hr_toolkit/project_store.py": STORE,
    "hr_toolkit/project_store_lite.py": STORE,
    "hr_toolkit/history_store.py": STORE,
    "hr_toolkit/project_run.py": PROCESS + " " + STORE,
    "hr_toolkit/run_coordinator.py": PROCESS,
    "hr_toolkit/background_process.py": PROCESS,
    "hr_toolkit/runlog.py": STORE,
    "hr_toolkit/runtime_checks.py": RUNTIME,
    "hr_toolkit/launcher.py": RUNTIME + " app_update",
    "hr_toolkit/__main__.py": RUNTIME,
    "hr_toolkit/__init__.py": "versioning release_metadata app_update " + RUNTIME,
    "hr_toolkit/cli.py": BUSINESS + " " + RUNTIME,
    "hr_toolkit/desktop_contract.py": PROCESS,
    "hr_toolkit/desktop_helpers.py": GUI + " " + STORE,
    "hr_toolkit/tutorial_content.py": GUI,
    "hr_toolkit/_icon_data.py": "app_icons qt_entrypoint",
    "hr_toolkit/update_runner.py": "app_update",
    "hr_toolkit/material_preferences.py": MATERIAL,
    "hr_toolkit/tools/material_collector.py": MATERIAL,
    "hr_toolkit/tools/material_progress.py": MATERIAL,
    "hr_toolkit/tools/salary_headers.py": "salary_merge salary_split output_regression",
    "hr_toolkit/tools/registry.py": "tool_registry " + BUSINESS + " " + GUI,
    "hr_toolkit/tools/__init__.py": BUSINESS,
    "hr_toolkit_app.py": RUNTIME,
    "hr_toolkit_qt_app.py": GUI,
    "hr_toolkit_updater.py": "app_update",
    "scripts/ci_scope.py": "ci_scope",
    "scripts/versioning.py": "versioning release release_metadata",
    "scripts/bump_version.py": "versioning",
    "scripts/release.py": "release versioning",
    "scripts/release_windows.py": "release windows_packaging",
    "scripts/build_update_assets.py": "app_update release_metadata",
    "scripts/generate_release_metadata.py": "release_metadata",
    "scripts/prepare_gitee_release.py": "prepare_gitee_release gitee_mirror",
    "scripts/publish_gitee_release.py": "prepare_gitee_release gitee_mirror",
    "scripts/compare_regression_outputs.py": "output_regression",
    "scripts/generate_app_icons.py": "app_icons",
    "scripts/prepare_win7_runtime.py": "windows_packaging runtime_checks",
    "scripts/build_windows.py": "windows_packaging",
    "scripts/build_windows_installers.py": "windows_packaging",
    "scripts/build_macos.py": "macos_smoke windows_packaging",
    "scripts/prepare_macos_x64_runtime.py": "macos_smoke",
    "scripts/verify_macos_bundle.py": "macos_smoke",
}


def select_scope(paths, full=False, root=ROOT):
    targets = set()
    python_files = []
    unmapped = []
    audit = full
    qt_smoke = full
    ocr_smoke = full
    for path in sorted(set(paths)):
        file = Path(path)
        if file.is_absolute() or ".." in file.parts:
            raise ValueError("Invalid repository path: " + path)
        if path.endswith(".py") and (root / path).is_file():
            python_files.append(path)
        names = set(ROUTES.get(path, "").split())
        # Deleted tests cannot be imported; renamed files arrive as delete + add.
        if path.startswith("tests/test_") and path.endswith(".py"):
            if (root / path).is_file():
                targets.add("tests." + file.stem)
        elif path.startswith("tests/qt_") or path.startswith("hr_toolkit/gui_qt/"):
            names.update(GUI.split())
        elif path.startswith("hr_toolkit/templates/"):
            names.update(BUSINESS.split())
        elif path.startswith(".github/workflows/"):
            targets.add(PIN_TEST)
            if file.name == "ci.yml":
                names.add("ci_scope")
            else:
                names.update("windows_packaging release release_metadata gitee_mirror".split())
        elif (file.name.startswith("requirements") and path.endswith(".txt")) or path.startswith("constraints/") or path == "pyproject.toml":
            audit = True
            names.update(RUNTIME.split())
        elif path.startswith(("packaging/", "installer/")) or path.endswith(".spec"):
            names.update("windows_packaging release_metadata".split())
        elif path in ("package.json", "package-lock.json"):
            names.update("versioning release_metadata".split())

        if path.startswith("hr_toolkit/tools/") and file.stem in BUSINESS.split():
            names.update("output_regression tool_cancellation".split())
        if path.startswith(("hr_toolkit/", "scripts/")) and path.endswith(".py"):
            conventional = root / "tests" / ("test_" + file.stem + ".py")
            if conventional.is_file():
                names.add(file.stem)
            if path.startswith("hr_toolkit/") and not names and not full:
                unmapped.append(path)
        targets.update("tests.test_" + name for name in names)

    if unmapped:
        raise ValueError("Add CI test routing for application files: " + ", ".join(unmapped))
    # Fail an obsolete mapping rather than hiding a missing test after a rename.
    for target in targets:
        module = target.split(".")[1]
        if not (root / "tests" / (module + ".py")).is_file():
            raise ValueError("CI test routing points to missing module: " + target)
    qt_smoke = qt_smoke or "tests.test_qt_entrypoint" in targets
    ocr_smoke = ocr_smoke or audit or bool(targets & {
        "tests.test_runtime_checks", "tests.test_material_collector",
        "tests.test_material_ocr_progress",
    })
    win7_targets = sorted(target for target in targets if target.split(".")[1][5:] in WIN7)
    if full:
        win7_targets = ["tests.test_" + name for name in sorted(WIN7)]
    return {
        "full": full,
        "targets": sorted(targets),
        "win7_targets": win7_targets,
        "python_files": python_files,
        "run": full or bool(targets or python_files),
        "tests": full or bool(targets),
        "win7_tests": bool(win7_targets),
        "audit": audit,
        "qt_smoke": qt_smoke,
        "ocr_smoke": ocr_smoke,
    }


def git(*args):
    return subprocess.check_output(["git", *args], cwd=str(ROOT), input=b"")


def diff_range(event_name, event):
    if event_name == "pull_request":
        base = event["pull_request"]["base"]["sha"]
        head = event["pull_request"]["head"]["sha"]
        return base + "..." + head
    if event_name == "push":
        base, head = event["before"], event["after"]
        if base == "0" * 40:
            base = git("hash-object", "-w", "-t", "tree", "--stdin").decode().strip()
        return base + ".." + head
    if event_name == "workflow_dispatch":
        # A manual incremental run covers the selected ref's last commit.
        parents = git("rev-list", "--parents", "-n", "1", "HEAD").decode().split()
        base = parents[1] if len(parents) > 1 else git("hash-object", "-w", "-t", "tree", "--stdin").decode().strip()
        return base + "..HEAD"
    raise ValueError("Unsupported CI event: " + event_name)


def plan():
    event = json.loads(Path(os.environ["GITHUB_EVENT_PATH"]).read_text(encoding="utf-8"))
    event_name = os.environ["GITHUB_EVENT_NAME"]
    full = event_name == "workflow_dispatch" and str(event.get("inputs", {}).get("full_tests", "false")).lower() == "true"
    revision_range = diff_range(event_name, event)
    # Fail on an unavailable base; never narrow a multi-commit push to HEAD^.
    try:
        changed = git("diff", "--name-only", "--no-renames", "-z", revision_range)
    except subprocess.CalledProcessError as error:
        raise ValueError("Cannot read the complete change range: " + revision_range + "; restore the missing history or explicitly request manual full validation.") from error
    paths = changed.decode("utf-8").split("\0")
    scope = select_scope([path for path in paths if path], full=full)
    with open(os.environ["GITHUB_OUTPUT"], "a", encoding="utf-8") as output:
        output.write("scope=" + json.dumps(scope, ensure_ascii=True) + "\n")
        for key, value in scope.items():
            output.write(key + "=" + json.dumps(value, ensure_ascii=True) + "\n")
    with open(os.environ["GITHUB_STEP_SUMMARY"], "a", encoding="utf-8") as summary:
        summary.write("### CI scope\n\nRange: `" + revision_range + "`\n\n")
        summary.write("Mode: " + ("manual full suite" if full else "changed files and related callers") + "\n\n")
        summary.write("```json\n" + json.dumps(scope, ensure_ascii=False, indent=2) + "\n```\n")


def run_tests():
    scope = json.loads(os.environ["CI_SCOPE"])
    win7 = os.environ.get("CI_WIN7") == "true"
    if scope["full"] and not win7:
        command = [sys.executable, "-m", "unittest", "discover", "-s", "tests", "-v"]
    else:
        targets = scope["win7_targets" if win7 else "targets"]
        if not targets:
            print("No related tests selected; skipping.")
            return
        if not all(re.fullmatch(r"tests\.test_\w+(?:\.\w+)*", item) for item in targets):
            raise ValueError("Invalid unittest target")
        command = [sys.executable, "-m", "unittest", "-v", *targets]
    subprocess.run(command, cwd=str(ROOT), check=True)


def compile_changed():
    paths = json.loads(os.environ["CI_SCOPE"])["python_files"]
    checked = 0
    for path in paths:
        # The legacy job historically excluded modern-only tests from compileall.
        if os.environ.get("CI_WIN7") == "true" and path.startswith("tests/") and Path(path).stem[5:] not in WIN7:
            continue
        file = ROOT / path
        if Path(path).is_absolute() or ROOT not in file.resolve().parents:
            raise ValueError("Invalid compilation path: " + path)
        if file.is_file():
            compile(file.read_bytes(), path, "exec", dont_inherit=True)
            checked += 1
    print("Syntax checked {} changed Python files.".format(checked))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("plan", "test", "compile"))
    args = parser.parse_args()
    {"plan": plan, "test": run_tests, "compile": compile_changed}[args.command]()
