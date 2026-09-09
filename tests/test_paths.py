from __future__ import annotations

import ctypes
import os
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch

from hr_toolkit.common import paths
from hr_toolkit.common.paths import path_is_relative_to


class PathCompatibilityTests(unittest.TestCase):
    def test_path_is_relative_to_matches_expected_containment(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary).resolve()
            self.assertTrue(path_is_relative_to(root, root))
            self.assertTrue(path_is_relative_to(root / "child" / "file.xlsx", root))
            self.assertFalse(path_is_relative_to(root.parent / "outside.xlsx", root))

    def test_windows_path_validation_preserves_chinese_spaces_and_network_paths(self) -> None:
        valid = (
            r"C:\人事资料\2026年9月 项目",
            "C:/人事资料/2026年9月 项目",
            r"\\服务器\共享资料\人事项目",
            r"\\?\C:\长目录\中文项目",
            r"\\?\UNC\服务器\共享资料\中文项目",
            r"C:\资料\..\项目",
            r"C:\资料\#100% (1).xlsx",
        )
        for value in valid:
            with self.subTest(value=value):
                self.assertIsNone(paths.path_text_error(value, windows=True))
        invalid = ("Ř<", "C:\\资料\x00", "C:\\资料\n项目", r"C:\资料\项目?", r"C:\资料\工资:社保", r"C:\资料\CON.txt", "C:\\资料\\项目.", r"\\服务器<\共享\项目", r"\\服务器\共享?\项目", r"\\.\pipe\项目", r"C:\CON\子目录")
        for value in invalid:
            with self.subTest(value=repr(value)):
                self.assertIsNotNone(paths.path_text_error(value, windows=True))
        self.assertIsNone(paths.path_text_error("/资料/工资:社保", windows=False))

    def test_absolute_hints_never_turn_corrupt_values_into_working_directory(self) -> None:
        for value in (None, True, {}, [], "", " ", ".", "relative/project", "Ř<", "bad\x00path"):
            with self.subTest(value=repr(value)):
                self.assertIsNone(paths.absolute_path_hint(value))
        self.assertEqual(paths.absolute_path_hint(Path.cwd()), Path.cwd())

    def test_windows_process_image_query_preserves_unicode_and_retries_truncation(self) -> None:
        from ctypes import wintypes

        expected = str(Path.cwd() / ("中文路径" * 80) / "HRToolkit.exe")

        def read_image(module, buffer, capacity):
            self.assertIsNone(module)
            if len(expected) >= capacity:
                buffer.value = expected[:capacity - 1]
                return capacity
            buffer.value = expected
            return len(expected)

        query = Mock(side_effect=read_image)
        dll = SimpleNamespace(GetModuleFileNameW=query)
        with patch.object(ctypes, "WinDLL", return_value=dll, create=True):
            self.assertEqual(paths._windows_executable_path(), Path(expected))
        self.assertGreater(query.call_count, 1)
        self.assertEqual(query.argtypes, (wintypes.HMODULE, wintypes.LPWSTR, wintypes.DWORD))
        self.assertIs(query.restype, wintypes.DWORD)

    def test_windows_process_image_query_rejects_failure_and_permanent_truncation(self) -> None:
        query = Mock(return_value=0)
        dll = SimpleNamespace(GetModuleFileNameW=query)
        with patch.object(ctypes, "WinDLL", return_value=dll, create=True):
            self.assertIsNone(paths._windows_executable_path())
            query.side_effect = lambda _module, _buffer, capacity: capacity
            self.assertIsNone(paths._windows_executable_path())
        self.assertEqual(query.call_args.args[2], 32768)

    def test_frozen_windows_executable_comes_from_process_image_not_python_hint(self) -> None:
        expected = Path(sys.executable).resolve()
        with patch.object(sys, "platform", "win32"), patch.object(sys, "frozen", True, create=True):
            for reported in ("Ř<", "", str(expected.parent / "wrong.exe")):
                with self.subTest(reported=reported), patch.object(sys, "executable", reported):
                    with patch.object(paths, "_windows_executable_path", return_value=expected):
                        self.assertEqual(paths.current_executable_path(), expected)
                    with patch.object(paths, "_windows_executable_path", return_value=None):
                        with self.assertRaisesRegex(RuntimeError, "实际安装位置"):
                            paths.current_executable_path()

    def test_corrupt_frozen_executable_allows_project_lifecycle_and_preserves_install_guard(self) -> None:
        from hr_toolkit import app_update, history_store, project_store, runlog

        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp).resolve()
            executable = base / "程序 中文" / "HRToolkit.exe"
            executable.parent.mkdir()
            executable.write_bytes(b"MZ")
            project_root = base / "人事项目"
            with patch.object(sys, "platform", "win32"), patch.object(sys, "frozen", True, create=True), patch.object(sys, "executable", "Ř<"), patch.object(paths, "_windows_executable_path", return_value=executable):
                with project_store.ProjectStore.create(project_root, "人事项目") as created:
                    project_id = created.workspace.project_id
                with project_store.ProjectStore.open(project_root) as reopened:
                    self.assertEqual(reopened.workspace.project_id, project_id)
                    self.assertTrue(reopened.writable)
                with self.assertRaisesRegex(project_store.ProjectStoreError, "安装目录"):
                    project_store.ProjectStore.create(executable.parent / "禁止的项目", "禁止的项目")
                with self.assertRaisesRegex(history_store.HistoryStoreError, "安装目录"):
                    history_store._validate_data_root(executable.parent / "禁止的资料库")
                self.assertEqual(history_store._validate_data_root(base / "资料库"), base / "资料库")
                self.assertEqual(app_update.current_launcher_path(), executable)
                self.assertEqual(app_update.current_app_dir(), executable.parent)
                self.assertEqual(app_update._update_url_search_dirs(), (executable.parent,))
                self.assertEqual(runlog.current_app_dir(), executable.parent)
            self.assertFalse((executable.parent / "禁止的项目").exists())

    def test_frozen_launcher_repairs_child_executable_before_freeze_support(self) -> None:
        from hr_toolkit import launcher, runlog

        expected = Path(sys.executable).resolve()
        calls = []

        def freeze_support():
            self.assertEqual(sys.executable, str(expected))
            self.assertEqual(calls, [str(expected)])

        with patch.object(sys, "platform", "win32"), patch.object(sys, "frozen", True, create=True), patch.object(sys, "executable", "Ř<"), patch.object(paths, "_windows_executable_path", return_value=expected):
            with patch.object(launcher.multiprocessing, "set_executable", side_effect=calls.append), patch.object(launcher.multiprocessing, "freeze_support", side_effect=freeze_support) as freeze, patch.object(launcher, "run_headless_command", return_value=0), patch.object(runlog, "log_line"):
                self.assertEqual(launcher.main(["--version"]), 0)
                freeze.assert_called_once_with()

    def test_invalid_or_unavailable_home_uses_system_profile(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            fallback = Path(tmp).resolve()
            for value in (Path("Ř<"), fallback / "missing", Path("bad\x00home")):
                with self.subTest(value=repr(value)), patch.object(Path, "home", return_value=value), patch.object(paths, "_system_home_dir", return_value=fallback):
                    self.assertEqual(paths.user_home_dir(), fallback)
            with patch.object(Path, "home", side_effect=RuntimeError("Cannot determine home")), patch.object(paths, "_system_home_dir", return_value=fallback):
                self.assertEqual(paths.user_home_dir(), fallback)

    def test_valid_home_is_preserved_and_missing_fallback_fails_clearly(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            home = Path(tmp).resolve()
            with patch.object(Path, "home", return_value=home), patch.object(paths, "_system_home_dir") as system:
                self.assertEqual(paths.user_home_dir(), home)
                system.assert_not_called()
        with patch.object(Path, "home", return_value=Path("Ř<")), patch.object(paths, "_system_home_dir", return_value=None):
            with self.assertRaisesRegex(RuntimeError, "用户文件夹"):
                paths.user_home_dir()

    def test_windows_shell_folder_binds_unicode_and_checks_hresult(self) -> None:
        from ctypes import wintypes

        expected = str(Path.cwd() / "用户目录 中文")

        def read_folder(hwnd, csidl, token, flags, buffer):
            self.assertEqual((hwnd, csidl, token, flags), (None, 0x28, None, 0))
            buffer.value = expected
            return 0

        query = Mock(side_effect=read_folder)
        dll = SimpleNamespace(SHGetFolderPathW=query)
        with patch.object(ctypes, "WinDLL", return_value=dll, create=True):
            self.assertEqual(paths._windows_shell_folder(0x28), Path(expected))
        self.assertEqual(query.argtypes, (wintypes.HWND, ctypes.c_int, wintypes.HANDLE, wintypes.DWORD, wintypes.LPWSTR))
        self.assertIs(query.restype, ctypes.c_int32)
        query.side_effect = None
        query.return_value = -2147467259
        with patch.object(ctypes, "WinDLL", return_value=dll, create=True):
            self.assertIsNone(paths._windows_shell_folder(0x28))

    @unittest.skipUnless(os.name == "nt", "Requires the real Windows Shell")
    def test_windows_profile_recovers_without_userprofile_environment(self) -> None:
        with patch.dict(os.environ, {"USERPROFILE": "Ř<"}):
            home = paths.user_home_dir()
        self.assertTrue(home.is_absolute())
        self.assertTrue(home.is_dir())

    def test_windows_profile_query_preserves_handle_width_and_always_closes_token(self) -> None:
        from ctypes import wintypes

        expected = str(Path.cwd() / "用户目录 中文")
        token_value = 0x100000123 if ctypes.sizeof(ctypes.c_void_p) == 8 else 123

        def open_token(process, access, token):
            self.assertEqual((process, access), (-1, 0x0008))
            token._obj.value = token_value
            return True

        def query_profile(token, buffer, size):
            self.assertEqual(token.value, token_value)
            if buffer is None:
                size._obj.value = len(expected) + 1
                return False
            buffer.value = expected
            return True

        kernel = SimpleNamespace(GetCurrentProcess=Mock(return_value=-1), CloseHandle=Mock(return_value=True))
        security = SimpleNamespace(OpenProcessToken=Mock(side_effect=open_token))
        profile = SimpleNamespace(GetUserProfileDirectoryW=Mock(side_effect=query_profile))
        dlls = {"kernel32": kernel, "advapi32": security, "userenv": profile}
        with patch.object(ctypes, "WinDLL", side_effect=lambda name, **_kwargs: dlls[name], create=True):
            self.assertEqual(paths._windows_profile_dir(), Path(expected))
            self.assertIs(kernel.GetCurrentProcess.restype, wintypes.HANDLE)
            self.assertEqual(kernel.CloseHandle.call_args.args[0].value, token_value)
            kernel.CloseHandle.assert_called_once()
            kernel.CloseHandle.reset_mock()
            profile.GetUserProfileDirectoryW.side_effect = lambda *_args: False
            self.assertIsNone(paths._windows_profile_dir())
            kernel.CloseHandle.assert_called_once()
            kernel.CloseHandle.reset_mock()
            security.OpenProcessToken.side_effect = lambda *_args: False
            self.assertIsNone(paths._windows_profile_dir())
            kernel.CloseHandle.assert_not_called()

    def test_windows_user_directories_share_validated_environment_and_shell_fallback(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp).resolve()
            with patch.object(sys, "platform", "win32"), patch.dict(os.environ, {"LOCALAPPDATA": str(base)}), patch.object(paths, "_windows_shell_folder") as shell:
                for kind in ("config", "data", "state"):
                    self.assertEqual(paths.user_app_data_dir(kind), base)
                shell.assert_not_called()
            for malformed in ("Ř<", "relative/data", ""):
                with self.subTest(value=repr(malformed)), patch.object(sys, "platform", "win32"), patch.dict(os.environ, {"LOCALAPPDATA": malformed}), patch.object(paths, "_windows_shell_folder", return_value=base) as shell:
                    self.assertEqual(paths.user_app_data_dir("config"), base)
                    shell.assert_called_once_with(0x1C)
            with patch.object(sys, "platform", "win32"), patch.dict(os.environ, {"LOCALAPPDATA": "Ř<"}), patch.object(paths, "_windows_shell_folder", return_value=None), patch.object(paths, "user_home_dir", return_value=base):
                self.assertEqual(paths.user_app_data_dir("data"), base / "AppData" / "Local")

    def test_relative_xdg_hints_do_not_redirect_data_into_working_directory(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            home = Path(tmp).resolve()
            with patch.object(sys, "platform", "linux"), patch.dict(os.environ, {"XDG_CONFIG_HOME": "relative", "XDG_DATA_HOME": "relative", "XDG_STATE_HOME": "relative"}), patch.object(paths, "user_home_dir", return_value=home):
                self.assertEqual(paths.user_app_data_dir("config"), home / ".config")
                self.assertEqual(paths.user_app_data_dir("data"), home / ".local" / "share")
                self.assertEqual(paths.user_app_data_dir("state"), home / ".local" / "state")

    def test_recovered_home_keeps_updater_directory_protection(self) -> None:
        from hr_toolkit.update_runner import _validate_app_dir

        with tempfile.TemporaryDirectory() as tmp:
            home = Path(tmp).resolve()
            with patch.object(Path, "home", return_value=Path("Ř<")), patch.object(paths, "_system_home_dir", return_value=home):
                _validate_app_dir(home / "应用")
                with self.assertRaisesRegex(RuntimeError, "范围过大"):
                    _validate_app_dir(home)


if __name__ == "__main__":
    unittest.main()
