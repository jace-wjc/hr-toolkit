from __future__ import annotations

import json
import os
from pathlib import Path
import tempfile
import threading
import time
import unittest
from datetime import date
from types import SimpleNamespace
from unittest.mock import Mock, patch


os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
os.environ.setdefault("HR_TOOLKIT_SKIP_UPDATE", "1")

try:
    from hr_toolkit.gui_qt.compat import QCoreApplication
    from hr_toolkit.gui_qt.controller import AppController
    from hr_toolkit.gui_qt.form_specs import ToolInvocation
    from hr_toolkit.gui_qt.models import LogModel
except ImportError:
    QCoreApplication = None
    AppController = None
    ToolInvocation = None
    LogModel = None


def _preview_probe(*, cancelled=None):
    if cancelled is not None and cancelled():
        raise RuntimeError("cancelled")
    from tests.test_rename_review import sample_plan
    return sample_plan()


def _prepare_template_choice(controller):
    from hr_toolkit.common.template_mapping import catalog
    controller.selectTool("data_statistics")
    controller._template_issue = {
        "tool": "data_statistics", "file": "考勤.xlsx",
        "roles": [{"key": "attendance_summary", **catalog("data_statistics")["attendance_summary"]}],
        "sheets": [{"name": "考勤表", "rows": [["222", "名字", "应出勤天数"], ["28", "测试人员", "20"]]}],
    }
    controller._template_issue_project = str(controller._project_path)
    controller._template_input_snapshot = controller._template_current_inputs()
    return {"role": "attendance_summary", "sheet": "考勤表", "row": 1, "columns": {"姓名": 1}}


@unittest.skipUnless(AppController is not None, "PySide GUI runtime is not installed")
class QtControllerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.application = QCoreApplication.instance() or QCoreApplication([])

    def controller(self):
        value = AppController()
        value._save_workspace_preferences = lambda: None
        # Qt translators are application-global; a closed controller can stay
        # alive in Python/Qt references until after the next test has started.
        self.addCleanup(lambda controller=value: controller.presentation.setLanguage("en_US"))
        return value

    def test_reconcile_variant_and_result_paths_are_available(self) -> None:
        controller = self.controller()
        self.addCleanup(controller.close)
        controller.selectTool("personnel_change_merge")
        self.assertIn({"id": "reconcile", "label": "流程核对"}, controller.variants)
        controller.selectVariant("reconcile")
        self.assertEqual(controller._spec.tool_id, "personnel_reconcile")
        self.assertEqual(controller._spec.support_id, "template_path")
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            report = root / "核对结果.xlsx"
            filled = root / "汇总表副本.xlsx"
            self.assertEqual(controller._result_output_paths("personnel_reconcile", {
                "output_file": str(report), "filled_output_file": str(filled),
                "source_file": str(root.parent / "原文件.xlsx"),
            }, root), [report, filled])

    def test_reconcile_validation_has_visible_dialog_and_does_not_start(self) -> None:
        from hr_toolkit.gui_qt.form_specs import FormValidationError
        controller = self.controller()
        self.addCleanup(controller.close)
        controller.selectTool("personnel_change_merge")
        controller.selectVariant("reconcile")
        prompts = []
        controller.notificationRequested.connect(lambda *args: prompts.append(args))
        with patch.object(controller, "_start_project_run") as start:
            for field in ("reconcile_month", "company_aliases"):
                message = "请检查：" + field
                controller._set_busy(True)
                controller._apply_invocation(None, FormValidationError("核对设置有误", message, field), False)
                self.assertFalse(controller._busy)
                self.assertEqual(prompts[-1], ("核对设置有误", message, "warning"))
                self.assertEqual(controller.selectionFeedback[field]["text"], message)
            start.assert_not_called()

    def test_reconcile_click_starts_without_confirmation(self) -> None:
        controller = self.controller()
        self.addCleanup(controller.close)
        controller.selectTool("personnel_change_merge")
        controller.selectVariant("reconcile")
        prompts = []
        controller.notificationRequested.connect(lambda *args: prompts.append(args))
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            flow, summary = root / "流程.xlsx", root / "汇总表.xlsx"
            flow.touch()
            summary.touch()
            controller._project_path = root
            controller._project_store = Mock(writable=True)
            key = controller._state_key()
            controller._input_states[key] = [flow]
            controller._support_states[key] = str(summary)
            with patch("hr_toolkit.gui_qt.controller.threading.Thread") as thread, \
                    patch.object(controller, "_start_project_run") as start:
                controller.runOrCancel()
                thread.call_args.kwargs["target"]()
                self.assertEqual(prompts, [])
                start.assert_called_once()
                self.assertEqual(start.call_args.args[0].tool_id, "personnel_reconcile")

    def test_replace_text_fields_keep_type_and_restore_existing_mode_labels(self) -> None:
        controller = self.controller()
        self.addCleanup(controller.close)
        controller.selectTool("folder_rename")
        for file_type in ("folder", "pdf", "image", "document", "all"):
            controller.setFieldValue("file_type", file_type)
            controller.setFieldValue("rename_mode", "replace_text")
            fields = {field["id"]: field for field in controller.formFields}
            self.assertTrue(fields["file_type"]["visible"])
            self.assertEqual(fields["file_type"]["value"], file_type)
            self.assertTrue(fields["rename_text"]["visible"])
            self.assertEqual(fields["rename_text"]["label"], "原文字")
            self.assertTrue(fields["replacement_name"]["visible"])
            self.assertEqual(fields["replacement_name"]["label"], "替换为")
            self.assertFalse(fields["target_name"]["visible"])
            self.assertFalse(controller.hasSupportField)
            for mode in ("append", "remove", "replace", "excel"):
                controller.setFieldValue("rename_mode", mode)
                legacy = {field["id"]: field for field in controller.formFields}
                self.assertEqual(legacy["file_type"]["value"], file_type)
                self.assertEqual(legacy["rename_text"]["label"], "追加/删除文字")
                self.assertEqual(legacy["replacement_name"]["label"], "新名称")
                self.assertEqual(legacy["target_name"]["visible"], mode != "excel")
                self.assertEqual(legacy["rename_text"]["visible"], mode in ("append", "remove"))
                self.assertEqual(legacy["replacement_name"]["visible"], mode == "replace")
                self.assertEqual(controller.hasSupportField, mode == "excel")

    def test_confirmed_rename_uses_review_plan_not_current_form_or_excel(self) -> None:
        from tests.test_rename_review import sample_plan
        controller = self.controller()
        self.addCleanup(controller.close)
        controller.selectTool("folder_rename")
        invocation = ToolInvocation(nav_id="folder_rename", variant="default", tool_id="folder_rename",
            tool_name="资料文件夹改名", group_name="人员与档案", description="Excel改名",
            function_module="hr_toolkit.tools.folder_rename", function_name="rename_files_by_excel",
            args=(), kwargs={"root_dir": "/old", "excel_path": "/missing.xlsx"}, preview=True)
        controller._rename_review_invocation = invocation
        controller._rename_review_context = (controller._state_key(), controller._project_generation)
        controller.setFieldValue("rename_mode", "append")
        plan = sample_plan()
        plan["rows"][0]["target_name"] = "韩信.PDF"
        with patch.object(controller, "_start_project_run") as start, patch.object(controller, "_prepare_invocation") as regenerate:
            controller._execute_reviewed_rename(plan)
        regenerate.assert_not_called()
        call = start.call_args.args[0]
        self.assertEqual(call.function_name, "execute_rename_plan")
        self.assertEqual(call.kwargs["plan"]["rows"][0]["target_name"], "韩信.PDF")
        self.assertNotIn("excel_path", call.kwargs)
        self.assertFalse(call.preview)

    def test_confirmed_rename_rejects_a_different_project(self) -> None:
        from tests.test_rename_review import sample_plan
        controller = self.controller()
        self.addCleanup(controller.close)
        controller._rename_review_invocation = object()
        controller._rename_review_context = (controller._state_key(), controller._project_generation - 1)
        with patch.object(controller, "_start_project_run") as start:
            controller._execute_reviewed_rename(sample_plan())
        start.assert_not_called()

    def test_copy_download_link_ignores_installed_version_and_update_cache(self) -> None:
        controller = self.controller()
        self.addCleanup(controller.close)
        controller._ready_update = object()
        controller._ready_update_package = Path("old-update.exe")
        clipboard = Mock()
        notices = []
        controller.notificationRequested.connect(lambda *args: notices.append(args))
        with patch("hr_toolkit.gui_qt.controller.threading.Thread") as thread, \
             patch("hr_toolkit.gui_qt.controller.latest_installer_download", return_value=("0.9.11", "https://latest.example/setup.exe")) as lookup, \
             patch("hr_toolkit.gui_qt.controller.__version__", "0.8.1"), \
             patch("hr_toolkit.gui_qt.controller.QGuiApplication") as gui:
            gui.clipboard.return_value = clipboard
            controller.copyLatestDownloadUrl("win7")
            self.assertTrue(controller.downloadLinkBusy)
            controller.copyLatestDownloadUrl("windows")
            self.assertEqual(thread.call_count, 1)
            thread.call_args.kwargs["target"]()
            lookup.assert_called_once_with("win7")
            clipboard.setText.assert_called_once_with("https://latest.example/setup.exe")
            self.assertFalse(controller.downloadLinkBusy)
            self.assertIn("Windows 7", notices[-1][1])
            controller.copyLatestDownloadUrl("windows")
            thread.call_args.kwargs["target"]()
            self.assertEqual(lookup.call_count, 2)
            lookup.assert_called_with("windows")
            self.assertIn("Windows 10 / 11", notices[-1][1])

    def test_copy_download_link_failure_or_close_preserves_clipboard(self) -> None:
        controller = self.controller()
        self.addCleanup(controller.close)
        with patch("hr_toolkit.gui_qt.controller.threading.Thread") as thread, \
             patch("hr_toolkit.gui_qt.controller.latest_installer_download", side_effect=RuntimeError("网络不可用")), \
             patch("hr_toolkit.gui_qt.controller.QGuiApplication") as gui:
            controller.copyLatestDownloadUrl("windows")
            thread.call_args.kwargs["target"]()
            self.assertFalse(controller.downloadLinkBusy)
            gui.clipboard.assert_not_called()
            controller.close()
            controller._apply_download_link("windows", ("0.9.11", "https://latest.example/setup.exe"), "")
            gui.clipboard.assert_not_called()

    def test_sheet_choices_persist_names_but_not_this_file_absences(self) -> None:
        controller = self.controller()
        self.addCleanup(controller.close)
        controller.selectTool("personnel_change_merge")
        controller._template_issue = {
            "tool": "personnel_change_merge", "kind": "worksheets", "file": "异动.xlsx", "choice_key": "file-key",
            "roles": [{"key": "增员"}, {"key": "减员"}],
            "sheet_requests": [{"key": "增员", "label": "增员", "optional": True}, {"key": "减员", "label": "减员", "optional": True}],
            "sheets": [{"name": "1", "rows": [["姓名"]]}],
        }
        controller._template_issue_project = str(controller._project_path)
        controller._template_input_snapshot = controller._template_current_inputs()
        controller._save_workspace_preferences = Mock(return_value=True)
        with patch("hr_toolkit.gui_qt.controller.QTimer.singleShot"):
            controller.saveTemplateChoice(json.dumps({"sheet_selections": {"增员": "1", "减员": None}, "remember": True}))
        saved = controller._header_name_rules["personnel_change_merge"]
        self.assertNotIn("sheet_choices", saved)
        self.assertIn("1", saved["sheets"]["增员"])
        self.assertIsNone(controller._template_session_rules["sheet_choices"]["file-key"]["减员"])

    def test_salary_sheet_rule_deletion_invalidates_related_profiles_and_rolls_back(self) -> None:
        controller = self.controller()
        self.addCleanup(controller.close)
        controller._header_name_rules["salary_merge"] = {"fields": {}, "sheets": {"detail": ["明细", "1"]}}
        controller._salary_header_profiles = {"project": {"detail-key": {"role": "detail", "sheet": "1"},
                                                         "summary-key": {"role": "summary", "sheet": "汇总"}}}
        before = json.loads(json.dumps(controller._salary_header_profiles))
        controller._save_workspace_preferences = Mock(return_value=False)
        with self.assertRaises(ValueError):
            controller._persist_salary_name_rules({"fields": {}, "sheets": {}})
        self.assertEqual(controller._salary_header_profiles, before)
        self.assertIn("1", controller._header_name_rules["salary_merge"]["sheets"]["detail"])
        controller._save_workspace_preferences.return_value = True
        controller._persist_salary_name_rules({"fields": {}, "sheets": {}})
        self.assertEqual(set(controller._salary_header_profiles["project"]), {"summary-key"})

    def test_template_choice_defaults_to_current_run_and_manual_start_clears_it(self) -> None:
        controller = self.controller()
        self.addCleanup(controller.close)
        choice = _prepare_template_choice(controller)
        controller._save_workspace_preferences = Mock(return_value=True)
        with patch("hr_toolkit.gui_qt.controller.QTimer.singleShot"):
            controller.saveTemplateChoice(json.dumps(choice))
        controller._save_workspace_preferences.assert_not_called()
        self.assertNotIn("data_statistics", controller._header_name_rules)
        self.assertEqual(controller._template_session_rules["profiles"][0]["columns"], {"姓名": 1})
        self.assertEqual(controller._template_session_snapshot, controller._template_current_inputs())
        # More prompts in the same continuation keep earlier one-time choices.
        _prepare_template_choice(controller)
        controller._template_issue["sheets"][0]["rows"][0][0] = "333"
        with patch("hr_toolkit.gui_qt.controller.QTimer.singleShot"):
            controller.saveTemplateChoice(json.dumps(choice))
        self.assertEqual(len(controller._template_session_rules["profiles"]), 2)
        continuing = []
        with patch.object(controller, "runOrCancel", side_effect=lambda: continuing.append(controller._template_continuing)):
            controller._continue_template_run()
        self.assertEqual(continuing, [True])
        self.assertFalse(controller._template_continuing)
        controller._project_store = Mock(writable=True)
        with patch.object(controller, "_prepare_invocation") as prepare:
            controller.runOrCancel()
            prepare.assert_called_once()
        self.assertIsNone(controller._template_session_rules)
        self.assertEqual(controller._template_session_snapshot, "")

    def test_remembered_template_choice_can_be_edited_and_deleted_with_save_rollback(self) -> None:
        controller = self.controller()
        self.addCleanup(controller.close)
        choice = _prepare_template_choice(controller)
        controller._save_workspace_preferences = Mock(return_value=True)
        with patch("hr_toolkit.gui_qt.controller.QTimer.singleShot"):
            controller.saveTemplateChoice(json.dumps({**choice, "remember": True}))
        controller.reviewTemplateRules()
        saved = controller.templateSavedProfiles[0]
        self.assertIn("姓名 ← 222", saved["description"])
        controller.editTemplateProfile(saved["key"])
        with patch("hr_toolkit.gui_qt.controller.QTimer.singleShot") as schedule:
            controller.saveTemplateChoice(json.dumps({**choice, "columns": {"姓名": 2}}))
        schedule.assert_not_called()  # Editing settings must not start processing.
        self.assertIn("姓名 ← 名字", controller.templateSavedProfiles[0]["description"])
        self.assertIsNone(controller._template_session_rules)
        controller._save_workspace_preferences.return_value = False
        self.assertFalse(controller.deleteTemplateProfile(saved["key"]))
        self.assertEqual(len(controller.templateSavedProfiles), 1)
        controller._save_workspace_preferences.return_value = True
        self.assertTrue(controller.deleteTemplateProfile(saved["key"]))
        self.assertEqual(controller.templateSavedProfiles, [])

    def test_legacy_template_choice_stays_visible_and_can_be_removed(self) -> None:
        from hr_toolkit.common.template_mapping import save_choice
        controller = self.controller()
        self.addCleanup(controller.close)
        choice = _prepare_template_choice(controller)
        rules = save_choice("data_statistics", {}, controller._template_issue, choice)
        profile = rules["profiles"][0]
        for key in ("headers", "file", "required", "one_of"):
            profile.pop(key, None)
        controller._header_name_rules["data_statistics"] = rules
        controller._save_workspace_preferences = Mock(return_value=True)
        controller.reviewTemplateRules()
        self.assertFalse(controller.templateSavedProfiles[0]["editable"])
        self.assertIn("姓名 ← 第 1 列", controller.templateSavedProfiles[0]["description"])
        self.assertTrue(controller.deleteTemplateProfile(profile["key"]))
        self.assertEqual(controller._header_name_rules["data_statistics"]["profiles"], [])

    def test_update_byte_progress_does_not_refresh_tool_or_result_state(self) -> None:
        controller = self.controller()
        self.addCleanup(controller.close)
        events = []
        controller.updateProgressChanged.connect(lambda: events.append("progress"))
        controller.updateChanged.connect(lambda: events.append("state"))
        controller.selectionStateChanged.connect(lambda: events.append("selection"))
        controller.lastResultChanged.connect(lambda: events.append("result"))
        controller._update_busy = True
        controller._apply_update_phase("downloading")
        self.assertIn("progress", events)
        self.assertIn("selection", events)
        self.assertTrue(controller.updateBlocksTools)
        events.clear()
        controller._apply_update_progress(25, 100)
        self.assertEqual(events, ["progress"])
        self.assertEqual(controller.updateProgress, 0.25)
        self.assertTrue(controller.updateBlocksTools)
        controller._apply_update_progress(25, 100)
        self.assertEqual(events, ["progress"])
        controller._apply_update_progress(100, 100)
        self.assertEqual(controller.updateProgress, 1.0)
        events.clear()
        controller._apply_update_phase("verifying")
        self.assertIn("progress", events)
        self.assertIn("state", events)
        self.assertEqual(controller.updateProgress, -1.0)
        self.assertTrue(controller.updateBlocksTools)
        events.clear()
        controller._apply_update_progress(50, 100)
        self.assertEqual(events, [])
        controller._apply_update_result("download-cancelled", None)
        self.assertFalse(controller.updateBlocksTools)
        self.assertIn("selection", events)
        self.assertIn("progress", events)

    def test_notice_classification_is_conservative_and_filters_preserve_all_rows(self) -> None:
        category = AppController._notice_category
        info = "OCR 智能索引缓存：命中 12 次，实时识别 3 次，缓存文件：/tmp/cache.json"
        self.assertEqual(category("material_collector", info), "运行信息")
        self.assertEqual(category("material_collector", "OCR 缓存写入失败：只读"), "运行提醒")
        self.assertEqual(category("material_collector", "照片人员归属冲突，未提取：a.jpg"), "业务核对")
        self.assertEqual(category("material_collector", info + "\n但是识别失败"), "其他提醒")
        self.assertEqual(category("salary_merge", info), "其他提醒")
        controller = self.controller()
        self.addCleanup(controller.close)
        controller.selectTool("material_collector")
        messages = [info, "OCR 缓存写入失败：只读", "照片人员归属冲突，未提取：a.jpg", "未知提醒"]
        controller.refreshWorkspace = lambda: None
        controller._apply_run_success({"warnings": messages}, tempfile.gettempdir(), 1, False)
        controller.setResultNoticeFilter("运行信息")
        self.assertEqual(controller.resultNoticeCount, 4)
        self.assertEqual(controller.resultNoticeModel.rowCount(), 1)
        self.assertEqual([row["text"] for row in controller._result_notice_rows], messages)
        controller.setResultNoticeFilter("全部")
        self.assertEqual([row["text"] for row in controller.resultNoticeModel.items()], messages)

    def test_date_editing_normalizes_valid_text_without_replacing_invalid_text(self) -> None:
        controller = self.controller()
        self.addCleanup(controller.close)
        controller.selectTool("data_statistics")
        controller.setFieldValue("week_start", "20260915")
        controller.normalizeDateField("week_start", "20260915")
        self.assertEqual(controller._form_states[controller._state_key()]["week_start"], "2026-09-15")
        controller.setFieldValue("week_start", "20260230")
        controller.normalizeDateField("week_start", "20260230")
        self.assertEqual(controller._form_states[controller._state_key()]["week_start"], "20260230")
        self.assertTrue(controller.selectionFeedback["week_range"]["error"])

    def test_notice_filter_reuse_never_keeps_rows_from_previous_result(self) -> None:
        controller = self.controller()
        self.addCleanup(controller.close)
        controller.selectTool("material_collector")
        controller.refreshWorkspace = lambda: None
        old = ["OCR 缓存写入失败：旧文件", "照片人员归属冲突，未提取：a.jpg"]
        controller._apply_run_success({"warnings": old}, tempfile.gettempdir(), 1, False)
        controller.setResultNoticeFilter("运行提醒")
        resets = []
        controller.resultNoticeModel.modelReset.connect(lambda: resets.append(True))
        controller.setResultNoticeFilter("运行提醒")
        self.assertEqual(resets, [])
        controller.setResultNoticeFilter("全部")
        self.assertEqual([row["text"] for row in controller.resultNoticeModel.items()], old)
        controller.setResultNoticeFilter("运行提醒")
        self.assertEqual(controller.resultNoticeModel.item_at(0)["text"], old[0])

        new = ["OCR 缓存写入失败：新文件"]
        controller._apply_run_success({"warnings": new}, tempfile.gettempdir(), 1, False)
        controller.setResultNoticeFilter("运行提醒")
        self.assertEqual([row["text"] for row in controller.resultNoticeModel.items()], new)
        controller._apply_run_success({"warnings": []}, tempfile.gettempdir(), 1, False)
        controller.setResultNoticeFilter("运行提醒")
        self.assertEqual(controller.resultNoticeModel.items(), [])

    def test_unchanged_preferences_skip_write_but_changed_save_reports_errors(self) -> None:
        controller = self.controller()
        self.addCleanup(controller.close)
        with tempfile.TemporaryDirectory() as tmp:
            settings = Path(tmp) / "workspace-ui.json"
            with patch.object(controller, "_settings_path", return_value=settings):
                self.assertTrue(AppController._save_workspace_preferences(controller))
                saved = json.loads(settings.read_text(encoding="utf-8"))
                saved["external_field"] = {"keep": 42}
                settings.write_text(json.dumps(saved), encoding="utf-8")
                with patch("hr_toolkit.gui_qt.controller.os.replace", wraps=os.replace) as replace:
                    self.assertTrue(AppController._save_workspace_preferences(controller))
                    replace.assert_not_called()
                    controller._release_notes_seen_version = "999.1"
                    self.assertTrue(AppController._save_workspace_preferences(controller))
                    replace.assert_called_once()
                saved = json.loads(settings.read_text(encoding="utf-8"))
                self.assertEqual(saved["external_field"], {"keep": 42})
                self.assertEqual(saved["release_notes_seen_version"], "999.1")
                controller._release_notes_seen_version = "999.2"
                with patch("hr_toolkit.gui_qt.controller.os.replace", side_effect=OSError("read only")), patch("hr_toolkit.gui_qt.controller.runlog.log_exception"):
                    self.assertFalse(AppController._save_workspace_preferences(controller))
                self.assertEqual(json.loads(settings.read_text(encoding="utf-8")), saved)

    def test_selecting_preset_name_does_not_apply_it(self) -> None:
        controller = self.controller()
        self.addCleanup(controller.close)
        controller.selectTool("material_collector")
        before = dict(controller._form_states[controller._state_key()])
        name = controller.materialPresets[0]
        self.assertFalse(controller.isCustomMaterialPreset(name))
        controller.setMaterialPresetName(name)
        self.assertEqual(controller._form_states[controller._state_key()], before)

    def test_waiting_hint_follows_the_attachment_kind(self) -> None:
        """等待首个字的提示按这一轮实际发出的附件走，不是一串写死的话。"""
        controller = self.controller()
        self.addCleanup(controller.close)

        controller._ai_attach_status_phrases([{"kind": "image"}])
        joined = "".join(controller.aiStatusPhrases)
        self.assertIn("图", joined)
        self.assertNotIn("表格", joined, "发了图却提示正在读取表格")

        controller._ai_attach_status_phrases([{"kind": "sheet"}])
        joined = "".join(controller.aiStatusPhrases)
        self.assertNotIn("图", joined, "只发了表格却提示在看图")
        self.assertTrue(any(marker in joined for marker in ("表格", "表头", "数据")))

        controller._ai_attach_status_phrases([{"kind": "image"}, {"kind": "sheet"}])
        self.assertIn("图", "".join(controller.aiStatusPhrases))

        controller._ai_attach_status_phrases([])
        joined = "".join(controller.aiStatusPhrases)
        self.assertNotIn("表格", joined)
        self.assertNotIn("图", joined)

        # 连着几轮不该是同一套措辞（否则等于还是死文案）。
        rounds = []
        for _ in range(5):
            controller._ai_attach_status_phrases([{"kind": "sheet"}])
            rounds.append(tuple(controller.aiStatusPhrases))
        self.assertGreater(len(set(rounds)), 1)

    def test_waiting_hint_signals_a_change_each_turn(self) -> None:
        controller = self.controller()
        self.addCleanup(controller.close)
        seen = []
        controller.aiStatusChanged.connect(lambda: seen.append(controller.aiStatusPhrases))
        controller._ai_attach_status_phrases([{"kind": "image"}])
        controller._ai_attach_status_phrases([{"kind": "image"}])
        self.assertEqual(len(seen), 2)
        self.assertTrue(all(phrases for phrases in seen))

    def _isolated_controller(self, folder):
        """AI 设置落到临时文件，别动用户真实的 ai-assistant.json。"""
        path = Path(folder) / "ai-assistant.json"
        patcher = patch("hr_toolkit.ai.config.default_settings_path", return_value=path)
        patcher.start()
        self.addCleanup(patcher.stop)
        controller = self.controller()
        self.addCleanup(controller.close)
        return controller

    def test_switching_provider_keeps_each_providers_own_settings(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            controller = self._isolated_controller(folder)

            self.assertTrue(controller.aiSaveSettings("minimax", "sk-minimax-key-1234", "MiniMax-M3", ""))
            self.assertTrue(controller.aiAddModel("我的自建模型"))
            self.assertEqual(controller.aiActiveProvider, "minimax")

            # 切到 DeepSeek：改用 DeepSeek 自己的 Key 与模型。
            self.assertTrue(controller.aiSelectProvider("deepseek"))
            self.assertEqual(controller.aiActiveProvider, "deepseek")
            self.assertEqual(controller.aiActiveModel, "deepseek-flash")
            self.assertEqual(controller.aiApiKeyFor("deepseek"), "")
            names = [row["value"] for row in controller.aiModelOptions]
            self.assertNotIn("我的自建模型", names, "串到了别家的模型列表")

            # 在 DeepSeek 里换个模型
            self.assertTrue(controller.aiSelectModel("deepseek-v4-pro"))

            # MiniMax 那边的 Key 与自建模型原样还在（切换不是「覆盖」）。
            self.assertEqual(controller.aiApiKeyFor("minimax"), "sk-minimax-key-1234")
            self.assertIn("我的自建模型", controller.aiModelChoicesFor("minimax"))

            # 切回 MiniMax：停在离开时那个模型（自建模型加完就切过去了）。
            self.assertTrue(controller.aiSelectProvider("minimax"))
            self.assertEqual(controller.aiActiveModel, "我的自建模型")
            self.assertIn("我的自建模型", [row["value"] for row in controller.aiModelOptions])

            # 再回 DeepSeek：刚才换的 reasoner 也还在。
            self.assertTrue(controller.aiSelectProvider("deepseek"))
            self.assertEqual(controller.aiActiveModel, "deepseek-v4-pro")

            # 未知服务商不能把配置改坏。
            self.assertFalse(controller.aiSelectProvider("not-a-provider"))
            self.assertEqual(controller.aiActiveProvider, "deepseek")

    def test_provider_menu_marks_the_active_provider(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            controller = self._isolated_controller(folder)
            values = [row["value"] for row in controller.aiProviderMenuOptions]
            self.assertEqual(values, ["deepseek", "minimax", "glm", "qwen"])

            def selected():
                return [row["value"] for row in controller.aiProviderMenuOptions if row["selected"]]

            self.assertEqual(selected(), ["minimax"])
            self.assertTrue(controller.aiSelectProvider("glm"))
            self.assertEqual(selected(), ["glm"])
            # 标签要能翻译（设置里的下拉框和面板菜单都靠它显示）。
            labels = {row["value"]: row["label"] for row in controller.aiProviderMenuOptions}
            self.assertEqual(labels["glm"], "智谱 GLM")
            self.assertEqual(labels["qwen"], "通义千问")

    def test_model_choices_are_per_provider(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            controller = self._isolated_controller(folder)
            self.assertIn("MiniMax-M3", controller.aiModelChoicesFor("minimax"))
            self.assertIn("glm-5.3", controller.aiModelChoicesFor("glm"))
            self.assertIn("qwen3.7-plus", controller.aiModelChoicesFor("qwen"))
            self.assertIn("deepseek-flash", controller.aiModelChoicesFor("deepseek"))
            self.assertNotIn("MiniMax-M3", controller.aiModelChoicesFor("glm"))
            self.assertNotIn("glm-4.6", controller.aiModelChoicesFor("qwen"))
            self.assertEqual(controller.aiModelChoicesFor("not-a-provider"), [])
            # 「添加模型」输入框的示例跟着服务商走。
            self.assertEqual(controller.aiProviderDefaultModel, "MiniMax-M3")
            controller.aiSelectProvider("glm")
            self.assertEqual(controller.aiProviderDefaultModel, "glm-5.3")

    def test_workspace_transfer_captures_path_and_rejects_changed_context(self) -> None:
        controller = self.controller()
        self.addCleanup(controller.close)
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            source = root / "共用资料" / "中文 名单#100%.xlsx"
            source.parent.mkdir()
            source.touch()
            controller._project_path = root
            controller._workspace_items = [{"path": str(source), "name": source.name, "isDir": False}]
            with patch.object(Path, "stat", side_effect=AssertionError("capture must not stat")):
                transfer = controller.beginWorkspaceTransfer(str(source))
                self.assertTrue(transfer["token"])
            with patch("hr_toolkit.gui_qt.controller.threading.Thread"):
                preview = controller.beginDropPreview("support", [transfer["url"]], transfer["token"])
                controller._workspace_items.clear()  # Delegate/row recycling cannot change source identity.
                controller._check_drop_previews()
                self.assertTrue(controller._drop_preview_request["accepted"])
                controller._project_generation += 1
                self.assertFalse(controller.finishDropPreview(preview["token"], "support", [transfer["url"]]))
                self.assertFalse(controller.beginDropPreview("support", [transfer["url"]], transfer["token"])["accepted"])
                self.assertFalse(controller.selectionChecking)
            self.assertTrue(source.exists())

    def test_workspace_click_import_uses_shared_policy_and_never_moves_source(self) -> None:
        controller = self.controller()
        self.addCleanup(controller.close)
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            source = root / "共用资料" / "名单.xlsx"
            source.parent.mkdir()
            source.touch()
            controller._project_path = root
            controller._workspace_items = [{"path": str(source), "name": source.name, "isDir": False}]
            controller.selectWorkspaceRow(0)
            self.assertTrue(controller.canUseWorkspaceSelection("support"))
            with patch("hr_toolkit.gui_qt.controller.threading.Thread") as worker:
                controller.useWorkspaceSelection("support")
                worker.call_args.kwargs["target"]()
            self.assertEqual(controller.supportPath, str(source))
            self.assertEqual(controller._input_states[controller._state_key()], [])
            self.assertTrue(source.exists())
            controller._workspace_items = [{"path": str(source.parent), "isDir": True}]
            self.assertEqual(controller.beginWorkspaceTransfer(str(source.parent)), {})
            controller._workspace_items = [{"path": str(root / ".hrtoolkit" / "trash.xlsx"), "isDir": False}]
            self.assertEqual(controller.beginWorkspaceTransfer(controller._workspace_items[0]["path"]), {})

    def test_workspace_worker_rejects_missing_or_escaped_source(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / "project"
            root.mkdir()
            outside = Path(temp) / "outside.xlsx"
            outside.touch()
            with self.assertRaises(ValueError):
                AppController._validate_workspace_source({"root": root, "path": outside})
            with self.assertRaises(OSError):
                AppController._validate_workspace_source({"root": root, "path": root / "资料" / "gone.xlsx"})

    def test_result_links_use_only_declared_outputs_and_reminders_keep_all_rows(self) -> None:
        controller = self.controller()
        self.addCleanup(controller.close)
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            report = root / "报表.xlsx"
            payload = {"output_file": str(report), "input_path": str(root / "input.xlsx"),
                       "warnings": ["运行信息 %d" % index for index in range(40)]}
            controller.refreshWorkspace = lambda: None
            controller._apply_run_success(payload, str(root), 1.0, False)
            # Social security has no generic output_file contract.
            self.assertFalse(controller.canOpenPrimaryResult)
            self.assertEqual(controller.resultNoticeCount, 40)
            self.assertEqual(AppController._result_output_paths("salary_merge", payload, root), [report])
            self.assertEqual(AppController._result_output_paths("salary_merge", {"output_file": str(root / ".." / "old.xlsx")}, root), [])
            multiple = {"output_files": [str(report), str(root / "另一份.xlsx")]}
            self.assertEqual(len(AppController._result_output_paths("archive_export", multiple, root)), 2)
            controller.selectTool("salary_split")
            self.assertFalse(controller.canOpenLastResult)
            self.assertEqual(controller.resultNoticeCount, 0)

    def test_generic_phase_and_stop_feedback_use_existing_callbacks(self) -> None:
        controller = self.controller()
        self.addCleanup(controller.close)
        controller._run_coordinator.cancel = Mock()
        controller._set_busy(True)
        controller._apply_run_progress(2, 8, "读取资料")
        self.assertEqual(controller.runProgressMessage, "读取资料")
        self.assertEqual(controller.runProgressTotal, 8)
        controller.runOrCancel()
        controller.runOrCancel()
        controller._run_coordinator.cancel.assert_called_once()
        self.assertEqual(controller.runButtonText, "正在安全停止…")
        controller._apply_run_progress(3, 8, "迟到的进度")
        self.assertIn("停止", controller.runProgressMessage)
        controller._set_busy(False)

    def test_drop_preview_uses_local_urls_without_disk_access(self) -> None:
        from hr_toolkit.gui_qt.compat import QUrl
        controller = self.controller()
        self.addCleanup(controller.close)
        path = Path(tempfile.gettempdir()) / "员工 名册#100%.xlsx"
        url = QUrl.fromLocalFile(str(path)).toString()
        with patch.object(Path, "stat", side_effect=AssertionError("drag hover must not stat")):
            self.assertTrue(controller.describeDrop("support", [url])["accepted"])
            self.assertEqual(controller._local_drop_paths([url]), [path])
            self.assertFalse(controller.describeDrop("support", [url, url])["accepted"])
            self.assertFalse(controller.describeDrop("input", ["https://example.com/a.xlsx"])["accepted"])
            self.assertFalse(controller.describeDrop("input", ["文字"])["accepted"])
            self.assertFalse(controller.describeDrop("support", [QUrl.fromLocalFile(str(path.with_suffix(".exe"))).toString()])["accepted"])

    def test_windows_drop_paths_preserve_local_characters_and_shares(self) -> None:
        from hr_toolkit.gui_qt.drop_paths import local_drop_paths, native_mime_paths
        from hr_toolkit.gui_qt.compat import QUrl
        from types import SimpleNamespace
        paths = ["C:\\Users\\甲方\\Desktop\\表 #100%.xlsx", "\\\\server\\share\\工资.xlsx"]
        self.assertEqual([str(p) for p in local_drop_paths(paths, windows=True)], paths)
        url = QUrl.fromLocalFile("C:/Users/甲方/Desktop/表 #100%.xlsx").toString()
        # Path 的字符串形式随平台变化（Windows 用反斜杠），这里只关心 #、% 与中文是否原样保留。
        self.assertEqual(local_drop_paths([url], windows=True)[0].as_posix(),
                         "C:/Users/甲方/Desktop/表 #100%.xlsx")
        key = 'application/x-qt-windows-mime;value="FileNameW"'
        mime = SimpleNamespace(urls=lambda: [], formats=lambda: [key],
                               data=lambda _: (paths[0] + "\x00").encode("utf-16-le"))
        self.assertEqual(native_mime_paths(mime), paths[:1])
        for invalid in ("https://example.com/a.xlsx", "C:relative.xlsx", "C:\\Desktop\\快捷方式.lnk"):
            with self.assertRaises(ValueError):
                local_drop_paths([invalid], windows=True)

    def test_drop_can_finish_while_hover_validation_is_pending(self) -> None:
        from hr_toolkit.gui_qt.compat import QUrl
        controller = self.controller()
        self.addCleanup(controller.close)
        url = QUrl.fromLocalFile(str(Path(tempfile.gettempdir()) / "工资.xlsx")).toString()
        with patch("threading.Thread.start"), patch.object(controller, "_submit_selection") as submit:
            preview = controller.beginDropPreview("input", [url])
            self.assertTrue(preview["pending"])
            controller.finishDropPreview(preview["token"], "input", [url])
            submit.assert_called_once()

    def test_hover_type_error_is_reported_before_drop_without_changing_selection(self) -> None:
        from hr_toolkit.gui_qt.compat import QUrl
        controller = self.controller()
        self.addCleanup(controller.close)
        previews = []
        controller.dropPreviewReady.connect(previews.append)
        with tempfile.TemporaryDirectory() as temp:
            exe = Path(temp) / "安装程序.exe"
            exe.touch()
            urls = [QUrl.fromLocalFile(str(exe)).toString()]
            with patch("hr_toolkit.gui_qt.controller.threading.Thread"):
                initial = controller.beginDropPreview("input", urls)
                self.assertTrue(initial["pending"])
                self.assertFalse(initial["accepted"])
                controller._check_drop_previews()
                self.assertFalse(previews[-1]["accepted"])
                self.assertIn("安装程序.exe", previews[-1]["message"])
                self.assertFalse(controller.finishDropPreview(initial["token"], "input", urls))
                self.assertFalse(controller.selectionChecking)
                self.assertEqual(controller.selectionFeedback, {})
                self.assertEqual(controller._input_states[controller._state_key()], [])

    def test_hover_checks_actual_folder_type_and_requires_matching_preview(self) -> None:
        from hr_toolkit.gui_qt.compat import QUrl
        controller = self.controller()
        self.addCleanup(controller.close)
        previews = []
        controller.dropPreviewReady.connect(previews.append)
        with tempfile.TemporaryDirectory() as temp:
            folder = Path(temp) / "资料.exe"
            folder.mkdir()
            urls = [QUrl.fromLocalFile(str(folder)).toString()]
            with patch("hr_toolkit.gui_qt.controller.threading.Thread"):
                initial = controller.beginDropPreview("input", urls)
                self.assertTrue(initial["pending"])
                # 悬停校验尚未完成时也允许松手（见 test_drop_can_finish_while_hover_validation_is_pending），
                # 但角色或路径对不上的一律拒绝。
                self.assertFalse(controller.finishDropPreview(initial["token"], "support", urls))
                self.assertFalse(controller.finishDropPreview(initial["token"], "input", []))
                controller._check_drop_previews()
                self.assertTrue(previews[-1]["accepted"])
                self.assertTrue(controller.finishDropPreview(initial["token"], "input", urls))
                self.assertTrue(controller.selectionChecking)

    def test_hover_uses_one_worker_and_ignores_exited_target_results(self) -> None:
        from hr_toolkit.gui_qt.compat import QUrl
        controller = self.controller()
        self.addCleanup(controller.close)
        previews = []
        controller.dropPreviewReady.connect(previews.append)
        urls = [QUrl.fromLocalFile(str(Path(tempfile.gettempdir()) / "名单.xlsx")).toString()]
        with patch("hr_toolkit.gui_qt.controller.threading.Thread") as worker:
            controller.beginDropPreview("input", urls)
            old = controller._drop_preview_request
            current = controller.beginDropPreview("support", urls)
            self.assertEqual(worker.return_value.start.call_count, 1)
            self.assertTrue(old["cancel"].is_set())
            previews.clear()
            controller._apply_drop_preview(old, "过期错误")
            self.assertEqual(previews, [])
            controller.cancelDropPreview(current["token"])
            self.assertIsNone(controller._drop_preview_pending)
            self.assertFalse(controller.finishDropPreview(current["token"], "support", urls))

    def test_recent_selection_history_is_bounded_filtered_and_metadata_only(self) -> None:
        controller = self.controller()
        self.addCleanup(controller.close)
        root = Path(tempfile.gettempdir()) / "recent-test"
        items = [{"path": str(root / (str(i) + ".xlsx")), "kind": "file"} for i in range(25)]
        items += [{"path": str(root / str(i)), "kind": "folder"} for i in range(15)]
        with patch.object(Path, "stat", side_effect=AssertionError("history must not touch disk")):
            controller._recent_selections[controller._spec.nav_id] = controller._bounded_recent_selections(
                [None, {"path": "relative.xlsx", "kind": "file"}] + items + items[:2])
            self.assertEqual(len(controller.recentSelectionItems("input", "file")), 20)
            self.assertEqual(len(controller.recentSelectionItems("input", "folder")), 10)
            self.assertEqual(controller.recentSelectionItems("support", "file")[0]["path"], items[0]["path"])
            controller._tool_recent_selections().insert(0, {"path": str(root / "batch.tar.gz"), "kind": "file"})
            self.assertEqual(len(controller.recentSelectionItems("input", "file")), 21)
            self.assertEqual(len(controller.recentSelectionItems("support", "file")), 20)
            controller.removeRecentSelection(items[0]["path"], "file")
            self.assertNotIn(items[0], controller._tool_recent_selections())
            controller.clearRecentSelections()
            self.assertEqual(controller._tool_recent_selections(), [])

    def test_recent_file_reuses_validation_and_never_starts_processing(self) -> None:
        controller = self.controller()
        self.addCleanup(controller.close)
        with tempfile.TemporaryDirectory() as temp:
            source = Path(temp) / "名单.xlsx"
            source.touch()
            controller._recent_selections[controller._spec.nav_id] = [{"path": str(source), "kind": "file"}]
            with patch("hr_toolkit.gui_qt.controller.threading.Thread") as worker, \
                 patch.object(controller, "runOrCancel") as run:
                controller.useRecentSelection("support", str(source), "file", False)
                worker.call_args.kwargs["target"]()
                self.assertEqual(controller.supportPath, str(source))
                self.assertEqual(controller._last_selected_dir, source.parent)
                self.assertEqual(controller._tool_recent_selections(), [{"path": str(source), "kind": "file"}])
                source.unlink()
                controller.useRecentSelection("support", str(source), "file", False)
                worker.call_args.kwargs["target"]()
                self.assertEqual(controller.supportPath, str(source))
                self.assertTrue(controller.selectionFeedback["support"]["error"])
                run.assert_not_called()

    def test_recent_folder_opens_existing_picker_and_cancel_preserves_selection(self) -> None:
        controller = self.controller()
        self.addCleanup(controller.close)
        with tempfile.TemporaryDirectory() as temp:
            controller._recent_selections[controller._spec.nav_id] = [{"path": temp, "kind": "folder"}]
            with patch("hr_toolkit.gui_qt.controller.threading.Thread") as worker, \
                 patch.object(controller.presentation, "file_dialog", return_value=([], "")) as picker, \
                 patch.object(controller, "runOrCancel") as run:
                controller.useRecentSelection("input", temp, "browse_files", True)
                worker.call_args.kwargs["target"]()
                self.assertEqual(picker.call_args.args[3], temp)
                self.assertEqual(controller._input_states[controller._state_key()], [])
                self.assertEqual(controller._tool_recent_selections(), [{"path": temp, "kind": "folder"}])
                run.assert_not_called()
                picker.reset_mock()
                controller.useRecentSelection("input", temp, "browse_files", True)
                controller.cancelSelectionCheck()
                worker.call_args.kwargs["target"]()
                picker.assert_not_called()

    def test_recent_histories_are_isolated_and_cleared_per_tool(self) -> None:
        controller = self.controller()
        self.addCleanup(controller.close)
        path = str(Path(tempfile.gettempdir()) / "records.xlsx")
        entry = {"path": path, "kind": "file"}
        controller._recent_selections["social_security"] = [entry]
        controller.selectTool("data_statistics")
        self.assertEqual(controller.recentSelectionItems("input", "file"), [])
        with patch.object(controller, "_submit_selection") as submit:
            controller.useRecentSelection("input", path, "file", False)
            submit.assert_not_called()
        controller._recent_selections["data_statistics"] = [entry]
        controller.clearRecentSelections()
        controller.selectTool("social_security")
        self.assertEqual(controller._tool_recent_selections(), [entry])
        controller.removeRecentSelection(path, "file")
        self.assertEqual(controller._tool_recent_selections(), [])

    def test_recent_history_records_selected_folders_and_archives_only(self) -> None:
        controller = self.controller()
        self.addCleanup(controller.close)
        with tempfile.TemporaryDirectory() as temp:
            folder = Path(temp) / "uploads"
            folder.mkdir()
            archive = folder / "records.zip"
            archive.touch()
            with patch("hr_toolkit.gui_qt.controller.threading.Thread") as worker:
                controller._submit_selection("input", [archive], replace=True)
                worker.call_args.kwargs["target"]()
                self.assertEqual(controller._tool_recent_selections(), [{"path": str(archive), "kind": "file"}])
                controller._submit_selection("input", [folder], replace=True)
                worker.call_args.kwargs["target"]()
                self.assertEqual(controller._tool_recent_selections(), [
                    {"path": str(folder), "kind": "folder"}, {"path": str(archive), "kind": "file"}])

    def test_recent_open_actions_do_not_select_or_process_items(self) -> None:
        controller = self.controller()
        self.addCleanup(controller.close)
        with tempfile.TemporaryDirectory() as temp:
            source = Path(temp) / "records.xlsx"
            source.touch()
            entries = [{"path": str(source), "kind": "file"}, {"path": temp, "kind": "folder"}]
            controller._recent_selections[controller._spec.nav_id] = entries.copy()
            with patch("hr_toolkit.gui_qt.controller.threading.Thread") as worker, \
                 patch("hr_toolkit.gui_qt.controller.open_path") as opener, \
                 patch.object(controller, "_submit_selection") as select, \
                 patch.object(controller, "runOrCancel") as run:
                for path, kind, action, expected in ((str(source), "file", "open", source),
                                                   (str(source), "file", "location", source.parent),
                                                   (temp, "folder", "open", Path(temp))):
                    controller.openRecentSelection(path, kind, action)
                    worker.call_args.kwargs["target"]()
                    opener.assert_called_with(expected)
                    self.assertFalse(controller._recent_location_pending)
                source.unlink()
                opener.reset_mock()
                notices = []
                controller.notificationRequested.connect(lambda *args: notices.append(args))
                controller.openRecentSelection(str(source), "file", "open")
                worker.call_args.kwargs["target"]()
                opener.assert_not_called()
                self.assertTrue(notices)
                self.assertFalse(controller._recent_location_pending)
                self.assertEqual(controller._tool_recent_selections(), entries)
                select.assert_not_called()
                run.assert_not_called()

    def test_drop_selection_is_atomic_and_support_does_not_change_inputs(self) -> None:
        controller = self.controller()
        self.addCleanup(controller.close)
        with tempfile.TemporaryDirectory() as temp:
            first, roster = Path(temp) / "缴费.xlsx", Path(temp) / "名单.xlsx"
            first.touch(); roster.touch()
            controller._set_inputs([first], replace=True)
            with patch("hr_toolkit.gui_qt.controller.threading.Thread"):
                controller._submit_selection("support", [roster], replace=True)
                request = controller._selection_request
                controller._apply_selection(request, [roster], "")
                self.assertEqual(controller.supportPath, str(roster))
                self.assertEqual(controller._input_states[controller._state_key()], [first])
                controller._submit_selection("input", [roster], replace=True)
                controller._apply_selection(controller._selection_request, [], "资料无法访问")
                self.assertEqual(controller._input_states[controller._state_key()], [first])
                self.assertTrue(controller.selectionFeedback["input"]["error"])

    def test_pending_selection_blocks_runs_and_discards_stale_or_cancelled_results(self) -> None:
        controller = self.controller()
        self.addCleanup(controller.close)
        source = Path(tempfile.gettempdir()) / "工资.xlsx"
        with patch("hr_toolkit.gui_qt.controller.threading.Thread"):
            controller._submit_selection("input", [source], replace=False)
            request = controller._selection_request
            self.assertTrue(controller.selectionChecking)
            self.assertFalse(controller.selectionEnabled)
            self.assertTrue(controller._block_run_for_update())
            controller.selectTool("salary_merge")
            controller._apply_selection(request, [source], "")
            self.assertEqual(controller._input_states[controller._state_key()], [])
            controller._submit_selection("input", [source], replace=False)
            request = controller._selection_request
            controller.cancelSelectionCheck()
            controller._apply_selection(request, [source], "")
            self.assertEqual(controller._input_states[controller._state_key()], [])
            self.assertFalse(controller.selectionChecking)
            controller._update_busy = True
            controller._update_phase = "downloading"
            self.assertFalse(controller.selectionEnabled)
            controller._submit_selection("input", [source], replace=False)
            self.assertIsNone(controller._selection_request)

    def test_attendance_explicit_append_does_not_use_legacy_replace(self) -> None:
        controller = self.controller()
        self.addCleanup(controller.close)
        controller.selectTool("data_statistics")
        filename = str(Path(tempfile.gettempdir()) / "考勤.xlsx")
        with patch.object(controller, "_submit_selection") as submit, \
             patch.object(controller, "_file_dialog_initial_dir", return_value=""), \
             patch.object(controller, "_remember_file_dialog_path"), \
             patch("hr_toolkit.gui_qt.controller.QFileDialog.getOpenFileNames", return_value=([filename], "")):
            controller._dialog_parent = lambda: None
            controller.chooseInputFiles()
            self.assertTrue(submit.call_args.kwargs["replace"])
            controller.appendInputFiles()
            self.assertFalse(submit.call_args.kwargs["replace"])

    def test_background_update_downloads_immediately_but_manual_check_prompts(self) -> None:
        from hr_toolkit.app_update import UpdateInfo
        info = UpdateInfo("9.0.0", "https://gitee.com/setup.exe", "a" * 64, (), True, "https://gitee.com/manifest")
        controller = self.controller()
        prompts = []
        controller.updatePromptRequested.connect(prompts.append)
        with patch.object(controller, "_accept_update") as download:
            controller._apply_update_result("available", info)
            download.assert_called_once_with(info, background=True)
        self.assertEqual(prompts, [])
        controller._update_manual = True
        with patch.object(controller, "_accept_update") as download:
            controller._apply_update_result("available", info)
            download.assert_not_called()
        self.assertEqual(prompts[-1]["version"], "9.0.0")
        controller.close()

    def test_background_download_keeps_origin_and_can_start_alongside_work(self) -> None:
        from hr_toolkit.app_update import UpdateInfo
        controller = self.controller()
        info = UpdateInfo("9.0.0", "https://gitee.com/setup.exe", "a" * 64, (), False, "https://gitee.com/manifest")
        controller._set_busy(True)
        with patch("hr_toolkit.gui_qt.controller.threading.Thread") as thread:
            controller._accept_update(info, background=True)
            thread.return_value.start.assert_called_once()
        self.assertFalse(controller._update_manual)
        self.assertTrue(controller.updateBusy)
        self.assertEqual(controller.updatePhase, "preparing")
        self.assertTrue(controller.busy)
        controller._set_busy(False)
        controller.close()

    def test_download_ready_does_not_install_and_blocks_new_runs_only(self) -> None:
        from hr_toolkit.app_update import UpdateInfo
        controller = self.controller()
        info = UpdateInfo("9.0.0", "https://gitee.com/setup.exe", "a" * 64, (), False, "https://gitee.com/manifest")
        controller._pending_update = info
        controller._update_busy = True
        controller._set_busy(True)
        with patch.object(controller, "_launch_ready_update") as launch:
            controller._apply_update_result("downloaded", Path("cached.exe"))
            launch.assert_not_called()
        self.assertTrue(controller.updateReady)
        self.assertTrue(controller.busy)
        with patch.object(controller._run_coordinator, "cancel") as cancel:
            controller.runOrCancel()
            cancel.assert_called_once()
        controller._set_busy(False)
        with patch.object(controller, "_prepare_invocation") as prepare:
            controller.runOrCancel()
            prepare.assert_not_called()
        with patch.object(controller._run_coordinator, "start") as start:
            controller._start_project_run(None)
            start.assert_not_called()
        with patch.object(controller, "_shutdown_work_running", return_value=True), patch("hr_toolkit.gui_qt.controller.threading.Thread") as thread:
            controller.restartToUpdate()
            thread.assert_not_called()
        with patch("hr_toolkit.gui_qt.controller.launch_update_replacement") as install:
            self.assertTrue(controller.requestClose())
            install.assert_not_called()

    def test_restart_update_shows_installation_window_on_windows_only(self) -> None:
        controller = self.controller()
        self.addCleanup(controller.close)
        for platform, expected in (("win32", True), ("darwin", False)):
            with patch("hr_toolkit.gui_qt.controller.sys.platform", platform):
                with patch.object(controller, "_launch_ready_update") as launch:
                    controller.restartToUpdate()
                    launch.assert_called_once_with(show_ui=expected)

    def test_manual_download_waits_for_restart_click(self) -> None:
        from hr_toolkit.app_update import UpdateInfo
        controller = self.controller()
        controller._update_manual = True
        controller._pending_update = UpdateInfo("9.0.0", "https://gitee.com/setup.exe", "a" * 64, (), False, "https://gitee.com/manifest")
        with patch.object(controller, "_launch_ready_update") as launch:
            controller._apply_update_result("downloaded", Path("cached.exe"))
            launch.assert_not_called()
        self.assertTrue(controller.updateReady)
        controller.close()

    def test_update_download_blocks_tool_entrypoints_until_cancel_or_failure(self) -> None:
        controller = self.controller()
        for phase in ("preparing", "downloading", "verifying", "launching"):
            with self.subTest(phase=phase):
                controller._update_busy = True
                controller._update_phase = phase
                self.assertTrue(controller.updateBlocksTools)
                with patch.object(controller, "_prepare_invocation") as prepare:
                    controller.runOrCancel()
                    prepare.assert_not_called()
                # Inner entry points must also reject calls from existing dialogs.
                controller._prepare_invocation(preview=False)
                controller._start_preview(None)
                with patch.object(controller._run_coordinator, "start") as start:
                    controller._start_project_run(None)
                    start.assert_not_called()
                controller._set_busy(True)
                with patch.object(controller._run_coordinator, "cancel") as cancel:
                    controller.runOrCancel()
                    cancel.assert_called_once()
                controller._set_busy(False)
        controller._update_phase = "checking"
        self.assertFalse(controller.updateBlocksTools)
        for result in ("download-cancelled", "download-error"):
            controller._update_busy = True
            controller._update_phase = "downloading"
            with patch("hr_toolkit.gui_qt.controller.runlog.log_line"):
                controller._apply_update_result(result, "fixture")
            self.assertFalse(controller.updateBlocksTools)
        controller.close()

    def test_no_update_only_prompts_after_manual_check(self) -> None:
        controller = self.controller()
        prompts = []
        controller.updatePromptRequested.connect(prompts.append)
        controller._apply_update_result("none", None)
        self.assertEqual(prompts, [])
        controller._update_manual = True
        controller._apply_update_result("none", None)
        self.assertEqual(prompts[-1]["available"], False)
        controller.close()

    def test_background_errors_do_not_prompt_and_ready_cache_restores_offline(self) -> None:
        from hr_toolkit.app_update import UpdateInfo
        controller = self.controller()
        notifications = []
        controller.notificationRequested.connect(lambda *args: notifications.append(args))
        controller._apply_update_result("check-error", "offline")
        with patch("hr_toolkit.gui_qt.controller.runlog.log_line"):
            controller._apply_update_result("download-error", "offline")
        self.assertEqual(notifications, [])
        info = UpdateInfo("9.0.0", "https://gitee.com/setup.exe", "a" * 64, (), False, "https://gitee.com/manifest")
        controller._apply_update_result("restored", (info, Path("cached.exe")))
        self.assertTrue(controller.updateReady)
        self.assertTrue(controller._block_run_for_update())
        controller.close()

    def test_date_presets_keep_legacy_calendar_ranges(self) -> None:
        controller = self.controller()
        controller.selectTool("data_statistics")
        controller.applyDatePreset("week", "this_week")
        state = controller._form_states[("data_statistics", "default")]
        today = date.today()
        start = date.fromisoformat(state["week_start"])
        end = date.fromisoformat(state["week_end"])
        self.assertEqual(start.weekday(), 0)
        self.assertEqual(end.weekday(), 6)
        self.assertLessEqual(start, today)
        self.assertGreaterEqual(end, today)

        controller.applyDatePreset("month", "this_month")
        self.assertEqual(date.fromisoformat(state["month_start"]).day, 1)
        self.assertEqual(date.fromisoformat(state["month_end"]).month, today.month)
        controller.applyDatePreset("month", "clear")
        self.assertEqual(state["month_start"], "")
        self.assertEqual(state["month_end"], "")
        controller.close()

    def test_legacy_history_reuse_accepts_every_current_navigation_tool(self) -> None:
        for tool_id in (
            "social_security",
            "insurance_ledger",
            "data_statistics",
            "salary_split",
            "salary_merge",
            "material_collector",
        ):
            with self.subTest(tool_id=tool_id):
                controller = self.controller()
                controller._history_selected = SimpleNamespace(
                    summary=SimpleNamespace(tool_id=tool_id, mode=None),
                    inputs=(),
                )
                controller.reuseHistory()
                self.assertEqual(controller.currentTool, tool_id)
                controller.close()

    def test_run_button_text_tracks_tool_switches(self) -> None:
        controller = self.controller()
        changes = []
        controller.runButtonTextChanged.connect(lambda: changes.append(controller.runButtonText))

        self.assertEqual(controller.runButtonText, "生成报表")
        controller.selectTool("material_collector")

        self.assertEqual(controller.runButtonText, "开始打包")
        self.assertIn("开始打包", changes)
        controller.close()

    def test_run_without_project_reports_required_next_step(self) -> None:
        controller = self.controller()
        notifications = []
        controller.notificationRequested.connect(
            lambda *args: notifications.append(args)
        )

        controller.runOrCancel()

        self.assertFalse(controller.busy)
        self.assertEqual(len(notifications), 1)
        self.assertEqual(notifications[0][0], "请先打开工作项目")
        self.assertIn("新建或打开", notifications[0][1])
        controller.close()

    def test_preview_process_start_failure_uses_compatible_worker(self) -> None:
        from hr_toolkit.background_process import BusinessProcessStartError

        controller = self.controller()
        invocation = ToolInvocation(
            nav_id="folder_rename",
            variant="default",
            tool_id="folder_rename",
            tool_name="资料文件夹改名",
            group_name="人员与档案",
            function_module="tests.test_qt_controller",
            function_name="_preview_probe",
            args=(),
            kwargs={},
            description="预览兼容测试",
            preview=True,
        )

        with patch(
            "hr_toolkit.background_process.run_business_process",
            side_effect=BusinessProcessStartError(
                "[WinError 2] 系统找不到指定的文件。"
            ),
        ), patch("hr_toolkit.gui_qt.controller.threading.Thread") as thread:
            controller._start_preview(invocation)
            worker = thread.call_args.kwargs["target"]
            worker()

        self.assertFalse(controller.busy)
        self.assertEqual(len(controller.renameReview._plan["rows"]), 3)
        self.assertEqual(controller.renameReview._plan["mode"], "excel")
        controller.close()

    def test_workspace_selection_details_follow_model_refresh(self) -> None:
        controller = self.controller()
        selected = {
            "name": "名单.xlsx",
            "path": str(Path.cwd() / "名单.xlsx"),
            "isDir": False,
            "detail": "XLSX",
        }
        controller._workspace_items = [selected]
        controller.selectWorkspaceRow(0)

        self.assertTrue(controller.workspaceSelectionAvailable)
        self.assertEqual(controller.workspaceSelectedName, "名单.xlsx")
        self.assertEqual(controller.workspaceSelectedDetail, "XLSX")

        controller._workspace_generation = 2
        controller._apply_workspace_items(2, [])
        self.assertFalse(controller.workspaceSelectionAvailable)
        controller.close()

    def test_workspace_refresh_preserves_rows_across_metadata_and_structure_changes(self) -> None:
        controller = self.controller()
        self.addCleanup(controller.close)
        controller._workspace_generation = 3
        rows = [{"path": str(Path.cwd() / str(i)), "name": str(i), "isDir": False,
                 "depth": 0, "expanded": False, "hasChildren": False, "detail": "old"}
                for i in range(40)]
        controller._apply_workspace_items(3, rows)
        controller.selectWorkspaceRow(8)
        resets, changes = [], []
        controller.workspaceModel.modelReset.connect(lambda: resets.append(True))
        controller.workspaceModel.dataChanged.connect(lambda first, last, roles: changes.append((first.row(), last.row())))
        updated = [dict(row, detail="new") if i == 8 else dict(row) for i, row in enumerate(rows)]
        controller._apply_workspace_items(3, updated)
        self.assertEqual(resets, [])
        self.assertEqual(changes, [(8, 8)])
        self.assertEqual(controller.workspaceSelectedDetail, "new")
        self.assertEqual(controller.workspaceModel.items(), updated)
        controller._apply_workspace_items(3, list(updated))
        controller._apply_workspace_items(2, [])
        self.assertEqual(changes, [(8, 8)])
        self.assertEqual(resets, [])

        for replacement in (list(reversed(updated)),
                            [dict(row, detail="all changed") for row in reversed(updated)],
                            updated[:-1], []):
            controller._apply_workspace_items(3, replacement)
            self.assertEqual(resets, [])
            self.assertEqual(controller.workspaceModel.items(), replacement)
            self.assertEqual(controller.workspaceSelectedPath, rows[8]["path"] if replacement else "")
        self.assertFalse(controller.workspaceSelectionAvailable)

    def test_workspace_structural_diff_keeps_unchanged_persistent_indices(self) -> None:
        from hr_toolkit.gui_qt.compat import QT_MAJOR
        from hr_toolkit.gui_qt.models import WorkspaceModel
        if QT_MAJOR == 6:
            from PySide6.QtCore import QPersistentModelIndex
        else:
            from PySide2.QtCore import QPersistentModelIndex
        model = WorkspaceModel()
        rows = [{"path": str(i), "name": str(i), "detail": "old"} for i in range(100)]
        model.set_items(rows)
        persistent = QPersistentModelIndex(model.index(50, 0))
        resets = []
        model.modelReset.connect(lambda: resets.append(True))
        replacement = rows[:5] + [{"path": "new", "name": "new"}] + rows[7:80] + rows[81:]
        replacement = [dict(row, detail="new") if row["path"] == "50" else row for row in replacement]
        model.sync_items(replacement)
        self.assertEqual(resets, [])
        self.assertTrue(persistent.isValid())
        path_role = next(role for role, name in model.roleNames().items() if name == b"path")
        self.assertEqual(persistent.data(path_role), "50")
        self.assertEqual(persistent.row(), 49)
        self.assertEqual(model.item_at(49)["detail"], "new")
        self.assertEqual([row["path"] for row in model.items()], [row["path"] for row in replacement])
        # Widespread pair swaps exceed the notification budget; the fallback
        # still produces exactly the requested order.
        many = [{"path": str(i)} for i in range(200)]
        model.set_items(many)
        resets.clear()
        swapped = [many[i ^ 1] for i in range(200)]
        model.sync_items(swapped)
        self.assertEqual(len(resets), 1)
        self.assertEqual([row["path"] for row in model.items()], [row["path"] for row in swapped])
        # Ambiguous identities must fall back without losing or merging rows.
        model.sync_items([{"path": "duplicate"}, {"path": "duplicate"}])
        self.assertEqual(len(resets), 2)
        self.assertEqual(model.rowCount(), 2)

    def test_workspace_refresh_keeps_expanded_branches_and_shows_new_results(self) -> None:
        controller = self.controller()
        self.addCleanup(controller.close)
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            results = root / "业务" / "工具" / "处理结果"
            results.mkdir(parents=True)
            closed = root / "未展开"
            closed.mkdir()
            (closed / "隐藏行.xlsx").touch()
            selected = results / "原结果.xlsx"
            selected.touch()
            controller._project_path = root
            expanded = frozenset(str(path) for path in (results.parent.parent, results.parent, results))
            controller._apply_workspace_items(controller._workspace_generation,
                                              controller._scan_workspace_tree(root, expanded))
            selected_row = next(i for i, item in enumerate(controller._workspace_items)
                                if item["path"] == str(selected))
            controller.selectWorkspaceRow(selected_row)
            (results / "新结果.xlsx").touch()
            jobs = []
            with patch.object(controller, "_schedule_workspace_read", side_effect=lambda generation, worker: jobs.append(worker)):
                controller.refreshWorkspace()
            with patch.object(AppController, "_scan_directory", wraps=AppController._scan_directory) as scan:
                jobs.pop()()
            self.assertEqual({item["path"] for item in controller._workspace_items if item["expanded"]}, expanded)
            self.assertIn(str(results / "新结果.xlsx"), {item["path"] for item in controller._workspace_items})
            self.assertNotIn(closed, [call.args[0] for call in scan.call_args_list])
            self.assertEqual(controller.workspaceSelectedPath, str(selected))
            self.assertTrue(controller.workspaceSelectionAvailable)
            self.assertFalse(controller._workspace_refresh_pending)

    def test_workspace_toggle_during_refresh_overrides_stale_expansion_snapshot(self) -> None:
        controller = self.controller()
        self.addCleanup(controller.close)
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            folder = root / "资料"
            folder.mkdir()
            (folder / "名单.xlsx").touch()
            controller._project_path = root
            controller._apply_workspace_items(controller._workspace_generation,
                                              controller._scan_workspace_tree(root, frozenset({str(folder)})))
            jobs = []
            with patch.object(controller, "_schedule_workspace_read", side_effect=lambda generation, worker: jobs.append(worker)):
                controller.refreshWorkspace()
                controller.toggleWorkspaceRow(0)
                jobs[0]()  # The stale expanded view must not restore itself.
                jobs[1]()
                self.assertEqual(len(controller._workspace_items), 1)
                self.assertFalse(controller._workspace_items[0]["expanded"])
                jobs.clear()
                controller.refreshWorkspace()
                controller.toggleWorkspaceRow(0)
                jobs[0]()  # The stale collapsed view must not undo expansion.
                jobs[1]()
            self.assertEqual(len(controller._workspace_items), 2)
            self.assertTrue(controller._workspace_items[0]["expanded"])
            self.assertEqual(controller._workspace_items[1]["path"], str(folder / "名单.xlsx"))

    def test_workspace_folder_toggle_updates_rows_without_model_reset(self) -> None:
        controller = self.controller()
        root_path = Path.cwd() / "共用资料"
        child_path = root_path / "名单.xlsx"
        sibling_path = Path.cwd() / "处理结果"
        controller._workspace_generation = 7
        controller._workspace_items = [
            {
                "name": "共用资料",
                "path": str(root_path),
                "isDir": True,
                "depth": 0,
                "expanded": True,
                "hasChildren": True,
                "detail": "文件夹",
            },
            {
                "name": "名单.xlsx",
                "path": str(child_path),
                "isDir": False,
                "depth": 1,
                "expanded": False,
                "hasChildren": False,
                "detail": "XLSX",
            },
            {
                "name": "处理结果",
                "path": str(sibling_path),
                "isDir": True,
                "depth": 0,
                "expanded": False,
                "hasChildren": True,
                "detail": "文件夹",
            },
        ]
        controller.workspaceModel.set_items(controller._workspace_items)
        resets = []
        removals = []
        insertions = []
        controller.workspaceModel.modelReset.connect(lambda: resets.append(True))
        controller.workspaceModel.rowsRemoved.connect(lambda *_args: removals.append(True))
        controller.workspaceModel.rowsInserted.connect(lambda *_args: insertions.append(True))

        controller.toggleWorkspaceRow(0)

        self.assertEqual(resets, [])
        self.assertEqual(removals, [True])
        self.assertEqual(controller.workspaceModel.rowCount(), 2)
        self.assertFalse(controller.workspaceModel.item_at(0)["expanded"])
        self.assertEqual(controller.workspaceModel.item_at(1)["name"], "处理结果")

        with patch("hr_toolkit.gui_qt.controller.threading.Thread") as thread:
            controller.toggleWorkspaceRow(0)
            thread.return_value.start.assert_called_once_with()
        controller._apply_workspace_children(
            7,
            0,
            str(root_path),
            0,
            [
                {
                    "name": "名单.xlsx",
                    "path": str(child_path),
                    "isDir": False,
                    "depth": 1,
                    "expanded": False,
                    "hasChildren": False,
                    "detail": "XLSX",
                }
            ],
        )

        self.assertEqual(resets, [])
        self.assertEqual(insertions, [True])
        self.assertEqual(controller.workspaceModel.rowCount(), 3)
        self.assertTrue(controller.workspaceModel.item_at(0)["expanded"])
        self.assertEqual(controller.workspaceModel.item_at(1)["name"], "名单.xlsx")
        controller.close()

    def test_qt_tutorial_uses_the_complete_legacy_tk_content(self) -> None:
        controller = self.controller()
        groups = controller.tutorialGroups
        items = [item for group in groups for item in group["items"]]
        self.assertEqual(
            [item["label"] for item in items],
            [
                "社保明细与汇总",
                "保险台账与预警",
                "考勤与周月报",
                "工资表拆分",
                "多月工资合并",
                "异动表汇总",
                "花名册更新",
                "异动流程核对",
                "档案入库",
                "档案表生成",
                "员工资料打包",
                "资料文件夹改名",
            ],
        )
        statistics = next(item for item in items if item["toolId"] == "data_statistics")
        copy = [line["text"] for line in statistics["lines"]]
        self.assertIn("容易疑惑1：", copy[6])
        self.assertIn("容易疑惑2：", copy[7])
        self.assertEqual(statistics["lines"][-1]["style"], "warning")
        controller.close()

    def test_close_requires_confirmation_while_background_work_is_active(self) -> None:
        controller = self.controller()
        prompts = []
        controller.confirmationRequested.connect(lambda *args: prompts.append(args))
        controller._busy = True
        self.assertFalse(controller.requestClose())
        self.assertEqual(len(prompts), 1)
        self.assertFalse(controller.requestClose())
        self.assertEqual(len(prompts), 1)
        token = prompts[0][2]
        controller.confirmAction(token, False)
        controller._busy = False
        self.assertTrue(controller.requestClose())
        self.assertTrue(controller._closed)

    def test_close_waits_for_project_and_storage_workers(self) -> None:
        for attribute in ("_project_opening", "_history_busy", "_trash_busy"):
            with self.subTest(attribute=attribute):
                controller = self.controller()
                prompts = []
                controller.confirmationRequested.connect(lambda *args: prompts.append(args))
                setattr(controller, attribute, True)
                self.assertFalse(controller.requestClose())
                self.assertEqual(len(prompts), 1)
                controller.confirmAction(prompts[0][2], False)
                setattr(controller, attribute, False)
                controller.close()

    def test_cancelling_workspace_import_does_not_cancel_update_download(self) -> None:
        controller = self.controller()
        workspace_cancel = SimpleNamespace(called=False)
        update_cancel = SimpleNamespace(called=False)
        workspace_cancel.set = lambda: setattr(workspace_cancel, "called", True)
        update_cancel.set = lambda: setattr(update_cancel, "called", True)
        controller._workspace_cancel_event = workspace_cancel
        controller._update_cancel_event = update_cancel
        controller.cancelWorkspaceImport()
        self.assertTrue(workspace_cancel.called)
        self.assertFalse(update_cancel.called)
        controller._workspace_cancel_event = None
        controller._update_cancel_event = None
        controller.close()

    def test_log_model_append_batch_preserves_order_and_truncation(self) -> None:
        model = LogModel()
        items = [{"time": "12:00:00", "text": f"msg_{i}", "level": "info"} for i in range(15)]
        model.append_batch(items[:10], maximum=10)
        self.assertEqual(len(model), 10)
        self.assertEqual(model.item_at(0)["text"], "msg_0")
        self.assertEqual(model.item_at(9)["text"], "msg_9")

        # Adding 5 more with maximum=10 should drop oldest 5 and keep newest 10
        model.append_batch(items[10:], maximum=10)
        self.assertEqual(len(model), 10)
        self.assertEqual(model.item_at(0)["text"], "msg_5")
        self.assertEqual(model.item_at(9)["text"], "msg_14")

    def test_controller_log_batching_and_synchronous_flush(self) -> None:
        controller = self.controller()
        controller._clear_logs()
        self.assertEqual(len(controller.logModel), 0)

        # Emitting 10 logs buffers them before flush
        for i in range(10):
            controller._append_log(f"test_log_{i}", "info")
        self.assertEqual(len(controller._log_buffer), 10)
        self.assertEqual(len(controller.logModel), 0)

        # Synchronous flush empties buffer and populates model in FIFO order
        controller._flush_logs()
        self.assertEqual(len(controller._log_buffer), 0)
        self.assertEqual(len(controller.logModel), 10)
        self.assertEqual(controller.logModel.item_at(0)["text"], "test_log_0")
        self.assertEqual(controller.logModel.item_at(9)["text"], "test_log_9")

        # _apply_run_finished forces synchronous flush
        controller._append_log("trailing_message", "success")
        self.assertEqual(len(controller._log_buffer), 1)
        controller._apply_run_finished()
        self.assertEqual(len(controller._log_buffer), 0)
        self.assertEqual(len(controller.logModel), 11)
        self.assertEqual(controller.logModel.item_at(10)["text"], "trailing_message")
        controller.close()

    def test_reconcile_notice_is_emphasized_log_only_and_survives_completion(self) -> None:
        controller = self.controller()
        self.addCleanup(controller.close)
        controller.selectTool("personnel_change_merge")
        controller.selectVariant("reconcile")
        controller._clear_logs()
        controller._set_busy(True)
        stage = controller.runProgressMessage
        message = "提示：入职流程缺少状态列，未进行状态筛选。"
        controller._queue_run_progress(0, 0, message)
        self.assertIsNone(controller._incoming_progress)
        controller._drain_run_progress()
        self.assertEqual(controller.runProgressMessage, stage)
        controller._queue_run_progress(1, 2, "正在核对资料")
        controller._drain_run_progress()
        self.assertEqual(controller.runProgressMessage, "正在核对资料")
        controller._apply_run_finished()
        notices = [item for item in controller.logModel.items() if item["text"] == message]
        self.assertEqual(len(notices), 1)
        self.assertEqual(notices[0]["level"], "warning_emphasis")

    def test_controller_log_timer_flush(self) -> None:
        import time

        controller = self.controller()
        controller._clear_logs()
        controller._append_log("timer_msg", "info")
        self.assertEqual(len(controller.logModel), 0)
        self.assertEqual(len(controller._log_buffer), 1)

        # Let Qt event loop process events until timer fires
        deadline = time.monotonic() + 0.5
        while time.monotonic() < deadline and len(controller.logModel) == 0:
            QCoreApplication.processEvents()
            time.sleep(0.01)

        self.assertEqual(len(controller.logModel), 1)
        self.assertEqual(controller.logModel.item_at(0)["text"], "timer_msg")
        controller.close()

    def test_controller_file_dialog_directory_memory_hierarchy_and_cancellation(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            saved_dir = tmp_path / "saved"
            saved_dir.mkdir()
            project_dir = tmp_path / "project"
            project_dir.mkdir()
            other_dir = tmp_path / "other"
            other_dir.mkdir()
            sample_file = other_dir / "test.xlsx"
            sample_file.write_text("dummy", encoding="utf-8")

            controller = self.controller()

            # 1. When last_selected_dir is valid, it takes priority
            controller._last_selected_dir = saved_dir
            controller._project_path = project_dir
            self.assertEqual(controller._file_dialog_initial_dir(), str(saved_dir))

            # 2. When last_selected_dir is deleted/invalid, falls back to project_path
            controller._last_selected_dir = tmp_path / "non_existent"
            self.assertEqual(controller._file_dialog_initial_dir(), str(project_dir))

            # 3. When project_path is also None, falls back to desktop / home
            controller._project_path = None
            fallback = controller._file_dialog_initial_dir()
            self.assertTrue(Path(fallback).is_dir())

            # 4. role="new_project" starts at defaultProjectParent
            self.assertEqual(
                controller._file_dialog_initial_dir(role="new_project"),
                str(Path(controller.defaultProjectParent).expanduser().absolute()),
            )

            # 5. Successful selection remembers folder (or parent folder for file)
            controller._remember_file_dialog_path(str(sample_file))
            self.assertEqual(controller._last_selected_dir, other_dir)

            # 6. Cancelled dialog (empty string/list/None) DOES NOT overwrite memory
            controller._remember_file_dialog_path("")
            self.assertEqual(controller._last_selected_dir, other_dir)
            controller._remember_file_dialog_path([])
            self.assertEqual(controller._last_selected_dir, other_dir)
            controller._remember_file_dialog_path(None)
            self.assertEqual(controller._last_selected_dir, other_dir)
            for invalid in ("relative", "Ř<", "bad\x00path", True, {"path": str(other_dir)}):
                controller._remember_file_dialog_path(invalid)
                self.assertEqual(controller._last_selected_dir, other_dir)

            controller.close()

    def test_controller_file_dialog_directory_memory_persists_in_settings(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            settings_file = tmp_path / "workspace-ui.json"
            chosen_dir = tmp_path / "chosen"
            chosen_dir.mkdir()

            with patch.object(AppController, "_settings_path", return_value=settings_file):
                controller = AppController()
                controller._remember_file_dialog_path(chosen_dir)

                self.assertTrue(settings_file.is_file())
                data = json.loads(settings_file.read_text(encoding="utf-8"))
                self.assertEqual(data.get("last_selected_dir"), str(chosen_dir))

                # New controller instance loads it on start()
                controller2 = AppController()
                controller2.start()
                deadline = time.monotonic() + 3
                while controller2._startup_loading and time.monotonic() < deadline:
                    self.application.processEvents()
                    time.sleep(0.001)
                self.assertFalse(controller2._startup_loading)
                self.assertEqual(controller2._last_selected_dir, chosen_dir)
                self.assertEqual(controller2._file_dialog_initial_dir(), str(chosen_dir))

                controller.close()
                controller2.close()

    def test_controller_trash_read_only_protection_and_restore_selection(self) -> None:
        controller = self.controller()
        fake_store = SimpleNamespace(writable=False, list_trash_details=lambda: [])
        controller._project_store = fake_store
        controller._trash_selected_id = "batch-1"

        with patch("threading.Thread") as mock_thread:
            controller.restoreSelectedTrash()
            # Read-only store prevents launching restore worker thread
            mock_thread.assert_not_called()

        # Selection retention test
        fake_detail = SimpleNamespace(
            summary=SimpleNamespace(
                id="batch-1",
                group_name="薪酬管理",
                tool_name="工资表拆分",
                business_description="七月",
                business_period="2026-07",
                directory_name="dir",
                status="success",
                deleted_at="2026-08-01T00:00:00Z",
            ),
            original_relative_path="rel",
            upload_count=1,
            result_count=1,
            supplement_count=0,
            total_size_bytes=100,
        )
        controller._apply_trash_list(controller._trash_generation, [fake_detail], "")
        self.assertEqual(controller.trashSelectedId, "batch-1")

        # Simulate restore failure
        notifications = []
        controller.notificationRequested.connect(lambda *args: notifications.append(args))
        controller._apply_trash_action(False, "权限不足")
        self.assertEqual(notifications[-1][0], "恢复没有完成")
        self.assertEqual(notifications[-1][1], "权限不足")
        controller._apply_trash_list(controller._trash_generation, [fake_detail], "")
        self.assertFalse(controller.trashBusy)
        self.assertEqual(controller.trashSelectedId, "batch-1")
        controller.close()

    def test_controller_workspace_search_and_scan_threading(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            sub = root / "sub"
            sub.mkdir()
            (sub / "file.xlsx").touch()

            controller = self.controller()
            controller._project_path = root

            threads_started = []
            orig_start = threading.Thread.start

            def tracking_start(t_self):
                threads_started.append(t_self.name)
                return orig_start(t_self)

            with patch.object(threading.Thread, "start", side_effect=tracking_start, autospec=True):
                controller.refreshWorkspace()

            self.assertIn("HRToolkit-workspace-scan", threads_started)
            controller.close()

    def test_controller_workspace_import_cancellation_and_state(self) -> None:
        controller = self.controller()
        controller._workspace_busy = True
        cancel_event = threading.Event()
        controller._workspace_cancel_event = cancel_event

        self.assertFalse(cancel_event.is_set())
        controller.cancelWorkspaceImport()
        self.assertTrue(cancel_event.is_set())

        notifications = []
        controller.notificationRequested.connect(lambda *args: notifications.append(args))
        controller._apply_workspace_import_result(False, "资料导入已取消。")
        self.assertFalse(controller.workspaceBusy)
        self.assertIsNone(controller._workspace_cancel_event)
        self.assertEqual(notifications[-1][0], "导入未完成")
        self.assertEqual(notifications[-1][1], "资料导入已取消。")
        controller.close()

    def test_controller_material_preferences_and_presets(self) -> None:
        controller = self.controller()
        controller.selectTool("material_collector")

        state = controller._form_states[("material_collector", "default")]
        self.assertTrue(state.get("collect_all"))

        # Apply preset "入职材料" -> collect_all becomes False, materials updated
        controller.applyMaterialPreset("入职材料")
        self.assertFalse(state.get("collect_all"))
        self.assertEqual(state.get("material_types"), ["身份证", "劳动合同"])

        # Add custom material via submitTextAction
        controller.requestAddCustomMaterial()
        token = controller._pending_text_action
        self.assertIsNotNone(token)
        controller.submitTextAction(token, "体检报告")
        self.assertIn("体检报告", state.get("material_types"))
        self.assertIn("体检报告", controller._material_preferences.custom_materials)

        # Clear and select all
        controller.clearMaterials()
        self.assertEqual(state.get("material_types"), [])
        controller.selectAllMaterials()
        self.assertEqual(
            set(state.get("material_types")),
            set(controller._material_preferences.available_materials),
        )
        controller.close()

    def test_controller_create_project_validation_and_creation(self) -> None:
        import time

        controller = self.controller()
        notifications = []
        controller.notificationRequested.connect(lambda *args: notifications.append(args))

        # 1. Invalid project name rejects before creating thread
        controller.createProject("CON", "/some/path")
        self.assertEqual(notifications[-1][0], "无法创建项目")
        self.assertIn("Windows 系统保留名称", notifications[-1][1])

        # 2. Valid project creates real project store in background without slot exceptions
        with tempfile.TemporaryDirectory() as tmp:
            parent = Path(tmp)
            opened = []
            controller._projectOpened.connect(lambda gen, store, path: opened.append((path, store)))

            try:
                controller.createProject("测试项目", str(parent))
                for _ in range(50):
                    if opened:
                        break
                    time.sleep(0.05)
                    QCoreApplication.processEvents()

                self.assertEqual(len(opened), 1)
                target_path, store = opened[0]
                self.assertEqual(Path(target_path), parent / "测试项目")
                self.assertEqual(controller.projectName, "测试项目")
                self.assertTrue(controller.projectWritable)
                self.assertEqual(Path(controller.projectPath), parent / "测试项目")
            finally:
                # Windows cannot remove project-write.lock while it is open.
                controller.close()
            self.assertIsNone(store._writer_lock)
            from hr_toolkit.project_store import ProjectStore
            with ProjectStore.open(parent / "测试项目", read_only_fallback=False) as reopened:
                self.assertTrue(reopened.writable)

    def test_project_recovery_guard_still_blocks_operations_until_reopen(self) -> None:
        controller = self.controller()
        self.addCleanup(controller.close)
        notifications = []
        controller.notificationRequested.connect(lambda *args: notifications.append(args))
        mock_store = Mock()
        mock_store.writable = True
        controller._project_store = mock_store
        controller._project_path = Path("/tmp/project")
        controller._workspace_recovery_blocked = True
        with patch.object(controller, "_submit_selection") as submit:
            controller._start_workspace_import([Path("/tmp/名单.xlsx")])
            submit.assert_not_called()
        # 3. Operations are blocked while recovery is blocked
        notifications.clear()
        controller.createProject("新建项目", "/tmp")
        self.assertEqual(notifications[-1][0], "项目未安全恢复")

        notifications.clear()
        controller.openProjectDialog()
        self.assertEqual(notifications[-1][0], "项目未安全恢复")

        notifications.clear()
        controller.openProject("/tmp/other_project")
        self.assertEqual(notifications[-1][0], "项目未安全恢复")

        notifications.clear()
        controller.restoreSelectedTrash()
        self.assertEqual(notifications[-1][0], "项目未安全恢复")

        notifications.clear()
        controller.runOrCancel()
        self.assertEqual(notifications[-1][0], "项目未安全恢复")

        # 4. Reopening the current project resets the recovery blocked state
        controller._apply_project_open(controller._project_generation, mock_store, "/tmp/project")
        self.assertFalse(controller._workspace_recovery_blocked)
        self.assertTrue(controller.projectWritable)


    def test_workspace_file_selection_does_not_archive_sources(self) -> None:
        controller = self.controller()
        self.addCleanup(controller.close)
        store = Mock()
        controller._project_store = store
        paths = [Path("/tmp/名单.xlsx")]
        with patch.object(controller, "_submit_selection") as submit:
            controller._start_workspace_import(paths)
            submit.assert_called_once_with("input", paths, replace=not controller.inputAllowsMultiple)
        store.import_sources.assert_not_called()
        store.import_to_directory.assert_not_called()

    def test_controller_ocr_cache_mode_switch_restores_user_preference(self) -> None:
        controller = self.controller()
        controller.selectTool("material_collector")

        # 1. User sets use_ocr_cache to False in normal (person_folder) mode
        controller.setFieldValue("use_ocr_cache", False)
        state = controller._form_states[controller._state_key()]
        self.assertFalse(state["use_ocr_cache"])

        # 2. Switch library_mode to flat_ocr -> use_ocr_cache is forced to True
        controller.setFieldValue("library_mode", "flat_ocr")
        self.assertTrue(state["use_ocr_cache"])

        # 3. Switch library_mode back to person_folder -> use_ocr_cache is restored to False!
        controller.setFieldValue("library_mode", "person_folder")
        self.assertFalse(state["use_ocr_cache"])

        controller.close()

    def test_controller_choose_project_parent_directory_memory_and_initial(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_root = Path(tmp)
            dir_a = tmp_root / "dir_a"
            dir_b = tmp_root / "dir_b"
            dir_a.mkdir()
            dir_b.mkdir()

            controller = self.controller()

            # 1. When called with an existing directory, that directory is passed as initial
            with patch("hr_toolkit.gui_qt.controller.QFileDialog.getExistingDirectory", return_value=str(dir_b)) as chooser:
                chosen = controller.chooseProjectParent(str(dir_a))
                self.assertEqual(chosen, str(dir_b))
                chooser.assert_called_once()
                self.assertEqual(chooser.call_args.args[2], str(dir_a.resolve()))
                # Memory is updated to chosen directory
                self.assertEqual(controller._last_selected_dir, dir_b)

            # 2. When user cancels, empty string is returned and memory does NOT change
            with patch("hr_toolkit.gui_qt.controller.QFileDialog.getExistingDirectory", return_value="") as chooser:
                chosen = controller.chooseProjectParent(str(dir_a))
                self.assertEqual(chosen, "")
                # Memory remains dir_b
                self.assertEqual(controller._last_selected_dir, dir_b)

            controller.close()

    def test_project_parent_chooser_recovers_empty_missing_and_corrupt_initial_paths(self) -> None:
        controller = self.controller()
        self.addCleanup(controller.close)
        with tempfile.TemporaryDirectory() as tmp:
            fallback = str(Path(tmp).resolve())
            for current in ("", str(Path(tmp) / "missing"), "Ř<", "bad\x00path"):
                with self.subTest(current=repr(current)), patch.object(controller, "_file_dialog_initial_dir", return_value=fallback) as initial, patch("hr_toolkit.gui_qt.controller.QFileDialog.getExistingDirectory", return_value="") as chooser:
                    self.assertEqual(controller.chooseProjectParent(current), "")
                    initial.assert_called_once_with(role="new_project")
                    self.assertEqual(chooser.call_args.args[2], fallback)

    def test_system_directory_recovery_is_shared_by_settings_logs_history_and_dialogs(self) -> None:
        from hr_toolkit import runlog
        from hr_toolkit.common import paths
        from hr_toolkit.desktop_helpers import desktop_dir
        from hr_toolkit.history_store import default_history_root

        controller = self.controller()
        self.addCleanup(controller.close)
        with tempfile.TemporaryDirectory() as tmp:
            profile = Path(tmp).resolve() / "系统用户目录"
            profile.mkdir()
            local_data = profile / "AppData" / "Local"
            with patch.object(paths.sys, "platform", "win32"), patch.dict(os.environ, {"LOCALAPPDATA": "Ř<", "HR_TOOLKIT_DATA_DIR": ""}), patch.object(Path, "home", return_value=Path("Ř<")), patch.object(paths, "_windows_profile_dir", return_value=profile), patch.object(paths, "_windows_shell_folder", return_value=local_data):
                self.assertEqual(controller._settings_path(), local_data / "HRToolkit" / "workspace-ui.json")
                self.assertEqual(runlog.user_log_dir(), local_data / "HRToolkit" / "logs")
                self.assertEqual(default_history_root(), local_data / "HRToolkit" / "Data")
                self.assertEqual(desktop_dir(), profile)
                self.assertEqual(controller.defaultProjectParent, str(profile))
                self.assertEqual(controller._file_dialog_initial_dir(), str(profile))

    def test_corrupt_startup_paths_never_open_cwd_or_leave_startup_busy(self) -> None:
        controller = self.controller()
        self.addCleanup(controller.close)
        notifications = []
        controller.notificationRequested.connect(lambda *args: notifications.append(args))
        with patch.object(controller, "_settings_path", side_effect=OSError("bad settings location")), patch("hr_toolkit.gui_qt.controller.cleanup_stale_update_files"), patch("hr_toolkit.gui_qt.controller.cleanup_cached_updates"), patch("hr_toolkit.gui_qt.controller.runlog.log_exception"):
            controller._startup_loading = True
            controller._set_busy(True)
            controller._load_startup()
            self.assertFalse(controller.busy)
            self.assertFalse(controller._startup_loading)
            self.assertFalse(AppController._save_workspace_preferences(controller))
        state = {"current_project": "Ř<", "recent_projects": [None, {}, "relative", "bad\x00path"]}
        with patch.object(controller, "openProject") as opened, patch("hr_toolkit.gui_qt.controller.cleanup_stale_update_files"), patch("hr_toolkit.gui_qt.controller.cleanup_cached_updates"):
            controller._startup_cancelled = False
            controller._apply_startup(state, [], None)
            opened.assert_not_called()
            self.assertEqual(notifications[-1][0], "请重新选择工作项目")
            controller._startup_cancelled = True
            controller._apply_startup(state, [], None)
            self.assertEqual(controller.recentProjects, [])

    def test_project_worker_errors_are_logged_and_identify_create_or_open(self) -> None:
        controller = self.controller()
        self.addCleanup(controller.close)
        notifications = []
        controller.notificationRequested.connect(lambda *args: notifications.append(args))
        with patch("hr_toolkit.gui_qt.controller.threading.Thread") as thread:
            for invalid in ("", "relative", "Ř<", "bad\x00path", "C:relative"):
                controller.openProject(invalid)
                self.assertFalse(controller._project_opening)
                self.assertEqual(notifications[-1][0], "无法打开项目")
            thread.assert_not_called()
        with tempfile.TemporaryDirectory() as tmp:
            with patch("hr_toolkit.gui_qt.controller.threading.Thread") as thread, patch("hr_toolkit.gui_qt.controller.ProjectStore.create", side_effect=OSError("creation failure")), patch("hr_toolkit.gui_qt.controller.runlog.log_exception") as logged:
                controller.createProject("新项目", tmp)
                thread.call_args.kwargs["target"]()
                self.assertFalse(controller._project_opening)
                self.assertEqual(notifications[-1][0], "无法创建项目")
                logged.assert_called_once()
            with patch("hr_toolkit.gui_qt.controller.threading.Thread") as thread, patch("hr_toolkit.gui_qt.controller.ProjectStore.open", side_effect=OSError("opening failure")), patch("hr_toolkit.gui_qt.controller.runlog.log_exception") as logged:
                controller.openProject(tmp)
                thread.call_args.kwargs["target"]()
                self.assertFalse(controller._project_opening)
                self.assertEqual(notifications[-1][0], "无法打开项目")
                logged.assert_called_once()


if __name__ == "__main__":
    unittest.main()
