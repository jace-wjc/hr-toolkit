from __future__ import annotations

import importlib.util
import io
import json
import ssl
import sys
import tempfile
import unittest
import urllib.error
import urllib.parse
from contextlib import redirect_stderr
from pathlib import Path
from unittest import mock


SCRIPTS_DIR = Path(__file__).resolve().parents[1] / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

METADATA_SPEC = importlib.util.spec_from_file_location(
    "generate_release_metadata",
    SCRIPTS_DIR / "generate_release_metadata.py",
)
release_metadata = importlib.util.module_from_spec(METADATA_SPEC)
assert METADATA_SPEC is not None and METADATA_SPEC.loader is not None
METADATA_SPEC.loader.exec_module(release_metadata)
sys.modules["generate_release_metadata"] = release_metadata

PUBLISH_SPEC = importlib.util.spec_from_file_location(
    "publish_gitee_release",
    SCRIPTS_DIR / "publish_gitee_release.py",
)
gitee_publish = importlib.util.module_from_spec(PUBLISH_SPEC)
assert PUBLISH_SPEC is not None and PUBLISH_SPEC.loader is not None
PUBLISH_SPEC.loader.exec_module(gitee_publish)


class FakeGiteeClient:
    def __init__(self, assets_dir: Path, tag: str) -> None:
        self.assets_dir = assets_dir
        self.tag = tag
        self.release: dict | None = {"id": 7, "tag_name": tag}
        self.attachments: list[dict] = [
            {"id": 1, "name": "stale.bin", "size": 5},
        ]
        self.upload_order: list[str] = []
        self.deleted: list[str] = []
        self.timeout_after_accepting: set[str] = set()
        self.upload_transport = "fake"

    def get_release_by_tag(self, _repository: str, _tag: str):
        return self.release

    def create_release(self, _repository: str, **kwargs):
        self.release = {"id": 7, "tag_name": kwargs["tag"]}
        return self.release

    def update_release(self, _repository: str, _release_id: str, **kwargs):
        self.release = {"id": 7, "tag_name": kwargs["tag"]}
        return self.release

    def list_attachments(self, _repository: str, _release_id: str):
        return list(self.attachments)

    def delete_attachment(self, _repository: str, _release_id: str, attachment_id: str):
        self.deleted.append(attachment_id)
        self.attachments = [
            item for item in self.attachments if str(item["id"]) != str(attachment_id)
        ]

    def upload_attachment(self, _repository: str, _release_id: str, file_path: Path):
        self.upload_order.append(file_path.name)
        attachment = {
            "id": len(self.attachments) + 10,
            "name": file_path.name,
            "size": file_path.stat().st_size,
            "browser_download_url": (
                f"https://gitee.com/company/hr/releases/download/{self.tag}/{file_path.name}"
            ),
        }
        self.attachments.append(attachment)
        if file_path.name in self.timeout_after_accepting:
            self.timeout_after_accepting.remove(file_path.name)
            raise gitee_publish.GiteeReleaseError("simulated response timeout")
        return attachment

    def get_public_latest_release(self, _repository: str):
        source_assets = [
            {
                "name": f"{self.tag}.zip",
                "browser_download_url": f"https://gitee.com/source/{self.tag}.zip",
            },
            {
                "name": f"{self.tag}.tar.gz",
                "browser_download_url": f"https://gitee.com/source/{self.tag}.tar.gz",
            },
        ]
        return {
            "id": 7,
            "tag_name": self.tag,
            "assets": list(self.attachments) + source_assets,
        }

    def get_public_json(self, _url: str):
        return json.loads((self.assets_dir / "latest.json").read_text(encoding="utf-8"))

    def get_public_bytes(self, _url: str):
        return (self.assets_dir / "SHA256SUMS.txt").read_bytes()


class GiteeCurlAPITransportTests(unittest.TestCase):
    """No network/subprocess execution: simulate curl's files and status."""

    def setUp(self):
        self.client = gitee_publish.GiteeClient("private/token+value", api_transport="curl",
                                               upload_transport="urllib", curl_executable="/usr/bin/curl", timeout=60)
        self.calls = []
        self.output = io.StringIO()
        self.responses = []
        runner = mock.patch.object(gitee_publish.subprocess, "run", side_effect=self.run_curl)
        self.runner = runner.start()
        self.addCleanup(runner.stop)
        sleeper = mock.patch.object(gitee_publish.time, "sleep")
        self.sleep = sleeper.start()
        self.addCleanup(sleeper.stop)
        stderr = redirect_stderr(self.output)
        stderr.__enter__()
        self.addCleanup(stderr.__exit__, None, None, None)

    def run_curl(self, command, **kwargs):
        response_path = Path(command[command.index("--output") + 1])
        body_path = response_path.parent / "body"
        self.calls.append((command, kwargs, body_path.read_bytes() if body_path.exists() else None))
        if gitee_publish.os.name == "posix":
            self.assertEqual(response_path.parent.stat().st_mode & 0o077, 0)
            self.assertEqual(response_path.stat().st_mode & 0o077, 0)
            if body_path.exists():
                self.assertEqual(body_path.stat().st_mode & 0o077, 0)
        item = self.responses.pop(0)
        if isinstance(item, Exception):
            raise item
        status, body, code = item
        response_path.write_bytes(body)
        return mock.Mock(returncode=code, stdout=str(status), stderr="private/token+value")

    def get_release(self):
        return self.client.get_release_by_tag("company/hr", "v0.9.25")

    def create_release(self):
        return self.client.create_release("company/hr", tag="v0.9.25", target_commitish="a" * 40,
                                          name="Release", body="Notes")

    def methods(self):
        return [command[command.index("--request") + 1] for command, _kwargs, _body in self.calls]

    def test_success_security_flags_token_privacy_and_cleanup(self):
        self.responses = [(200, b'{"id":7}', 0)]
        self.assertEqual(self.get_release(), {"id": 7})
        command, kwargs, body = self.calls[0]
        self.assertEqual(command[1], "--disable")
        for flag in ("--http1.1", "--tlsv1.2", "--max-time", "--max-filesize"):
            self.assertIn(flag, command)
        for flag in ("--insecure", "--location", "--retry", "--verbose"):
            self.assertNotIn(flag, command)
        self.assertNotIn("private", str(command))
        self.assertIn("access_token=private%2Ftoken%2Bvalue", kwargs["input"])
        self.assertEqual(kwargs["timeout"], 65)
        self.assertIsNone(body)
        self.assertFalse(Path(command[command.index("--output") + 1]).parent.exists())

    def test_waf_retry_recovers_and_persistent_block_stops(self):
        waf = b'<html id="baidu_waf_intercept_page">private/token+value</html>'
        self.responses = [(403, waf, 0), (200, b'{"id":7}', 0)]
        self.assertEqual(self.get_release(), {"id": 7})
        self.sleep.assert_called_once_with(15)
        self.calls.clear()
        self.sleep.reset_mock()
        self.responses = [(403, waf, 0)] * 4
        with self.assertRaisesRegex(gitee_publish.GiteeRequestError, "HTTP 403"):
            self.get_release()
        self.assertEqual(self.methods(), ["GET"] * 4)
        self.assertEqual(self.sleep.call_args_list, [mock.call(15), mock.call(30), mock.call(60)])
        self.assertNotIn("private", self.output.getvalue())
        self.assertNotIn("<html", self.output.getvalue())

    def test_certificate_redirect_permission_and_size_errors_are_final(self):
        for item in (("000", b"", 60), ("000", b"", 77), ("000", b"", 63),
                     (302, b"", 0), (403, b'{"message":"permission"}', 0)):
            self.calls.clear()
            self.responses = [item]
            with self.subTest(item=item), self.assertRaises(gitee_publish.GiteeRequestError) as error:
                self.get_release()
            self.assertFalse(error.exception.retryable)
            self.assertEqual(len(self.calls), 1)
            self.assertNotIn("private", str(error.exception))

    def test_timeout_then_read_recovers(self):
        for failure in (("000", b"", 28), gitee_publish.subprocess.TimeoutExpired("curl", 65)):
            self.responses = [failure, (200, b'{"id":7}', 0)]
            self.assertEqual(self.get_release(), {"id": 7})

    def test_lost_post_is_reconciled_not_blindly_replayed(self):
        self.responses = [("000", b"", 28), (200, b'{"id":7}', 0)]
        self.assertEqual(self.create_release(), {"id": 7})
        self.assertEqual(self.methods(), ["POST", "GET"])
        self.assertIn(b"access_token=private%2Ftoken%2Bvalue", self.calls[0][2])
        self.assertNotIn("private", str(self.calls[0][0]))

    def test_create_retries_only_after_confirmed_absence(self):
        self.responses = [(403, b"<html>blocked</html>", 0), (404, b"{}", 0), (200, b'{"id":7}', 0)]
        self.assertEqual(self.create_release(), {"id": 7})
        self.assertEqual(self.methods(), ["POST", "GET", "POST"])
        self.assertEqual(self.calls[0][2], self.calls[2][2])

    def test_public_download_follows_only_https_without_token(self):
        self.responses = [(200, b"checksum", 0)]
        self.assertEqual(self.client.get_public_bytes("https://gitee.com/checksum"), b"checksum")
        command, kwargs, body = self.calls[0]
        self.assertIn("--location", command)
        self.assertEqual(command[command.index("--proto-redir") + 1], "=https")
        self.assertNotIn("access_token", kwargs["input"])
        self.assertIsNone(body)

    def test_oversized_response_and_invalid_status_are_rejected(self):
        for response in ((200, b"x" * 33, 0), ("unexpected-output", b"{}", 0)):
            self.responses = [response]
            with mock.patch.object(gitee_publish, "API_RESPONSE_MAX_BYTES", 32), \
                    self.assertRaises(gitee_publish.GiteeRequestError) as error:
                self.get_release()
            self.assertFalse(error.exception.retryable)

    def test_missing_curl_does_not_fall_back_to_another_write_transport(self):
        self.client._curl_executable = None
        with mock.patch.object(gitee_publish.shutil, "which", return_value=None), \
                self.assertRaises(gitee_publish.GiteeRequestError):
            self.create_release()
        self.runner.assert_not_called()

    def test_urllib_context_advertises_http11_with_verification(self):
        with mock.patch.object(gitee_publish.ssl.SSLContext, "set_alpn_protocols", autospec=True) as alpn, \
                mock.patch.object(gitee_publish.ssl, "HAS_ALPN", True):
            client = gitee_publish.GiteeClient("test")
        self.assertEqual(alpn.call_args.args[-1], ["http/1.1"])
        self.assertTrue(client._ssl_context.check_hostname)
        self.assertEqual(client._ssl_context.verify_mode, ssl.CERT_REQUIRED)


class GiteeClientTransportTests(unittest.TestCase):
    """Offline regressions for the v0.9.24 API/WAF failure and safe retries."""

    WAF_BODY = b'<!DOCTYPE html><html><title>403</title><div id="baidu_waf_intercept_page"></div></html>'
    RELEASE = {"id": 7, "tag_name": "v0.9.24"}

    def setUp(self) -> None:
        self.client = gitee_publish.GiteeClient("test-private-token", upload_transport="urllib")
        self.output = io.StringIO()
        urlopen_patch = mock.patch.object(gitee_publish.urllib.request, "urlopen")
        sleep_patch = mock.patch.object(gitee_publish.time, "sleep")
        self.urlopen = urlopen_patch.start()
        self.addCleanup(urlopen_patch.stop)
        self.sleep = sleep_patch.start()
        self.addCleanup(sleep_patch.stop)
        self.stderr = redirect_stderr(self.output)
        self.stderr.__enter__()
        self.addCleanup(self.stderr.__exit__, None, None, None)

    def response(self, payload):
        result = mock.MagicMock()
        result.__enter__.return_value.read.return_value = (
            payload if isinstance(payload, bytes) else json.dumps(payload).encode()
        )
        return result

    def error(self, code, body=b'{"message":"request failed"}'):
        return urllib.error.HTTPError("https://gitee.com/api/v5/example", code, "failure", {}, io.BytesIO(body))

    def get_release(self):
        return self.client.get_release_by_tag("company/hr", "v0.9.24")

    def create_release(self):
        return self.client.create_release(
            "company/hr", tag="v0.9.24", target_commitish="a" * 40, name="Release", body="Notes",
        )

    def methods(self):
        return [call.args[0].get_method() for call in self.urlopen.call_args_list]

    def test_actual_ci_waf_403_retries_then_succeeds(self) -> None:
        self.urlopen.side_effect = [self.error(403, self.WAF_BODY), self.response(self.RELEASE)]
        self.assertEqual(self.get_release(), self.RELEASE)
        self.assertEqual(self.methods(), ["GET", "GET"])
        self.sleep.assert_called_once_with(15)
        self.assertIn("网页防护", self.output.getvalue())
        self.assertNotIn("<html>", self.output.getvalue())
        self.assertNotIn("test-private-token", self.output.getvalue())

    def test_persistent_waf_is_still_an_error_after_bounded_attempts(self) -> None:
        self.urlopen.side_effect = [self.error(403, self.WAF_BODY) for _ in range(4)]
        with self.assertRaisesRegex(gitee_publish.GiteeRequestError, "HTTP 403.*发布节点"):
            self.get_release()
        self.assertEqual(self.urlopen.call_count, 4)
        self.assertEqual(self.sleep.call_args_list, [mock.call(15), mock.call(30), mock.call(60)])

    def test_permission_and_certificate_errors_are_not_retried(self) -> None:
        for error in (
            self.error(401), self.error(403), self.error(400),
            urllib.error.URLError(ssl.SSLCertVerificationError("certificate invalid")),
        ):
            with self.subTest(error=error):
                self.urlopen.reset_mock()
                self.sleep.reset_mock()
                self.urlopen.side_effect = [error]
                with self.assertRaises(gitee_publish.GiteeRequestError) as caught:
                    self.get_release()
                self.assertFalse(caught.exception.retryable)
                self.assertEqual(self.urlopen.call_count, 1)
                self.sleep.assert_not_called()

    def test_transient_api_failures_retry(self) -> None:
        for error in (
            self.error(408), self.error(429), self.error(500), self.error(502), self.error(503), self.error(504),
            TimeoutError("timed out"), urllib.error.URLError(TimeoutError("SSL connection timeout")),
            ConnectionResetError("connection reset"),
            gitee_publish.http.client.IncompleteRead(b"partial"),
        ):
            with self.subTest(error=error):
                self.urlopen.side_effect = [error, self.response(self.RELEASE)]
                self.assertEqual(self.get_release(), self.RELEASE)

    def test_not_found_is_not_retried(self) -> None:
        self.urlopen.side_effect = [self.error(404)]
        self.assertIsNone(self.get_release())
        self.assertEqual(self.urlopen.call_count, 1)
        self.sleep.assert_not_called()

    def test_truncated_json_retries_for_reads(self) -> None:
        self.urlopen.side_effect = [self.response(b'{"id":'), self.response(self.RELEASE)]
        self.assertEqual(self.get_release(), self.RELEASE)
        self.assertEqual(self.methods(), ["GET", "GET"])

    def test_empty_create_response_is_reconciled_before_retry(self) -> None:
        self.urlopen.side_effect = [self.response(b""), self.response(self.RELEASE)]
        self.assertEqual(self.create_release(), self.RELEASE)
        self.assertEqual(self.methods(), ["POST", "GET"])

    def test_lost_create_response_checks_tag_instead_of_duplicating_release(self) -> None:
        self.urlopen.side_effect = [TimeoutError("response lost"), self.response(self.RELEASE)]
        self.assertEqual(self.create_release(), self.RELEASE)
        self.assertEqual(self.methods(), ["POST", "GET"])

    def test_create_retries_only_after_confirmed_not_found(self) -> None:
        self.urlopen.side_effect = [self.error(403, self.WAF_BODY), self.error(404), self.response(self.RELEASE)]
        self.assertEqual(self.create_release(), self.RELEASE)
        self.assertEqual(self.methods(), ["POST", "GET", "POST"])
        posts = [call.args[0].data for call in self.urlopen.call_args_list if call.args[0].get_method() == "POST"]
        self.assertEqual(posts[0], posts[1])

    def test_create_conflict_reuses_existing_tag_without_reposting(self) -> None:
        for status in (409, 422):
            with self.subTest(status=status):
                self.urlopen.reset_mock()
                self.urlopen.side_effect = [self.error(status), self.response(self.RELEASE)]
                self.assertEqual(self.create_release(), self.RELEASE)
                self.assertEqual(self.methods(), ["POST", "GET"])

    def test_create_permission_error_is_not_retried(self) -> None:
        self.urlopen.side_effect = [self.error(403)]
        with self.assertRaises(gitee_publish.GiteeRequestError):
            self.create_release()
        self.assertEqual(self.methods(), ["POST"])
        self.sleep.assert_not_called()

    def test_failed_lookup_never_authorizes_another_create(self) -> None:
        self.urlopen.side_effect = [TimeoutError("response lost")] + [self.error(503) for _ in range(4)]
        with self.assertRaises(gitee_publish.GiteeRequestError):
            self.create_release()
        self.assertEqual(self.methods(), ["POST", "GET", "GET", "GET", "GET"])

    def test_persistent_create_failure_stops_after_four_posts(self) -> None:
        self.urlopen.side_effect = [item for _ in range(4) for item in (self.error(403, self.WAF_BODY), self.error(404))]
        with self.assertRaises(gitee_publish.GiteeRequestError):
            self.create_release()
        self.assertEqual(self.methods(), ["POST", "GET"] * 4)

    def test_update_retries_the_same_payload(self) -> None:
        self.urlopen.side_effect = [self.error(503), self.response(self.RELEASE)]
        self.client.update_release("company/hr", "7", tag="v0.9.24", name="Release", body="Notes")
        self.assertEqual(self.methods(), ["PATCH", "PATCH"])
        self.assertEqual(self.urlopen.call_args_list[0].args[0].data, self.urlopen.call_args_list[1].args[0].data)

    def test_lost_delete_response_accepts_confirmed_absence(self) -> None:
        self.urlopen.side_effect = [TimeoutError("response lost"), self.error(404)]
        self.client.delete_attachment("company/hr", "7", "10")
        self.assertEqual(self.methods(), ["DELETE", "DELETE"])

    def test_attachment_post_is_not_blindly_replayed_by_transport(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            file_path = Path(temporary) / "SHA256SUMS.txt"
            file_path.write_bytes(b"fixture")
            self.urlopen.side_effect = [TimeoutError("response lost")]
            with self.assertRaises(gitee_publish.GiteeRequestError):
                self.client.upload_attachment("company/hr", "7", file_path)
        self.assertEqual(self.methods(), ["POST"])
        self.sleep.assert_not_called()

    def test_public_checksum_read_retries_without_credentials(self) -> None:
        self.urlopen.side_effect = [self.error(503), self.response(b"checksum")]
        self.assertEqual(self.client.get_public_bytes("https://gitee.com/checksum"), b"checksum")
        for call in self.urlopen.call_args_list:
            self.assertNotIn("access_token", call.args[0].full_url)
            self.assertNotIn("Authorization", call.args[0].headers)

    def test_public_verification_does_not_multiply_exhausted_transport_retries(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            assets_dir = Path(temporary)
            (assets_dir / "SHA256SUMS.txt").write_bytes(b"fixture")
            for verify in (gitee_publish.verify_public_source_release, gitee_publish.verify_public_release):
                with self.subTest(verify=verify.__name__):
                    self.urlopen.reset_mock()
                    self.sleep.reset_mock()
                    self.urlopen.side_effect = [self.error(403, self.WAF_BODY) for _ in range(4)]
                    extra = {"names": ()} if verify is gitee_publish.verify_public_release else {}
                    with self.assertRaisesRegex(gitee_publish.GiteeReleaseError, "HTTP 403"):
                        verify(self.client, assets_dir=assets_dir, repository="company/hr", tag="v0.9.24", **extra)
                    self.assertEqual(self.urlopen.call_count, 4)
                    self.assertEqual(self.sleep.call_args_list, [mock.call(15), mock.call(30), mock.call(60)])

    def test_error_redacts_url_encoded_tokens(self) -> None:
        secret = "secret+value/="
        self.client = gitee_publish.GiteeClient(secret)
        encoded = urllib.parse.quote_plus(secret)
        self.urlopen.side_effect = [self.error(403, json.dumps({"message": encoded}).encode())]
        with self.assertRaises(gitee_publish.GiteeRequestError) as caught:
            self.get_release()
        self.assertNotIn(secret, str(caught.exception))
        self.assertNotIn(encoded, str(caught.exception))


class GiteeMirrorTests(unittest.TestCase):
    VERSION = "0.2.3"
    TAG = "v0.2.3"
    GITEE_REPOSITORY = "optimistic-little-sunspot/hr-toolkit"
    GITHUB_REPOSITORY = "xhzwjc/hr-toolkit"

    def _build_assets(self, assets_dir: Path) -> None:
        for name in release_metadata.release_asset_names(self.VERSION, mac_variant="universal2"):
            (assets_dir / name).write_bytes(("payload:" + name).encode("utf-8"))
        windows_installer = f"HRToolkit_{self.VERSION}_x64-setup.exe"
        win7_installer = f"HRToolkit_{self.VERSION}_win7_x64-setup.exe"
        release_metadata.generate_release_metadata(
            assets_dir,
            version=self.VERSION,
            tag=self.TAG,
            repository=self.GITHUB_REPOSITORY,
            project_version=self.VERSION,
            notes=("Gitee 镜像测试更新内容",),
            download_base_url=(
                f"https://gitee.com/{self.GITEE_REPOSITORY}/releases/download"
            ),
            release_url=f"https://gitee.com/{self.GITEE_REPOSITORY}/releases/tag/{self.TAG}",
            fallback_download_base_url=(
                f"https://github.com/{self.GITHUB_REPOSITORY}/releases/download"
            ),
            primary_download_max_bytes=release_metadata.GITEE_ATTACHMENT_SAFE_MAX_BYTES,
            primary_download_asset_names=(windows_installer, win7_installer),
        )

    def test_validates_exact_gitee_assets_and_github_fallback(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            assets_dir = Path(temporary)
            self._build_assets(assets_dir)

            names = gitee_publish.validate_mirror_assets(
                assets_dir,
                version=self.VERSION,
                tag=self.TAG,
                repository=self.GITEE_REPOSITORY,
            )

            self.assertEqual(
                set(names),
                {
                    f"HRToolkit_{self.VERSION}_x64-setup.exe",
                    f"HRToolkit_{self.VERSION}_win7_x64-setup.exe",
                    "latest.json",
                    "SHA256SUMS.txt",
                },
            )
            manifest = json.loads((assets_dir / "latest.json").read_text(encoding="utf-8"))
            self.assertTrue(
                manifest["platforms"]["windows"]["file_url"].startswith("https://gitee.com/")
            )
            self.assertTrue(
                manifest["platforms"]["windows-x64-win7"]["file_url"].startswith(
                    "https://gitee.com/"
                )
            )
            self.assertTrue(
                manifest["platforms"]["macos"]["file_url"].startswith("https://github.com/")
            )
            self.assertNotIn("fallback_urls", manifest["platforms"]["macos"])

    def test_rejects_manifest_without_github_fallback(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            assets_dir = Path(temporary)
            self._build_assets(assets_dir)
            latest_path = assets_dir / "latest.json"
            manifest = json.loads(latest_path.read_text(encoding="utf-8"))
            manifest["platforms"]["windows"].pop("fallback_urls")
            latest_path.write_text(json.dumps(manifest), encoding="utf-8")

            with self.assertRaisesRegex(gitee_publish.GiteeReleaseError, "GitHub 备用"):
                gitee_publish.validate_mirror_assets(
                    assets_dir,
                    version=self.VERSION,
                    tag=self.TAG,
                    repository=self.GITEE_REPOSITORY,
                )

    def test_capacity_limit_rejects_release_when_required_exe_is_too_large(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            assets_dir = Path(temporary)
            self._build_assets(assets_dir)
            windows_installer = f"HRToolkit_{self.VERSION}_x64-setup.exe"
            release_metadata.generate_release_metadata(
                assets_dir,
                version=self.VERSION,
                tag=self.TAG,
                repository=self.GITHUB_REPOSITORY,
                project_version=self.VERSION,
                notes=("Gitee 镜像测试更新内容",),
                download_base_url=(
                    f"https://gitee.com/{self.GITEE_REPOSITORY}/releases/download"
                ),
                release_url=f"https://gitee.com/{self.GITEE_REPOSITORY}/releases/tag/{self.TAG}",
                fallback_download_base_url=(
                    f"https://github.com/{self.GITHUB_REPOSITORY}/releases/download"
                ),
                primary_download_max_bytes=1,
                primary_download_asset_names=(windows_installer,),
            )

            with self.assertRaisesRegex(
                gitee_publish.GiteeReleaseError,
                "Gitee 必需的 Windows EXE 不可发布",
            ):
                gitee_publish.validate_mirror_assets(
                    assets_dir,
                    version=self.VERSION,
                    tag=self.TAG,
                    repository=self.GITEE_REPOSITORY,
                    max_asset_bytes=1,
                )

    def test_publish_is_idempotent_and_uploads_latest_json_last(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            assets_dir = Path(temporary)
            self._build_assets(assets_dir)
            client = FakeGiteeClient(assets_dir, self.TAG)

            _release, names = gitee_publish.publish_gitee_release(
                client,
                assets_dir=assets_dir,
                version=self.VERSION,
                tag=self.TAG,
                repository=self.GITEE_REPOSITORY,
                target_commitish="a" * 40,
                name=f"HR Toolkit {self.TAG}",
                body="mirror",
            )
            gitee_publish.verify_public_release(
                client,
                assets_dir=assets_dir,
                repository=self.GITEE_REPOSITORY,
                tag=self.TAG,
                names=names,
                attempts=1,
            )

            self.assertEqual(client.deleted, ["1"])
            self.assertEqual(client.upload_order[-1], "latest.json")
            self.assertEqual(set(client.upload_order), set(names))

            client.upload_order.clear()
            gitee_publish.publish_gitee_release(
                client,
                assets_dir=assets_dir,
                version=self.VERSION,
                tag=self.TAG,
                repository=self.GITEE_REPOSITORY,
                target_commitish="a" * 40,
                name=f"HR Toolkit {self.TAG}",
                body="mirror",
            )
            self.assertEqual(client.upload_order, [])

    def test_upload_timeout_after_server_accepts_does_not_duplicate_asset(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            assets_dir = Path(temporary)
            self._build_assets(assets_dir)
            client = FakeGiteeClient(assets_dir, self.TAG)
            first_asset = sorted(
                name
                for name in gitee_publish.validate_mirror_assets(
                    assets_dir,
                    version=self.VERSION,
                    tag=self.TAG,
                    repository=self.GITEE_REPOSITORY,
                )
                if name != "latest.json"
            )[0]
            client.timeout_after_accepting.add(first_asset)

            _release, names = gitee_publish.publish_gitee_release(
                client,
                assets_dir=assets_dir,
                version=self.VERSION,
                tag=self.TAG,
                repository=self.GITEE_REPOSITORY,
                target_commitish="a" * 40,
                name=f"HR Toolkit {self.TAG}",
                body="mirror",
                retry_delay=0,
            )

            self.assertEqual(client.upload_order.count(first_asset), 1)
            self.assertEqual(client.upload_order[-1], "latest.json")
            self.assertEqual(
                {item["name"] for item in client.attachments},
                set(names),
            )

    def test_curl_upload_streams_file_without_token_in_process_arguments(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            asset = Path(temporary) / "asset.zip"
            asset.write_bytes(b"payload")
            response = {
                "id": 9,
                "name": asset.name,
                "size": asset.stat().st_size,
                "browser_download_url": "https://gitee.com/download/asset.zip",
            }
            completed = mock.Mock(
                returncode=0,
                stdout=json.dumps(response),
                stderr="",
            )
            client = gitee_publish.GiteeClient(
                "top-secret-token",
                upload_transport="curl",
                curl_executable="/usr/bin/curl",
            )

            with mock.patch.object(gitee_publish.subprocess, "run", return_value=completed) as run:
                result = client.upload_attachment(
                    self.GITEE_REPOSITORY,
                    "7",
                    asset,
                )

            command = run.call_args.args[0]
            self.assertNotIn("top-secret-token", "\n".join(command))
            self.assertIn("top-secret-token", run.call_args.kwargs["input"])
            self.assertIn("--http1.1", command)
            self.assertIn("Expect:", command)
            self.assertEqual(result, response)

    def test_curl_upload_error_redacts_token(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            asset = Path(temporary) / "asset.zip"
            asset.write_bytes(b"payload")
            completed = mock.Mock(
                returncode=28,
                stdout="",
                stderr="timeout top-secret-token",
            )
            client = gitee_publish.GiteeClient(
                "top-secret-token",
                upload_transport="curl",
                curl_executable="/usr/bin/curl",
            )

            with mock.patch.object(gitee_publish.subprocess, "run", return_value=completed):
                with self.assertRaisesRegex(gitee_publish.GiteeReleaseError, r"timeout \*\*\*"):
                    client.upload_attachment(self.GITEE_REPOSITORY, "7", asset)

    def test_partial_release_resumes_and_reuploads_latest_json_last(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            assets_dir = Path(temporary)
            self._build_assets(assets_dir)
            client = FakeGiteeClient(assets_dir, self.TAG)
            names = gitee_publish.validate_mirror_assets(
                assets_dir,
                version=self.VERSION,
                tag=self.TAG,
                repository=self.GITEE_REPOSITORY,
            )
            completed_name = next(name for name in names if name not in {"latest.json", "SHA256SUMS.txt"})
            completed_path = assets_dir / completed_name
            client.attachments = [
                {
                    "id": 20,
                    "name": completed_name,
                    "size": completed_path.stat().st_size,
                },
                {
                    "id": 21,
                    "name": "latest.json",
                    "size": (assets_dir / "latest.json").stat().st_size,
                },
            ]

            gitee_publish.publish_gitee_release(
                client,
                assets_dir=assets_dir,
                version=self.VERSION,
                tag=self.TAG,
                repository=self.GITEE_REPOSITORY,
                target_commitish="a" * 40,
                name=f"HR Toolkit {self.TAG}",
                body="mirror",
            )

            self.assertNotIn(completed_name, client.upload_order)
            self.assertEqual(client.upload_order[0], "SHA256SUMS.txt")
            self.assertEqual(client.upload_order[-1], "latest.json")
            self.assertIn("21", client.deleted)

    def test_dry_run_does_not_require_token(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            assets_dir = Path(temporary)
            self._build_assets(assets_dir)

            exit_code = gitee_publish.main(
                [
                    "--version",
                    self.VERSION,
                    "--tag",
                    self.TAG,
                    "--repository",
                    self.GITEE_REPOSITORY,
                    "--target-commitish",
                    "a" * 40,
                    "--assets-dir",
                    str(assets_dir),
                    "--dry-run",
                ]
            )

            self.assertEqual(exit_code, 0)

    def test_source_release_uploads_only_checksum_and_preserves_manual_assets(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            assets_dir = Path(temporary)
            checksum_path = assets_dir / "SHA256SUMS.txt"
            checksum_path.write_text(
                f"{'a' * 64}  HRToolkit_{self.VERSION}_x64-setup.exe\n",
                encoding="utf-8",
            )
            client = FakeGiteeClient(assets_dir, self.TAG)
            client.attachments = [
                {
                    "id": 20,
                    "name": f"HRToolkit_{self.VERSION}_x64-setup.exe",
                    "size": 123,
                    "browser_download_url": "https://gitee.com/manual-installer.exe",
                },
                {
                    "id": 21,
                    "name": "SHA256SUMS.txt",
                    "size": 1,
                    "browser_download_url": "https://gitee.com/stale-checksum.txt",
                },
            ]

            _release, names = gitee_publish.publish_gitee_source_release(
                client,
                assets_dir=assets_dir,
                tag=self.TAG,
                repository=self.GITEE_REPOSITORY,
                target_commitish="a" * 40,
                name=f"HR Toolkit {self.TAG}",
                body="source release",
                retry_delay=0,
            )
            gitee_publish.verify_public_source_release(
                client,
                assets_dir=assets_dir,
                repository=self.GITEE_REPOSITORY,
                tag=self.TAG,
                attempts=1,
            )

            self.assertEqual(names, ("SHA256SUMS.txt",))
            self.assertEqual(client.upload_order, ["SHA256SUMS.txt"])
            self.assertIn("21", client.deleted)
            self.assertIn(
                f"HRToolkit_{self.VERSION}_x64-setup.exe",
                {item["name"] for item in client.attachments},
            )

            client.upload_order.clear()
            gitee_publish.publish_gitee_source_release(
                client,
                assets_dir=assets_dir,
                tag=self.TAG,
                repository=self.GITEE_REPOSITORY,
                target_commitish="a" * 40,
                name=f"HR Toolkit {self.TAG}",
                body="source release",
                retry_delay=0,
            )
            self.assertEqual(client.upload_order, [])

    def test_source_release_rejects_any_staged_installer(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            assets_dir = Path(temporary)
            (assets_dir / "SHA256SUMS.txt").write_text(
                f"{'a' * 64}  HRToolkit_{self.VERSION}_x64-setup.exe\n",
                encoding="utf-8",
            )
            (assets_dir / f"HRToolkit_{self.VERSION}_x64-setup.exe").write_bytes(b"installer")

            with self.assertRaisesRegex(
                gitee_publish.GiteeReleaseError,
                "只能包含 SHA256SUMS.txt",
            ):
                gitee_publish.validate_source_release_assets(assets_dir)

    def test_source_release_dry_run_does_not_require_token(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            assets_dir = Path(temporary)
            (assets_dir / "SHA256SUMS.txt").write_text(
                f"{'a' * 64}  HRToolkit_{self.VERSION}_x64-setup.exe\n",
                encoding="utf-8",
            )

            exit_code = gitee_publish.main(
                [
                    "--version",
                    self.VERSION,
                    "--tag",
                    self.TAG,
                    "--repository",
                    self.GITEE_REPOSITORY,
                    "--target-commitish",
                    "a" * 40,
                    "--assets-dir",
                    str(assets_dir),
                    "--source-metadata-only",
                    "--dry-run",
                ]
            )

            self.assertEqual(exit_code, 0)

    def test_large_upload_defaults_to_streaming_curl(self) -> None:
        args = gitee_publish.build_parser().parse_args(
            [
                "--version", self.VERSION,
                "--target-commitish", "a" * 40,
                "--assets-dir", ".",
            ]
        )

        self.assertEqual(args.upload_transport, "curl")

    def test_urllib_multipart_rejects_large_asset_before_reading(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            asset = Path(temporary) / "large.zip"
            asset.write_bytes(b"12")

            with (
                mock.patch.object(gitee_publish, "URLLIB_MAX_UPLOAD_BYTES", 1),
                mock.patch.object(Path, "read_bytes", side_effect=AssertionError("must not read")),
                self.assertRaisesRegex(gitee_publish.GiteeReleaseError, "curl"),
            ):
                gitee_publish._multipart_body({}, asset)


if __name__ == "__main__":
    unittest.main()
