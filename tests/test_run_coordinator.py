from __future__ import annotations

import tempfile
import threading
import unittest
from pathlib import Path
from unittest.mock import patch

from hr_toolkit.background_process import (
    BusinessProcessError,
    BusinessProcessStartError,
    ProcessCallResult,
)
from hr_toolkit.project_store import ProjectStore
from hr_toolkit.run_coordinator import (
    PROGRESS_UI_INTERVAL_SECONDS,
    ProjectRunCoordinator,
    RunCallbacks,
    RunRequest,
)


def _copy_probe(
    input_path,
    output_dir,
    *,
    cancelled=None,
    progress_callback=None,
):
    if cancelled is not None and cancelled():
        raise RuntimeError("cancelled")
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    output = Path(output_dir) / "same.txt"
    output.write_bytes(Path(input_path).read_bytes())
    if progress_callback is not None:
        progress_callback(1, 1, "完成")
    return {"output_file": str(output), "value": Path(input_path).read_text(encoding="utf-8")}


def _fake_folder_rename(root_dir, *, mode, cancelled=None, progress_callback=None):
    target = Path(root_dir) / "张三-已核对"
    (Path(root_dir) / "张三").rename(target)
    return {"count": 1, "output_dir": str(root_dir)}


class ProjectRunCoordinatorTests(unittest.TestCase):
    def test_replace_text_confirmed_preview_runs_on_project_copy(self) -> None:
        from hr_toolkit.tools.folder_rename import rename_person_folders
        from hr_toolkit.project_store import CATEGORY_RESULTS

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "资料"
            source.mkdir()
            (source / "old.pdf").write_bytes(b"pdf-source")
            (source / "old.jpg").write_bytes(b"image-source")
            kwargs = {"mode": "replace_text", "text": "old", "replacement_name": "new", "file_type": "pdf"}
            preview = rename_person_folders(source, **kwargs, dry_run=True)
            kwargs["expected_operations"] = [(op.source.name, op.target.name) for op in preview.operations]
            kwargs["expected_warnings"] = preview.warnings
            store = ProjectStore.create(root / "project", "测试项目")
            errors, successes = [], []
            try:
                request = RunRequest("folder_rename", "改名", "测试", "替换文字", rename_person_folders, (source,), kwargs)
                ProjectRunCoordinator()._run(store, request,
                    RunCallbacks(error=errors.append, success=lambda *args: successes.append(args)), threading.Event())
                self.assertEqual(errors, [])
                self.assertEqual(len(successes), 1)
                self.assertEqual((source / "old.pdf").read_bytes(), b"pdf-source")
                self.assertEqual((source / "old.jpg").read_bytes(), b"image-source")
                self.assertFalse((source / "new.pdf").exists())
                detail = store.get_batch(store.list_batches()[0].id)
                results = detail.directories[CATEGORY_RESULTS]
                renamed = list(results.rglob("new.pdf"))
                self.assertEqual(len(renamed), 1)
                self.assertEqual(renamed[0].read_bytes(), b"pdf-source")
                self.assertEqual((renamed[0].parent / "old.jpg").read_bytes(), b"image-source")
            finally:
                store.close()

    def test_social_roster_mapping_prompt_does_not_create_output(self) -> None:
        from openpyxl import Workbook
        from hr_toolkit.common.template_mapping import TemplateSelectionRequired
        from hr_toolkit.tools.social_security import generate_social_security_reports

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            roster, payment = root / "花名册.xlsx", root / "社保.xlsx"
            for path in (roster, payment):
                workbook = Workbook()
                workbook.active.append(["无法识别的列"])
                workbook.save(path)
                workbook.close()
            store = ProjectStore.create(root / "project", "测试项目")
            errors = []
            request = RunRequest("social_security", "社保", "测试", "社保", generate_social_security_reports,
                                 (payment, roster, root), {"template_rules": {}})
            try:
                ProjectRunCoordinator()._run(store, request, RunCallbacks(error=errors.append), threading.Event())
                self.assertEqual(len(errors), 1)
                self.assertIsInstance(errors[0], TemplateSelectionRequired)
                self.assertEqual(store.list_batches(), ())
                self.assertFalse((store.root / "测试").exists())
                self.assertEqual(list(store.staging_dir.iterdir()), [])
            finally:
                store.close()

    def test_prevalidation_retry_never_creates_output_or_failed_batch(self) -> None:
        from hr_toolkit.common.run_temp import temporary_directory
        from hr_toolkit.common.template_mapping import TemplateSelectionRequired

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "source.txt"
            source.write_text("source", encoding="utf-8")
            store = ProjectStore.create(root / "project", "测试项目")
            errors, outputs = [], []

            def invalid_template(input_path, output_dir):
                self.assertEqual(Path(input_path), source)
                outputs.append(Path(output_dir))
                self.assertFalse(Path(output_dir).parent.exists())
                with temporary_directory() as temp:
                    (Path(temp) / "解析资料.txt").write_text("temporary", encoding="utf-8")
                    raise TemplateSelectionRequired({"tool": "social_security", "message": "请确认对应列：姓名、身份证号码"})

            request = RunRequest("social_security", "社保明细与汇总", "测试", "社保", invalid_template,
                                 (source, root), {})
            try:
                for _ in range(2):
                    ProjectRunCoordinator()._run(store, request, RunCallbacks(error=errors.append), threading.Event())
                    self.assertEqual(store.list_batches(), ())
                    self.assertEqual(store.list_trash(), ())
                    self.assertEqual(list(store.staging_dir.iterdir()), [])
                    self.assertFalse((store.root / "测试").exists())
                self.assertEqual(len(errors), 2)
                self.assertTrue(all(isinstance(error, TemplateSelectionRequired) for error in errors))
                self.assertTrue(all(not path.exists() for path in outputs))
                self.assertEqual(source.read_text(encoding="utf-8"), "source")
            finally:
                store.close()

    def test_worker_template_error_discards_only_reserved_batch(self) -> None:
        from hr_toolkit.common.template_mapping import TemplateSelectionRequired
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "source.txt"
            source.write_text("source", encoding="utf-8")
            store = ProjectStore.create(root / "project", "测试项目")
            errors = []
            request = RunRequest("social_security", "社保", "测试", "社保", _copy_probe, (source, root), {})
            remote_error = BusinessProcessError(str(TemplateSelectionRequired({"tool": "social_security"})))
            try:
                with patch("hr_toolkit.run_coordinator.should_use_process", return_value=True), patch(
                    "hr_toolkit.run_coordinator.run_business_process", side_effect=remote_error,
                ):
                    ProjectRunCoordinator()._run(store, request, RunCallbacks(error=errors.append), threading.Event())
                self.assertEqual(errors, [remote_error])
                self.assertEqual(store.list_batches(), ())
                self.assertFalse((store.root / "测试").exists())
            finally:
                store.close()

    def test_invalid_folder_configuration_does_not_create_result_copy(self) -> None:
        from hr_toolkit.tools.folder_rename import rename_person_folders
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "source"
            source.mkdir()
            (source / "说明.txt").write_text("original", encoding="utf-8")
            store = ProjectStore.create(root / "project", "测试项目")
            errors = []
            request = RunRequest("folder_rename", "改名", "测试", "改名", rename_person_folders,
                                 (source,), {"mode": "invalid"})
            try:
                ProjectRunCoordinator()._run(store, request, RunCallbacks(error=errors.append), threading.Event())
                self.assertEqual(len(errors), 1)
                self.assertIn("不支持的改名模式", str(errors[0]))
                self.assertEqual(store.list_batches(), ())
                self.assertFalse((store.root / "测试").exists())
                self.assertEqual((source / "说明.txt").read_text(encoding="utf-8"), "original")
            finally:
                store.close()

    def test_business_progress_is_coalesced_without_losing_completion(self) -> None:
        def noisy_probe(*, progress_callback=None):
            for current in range(1, 1001):
                if progress_callback is not None:
                    progress_callback(current, 1000, f"处理 {current}")
            return {"count": 1000}

        progress = []
        request = RunRequest(
            tool_id="probe",
            tool_name="进度测试",
            group_name="测试",
            description="进度测试",
            function=noisy_probe,
            args=(),
            kwargs={},
        )
        payload, isolated = ProjectRunCoordinator()._business_call(
            request,
            (),
            {},
            threading.Event(),
            RunCallbacks(progress=lambda *values: progress.append(values)),
        )

        self.assertEqual(PROGRESS_UI_INTERVAL_SECONDS, 0.1)
        self.assertEqual(payload, {"count": 1000})
        self.assertFalse(isolated)
        self.assertGreaterEqual(len(progress), 1)
        self.assertLessEqual(len(progress), 2)
        self.assertEqual(progress[-1], (1000, 1000, "处理 1000"))

    def test_process_start_failure_falls_back_without_changing_output(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "source.txt"
            source.write_text("unchanged-business-value", encoding="utf-8")
            output_dir = root / "output"
            output_dir.mkdir()
            logs = []
            request = RunRequest(
                tool_id="probe",
                tool_name="兼容模式测试",
                group_name="测试",
                description="兼容模式测试",
                function=_copy_probe,
                args=(source, output_dir),
                kwargs={},
            )

            coordinator = ProjectRunCoordinator()
            with patch(
                "hr_toolkit.run_coordinator.should_use_process",
                return_value=True,
            ), patch(
                "hr_toolkit.run_coordinator.run_business_process",
                side_effect=BusinessProcessStartError("[WinError 2] 系统找不到指定的文件。"),
            ) as process_call:
                payload, isolated = coordinator._business_call(
                    request,
                    request.args,
                    request.kwargs,
                    threading.Event(),
                    RunCallbacks(log=logs.append),
                )
                second_payload, second_isolated = coordinator._business_call(
                    request,
                    request.args,
                    request.kwargs,
                    threading.Event(),
                    RunCallbacks(log=logs.append),
                )

            self.assertFalse(isolated)
            self.assertFalse(second_isolated)
            self.assertFalse(coordinator.process_isolation_available)
            self.assertIn("WinError 2", coordinator.process_isolation_failure)
            process_call.assert_called_once_with(
                module_name=request.function.__module__,
                function_name="_copy_probe",
                args=request.args,
                kwargs={},
                cancel_event=unittest.mock.ANY,
                on_progress=unittest.mock.ANY,
            )
            self.assertEqual(payload["value"], "unchanged-business-value")
            self.assertEqual(second_payload, payload)
            self.assertEqual(
                (output_dir / "same.txt").read_text(encoding="utf-8"),
                "unchanged-business-value",
            )
            self.assertEqual(
                logs,
                ["独立后台进程不可用，已自动切换兼容后台模式继续处理。"],
            )

    def test_running_process_failure_is_not_retried_in_thread(self) -> None:
        business_calls = []

        def probe():
            business_calls.append("called")
            return {"ok": True}

        request = RunRequest(
            tool_id="probe",
            tool_name="失败测试",
            group_name="测试",
            description="失败测试",
            function=probe,
            args=(),
            kwargs={},
        )
        with patch(
            "hr_toolkit.run_coordinator.should_use_process",
            return_value=True,
        ), patch(
            "hr_toolkit.run_coordinator.run_business_process",
            side_effect=BusinessProcessError("后台业务已经失败"),
        ):
            with self.assertRaises(BusinessProcessError):
                ProjectRunCoordinator()._business_call(
                    request,
                    (),
                    {},
                    threading.Event(),
                    RunCallbacks(),
                )

        self.assertEqual(business_calls, [])

    def test_hundred_inputs_still_use_exactly_one_worker_process(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            inputs = []
            for index in range(100):
                source = root / f"input-{index:03d}.xlsx"
                source.write_bytes(b"x")
                inputs.append(source)

            def count_probe(input_paths, output_dir):
                return {"count": len(input_paths)}

            request = RunRequest(
                tool_id="social_security",
                tool_name="百文件测试",
                group_name="测试",
                description="百文件测试",
                function=count_probe,
                args=(inputs, root / "output"),
                kwargs={},
            )
            expected = ProcessCallResult(payload={"count": 100}, elapsed_seconds=0.01)
            with patch(
                "hr_toolkit.run_coordinator.run_business_process",
                return_value=expected,
            ) as process_call:
                payload, isolated = ProjectRunCoordinator()._business_call(
                    request,
                    request.args,
                    request.kwargs,
                    threading.Event(),
                    RunCallbacks(),
                )

            self.assertTrue(isolated)
            self.assertEqual(payload, {"count": 100})
            process_call.assert_called_once()

    def test_original_inputs_business_output_and_result_registration(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "source.txt"
            source.write_text("unchanged-business-value", encoding="utf-8")
            project_root = root / "project"
            store = ProjectStore.create(project_root, "测试项目")
            coordinator = ProjectRunCoordinator()
            finished = threading.Event()
            success = []
            errors = []
            request = RunRequest(
                tool_id="probe",
                tool_name="测试工具",
                group_name="测试",
                description="测试工具",
                function=_copy_probe,
                args=(source, project_root),
                kwargs={},
            )
            callbacks = RunCallbacks(
                success=lambda *payload: success.append(payload),
                error=lambda error: errors.append(error),
                finished=finished.set,
            )
            try:
                self.assertTrue(coordinator.start(store, request, callbacks))
                self.assertTrue(finished.wait(10))
                self.assertFalse(errors)
                self.assertEqual(len(success), 1)
                payload, result_dir, _elapsed, _isolated = success[0]
                self.assertEqual(payload["value"], "unchanged-business-value")
                self.assertEqual((Path(result_dir) / "same.txt").read_text(encoding="utf-8"), "unchanged-business-value")
                summaries = store.list_batches()
                self.assertEqual(len(summaries), 1)
                self.assertEqual(summaries[0].status, "success")
                self.assertEqual(source.read_text(encoding="utf-8"), "unchanged-business-value")
                self.assertEqual(list(project_root.rglob("上传资料")), [])
                self.assertEqual(list(store.staging_dir.iterdir()), [])
                detail = store.get_batch(summaries[0].id)
                self.assertEqual(detail.files_for("uploads"), ())
                source.unlink()
                self.assertTrue(store.verify_batch_files(summaries[0].id))
            finally:
                store.close()

    def test_coordinator_folder_rename_operates_on_project_copy_and_preserves_customer_source(self) -> None:
        import hashlib
        from hr_toolkit.project_store import CATEGORY_RESULTS

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            customer_source = root / "人员资料"
            person_folder = customer_source / "张三"
            person_folder.mkdir(parents=True)
            (person_folder / "说明.txt").write_text("record-content-original", encoding="utf-8")
            (customer_source / "根文件.txt").write_text("root-file-original", encoding="utf-8")

            def _hash_tree(directory: Path) -> dict[str, str]:
                result = {}
                for path in sorted(directory.rglob("*")):
                    if path.is_file():
                        rel = str(path.relative_to(directory))
                        result[rel] = hashlib.sha256(path.read_bytes()).hexdigest()
                return result

            hashes_before = _hash_tree(customer_source)
            self.assertEqual(len(hashes_before), 2)

            project_root = root / "project"
            store = ProjectStore.create(project_root, "测试项目")
            coordinator = ProjectRunCoordinator()
            finished = threading.Event()
            success = []
            errors = []

            request = RunRequest(
                tool_id="folder_rename",
                tool_name="资料文件夹改名",
                group_name="人员与档案",
                description="改名测试",
                function=_fake_folder_rename,
                args=(customer_source,),
                kwargs={"mode": "append"},
            )
            callbacks = RunCallbacks(
                success=lambda *payload: success.append(payload),
                error=lambda error: errors.append(error),
                finished=finished.set,
            )
            try:
                self.assertTrue(coordinator.start(store, request, callbacks))
                self.assertTrue(finished.wait(10))
                self.assertFalse(errors)
                self.assertEqual(len(success), 1)

                # Customer source folder MUST REMAIN UNTOUCHED - verified by SHA-256
                hashes_after = _hash_tree(customer_source)
                self.assertEqual(hashes_before, hashes_after)
                self.assertTrue((customer_source / "张三" / "说明.txt").is_file())
                self.assertFalse((customer_source / "张三-已核对").exists())

                # Project results copy MUST HAVE THE RENAMED FOLDER
                batches = store.list_batches()
                self.assertEqual(len(batches), 1)
                batch_detail = store.get_batch(batches[0].id)
                assert batch_detail is not None
                results_dir = batch_detail.directories[CATEGORY_RESULTS]
                found = list(results_dir.glob("**/张三-已核对"))
                self.assertTrue(len(found) > 0, f"Expected renamed folder in results: {list(results_dir.rglob('*'))}")
            finally:
                store.close()


if __name__ == "__main__":
    unittest.main()
