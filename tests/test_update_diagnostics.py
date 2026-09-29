from __future__ import annotations

import io
import json
import ssl
import threading
import unittest
import urllib.error
from concurrent.futures import ThreadPoolExecutor
from unittest.mock import patch

from hr_toolkit import app_update as updater, update_diagnostics as diagnostics


class Response(io.BytesIO):
    def __init__(self, payload, url="https://gitee.com/example/latest.json", headers=None):
        super().__init__(payload if isinstance(payload, bytes) else json.dumps(payload).encode("utf-8"))
        self.status = 200
        self.headers = headers or {"Content-Type": "application/json"}
        self.url = url

    def geturl(self):
        return self.url


class UpdateDiagnosticsTests(unittest.TestCase):
    def setUp(self):
        log_patch = patch("hr_toolkit.runlog.log_line")
        self.log = log_patch.start()
        self.addCleanup(log_patch.stop)
        proxy_patch = patch("hr_toolkit.update_diagnostics.urllib.request.getproxies", return_value={})
        proxy_patch.start()
        self.addCleanup(proxy_patch.stop)

    def records(self, name=None):
        records = [json.loads(call.args[0].split("[更新诊断] ", 1)[1])
                   for call in self.log.call_args_list if call.args[0].startswith("[更新诊断] ")]
        return [row for row in records if name is None or row["event"] == name]

    @staticmethod
    def error(code=403, body=b"<html>baidu_waf_intercept_page private-body</html>"):
        return urllib.error.HTTPError(updater.GITEE_LATEST_RELEASE_API_URL, code, "Forbidden", {
            "Content-Type": "text/html; charset=utf-8", "Retry-After": "30",
            "X-Request-Id": "request-123", "Server": "nginx",
            "Set-Cookie": "session=private-cookie", "Authorization": "Bearer private-token",
            "Location": "https://example.test/private?token=private-location",
        }, io.BytesIO(body))

    def test_success_retains_result_headers_and_single_request_with_one_manual_trace(self):
        url = "https://gitee.com/example/latest.json?token=private-query"
        with patch.object(updater, "_open_url", return_value=Response({"version": "0.9.24"}, url)) as network:
            with diagnostics.session("check", "manual"):
                result = updater.check_for_update("0.9.24", url, "windows-x64-modern")
        self.assertIsNone(result)
        self.assertEqual(network.call_count, 1)
        request = network.call_args.args[0]
        self.assertEqual(request.full_url, url)
        self.assertEqual(dict(request.header_items()), {"User-agent": updater.USER_AGENT, "Accept": "application/json"})
        self.assertEqual(len(self.records("start")), 1)
        self.assertEqual(self.records("start")[0]["trigger"], "manual")
        self.assertEqual(len({row["id"] for row in self.records()}), 1)
        self.assertEqual(self.records("result")[0]["outcome"], "no_new_version")
        self.assertEqual(self.records("response")[0]["status"], 200)
        self.assertEqual(self.records("finish")[0]["outcome"], "completed")
        self.assertNotIn("private-query", str(self.log.call_args_list))

    def test_waf_recovery_keeps_two_requests_and_correct_copy_link(self):
        url = "https://gitee.com/optimistic-little-sunspot/hr-toolkit/releases/download/v0.9.24/HRToolkit_0.9.24_win7_x64-setup.exe"
        release = {"tag_name": "v0.9.24", "assets": [{"name": "HRToolkit_0.9.24_win7_x64-setup.exe", "browser_download_url": url}]}
        with patch.object(updater, "_open_url", side_effect=[self.error(), Response([release])]) as network:
            self.assertEqual(updater.latest_installer_download("win7"), ("0.9.24", url))
        self.assertEqual(network.call_count, 2)
        self.assertEqual(self.records("error_sample")[0]["body_kind"], "html")
        self.assertTrue(self.records("error_sample")[0]["waf_marker"])
        self.assertEqual(self.records("response")[0]["retry-after"], "30")
        self.assertEqual(self.records("response")[0]["x-request-id"], "request-123")
        self.assertEqual(self.records("fallback")[0]["target"], "gitee_release_list")
        self.assertEqual(self.records("result")[0]["outcome"], "download_link_found")
        self.assertEqual([row["request"] for row in self.records("request_start")], [1, 2])
        text = str(self.log.call_args_list)
        for private in ("private-body", "private-cookie", "private-token", "private-location"):
            self.assertNotIn(private, text)

    def test_persistent_403_keeps_two_attempts_and_failure(self):
        with patch.object(updater, "_open_url", side_effect=[self.error(), self.error()]) as network:
            with self.assertRaisesRegex(updater.UpdateError, "HTTP 403"):
                updater.check_for_update("0.9.24", updater.GITEE_LATEST_RELEASE_API_URL, "windows-x64-modern")
        self.assertEqual(network.call_count, 2)
        self.assertEqual(len(self.records("request_end")), 2)
        self.assertEqual(self.records("finish")[0]["outcome"], "failed")
        self.assertEqual(self.records("finish")[0]["stage"], "release_list_fallback")

    def test_error_sample_is_bounded_and_never_records_body(self):
        stream = io.BytesIO(b"private-data" * 2000)
        response = urllib.error.HTTPError("https://example.test", 403, "Forbidden", {}, stream)
        with diagnostics.session("check"):
            diagnostics.error_sample(response, 1)
        self.assertEqual(stream.tell(), diagnostics.ERROR_SAMPLE_BYTES)
        self.assertTrue(self.records("error_sample")[0]["sample_at_limit"])
        self.assertNotIn("private-data", str(self.log.call_args_list))
        response.close()

    def test_sample_read_failure_preserves_http_error_and_retry(self):
        first, second = self.error(), self.error()
        with patch.object(first, "read1", side_effect=TimeoutError("private-read-error")), \
                patch.object(updater, "_open_url", side_effect=[first, second]) as network:
            with self.assertRaisesRegex(updater.UpdateError, "HTTP 403"):
                updater.check_for_update("0.9.24", updater.GITEE_LATEST_RELEASE_API_URL, "windows")
        self.assertEqual(network.call_count, 2)
        self.assertEqual(self.records("error_sample")[0]["sample"], "unavailable")
        self.assertNotIn("private-read-error", str(self.log.call_args_list))

    def test_invalid_json_is_logged_without_retry_or_raw_body(self):
        with patch.object(updater, "_open_url", return_value=Response(b"private-invalid-json")) as network:
            with self.assertRaisesRegex(updater.UpdateError, "JSON"):
                updater.fetch_update_manifest("https://gitee.com/example/latest.json")
        self.assertEqual(network.call_count, 1)
        self.assertEqual(len(self.records("json_invalid")), 1)
        self.assertEqual(self.records("finish")[0]["stage"], "manifest_fetch")
        self.assertNotIn("private-invalid-json", str(self.log.call_args_list))

    def test_timeout_and_certificate_errors_keep_existing_retry_policy(self):
        cases = [(TimeoutError("private-timeout"), 2),
                 (urllib.error.URLError(ssl.SSLCertVerificationError("private-cert")), 1)]
        for error, expected in cases:
            with self.subTest(error=type(error).__name__), \
                    patch.object(updater, "_open_url", side_effect=error) as network, \
                    patch.object(updater.time, "sleep") as sleep:
                self.log.reset_mock()
                with self.assertRaises(updater.UpdateError):
                    updater.fetch_update_manifest("https://gitee.com/example/latest.json")
                self.assertEqual(network.call_count, expected)
                self.assertEqual(sleep.call_count, expected - 1)
                self.assertEqual(self.records("request_end")[0]["outcome"], "connection_error")
                self.assertNotIn("private-", str(self.log.call_args_list))

    def test_logging_failure_cannot_change_successful_result(self):
        self.log.side_effect = OSError("log unavailable")
        with patch.object(updater, "_open_url", return_value=Response({"version": "0.9.24"})) as network:
            self.assertIsNone(updater.check_for_update("0.9.24", "https://gitee.com/example/latest.json", "windows"))
        self.assertEqual(network.call_count, 1)

    def test_environment_and_opener_proxy_values_are_not_logged(self):
        proxy = {"https": "http://private-user:private-password@private-proxy:8080", "no": "private-intranet"}
        with patch.object(diagnostics.urllib.request, "getproxies", return_value=proxy), \
                patch.dict(diagnostics.os.environ, {"HTTPS_PROXY": proxy["https"]}, clear=True):
            with diagnostics.session("check", "automatic"):
                pass
        row = self.records("proxy_snapshot")[0]
        self.assertTrue(row["https_configured"])
        self.assertTrue(row["env_proxy_present"])
        self.assertEqual(self.records("start")[0]["trigger"], "automatic")
        self.assertNotIn("private-", str(self.log.call_args_list))

    def test_configuration_source_and_custom_endpoint_are_sanitized(self):
        url = "https://private-user:private-password@example.test/private-path?token=private-token#private-fragment"
        with patch.dict(updater.os.environ, {updater.UPDATE_URL_ENV: url}, clear=True):
            with diagnostics.session("check"):
                self.assertEqual(updater.update_manifest_urls(), (url,))
                diagnostics.event("source", endpoint=diagnostics.endpoint(url))
        self.assertEqual(self.records("configuration")[0]["source"], "environment")
        self.assertEqual(self.records("source")[0]["endpoint"], "https://example.test/[redacted-path]")
        self.assertNotIn("private-", str(self.log.call_args_list))

    def test_default_and_file_sources_are_distinguishable_without_more_reads(self):
        for urls, expected in (((), "default"), (("https://gitee.com/custom/latest.json",), "update_url_file")):
            self.log.reset_mock()
            with patch.dict(updater.os.environ, {}, clear=True), \
                    patch.object(updater, "_read_update_url_files", return_value=urls) as read:
                with diagnostics.session("check"):
                    self.assertEqual(updater.update_manifest_urls(), urls or updater.DEFAULT_UPDATE_MANIFEST_URLS)
            read.assert_called_once_with()
            self.assertEqual(self.records("configuration")[0]["source"], expected)

    def test_compressed_error_body_is_not_decompressed_or_read(self):
        stream = io.BytesIO(b"private-compressed-data")
        response = urllib.error.HTTPError("https://example.test", 403, "Forbidden", {"Content-Encoding": "gzip"}, stream)
        with diagnostics.session("check"):
            diagnostics.error_sample(response, 1)
        self.assertEqual(stream.tell(), 0)
        self.assertEqual(self.records("error_sample")[0]["sample"], "unavailable")
        response.close()

    def test_unexpected_exception_message_cannot_leak_into_final_failure(self):
        with patch.object(updater, "_open_url", side_effect=RuntimeError("https://user:private-password@example.test/?token=private-token")):
            with self.assertRaises(updater.UpdateError) as error:
                updater.check_for_update("0.9.24", "https://gitee.com/example/latest.json", "windows")
        self.assertNotIn("private-", str(error.exception) + str(self.log.call_args_list))

    def test_threads_have_independent_ids_and_request_numbers(self):
        barrier = threading.Barrier(2)

        def worker(trigger):
            with diagnostics.session("check", trigger):
                barrier.wait(timeout=5)
                diagnostics.event("request_start", request=diagnostics.next_request())

        with ThreadPoolExecutor(max_workers=2) as pool:
            futures = [pool.submit(worker, trigger) for trigger in ("manual", "automatic")]
            for future in futures:
                future.result(timeout=10)
        starts = self.records("start")
        self.assertEqual(len({row["id"] for row in starts}), 2)
        self.assertEqual([row["request"] for row in self.records("request_start")], [1, 1])
        self.assertIsNone(diagnostics._current.get())

    def test_rate_limit_marker_is_evidence_not_a_claim_of_waf(self):
        with diagnostics.session("check"):
            response = self.error(429, b'{"error":"Application has exceeded the rate limit", "secret":"private"}')
            diagnostics.error_sample(response, 1)
            response.close()
        self.assertTrue(self.records("error_sample")[0]["rate_limit_marker"])
        self.assertFalse(self.records("error_sample")[0]["waf_marker"])
        self.assertEqual(self.records("error_sample")[0]["body_kind"], "json_like")


if __name__ == "__main__":
    unittest.main()
