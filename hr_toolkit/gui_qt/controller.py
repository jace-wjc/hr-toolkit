"""Qt-facing controller; business and project rules remain in existing modules."""

from __future__ import annotations

import json
import re
import os
import sys
import threading
import time
import calendar
from collections import deque
from dataclasses import replace
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4

from hr_toolkit import __version__, runlog
from hr_toolkit.common.paths import absolute_path_hint, path_text_error, user_app_data_dir, user_home_dir
from hr_toolkit.common.inputs import ARCHIVE_FILE_DIALOG_PATTERN
from hr_toolkit.app_update import (
    UpdateCancelledError,
    UpdateInfo,
    check_for_update,
    latest_installer_download,
    cleanup_stale_update_files,
    cleanup_cached_updates,
    download_cached_update,
    load_ready_update,
    launch_update_replacement,
    resolve_download_url,
    update_check_enabled,
    is_newer_version,
)
from hr_toolkit.release_notes import notes_for_version, release_entries
from hr_toolkit.desktop_helpers import (
    default_workspace_project_name,
    desktop_dir,
    open_path,
    workspace_project_create_error_message,
    workspace_project_creation_target,
)
from hr_toolkit.history_store import HISTORY_PAGE_SIZE, HistoryStore, TaskDetail
from hr_toolkit.material_preferences import MaterialPreferences
from hr_toolkit.project_store import ImportCancelled, ProjectStore
from hr_toolkit.run_coordinator import (
    ProjectRunCoordinator,
    RunCallbacks,
    RunRequest,
)
from hr_toolkit.tutorial_content import tutorial_groups

from .compat import (
    Property,
    QCoreApplication,
    QEvent,
    QDesktopServices,
    QFileDialog,
    QGuiApplication,
    QObject,
    QTimer,
    QUrl,
    Signal,
    Slot,
    constant_property,
)
from .form_specs import (
    DEFAULT_VARIANTS,
    EXCEL_SUFFIXES,
    normalize_report_date_text,
    FormValidationError,
    ToolInvocation,
    build_invocation,
    default_values,
    spec_for,
    variants_for,
)
from .models import (
    AiAttachmentModel,
    AiChatModel,
    AiConversationModel,
    HistoryModel,
    InputFileModel,
    LogModel,
    TrashModel,
    WorkspaceModel,
    ObjectListModel,
)
from .input_selection import accepts_file_name, selection_hint, selection_mode, validate_selection
from .drop_paths import local_drop_paths, native_mime_paths, text_paths
from .rename_review import RenameReview
from .presentation import Presentation


NAV_GROUPS = (
    ("社保与保险", (("social_security", "社保明细与汇总"), ("insurance_ledger", "保险台账与预警"))),
    ("考勤与统计", (("data_statistics", "考勤与周月报"),)),
    ("薪酬管理", (("salary_split", "工资表拆分"), ("salary_merge", "多月工资合并"))),
    (
        "人员与档案",
        (
            ("personnel_change_merge", "异动汇总"),
            ("archive_import", "档案入库"),
            ("material_collector", "员工资料打包"),
            ("folder_rename", "资料文件夹改名"),
        ),
    ),
)

WORKSPACE_HIDDEN_NAMES = frozenset({".hrtoolkit", ".DS_Store", "Thumbs.db", "desktop.ini"})
WORKSPACE_HIDDEN_SUFFIXES = (".partial", ".tmp", ".temp", ".lock")
WORKSPACE_SEARCH_LIMIT = 500
MAX_LOG_ROWS = 1000
HISTORY_STATUS_LABELS = {
    "draft": "未开始",
    "running": "处理中",
    "success": "已完成",
    "failed": "未完成",
    "stopped": "已停止",
}


class AppController(QObject):
    specChanged = Signal()
    projectChanged = Signal()
    busyChanged = Signal()
    runButtonTextChanged = Signal()
    runProgressChanged = Signal()
    salaryMappingChanged = Signal()
    salaryMappingRequested = Signal()
    salaryMappingClosed = Signal()
    templateRulesRequested = Signal()
    templateSelectionRequested = Signal()
    workspaceBusyChanged = Signal()
    workspaceChanged = Signal()
    workspaceSelectionChanged = Signal()
    supportChanged = Signal()
    selectionStateChanged = Signal()
    recentSelectionsChanged = Signal()
    _recentLocationReady = Signal(str)
    dropPreviewReady = Signal("QVariantMap", arguments=["preview"])
    formRevisionChanged = Signal()
    lastResultChanged = Signal()
    historyChanged = Signal()
    trashChanged = Signal()
    materialChanged = Signal()
    updateChanged = Signal()
    downloadLinkChanged = Signal()
    updateProgressChanged = Signal()
    updatePromptRequested = Signal("QVariantMap", arguments=["prompt"])
    releaseNotesRequested = Signal("QVariantMap", arguments=["details"])
    _updatePhaseIncoming = Signal(str)
    # Qt 5.15.2 rebuilds Connections handlers' argument tables from signal
    # metadata. Unnamed PySide2 arguments can crash QQmlBoundSignalExpression
    # during QML loading. Keep these names aligned with Main.qml; argument
    # types, order, emitters and business payloads remain unchanged.
    notificationRequested = Signal(str, str, str, arguments=["title", "message", "level"])
    confirmationRequested = Signal(str, str, str, arguments=["title", "message", "token"])
    projectCreationRequested = Signal(str, str, arguments=["name", "parent"])
    textInputRequested = Signal(
        str, str, str, str, arguments=["title", "prompt", "initialValue", "token"]
    )
    resizeSample = Signal(float)

    _projectOpened = Signal(int, object, str)
    _projectOpenFailed = Signal(int, str)
    _workspaceItemsReady = Signal(int, object)
    _workspaceChildrenReady = Signal(int, int, str, int, object)
    _logIncoming = Signal(str, str)
    _runProgress = Signal(int, int, str)
    _runSuccess = Signal(object, str, float, bool)
    _runError = Signal(str)
    _runStopped = Signal()
    _runFinished = Signal()
    _previewReady = Signal(object)
    _previewFailed = Signal(str)
    _salaryInspectionReady = Signal(object, str)
    _workspaceImportFinished = Signal(bool, str)
    _historyListReady = Signal(int, object, int, str)
    _historyDetailReady = Signal(int, object, str)
    _historyActionFinished = Signal(str, bool, str)
    _trashReady = Signal(int, object, str)
    _trashActionFinished = Signal(bool, str)
    _updateResult = Signal(str, object)
    _downloadLinkResult = Signal(str, object, str)
    _updateProgressIncoming = Signal(int, int)
    _inputItemsReady = Signal(int, object)
    _selectionReady = Signal(object, object, str)
    _dropPreviewResult = Signal(object, str)
    _invocationReady = Signal(object, object, bool)
    _startupReady = Signal(object, object, object)
    aiChanged = Signal()
    aiSettingsChanged = Signal()
    aiStatusChanged = Signal()
    aiHistoryChanged = Signal()
    aiTestFinished = Signal(bool, str)
    _aiDeltaIncoming = Signal(str)
    _aiFinishedIncoming = Signal(bool, str)
    _aiAttachmentsReady = Signal(int, object, object)

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._nav_id = "social_security"
        self._variants: dict[str, str] = dict(DEFAULT_VARIANTS)
        self._spec = spec_for(self._nav_id)
        self._form_states: dict[tuple[str, str], dict[str, Any]] = {}
        self._input_states: dict[tuple[str, str], list[Path]] = {}
        self._support_states: dict[tuple[str, str], str] = {}
        self._form_revision = 0
        self._input_model = InputFileModel(self)
        self._input_generation = 0
        self._input_metadata: dict[Path, dict[str, Any]] = {}
        self._selection_request = None
        self._selection_messages: dict[tuple[str, str], dict[str, tuple[str, bool]]] = {}
        self._drop_preview_request = None
        self._native_drop_urls = []
        self._drop_preview_pending = None
        self._drop_preview_lock = threading.Lock()
        self._drop_preview_running = False
        self._drop_preview_serial = 0
        self._workspace_transfer = None
        self._input_scan_lock = threading.Lock()
        self._input_scan_pending = None
        self._input_scan_running = False
        self._log_model = LogModel(self)
        self._log_buffer: list[dict[str, Any]] = []
        self._log_flush_timer = QTimer(self)
        self._log_flush_timer.setSingleShot(True)
        self._log_flush_timer.setInterval(50)
        self._log_flush_timer.timeout.connect(self._flush_logs)
        self._workspace_model = WorkspaceModel(self)
        self._history_model = HistoryModel(self)
        self._trash_model = TrashModel(self)
        self._workspace_items: list[dict[str, Any]] = []
        self._workspace_child_loads: set[str] = set()
        self._workspace_read_lock = threading.Lock()
        self._workspace_read_jobs = deque()
        self._workspace_read_workers = 0
        try:
            self._workspace_read_limit = max(1, min(4, int(os.environ.get("HR_TOOLKIT_SCAN_WORKERS", "2"))))
        except ValueError:
            self._workspace_read_limit = 2
        self._workspace_generation = 0
        self._workspace_refresh_pending = False
        self._workspace_scope = "all"
        self._workspace_search = ""
        self._workspace_selected_path: Path | None = None
        self._workspace_selected_item: dict[str, Any] | None = None
        self._workspace_expanded = False
        self._workspace_busy = False
        self._workspace_cancel_event: threading.Event | None = None
        self._project_store: ProjectStore | None = None
        self._project_path: Path | None = None
        self._project_opening = False
        self._project_operation = "打开"
        self._project_generation = 0
        self._recent_projects: list[Path] = []
        self._busy = False
        self._run_progress_visible = False
        self._run_progress_current = 0
        self._run_progress_total = 0
        self._run_progress_message = ""
        self._run_progress_started = 0.0
        self._run_progress_updated = 0.0
        self._run_progress_elapsed = 0
        self._run_progress_wait = 0
        self._run_progress_pending: tuple[int, int, str] | None = None
        self._incoming_progress_lock = threading.Lock()
        self._incoming_progress = None
        self._run_coordinator = ProjectRunCoordinator()
        self._preview_cancel_event: threading.Event | None = None
        self._presentation = Presentation(self)
        self._presentation.preferencesChanged.connect(self._save_workspace_preferences)
        self._rename_review = RenameReview(self)
        self._rename_review.confirmed.connect(self._execute_reviewed_rename)
        self._rename_review_invocation = None
        self._rename_review_context = None
        self._salary_header_profiles: dict[str, dict[str, Any]] = {}
        self._header_name_rules: dict[str, dict[str, Any]] = {}
        self._template_issue: dict[str, Any] = {}
        self._template_settings_tool = ""
        self._template_issue_project = ""
        self._template_input_snapshot = ""
        self._template_session_rules: dict[str, Any] | None = None
        self._template_session_snapshot = ""
        self._template_continuing = False
        self._salary_pending: ToolInvocation | None = None
        self._salary_project_key = ""
        self._salary_inspection: dict[str, Any] = {}
        self._salary_draft_profiles: dict[str, Any] = {}
        self._salary_hints: dict[str, Any] = {}
        self._salary_selection_drafts: dict[str, Any] = {}
        self._salary_reset_profile_keys: set[str] = set()
        self._salary_force_next = False
        self._salary_force_dialog = False
        self._pending_confirmation: str | None = None
        self._pending_confirmation_action: tuple[str, Any] | None = None
        self._pending_text_action: str | None = None
        self._pending_text_payload: Any = None
        self._last_result_dir: Path | None = None
        self._result_context = None
        self._result_files: list[Path] = []
        self._last_result_availability = (False, False)
        self._result_notices = ObjectListModel(("text", "category"), self)
        self._result_notice_rows = []
        self._result_notice_groups: dict[str, list[dict[str, Any]]] = {}
        self._result_notice_filter = "全部"
        self._result_notice_counts = {}
        self._stop_requested = False
        self._last_selected_dir: Path | None = None
        self._recent_selections: dict[str, list[dict[str, str]]] = {}
        self._recent_location_pending = False
        self._recentLocationReady.connect(self._finish_recent_location)
        self._last_run_by_key: dict[tuple[str, str], tuple[str, bool]] = {}
        self._original_switch_interval: float | None = None
        self._closed = False
        self._startup_loading = False
        self._startup_cancelled = False
        self._material_preferences = MaterialPreferences()
        self._material_preset_name = ""
        self._history_store: HistoryStore | None = None
        self._history_init_attempted = False
        self._history_generation = 0
        self._history_page = 0
        self._history_total = 0
        self._history_search = ""
        self._history_tool_id = ""
        self._history_date_filter = "全部时间"
        self._history_busy = False
        self._history_message = ""
        self._history_selected: TaskDetail | None = None
        self._history_detail: dict[str, Any] = {}
        self._trash_generation = 0
        self._trash_busy = False
        self._trash_search = ""
        self._trash_items: list[Any] = []
        self._trash_row_index: list[tuple[dict[str, Any], str]] = []
        self._trash_visible_rows: list[dict[str, Any]] = []
        self._trash_applied_query: str | None = None
        self._trash_selected_id = ""
        self._trash_selected_row = -1
        self._update_busy = False
        self._download_link_busy = False
        self._update_status = ""
        self._update_progress = -1.0
        self._update_phase = ""
        self._update_manual = False
        self._ready_update: UpdateInfo | None = None
        self._ready_update_package: Path | None = None
        self._update_restart_requested = False
        self._background_update_timer = QTimer(self)
        self._background_update_timer.setInterval(4 * 60 * 60 * 1000)
        self._background_update_timer.timeout.connect(self.requestStartupUpdateCheck)
        self._release_notes_seen_version = ""
        self._release_notes_open = False
        self._startup_notes_pending = False
        self._pending_update: UpdateInfo | None = None
        self._update_cancel_event: threading.Event | None = None
        self._workspace_scan_cancel_event: threading.Event | None = None
        self._workspace_recovery_blocked: bool = False
        self._workspace_recovery_error: str = ""
        self._shutdown_requested = False
        self._shutdown_wait_started = 0.0

        self._ensure_state(self._spec)
        self._sync_input_model()
        self._append_log(self._spec.log_text, "info")

        self._projectOpened.connect(self._apply_project_open)
        self._projectOpenFailed.connect(self._apply_project_error)
        self._workspaceItemsReady.connect(self._apply_workspace_items)
        self._workspaceChildrenReady.connect(self._apply_workspace_children)
        self._logIncoming.connect(self._append_log)
        self._runProgress.connect(self._apply_run_progress)
        self._runSuccess.connect(self._apply_run_success)
        self._runError.connect(self._apply_run_error)
        self._runStopped.connect(self._apply_run_stopped)
        self._runFinished.connect(self._apply_run_finished)
        self._previewReady.connect(self._apply_preview)
        self._previewFailed.connect(self._apply_preview_error)
        self._salaryInspectionReady.connect(self._apply_salary_inspection)
        self._workspaceImportFinished.connect(self._apply_workspace_import_result)
        self._historyListReady.connect(self._apply_history_list)
        self._historyDetailReady.connect(self._apply_history_detail)
        self._historyActionFinished.connect(self._apply_history_action)
        self._trashReady.connect(self._apply_trash_list)
        self._trashActionFinished.connect(self._apply_trash_action)
        self._updateResult.connect(self._apply_update_result)
        self._downloadLinkResult.connect(self._apply_download_link)
        self._updateProgressIncoming.connect(self._apply_update_progress)
        self._updatePhaseIncoming.connect(self._apply_update_phase)
        # Phase changes also refresh the footer; byte progress must not fan
        # out into selection checks and result models across the whole UI.
        self.updateChanged.connect(self.updateProgressChanged.emit)
        self._inputItemsReady.connect(self._apply_input_items)
        self._selectionReady.connect(self._apply_selection)
        self._dropPreviewResult.connect(self._apply_drop_preview)
        for state_signal in (self.specChanged, self.formRevisionChanged, self.projectChanged,
                             self.busyChanged, self.workspaceBusyChanged, self.updateChanged):
            state_signal.connect(self._selection_environment_changed)
        self._invocationReady.connect(self._apply_invocation)
        self._startupReady.connect(self._apply_startup)

        self._search_timer = QTimer(self)
        self._search_timer.setSingleShot(True)
        self._search_timer.setInterval(300)
        self._search_timer.timeout.connect(self.refreshWorkspace)
        self.specChanged.connect(self.runButtonTextChanged.emit)
        self.busyChanged.connect(self.runButtonTextChanged.emit)
        self._run_progress_timer = QTimer(self)
        self._run_progress_timer.setInterval(1000)
        self._run_progress_timer.timeout.connect(self._refresh_run_progress_clock)
        self._run_progress_flush_timer = QTimer(self)
        self._run_progress_flush_timer.setSingleShot(True)
        self._run_progress_flush_timer.setInterval(100)
        self._run_progress_flush_timer.timeout.connect(self._flush_material_progress)
        self._incoming_progress_timer = QTimer(self)
        self._incoming_progress_timer.setInterval(100)
        self._incoming_progress_timer.timeout.connect(self._drain_run_progress)

        self._ai_session = None
        self._ai_settings = None
        self._ai_chat_model = AiChatModel(self)
        self._ai_attachment_model = AiAttachmentModel(self)
        self._ai_conversation_model = AiConversationModel(self)
        self._ai_conversation_store = None
        self._ai_conversation = None
        self._ai_activated = False
        self._ai_busy = False
        self._ai_testing = False
        self._ai_preparing = False
        self._ai_attachment_generation = 0
        self._ai_draft = ""
        self._ai_history_query = ""
        # 等待首个字时轮流显示的状态文案：按这一轮实际发出去的附件类型生成，
        # 每轮换一组（见 hr_toolkit.ai.status）。
        self._ai_status_phrases: list[str] = []
        self._aiDeltaIncoming.connect(self._apply_ai_delta)
        self._aiFinishedIncoming.connect(self._apply_ai_finished)
        self._aiAttachmentsReady.connect(self._apply_ai_attachments)
        self.aiTestFinished.connect(self._ai_test_finished)
        # 主题切换后要重算富文本里的表格/代码底色，否则暗色下会白底黑字。
        self._presentation.changed.connect(self._rerender_ai_messages)

    def _state_key(self) -> tuple[str, str]:
        return self._spec.nav_id, self._spec.variant

    def _ensure_state(self, spec) -> None:
        key = (spec.nav_id, spec.variant)
        if key not in self._form_states:
            values = default_values(spec)
            if spec.tool_id == "material_collector":
                values["material_types"] = list(self._material_preferences.available_materials)
            self._form_states[key] = values
        self._input_states.setdefault(key, [])
        self._support_states.setdefault(key, "")

    @constant_property(str)
    def appVersion(self) -> str:
        return __version__

    @constant_property(str)
    def updateIconSource(self) -> str:
        from hr_toolkit._icon_data import APP_ICON_PNGS_BASE64
        return "data:image/png;base64," + max(APP_ICON_PNGS_BASE64.values(), key=len)

    @constant_property("QVariantList")
    def navGroups(self):
        return [
            {
                "name": group,
                "items": [{"id": tool_id, "label": label} for tool_id, label in items],
            }
            for group, items in NAV_GROUPS
        ]

    @constant_property("QVariantList")
    def tutorialGroups(self):
        return tutorial_groups()

    @Property(str, notify=specChanged)
    def currentTool(self) -> str:
        return self._spec.nav_id

    @Property(str, notify=specChanged)
    def currentVariant(self) -> str:
        return self._spec.variant

    @Property(str, notify=specChanged)
    def toolTitle(self) -> str:
        return self._spec.title

    @Property(str, notify=specChanged)
    def toolDescription(self) -> str:
        return self._spec.description

    @Property(str, notify=specChanged)
    def toolGroup(self) -> str:
        return self._spec.group

    @Property(str, notify=specChanged)
    def inputLabel(self) -> str:
        return self._spec.input_label

    @Property(str, notify=specChanged)
    def inputHint(self) -> str:
        return self._spec.input_hint

    @Property(str, notify=specChanged)
    def inputDropTitle(self) -> str:
        return self._spec.input_drop_title

    @Property(bool, notify=specChanged)
    def inputAllowsFiles(self) -> bool:
        return self._spec.input_mode != "directory_single"

    @Property(bool, notify=specChanged)
    def inputAllowsFolder(self) -> bool:
        return self._spec.input_mode != "excel_single"

    @Property(bool, notify=specChanged)
    def inputAllowsMultiple(self) -> bool:
        return self._spec.input_mode == "excel_archive_multi"

    @Property(str, notify=specChanged)
    def supportLabel(self) -> str:
        if self._spec.tool_id == "folder_rename" and self._form_states[self._state_key()].get("rename_mode") == "excel_map":
            return "原文件名 → 新名称映射表"
        return self._spec.support_label

    @Property(str, notify=specChanged)
    def supportButtonText(self) -> str:
        return self._spec.support_button

    @Property(bool, notify=specChanged)
    def hasSupportField(self) -> bool:
        if not self._spec.support_id:
            return False
        if self._spec.tool_id == "folder_rename":
            return self._form_states[self._state_key()].get("rename_mode") in {"excel", "excel_map"}
        return True

    @Property(bool, notify=specChanged)
    def supportAllowsFolder(self) -> bool:
        return self._spec.support_mode in {"excel_or_folder", "excel_archive_or_folder"}

    @Property(str, notify=supportChanged)
    def supportPath(self) -> str:
        return self._support_states[self._state_key()]

    @Property("QVariantList", notify=specChanged)
    def variants(self):
        specs = variants_for(self._spec.nav_id)
        if len(specs) < 2:
            return []
        labels = {
            ("personnel_change_merge", "merge"): "异动汇总",
            ("personnel_change_merge", "roster"): "花名册更新",
            ("personnel_change_merge", "reconcile"): "流程核对",
            ("archive_import", "import"): "档案入库",
            ("archive_import", "export"): "档案表生成",
        }
        return [
            {"id": item.variant, "label": labels[(item.nav_id, item.variant)]}
            for item in specs
        ]

    @Property("QVariantList", notify=formRevisionChanged)
    def formFields(self):
        values = self._form_states[self._state_key()]
        payload = []
        for source in self._spec.fields:
            field = dict(source)
            if (self._spec.tool_id == "folder_rename"
                    and values.get("rename_mode", "append") in {"append", "remove"}
                    and field["id"] == "target_name"):
                field["label"] = "姓名/原名称（可选）"
                field["placeholder"] = "留空处理所选文件类型的全部项目"
            if self._spec.tool_id == "folder_rename" and values.get("rename_mode") == "replace_text":
                if field["id"] == "rename_text":
                    field["label"] = "原文字"
                elif field["id"] == "replacement_name":
                    field["label"] = "替换为"
            if field.get("kind") == "date_range":
                field["startValue"] = values.get(field["startId"], "")
                field["endValue"] = values.get(field["endId"], "")
            else:
                field["value"] = values.get(field["id"], field.get("default", ""))
            field["visible"] = self._field_visible(field["id"], values)
            if field["kind"] == "materials":
                selected = set(values.get("material_types") or [])
                field["options"] = [
                    {"label": name, "value": name, "selected": name in selected}
                    for name in self._material_preferences.available_materials
                ]
            payload.append(field)
        return payload

    def _field_visible(self, field_id: str, values: dict[str, Any]) -> bool:
        if self._spec.tool_id == "folder_rename":
            mode = values.get("rename_mode") or "append"
            if field_id in {"source_column", "target_column"}:
                return mode == "excel_map"
            if field_id in {"trim_spaces", "collapse_spaces", "normalize_separators"}:
                return mode == "normalize"
            if field_id == "target_name":
                return mode in {"append", "remove", "replace"}
            if field_id == "rename_text":
                return mode in {"append", "remove", "replace_text"}
            if field_id == "replacement_name":
                return mode in {"replace", "replace_text"}
        if self._spec.tool_id == "material_collector" and field_id == "material_types":
            return not bool(values.get("collect_all", True))
        return True

    @Property(int, notify=formRevisionChanged)
    def formRevision(self) -> int:
        return self._form_revision

    @constant_property(QObject)
    def inputModel(self):
        return self._input_model

    @constant_property(QObject)
    def logModel(self):
        return self._log_model

    @constant_property(QObject)
    def workspaceModel(self):
        return self._workspace_model

    @constant_property(QObject)
    def historyModel(self):
        return self._history_model

    @constant_property(QObject)
    def trashModel(self):
        return self._trash_model

    @Property(bool, notify=historyChanged)
    def historyBusy(self) -> bool:
        return self._history_busy

    @Property(str, notify=historyChanged)
    def historyMessage(self) -> str:
        return self._history_message

    @Property(str, notify=historyChanged)
    def historyPageText(self) -> str:
        pages = max(1, (self._history_total + HISTORY_PAGE_SIZE - 1) // HISTORY_PAGE_SIZE)
        return f"第 {min(self._history_page + 1, pages)} / {pages} 页"

    @Property(bool, notify=historyChanged)
    def historyHasPrevious(self) -> bool:
        return self._history_page > 0

    @Property(bool, notify=historyChanged)
    def historyHasNext(self) -> bool:
        return (self._history_page + 1) * HISTORY_PAGE_SIZE < self._history_total

    @Property("QVariantMap", notify=historyChanged)
    def historyDetail(self):
        return dict(self._history_detail)

    @constant_property("QVariantList")
    def historyToolOptions(self):
        values = [{"label": "全部功能", "value": ""}]
        seen: set[str] = set()
        for _group, items in NAV_GROUPS:
            for tool_id, label in items:
                if tool_id not in seen:
                    values.append({"label": label, "value": tool_id})
                    seen.add(tool_id)
        return values

    @constant_property("QVariantList")
    def historyDateOptions(self):
        return ["全部时间", "今天", "最近7天", "最近30天", "今年"]

    @Property(bool, notify=trashChanged)
    def trashBusy(self) -> bool:
        return self._trash_busy

    @Property(str, notify=trashChanged)
    def trashSelectedId(self) -> str:
        return self._trash_selected_id

    @Property(int, notify=trashChanged)
    def trashSelectedRow(self) -> int:
        return self._trash_selected_row

    @Property(bool, notify=materialChanged)
    def materialEditorAvailable(self) -> bool:
        return self._spec.tool_id == "material_collector"

    @Property("QVariantList", notify=materialChanged)
    def materialPresets(self):
        return list(self._material_preferences.preset_names)

    @Property("QVariantList", notify=materialChanged)
    def customMaterials(self):
        return list(self._material_preferences.custom_materials)

    @Property(str, notify=materialChanged)
    def materialPresetName(self) -> str:
        return self._material_preset_name

    @Property(bool, notify=updateChanged)
    def updateBusy(self) -> bool:
        return self._update_busy

    @Property(bool, notify=downloadLinkChanged)
    def downloadLinkBusy(self) -> bool:
        return self._download_link_busy

    @Property(bool, notify=updateChanged)
    def updateReady(self) -> bool:
        return self._ready_update is not None and self._ready_update_package is not None

    @Property(bool, notify=updateChanged)
    def updateBlocksTools(self) -> bool:
        return self.updateReady or (
            self._update_busy and self._update_phase in ("preparing", "downloading", "verifying", "launching")
        )

    @Property(str, notify=updateChanged)
    def updateBlockMessage(self) -> str:
        if self.updateReady:
            return "新版本已准备好，请先点击左下角“重启以更新”。"
        return "正在下载或校验更新，暂不能开始工具处理，请等待完成后重启以更新。"

    @Property(bool, notify=updateChanged)
    def updateBackground(self) -> bool:
        return not self._update_manual

    @Property(bool, notify=updateChanged)
    def updateRestarting(self) -> bool:
        return self._update_restart_requested

    @Property(str, notify=updateChanged)
    def updateVersion(self) -> str:
        info = self._ready_update or self._pending_update
        return info.version if info else ""

    @Property(str, notify=updateProgressChanged)
    def updateStatus(self) -> str:
        return self._update_status

    @Property(float, notify=updateProgressChanged)
    def updateProgress(self) -> float:
        return self._update_progress

    @Property(str, notify=updateChanged)
    def updatePhase(self) -> str:
        return self._update_phase

    @Property(bool, notify=updateChanged)
    def updateCanCancel(self) -> bool:
        return self._update_busy and self._update_cancel_event is not None and self._update_phase in ("preparing", "downloading", "verifying")

    @Property(bool, notify=busyChanged)
    def busy(self) -> bool:
        return self._busy

    @Property(bool, notify=runProgressChanged)
    def runProgressVisible(self) -> bool:
        return self._run_progress_visible

    @Property(int, notify=runProgressChanged)
    def runProgressCurrent(self) -> int:
        return self._run_progress_current

    @Property(int, notify=runProgressChanged)
    def runProgressTotal(self) -> int:
        return self._run_progress_total

    @Property(str, notify=runProgressChanged)
    def runProgressMessage(self) -> str:
        return self._run_progress_message

    @Property(int, notify=runProgressChanged)
    def runProgressElapsed(self) -> int:
        return self._run_progress_elapsed

    @Property(int, notify=runProgressChanged)
    def runProgressWaitSeconds(self) -> int:
        return self._run_progress_wait

    @Slot()
    def _refresh_run_progress_clock(self) -> None:
        if not self._run_progress_visible or not self._busy:
            return
        now = time.monotonic()
        self._run_progress_elapsed = int(now - self._run_progress_started)
        self._run_progress_wait = int(now - self._run_progress_updated)
        # 时钟只解释等待时间，绝不驱动完成数或百分比。
        self.runProgressChanged.emit()

    @Property(str, notify=runButtonTextChanged)
    def runButtonText(self) -> str:
        return ("正在安全停止…" if self._stop_requested else "停止处理") if self._busy else self._spec.run_text

    @Property(str, notify=projectChanged)
    def projectName(self) -> str:
        if self._project_store is None:
            return "未打开工作项目"
        return str(self._project_store.workspace.name)

    @Property(str, notify=projectChanged)
    def projectPath(self) -> str:
        return "" if self._project_path is None else str(self._project_path)

    @Property(bool, notify=projectChanged)
    def hasProject(self) -> bool:
        return self._project_store is not None

    @Property(bool, notify=projectChanged)
    def projectWritable(self) -> bool:
        if self._workspace_recovery_blocked:
            return False
        return bool(self._project_store is not None and self._project_store.writable)

    @constant_property(str)
    def defaultProjectName(self) -> str:
        return default_workspace_project_name()

    @Property(str, notify=projectChanged)
    def defaultProjectParent(self) -> str:
        if self._recent_projects:
            return str(self._recent_projects[0].parent)
        home = user_home_dir()
        documents = home / "Documents"
        return str(documents if documents.is_dir() else home)

    @Property("QVariantList", notify=projectChanged)
    def recentProjects(self):
        return [
            {"name": path.name, "path": str(path)}
            for path in self._recent_projects[:8]
        ]

    @Property(bool, notify=workspaceChanged)
    def workspaceExpanded(self) -> bool:
        return self._workspace_expanded

    @Property(str, notify=workspaceChanged)
    def workspaceScope(self) -> str:
        return self._workspace_scope

    @Property(bool, notify=workspaceBusyChanged)
    def workspaceBusy(self) -> bool:
        return self._workspace_busy

    @Property(bool, notify=workspaceSelectionChanged)
    def workspaceSelectionAvailable(self) -> bool:
        return self._workspace_selected_item is not None

    @Property(str, notify=workspaceSelectionChanged)
    def workspaceSelectedPath(self) -> str:
        item = self._workspace_selected_item
        return "" if item is None else str(item.get("path") or "")

    @Property(str, notify=workspaceSelectionChanged)
    def workspaceSelectedName(self) -> str:
        item = self._workspace_selected_item
        return "" if item is None else str(item.get("name") or "")

    @Property(str, notify=workspaceSelectionChanged)
    def workspaceSelectedDetail(self) -> str:
        item = self._workspace_selected_item
        if item is None:
            return "双击可以打开文件；文件夹可展开查看。"
        detail = str(item.get("detail") or "").strip()
        if detail:
            return detail
        return "文件夹" if item.get("isDir") else "文件"

    @Property(bool, notify=lastResultChanged)
    def canOpenLastResult(self) -> bool:
        return bool(self._last_result_dir is not None and self._result_context == (self._state_key(), self._project_generation))

    @Property(bool, notify=lastResultChanged)
    def canOpenPrimaryResult(self) -> bool:
        return (self.canOpenLastResult and len(self._result_files) == 1
                and self._result_files[0].suffix.lower() in EXCEL_SUFFIXES)

    def _notify_last_result_changed(self, *, force: bool = False) -> None:
        availability = (self.canOpenLastResult, self.canOpenPrimaryResult)
        changed = availability != self._last_result_availability
        # Store before emitting: QML or other synchronous receivers can read
        # the result state while handling the notification.
        self._last_result_availability = availability
        if force or changed:
            self.lastResultChanged.emit()

    @Property(int, notify=lastResultChanged)
    def resultNoticeCount(self) -> int:
        return len(self._result_notice_rows) if self.canOpenLastResult else 0

    @Property("QVariantList", notify=lastResultChanged)
    def resultNoticeCategories(self):
        if not self.canOpenLastResult:
            return []
        return [{"name": "全部", "count": len(self._result_notice_rows)}] + [
            {"name": name, "count": self._result_notice_counts[name]}
            for name in ("业务核对", "运行提醒", "运行信息", "其他提醒") if self._result_notice_counts.get(name)]

    @Property(str, notify=lastResultChanged)
    def resultNoticeFilter(self) -> str:
        return self._result_notice_filter

    @Slot(str)
    def setResultNoticeFilter(self, category: str) -> None:
        if not self.canOpenLastResult or category not in {"全部", *self._result_notice_counts}:
            return
        if category == self._result_notice_filter:
            return
        if category == "全部":
            rows = self._result_notice_rows
        else:
            rows = self._result_notice_groups.get(category)
            if rows is None:
                rows = [row for row in self._result_notice_rows if row["category"] == category]
                self._result_notice_groups[category] = rows
        self._result_notice_filter = category
        self._result_notices.set_items(rows)
        self._notify_last_result_changed(force=True)

    @staticmethod
    def _notice_category(tool_id: str, text: str) -> str:
        # Only classify known producer messages, not generic keyword matches.
        # Unknown wording remains visible as "other"; never alter source text.
        if tool_id == "material_collector":
            if re.fullmatch(r"(?:OCR 智能索引缓存：命中 [0-9]+ 次，实时识别 [0-9]+ 次|无序资料 OCR 索引：复用 [0-9]+ 个，新增识别 [0-9]+ 个)(?:，缓存文件：[^\n]+)?", text):
                return "运行信息"
            if text.startswith(("OCR 缓存写入失败：", "OCR 索引缓存写入失败：")):
                return "运行提醒"
            if text.startswith(("照片人员归属冲突，未提取：", "合同人员归属冲突，未提取：", "已复制原件但未完成身份核对：")):
                return "业务核对"
        if tool_id == "insurance_ledger" and text.startswith("花名册身份证重复但姓名不同："):
            return "业务核对"
        return "其他提醒"

    @constant_property(QObject)
    def resultNoticeModel(self):
        return self._result_notices

    @Slot()
    def copyResultNotices(self) -> None:
        if self.canOpenLastResult:
            QGuiApplication.clipboard().setText("\n".join(self._presentation.translate(str(row["text"]), self._presentation.language) for row in self._result_notice_rows))

    @Property(str, notify=specChanged)
    def lastRunText(self) -> str:
        record = self._last_run_by_key.get(self._state_key())
        if record is None:
            return ""
        stamp, success = record
        return f"上次运行 {stamp} · {'成功' if success else '失败'}"

    @Slot(str)
    def selectTool(self, nav_id: str) -> None:
        if self._busy or nav_id == self._spec.nav_id:
            return
        variant = self._variants.get(nav_id, DEFAULT_VARIANTS.get(nav_id, "default"))
        try:
            spec = spec_for(nav_id, variant)
        except KeyError:
            return
        self._spec = spec
        self._ensure_state(spec)
        self._sync_input_model()
        self._clear_logs()
        self._append_log(spec.log_text, "info")
        self._flush_logs()
        self.specChanged.emit()
        self.materialChanged.emit()
        self.supportChanged.emit()
        self._bump_form_revision()
        if self._workspace_scope == "tool":
            self.refreshWorkspace()

    @Slot(str)
    def selectVariant(self, variant: str) -> None:
        if self._busy or variant == self._spec.variant:
            return
        try:
            spec = spec_for(self._spec.nav_id, variant)
        except KeyError:
            return
        self._variants[self._spec.nav_id] = variant
        self._spec = spec
        self._ensure_state(spec)
        self._sync_input_model()
        self._clear_logs()
        self._append_log(spec.log_text, "info")
        self._flush_logs()
        self.specChanged.emit()
        self.materialChanged.emit()
        self.supportChanged.emit()
        self._bump_form_revision()
        if self._workspace_scope == "tool":
            self.refreshWorkspace()

    @Slot(str, "QVariant")
    def setFieldValue(self, field_id: str, value: Any) -> None:
        state = self._form_states[self._state_key()]
        state[field_id] = value
        if field_id == "use_ocr_cache" and state.get("library_mode") != "flat_ocr":
            state.pop("_saved_use_ocr_cache", None)
        elif field_id == "library_mode":
            if value == "flat_ocr":
                if "_saved_use_ocr_cache" not in state:
                    state["_saved_use_ocr_cache"] = bool(state.get("use_ocr_cache", True))
                state["use_ocr_cache"] = True
            else:
                if "_saved_use_ocr_cache" in state:
                    state["use_ocr_cache"] = state.pop("_saved_use_ocr_cache")
        if field_id in {"rename_mode", "collect_all", "library_mode", "use_ocr_cache"}:
            self.specChanged.emit()
            self._bump_form_revision()

    @Slot(str, str)
    def normalizeDateField(self, field_id: str, text: str) -> None:
        if (self._spec.tool_id != "data_statistics" or self._busy or self.updateBlocksTools
                or field_id not in {"week_start", "week_end", "month_start", "month_end"}):
            return
        role = field_id.split("_", 1)[0] + "_range"
        try:
            normalized = normalize_report_date_text(text)
        except ValueError as exc:
            self._selection_message(role, str(exc), True)
            return  # Retain invalid user text for correction, never substitute today.
        state = self._form_states[self._state_key()]
        if state[field_id] != normalized:
            state[field_id] = normalized
            self._bump_form_revision()
        else:
            self._selection_message(role, "")

    @Slot(str, str)
    def applyDatePreset(self, group: str, preset: str) -> None:
        """Apply the same calendar ranges as the legacy UI."""

        if self._spec.tool_id != "data_statistics" or group not in {"week", "month"}:
            return
        state = self._form_states[self._state_key()]
        start_id = "week_start" if group == "week" else "month_start"
        end_id = "week_end" if group == "week" else "month_end"
        if preset == "clear":
            state[start_id] = ""
            state[end_id] = ""
            self._bump_form_revision()
            return
        today = date.today()
        if preset == "this_month":
            start = today.replace(day=1)
            end = today.replace(day=calendar.monthrange(today.year, today.month)[1])
        elif preset == "last_month":
            end = today.replace(day=1) - timedelta(days=1)
            start = end.replace(day=1)
        elif group == "week" and preset in {"this_week", "last_week"}:
            monday = today - timedelta(days=today.weekday())
            if preset == "this_week":
                start = monday
                end = monday + timedelta(days=6)
            else:
                start = monday - timedelta(days=7)
                end = monday - timedelta(days=1)
        else:
            return
        state[start_id] = start.isoformat()
        state[end_id] = end.isoformat()
        self._bump_form_revision()

    @Slot(str, bool)
    def toggleMaterial(self, name: str, selected: bool) -> None:
        state = self._form_states[self._state_key()]
        values = list(state.get("material_types") or [])
        if selected and name not in values:
            values.append(name)
        elif not selected and name in values:
            values.remove(name)
        state["material_types"] = values

    @Slot()
    def selectAllMaterials(self) -> None:
        self._form_states[self._state_key()]["material_types"] = list(
            self._material_preferences.available_materials
        )
        self._bump_form_revision()

    @Slot()
    def clearMaterials(self) -> None:
        self._form_states[self._state_key()]["material_types"] = []
        self._bump_form_revision()

    def _selected_materials(self) -> list[str]:
        values = self._form_states.get(("material_collector", "default"), {})
        selected = set(values.get("material_types") or [])
        return [
            name
            for name in self._material_preferences.available_materials
            if name in selected
        ]

    def _material_mutated(self) -> None:
        state = self._form_states.get(("material_collector", "default"))
        if state is not None:
            available = set(self._material_preferences.available_materials)
            state["material_types"] = [
                name for name in state.get("material_types", []) if name in available
            ]
        self._save_workspace_preferences()
        self._bump_form_revision()
        self.materialChanged.emit()

    @Slot(str, result=bool)
    def isCustomMaterialPreset(self, name: str) -> bool:
        return name in self._material_preferences.custom_presets

    @Slot(str)
    def setMaterialPresetName(self, name: str) -> None:
        if name not in self._material_preferences.preset_names:
            return
        self._material_preset_name = name
        self.materialChanged.emit()

    @Slot(str)
    def applyMaterialPreset(self, name: str) -> None:
        materials = self._material_preferences.get_preset(name)
        if materials is None:
            self.notificationRequested.emit("预设不可用", "这个预设不存在或已经被删除。", "warning")
            return
        self._material_preset_name = name
        state = self._form_states[("material_collector", "default")]
        state["material_types"] = list(materials)
        state["collect_all"] = False
        self._bump_form_revision()
        self.materialChanged.emit()

    @Slot()
    def requestAddCustomMaterial(self) -> None:
        token = f"material-add:{time.monotonic_ns()}"
        self._pending_text_action = token
        self.textInputRequested.emit(
            "添加自定义材料",
            "输入材料名称（例如：户口本、体检报告）",
            "",
            token,
        )

    @Slot(str)
    def requestDeleteCustomMaterial(self, name: str) -> None:
        if name not in self._material_preferences.custom_materials:
            self.notificationRequested.emit("请选择材料", "请先选择要删除的自定义材料。", "warning")
            return
        referenced_by = [
            preset
            for preset, materials in self._material_preferences.custom_presets.items()
            if name in materials
        ]
        suffix = ""
        if referenced_by:
            suffix = "\n\n删除后会自动清理这些预设中的引用：" + "、".join(referenced_by)
        token = f"material-delete:{time.monotonic_ns()}"
        self._pending_confirmation = token
        self._pending_confirmation_action = ("material-delete", name)
        self.confirmationRequested.emit("确认删除材料", f"确定删除自定义材料“{name}”吗？{suffix}", token)

    @Slot()
    def requestCreateMaterialPreset(self) -> None:
        if not self._selected_materials():
            self.notificationRequested.emit("没有选择材料", "请先勾选至少一种材料，再保存为预设。", "warning")
            return
        token = f"preset-create:{time.monotonic_ns()}"
        self._pending_text_action = token
        self.textInputRequested.emit("保存自定义预设", "输入预设名称", "", token)

    @Slot(str)
    def updateMaterialPreset(self, name: str) -> None:
        try:
            saved = self._material_preferences.save_preset(
                name,
                self._selected_materials(),
                replacing=name,
            )
        except ValueError as exc:
            self.notificationRequested.emit("无法更新预设", str(exc), "warning")
            return
        self._material_preset_name = saved
        self._material_mutated()
        self.notificationRequested.emit("预设已更新", f"“{saved}”已按当前勾选更新。", "success")

    @Slot(str)
    def requestRenameMaterialPreset(self, name: str) -> None:
        if self._material_preferences.is_builtin_preset(name):
            self.notificationRequested.emit("内置预设不能重命名", "内置预设会一直保留；自定义预设可以重命名。", "info")
            return
        token = f"preset-rename:{time.monotonic_ns()}"
        self._pending_text_action = token
        self._pending_text_payload = name
        self.textInputRequested.emit("重命名预设", "输入新的预设名称", name, token)

    @Slot(str)
    def requestDeleteMaterialPreset(self, name: str) -> None:
        if self._material_preferences.is_builtin_preset(name):
            self.notificationRequested.emit("内置预设不能删除", "内置预设会一直保留；自定义预设可以删除。", "info")
            return
        token = f"preset-delete:{time.monotonic_ns()}"
        self._pending_confirmation = token
        self._pending_confirmation_action = ("preset-delete", name)
        self.confirmationRequested.emit("确认删除预设", f"确定删除自定义预设“{name}”吗？\n\n材料本身不会被删除。", token)

    @Slot(str, str)
    def submitTextAction(self, token: str, value: str) -> None:
        if token != self._pending_text_action:
            return
        self._pending_text_action = None
        try:
            if token.startswith("material-add:"):
                material = self._material_preferences.add_material(value)
                state = self._form_states[("material_collector", "default")]
                state.setdefault("material_types", []).append(material)
                self._material_mutated()
                self.notificationRequested.emit("材料已添加", f"已添加自定义材料“{material}”。", "success")
            elif token.startswith("preset-create:"):
                saved = self._material_preferences.save_preset(value, self._selected_materials())
                self._material_preset_name = saved
                self._material_mutated()
                self.notificationRequested.emit("预设已保存", f"已保存“{saved}”。", "success")
            elif token.startswith("preset-rename:"):
                current = str(getattr(self, "_pending_text_payload", ""))
                saved = self._material_preferences.rename_preset(current, value)
                self._material_preset_name = saved
                self._material_mutated()
        except ValueError as exc:
            self.notificationRequested.emit("无法保存", str(exc), "warning")

    def _bump_form_revision(self) -> None:
        self._form_revision += 1
        feedback = self._selection_messages.get(self._state_key(), {})
        feedback.pop("week_range", None)
        feedback.pop("month_range", None)
        feedback.pop("material_types", None)
        if self._spec.tool_id == "material_collector" and str(self._form_states[self._state_key()].get("target_input") or "").strip():
            feedback.pop("support", None)
        # The connected environment handler invalidates stale requests and
        # emits selectionStateChanged synchronously for this revision.
        self.formRevisionChanged.emit()

    def _dialog_parent(self):
        from .compat import QApplication

        return QApplication.activeWindow()

    def _file_dialog_initial_dir(self, *, role: str = "general") -> str:
        if role == "new_project":
            try:
                parent = Path(self.defaultProjectParent).expanduser().absolute()
                if parent.is_dir():
                    return str(parent)
            except Exception:
                pass

        if self._last_selected_dir is not None:
            try:
                cand = Path(self._last_selected_dir).expanduser().absolute()
                if cand.is_dir():
                    return str(cand)
            except Exception:
                pass
        if self._project_path is not None:
            try:
                cand = Path(self._project_path).expanduser().absolute()
                if cand.is_dir():
                    return str(cand)
            except Exception:
                pass
        try:
            fallback = desktop_dir()
            if fallback and Path(fallback).is_dir():
                return str(Path(fallback).expanduser().absolute())
        except Exception:
            pass
        # An empty initial directory lets the native chooser use its own
        # default if every optional remembered/system location is unavailable.
        return ""

    def _remember_file_dialog_path(
        self, selected: str | Path | list[str | Path] | tuple[str | Path, ...] | None
    ) -> None:
        if not selected:
            return
        item = selected[0] if isinstance(selected, (list, tuple)) else selected
        if not item:
            return
        path = absolute_path_hint(item)
        if path is None:
            return
        try:
            folder = path if path.is_dir() else path.parent
            if folder.is_dir():
                self._last_selected_dir = folder
                self._save_workspace_preferences()
        except Exception:
            pass

    @staticmethod
    def _bounded_recent_selections(items) -> list[dict[str, str]]:
        # Metadata only: never stat a network drive while loading/showing history.
        result, seen = [], set()
        counts = {"file": 0, "folder": 0}
        for item in items[:90] if isinstance(items, list) else []:
            if (not isinstance(item, dict) or not isinstance(item.get("kind"), str)
                    or item["kind"] not in counts):
                continue
            value = item.get("path")
            if not isinstance(value, str) or not value or len(value) > 32768:
                continue
            path = absolute_path_hint(value)
            if path is None:
                continue
            kind = item["kind"]
            key = (kind, os.path.normcase(str(path)))
            if key in seen or counts[kind] >= (20 if kind == "file" else 10):
                continue
            seen.add(key)
            counts[kind] += 1
            result.append({"path": str(path), "kind": kind})
        return result

    @Slot(str, str, result="QVariantList")
    def recentSelectionItems(self, role: str, kind: str):
        if role not in {"input", "support"} or (role == "support" and not self.hasSupportField):
            return []
        mode = selection_mode(self._spec, role)
        return [{**item, "name": Path(item["path"]).name or item["path"]}
                for item in self._tool_recent_selections() if item["kind"] == kind
                and (kind == "folder" or accepts_file_name(Path(item["path"]), mode))]

    def _tool_recent_selections(self):
        # Navigation tools own history; variants of the same tool share it.
        return self._recent_selections.get(self._spec.nav_id, [])

    @Slot(str, str)
    def removeRecentSelection(self, path: str, kind: str) -> None:
        self._recent_selections[self._spec.nav_id] = [item for item in self._tool_recent_selections()
                                                     if (item["path"], item["kind"]) != (path, kind)]
        self._save_workspace_preferences()
        self.recentSelectionsChanged.emit()

    @Slot()
    def clearRecentSelections(self) -> None:
        self._recent_selections.pop(self._spec.nav_id, None)
        self._save_workspace_preferences()
        self.recentSelectionsChanged.emit()

    @Slot(str, str, str, bool)
    def useRecentSelection(self, role: str, path: str, action: str, append: bool) -> None:
        if (not self.selectionEnabled or role not in {"input", "support"}
                or (role == "support" and not self.hasSupportField)):
            return
        kind = "file" if action == "file" else "folder"
        if action not in {"file", "browse_files", "browse_folder"} or not any(
                item["path"] == path and item["kind"] == kind for item in self._tool_recent_selections()):
            return
        allows_files = self.inputAllowsFiles if role == "input" else True
        allows_folder = self.inputAllowsFolder if role == "input" else self.supportAllowsFolder
        if (action in {"file", "browse_files"} and not allows_files
                or action == "browse_folder" and not allows_folder):
            return
        replace = role == "support" or not self.inputAllowsMultiple or (
            self._spec.tool_id == "data_statistics" and not append)
        self._submit_selection(role, [Path(path)], replace=replace,
                               recent_action=action, recent_append=append)

    @Slot(str, str, str)
    def openRecentSelection(self, path: str, kind: str, action: str) -> None:
        if (not self.selectionEnabled or self._recent_location_pending
                or kind not in {"file", "folder"} or action not in {"open", "location"}
                or not any(item["path"] == path and item["kind"] == kind
                           for item in self._tool_recent_selections())):
            return
        target = Path(path).parent if kind == "file" and action == "location" else Path(path)
        folder = kind == "folder" or action == "location"
        self._recent_location_pending = True

        def worker():
            error = ""
            try:
                if not (target.is_dir() if folder else target.is_file()):
                    raise OSError("unavailable")
                if not self._closed:
                    open_path(target)
            except OSError:
                error = "无法打开最近记录：文件或文件夹已移动、删除、无法访问，或没有可用的打开程序。"
            if not self._closed:
                self._recentLocationReady.emit(error)

        try:
            threading.Thread(target=worker, daemon=True, name="HRToolkit-recent-open").start()
        except RuntimeError:
            self._finish_recent_location("暂时无法打开最近记录，请稍后重试。")

    @Slot(str)
    def _finish_recent_location(self, error: str) -> None:
        self._recent_location_pending = False
        if error and not self._closed:
            self.notificationRequested.emit("无法打开资料", error, "warning")

    def _selection_block_reason(self) -> str:
        if self._closed or self._shutdown_requested:
            return "工具正在退出，暂不能添加资料。"
        if self.updateBlocksTools:
            return self.updateBlockMessage
        if self._busy or self._workspace_busy or self._project_opening:
            return "正在处理或保存项目资料，请稍后再添加。"
        return ""

    @Property(bool, notify=selectionStateChanged)
    def selectionEnabled(self) -> bool:
        return self._selection_request is None and not self._selection_block_reason()

    @Property(bool, notify=selectionStateChanged)
    def selectionChecking(self) -> bool:
        return self._selection_request is not None

    @Property(str, notify=specChanged)
    def inputDropHint(self) -> str:
        return "可拖入" + selection_hint(self._spec.input_mode) + "，也可点击选择"

    @Property(str, notify=specChanged)
    def supportDropHint(self) -> str:
        if self._spec.tool_id == "material_collector":
            return "可拖入" + selection_hint(self._spec.support_mode) + "；已填写目标人员时可不选"
        return "可拖入" + selection_hint(self._spec.support_mode) if self.hasSupportField else ""

    @Property("QVariantMap", notify=selectionStateChanged)
    def selectionFeedback(self):
        return {role: {"text": text, "error": error}
                for role, (text, error) in self._selection_messages.get(self._state_key(), {}).items()}

    def _selection_context(self):
        return (self._state_key(), self._project_generation, self._form_revision,
                self._input_generation, self.supportPath)

    def _selection_message(self, role: str, text: str, error: bool = False) -> None:
        self._selection_messages.setdefault(self._state_key(), {})[role] = (text, error)
        self.selectionStateChanged.emit()

    @Slot()
    def _selection_environment_changed(self) -> None:
        source = self._workspace_transfer
        if source and (source["context"] != self._selection_context() or self._selection_block_reason()):
            self._workspace_transfer = None
        request = self._selection_request
        if request and (request["context"] != self._selection_context() or self._selection_block_reason()):
            request["cancel"].set()
        preview = self._drop_preview_request
        if preview and (preview["context"] != self._selection_context() or not self.selectionEnabled):
            self.cancelDropPreview(preview["token"])
        self.selectionStateChanged.emit()
        self._notify_last_result_changed()

    @staticmethod
    def _local_drop_paths(urls) -> list[Path]:
        return local_drop_paths(urls)

    def eventFilter(self, watched, event):
        if event.type() in (QEvent.DragEnter, QEvent.Drop):
            self._native_drop_urls = []
            try:
                mime = event.mimeData()
                self._native_drop_urls = native_mime_paths(mime)
                runlog.log_line(f"拖拽元数据：阶段={int(event.type())}，URL数={len(mime.urls())}，"
                                f"候选数={len(self._native_drop_urls)}，格式={list(mime.formats())}")
            except (AttributeError, UnicodeError, LookupError, ValueError) as exc:
                runlog.log_line(f"拖拽路径解码失败：{type(exc).__name__}")
        elif event.type() == QEvent.DragLeave:
            self._native_drop_urls = []
        return False

    @Slot("QVariantList", str, str, result="QVariantList")
    def resolveDropUrls(self, urls, uri_text: str, path_text: str):
        return list(urls) or list(self._native_drop_urls) or text_paths(uri_text) or text_paths(path_text)

    @Slot(str, "QVariantList", result="QVariantMap")
    def describeDrop(self, role: str, urls) -> dict[str, Any]:
        """Only inspect URL metadata here; never touch disk during drag-over."""
        try:
            if not self.selectionEnabled:
                raise ValueError(self._selection_block_reason() or "正在检查上一批资料，请稍后再拖入。")
            if role == "support" and not self.hasSupportField:
                raise ValueError("当前模式没有配套资料输入区。")
            mode = selection_mode(self._spec, role)
            paths = self._local_drop_paths(urls)
            if not paths:
                raise ValueError("拖拽未提供可用文件路径，请点击选择文件；未下载的附件请先保存到本地。")
            if mode != "excel_archive_multi" and len(paths) != 1:
                raise ValueError("这里只接收" + selection_hint(mode) + "，不能一次拖入多项。")
            # File-only targets can reject incompatible names without stat().
            # Targets allowing folders must inspect metadata in the worker:
            # a perfectly valid folder can itself be named "资料.exe".
            if mode in {"excel_single", "excel_file"} and any(path.suffix.lower() not in EXCEL_SUFFIXES for path in paths):
                raise ValueError("不支持此类型，这里只接收 1 个 Excel 文件（.xlsx / .xls）。")
            label = self.inputLabel if role == "input" else self.supportLabel
            replacing = bool(self.supportPath) if role == "support" else (not self.inputAllowsMultiple and bool(self._input_states[self._state_key()]))
            action = "替换" if replacing else "设置" if role == "support" else "添加"
            return {"accepted": True, "message": f"松开后{action}：{label}"}
        except ValueError as exc:
            return {"accepted": False, "message": str(exc)}

    @Slot(str, "QVariantList", result="QVariantMap")
    @Slot(str, "QVariantList", str, result="QVariantMap")
    def beginDropPreview(self, role: str, urls, workspace_token: str = "") -> dict[str, Any]:
        if self._drop_preview_request:
            self.cancelDropPreview(self._drop_preview_request["token"])
        initial = self.describeDrop(role, urls)
        if not initial["accepted"]:
            return {**initial, "pending": False, "token": ""}
        source = None
        if workspace_token:
            source = self._workspace_transfer
            if (not source or source["token"] != workspace_token
                    or source["context"] != self._selection_context()
                    or self._local_drop_paths(urls) != [source["path"]]):
                return {"accepted": False, "pending": False, "token": "",
                        "message": "项目或工具已变化，请重新从项目文件拖入。"}
        self._drop_preview_serial += 1
        token = str(self._drop_preview_serial)
        request = {"token": token, "role": role, "paths": self._local_drop_paths(urls),
                   "mode": selection_mode(self._spec, role), "context": self._selection_context(),
                   "cancel": threading.Event(), "message": initial["message"], "accepted": False, "checked": False,
                   "workspace_source": source}
        self._drop_preview_request = request
        with self._drop_preview_lock:
            # Keep one worker and only the latest waiting hover request. Moving
            # between targets must not create a thread/queue per drag event.
            self._drop_preview_pending = request
            start = not self._drop_preview_running
            self._drop_preview_running = True
        if start:
            try:
                threading.Thread(target=self._check_drop_previews, daemon=True,
                                 name="HRToolkit-drop-preview").start()
            except Exception:
                with self._drop_preview_lock:
                    self._drop_preview_running = False
                self.cancelDropPreview(token)
                return {"accepted": False, "pending": False, "token": "",
                        "message": "暂时无法检查资料，请使用点击选择。"}
        return {"accepted": False, "pending": True, "token": token,
                "message": "正在检查资料类型，请稍候再松手…"}

    def _check_drop_previews(self) -> None:
        while True:
            with self._drop_preview_lock:
                request = self._drop_preview_pending
                self._drop_preview_pending = None
                if request is None or self._closed:
                    self._drop_preview_running = False
                    return
            try:
                self._validate_workspace_source(request.get("workspace_source"))
                validate_selection(request["paths"], request["mode"], request["cancel"].is_set)
                error = ""
            except Exception as exc:
                error = str(exc).replace("本次未添加，原选择保持不变。\n", "无法放入此区域：\n", 1)
            if not self._closed and not request["cancel"].is_set():
                self._dropPreviewResult.emit(request, error)

    @Slot(object, str)
    def _apply_drop_preview(self, request, error: str) -> None:
        if (request is not self._drop_preview_request or request["cancel"].is_set()
                or request["context"] != self._selection_context() or not self.selectionEnabled):
            return
        request["accepted"] = not error
        request["checked"] = True
        self.dropPreviewReady.emit({"token": request["token"], "pending": False,
                                    "accepted": not error, "message": error or request["message"]})

    @Slot(str)
    def cancelDropPreview(self, token: str) -> None:
        request = self._drop_preview_request
        if request is None or request["token"] != token:
            return
        request["cancel"].set()
        self._drop_preview_request = None
        with self._drop_preview_lock:
            if self._drop_preview_pending is request:
                self._drop_preview_pending = None
        self.dropPreviewReady.emit({"token": token, "pending": False, "accepted": False, "message": ""})

    @Slot(str, str, "QVariantList", result=bool)
    def finishDropPreview(self, token: str, role: str, urls) -> bool:
        request = self._drop_preview_request
        if (request is None or request["token"] != token or request["role"] != role
                or (request["checked"] and not request["accepted"]) or request["cancel"].is_set()
                or request["context"] != self._selection_context() or not self.selectionEnabled):
            return False
        try:
            paths = self._local_drop_paths(urls)
        except ValueError:
            return False
        if paths != request["paths"]:
            return False
        source = request.get("workspace_source")
        if source and source is not self._workspace_transfer:
            return False
        self.cancelDropPreview(token)
        # Recheck after drop as a safety net for files deleted/moved since hover.
        self._submit_selection(role, paths, replace=role == "support" or not self.inputAllowsMultiple,
                               workspace_source=source)
        return self.selectionChecking

    @Slot(str, "QVariantList")
    def addDroppedUrls(self, role: str, urls) -> None:
        preview = self.describeDrop(role, urls)
        if not preview["accepted"]:
            if role in {"input", "support"}:
                self._selection_message(role, preview["message"], True)
            return
        self._submit_selection(role, self._local_drop_paths(urls),
                               replace=role == "support" or not self.inputAllowsMultiple)

    def _submit_selection(self, role: str, paths: list[Path], *, replace: bool, workspace_source=None,
                          recent_action: str = "", recent_append: bool = False) -> None:
        if not self.selectionEnabled:
            return
        mode = "directory_single" if recent_action.startswith("browse_") else selection_mode(self._spec, role)
        request = {"context": self._selection_context(), "role": role,
                   "recent_action": recent_action, "recent_append": recent_append,
                   "replace": replace, "cancel": threading.Event()}
        self._selection_request = request
        self._selection_message(role, "正在检查所选资料…")

        def worker() -> None:
            try:
                self._validate_workspace_source(workspace_source)
                if recent_action == "file" and not paths[0].is_file():
                    raise ValueError("最近文件已移动、删除或无法访问，请重新选择。")
                selected = validate_selection(paths, mode, request["cancel"].is_set)
                error = ""
                # Record only bounded metadata, on this existing worker. A failed
                # history lookup must never change the selection result.
                history = []
                for path in selected[:30]:
                    if request["cancel"].is_set():
                        break
                    try:
                        kind = "folder" if path.is_dir() else "file"
                        history.append({"path": str(path), "kind": kind})
                    except OSError:
                        pass
                request["history"] = history
            except Exception as exc:
                selected, error = [], str(exc)
            if not self._closed:
                self._selectionReady.emit(request, selected, error)

        try:
            threading.Thread(target=worker, daemon=True, name="HRToolkit-input-selection").start()
        except Exception:
            self._selection_request = None
            self._selection_message(role, "暂时无法检查资料，请稍后重试。", True)

    @Slot(object, object, str)
    def _apply_selection(self, request, paths, error: str) -> None:
        if request is not self._selection_request:
            return
        self._selection_request = None
        role = request["role"]
        # A user can navigate away and back while a network path is checking.
        if self._closed or request["context"] != self._selection_context():
            self._selection_messages.get(request["context"][0], {}).pop(role, None)
            self.selectionStateChanged.emit()
            return
        if request["cancel"].is_set() or self._selection_block_reason():
            self._selection_message(role, "本次检查已取消，原选择保持不变。")
            return
        if error:
            self._selection_message(role, error, True)
            return
        action = request.get("recent_action", "")
        if action.startswith("browse_"):
            self._selection_message(role, "")
            initial_dir = str(paths[0])
            if role == "input":
                chooser = self._choose_input_files if action == "browse_files" else self._choose_input_folder
                chooser(append=request["recent_append"], initial_dir=initial_dir)
            else:
                chooser = self._choose_support_file if action == "browse_files" else self._choose_support_folder
                chooser(initial_dir=initial_dir)
            return
        if role == "support":
            self._support_states[self._state_key()] = str(paths[0])
            self.supportChanged.emit()
            message = "已设置" + self.supportLabel + "。"
        else:
            before = len(self._input_states[self._state_key()])
            self._set_inputs(paths, replace=request["replace"])
            count = len(self._input_states[self._state_key()])
            added = count if request["replace"] else count - before
            message = f"已{'选择' if request['replace'] else '添加'} {added} 项资料，当前共 {count} 项。"
            if not added:
                message = "这些资料已在列表中，未重复添加。"
        self._selection_message(role, message)
        history = request.get("history", [])
        if history:
            self._recent_selections[self._spec.nav_id] = self._bounded_recent_selections(history + self._tool_recent_selections())
            if action == "file":
                self._last_selected_dir = paths[0].parent
            self._save_workspace_preferences()
            self.recentSelectionsChanged.emit()

    @Slot()
    def cancelSelectionCheck(self) -> None:
        if self._selection_request is not None:
            self._selection_request["cancel"].set()
            self._selection_message(self._selection_request["role"], "已请求取消，等待当前路径检查退出…")

    @Slot()
    def chooseInputFiles(self) -> None:
        self._choose_input_files(append=False)

    @Slot()
    def appendInputFiles(self) -> None:
        self._choose_input_files(append=True)

    def _choose_input_files(self, *, append: bool, initial_dir: str | None = None) -> None:
        if not self.selectionEnabled or not self.inputAllowsFiles:
            return
        parent = self._dialog_parent()
        file_filter = f"Excel 或压缩包 (*.xlsx *.xls {ARCHIVE_FILE_DIALOG_PATTERN});;所有文件 (*)"
        initial_dir = self._file_dialog_initial_dir() if initial_dir is None else initial_dir
        if self._spec.input_mode == "excel_single":
            filename, _selected = self._presentation.file_dialog(QFileDialog.getOpenFileName,
                parent, self._spec.input_drop_title, initial_dir, "Excel 工作簿 (*.xlsx *.xls);;所有文件 (*)"
            )
            paths = [Path(filename)] if filename else []
        else:
            filenames, _selected = self._presentation.file_dialog(QFileDialog.getOpenFileNames,
                parent, self._spec.input_drop_title, initial_dir, file_filter
            )
            paths = [Path(filename) for filename in filenames]
        if paths:
            self._remember_file_dialog_path(paths)
            self._submit_selection("input", paths, replace=not self.inputAllowsMultiple or (self._spec.tool_id == "data_statistics" and not append))

    @Slot()
    def chooseInputFolder(self) -> None:
        self._choose_input_folder(append=False)

    @Slot()
    def appendInputFolder(self) -> None:
        self._choose_input_folder(append=True)

    def _choose_input_folder(self, *, append: bool, initial_dir: str | None = None) -> None:
        if not self.selectionEnabled or not self.inputAllowsFolder:
            return
        selected = self._presentation.file_dialog(QFileDialog.getExistingDirectory,
            self._dialog_parent(), self._spec.input_drop_title, self._file_dialog_initial_dir() if initial_dir is None else initial_dir
        )
        if selected:
            self._remember_file_dialog_path(selected)
            self._submit_selection("input", [Path(selected)], replace=not self.inputAllowsMultiple or (self._spec.tool_id == "data_statistics" and not append))

    def _set_inputs(self, paths: list[Path], *, replace: bool) -> None:
        key = self._state_key()
        current = [] if replace else list(self._input_states[key])
        known = set(current)
        for path in paths:
            if path not in known:
                current.append(path)
                known.add(path)
        self._input_states[key] = current
        self._sync_input_model()

    def _sync_input_model(self) -> None:
        # A virtual view still freezes if its model calls stat() on the GUI
        # thread. Show cached labels immediately and refresh disk metadata in
        # one worker. Rapid tab switches replace the pending request.
        paths = tuple(self._input_states[self._state_key()])
        retained = {path for values in self._input_states.values() for path in values}
        self._input_metadata = {path: item for path, item in self._input_metadata.items() if path in retained}
        self._input_generation += 1
        generation = self._input_generation
        self._input_model.set_items(
            self._input_metadata.get(path) or {
                "name": path.name or str(path), "path": str(path),
                "kind": "file", "detail": path.suffix.lstrip(".").upper() or "文件",
            }
            for path in paths
        )
        with self._input_scan_lock:
            self._input_scan_pending = (generation, paths) if paths else None
            if not paths or self._input_scan_running:
                return
            self._input_scan_running = True
        threading.Thread(target=self._scan_input_metadata, daemon=True,
                         name="HRToolkit-input-metadata").start()

    def _scan_input_metadata(self) -> None:
        while True:
            with self._input_scan_lock:
                request = self._input_scan_pending
                self._input_scan_pending = None
                if request is None or self._closed:
                    self._input_scan_running = False
                    return
            generation, paths = request
            items = []
            for path in paths:
                if self._closed or generation != self._input_generation:
                    break
                try:
                    is_dir = path.is_dir()
                except OSError:
                    is_dir = False
                items.append({
                    "name": path.name or str(path), "path": str(path),
                    "kind": "folder" if is_dir else "file",
                    "detail": "文件夹" if is_dir else path.suffix.lstrip(".").upper() or "文件",
                })
            else:
                if not self._closed:
                    self._inputItemsReady.emit(generation, items)

    @Slot(int, object)
    def _apply_input_items(self, generation: int, items: list[dict[str, Any]]) -> None:
        if self._closed or generation != self._input_generation:
            return
        retained = {path for paths in self._input_states.values() for path in paths}
        self._input_metadata = {path: item for path, item in self._input_metadata.items() if path in retained}
        self._input_metadata.update((Path(item["path"]), item) for item in items)
        # Avoid destroying/recreating visible delegates when labels are unchanged.
        if items != self._input_model.items():
            self._input_model.set_items(items)

    @Slot(int)
    def removeInput(self, index: int) -> None:
        if not self.selectionEnabled:
            return
        values = self._input_states[self._state_key()]
        if 0 <= index < len(values):
            del values[index]
            self._sync_input_model()
            self._selection_message("input", "")

    @Slot()
    def clearInputs(self) -> None:
        if not self.selectionEnabled:
            return
        self._input_states[self._state_key()].clear()
        self._sync_input_model()
        self._selection_message("input", "已清空选择，原文件未删除。")

    @Slot()
    def chooseSupportFile(self) -> None:
        self._choose_support_file()

    def _choose_support_file(self, *, initial_dir: str | None = None) -> None:
        if not self.selectionEnabled or not self.hasSupportField:
            return
        file_filter = "Excel 工作簿 (*.xlsx *.xls);;所有文件 (*)"
        if self._spec.support_mode == "excel_archive_or_folder":
            file_filter = f"Excel 或压缩包 (*.xlsx *.xls {ARCHIVE_FILE_DIALOG_PATTERN});;所有文件 (*)"
        filename, _selected = self._presentation.file_dialog(QFileDialog.getOpenFileName,
            self._dialog_parent(), self._spec.support_label, self._file_dialog_initial_dir() if initial_dir is None else initial_dir, file_filter
        )
        if filename:
            self._remember_file_dialog_path(filename)
            self._submit_selection("support", [Path(filename)], replace=True)

    @Slot()
    def chooseSupportFolder(self) -> None:
        self._choose_support_folder()

    def _choose_support_folder(self, *, initial_dir: str | None = None) -> None:
        if not self.selectionEnabled or not self.hasSupportField or not self.supportAllowsFolder:
            return
        selected = self._presentation.file_dialog(QFileDialog.getExistingDirectory,
            self._dialog_parent(), self._spec.support_label, self._file_dialog_initial_dir() if initial_dir is None else initial_dir
        )
        if selected:
            self._remember_file_dialog_path(selected)
            self._submit_selection("support", [Path(selected)], replace=True)

    @Slot()
    def clearSupport(self) -> None:
        if not self.selectionEnabled:
            return
        self._support_states[self._state_key()] = ""
        self.supportChanged.emit()
        self._selection_message("support", "")

    @Slot(result=str)
    @Slot(str, result=str)
    def chooseProjectParent(self, current: str = "") -> str:
        initial = ""
        current_dir = absolute_path_hint(current)
        try:
            if current_dir is not None and current_dir.is_dir():
                initial = str(current_dir.resolve())
        except (OSError, RuntimeError, ValueError):
            pass
        if not initial:
            initial = self._file_dialog_initial_dir(role="new_project")
        selected = self._presentation.file_dialog(QFileDialog.getExistingDirectory,
            self._dialog_parent(), "选择项目保存位置", initial
        )
        if selected:
            self._remember_file_dialog_path(selected)
            return str(selected)
        return ""

    @Slot()
    def requestCreateProject(self) -> None:
        if self._busy or self._workspace_busy:
            return
        self.projectCreationRequested.emit(self.defaultProjectName, self.defaultProjectParent)

    @Slot(str, str)
    def createProject(self, name: str, parent: str) -> None:
        if self._busy or self._workspace_busy or self._project_opening:
            return
        if self._workspace_recovery_blocked:
            self.notificationRequested.emit(
                "项目未安全恢复",
                "当前项目处于未恢复状态，禁止新建项目。请重新打开当前项目以恢复状态。",
                "error",
            )
            return
        target, error = workspace_project_creation_target(parent, name)
        if error or target is None:
            self.notificationRequested.emit("无法创建项目", error or "项目位置无效。", "error")
            return
        self._project_generation += 1
        generation = self._project_generation
        self._project_opening = True
        self._project_operation = "创建"

        def worker() -> None:
            try:
                store = ProjectStore.create(target, str(name).strip())
            except Exception as exc:
                runlog.log_exception("创建工作项目失败", exc)
                self._projectOpenFailed.emit(generation, workspace_project_create_error_message(exc))
                return
            self._projectOpened.emit(generation, store, str(target))

        threading.Thread(target=worker, daemon=True, name="HRToolkit-create-project").start()

    @Slot()
    def openProjectDialog(self) -> None:
        if self._busy or self._workspace_busy or self._project_opening:
            return
        if self._workspace_recovery_blocked:
            self.notificationRequested.emit(
                "项目未安全恢复",
                "当前项目处于未恢复状态，禁止打开其他项目。请重新打开当前项目以恢复状态。",
                "error",
            )
            return
        selected = self._presentation.file_dialog(QFileDialog.getExistingDirectory,
            self._dialog_parent(), "打开工作项目", self._file_dialog_initial_dir()
        )
        if selected:
            self._remember_file_dialog_path(selected)
            self.openProject(selected)

    @Slot(str)
    def openProject(self, path: str) -> None:
        if self._busy or self._workspace_busy or self._project_opening:
            return
        error = path_text_error(path)
        if error:
            self.notificationRequested.emit("无法打开项目", error, "error")
            return
        if self._workspace_recovery_blocked:
            try:
                target_path = Path(path).resolve()
                current_path = self._project_path.resolve() if self._project_path else None
            except (OSError, RuntimeError, ValueError) as exc:
                runlog.log_exception("校验待恢复项目位置失败", exc)
                self.notificationRequested.emit("无法打开项目", "项目位置不可用，请重新选择原项目文件夹。", "error")
                return
            if target_path != current_path:
                self.notificationRequested.emit(
                    "项目未安全恢复",
                    "当前项目处于未恢复状态，禁止切换到其他项目。请先重新打开当前项目以恢复状态。",
                    "error",
                )
                return
        target = absolute_path_hint(path)
        if target is None:
            self.notificationRequested.emit("无法打开项目", "项目位置不完整，请通过“打开项目”重新选择文件夹。", "error")
            return
        self._project_generation += 1
        generation = self._project_generation
        self._project_opening = True
        self._project_operation = "打开"

        def worker() -> None:
            try:
                store = ProjectStore.open(target, writable=True, read_only_fallback=True)
            except Exception as exc:
                runlog.log_exception("打开工作项目失败", exc)
                self._projectOpenFailed.emit(generation, str(exc))
                return
            self._projectOpened.emit(generation, store, str(path))

        threading.Thread(target=worker, daemon=True, name="HRToolkit-open-project").start()

    @Slot(int, object, str)
    def _apply_project_open(self, generation: int, store: ProjectStore, path: str) -> None:
        if generation != self._project_generation or self._closed:
            store.close()
            return
        previous = self._project_store
        self._project_store = store
        self._project_path = Path(path)
        self._project_opening = False
        self._workspace_recovery_blocked = False
        self._workspace_recovery_error = ""
        if previous is not None:
            try:
                previous.close()
            except Exception as exc:
                runlog.log_exception("关闭旧工作项目失败", exc)
        self._remember_project(self._project_path)
        self._remember_file_dialog_path(self._project_path)
        self._save_workspace_preferences()
        # Discard both cached rows and late list results from the old project.
        self._trash_generation += 1
        self._clear_trash_items()
        self._trash_busy = False
        self.trashChanged.emit()
        self.projectChanged.emit()
        self.refreshWorkspace()
        if not store.writable:
            reason = store.workspace.read_only_reason or "项目当前为只读状态。"
            self.notificationRequested.emit("项目以只读方式打开", reason, "warning")

    @Slot(int, str)
    def _apply_project_error(self, generation: int, message: str) -> None:
        if generation != self._project_generation:
            return
        self._project_opening = False
        self.notificationRequested.emit(f"无法{self._project_operation}项目", message, "error")

    def _remember_project(self, path: Path) -> None:
        self._recent_projects = [path, *(item for item in self._recent_projects if item != path)][:8]

    @staticmethod
    def _settings_path() -> Path:
        return user_app_data_dir("config") / "HRToolkit" / "workspace-ui.json"

    @Slot()
    def start(self) -> None:
        if self._startup_loading or self._closed:
            return
        self._startup_loading = True
        self._startup_cancelled = False
        self._set_busy(True)
        threading.Thread(target=self._load_startup, daemon=True,
                         name="HRToolkit-startup-settings").start()

    def _load_startup(self) -> None:
        state: dict[str, Any] = {}
        if update_check_enabled():
            try:
                cached = load_ready_update(__version__)
                if cached:
                    self._updateResult.emit("restored", cached)
            except Exception as exc:
                runlog.log_line(f"已跳过不可用的更新缓存：{exc}")
        try:
            path = self._settings_path()
            if path.is_file():
                payload = json.loads(path.read_text(encoding="utf-8"))
                if isinstance(payload, dict):
                    state = payload
        except Exception as exc:
            runlog.log_exception("读取项目界面设置失败", exc)
        recent = []
        candidates = state.get("recent_projects", [])
        for value in candidates if isinstance(candidates, list) else []:
            if self._closed or self._shutdown_requested or self._startup_cancelled:
                break
            try:
                candidate = absolute_path_hint(value)
                if candidate is not None and candidate.is_dir() and candidate not in recent:
                    recent.append(candidate)
            except (OSError, ValueError):
                continue
        last_dir = None
        raw_last_dir = state.get("last_selected_dir")
        if raw_last_dir and not self._startup_cancelled:
            try:
                candidate = absolute_path_hint(raw_last_dir)
                if candidate is not None and candidate.is_dir():
                    last_dir = candidate
            except Exception:
                pass
        self._startupReady.emit(state, recent[:8], last_dir)

    @Slot(object, object, object)
    def _apply_startup(self, state: dict[str, Any], recent: list[Path], last_dir) -> None:
        if self._closed or self._shutdown_requested:
            self._set_busy(False)
            return
        self._startup_loading = False
        self._set_busy(False)
        self._presentation.restore(state.get("theme"), state.get("language"))
        self._recent_projects = recent
        if self._startup_cancelled:
            # A cancelled disk check must not discard unexamined history.
            candidates = state.get("recent_projects", [])
            if isinstance(candidates, list):
                self._recent_projects = [path for value in candidates if (path := absolute_path_hint(value)) is not None][:8]
        self._last_selected_dir = last_dir
        # Legacy global entries have no reliable tool ownership (and may contain
        # inferred parent folders). Do not seed them into the new tool histories.
        histories = state.get("recent_selections_by_tool", {})
        self._recent_selections = {
            nav_id: self._bounded_recent_selections(histories.get(nav_id, []))
            for _group, items in NAV_GROUPS for nav_id, _label in items
        } if isinstance(histories, dict) else {}
        self.recentSelectionsChanged.emit()
        self._release_notes_seen_version = str(state.get("release_notes_seen_version") or "")
        self._material_preferences = MaterialPreferences.from_payload(
            state.get("material_preferences")
        )
        salary_profiles = state.get("salary_header_profiles")
        header_rules = state.get("header_name_rules")
        if isinstance(header_rules, dict):
            self._header_name_rules = {str(key): value for key, value in header_rules.items() if isinstance(value, dict)}
        if isinstance(salary_profiles, dict):
            self._salary_header_profiles = {
                str(project): {str(key): value for key, value in rules.items() if isinstance(value, dict)}
                for project, rules in salary_profiles.items() if isinstance(rules, dict)
            }
        preset_names = self._material_preferences.preset_names
        self._material_preset_name = preset_names[0] if preset_names else ""
        material_key = ("material_collector", "default")
        if material_key in self._form_states:
            selected = list(self._form_states[material_key].get("material_types") or [])
            if not selected or selected == list(MaterialPreferences().available_materials):
                self._form_states[material_key]["material_types"] = list(
                    self._material_preferences.available_materials
                )
        self._bump_form_revision()
        self.materialChanged.emit()
        self.projectChanged.emit()
        current = state.get("current_project")
        if current and not self._startup_cancelled:
            path = absolute_path_hint(current)
            if path is not None:
                self.openProject(str(path))
            else:
                self.notificationRequested.emit("请重新选择工作项目", "上次记录的项目位置无效，请通过“打开项目”重新选择。", "warning")
        def cleanup_updates():
            cleanup_stale_update_files()
            cleanup_cached_updates()

        threading.Thread(
            target=cleanup_updates,
            daemon=True,
            name="HRToolkit-update-cleanup",
        ).start()
        self._startup_notes_pending = bool(notes_for_version(__version__)) and (
            not self._release_notes_seen_version
            or is_newer_version(__version__, self._release_notes_seen_version)
        )
        QTimer.singleShot(600, self._show_startup_release_notes)

    def _save_workspace_preferences(self) -> bool:
        # Closing while a disconnected recent path is being checked must not
        # overwrite the unread settings with this controller's defaults.
        if self._startup_loading:
            return False
        try:
            path = self._settings_path()
        except (OSError, RuntimeError, ValueError) as exc:
            runlog.log_exception("读取项目界面设置位置失败", exc)
            return False
        payload: dict[str, Any] = {}
        existing = None
        try:
            if path.is_file():
                existing = json.loads(path.read_text(encoding="utf-8"))
                if isinstance(existing, dict):
                    payload.update(existing)
        except Exception:
            pass
        payload.pop("recent_selections", None)
        payload.update(
            {
                "version": max(2, int(payload.get("version", 0) or 0)),
                "current_project": None if self._project_path is None else str(self._project_path),
                "recent_projects": [str(item) for item in self._recent_projects[:8]],
                "material_preferences": self._material_preferences.to_payload(),
                "last_selected_dir": str(self._last_selected_dir) if self._last_selected_dir is not None else None,
                "recent_selections_by_tool": self._recent_selections,
                "salary_header_profiles": self._salary_header_profiles,
                "header_name_rules": self._header_name_rules,
                "release_notes_seen_version": self._release_notes_seen_version,
                "theme": self._presentation.theme,
                "language": self._presentation.language,
            }
        )
        # Re-read on every call to preserve external settings changes, but do
        # not serialize and replace an already identical on-disk document.
        if isinstance(existing, dict) and payload == existing:
            return True
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            temp = path.with_suffix(".tmp")
            temp.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
            os.replace(temp, path)
            return True
        except Exception as exc:
            runlog.log_exception("保存项目界面设置失败", exc)
            return False

    @Slot()
    def openProjectFolder(self) -> None:
        if self._project_path is not None:
            open_path(self._project_path)

    @Slot(bool)
    def setWorkspaceExpanded(self, expanded: bool) -> None:
        if self._workspace_expanded == bool(expanded):
            return
        self._workspace_expanded = bool(expanded)
        self.workspaceChanged.emit()
        if expanded:
            self.refreshWorkspace()

    @Slot(str)
    def setWorkspaceScope(self, scope: str) -> None:
        if scope not in {"all", "tool"} or scope == self._workspace_scope:
            return
        self._workspace_scope = scope
        self.workspaceChanged.emit()
        self.refreshWorkspace()

    @Slot(str)
    def setWorkspaceSearch(self, query: str) -> None:
        self._workspace_search = str(query or "").strip()
        self._search_timer.start()

    def _workspace_root(self) -> Path | None:
        if self._project_path is None:
            return None
        if self._workspace_scope == "all":
            return self._project_path
        return self._project_path / self._spec.group / self._project_tool_name()

    def _project_tool_name(self) -> str:
        names = {
            "social_security": "社保明细与汇总",
            "insurance_ledger": "保险台账与预警",
            "data_statistics": "考勤与周月报",
            "salary_split": "工资表拆分",
            "salary_merge": "多月工资合并",
            "personnel_change_merge": "异动汇总",
            "roster_update": "花名册更新",
            "personnel_reconcile": "异动流程核对",
            "archive_import": "档案入库",
            "archive_export": "档案表生成",
            "material_collector": "员工资料打包",
            "folder_rename": "资料文件夹改名",
        }
        return names[self._spec.tool_id]

    @staticmethod
    def _hide_workspace_path(path: Path) -> bool:
        name = path.name
        lower = name.casefold()
        return (
            name in WORKSPACE_HIDDEN_NAMES
            or name.startswith(".")
            or name.startswith("~$")
            or any(lower.endswith(suffix) for suffix in WORKSPACE_HIDDEN_SUFFIXES)
            or path.is_symlink()
        )

    @classmethod
    def _scan_directory(cls, root: Path, *, depth: int = 0, cancelled=None) -> list[dict[str, Any]]:
        records = []
        try:
            with os.scandir(root) as entries:
                for entry in entries:
                    if cancelled is not None and cancelled():
                        return []
                    path = Path(entry.path)
                    # DirEntry already knows whether this is a symlink; do
                    # not issue a separate lstat() for every directory item.
                    name = entry.name
                    if (name in WORKSPACE_HIDDEN_NAMES or name.startswith((".", "~$"))
                            or name.casefold().endswith(WORKSPACE_HIDDEN_SUFFIXES)
                            or entry.is_symlink()):
                        continue
                    try:
                        is_dir = entry.is_dir(follow_symlinks=False)
                    except OSError:
                        is_dir = False
                    records.append(
                        {
                            "name": entry.name,
                            "path": str(path),
                            "isDir": is_dir,
                            "depth": depth,
                            "expanded": False,
                            "hasChildren": is_dir,
                            "detail": "文件夹" if is_dir else (path.suffix.lower().lstrip(".").upper() or "文件"),
                        }
                    )
        except OSError:
            return []
        records.sort(key=lambda item: (not bool(item["isDir"]), str(item["name"]).casefold()))
        return records

    @classmethod
    def _search_workspace(
        cls,
        root: Path,
        query: str,
        *,
        cancelled=None,
    ) -> list[dict[str, Any]]:
        results = []
        try:
            for current_root, dir_names, file_names in os.walk(root, followlinks=False):
                if cancelled is not None and cancelled():
                    return results
                current = Path(current_root)
                dir_names[:] = [
                    name for name in dir_names if not cls._hide_workspace_path(current / name)
                ]
                for name in (*dir_names, *file_names):
                    if cancelled is not None and cancelled():
                        return results
                    path = current / name
                    if query not in name.casefold() or cls._hide_workspace_path(path):
                        continue
                    try:
                        is_dir = path.is_dir()
                    except OSError:
                        is_dir = False
                    try:
                        relative_parent = path.parent.relative_to(root).as_posix()
                    except ValueError:
                        relative_parent = path.parent.name
                    results.append(
                        {
                            "name": name,
                            "path": str(path),
                            "isDir": is_dir,
                            "depth": 0,
                            "expanded": False,
                            "hasChildren": is_dir,
                            "detail": relative_parent if relative_parent != "." else ("文件夹" if is_dir else "文件"),
                        }
                    )
                    if len(results) >= WORKSPACE_SEARCH_LIMIT:
                        return results
        except OSError:
            return results
        return results

    @Slot()
    def refreshWorkspace(self) -> None:
        previous_cancel = self._workspace_scan_cancel_event
        if previous_cancel is not None:
            previous_cancel.set()
        cancel_event = threading.Event()
        self._workspace_scan_cancel_event = cancel_event
        root = self._workspace_root()
        self._workspace_generation += 1
        self._workspace_child_loads.clear()
        generation = self._workspace_generation
        self._workspace_refresh_pending = root is not None
        if root is None:
            self._workspace_items = []
            self._workspace_selected_path = None
            self._workspace_selected_item = None
            self._workspace_model.clear()
            self.workspaceSelectionChanged.emit()
            return
        query = self._workspace_search.casefold()
        expanded_paths = frozenset(
            str(item["path"]) for item in self._workspace_items
            if item.get("isDir") and item.get("expanded")
        )

        def worker() -> None:
            items = (
                self._search_workspace(root, query, cancelled=cancel_event.is_set)
                if query
                else self._scan_workspace_tree(root, expanded_paths, cancelled=cancel_event.is_set)
            )
            if cancel_event.is_set():
                return
            self._workspaceItemsReady.emit(generation, items)

        self._schedule_workspace_read(generation, worker)

    @classmethod
    def _scan_workspace_tree(cls, root: Path, expanded_paths: frozenset[str], *, cancelled=None):
        """Refresh visible branches, preserving expansion by stable directory path."""
        items = []
        pending = [iter(cls._scan_directory(root, cancelled=cancelled))]
        while pending:
            if cancelled is not None and cancelled():
                return []
            item = next(pending[-1], None)
            if item is None:
                pending.pop()
                continue
            items.append(item)
            if item.get("isDir") and str(item["path"]) in expanded_paths:
                item["expanded"] = True
                children = cls._scan_directory(Path(item["path"]), depth=int(item["depth"]) + 1,
                                               cancelled=cancelled)
                pending.append(iter(children))
        return items

    def _schedule_workspace_read(self, generation: int, worker) -> None:
        with self._workspace_read_lock:
            if self._closed:
                return
            self._workspace_read_jobs = deque(
                job for job in self._workspace_read_jobs if job[0] == self._workspace_generation
            )
            self._workspace_read_jobs.append((generation, worker))
            if self._workspace_read_workers >= self._workspace_read_limit:
                return
            self._workspace_read_workers += 1
        # Daemon workers let shutdown finish even if the OS is stuck in a
        # disconnected share. No writer/project tasks use this read queue.
        threading.Thread(target=self._run_workspace_reads, daemon=True,
                         name="HRToolkit-workspace-scan").start()

    def _run_workspace_reads(self) -> None:
        while True:
            with self._workspace_read_lock:
                if self._closed or not self._workspace_read_jobs:
                    self._workspace_read_workers -= 1
                    return
                generation, worker = self._workspace_read_jobs.popleft()
            if generation != self._workspace_generation:
                continue
            try:
                worker()
            except Exception as exc:
                runlog.log_exception("读取项目目录失败", exc)

    @Slot(int, object)
    def _apply_workspace_items(self, generation: int, items: list[dict[str, Any]]) -> None:
        if generation != self._workspace_generation or self._closed:
            return
        self._workspace_refresh_pending = False
        next_items = list(items)
        previous_items = self._workspace_items
        changed = next_items != previous_items
        self._workspace_items = next_items
        if changed:
            # Keep delegates and their viewport positions for a small metadata
            # refresh with identical row identities. Structural changes use
            # path-based splices; large metadata batches coalesce notifications.
            updates = [] if len(next_items) == len(previous_items) else None
            if updates is not None:
                for row, (before, after) in enumerate(zip(previous_items, next_items)):
                    if before.get("path") != after.get("path"):
                        updates = None
                        break
                    if before != after:
                        updates.append((row, after))
                        if len(updates) > 32:
                            updates = None
                            break
            if updates is None:
                self._workspace_model.sync_items(self._workspace_items)
            else:
                for row, item in updates:
                    self._workspace_model.update_at(row, item)
        selected_text = str(self._workspace_selected_path or "")
        self._workspace_selected_item = next(
            (
                dict(item)
                for item in self._workspace_items
                if str(item.get("path") or "") == selected_text
            ),
            None,
        )
        self.workspaceSelectionChanged.emit()

    @Slot(int)
    def toggleWorkspaceRow(self, row: int) -> None:
        if self._workspace_search or row < 0 or row >= len(self._workspace_items):
            return
        item = self._workspace_items[row]
        if not item.get("isDir"):
            return
        depth = int(item.get("depth", 0))
        if item.get("expanded"):
            end = row + 1
            while end < len(self._workspace_items) and int(self._workspace_items[end].get("depth", 0)) > depth:
                end += 1
            item["expanded"] = False
            self._workspace_model.update_at(row, item)
            remove_count = end - row - 1
            del self._workspace_items[row + 1 : end]
            self._workspace_model.splice(row + 1, remove_count)
            if self._workspace_refresh_pending:
                self.refreshWorkspace()
            return
        item["expanded"] = True
        self._workspace_model.update_at(row, item)
        if self._workspace_refresh_pending:
            # A refresh in flight contains an older expansion snapshot. Restart
            # it so a late result cannot undo this click or duplicate children.
            self.refreshWorkspace()
            return
        generation = self._workspace_generation
        path = Path(str(item["path"]))
        path_text = str(path)
        if path_text in self._workspace_child_loads:
            return
        self._workspace_child_loads.add(path_text)

        def worker() -> None:
            children = self._scan_directory(path, depth=depth + 1,
                                            cancelled=lambda: self._closed or generation != self._workspace_generation)
            self._workspaceChildrenReady.emit(generation, row, path_text, depth, children)

        self._schedule_workspace_read(generation, worker)

    @Slot(int, int, str, int, object)
    def _apply_workspace_children(self, generation: int, row: int, path: str, depth: int, children) -> None:
        if self._closed or generation != self._workspace_generation:
            return
        self._workspace_child_loads.discard(path)
        # Another expanded folder can insert rows while this directory is
        # loading. Locate the same folder again instead of dropping its result.
        if row >= len(self._workspace_items) or str(self._workspace_items[row].get("path")) != path:
            row = next((index for index, item in enumerate(self._workspace_items)
                        if str(item.get("path")) == path), -1)
        if row < 0:
            return
        item = self._workspace_items[row]
        if str(item.get("path")) != path or not item.get("expanded") or int(item.get("depth", 0)) != depth:
            return
        inserted = list(children)
        self._workspace_items[row + 1 : row + 1] = inserted
        self._workspace_model.splice(row + 1, items=inserted)

    @Slot(int)
    def selectWorkspaceRow(self, row: int) -> None:
        if 0 <= row < len(self._workspace_items):
            item = self._workspace_items[row]
            self._workspace_selected_path = Path(str(item["path"]))
            self._workspace_selected_item = dict(item)
        else:
            self._workspace_selected_path = None
            self._workspace_selected_item = None
        self.workspaceSelectionChanged.emit()

    def _workspace_transfer_source(self, path_text: str):
        """Capture stable identity from the current model, without filesystem IO."""
        if not self.selectionEnabled or self._project_path is None:
            return None
        item = next((item for item in self._workspace_items if item.get("path") == path_text), None)
        if item is None:
            return None
        path = Path(path_text)
        try:
            parts = path.relative_to(self._project_path).parts
        except ValueError:
            return None
        # Top-level categories are navigation, not individual input sources.
        if len(parts) < 2 or any(part in {"..", "回收站"} or part.startswith((".", "~$"))
                                 or part.casefold() in {name.casefold() for name in WORKSPACE_HIDDEN_NAMES}
                                 or part.casefold().endswith(WORKSPACE_HIDDEN_SUFFIXES) for part in parts):
            return None
        return {"token": uuid4().hex, "path": path, "root": self._project_path,
                "context": self._selection_context(), "is_dir": bool(item.get("isDir"))}

    @staticmethod
    def _validate_workspace_source(source) -> None:
        """Worker-only containment check; never scan directories or copy sources."""
        if source is None:
            return
        root, path = source["root"], source["path"]
        resolved_root = root.resolve(strict=True)
        resolved = path.resolve(strict=True)
        relative = resolved.relative_to(resolved_root)
        if len(relative.parts) < 2:
            raise ValueError("不能带入项目根目录或分类栏目。")
        current = root
        for part in path.relative_to(root).parts:
            current = current / part
            if current.is_symlink():
                raise ValueError("不能带入链接目录，请选择项目中的实际资料。")
        if any(part.startswith((".", "~$")) or part == "回收站"
               or part.casefold() in {name.casefold() for name in WORKSPACE_HIDDEN_NAMES}
               for part in relative.parts):
            raise ValueError("不能带入回收站或项目内部资料。")

    @Slot(str, result="QVariantMap")
    def beginWorkspaceTransfer(self, path_text: str):
        source = self._workspace_transfer_source(path_text)
        self._workspace_transfer = source
        if source is None:
            return {}
        return {"token": source["token"], "url": QUrl.fromLocalFile(str(source["path"])).toString(),
                "name": source["path"].name}

    @Slot(str)
    def endWorkspaceTransfer(self, token: str) -> None:
        if self._workspace_transfer and self._workspace_transfer["token"] == token:
            self._workspace_transfer = None
            preview = self._drop_preview_request
            if preview and preview.get("workspace_source"):
                self.cancelDropPreview(preview["token"])

    @Slot(str, result=bool)
    def canUseWorkspaceSelection(self, role: str) -> bool:
        if role not in {"input", "support"}:
            return False
        source = self._workspace_transfer_source(str(self._workspace_selected_path or ""))
        if not source or (role == "support" and not self.hasSupportField):
            return False
        mode = selection_mode(self._spec, role)
        if source["is_dir"]:
            return mode in {"directory_single", "excel_archive_multi", "excel_or_folder", "excel_archive_or_folder"}
        from hr_toolkit.common.inputs import is_supported_archive_file
        return mode != "directory_single" and (source["path"].suffix.lower() in EXCEL_SUFFIXES
            or (mode in {"excel_archive_multi", "excel_archive_or_folder"} and is_supported_archive_file(source["path"])))

    @Slot(str)
    def useWorkspaceSelection(self, role: str) -> None:
        if not self.canUseWorkspaceSelection(role):
            return
        source = self._workspace_transfer_source(str(self._workspace_selected_path))
        self._submit_selection(role, [source["path"]],
                               replace=role == "support" or not self.inputAllowsMultiple, workspace_source=source)

    @Slot(str)
    def openSelectedInput(self, path_text: str) -> None:
        if not self.selectionEnabled:
            return
        path = Path(path_text)
        if path in self._input_states[self._state_key()] or path_text == self.supportPath:
            # Explicit user action only; use the same OS opener as project files.
            try:
                open_path(path)
            except OSError as exc:
                self.notificationRequested.emit("无法打开资料", str(exc), "warning")

    @Slot(int)
    def openWorkspaceRow(self, row: int) -> None:
        if 0 <= row < len(self._workspace_items):
            path = Path(str(self._workspace_items[row]["path"]))
            if path.is_dir():
                self.toggleWorkspaceRow(row)
            elif path.exists():
                open_path(path)

    @Slot()
    def launchWorkspaceSelection(self) -> None:
        path = self._workspace_selected_path
        if path is not None and path.exists():
            open_path(path)

    @Slot()
    def revealWorkspaceSelection(self) -> None:
        path = self._workspace_selected_path
        if path is None:
            return
        target = path if path.is_dir() else path.parent
        if target.exists():
            open_path(target)

    @Slot(int)
    def revealWorkspaceRow(self, row: int) -> None:
        if 0 <= row < len(self._workspace_items):
            path = Path(str(self._workspace_items[row]["path"]))
            target = path if path.is_dir() else path.parent
            if target.exists():
                open_path(target)

    @Slot()
    def importWorkspaceFiles(self) -> None:
        if not self.projectWritable or self._busy or self._workspace_busy:
            return
        names, _selected = self._presentation.file_dialog(QFileDialog.getOpenFileNames,
            self._dialog_parent(), "选择本次处理的文件", self._file_dialog_initial_dir(), "所有文件 (*)"
        )
        if names:
            self._remember_file_dialog_path(names)
            self._start_workspace_import([Path(name) for name in names])

    @Slot()
    def importWorkspaceFolder(self) -> None:
        if not self.projectWritable or self._busy or self._workspace_busy:
            return
        selected = self._presentation.file_dialog(QFileDialog.getExistingDirectory,
            self._dialog_parent(), "选择本次处理的文件夹", self._file_dialog_initial_dir()
        )
        if selected:
            self._remember_file_dialog_path(selected)
            self._start_workspace_import([Path(selected)])

    def _workspace_import_target(self) -> tuple[Path, tuple[str, str] | None] | None:
        store = self._project_store
        if store is None:
            return None
        common = store.workspace.common_root
        selected = self._workspace_selected_path
        target = selected if selected is not None and selected.is_dir() else common
        try:
            locations = store.list_batch_locations()
        except Exception:
            locations = ()
        for summary, directories in locations:
            for category in ("uploads", "supplements"):
                directory = directories.get(category)
                if directory is None:
                    continue
                try:
                    target.relative_to(directory)
                except ValueError:
                    continue
                if category == "uploads" and summary.status != "draft":
                    target = directories["supplements"]
                    category = "supplements"
                return target, (summary.id, category)
            result_dir = directories.get("results")
            if result_dir is not None:
                try:
                    target.relative_to(result_dir)
                except ValueError:
                    pass
                else:
                    return directories["supplements"], (summary.id, "supplements")
        try:
            target.relative_to(common)
        except ValueError:
            target = common
        return target, None

    def _start_workspace_import(self, sources: list[Path]) -> None:
        if self._workspace_recovery_blocked:
            self.notificationRequested.emit("项目未安全恢复", "请重新打开当前项目后再选择资料。", "error")
            return
        # Selecting material must never create a permanent project copy.
        self._submit_selection("input", sources, replace=not self.inputAllowsMultiple)

    @Slot()
    def cancelWorkspaceImport(self) -> None:
        if self._workspace_cancel_event is not None:
            self._workspace_cancel_event.set()

    @Slot(bool, str)
    def _apply_workspace_import_result(self, success: bool, message: str) -> None:
        self._workspace_busy = False
        self._workspace_cancel_event = None
        self.workspaceBusyChanged.emit()
        if self._workspace_recovery_blocked:
            self.projectChanged.emit()
            self._append_log(message, "error")
            self.notificationRequested.emit("项目未安全恢复", message, "error")
        else:
            self._append_log(message, "success" if success else "warning")
            self.notificationRequested.emit("项目文件" if success else "导入未完成", message, "info" if success else "warning")
        self.refreshWorkspace()

    @staticmethod
    def _format_size(value: int) -> str:
        size = max(0, int(value))
        if size >= 1024**3:
            return f"{size / 1024**3:.1f} GB"
        if size >= 1024**2:
            return f"{size / 1024**2:.1f} MB"
        if size >= 1024:
            return f"{size / 1024:.1f} KB"
        return f"{size} B"

    @staticmethod
    def _format_time(value: str, short: bool = False) -> str:
        try:
            pattern = "%m-%d %H:%M" if short else "%Y-%m-%d %H:%M"
            return datetime.fromisoformat(value).astimezone().strftime(pattern)
        except (TypeError, ValueError):
            return str(value or "")

    @staticmethod
    def _names_text(names, empty: str, *, full: bool = False) -> str:
        values = tuple(str(item) for item in names if str(item))
        if not values:
            return empty
        if full:
            visible = "、".join(values[:5])
            return visible if len(values) <= 5 else f"{visible} 等 {len(values)} 个文件"
        return values[0] if len(values) == 1 else f"{values[0]} 等 {len(values)} 个"

    def _history_started_after(self) -> str | None:
        today = datetime.now().astimezone().replace(hour=0, minute=0, second=0, microsecond=0)
        if self._history_date_filter == "今天":
            start = today
        elif self._history_date_filter == "最近7天":
            start = today - timedelta(days=6)
        elif self._history_date_filter == "最近30天":
            start = today - timedelta(days=29)
        elif self._history_date_filter == "今年":
            start = today.replace(month=1, day=1)
        else:
            return None
        return start.astimezone(timezone.utc).isoformat(timespec="seconds")

    @Slot()
    def requestHistory(self) -> None:
        self.refreshHistory(self._history_search, self._history_tool_id, self._history_date_filter)

    @Slot(str, str, str)
    def refreshHistory(self, search: str, tool_id: str, date_filter: str) -> None:
        self._history_search = str(search or "").strip()
        self._history_tool_id = str(tool_id or "").strip()
        self._history_date_filter = str(date_filter or "全部时间")
        self._history_generation += 1
        generation = self._history_generation
        self._history_busy = True
        self._history_message = "正在读取旧版记录…"
        self.historyChanged.emit()

        def worker() -> None:
            try:
                store = self._history_store
                if store is None:
                    store = HistoryStore()
                    self._history_store = store
                    self._history_init_attempted = True
                tasks, total = store.list_tasks(
                    search=self._history_search,
                    tool_id=self._history_tool_id or None,
                    started_after=self._history_started_after(),
                    limit=HISTORY_PAGE_SIZE,
                    offset=self._history_page * HISTORY_PAGE_SIZE,
                )
                rows = [
                    {
                        "recordId": task.id,
                        "time": self._format_time(task.started_at, short=True),
                        "tool": task.tool_name,
                        "status": HISTORY_STATUS_LABELS.get(task.status, task.status),
                        "inputs": self._names_text(task.input_names, "未归档上传资料"),
                        "outputs": self._names_text(task.output_names, "暂无完整结果"),
                        "detail": task.error_message or "",
                    }
                    for task in tasks
                ]
                message = f"共找到 {total} 次处理记录"
                try:
                    stats = store.storage_stats()
                    message += f" · 已留存 {self._format_size(stats['total_bytes'])} · 磁盘可用 {self._format_size(stats['free_bytes'])}"
                    if stats["trash_bytes"]:
                        message += f"（回收站 {self._format_size(stats['trash_bytes'])}）"
                except Exception:
                    pass
                if not rows:
                    message = (
                        "没有找到相关记录，可以清除查找内容或更换筛选条件。"
                        if self._history_search or self._history_tool_id or self._history_date_filter != "全部时间"
                        else "没有找到旧版记录。新处理的资料和结果请在“项目文件”中查看。"
                    )
            except Exception as exc:
                self._historyListReady.emit(generation, [], 0, f"历史记录暂时无法读取：{exc}")
                return
            self._historyListReady.emit(generation, rows, total, message)

        threading.Thread(target=worker, daemon=True, name="HRToolkit-history-list").start()

    @Slot(int, object, int, str)
    def _apply_history_list(self, generation: int, rows, total: int, message: str) -> None:
        if generation != self._history_generation or self._closed:
            return
        self._history_busy = False
        self._history_total = max(0, int(total))
        pages = max(1, (self._history_total + HISTORY_PAGE_SIZE - 1) // HISTORY_PAGE_SIZE)
        if self._history_page >= pages:
            self._history_page = pages - 1
        self._history_message = message
        self._history_model.set_items(rows)
        self._history_selected = None
        self._history_detail = {}
        self.historyChanged.emit()
        if rows:
            self.selectHistoryRow(0)

    @Slot(int)
    def changeHistoryPage(self, delta: int) -> None:
        target = self._history_page + int(delta)
        if target < 0 or (target * HISTORY_PAGE_SIZE >= self._history_total and delta > 0):
            return
        self._history_page = target
        self.requestHistory()

    @Slot(int)
    def selectHistoryRow(self, row: int) -> None:
        item = self._history_model.item_at(row)
        store = self._history_store
        if item is None or store is None:
            return
        task_id = str(item["recordId"])
        generation = self._history_generation
        self._history_detail = {"id": task_id, "title": "正在读取详情…", "body": ""}
        self.historyChanged.emit()

        def worker() -> None:
            try:
                detail = store.get_task(task_id)
                if detail is None:
                    raise RuntimeError("历史记录不存在。")
                summary = detail.summary
                status = HISTORY_STATUS_LABELS.get(summary.status, summary.status)
                lines = [
                    f"处理时间：{self._format_time(summary.started_at)}",
                    f"上传资料：{self._names_text(summary.input_names, '未归档上传资料', full=True)}",
                    f"处理结果：{self._names_text(summary.output_names, '未生成完整结果', full=True)}",
                ]
                if summary.status == "failed":
                    lines.append("说明：上传资料已保存，但本次没有正常生成完整结果。")
                elif summary.status == "stopped":
                    lines.append("说明：这次处理没有正常完成，可以再次使用已保存的资料。")
                if summary.error_message and summary.status in {"failed", "stopped"}:
                    lines.append(f"原因：{summary.error_message}")
                payload = {
                    "batchId": summary.id,
                    "title": f"{summary.tool_name} · {status}",
                    "body": "\n".join(lines),
                    "canOpenOutput": bool(detail.outputs),
                    "canOpenInput": bool(detail.inputs),
                    "canReuse": summary.tool_id != "folder_rename" and bool(detail.inputs),
                    "canDelete": summary.status != "running",
                }
            except Exception as exc:
                self._historyDetailReady.emit(generation, None, str(exc))
                return
            self._historyDetailReady.emit(generation, (detail, payload), "")

        threading.Thread(target=worker, daemon=True, name="HRToolkit-history-detail").start()

    @Slot(int, object, str)
    def _apply_history_detail(self, generation: int, result, error: str) -> None:
        if generation != self._history_generation or self._closed:
            return
        if error or not result:
            self._history_selected = None
            self._history_detail = {"title": "这条记录暂时无法读取", "body": error}
        else:
            detail, payload = result
            self._history_selected = detail
            self._history_detail = dict(payload)
        self.historyChanged.emit()

    @Slot()
    def openHistoryInput(self) -> None:
        detail = self._history_selected
        if detail is not None and detail.inputs and detail.input_dir.is_dir():
            open_path(detail.input_dir)

    @Slot()
    def openHistoryOutput(self) -> None:
        detail = self._history_selected
        if detail is not None and detail.outputs and detail.output_dir.is_dir():
            open_path(detail.output_dir)

    @Slot()
    def openHistoryRoot(self) -> None:
        if self._history_store is not None:
            open_path(self._history_store.records_dir)

    @Slot()
    def openHistoryTrash(self) -> None:
        if self._history_store is not None:
            open_path(self._history_store.trash_dir)

    @Slot()
    def reuseHistory(self) -> None:
        detail = self._history_selected
        if detail is None or self._busy:
            return
        tool_id = detail.summary.tool_id
        nav_id = {"roster_update": "personnel_change_merge", "personnel_reconcile": "personnel_change_merge", "archive_export": "archive_import"}.get(tool_id, tool_id)
        try:
            spec_for(nav_id, DEFAULT_VARIANTS.get(nav_id, "default"))
        except KeyError:
            self.notificationRequested.emit("暂不支持", "这条旧记录暂时不能直接再次使用，可以先打开上传资料。", "warning")
            return
        if tool_id == "folder_rename":
            self.notificationRequested.emit("请先复制资料", "为了保护历史原件，文件夹改名记录不能直接再次处理。", "info")
            return
        variant = DEFAULT_VARIANTS.get(nav_id, "default")
        if nav_id == "personnel_change_merge" and (tool_id == "roster_update" or detail.summary.mode == "roster"):
            variant = "roster"
        elif nav_id == "personnel_change_merge" and tool_id == "personnel_reconcile":
            variant = "reconcile"
        elif nav_id == "archive_import" and (tool_id == "archive_export" or detail.summary.mode == "export"):
            variant = "export"
        self._variants[nav_id] = variant
        self._spec = spec_for(nav_id, variant)
        self._ensure_state(self._spec)
        main_inputs = [
            item.archived_path
            for item in detail.inputs
            if item.role in {"input_path", "input_paths"} and item.archived_path.exists()
        ]
        secondary: dict[str, list[Path]] = {}
        for item in detail.inputs:
            if item.role not in {"input_path", "input_paths"} and item.archived_path.exists():
                secondary.setdefault(item.role, []).append(item.archived_path)
        if self._spec.input_mode == "excel_single":
            main_inputs = main_inputs[:1]
        self._input_states[self._state_key()] = main_inputs
        self._support_states[self._state_key()] = ""
        if secondary:
            paths = next(iter(secondary.values()))
            try:
                support = paths[0] if len(paths) == 1 else Path(os.path.commonpath([str(path) for path in paths]))
            except ValueError:
                support = paths[0]
            self._support_states[self._state_key()] = str(support)
        self._sync_input_model()
        self._clear_logs()
        self._append_log(self._spec.log_text, "info")
        self._flush_logs()
        self.specChanged.emit()
        self.supportChanged.emit()
        self.materialChanged.emit()
        self._bump_form_revision()
        self.notificationRequested.emit("资料已带入", "以前保存的资料已经放回当前功能，请确认后重新处理。", "success")

    @Slot()
    def requestMoveHistoryToTrash(self) -> None:
        detail = self._history_selected
        if detail is None or detail.summary.status == "running":
            return
        token = f"history-trash:{time.monotonic_ns()}"
        self._pending_confirmation = token
        self._pending_confirmation_action = ("history-trash", detail.summary.id)
        self.confirmationRequested.emit(
            "移到回收站",
            "这次处理的上传资料和结果会移到 HRToolkit 回收站，不会立即永久删除。是否继续？",
            token,
        )

    def _move_history_to_trash(self, task_id: str) -> None:
        store = self._history_store
        if store is None:
            return
        self._history_busy = True
        self.historyChanged.emit()

        def worker() -> None:
            try:
                store.move_to_trash(task_id)
            except Exception as exc:
                self._historyActionFinished.emit("trash", False, str(exc))
            else:
                self._historyActionFinished.emit("trash", True, "已移到旧版记录回收站。")

        threading.Thread(target=worker, daemon=True, name="HRToolkit-history-trash").start()

    @Slot()
    def rebuildHistoryIndex(self) -> None:
        store = self._history_store
        if store is None or self._history_busy:
            return
        self._history_busy = True
        self._history_message = "正在整理历史记录，请稍候…"
        self.historyChanged.emit()

        def worker() -> None:
            try:
                count = store.rebuild_index_from_manifests()
            except Exception as exc:
                self._historyActionFinished.emit("rebuild", False, str(exc))
            else:
                self._historyActionFinished.emit("rebuild", True, f"历史记录已经整理完成，恢复或修复了 {count} 条记录。")

        threading.Thread(target=worker, daemon=True, name="HRToolkit-history-rebuild").start()

    @Slot(str, bool, str)
    def _apply_history_action(self, kind: str, success: bool, message: str) -> None:
        self._history_busy = False
        self.historyChanged.emit()
        self.notificationRequested.emit("整理完成" if success else "操作未完成", message, "success" if success else "error")
        self.requestHistory()

    def _rebuild_trash_row_index(self) -> None:
        rows: list[tuple[dict[str, Any], str]] = []
        for detail in self._trash_items:
            summary = detail.summary
            title = summary.business_description or summary.directory_name or summary.tool_name
            searchable = " ".join((title, summary.tool_name, summary.group_name, summary.business_period)).casefold()
            rows.append(
                ({
                    "batchId": summary.id,
                    "title": title,
                    "tool": f"{summary.group_name} · {summary.tool_name}",
                    "status": HISTORY_STATUS_LABELS.get(summary.status, summary.status),
                    "deletedAt": self._format_time(summary.deleted_at or ""),
                    "counts": f"上传 {detail.upload_count} · 结果 {detail.result_count} · 补充 {detail.supplement_count}",
                    "restorePath": detail.original_relative_path,
                    "size": self._format_size(detail.total_size_bytes),
                }, searchable)
            )
        self._trash_row_index = rows
        self._trash_applied_query = None

    def _filtered_trash_rows(self) -> list[dict[str, Any]]:
        query = self._trash_search.casefold()
        return [row for row, searchable in self._trash_row_index
                if not query or query in searchable]

    def _refresh_trash_model(self) -> None:
        rows = self._filtered_trash_rows()
        changed = rows != self._trash_visible_rows
        self._trash_visible_rows = rows
        self._trash_applied_query = self._trash_search.casefold()
        self._trash_selected_row = next(
            (index for index, item in enumerate(rows)
             if str(item["batchId"]) == self._trash_selected_id),
            0 if rows else -1,
        )
        self._trash_selected_id = (
            str(rows[self._trash_selected_row]["batchId"])
            if self._trash_selected_row >= 0 else ""
        )
        if changed:
            self._trash_model.set_items(rows)

    def _clear_trash_items(self) -> None:
        self._trash_items = []
        self._trash_row_index = []
        self._trash_visible_rows = []
        self._trash_applied_query = None
        self._trash_selected_id = ""
        self._trash_selected_row = -1
        self._trash_model.clear()

    @Slot()
    def requestProjectTrash(self) -> None:
        store = self._project_store
        if store is None:
            self.notificationRequested.emit("请先打开项目", "打开工作项目后才能查看项目回收站。", "warning")
            return
        self._trash_generation += 1
        generation = self._trash_generation
        self._trash_busy = True
        self.trashChanged.emit()

        def worker() -> None:
            try:
                items = list(store.list_trash_details())
            except Exception as exc:
                self._trashReady.emit(generation, [], str(exc))
            else:
                self._trashReady.emit(generation, items, "")

        threading.Thread(target=worker, daemon=True, name="HRToolkit-project-trash-list").start()

    @Slot(int, object, str)
    def _apply_trash_list(self, generation: int, items, error: str) -> None:
        if generation != self._trash_generation or self._closed:
            return
        self._trash_busy = False
        if error:
            self._clear_trash_items()
            self.notificationRequested.emit("回收站暂时无法读取", error, "error")
        else:
            self._trash_items = list(items)
            self._rebuild_trash_row_index()
            self._refresh_trash_model()
        self.trashChanged.emit()

    @Slot(str)
    def setTrashSearch(self, query: str) -> None:
        if self._closed:
            return
        self._trash_search = str(query or "").strip()
        if self._trash_search.casefold() == self._trash_applied_query:
            return
        self._refresh_trash_model()
        self.trashChanged.emit()

    @Slot(int)
    def selectTrashRow(self, row: int) -> None:
        item = self._trash_model.item_at(row)
        self._trash_selected_id = "" if item is None else str(item["batchId"])
        self._trash_selected_row = -1 if item is None else row
        self.trashChanged.emit()

    @Slot()
    def restoreSelectedTrash(self) -> None:
        store = self._project_store
        batch_id = self._trash_selected_id
        if store is None or not batch_id or self._trash_busy or not store.writable or self._busy or self._workspace_busy or self._workspace_recovery_blocked:
            if self._workspace_recovery_blocked:
                self.notificationRequested.emit("项目未安全恢复", "当前项目处于未恢复状态，写入已锁定。请重新打开当前项目以恢复状态。", "error")
            return
        self._trash_busy = True
        self.trashChanged.emit()

        def worker() -> None:
            try:
                store.restore_from_trash(batch_id)
            except Exception as exc:
                self._trashActionFinished.emit(False, str(exc))
            else:
                self._trashActionFinished.emit(True, "处理批次已恢复到当前项目，现有资料没有被覆盖。")

        threading.Thread(target=worker, daemon=True, name="HRToolkit-project-trash-restore").start()

    @Slot(bool, str)
    def _apply_trash_action(self, success: bool, message: str) -> None:
        self._trash_busy = False
        self.trashChanged.emit()
        self.notificationRequested.emit("已恢复到项目" if success else "恢复没有完成", message, "success" if success else "error")
        self.refreshWorkspace()
        self.requestProjectTrash()

    def _selected_workspace_batch(self):
        store = self._project_store
        selected = self._workspace_selected_path
        if store is None or selected is None:
            return None
        try:
            locations = store.list_batch_locations()
        except Exception:
            return None
        for summary, directories in locations:
            for directory in directories.values():
                try:
                    selected.relative_to(directory)
                except ValueError:
                    continue
                return summary
        return None

    @Slot()
    def requestMoveSelectedBatchToTrash(self) -> None:
        summary = self._selected_workspace_batch()
        if summary is None:
            self.notificationRequested.emit("请选择处理批次", "请先在项目文件中选择某个处理批次内的文件或文件夹。", "warning")
            return
        token = f"project-trash:{time.monotonic_ns()}"
        self._pending_confirmation = token
        self._pending_confirmation_action = ("project-trash", summary.id)
        title = summary.business_description or summary.directory_name or summary.tool_name
        self.confirmationRequested.emit(
            "移到项目回收站",
            f"“{title}”的处理结果及已有历史资料会一起移到当前项目回收站，不会永久删除。是否继续？",
            token,
        )

    def _move_project_batch_to_trash(self, batch_id: str) -> None:
        store = self._project_store
        if store is None or not store.writable or self._busy or self._workspace_busy or self._workspace_recovery_blocked:
            if self._workspace_recovery_blocked:
                self.notificationRequested.emit("项目未安全恢复", "当前项目处于未恢复状态，写入已锁定。请重新打开当前项目以恢复状态。", "error")
            return
        self._workspace_busy = True
        self.workspaceBusyChanged.emit()

        def worker() -> None:
            try:
                store.move_to_trash(batch_id)
            except Exception as exc:
                self._workspaceImportFinished.emit(False, f"无法移到项目回收站：{exc}")
            else:
                self._workspaceImportFinished.emit(True, "完整处理批次已移到当前项目回收站，之后可以恢复。")

        threading.Thread(target=worker, daemon=True, name="HRToolkit-project-trash-move").start()

    @Slot()
    def _show_startup_release_notes(self) -> None:
        if self._closed or self._shutdown_requested:
            return
        if self._busy or self._workspace_busy or self._project_opening or self._update_busy or self._release_notes_open:
            QTimer.singleShot(600, self._show_startup_release_notes)
            return
        if self._startup_notes_pending:
            self._release_notes_open = True
            self.releaseNotesRequested.emit({
                "startup": True, "currentVersion": __version__,
                "entries": [{"version": __version__, "notes": list(notes_for_version(__version__))}],
            })
        else:
            self.requestStartupUpdateCheck()

    @Slot()
    def showReleaseNotes(self) -> None:
        if self._update_busy or self._release_notes_open:
            return
        self._release_notes_open = True
        self.releaseNotesRequested.emit({
            "startup": False, "currentVersion": __version__,
            "entries": release_entries(__version__)[:10],
        })

    @Slot()
    def closeReleaseNotes(self) -> None:
        self._release_notes_open = False
        if self._startup_notes_pending:
            self._startup_notes_pending = False
            self._release_notes_seen_version = __version__
            self._save_workspace_preferences()
            QTimer.singleShot(600, self.requestStartupUpdateCheck)

    @Slot()
    def requestStartupUpdateCheck(self) -> None:
        if self._closed or self._shutdown_requested:
            return
        if update_check_enabled():
            if not self._background_update_timer.isActive():
                self._background_update_timer.start()
            if self.updateReady or self._update_busy or (
                self._pending_confirmation_action and self._pending_confirmation_action[0] == "update"
            ):
                return
            self._start_update_check(False)

    @Slot()
    def requestUpdateCheck(self) -> None:
        if self.updateReady and not self._update_busy:
            self._update_manual = True
            self._apply_update_result("available", self._ready_update)
            return
        self._start_update_check(True)

    @Slot(str)
    def copyLatestDownloadUrl(self, platform: str) -> None:
        if self._closed or self._shutdown_requested or self._download_link_busy:
            return
        self._download_link_busy = True
        self.downloadLinkChanged.emit()

        def worker() -> None:
            try:
                result = latest_installer_download(platform)
            except Exception as exc:
                self._downloadLinkResult.emit(platform, None, str(exc))
            else:
                self._downloadLinkResult.emit(platform, result, "")

        threading.Thread(target=worker, daemon=True, name="HRToolkit-download-link").start()

    @Slot(str, object, str)
    def _apply_download_link(self, platform: str, result, error: str) -> None:
        if self._closed or self._shutdown_requested:
            return
        self._download_link_busy = False
        self.downloadLinkChanged.emit()
        if error:
            self.notificationRequested.emit("未能复制下载地址", f"{error}\n请联网后重试，本次未复制任何地址。", "warning")
            return
        version, url = result
        try:
            clipboard = QGuiApplication.clipboard()
            if clipboard is None:
                raise RuntimeError("系统剪贴板暂不可用")
            clipboard.setText(url)
        except Exception as exc:
            self.notificationRequested.emit("复制失败", str(exc), "error")
            return
        label = "Windows 7" if platform == "win7" else "Windows 10 / 11"
        self.notificationRequested.emit(
            "下载地址已复制",
            f"最新版本 {version} · {label}（64 位）\n可直接粘贴发给同事下载。\n\n"
            "请务必按接收方电脑的系统使用对应链接：\n"
            "Windows 7 必须使用 Win7 安装包，切勿下载或安装 Win10/11 安装包。\n"
            "Windows 10/11 请使用对应的 Win10/11 安装包。\n\n"
            "此处仅提供 Windows 安装包；Mac 及其他系统的安装包，请联系管理员获取。",
            "success",
        )

    def _start_update_check(self, manual: bool) -> None:
        if self._closed or self._shutdown_requested:
            return
        if self._update_busy:
            if manual:
                self.notificationRequested.emit("正在检查更新", "请稍候，检查完成后会自动提示。", "info")
            return
        self._update_busy = True
        self._update_manual = bool(manual)
        self._update_phase = "checking"
        self._update_status = "正在检查更新…"
        self._update_progress = -1.0
        self.updateChanged.emit()

        def worker() -> None:
            try:
                update = check_for_update(__version__)
            except Exception as exc:
                self._updateResult.emit("check-error", str(exc))
            else:
                self._updateResult.emit("available" if update is not None else "none", update)

        threading.Thread(target=worker, daemon=True, name="HRToolkit-update-check").start()

    @Slot(str, object)
    def _apply_update_result(self, kind: str, payload) -> None:
        if self._closed or self._shutdown_requested:
            return
        if kind == "restored":
            self._set_update_ready(*payload)
            return
        if kind == "cache-invalid":
            self._update_restart_requested = False
            self._ready_update = None
            self._ready_update_package = None
            self._update_busy = False
            self._update_phase = ""
            self._update_status = "更新文件已失效，将重新检查更新"
            self.updateChanged.emit()
            self.notificationRequested.emit("需要重新下载更新", "已下载的更新文件缺失或不完整，工具将重新检查更新。", "warning")
            self.requestStartupUpdateCheck()
            return
        if kind in ("check-error", "none", "available", "manual-ready", "download-error", "download-cancelled", "launch-error"):
            self._update_phase = ""
            self._update_cancel_event = None
        if kind == "downloaded":
            if self._update_cancel_event is not None and self._update_cancel_event.is_set():
                self._apply_update_result("download-cancelled", None)
                return
            self._set_update_ready(self._pending_update, payload)
            return
        if kind == "check-error":
            self._update_busy = False
            self._update_status = "检查更新失败"
            self.updateChanged.emit()
            if getattr(self, "_update_manual", False):
                self.notificationRequested.emit("检查更新失败", str(payload), "error")
            return
        if kind == "none":
            self._update_busy = False
            self._update_status = "没有新版本"
            self.updateChanged.emit()
            if getattr(self, "_update_manual", False):
                self.updatePromptRequested.emit({"available": False, "currentVersion": __version__})
            return
        if kind == "available" and isinstance(payload, UpdateInfo):
            self._update_busy = False
            self._pending_update = payload
            self._update_status = f"发现新版本 v{payload.version}"
            self.updateChanged.emit()
            if not self._update_manual and payload.update_mode == "auto":
                self._accept_update(payload, background=True)
                return
            token = f"update:{time.monotonic_ns()}"
            self._pending_confirmation = token
            self._pending_confirmation_action = ("update", payload)
            self.updatePromptRequested.emit({
                "available": True, "currentVersion": __version__, "version": payload.version,
                "notes": list(payload.notes or ()), "mandatory": payload.mandatory,
                "manual": payload.update_mode == "manual", "token": token,
            })
            return
        if kind == "manual-ready" and isinstance(payload, str):
            self._update_busy = False
            self._update_status = "已打开下载地址"
            self.updateChanged.emit()
            QDesktopServices.openUrl(QUrl(payload))
            return
        if kind == "download-error":
            self._update_busy = False
            self._update_status = "更新下载失败"
            self._update_progress = -1.0
            self.updateChanged.emit()
            if self._update_manual:
                self.notificationRequested.emit("更新失败", str(payload), "error")
            else:
                runlog.log_line(f"后台更新下载失败，稍后重试：{payload}")
            return
        if kind == "download-cancelled":
            self._update_busy = False
            self._update_status = "更新下载已取消"
            self._update_progress = -1.0
            self.updateChanged.emit()
            return
        if kind == "launch-error":
            self._update_restart_requested = False
            self._update_busy = False
            self._update_status = "更新程序启动失败"
            self.updateChanged.emit()
            self.notificationRequested.emit("更新失败", str(payload), "error")
            return
        if kind == "launched":
            self._update_status = "安装程序已启动，正在关闭当前版本…"
            self._update_progress = 1.0
            self.updateChanged.emit()
            self.close()
            QTimer.singleShot(500, QCoreApplication.quit)

    def _set_update_ready(self, info: UpdateInfo, package: Path) -> None:
        self._ready_update = info
        self._ready_update_package = package
        self._pending_update = info
        self._update_cancel_event = None
        self._update_busy = False
        self._update_phase = "ready"
        self._update_progress = 1.0
        self._update_status = "重启以更新"
        self.updateChanged.emit()

    def _block_run_for_update(self) -> bool:
        if self.selectionChecking:
            self.notificationRequested.emit("正在检查资料", "请等待资料检查完成，或先取消本次检查。", "warning")
            return True
        if not self.updateBlocksTools:
            return False
        self.notificationRequested.emit(
            "请先更新工具", self.updateBlockMessage, "warning",
        )
        return True

    @Slot()
    def restartToUpdate(self) -> None:
        self._launch_ready_update(show_ui=sys.platform.startswith("win"))

    def _launch_ready_update(self, *, show_ui: bool) -> None:
        if not self.updateReady or self._update_busy or self._closed or self._shutdown_requested:
            return
        if self._shutdown_work_running():
            self.notificationRequested.emit("请先完成当前处理", "当前任务或资料保存尚未结束，请完成后再点击重启以更新。", "warning")
            return
        self._update_restart_requested = True
        self._update_busy = True
        self._update_manual = show_ui
        self._update_phase = "launching"
        self._update_status = "正在准备重启…"
        self.updateChanged.emit()
        expected = self._ready_update

        def worker() -> None:
            try:
                cached = load_ready_update(__version__)
                if not cached or cached[0].version != expected.version or cached[0].sha256 != expected.sha256:
                    self._updateResult.emit("cache-invalid", None)
                    return
                launch_update_replacement(cached[1], show_ui=show_ui)
            except Exception as exc:
                self._updateResult.emit("launch-error", str(exc))
            else:
                self._updateResult.emit("launched", None)

        threading.Thread(target=worker, daemon=True, name="HRToolkit-update-install").start()

    def _accept_update(self, update: UpdateInfo, *, background: bool = False) -> None:
        if self._update_busy:
            return
        # Downloading is safe alongside work; only installation requires idle.
        # Keep automatic download failures quiet; confirmed downloads report them.
        self._update_manual = not background
        self._pending_update = update
        self._update_busy = True
        self._update_progress = -1.0
        self._update_phase = "preparing"
        self._update_cancel_event = threading.Event() if update.update_mode != "manual" else None
        self._update_status = f"正在准备 v{update.version}…"
        self.updateChanged.emit()
        if update.update_mode == "manual":
            def manual_worker() -> None:
                try:
                    url = resolve_download_url(update)
                except Exception as exc:
                    self._updateResult.emit("download-error", str(exc))
                else:
                    self._updateResult.emit("manual-ready", url)

            threading.Thread(target=manual_worker, daemon=True, name="HRToolkit-update-url").start()
            return
        cancel_event = self._update_cancel_event

        def download_worker() -> None:
            last_emit = 0.0

            def progress(downloaded: int, total: int) -> None:
                nonlocal last_emit
                now = time.monotonic()
                if now - last_emit >= 0.25 or (total > 0 and downloaded >= total):
                    last_emit = now
                    self._updateProgressIncoming.emit(int(downloaded), int(total))

            try:
                package = download_cached_update(
                    update, __version__,
                    progress_callback=progress,
                    cancel_event=cancel_event,
                    stage_callback=self._updatePhaseIncoming.emit,
                )
            except UpdateCancelledError:
                self._updateResult.emit("download-cancelled", None)
            except Exception as exc:
                self._updateResult.emit("download-error", str(exc))
            else:
                self._updateResult.emit("downloaded", package)

        threading.Thread(target=download_worker, daemon=True, name="HRToolkit-update-download").start()

    @Slot(int, int)
    def _apply_update_progress(self, downloaded: int, total: int) -> None:
        if self._closed or self._shutdown_requested or self._update_phase != "downloading":
            return
        previous = (self._update_progress, self._update_status)
        megabytes = downloaded / 1024 / 1024
        if total > 0:
            self._update_progress = min(1.0, downloaded / total)
            self._update_status = f"{megabytes:.1f} / {total / 1024 / 1024:.1f} MB"
        else:
            self._update_progress = -1.0
            self._update_status = f"已下载 {megabytes:.1f} MB"
        if previous != (self._update_progress, self._update_status):
            self.updateProgressChanged.emit()

    @Slot(str)
    def _apply_update_phase(self, phase: str) -> None:
        if self._update_phase == "cancelling":
            return
        self._update_phase = phase
        self._update_progress = -1.0
        self._update_status = "正在校验更新文件…" if phase == "verifying" else "正在连接下载地址…"
        self.updateChanged.emit()

    @Slot()
    def cancelUpdate(self) -> None:
        if self.updateCanCancel:
            self._update_cancel_event.set()
            self._update_phase = "cancelling"
            self._update_status = "正在取消下载，请稍候…"
            self.updateChanged.emit()

    @Slot()
    def runOrCancel(self) -> None:
        if self._busy:
            if self._stop_requested:
                return
            self._stop_requested = True
            self.runButtonTextChanged.emit()
            if self._startup_loading:
                self._startup_cancelled = True
            if self._preview_cancel_event is not None:
                self._preview_cancel_event.set()
            self._run_coordinator.cancel()
            self._run_progress_message = "已请求停止，等待当前步骤安全退出…"
            self.runProgressChanged.emit()
            self._append_log("已请求停止，正在安全结束…", "warning")
            return
        if self._block_run_for_update():
            return
        if self._workspace_busy:
            self.notificationRequested.emit("项目资料正在保存", "请等待资料保存完成后再开始处理。", "warning")
            return
        store = self._project_store
        if store is None:
            self.notificationRequested.emit("请先打开工作项目", "请先新建或打开一个工作项目。", "warning")
            return
        if self._workspace_recovery_blocked:
            self.notificationRequested.emit("项目未安全恢复", "当前项目处于未恢复状态，写入已锁定。请重新打开当前项目以恢复状态。", "error")
            return
        if not store.writable:
            self.notificationRequested.emit("当前项目只能查看", store.workspace.read_only_reason or "项目为只读状态。", "warning")
            return
        if not self._template_continuing:
            self._reset_template_session()
        self._prepare_invocation(preview=self._spec.tool_id == "folder_rename")

    @Slot(result="QVariantMap")
    def regionCodeSettings(self):
        try:
            from hr_toolkit.region_codes import effective_region_codes
            store = self._project_store
            if store is None:
                raise ValueError("请先打开工作项目。")
            custom = store.read_region_overrides()
            return {"project": str(store.root), "rows": [
                {"name": name, "code": code, "custom": name in custom}
                for name, code in effective_region_codes(custom).items()], "error": ""}
        except Exception as exc:
            return {"project": "", "rows": [], "error": str(exc)}

    @Slot(str, str, str, bool, result=str)
    def saveRegionCode(self, project: str, name: str, code: str, remove: bool = False) -> str:
        try:
            from hr_toolkit.region_codes import validate_overrides
            store = self._project_store
            if self._busy or store is None or str(store.root) != project or self._workspace_recovery_blocked:
                raise ValueError("当前项目或任务状态已变化，请关闭后重新打开维护窗口。")
            custom = store.read_region_overrides()
            name, code = name.strip(), code.strip()
            if remove:
                custom.pop(name, None)
            else:
                entry = validate_overrides({name: code})
                custom = {key: value for key, value in custom.items() if key != name and int(value) != int(code)}
                custom.update(entry)
            store.save_region_overrides(custom)
            return ""
        except Exception as exc:
            return str(exc)

    def _prepare_invocation(self, *, preview: bool, preview_result=None) -> None:
        if self._block_run_for_update():
            return
        spec = self._spec
        kwargs = dict(
            input_paths=list(self._input_states[self._state_key()]),
            support_text=self._support_states[self._state_key()],
            values=dict(self._form_states[self._state_key()]),
            output_dir=self._project_path, preview=preview, preview_result=preview_result,
        )
        force_dialog = self._salary_force_next
        store = self._project_store
        event = threading.Event()
        self._preview_cancel_event = event
        self._set_busy(True)

        def worker() -> None:
            try:
                invocation = build_invocation(spec, **kwargs)
                if spec.tool_id == "archive_import" and store is not None:
                    invocation = replace(invocation, kwargs={**invocation.kwargs,
                        "region_overrides": store.read_region_overrides()})
            except Exception as exc:
                self._invocationReady.emit(None, exc, force_dialog)
            else:
                self._invocationReady.emit(invocation, None, force_dialog)

        threading.Thread(target=worker, daemon=True, name="HRToolkit-validate-inputs").start()

    @Slot(object, object, bool)
    def _apply_invocation(self, invocation, error, force_dialog: bool) -> None:
        cancelled = self._preview_cancel_event is not None and self._preview_cancel_event.is_set()
        self._preview_cancel_event = None
        self._set_busy(False)
        if self._closed or self._shutdown_requested or cancelled:
            return
        if error is not None:
            title = error.title if isinstance(error, FormValidationError) else "无法准备处理"
            self._append_log(str(error), "warning")
            self._flush_logs()
            if isinstance(error, FormValidationError) and error.field:
                self._selection_message(error.field, str(error), True)
                # Only these controls actually render selectionFeedback in
                # Main.qml. Text/choice/check fields need the dialog fallback;
                # otherwise validation stops the run without any visible reason.
                if error.field in {"input", "support", "week_range", "month_range", "material_types"}:
                    return
            self.notificationRequested.emit(title, str(error), "warning")
            return
        if invocation.tool_id == "salary_merge":
            self._start_salary_inspection(invocation, force_dialog=force_dialog)
        elif invocation.preview:
            self._start_preview(invocation)
        else:
            self._start_project_run(invocation)

    def _set_busy(self, value: bool) -> None:
        if self._busy == value:
            return
        self._busy = value
        self._stop_requested = False
        if value:
            self._run_progress_message = "正在准备并检查资料…"
            self._run_progress_current = self._run_progress_total = 0
            self.runProgressChanged.emit()
        if value:
            try:
                original = float(sys.getswitchinterval())
                self._original_switch_interval = original
                if original > 0.001:
                    sys.setswitchinterval(0.001)
            except Exception:
                self._original_switch_interval = None
        elif self._original_switch_interval is not None:
            try:
                sys.setswitchinterval(self._original_switch_interval)
            except Exception:
                pass
            self._original_switch_interval = None
        self.busyChanged.emit()

    @Property("QVariantMap", notify=salaryMappingChanged)
    def salaryMappingData(self) -> dict[str, Any]:
        return self._salary_inspection

    @Property(bool, notify=specChanged)
    def supportsTemplateRules(self) -> bool:
        from hr_toolkit.common.template_mapping import SUPPORTED_TOOLS
        return self._spec.tool_id in (*SUPPORTED_TOOLS, "salary_merge")

    @Property("QVariantList", notify=specChanged)
    def templateRuleSections(self):
        if self._template_settings_tool == "salary_merge":
            return self.salaryAliasSections
        from hr_toolkit.common.template_mapping import sections
        result = sections(self._template_settings_tool, self._header_name_rules.get(self._template_settings_tool, {}))
        names = [page["name"] for page in self._template_issue.get("sheets", [])] if self._template_issue.get("tool") == self._template_settings_tool else []
        for item in result:
            if item["kind"] == "sheets":
                item["options"] = list(dict.fromkeys([*item["options"], *names]))
        return result

    @Property("QVariantMap", notify=templateSelectionRequested)
    def templateSelectionData(self):
        return self._template_issue

    @Property("QVariantList", notify=specChanged)
    def templateSavedProfiles(self):
        from hr_toolkit.common.template_mapping import SUPPORTED_TOOLS, saved_choices
        tool = self._spec.tool_id
        if tool not in SUPPORTED_TOOLS or not self.templateSavedProfileCount:
            return []
        return saved_choices(tool, self._header_name_rules.get(tool, {}))

    @Property(int, notify=specChanged)
    def templateSavedProfileCount(self):
        # The main toolbar must not load spreadsheet parsers just to show a count.
        profiles = self._header_name_rules.get(self._spec.tool_id, {}).get("profiles", [])
        return len(profiles) if isinstance(profiles, list) else 0

    def _reset_template_session(self):
        self._template_session_rules = None
        self._template_session_snapshot = ""

    @Slot(str, result=bool)
    def deleteTemplateProfile(self, key):
        if self._busy or self._template_settings_tool != self._spec.tool_id:
            return False
        from hr_toolkit.common.template_mapping import clean_rules
        try:
            tool = self._spec.tool_id
            rules = clean_rules(tool, self._header_name_rules.get(tool, {}))
            rules["profiles"] = [p for p in rules["profiles"] if p["key"] != key]
            previous = dict(self._header_name_rules)
            self._header_name_rules[tool] = rules
            if not self._save_workspace_preferences():
                self._header_name_rules = previous
                raise ValueError("删除未能保存，请重试")
            self._reset_template_session()
            self.specChanged.emit()
            return True
        except (ValueError, TypeError, KeyError) as exc:
            self.notificationRequested.emit("未能删除选择", str(exc), "warning")
            return False

    @Slot(str)
    def editTemplateProfile(self, key):
        if self._busy or self._template_settings_tool != self._spec.tool_id:
            return
        from hr_toolkit.common.template_mapping import profile_issue
        try:
            tool = self._spec.tool_id
            self._template_issue = profile_issue(tool, self._header_name_rules.get(tool, {}), key)
            self._template_issue_project = str(self._project_path)
            self._template_input_snapshot = self._template_current_inputs()
            self.templateSelectionRequested.emit()
        except (ValueError, TypeError, KeyError) as exc:
            self.notificationRequested.emit("请重新选择列名", str(exc), "warning")

    @Slot()
    def reviewTemplateRules(self):
        if self._busy or not self.supportsTemplateRules:
            return
        self._template_settings_tool = self._spec.tool_id
        self.templateRulesRequested.emit()

    def _persist_salary_name_rules(self, rules):
        from hr_toolkit.tools.salary_headers import ALIAS_PROFILE_KEY, alias_rules
        previous = dict(self._header_name_rules)
        previous_profiles = self._salary_header_profiles
        old = alias_rules({ALIAS_PROFILE_KEY: previous.get("salary_merge", {})})
        changed = {role for role in ("detail", "summary") if old["sheets"].get(role) != rules["sheets"].get(role)}
        self._salary_header_profiles = {
            project: {key: profile for key, profile in profiles.items() if profile.get("role") not in changed}
            for project, profiles in previous_profiles.items()
        }
        self._header_name_rules["salary_merge"] = rules
        if not self._save_workspace_preferences():
            self._header_name_rules = previous
            self._salary_header_profiles = previous_profiles
            raise ValueError("名称规则未能保存，请重试")
        return changed

    @Slot(str, result=bool)
    def saveTemplateRules(self, payload):
        if self._busy or self._template_settings_tool != self._spec.tool_id:
            return False
        if self._template_settings_tool == "salary_merge":
            if self._salary_pending is not None:
                return self.saveSalaryAliasRules(payload)
            from hr_toolkit.tools.salary_headers import ALIAS_PROFILE_KEY, alias_rules
            try:
                rules = alias_rules({ALIAS_PROFILE_KEY: json.loads(payload)})
                self._persist_salary_name_rules(rules)
                self.notificationRequested.emit("名称已保存", "下次处理工资表时会使用这些名称。", "success")
                return True
            except (ValueError, TypeError, KeyError) as exc:
                self.notificationRequested.emit("名称未保存", str(exc), "warning")
                return False
        from hr_toolkit.common.template_mapping import catalog, clean_rules
        from hr_toolkit.common.header_aliases import normalize_alias
        try:
            values = json.loads(payload)
            specs = catalog(self._template_settings_tool)
            defaults = {r + "|" + n: a for r, s in specs.items() for n, a in s["fields"].items()}
            # 未改过的可选字段不因打开设置窗口而变为必填。
            values["fields"] = {k: v for k, v in values.get("fields", {}).items()
                                if {normalize_alias(x) for x in v} != {normalize_alias(x) for x in defaults.get(k, [])}}
            rules = clean_rules(self._template_settings_tool, values)
            previous = dict(self._header_name_rules)
            old = clean_rules(self._template_settings_tool, previous.get(self._template_settings_tool, {}))
            changed_roles = {role for role in specs if rules["sheets"].get(role) != old["sheets"].get(role)}
            changed_roles.update(key.split("|", 1)[0] for key in set(rules["fields"]) | set(old["fields"])
                                 if rules["fields"].get(key) != old["fields"].get(key))
            # 仅失效相关用途的旧记忆，避免改一个页名清空其他模板的列设置。
            changed_names = {name for role in changed_roles for name in [*old["sheets"].get(role, []), *rules["sheets"].get(role, [])]}
            rules["profiles"] = [p for p in old["profiles"] if p["role"] not in changed_roles
                                  and not (p["role"] == "_ignore" and p.get("sheet") in changed_names)]
            self._header_name_rules[self._template_settings_tool] = rules
            if not self._save_workspace_preferences():
                self._header_name_rules = previous
                raise ValueError("保存失败，请重试")
            self._reset_template_session()
            self.specChanged.emit()
            self.notificationRequested.emit("名称规则已保存", "请重新点击开始处理。不同工具的设置互不影响。", "success")
            return True
        except (ValueError, TypeError, KeyError) as exc:
            self.notificationRequested.emit("名称规则未保存", str(exc), "warning")
            return False

    @Slot(str)
    def saveTemplateChoice(self, payload):
        if self._busy:
            return
        from hr_toolkit.common.template_mapping import clean_rules, save_choice
        try:
            tool = self._template_issue.get("tool")
            if tool != self._spec.tool_id or self._template_issue_project != str(self._project_path):
                raise ValueError("当前工具或项目已改变，请重新开始处理")
            if self._template_input_snapshot != self._template_current_inputs():
                raise ValueError("选择的文件或处理选项已改变，请返回主界面重新开始处理")
            selection = json.loads(payload)
            editing = self._template_issue.get("editing_profile")
            persistent = self._header_name_rules.get(tool, {})
            base = self._template_session_rules if self._template_session_snapshot == self._template_input_snapshot else None
            rules = save_choice(tool, base if base is not None else persistent, self._template_issue, selection)
            if editing or selection.get("remember") is True:
                if editing:
                    persistent = clean_rules(tool, persistent)
                    if not any(p["key"] == editing for p in persistent["profiles"]):
                        raise ValueError("这条选择已删除，请返回重新选择")
                    persistent["profiles"] = [p for p in persistent["profiles"] if p["key"] != editing]
                saved = save_choice(tool, persistent, self._template_issue, selection)
                saved.pop("sheet_choices", None)
                previous = dict(self._header_name_rules)
                self._header_name_rules[tool] = saved
                if not self._save_workspace_preferences():
                    self._header_name_rules = previous
                    raise ValueError("对应关系未能保存，请重试")
                self.specChanged.emit()
            self._template_issue = {}
            if editing:
                self._reset_template_session()
                self.notificationRequested.emit("选择已修改", "下次处理相同表头时使用新选择。", "success")
                return
            self._template_session_rules = rules
            self._template_session_snapshot = self._template_input_snapshot
            self._append_log("已确认模板对应关系，继续处理。" + ("已记住，可在“模板设置”中修改或删除。" if selection.get("remember") is True else "本次选择不会保存到下次。"), "info")
            # 回到正常入口，重新检查项目状态和输入；不复用失败任务的运行目录。
            QTimer.singleShot(0, self._continue_template_run)
        except (ValueError, TypeError, KeyError) as exc:
            self.notificationRequested.emit("对应关系未保存", str(exc), "warning")
            if (self._template_issue.get("tool") == self._spec.tool_id
                    and self._template_issue_project == str(self._project_path)
                    and self._template_input_snapshot == self._template_current_inputs()):
                self.templateSelectionRequested.emit()
            else:
                self._template_issue = {}

    def _template_current_inputs(self):
        key = self._state_key()
        return json.dumps([str(self._project_path), key, self._input_states[key],
                           self._support_states[key], self._form_states[key]],
                          ensure_ascii=False, sort_keys=True, default=str)

    def _continue_template_run(self):
        if self._closed or self._shutdown_requested:
            return
        if self._busy or self._template_input_snapshot != self._template_current_inputs():
            self._reset_template_session()
            self.notificationRequested.emit("请重新确认列名", "当前处理状态已改变，请回到主界面重新开始处理。", "warning")
            return
        self._template_continuing = True
        try:
            self.runOrCancel()
        finally:
            self._template_continuing = False

    @Property("QVariantList", notify=salaryMappingChanged)
    def salaryAliasSections(self) -> list[dict[str, Any]]:
        from hr_toolkit.tools.salary_headers import ALIAS_PROFILE_KEY, ALIASES, FIELD_LABELS, SHEET_LABELS, SHEET_ALIASES, alias_rules

        rules = alias_rules({ALIAS_PROFILE_KEY: self._header_name_rules.get("salary_merge", {})})
        groups = self._salary_inspection.get("groups", [])
        columns = list(dict.fromkeys(c["label"] for g in groups for c in g.get("columns", [])))
        sheets = list(dict.fromkeys(name for g in groups for name in g.get("sheet_names", [])))
        return [{"kind": kind, "key": key, "label": label,
                 "selected": rules[kind].get(key, list(ALIASES[key]) if kind == "fields" else list(SHEET_ALIASES[key])),
                 "builtins": list(ALIASES[key]) if kind == "fields" else list(SHEET_ALIASES[key]),
                 "builtinRule": "名称包含“明细”或“汇总”的原有识别规则始终保留" if kind == "sheets" else "",
                 "options": columns if kind == "fields" else sheets}
                for kind, labels in (("fields", FIELD_LABELS), ("sheets", SHEET_LABELS)) for key, label in labels.items()]

    @Slot(str)
    def saveSalaryAliasRules(self, payload: str) -> bool:
        if self._busy or self._salary_pending is None or self._salary_project_key != str(self._project_path):
            return False
        from hr_toolkit.tools.salary_headers import ALIAS_PROFILE_KEY, alias_rules

        try:
            rules = alias_rules({ALIAS_PROFILE_KEY: json.loads(payload)})
            changed = self._persist_salary_name_rules(rules)
            self._salary_draft_profiles = {key: profile for key, profile in self._salary_draft_profiles.items()
                                           if key == ALIAS_PROFILE_KEY or profile.get("role") not in changed}
            self._salary_draft_profiles[ALIAS_PROFILE_KEY] = rules
            self._salary_selection_drafts = {}
            self._salary_hints = {}
            self._salary_force_dialog = True
            self._inspect_salary_in_background()
            return True
        except (ValueError, TypeError) as exc:
            self.notificationRequested.emit("名称规则未保存", str(exc), "warning")
            return False

    @Slot()
    def reviewSalaryHeaders(self) -> None:
        if self._busy or self._spec.tool_id != "salary_merge":
            return
        self._salary_force_next = True
        try:
            self.runOrCancel()
        finally:
            self._salary_force_next = False

    def _start_salary_inspection(self, invocation: ToolInvocation, *, force_dialog: bool = False) -> None:
        self._salary_pending = invocation
        self._salary_project_key = str(self._project_path)
        self._salary_draft_profiles = json.loads(json.dumps(
            self._salary_header_profiles.get(self._salary_project_key, {}), ensure_ascii=False,
        ))
        from hr_toolkit.tools.salary_headers import ALIAS_PROFILE_KEY
        self._salary_draft_profiles[ALIAS_PROFILE_KEY] = json.loads(json.dumps(self._header_name_rules.get("salary_merge", {}), ensure_ascii=False))
        self._salary_hints = {}
        self._salary_selection_drafts = {}
        self._salary_reset_profile_keys = set()
        self._salary_force_dialog = force_dialog
        self._run_progress_visible = False
        self._clear_logs()
        self._inspect_salary_in_background()

    def _inspect_salary_in_background(self) -> None:
        invocation = self._salary_pending
        if invocation is None:
            return
        self._set_busy(True)
        event = threading.Event()
        self._preview_cancel_event = event
        kwargs = {
            "existing_summary_path": invocation.kwargs.get("existing_summary_path"),
            "header_profiles": dict(self._salary_draft_profiles), "layout_hints": dict(self._salary_hints),
        }
        request = RunRequest("salary_merge", invocation.tool_name, invocation.group_name,
                             invocation.description, None, (invocation.args[0],), kwargs,
                             "hr_toolkit.tools.salary_merge", "inspect_salary_templates")
        self._append_log("正在检查工资表列头；不会修改原表。", "info")
        self._flush_logs()

        def worker() -> None:
            try:
                payload, _isolated = self._run_coordinator._business_call(
                    request, request.args, request.kwargs, event,
                    RunCallbacks(log=lambda text: self._logIncoming.emit(str(text), "warning"),
                                 progress=lambda c, t, text: self._logIncoming.emit(str(text), "info")),
                )
                if event.is_set():
                    raise RuntimeError("已取消列头检查")
            except Exception as exc:
                self._salaryInspectionReady.emit({}, str(exc))
                return
            self._salaryInspectionReady.emit(payload, "")

        threading.Thread(target=worker, daemon=True, name="HRToolkit-salary-headers").start()

    @Slot(object, str)
    def _apply_salary_inspection(self, payload: dict[str, Any], error: str) -> None:
        cancelled = self._preview_cancel_event is not None and self._preview_cancel_event.is_set()
        self._preview_cancel_event = None
        self._set_busy(False)
        if self._closed or self._shutdown_requested:
            self._salary_pending = None
            return
        if self._salary_project_key != str(self._project_path):
            self.cancelSalaryMappings()
            return
        if error or cancelled:
            self._append_log("列头检查已停止。" if cancelled else error, "warning" if cancelled else "error")
            self._flush_logs()
            if not cancelled:
                self.notificationRequested.emit("列头检查未完成", error, "error")
            self.cancelSalaryMappings()
            return
        self._salary_inspection = payload
        for group in payload.get("groups", []):
            draft = self._salary_selection_drafts.get(group["group_id"])
            if draft:
                group["selections"] = draft.get("selections", group["selections"])
                group["skip"] = bool(draft.get("skip"))
        self.salaryMappingChanged.emit()
        self._flush_logs()
        if self._salary_force_dialog or payload.get("issues") or any(not group["ready"] for group in payload.get("groups", [])):
            self.salaryMappingRequested.emit()
        else:
            self._launch_salary_with_profiles(self._salary_draft_profiles, [])

    @Slot(str, str, int, int, str)
    def rescanSalaryHeader(self, group_id: str, sheet: str, first: int, bottom: int, choices_json: str) -> None:
        if self._busy or self._salary_pending is None:
            return
        try:
            if (first, bottom) != (0, 0) and (not 1 <= first <= bottom <= 200 or bottom - first > 5):
                raise ValueError("表头范围须在 1—200 行内，连续表头最多 6 行")
            self._salary_selection_drafts = {x["group_id"]: x for x in json.loads(choices_json).get("groups", [])}
            group = next(g for g in self._salary_inspection["groups"] if g["group_id"] == group_id)
            if sheet not in group["sheet_names"]:
                raise ValueError("请选择列表中的工作表")
            for item in group["files"]:
                self._salary_hints[item["key"]] = {"sheet": sheet, "header_row": first, "header_bottom": bottom}
            self._salary_selection_drafts.pop(group_id, None)
            self._salary_force_dialog = True
            self._inspect_salary_in_background()
        except (ValueError, KeyError, StopIteration, TypeError) as exc:
            self.notificationRequested.emit("无法重新识别列头", str(exc), "warning")

    @Slot(str, str)
    def resetSalaryHeader(self, group_id: str, choices_json: str) -> None:
        if self._busy or self._salary_pending is None:
            return
        try:
            self._salary_selection_drafts = {x["group_id"]: x for x in json.loads(choices_json).get("groups", [])}
            group = next(g for g in self._salary_inspection["groups"] if g["group_id"] == group_id)
            # 相似表头可能是仍在使用的另一套模板，只重置当前模板。
            self._salary_draft_profiles.pop(group["key"], None)
            self._salary_reset_profile_keys.add(group["key"])
            self._salary_selection_drafts.pop(group_id, None)
            for item in group["files"]:
                self._salary_hints.pop(item["key"], None)
            self._salary_force_dialog = True
            self._inspect_salary_in_background()
        except (ValueError, KeyError, StopIteration, TypeError) as exc:
            self.notificationRequested.emit("无法恢复自动识别", str(exc), "warning")

    @Slot(str, bool)
    @Slot(str, bool, bool)
    def applySalaryMappings(self, choices_json: str, remember: bool, start_merge: bool = True) -> None:
        if self._busy or self._salary_pending is None:
            return
        if self._salary_project_key != str(self._project_path):
            self.notificationRequested.emit("工作项目已变化", "请在当前项目重新选择工资表。", "warning")
            self.cancelSalaryMappings()
            return
        from hr_toolkit.tools.salary_headers import ALIAS_PROFILE_KEY, MAX_PROFILES, profile_from_selection, remember_sheet_names

        try:
            payload = json.loads(choices_json)
            choices = {item["group_id"]: item for item in payload.get("groups", [])}
            profiles = dict(self._salary_draft_profiles)
            skipped: set[str] = set()
            included = 0
            for group in self._salary_inspection.get("groups", []):
                choice = choices.get(group["group_id"], {})
                if choice.get("skip"):
                    if group["role"] != "detail":
                        raise ValueError("已有汇总表不能跳过，请完成其列头对应或取消选择该汇总表")
                    skipped.update(item["key"] for item in group["files"])
                    continue
                selections = choice.get("selections", {})
                if not start_merge and (
                    not any(selections.values())
                    or (group["key"] in self._salary_reset_profile_keys and selections == group["builtin_selections"])
                ):
                    continue
                profile = profile_from_selection(group, selections)
                if group["saved"] or not group["ready"] or group.get("hinted") or selections != group["builtin_selections"]:
                    profiles[group["key"]] = profile
                if group["role"] == "detail":
                    included += len(group["files"])
            selected_issues = set(payload.get("skipped_issues", []))
            for issue in self._salary_inspection.get("issues", []) if start_merge else []:
                if not issue["skippable"] or issue["key"] not in selected_issues:
                    raise ValueError(f"请处理 {issue['name']} 的问题，或明确选择本次不合并该文件")
                skipped.add(issue["key"])
            if start_merge and included == 0:
                raise ValueError("至少保留一份工资明细表参与合并")
            if remember:
                selected_groups = [g for g in self._salary_inspection.get("groups", [])
                                   if not choices.get(g["group_id"], {}).get("skip")]
                profiles = remember_sheet_names(profiles, selected_groups)
            saved_profiles = {key: value for key, value in profiles.items() if key != ALIAS_PROFILE_KEY}
            if len(saved_profiles) > MAX_PROFILES:
                raise ValueError("当前项目已达到 200 套对应设置，请先恢复不再使用模板的自动识别")
            if remember:
                previous = self._salary_header_profiles.get(self._salary_project_key)
                previous_rules = dict(self._header_name_rules)
                self._header_name_rules["salary_merge"] = profiles[ALIAS_PROFILE_KEY]
                self._salary_header_profiles[self._salary_project_key] = saved_profiles
                if not self._save_workspace_preferences():
                    if previous is None:
                        self._salary_header_profiles.pop(self._salary_project_key, None)
                    else:
                        self._salary_header_profiles[self._salary_project_key] = previous
                    self._header_name_rules = previous_rules
                    raise ValueError("设置未能保存；可取消勾选记住设置，仅用于本次合并")
            if start_merge:
                self._launch_salary_with_profiles(profiles, sorted(skipped))
            else:
                self.cancelSalaryMappings()
                self.notificationRequested.emit("列头设置已保存", "对应设置已保存到当前项目。", "success")
        except (ValueError, TypeError, KeyError) as exc:
            self.notificationRequested.emit("请完善列头对应", str(exc), "warning")

    def _launch_salary_with_profiles(self, profiles: dict[str, Any], skipped: list[str]) -> None:
        invocation = self._salary_pending
        if invocation is None:
            return
        kwargs = dict(invocation.kwargs)
        kwargs.update(header_profiles=profiles, strict_headers=True, skipped_source_keys=skipped,
                      expected_sources=self._salary_inspection.get("expected_sources", []),
                      confirmed_layouts={item["key"]: item["layout"]
                                         for group in self._salary_inspection.get("groups", [])
                                         for item in group["files"] if item["key"] not in skipped})
        self._salary_pending = None
        self.salaryMappingClosed.emit()
        self._start_project_run(replace(invocation, kwargs=kwargs))

    @Slot()
    def cancelSalaryMappings(self) -> None:
        if self._busy:
            if self._preview_cancel_event is not None:
                self._preview_cancel_event.set()
            return
        self._salary_pending = None
        self._salary_inspection = {}
        self._salary_selection_drafts = {}
        self.salaryMappingClosed.emit()

    def _start_preview(self, invocation: ToolInvocation) -> None:
        if self._block_run_for_update():
            return
        from hr_toolkit.background_process import (
            BusinessProcessStartError,
            run_business_process,
        )

        if invocation.function_module in {"hr_toolkit.tools.folder_rename", "hr_toolkit.tools.rename_plan"}:
            self._rename_review_invocation = invocation
            self._rename_review_context = (self._state_key(), self._project_generation)
            arguments = dict(invocation.kwargs)
            if invocation.function_name == "rename_files_by_excel":
                arguments["mode"] = "excel"
            invocation = replace(invocation, function_module="hr_toolkit.tools.rename_plan",
                                 function_name="build_rename_plan", kwargs=arguments)
        self._set_busy(True)
        self._preview_cancel_event = threading.Event()
        self._clear_logs()
        self._append_log("正在生成改名预览…", "info")
        self._flush_logs()

        def worker() -> None:
            try:
                payload = None
                if self._run_coordinator.process_isolation_available:
                    try:
                        result = run_business_process(
                            module_name=invocation.function_module,
                            function_name=invocation.function_name,
                            args=invocation.args,
                            kwargs=invocation.kwargs,
                            cancel_event=self._preview_cancel_event,
                        )
                        payload = result.payload
                    except BusinessProcessStartError as exc:
                        self._run_coordinator.note_process_start_failure(exc)
                        fallback_message = (
                            "独立后台进程不可用，已自动切换兼容后台模式继续处理。"
                        )
                        runlog.log_line(f"{fallback_message} 原因：{exc}")
                        self._logIncoming.emit(fallback_message, "warning")
                if payload is None:
                    call_kwargs = dict(invocation.kwargs)
                    call_kwargs["cancelled"] = self._preview_cancel_event.is_set
                    direct_result = invocation.resolve_function()(
                        *invocation.args,
                        **call_kwargs,
                    )
                    payload = ProjectRunCoordinator._payload(direct_result)
            except Exception as exc:
                self._previewFailed.emit(str(exc))
                return
            self._previewReady.emit(payload)

        threading.Thread(target=worker, daemon=True, name="HRToolkit-rename-preview").start()

    @Slot(object)
    def _apply_preview(self, payload: dict[str, Any]) -> None:
        cancelled = self._preview_cancel_event is not None and self._preview_cancel_event.is_set()
        self._preview_cancel_event = None
        self._set_busy(False)
        if self._closed or self._shutdown_requested or cancelled:
            return
        if payload.get("schema") == 1 and "rows" in payload:
            self._append_log(f"预览已生成：共 {len(payload['rows'])} 项，请在完整预览中核对和调整。", "info")
            self._rename_review.load(payload)
            return
        self.notificationRequested.emit("预览失败", "改名预览格式无效，请重新预览。", "error")

    @constant_property(QObject)
    def presentation(self):
        return self._presentation

    @constant_property(QObject)
    def renameReview(self):
        return self._rename_review

    @Slot(object)
    def _execute_reviewed_rename(self, plan) -> None:
        if (self._busy or self._closed or self._shutdown_requested or self._rename_review_invocation is None
                or self._rename_review_context != (self._state_key(), self._project_generation)):
            self.notificationRequested.emit("请重新预览", "项目或工具已变化，未执行改名。", "warning")
            return
        invocation = replace(self._rename_review_invocation, function_module="hr_toolkit.tools.rename_plan",
                             function_name="execute_rename_plan", preview=False,
                             kwargs={"root_dir": Path(plan["root_dir"]), "plan": plan})
        self._rename_review_invocation = None
        self._start_project_run(invocation)

    @Slot(str)
    def _apply_preview_error(self, message: str) -> None:
        self._preview_cancel_event = None
        self._set_busy(False)
        self._last_run_by_key[self._state_key()] = (datetime.now().strftime("%H:%M"), False)
        self.specChanged.emit()
        self.notificationRequested.emit("预览失败", message, "error")

    @Slot(str, bool)
    def confirmAction(self, token: str, accepted: bool) -> None:
        if token != self._pending_confirmation:
            return
        self._pending_confirmation = None
        action = self._pending_confirmation_action
        self._pending_confirmation_action = None
        if not accepted:
            if action and action[0] == "update" and isinstance(action[1], UpdateInfo) and action[1].mandatory:
                QCoreApplication.quit()
            return
        if not action:
            return
        action_name, payload = action
        if action_name == "material-delete":
            try:
                result = self._material_preferences.remove_material(str(payload))
            except ValueError as exc:
                self.notificationRequested.emit("无法删除材料", str(exc), "warning")
                return
            self._material_mutated()
            message = f"已删除自定义材料“{payload}”。"
            if result.updated_presets:
                message += "\n已更新预设：" + "、".join(result.updated_presets)
            if result.removed_presets:
                message += "\n已删除空预设：" + "、".join(result.removed_presets)
            self.notificationRequested.emit("材料已删除", message, "success")
            return
        if action_name == "preset-delete":
            try:
                self._material_preferences.delete_preset(str(payload))
            except ValueError as exc:
                self.notificationRequested.emit("无法删除预设", str(exc), "warning")
                return
            names = self._material_preferences.preset_names
            self._material_preset_name = names[0] if names else ""
            self._material_mutated()
            return
        if action_name == "history-trash":
            self._move_history_to_trash(str(payload))
            return
        if action_name == "project-trash":
            self._move_project_batch_to_trash(str(payload))
            return
        if action_name == "update" and isinstance(payload, UpdateInfo):
            self._accept_update(payload)
            return
        if action_name == "close":
            self._begin_shutdown()
            return

    def _start_project_run(self, invocation: ToolInvocation) -> None:
        if self._block_run_for_update():
            return
        store = self._project_store
        if store is None:
            return
        from hr_toolkit.common.template_mapping import SUPPORTED_TOOLS
        if invocation.tool_id in SUPPORTED_TOOLS:
            self._template_settings_tool = invocation.tool_id
            rules = self._header_name_rules.get(invocation.tool_id, {})
            if self._template_session_snapshot == self._template_current_inputs() and self._template_session_rules is not None:
                rules = self._template_session_rules
            invocation = replace(invocation, kwargs={**invocation.kwargs,
                "template_rules": json.loads(json.dumps(rules, ensure_ascii=False))})
            self._template_issue_project = str(self._project_path)
            self._template_input_snapshot = self._template_current_inputs()
        request = RunRequest(
            tool_id=invocation.tool_id,
            tool_name=invocation.tool_name,
            group_name=invocation.group_name,
            description=invocation.description,
            function=None,
            args=invocation.args,
            kwargs=invocation.kwargs,
            function_module=invocation.function_module,
            function_name=invocation.function_name,
        )
        self._set_busy(True)
        self._result_context = None
        self._result_files = []
        self._result_notices.clear()
        self._result_notice_rows = []
        self._result_notice_groups.clear()
        self._result_notice_counts = {}
        self._result_notice_filter = "全部"
        self._notify_last_result_changed(force=True)
        self._run_progress_visible = (invocation.tool_id == "material_collector"
                                      or invocation.function_module == "hr_toolkit.tools.rename_plan")
        self._run_progress_current = self._run_progress_total = 0
        self._run_progress_message = "正在准备项目资料，总量尚未确定"
        self._run_progress_started = self._run_progress_updated = time.monotonic()
        self._run_progress_elapsed = self._run_progress_wait = 0
        self.runProgressChanged.emit()
        if self._run_progress_visible:
            self._run_progress_timer.start()
        self._clear_logs()
        self._append_log(f"开始{invocation.tool_name}，请稍候…", "info")
        if invocation.tool_id == "personnel_reconcile":
            self._append_log("提示：核对以本次导入资料为准，请提供同一事业部、核对范围内的完整记录，避免将未提供的记录误判为缺失。", "info")
        self._flush_logs()
        callbacks = RunCallbacks(
            log=lambda message: self._logIncoming.emit(str(message), "info"),
            progress=self._queue_run_progress,
            success=lambda payload, result_dir, elapsed, isolated: self._runSuccess.emit(payload, str(result_dir), float(elapsed), bool(isolated)),
            error=lambda error: self._runError.emit(str(error)),
            stopped=self._runStopped.emit,
            finished=self._runFinished.emit,
        )
        self._incoming_progress_timer.start()
        if not self._run_coordinator.start(store, request, callbacks):
            self._incoming_progress_timer.stop()
            self._run_progress_timer.stop()
            self._set_busy(False)
            self.notificationRequested.emit("已有任务正在处理", "请等待当前任务结束。", "warning")

    def _queue_run_progress(self, current: int, total: int, message: str) -> None:
        # Even a throttled producer can emit thousands of phase completions.
        # Coalesce BEFORE crossing into Qt, so its event queue stays bounded.
        if self._closed:
            return
        # Reconciliation's zero-total notice is a log-only diagnostic, not
        # a task stage. Bypass progress coalescing so later stages cannot
        # replace it or briefly expose it below the action buttons.
        if (self._spec.tool_id == "personnel_reconcile" and current == 0 and total == 0
                and str(message).startswith("提示：")):
            self._logIncoming.emit(str(message), "warning_emphasis")
            return
        with self._incoming_progress_lock:
            self._incoming_progress = (int(current), int(total), str(message))

    @Slot()
    def _drain_run_progress(self) -> None:
        with self._incoming_progress_lock:
            payload = self._incoming_progress
            self._incoming_progress = None
        if payload is not None:
            self._apply_run_progress(*payload)

    @Slot(int, int, str)
    def _apply_run_progress(self, current: int, total: int, message: str) -> None:
        if self._run_progress_visible:
            self._run_progress_pending = (current, total, message)
            if not self._run_progress_flush_timer.isActive():
                self._run_progress_flush_timer.start()
            return
        if not self._stop_requested:
            self._run_progress_message = message
        self._run_progress_current = max(0, current)
        self._run_progress_total = max(0, total)
        self.runProgressChanged.emit()
        self._append_log(message, "info")

    @Slot()
    def _flush_material_progress(self) -> None:
        self._run_progress_flush_timer.stop()
        payload = self._run_progress_pending
        if payload is None:
            return
        self._run_progress_pending = None
        current, total, message = payload
        self._run_progress_current = max(0, current)
        self._run_progress_total = max(0, total)
        if not self._stop_requested:
            self._run_progress_message = message
        self._run_progress_updated = time.monotonic()
        self._run_progress_wait = 0
        self.runProgressChanged.emit()
        self._append_log(message, "info")

    @Slot(object, str, float, bool)
    def _apply_run_success(self, payload, result_dir: str, elapsed: float, isolated: bool) -> None:
        self._reset_template_session()
        self._drain_run_progress()
        self._flush_material_progress()
        if self._run_progress_visible:
            self._run_progress_message = "全部处理完成，结果已登记保存。"
            self.runProgressChanged.emit()
        self._last_result_dir = Path(result_dir)
        self._result_context = (self._state_key(), self._project_generation)
        self._result_files = self._result_output_paths(self._spec.tool_id, payload, self._last_result_dir)
        self._last_run_by_key[self._state_key()] = (datetime.now().strftime("%H:%M"), True)
        self.specChanged.emit()
        warnings = list(payload.get("warnings", [])) if isinstance(payload, dict) else []
        self._result_notice_rows = [{"text": str(warning), "category": self._notice_category(self._spec.tool_id, str(warning))} for warning in warnings]
        self._result_notice_groups.clear()
        self._result_notice_counts = {}
        for row in self._result_notice_rows:
            category = row["category"]
            self._result_notice_counts[category] = self._result_notice_counts.get(category, 0) + 1
        self._result_notice_filter = "全部"
        self._result_notices.set_items(self._result_notice_rows)
        self._notify_last_result_changed(force=True)
        mode_text = "独立进程" if isolated else "后台线程"
        self._append_log(f"处理完成，用时 {elapsed:.1f} 秒（{mode_text}）。", "success")
        completion_message = "结果已安全保存到当前项目。"
        if isinstance(payload, dict) and payload.get("rename_ledger"):
            completion_message = (f"已改名 {payload['operation_count']} 项，排除 {payload['excluded_count']} 项，"
                                  f"名称不变 {payload['unchanged_count']} 项。原目录未修改。\n"
                                  f"结果目录：{payload['renamed_root']}\n改名记录和清单已保存到本批次处理结果。")
            self._append_log(completion_message, "info")
        if self._run_progress_visible and isinstance(payload, dict) and self._spec.tool_id == "material_collector":
            copied_count = sum(bool(item.get("target_path")) for item in payload.get("matches", []))
            completion_message = f"已提取 {copied_count} 个资料文件。"
            if payload.get("review_path"):
                completion_message += "另有资料待核对，请打开结果中的《资料待确认.xlsx》。"
            self._append_log(completion_message, "warning" if payload.get("review_path") else "info")
        if warnings:
            completion_message += f"\n另有 {len(warnings)} 条处理提醒/运行信息，可在结果提醒区查看全部。"
            self._append_log(f"共有 {len(warnings)} 条提醒。", "warning")
            for index, warning in enumerate(warnings):
                if index < 30 or str(warning).startswith(("未处理工作表：", "用户已确认：")):
                    self._append_log(str(warning), "warning")
        self._flush_logs()
        self.notificationRequested.emit("处理完成", completion_message, "success")
        self.refreshWorkspace()

    @Slot(str)
    def _apply_run_error(self, message: str) -> None:
        self._drain_run_progress()
        self._flush_material_progress()
        if self._run_progress_visible:
            self._run_progress_message = "处理失败：" + message
            self.runProgressChanged.emit()
        self._last_run_by_key[self._state_key()] = (datetime.now().strftime("%H:%M"), False)
        self.specChanged.emit()
        from hr_toolkit.common.template_mapping import ERROR_PREFIX
        if ERROR_PREFIX in message:
            try:
                issue, _ = json.JSONDecoder().raw_decode(message.split(ERROR_PREFIX, 1)[1])
                if issue.get("tool") == self._spec.tool_id:
                    self._template_issue = issue
                    self._append_log("需要确认模板对应关系：" + issue.get("message", ""), "warning")
                    self._flush_logs()
                    self.templateSelectionRequested.emit()
                    self.refreshWorkspace()
                    return
            except (ValueError, TypeError, AttributeError):
                pass
        self._append_log(f"处理失败：{message}", "error")
        self._reset_template_session()
        self._flush_logs()
        self.notificationRequested.emit("处理失败", message, "error")
        self.refreshWorkspace()

    @Slot()
    def _apply_run_stopped(self) -> None:
        self._reset_template_session()
        self._drain_run_progress()
        self._flush_material_progress()
        if self._run_progress_visible:
            self._run_progress_message = "已停止，保留最后实际完成的进度。"
            self.runProgressChanged.emit()
        self._append_log("本次处理已安全停止。", "warning")
        self._flush_logs()
        self.notificationRequested.emit("已停止", "本次处理已安全结束，未完成批次可在项目中追溯。", "info")
        self.refreshWorkspace()

    @Slot()
    def _apply_run_finished(self) -> None:
        self._incoming_progress_timer.stop()
        self._drain_run_progress()
        self._flush_material_progress()
        self._refresh_run_progress_clock()
        self._run_progress_timer.stop()
        self._flush_logs()
        self._set_busy(False)

    @Slot()
    def _flush_logs(self) -> None:
        if hasattr(self, "_log_flush_timer") and self._log_flush_timer.isActive():
            self._log_flush_timer.stop()
        if not hasattr(self, "_log_buffer") or not self._log_buffer:
            return
        buffered = self._log_buffer
        self._log_buffer = []
        self._log_model.append_batch(buffered, maximum=MAX_LOG_ROWS)

    def _clear_logs(self) -> None:
        if hasattr(self, "_log_flush_timer") and self._log_flush_timer.isActive():
            self._log_flush_timer.stop()
        if hasattr(self, "_log_buffer"):
            self._log_buffer.clear()
        self._log_model.clear()

    @Slot()
    def copyRunLogs(self) -> None:
        self._flush_logs()
        text = "\n".join(
            "{} {}".format(item.get("time", ""), self._presentation.translate(item.get("text", ""), self._presentation.language)).strip()
            for item in self._log_model.items()
        )
        QGuiApplication.clipboard().setText(text)

    @Slot(str, str)
    def _append_log(self, text: str, level: str = "info") -> None:
        self._log_buffer.append(
            {"time": datetime.now().strftime("%H:%M:%S"), "text": str(text), "level": str(level)}
        )
        if len(self._log_buffer) >= 30:
            self._flush_logs()
        elif hasattr(self, "_log_flush_timer") and not self._log_flush_timer.isActive():
            self._log_flush_timer.start(50)

    # ------------------------------------------------------------------
    # AI 智能助手：云端对话 + 表格分析 + 工具指导。
    # AI 模块全部懒加载，不进入启动路径；网络请求在守护线程中执行。
    # ------------------------------------------------------------------
    def _ai_settings_obj(self):
        if self._ai_settings is None:
            from hr_toolkit.ai.config import load_ai_settings

            self._ai_settings = load_ai_settings()
        return self._ai_settings

    def _ai_session_obj(self):
        if self._ai_session is None:
            from hr_toolkit.ai.assistant import AiAssistantSession

            self._ai_session = AiAssistantSession(self._ai_settings_obj())
        return self._ai_session

    # ---- 对话历史 -----------------------------------------------------
    def _ai_store_obj(self):
        if self._ai_conversation_store is None:
            from hr_toolkit.ai.history import ConversationStore

            self._ai_conversation_store = ConversationStore()
        return self._ai_conversation_store

    def _ai_dark_theme(self) -> bool:
        return str(getattr(self._presentation, "theme", "light")) == "dark"

    def _ai_render(self, text: str) -> str:
        return self._ai_rendered(text)["html"]

    def _ai_rendered(self, text: str) -> dict:
        from hr_toolkit.ai.markdown import render_markdown_payload

        return render_markdown_payload(
            text, dark=self._ai_dark_theme(), font_family=self._ai_ui_font_family()
        )

    @staticmethod
    def _ai_ui_font_family() -> str:
        """当前界面字体。

        Qt 富文本的表格单元格不继承控件字体，模型给的 Markdown 表格如果不显式
        带上字族，表里的中文会掉到另一套字去（看着像等宽宽体），跟正文对不上。
        """
        application = QGuiApplication.instance()
        if application is None:
            return ""
        try:
            return str(application.font().family() or "")
        except Exception:  # pragma: no cover - 只在异常 Qt 环境里兜底
            return ""

    def _ai_refresh_history(self) -> None:
        current = self._ai_conversation.conversation_id if self._ai_conversation else ""
        self._ai_conversation_model.set_items(
            [dict(summary, active=summary["id"] == current)
             for summary in self._ai_store_obj().summaries(query=self._ai_history_query)]
        )
        self.aiHistoryChanged.emit()

    def _ai_ensure_conversation(self, title_hint: str = ""):
        if self._ai_conversation is None:
            from hr_toolkit.ai.history import make_title

            from hr_toolkit.ai.history import ConversationRecord
            import uuid
            self._ai_conversation = ConversationRecord(
                uuid.uuid4().hex, make_title(title_hint), time.time()
            )
        return self._ai_conversation

    def _ai_sync_conversation(self) -> None:
        """把面板上现有的消息写回当前对话并落盘；空对话直接丢弃不占历史。"""
        if self._ai_conversation is None:
            return
        rows = self._ai_chat_model.items()
        store = self._ai_store_obj()
        if not rows:
            store.remove(self._ai_conversation.conversation_id)
            self._ai_refresh_history()
            return
        self._ai_conversation.messages = rows
        self._ai_conversation.draft = self._ai_draft
        try:
            store.upsert(self._ai_conversation)
        except OSError:
            self.notificationRequested.emit("Sage", "无法保存对话历史，请检查磁盘权限或删除不再需要的旧对话。", "warning")
            return
        self._ai_refresh_history()

    def _ai_restore_record(self, record) -> None:
        rows = []
        for item in record.messages:
            content = str(item.get("content") or "")
            if item.get("role") == "assistant" and item.get("status") == "stopped" and not content:
                content = self._presentation.translate("上次回复被中断，请重试。", self._presentation.language)
            rows.append(
                {
                    **item,
                    "role": str(item.get("role") or "assistant"),
                    "content": content,
                    **(self._ai_rendered(content) if item.get("role") == "assistant" else {"html": "", "blocks": []}),
                    "streaming": False,
                    "time": str(item.get("time") or ""),
                    "attachments": item.get("attachments") or [],
                }
            )
        self._ai_chat_model.set_items(rows)
        self._ai_attachment_model.clear()
        self._ai_session_obj().load_history(record.messages)
        self._ai_conversation = record
        self._ai_draft = str(getattr(record, "draft", "") or "")
        self._ai_prune_image_cache()
        self.aiChanged.emit()

    def _ai_prune_image_cache(self) -> None:
        """清掉不再引用的粘贴图片：缓存目录不该无限长大。"""
        if self._ai_session is None:
            return
        try:
            from hr_toolkit.ai.images import prune_image_cache

            retained = self._ai_session.retained_image_paths()
            retained.extend(self._ai_store_obj().retained_image_paths())
            prune_image_cache(retained)
        except Exception:
            return

    @Slot()
    def aiActivate(self) -> None:
        """面板打开时恢复最近一次对话（AI 模块保持懒加载，不进启动路径）。"""
        if self._ai_busy or self._ai_conversation is not None or len(self._ai_chat_model) > 0:
            return
        if self._ai_activated:
            return
        self._ai_activated = True
        record = self._ai_store_obj().latest()
        if record is not None and record.messages:
            self._ai_restore_record(record)
            self.aiChanged.emit()
        self._ai_refresh_history()

    @Slot()
    def _rerender_ai_messages(self) -> None:
        for row in range(len(self._ai_chat_model)):
            item = self._ai_chat_model.item_at(row)
            if item is None or item.get("role") != "assistant":
                continue
            item.update(self._ai_rendered(item.get("content") or ""))
            self._ai_chat_model.update_at(row, item)

    @constant_property(QObject)
    def aiChatModel(self):
        return self._ai_chat_model

    @constant_property(QObject)
    def aiAttachmentModel(self):
        return self._ai_attachment_model

    @Property(bool, notify=aiChanged)
    def aiHasPendingImage(self) -> bool:
        """待发附件里有没有图：决定要不要提示「当前模型读不了图」。

        只在真的要发图时才提醒，平时不占一行位置。
        """
        if self._ai_session is None:
            return False
        return any(item.is_image for item in self._ai_session.pending_attachments())

    @constant_property(QObject)
    def aiConversationModel(self):
        return self._ai_conversation_model

    @Slot(str)
    def aiCopyMessage(self, text: str) -> None:
        from .compat import QApplication

        board = QApplication.clipboard()
        if board is not None:
            board.setText(str(text or ""))

    @Slot(result=str)
    def aiCurrentConversationTitle(self) -> str:
        if self._ai_conversation is None:
            return ""
        return self._ai_conversation.title

    @Slot()
    def aiNewConversation(self) -> None:
        if self._ai_busy or self._ai_preparing:
            return
        self._ai_sync_conversation()
        self._ai_conversation = None
        self._ai_chat_model.clear()
        self._ai_attachment_model.clear()
        self._ai_draft = ""
        self._ai_session_obj().reset_conversation()
        self._ai_refresh_history()
        self.aiChanged.emit()

    @Slot(str)
    def aiOpenConversation(self, conversation_id: str) -> None:
        if self._ai_busy or self._ai_preparing:
            return
        record = self._ai_store_obj().get(str(conversation_id))
        if record is None:
            return
        if self._ai_conversation is not None:
            self._ai_sync_conversation()
        self._ai_restore_record(record)
        self._ai_refresh_history()
        self.aiChanged.emit()

    @Slot(str)
    def aiDeleteConversation(self, conversation_id: str) -> None:
        if self._ai_busy or self._ai_preparing:
            return
        target = str(conversation_id)
        if self._ai_conversation is not None and self._ai_conversation.conversation_id == target:
            self._ai_conversation = None
            self._ai_chat_model.clear()
            self._ai_attachment_model.clear()
            self._ai_draft = ""
            self._ai_session_obj().reset_conversation()
        self._ai_store_obj().remove(target)
        self._ai_prune_image_cache()
        self._ai_refresh_history()
        self.aiChanged.emit()

    @Slot(str, str, result=bool)
    def aiRenameConversation(self, conversation_id: str, title: str) -> bool:
        if not str(title or "").strip():
            return False
        ok = self._ai_store_obj().rename(str(conversation_id), title)
        if ok and self._ai_conversation is not None:
            if self._ai_conversation.conversation_id == str(conversation_id):
                self._ai_conversation.title = str(title).strip()
        self._ai_refresh_history()
        self.aiHistoryChanged.emit()
        return ok

    @Slot(str)
    def aiSearchHistory(self, query: str) -> None:
        """按标题或正文过滤历史列表；空串恢复全部。"""
        self._ai_history_query = str(query or "").strip()
        self._ai_refresh_history()

    @Slot(str)
    def aiSaveDraft(self, text: str) -> None:
        """记住输入框草稿：切走再回来不丢。只在已有对话时落盘。"""
        self._ai_draft = str(text or "")
        if self._ai_conversation is not None:
            try:
                self._ai_store_obj().set_draft(
                    self._ai_conversation.conversation_id, self._ai_draft
                )
            except OSError:
                self.notificationRequested.emit("Sage", "无法保存对话历史，请检查磁盘权限或删除不再需要的旧对话。", "warning")

    @Property(str, notify=aiChanged)
    def aiDraft(self) -> str:
        return self._ai_draft

    @Property(str, notify=aiChanged)
    def aiConversationId(self) -> str:
        return self._ai_conversation.conversation_id if self._ai_conversation else ""

    @Slot(int, str)
    def aiEditMessage(self, row: int, text: str) -> None:
        """编辑并重发：从这条用户消息起截断，用新内容重新问一次。"""
        if self._ai_busy or self._ai_preparing:
            return
        index = int(row)
        if index < 0 or index >= len(self._ai_chat_model):
            return
        item = self._ai_chat_model.item_at(index)
        if item is None or item.get("role") != "user":
            return
        question = str(text or "").strip()
        if not question:
            return
        if len(question) > 10000:
            self.notificationRequested.emit("Sage", "问题过长，请缩短到 10000 字以内。", "warning")
            return
        remaining = self._ai_chat_model.items()[:index]
        attachment_rows = item.get("attachments") or []
        while len(self._ai_chat_model) > index:
            self._ai_chat_model.remove_at(len(self._ai_chat_model) - 1)
        self._ai_session_obj().load_history(remaining)
        if not remaining and self._ai_conversation is not None:
            from hr_toolkit.ai.history import make_title
            self._ai_conversation.title = make_title(question)
        context_body = str(item.get("apiContent") or "")
        old_question = str(item.get("content") or "")
        if context_body and old_question and context_body.endswith(old_question):
            context_body = context_body[:-len(old_question)] + question
        elif context_body:
            context_body += "\nUpdated user question: " + question
        self._ai_begin_turn(question, attachment_rows, [], context_body=context_body or None)

    @Property("QVariantList", notify=aiSettingsChanged)
    def aiModelOptions(self):
        """当前服务商可切换的模型（面板里的模型菜单）。带 vision 标记。"""
        try:
            settings = self._ai_settings_obj()
            preset = settings.preset()
            config = settings.provider_config()
        except Exception:
            return []
        from hr_toolkit.ai.config import model_supports_vision

        current = config.resolved_model(preset)
        return [
            {
                "value": name,
                "label": name,
                "selected": name == current,
                "vision": model_supports_vision(preset.provider_id, name),
                # 正在用的模型不给删，否则会把当前配置删空。
                "removable": name != current,
            }
            for name in config.model_choices(preset)
        ]

    @Property(bool, notify=aiSettingsChanged)
    def aiVisionCapable(self) -> bool:
        """当前模型能否读图（启发式，仅用于界面提示，不拦截请求）。"""
        try:
            settings = self._ai_settings_obj()
            preset = settings.preset()
            config = settings.provider_config()
        except Exception:
            return False
        from hr_toolkit.ai.config import model_supports_vision

        return bool(model_supports_vision(preset.provider_id, config.resolved_model(preset)))

    @Property(str, notify=aiSettingsChanged)
    def aiVisionHint(self) -> str:
        """模型不吃图时给一句可操作的提示。"""
        if self.aiVisionCapable:
            return ""
        return "当前模型可能读不了图片，请在模型菜单切换到带 VL / Vision 的视觉模型。"

    @Slot(str, result=bool)
    def aiSelectProvider(self, provider: str) -> bool:
        """切换服务商。

        每个服务商各有自己的 Key / 模型 / 用户自建模型列表，所以这里只动
        ``active_provider``；切换过去时那家原来配好的东西原样还在。
        """
        from hr_toolkit.ai.config import AiConfigError, save_ai_settings

        key = str(provider or "").strip()
        if not key:
            return False
        try:
            from copy import deepcopy
            settings = deepcopy(self._ai_settings_obj())
            if key == settings.active_provider:
                return True
            preset = settings.preset(key)  # 未知 id 会抛 AiConfigError
            settings.provider_config(key)  # 确保这一家的配置节存在
            settings.active_provider = preset.provider_id
            save_ai_settings(settings)
            self._ai_settings = settings
        except (AiConfigError, OSError):
            return False
        if self._ai_session is not None and not self._ai_busy:
            self._ai_session.refresh_settings(settings)
        self.aiSettingsChanged.emit()
        return True

    @Slot(str, result="QVariantList")
    def aiModelChoicesFor(self, provider: str) -> list:
        """某个服务商可选的模型名（当前在用的 + 预置/自建列表，去重保序）。"""
        try:
            settings = self._ai_settings_obj()
            preset = settings.preset(str(provider or "").strip())
            return list(settings.provider_config(preset.provider_id).model_choices(preset))
        except Exception:
            return []

    @Slot(str, result=bool)
    def aiSelectModel(self, model: str) -> bool:
        name = str(model or "").strip()
        if not name:
            return False
        try:
            from copy import deepcopy
            settings = deepcopy(self._ai_settings_obj())
            preset = settings.preset()
            config = settings.provider_config()
        except Exception:
            return False
        if name == config.resolved_model(preset):
            return True
        from hr_toolkit.ai.config import AiConfigError, save_ai_settings, validate_model

        try:
            config.model = validate_model(name)
            save_ai_settings(settings)
            self._ai_settings = settings
        except (AiConfigError, OSError) as exc:
            self.aiTestFinished.emit(False, str(exc))
            return False
        if self._ai_session is not None and not self._ai_busy:
            self._ai_session.refresh_settings(settings)
        self.aiSettingsChanged.emit()
        return True

    @Slot(str, result=bool)
    def aiAddModel(self, model: str) -> bool:
        """把用户自己填的模型加进当前服务商的模型列表（可加多个）。"""
        from hr_toolkit.ai.config import AiConfigError, save_ai_settings

        name = str(model or "").strip()
        if not name:
            return False
        try:
            from copy import deepcopy
            settings = deepcopy(self._ai_settings_obj())
            preset = settings.preset()
            config = settings.provider_config()
            if not config.add_model(preset, name):
                self.aiTestFinished.emit(False, f"模型「{name}」已经在列表里了。")
                return False
            save_ai_settings(settings)
            self._ai_settings = settings
        except (AiConfigError, OSError) as exc:
            self.aiTestFinished.emit(False, str(exc))
            return False
        if self._ai_session is not None and not self._ai_busy:
            self._ai_session.refresh_settings(settings)
        # 加完直接切过去：用户加它就是为了用它。
        return self.aiSelectModel(name)

    @Slot(str, result=bool)
    def aiRemoveModel(self, model: str) -> bool:
        """从列表里移除一个模型；正在用的那个不允许移除。"""
        from hr_toolkit.ai.config import AiConfigError, save_ai_settings

        name = str(model or "").strip()
        if not name:
            return False
        try:
            from copy import deepcopy
            settings = deepcopy(self._ai_settings_obj())
            preset = settings.preset()
            config = settings.provider_config()
            if name == config.resolved_model(preset):
                self.aiTestFinished.emit(False, "这是正在使用的模型，请先切换到别的模型。")
                return False
            if not config.remove_model(preset, name):
                self.aiTestFinished.emit(False, f"列表里没有模型「{name}」。")
                return False
            save_ai_settings(settings)
            self._ai_settings = settings
        except (AiConfigError, OSError) as exc:
            self.aiTestFinished.emit(False, str(exc))
            return False
        if self._ai_session is not None and not self._ai_busy:
            self._ai_session.refresh_settings(settings)
        self.aiSettingsChanged.emit()
        return True

    @Property(bool, notify=aiChanged)
    def aiBusy(self) -> bool:
        return self._ai_busy or self._ai_preparing

    @Property(bool, notify=aiSettingsChanged)
    def aiReady(self) -> bool:
        return self._ai_settings_obj().is_ready()

    @Property(str, notify=aiSettingsChanged)
    def aiSetupMessage(self) -> str:
        return "；".join(self._ai_settings_obj().problems())

    @Property(str, notify=aiSettingsChanged)
    def aiActiveProvider(self) -> str:
        return self._ai_settings_obj().active_provider

    @Property(str, notify=aiSettingsChanged)
    def aiActiveProviderLabel(self) -> str:
        return self._ai_settings_obj().preset().label

    @Property(str, notify=aiSettingsChanged)
    def aiActiveModel(self) -> str:
        settings = self._ai_settings_obj()
        return settings.provider_config().resolved_model(settings.preset())

    @Property(str, notify=aiSettingsChanged)
    def aiProviderDefaultModel(self) -> str:
        """当前服务商的官方默认模型；用作「添加模型」输入框的示例。"""
        return self._ai_settings_obj().preset().default_model

    @Property(str, notify=aiSettingsChanged)
    def aiModelsNote(self) -> str:
        """模型菜单底部那句来源说明，省得用户对着一串模型名不知道是什么。"""
        return self._ai_settings_obj().preset().models_note

    @Property("QVariantList", notify=aiStatusChanged)
    def aiStatusPhrases(self):
        """Waiting status for the attachments actually sent."""
        from hr_toolkit.ai.status import default_status_phrases

        return list(self._ai_status_phrases) or default_status_phrases()

    @Property("QVariantList", notify=aiSettingsChanged)
    def aiProviderOptions(self):
        from hr_toolkit.ai.config import PROVIDER_PRESETS

        return [
            {"value": preset.provider_id, "label": preset.label}
            for preset in PROVIDER_PRESETS.values()
        ]

    @Property("QVariantList", notify=aiSettingsChanged)
    def aiProviderMenuOptions(self):
        """面板模型菜单顶部那一组服务商行：当前生效的那家打勾。"""
        from hr_toolkit.ai.config import PROVIDER_PRESETS

        active = self._ai_settings_obj().active_provider
        return [
            {
                "value": preset.provider_id,
                "label": preset.label,
                "selected": preset.provider_id == active,
            }
            for preset in PROVIDER_PRESETS.values()
        ]

    @Property("QVariantList", notify=aiChanged)
    def aiSuggestions(self):
        return [
            "对比我附加的两张表的差异",
            "谁的增长值更好？",
            "工资怎么按入职公司拆分？",
            "周报几点算超时？",
        ]

    @Slot(str, str, str, str)
    def aiSaveSettings(self, provider: str, api_key: str, model: str, endpoint: str) -> bool:
        from hr_toolkit.ai.config import AiConfigError, save_ai_settings

        try:
            from copy import deepcopy
            settings = deepcopy(self._ai_settings_obj())
            preset = settings.preset(str(provider).strip() or "minimax")
            settings.active_provider = preset.provider_id
            config = settings.provider_config(preset.provider_id)
            from hr_toolkit.ai.config import normalize_api_key, validate_endpoint, validate_model

            config.api_key = normalize_api_key(api_key)
            config.model = validate_model(str(model or "").strip() or preset.default_model)
            endpoint_text = str(endpoint or "").strip()
            config.endpoint = validate_endpoint(endpoint_text) if endpoint_text else ""
            save_ai_settings(settings)
            self._ai_settings = settings
        except (AiConfigError, OSError) as exc:
            self.aiTestFinished.emit(False, str(exc))
            return False
        session = self._ai_session
        if session is not None and not self._ai_busy:
            session.refresh_settings(settings)
        self.aiSettingsChanged.emit()
        return True

    @Slot(result=str)
    def aiCurrentApiKey(self) -> str:
        return self._ai_settings_obj().provider_config().api_key

    @Slot(str, result=str)
    def aiApiKeyFor(self, provider: str) -> str:
        try:
            return self._ai_settings_obj().provider_config(str(provider)).api_key
        except Exception:
            return ""

    @Slot(str, result=str)
    def aiEndpointFor(self, provider: str) -> str:
        try:
            settings = self._ai_settings_obj()
            preset = settings.preset(str(provider))
            return settings.provider_config(str(provider)).resolved_endpoint(preset)
        except Exception:
            return ""

    @Slot(str, result=str)
    def aiModelFor(self, provider: str) -> str:
        try:
            settings = self._ai_settings_obj()
            preset = settings.preset(str(provider))
            return settings.provider_config(str(provider)).resolved_model(preset)
        except Exception:
            return ""

    @Property(bool, notify=aiSettingsChanged)
    def aiTesting(self):
        return self._ai_testing

    @Property(bool, notify=aiChanged)
    def aiPreparing(self):
        return self._ai_preparing

    @Slot(bool, str)
    def _ai_test_finished(self, ok, message):
        self._ai_testing = False
        self.aiSettingsChanged.emit()

    @Slot()
    @Slot(str, str, str, str)
    def aiTestConnection(self, provider=None, api_key=None, model=None, endpoint=None) -> None:
        if self._ai_testing or self._closed:
            return
        from copy import deepcopy
        from hr_toolkit.ai.config import normalize_api_key, validate_endpoint, validate_model
        settings = deepcopy(self._ai_settings_obj())
        try:
            if provider is not None:
                settings.preset(provider)
                settings.active_provider = provider
                config = settings.provider_config(provider)
                config.api_key = normalize_api_key(api_key)
                config.model = validate_model(model) if model.strip() else ""
                config.endpoint = validate_endpoint(endpoint) if endpoint.strip() else ""
        except ValueError as exc:
            self.aiTestFinished.emit(False, str(exc))
            return
        self._ai_testing = True
        self.aiSettingsChanged.emit()

        def worker() -> None:
            from hr_toolkit.ai.client import ChatError, test_connection
            try:
                reply = test_connection(settings)
                result = (True, "连接成功" + (f"：{reply}" if reply else ""))
            except ChatError as exc:
                result = (False, str(exc))
            except Exception:
                result = (False, "请求失败，请稍后重试。")
            if not self._closed:
                self.aiTestFinished.emit(*result)

        threading.Thread(target=worker, daemon=True, name="HRToolkit-ai-test").start()

    @Slot(str)
    def aiSendMessage(self, text: str) -> None:
        question = str(text or "").strip()
        if self._ai_busy or self._ai_preparing:
            return
        if len(question) > 10000:
            self.notificationRequested.emit("Sage", "问题过长，请缩短到 10000 字以内。", "warning")
            return
        if not question and self._ai_attachment_model.rowCount() == 0:
            return
        settings = self._ai_settings_obj()
        if not settings.is_ready():
            self.aiSettingsChanged.emit()
            return
        # 附件跟着这条消息走：快照进消息行，待发区清空，用户才看得出确实发出去了。
        sent = self._ai_session_obj().consume_pending()
        attachment_rows = [item.as_history_row() for item in sent]
        if not question and not attachment_rows:
            return
        self._ai_begin_turn(question, attachment_rows, sent)

    def _ai_attach_status_phrases(self, attachment_rows) -> None:
        """Show only observable input and waiting state, never invented progress."""
        from hr_toolkit.ai.status import build_status_phrases

        self._ai_status_phrases = build_status_phrases(
            [
                str(row.get("kind") or "")
                for row in (attachment_rows or [])
                if isinstance(row, dict)
            ],
        )
        self.aiStatusChanged.emit()

    def _ai_begin_turn(self, question: str, attachment_rows, sent_attachments, *, context_body=None) -> None:
        session = self._ai_session_obj()
        self._ai_ensure_conversation(question)
        session.prepare_request()
        session.language = self._presentation.language
        session.context_label = self._spec.title
        # Snapshot settings: changing provider mid-response cannot mutate this request.
        from copy import deepcopy
        session.refresh_settings(deepcopy(self._ai_settings_obj()))
        self._ai_attach_status_phrases(attachment_rows)
        self._ai_chat_model.append(
            {
                "role": "user",
                "content": question if question else self._presentation.translate("请分析所附文件。", self._presentation.language),
                "apiContent": context_body or session._context_message(question, sent_attachments),
                "html": "",
                "streaming": False,
                "time": datetime.now().strftime("%H:%M"),
                "attachments": list(attachment_rows or []),
            },
            maximum=200,
        )
        self._ai_attachment_model.clear()
        self._ai_chat_model.append(
            {"role": "assistant", "content": "", "html": "", "streaming": True,
             "time": datetime.now().strftime("%H:%M"), "attachments": []},
            maximum=200,
        )
        self._ai_busy = True
        self._ai_draft = ""
        self.aiChanged.emit()
        self._ai_sync_conversation()
        self._ai_prune_image_cache()

        def worker() -> None:
            from hr_toolkit.ai.client import ChatError

            buffer: list[str] = []
            last_flush = time.monotonic()

            def flush() -> None:
                nonlocal last_flush
                if buffer and not self._closed:
                    self._aiDeltaIncoming.emit("".join(buffer))
                    buffer.clear()
                last_flush = time.monotonic()

            try:
                for delta in session.ask(question, list(sent_attachments or []),
                                         context_body=context_body, image_rows=attachment_rows if context_body else ()):
                    if self._closed:
                        return
                    buffer.append(delta)
                    if time.monotonic() - last_flush >= 0.12:
                        flush()
                flush()
                if not self._closed:
                    self._aiFinishedIncoming.emit(True, "")
            except ChatError as exc:
                flush()
                if not self._closed:
                    self._aiFinishedIncoming.emit(False, str(exc))
            except Exception as exc:
                flush()
                runlog.log_exception("AI 助手请求失败", exc)
                if not self._closed:
                    self._aiFinishedIncoming.emit(False, "请求失败，请稍后重试。")

        threading.Thread(target=worker, daemon=True, name="HRToolkit-ai-chat").start()

    @Slot()
    def aiRegenerate(self) -> None:
        """重新生成最后一条回答：退掉最后的一问一答，用同一条问题再问一次。"""
        if self._ai_busy or self._ai_preparing or len(self._ai_chat_model) < 2:
            return
        last_row = self._ai_chat_model.item_at(len(self._ai_chat_model) - 1)
        question_row = self._ai_chat_model.item_at(len(self._ai_chat_model) - 2)
        if last_row is None or question_row is None:
            return
        if last_row.get("role") != "assistant" or question_row.get("role") != "user":
            return
        question = str(question_row.get("content") or "")
        attachment_rows = question_row.get("attachments") or []
        self._ai_chat_model.remove_at(len(self._ai_chat_model) - 1)
        self._ai_chat_model.remove_at(len(self._ai_chat_model) - 1)
        # 用剩下的消息行重建上下文：带附件的用户行存了 apiContent（表格正文），
        # 所以重问时模型仍然看得见原来的表格。
        self._ai_session_obj().load_history(self._ai_chat_model.items())
        self._ai_begin_turn(question, attachment_rows, [], context_body=question_row.get("apiContent") or None)

    @Slot()
    def aiStopGenerating(self) -> None:
        if self._ai_preparing:
            self._ai_attachment_generation += 1
            self._ai_preparing = False
            self.aiChanged.emit()
        if self._ai_session is not None:
            self._ai_session.request_stop()

    @Slot()
    def aiClearConversation(self) -> None:
        self.aiNewConversation()

    @Slot()
    def aiChooseAttachments(self) -> None:
        from hr_toolkit.gui_qt.image_input import ATTACH_FILE_FILTER

        parent = self._dialog_parent()
        filenames, _selected = self._presentation.file_dialog(
            QFileDialog.getOpenFileNames,
            parent,
            "选择要分析的表格或图片",
            self._file_dialog_initial_dir(),
            ATTACH_FILE_FILTER,
        )
        if filenames:
            self.aiAttachPaths([str(name) for name in filenames])

    @Slot(result=bool)
    def aiClipboardHasImage(self) -> bool:
        """剪贴板里有没有图：输入框据此决定 Ctrl+V 是粘图还是粘文字。"""
        try:
            from hr_toolkit.gui_qt.image_input import clipboard_has_image
        except ImportError:
            return False
        return bool(clipboard_has_image())

    @Slot(result=bool)
    def aiPasteImage(self) -> bool:
        if self._ai_busy or self._ai_preparing:
            return False
        """把剪贴板里的图附加进来；剪贴板没有图返回 False，让普通文本粘贴继续。"""
        try:
            from hr_toolkit.gui_qt.image_input import clipboard_image_payload
        except ImportError:
            return False
        try:
            payload = clipboard_image_payload()
        except ValueError as exc:
            self.notificationRequested.emit("图片粘贴", str(exc), "warning")
            return True
        if not payload:
            return False
        self._ai_attach_image_payload(
            name=payload["name"],
            data=payload["data"],
            mime=payload["mime"],
            width=payload["width"],
            height=payload["height"],
            cached=payload.get("cached_path"),
        )
        return True

    def _ai_attach_image_payload(
        self, *, name, data, mime, width, height, cached=None
    ) -> bool:
        session = self._ai_session_obj()
        try:
            row = session.add_image(
                name=name,
                data=data,
                mime=mime,
                width=width,
                height=height,
                path=cached,
            )
        except ValueError as exc:
            self.notificationRequested.emit("图片附件", str(exc), "warning")
            return False
        self._ai_attachment_model.append(row)
        self.aiChanged.emit()
        return True

    @Slot("QVariantList")
    def aiAttachPaths(self, paths) -> None:
        """Decode/parse off the GUI thread; only publish a completed batch here."""
        if self._ai_busy or self._ai_preparing or self._closed:
            return
        from hr_toolkit.ai.assistant import AiAssistantSession
        from hr_toolkit.ai import images as image_support
        resolved = []
        errors = []
        for raw in paths or []:
            try:
                resolved.extend(local_drop_paths([raw]))
            except ValueError as exc:
                errors.append(str(exc))
        session = self._ai_session_obj()
        self._ai_prune_image_cache()
        pending = list(session.pending_attachments())
        self._ai_preparing = True
        self._ai_attachment_generation += 1
        generation = self._ai_attachment_generation
        self.aiChanged.emit()

        def worker():
            temporary = AiAssistantSession(session.settings)
            temporary._attachments = list(pending)
            for path in resolved:
                if self._closed or generation != self._ai_attachment_generation:
                    return
                try:
                    if image_support.is_image_filename(path.name):
                        from hr_toolkit.gui_qt.image_input import load_image_file
                        payload = load_image_file(path)
                        temporary.add_image(name=payload["name"], data=payload["data"],
                                            mime=payload["mime"], width=payload["width"],
                                            height=payload["height"], path=payload["cached_path"])
                    else:
                        temporary.add_attachment(path)
                except (ValueError, OSError) as exc:
                    errors.append(str(exc))
                except Exception:
                    errors.append("附件解析失败，请检查文件格式。")
            if not self._closed:
                self._aiAttachmentsReady.emit(generation, temporary.pending_attachments(), errors)

        threading.Thread(target=worker, daemon=True, name="HRToolkit-ai-attachments").start()

    @Slot(int, object, object)
    def _apply_ai_attachments(self, generation, attachments, errors):
        if self._closed or generation != self._ai_attachment_generation:
            return
        self._ai_session_obj()._attachments = list(attachments)
        self._ai_attachment_model.set_items([item.as_model_row() for item in attachments])
        self._ai_preparing = False
        self.aiChanged.emit()
        if errors:
            self.notificationRequested.emit("附件解析", "\n".join(errors[:3]), "warning")

    @Slot(str)
    def aiOpenImage(self, path: str) -> None:
        """用系统看图程序打开附件原图。"""
        target = str(path or "").strip()
        if not target:
            return
        if target.startswith("file://"):
            target = QUrl(target).toLocalFile()
        QDesktopServices.openUrl(QUrl.fromLocalFile(target))

    @Slot(int)
    def aiRemoveAttachment(self, row: int) -> None:
        if self._ai_preparing or self._ai_busy:
            return
        if self._ai_session is not None:
            self._ai_session.remove_attachment(int(row))
        self._ai_attachment_model.remove_at(int(row))
        self.aiChanged.emit()

    @Slot()
    def aiClearAttachments(self) -> None:
        if self._ai_preparing or self._ai_busy:
            return
        if self._ai_session is not None:
            self._ai_session.clear_attachments()
        self._ai_attachment_model.clear()
        self.aiChanged.emit()

    @Slot(str)
    def _apply_ai_delta(self, text: str) -> None:
        if self._closed:
            return
        row = len(self._ai_chat_model) - 1
        item = self._ai_chat_model.item_at(row)
        if not item:
            return
        item["content"] = (item.get("content") or "") + str(text)
        item.update(self._ai_rendered(item["content"]))
        self._ai_chat_model.update_at(row, item)

    @Slot(bool, str)
    def _apply_ai_finished(self, ok: bool, error: str) -> None:
        if self._closed:
            return
        row = len(self._ai_chat_model) - 1
        item = self._ai_chat_model.item_at(row)
        if item is not None and item.get("role") == "assistant":
            stopped = self._ai_session is not None and self._ai_session.stopped
            item["status"] = "stopped" if stopped else ("complete" if ok else "error")
            if stopped:
                item["content"] = (item.get("content") or "") + "\n\n" + self._presentation.translate("已停止生成", self._presentation.language)
            elif not ok:
                existing = item.get("content") or ""
                item["content"] = (
                    existing + "\n\n" if existing else ""
                ) + "⚠ " + self._presentation.translate(str(error or "请求失败"), self._presentation.language)
            item["streaming"] = False
            item.update(self._ai_rendered(item.get("content") or ""))
            self._ai_chat_model.update_at(row, item)
        # 用户行记下真正发给模型的正文（含表格），历史恢复与重新生成都要用它。
        question_row = row - 1
        if question_row >= 0 and self._ai_session is not None:
            context_body = getattr(self._ai_session, "last_context_body", "")
            question_item = self._ai_chat_model.item_at(question_row)
            if question_item is not None and question_item.get("role") == "user" and context_body:
                question_item["apiContent"] = context_body
                self._ai_chat_model.update_at(question_row, question_item)
        self._ai_busy = False
        self.aiChanged.emit()
        self._ai_sync_conversation()

    @Slot()
    def openLastResult(self) -> None:
        if self.canOpenLastResult and self._last_result_dir.exists():
            open_path(self._last_result_dir)

    @staticmethod
    def _result_output_paths(tool_id: str, payload, result_dir: Path) -> list[Path]:
        """Use documented output fields only; never infer from source/input paths."""
        if not isinstance(payload, dict):
            return []
        fields = {
            "social_security": ("detail_output_file", "detail_output_files", "summary_output_file"),
            "insurance_ledger": ("output_file", "roster_warning_file"),
            "data_statistics": ("output_file",),
            "salary_merge": ("output_file",),
            "personnel_change_merge": ("output_file", "output_files", "roster_output_file"),
            "roster_update": ("output_file",),
            "personnel_reconcile": ("output_file", "filled_output_file"),
            "archive_import": ("output_file",),
            "archive_export": ("output_files",),
            "material_collector": ("report_path", "review_path", "zip_path"),
        }.get(tool_id, ())
        values = []
        for field in fields:
            value = payload.get(field)
            values.extend(value if isinstance(value, list) else [value])
        if tool_id == "salary_split":
            values.extend(item.get("file_path") for item in payload.get("outputs", []) if isinstance(item, dict))
        result = []
        for value in values:
            if not isinstance(value, (str, Path)) or not str(value):
                continue
            path = Path(value)
            try:
                relative = path.relative_to(result_dir)
            except ValueError:
                continue
            if relative.parts and ".." not in relative.parts and path not in result:
                result.append(path)
        return result

    @Slot()
    def openPrimaryResult(self) -> None:
        if not self.canOpenPrimaryResult:
            return
        try:
            path = self._result_files[0].resolve(strict=True)
            path.relative_to(self._last_result_dir.resolve(strict=True))
            if not path.is_file():
                raise ValueError("结果文件已不存在，请打开结果目录查看。")
            open_path(path)
        except (OSError, ValueError) as exc:
            self.notificationRequested.emit("无法打开结果", str(exc), "warning")

    @Slot()
    def openRunLog(self) -> None:
        try:
            path = runlog.run_log_path()
        except Exception:
            return
        if path.exists():
            open_path(path)

    @Slot(str)
    def openUrl(self, url: str) -> None:
        QDesktopServices.openUrl(QUrl(url))

    @Slot()
    def _begin_shutdown(self) -> None:
        if self._shutdown_requested or self._closed:
            return
        self._shutdown_requested = True
        if self._drop_preview_request is not None:
            self.cancelDropPreview(self._drop_preview_request["token"])
        if self._selection_request is not None:
            self._selection_request["cancel"].set()
        self._shutdown_wait_started = time.monotonic()
        if self._preview_cancel_event is not None:
            self._preview_cancel_event.set()
        self._run_coordinator.cancel()
        if self._workspace_cancel_event is not None:
            self._workspace_cancel_event.set()
        if self._update_cancel_event is not None:
            self._update_cancel_event.set()
        self._append_log("正在安全结束后台任务并关闭…", "warning")
        QTimer.singleShot(50, self._poll_shutdown)

    def _shutdown_work_running(self) -> bool:
        return bool(
            self._busy
            or self._workspace_busy
            or self._project_opening
            or self._history_busy
            or self._trash_busy
            or self._run_coordinator.running
            or self._preview_cancel_event is not None
        )

    @Slot()
    def _poll_shutdown(self) -> None:
        if self._closed:
            return
        elapsed = time.monotonic() - self._shutdown_wait_started
        if self._shutdown_work_running() and elapsed < 10.0:
            QTimer.singleShot(100, self._poll_shutdown)
            return
        if self._shutdown_work_running():
            runlog.log_line("关闭等待超过 10 秒；保留项目写锁并交由下次启动恢复未完成批次。")
        self.close()
        QCoreApplication.quit()

    @Slot(result=bool)
    def requestClose(self) -> bool:
        if self._update_restart_requested:
            return False
        if self._closed:
            return True
        if self._shutdown_requested:
            return False
        if self._shutdown_work_running():
            if self._pending_confirmation_action and self._pending_confirmation_action[0] == "close":
                return False
            token = f"close:{time.monotonic_ns()}"
            self._pending_confirmation = token
            self._pending_confirmation_action = ("close", None)
            self.confirmationRequested.emit(
                "处理尚未结束",
                "当前处理或资料保存还没有完全结束。现在退出会先请求安全停止，并把未完成批次留待下次打开时恢复。是否仍要退出？",
                token,
            )
            return False
        self.close()
        return True

    @Slot()
    def close(self) -> None:
        self._rename_review.cancel()
        if self._closed:
            return
        self._background_update_timer.stop()
        self._incoming_progress_timer.stop()
        self._search_timer.stop()
        self._run_progress_timer.stop()
        self._run_progress_flush_timer.stop()
        self._flush_logs()
        if hasattr(self, "_log_flush_timer") and self._log_flush_timer.isActive():
            self._log_flush_timer.stop()
        self._closed = True
        if self._ai_session is not None:
            self._ai_session.request_stop()
        self._clear_trash_items()
        if self._drop_preview_request is not None:
            self.cancelDropPreview(self._drop_preview_request["token"])
        if self._selection_request is not None:
            self._selection_request["cancel"].set()
        with self._workspace_read_lock:
            self._workspace_read_jobs.clear()
        if self._preview_cancel_event is not None:
            self._preview_cancel_event.set()
        self._run_coordinator.cancel()
        if self._workspace_cancel_event is not None:
            self._workspace_cancel_event.set()
        if self._workspace_scan_cancel_event is not None:
            self._workspace_scan_cancel_event.set()
        if self._update_cancel_event is not None:
            self._update_cancel_event.set()
        self._save_workspace_preferences()
        # Do not release the writer lock while a worker can still write.  The
        # process exits immediately after the Qt event loop and project recovery
        # will safely close any interrupted batch on next open.
        project_worker_running = bool(
            self._run_coordinator.running
            or self._workspace_busy
            or self._project_opening
            or self._trash_busy
        )
        if self._project_store is not None and not project_worker_running:
            try:
                self._project_store.close()
            except Exception as exc:
                runlog.log_exception("关闭工作项目失败", exc)
