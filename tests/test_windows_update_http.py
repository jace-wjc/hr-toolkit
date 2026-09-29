"""Offline transport/policy regression tests; not Windows device acceptance."""

import ctypes
import io
import json
import ssl
import unittest
import urllib.error
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from hr_toolkit import app_update as updater
from hr_toolkit import update_diagnostics as diagnostics
from hr_toolkit import windows_update_http as native


class FakeAPI:
    def __init__(self, body=b'{"tag_name":"v0.9.25"}', status=200, fail=""):
        self.body, self.status, self.fail = body, status, fail
        self.offset = 0
        self.closed, self.options, self.timeouts, self.requests = [], [], [], []
        self.length = str(len(body))

    def WinHttpOpen(self, *args):
        self.open_args = args
        return 0 if self.fail == "open" else 1

    def WinHttpConnect(self, *args):
        self.connect_args = args
        return 0 if self.fail == "connect" else 2

    def WinHttpOpenRequest(self, *args):
        self.requests.append(args)
        return 0 if self.fail == "request" else 3

    def WinHttpSetOption(self, handle, option, value, size):
        self.options.append((handle, option, value._obj.value))
        return self.fail != "option"

    def WinHttpSetTimeouts(self, *args):
        self.timeouts.append(args)
        return self.fail != "timeout"

    def WinHttpSendRequest(self, *args):
        self.send_args = args
        return self.fail != "send"

    def WinHttpReceiveResponse(self, *args):
        return self.fail != "receive"

    def WinHttpQueryHeaders(self, handle, query, name, output, size, index):
        if self.fail == "header":
            return False
        if query == 19 | 0x20000000:
            output._obj.value = self.status
        else:
            output.value = "application/json" if query == 1 else self.length
        return True

    def WinHttpReadData(self, handle, buffer, size, received):
        if self.fail == "read":
            return False
        chunk = self.body[self.offset:self.offset + size]
        ctypes.memmove(buffer, chunk, len(chunk))
        received._obj.value = len(chunk)
        self.offset += len(chunk)
        return True

    def WinHttpCloseHandle(self, handle):
        self.closed.append(handle)
        return True


class WindowsUpdateHTTPTests(unittest.TestCase):
    def setUp(self):
        log = patch("hr_toolkit.runlog.log_line")
        self.log = log.start()
        self.addCleanup(log.stop)

    def fetch(self, api, **kwargs):
        with patch.object(native, "_load_api", return_value=api), \
                patch.object(ctypes, "get_last_error", return_value=12175, create=True):
            return native.fetch_release(native.ENDPOINT, {"User-Agent": updater.USER_AGENT,
                                        "Accept": "application/json"}, kwargs.get("timeout", 10))

    def test_native_success_keeps_tls_identity_and_closes_all_handles(self):
        api = FakeAPI()
        with self.fetch(api) as response:
            self.assertEqual(json.load(response)["tag_name"], "v0.9.25")
            self.assertEqual(response.geturl(), native.ENDPOINT)
        self.assertEqual(api.closed, [3, 2, 1])
        self.assertEqual(api.options, [(1, 84, 0x800), (1, 4, 1), (3, 63, 7)])
        self.assertEqual(api.open_args, (updater.USER_AGENT, 1, None, None, 0))
        self.assertEqual(api.connect_args, (1, "gitee.com", 443, 0))
        self.assertEqual(api.requests[0][-1], 0x800000)
        self.assertTrue(all(0 < row[1] <= 10000 for row in api.timeouts))

    def test_redirect_is_returned_without_following_or_sending_credentials(self):
        api = FakeAPI(status=302)
        with self.fetch(api) as response:
            self.assertEqual(response.status, 302)
        self.assertEqual(len(api.requests), 1)
        self.assertNotIn("Authorization", api.send_args[1])
        self.assertNotIn("Cookie", api.send_args[1])
        self.assertIn((3, 63, 7), api.options)

    def test_failure_at_each_native_stage_closes_created_handles(self):
        for stage, closed in (("open", []), ("option", [1]), ("timeout", [1]),
                              ("connect", [1]), ("request", [2, 1]),
                              ("send", [3, 2, 1]), ("receive", [3, 2, 1]),
                              ("header", [3, 2, 1]), ("read", [3, 2, 1])):
            with self.subTest(stage=stage):
                api = FakeAPI(fail=stage)
                with self.assertRaises(native.NativeHTTPError) as error:
                    self.fetch(api)
                self.assertEqual(error.exception.winerror, 12175)
                self.assertEqual(api.closed, closed)

    def test_declared_and_streamed_size_limits(self):
        for length in ("33", "", "1"):
            api = FakeAPI(body=b"x" * 33)
            api.length = length
            with self.subTest(length=length), patch.object(native, "MAX_BYTES", 32):
                with self.assertRaises(ValueError):
                    self.fetch(api)
                self.assertLessEqual(api.offset, 33)
                self.assertEqual(api.closed, [3, 2, 1])

    def test_error_body_read_is_bounded(self):
        api = FakeAPI(body=b"x" * 9000, status=403)
        with self.fetch(api) as response:
            self.assertEqual(len(response.read()), 4096)
        self.assertLessEqual(api.offset, 4096)

    def test_native_abi_uses_system_dll_and_pointer_sized_handles(self):
        kernel, api = MagicMock(), MagicMock()

        def system_directory(buffer, size):
            buffer.value = "C:\\Windows\\System32"
            return len(buffer.value)

        kernel.GetSystemDirectoryW.side_effect = system_directory
        with patch.object(native, "sys", SimpleNamespace(platform="win32")), \
                patch.object(ctypes, "WinDLL", side_effect=[kernel, api], create=True) as loader:
            self.assertIs(native._load_api(), api)
        self.assertEqual(loader.call_args.args[0], native.os.path.join("C:\\Windows\\System32", "winhttp.dll"))
        self.assertIs(api.WinHttpOpen.restype, ctypes.c_void_p)
        self.assertIs(api.WinHttpSendRequest.argtypes[-1], ctypes.c_size_t)
        self.assertEqual(ctypes.sizeof(native.DWORD), 4)

    def test_expired_deadline_stops_before_network_send(self):
        api = FakeAPI()
        with patch.object(native.time, "monotonic", side_effect=[0, 2]):
            with self.assertRaises(TimeoutError):
                self.fetch(api, timeout=1)
        self.assertFalse(api.requests)
        self.assertEqual(api.closed, [1])

    def test_only_exact_endpoint_and_safe_headers_allowed(self):
        for url in (native.ENDPOINT.replace("https:", "http:"), native.ENDPOINT + "?token=x",
                    native.ENDPOINT.replace("gitee.com", "example.test")):
            with patch.object(native, "_load_api") as loader:
                with self.assertRaises(ValueError):
                    native.fetch_release(url, {}, 10)
                loader.assert_not_called()
        for headers in ({"Authorization": "x"}, {"Accept": "application/json\r\nCookie: x"}):
            with self.assertRaises(ValueError):
                native.fetch_release(native.ENDPOINT, headers, 10)

    def test_proxy_pac_and_custom_opener_skip_compatibility(self):
        registry = SimpleNamespace(HKEY_CURRENT_USER=1, OpenKey=MagicMock(), QueryValueEx=MagicMock())
        registry.QueryValueEx.side_effect = FileNotFoundError
        with patch.object(native, "sys", SimpleNamespace(platform="win32")), \
                patch.dict("sys.modules", {"winreg": registry}), \
                patch.dict(native.os.environ, {}, clear=True), \
                patch.object(native.urllib.request, "getproxies", return_value={}) as proxies, \
                patch.object(native.urllib.request, "_opener", None):
            self.assertTrue(native.direct_connection_allowed())
            proxies.return_value = {"https": "private-proxy"}
            self.assertFalse(native.direct_connection_allowed())
            proxies.return_value = {}
            with patch.dict(native.os.environ, {"ALL_PROXY": "private-proxy"}):
                self.assertFalse(native.direct_connection_allowed())
            with patch.object(native.urllib.request, "_opener", object()):
                self.assertFalse(native.direct_connection_allowed())
            registry.QueryValueEx.side_effect = None
            registry.QueryValueEx.return_value = ("private-PAC", 1)
            self.assertFalse(native.direct_connection_allowed())
            proxies.side_effect = OSError()
            self.assertFalse(native.direct_connection_allowed())

    def test_custom_tls_context_offers_http11_and_keeps_certificate_validation(self):
        context = ssl.create_default_context()
        with patch.object(updater.ssl, "create_default_context", return_value=context), \
                patch.object(updater.ssl.SSLContext, "set_alpn_protocols", autospec=True) as alpn, \
                patch.object(updater.ssl, "HAS_ALPN", True):
            self.assertIs(updater.create_https_context(), context)
            self.assertEqual(alpn.call_args.args[-1], ["http/1.1"])
        self.assertEqual(context.verify_mode, ssl.CERT_REQUIRED)
        self.assertTrue(context.check_hostname)

    def test_unavailable_alpn_does_not_disable_certificate_validation(self):
        for supported in (False, True):
            with patch.object(updater.ssl, "HAS_ALPN", supported), \
                    patch.object(updater.ssl.SSLContext, "set_alpn_protocols", side_effect=NotImplementedError):
                context = updater.create_https_context()
                self.assertTrue(context.check_hostname)
                self.assertEqual(context.verify_mode, ssl.CERT_REQUIRED)

    @staticmethod
    def blocked(code=403, body=b"<html>baidu_waf_intercept_page private-body</html>", headers=None):
        return urllib.error.HTTPError(native.ENDPOINT, code, "Blocked", headers or {}, io.BytesIO(body))

    def test_waf_recovery_enters_existing_check_and_copy_validation(self):
        prefix = "https://gitee.com/optimistic-little-sunspot/hr-toolkit/releases/download/v0.7.9/"
        filename = "HRToolkit_0.7.9_win7_x64-setup.exe"
        manifest = {"version": "0.7.9", "platforms": {
            "windows-x64-win7": {"sha256": "a" * 64, "file_url": prefix + filename}}}
        release = {"tag_name": "v0.7.9", "assets": [
            {"name": name, "browser_download_url": prefix + name} for name in ("latest.json", filename)]}
        for operation in ("same", "new", "copy"):
            responses = [self.blocked()]
            if operation != "copy":
                responses.append(io.BytesIO(json.dumps(manifest).encode()))
            with self.subTest(operation=operation), \
                    patch.object(updater, "sys", SimpleNamespace(platform="win32")), \
                    patch.object(updater, "update_manifest_urls", return_value=(native.ENDPOINT,)), \
                    patch.object(updater, "_open_url", side_effect=responses) as network, \
                    patch.object(native, "direct_connection_allowed", return_value=True), \
                    patch.object(native, "fetch_release", return_value=native.Response(
                        json.dumps(release).encode(), 200, {})) as fallback:
                if operation == "copy":
                    version, url = updater.latest_installer_download("win7")
                    self.assertEqual(version, "0.7.9")
                    self.assertIn("win7_x64-setup.exe", url)
                else:
                    result = updater.check_for_update("0.7.9" if operation == "same" else "0.7.8",
                                                      native.ENDPOINT, "windows-x64-win7")
                    if operation == "same":
                        self.assertIsNone(result)
                    else:
                        self.assertEqual(result.version, "0.7.9")
                        self.assertEqual(result.sha256, manifest["platforms"]["windows-x64-win7"]["sha256"])
                self.assertEqual(fallback.call_count, 1)
                self.assertEqual(network.call_count, len(responses))
                self.assertEqual(fallback.call_args.args[1]["User-Agent"], updater.USER_AGENT)

    def test_native_failure_preserves_bounded_list_fallback(self):
        cases = [TimeoutError(), native.NativeHTTPError("send", 12175), OSError(),
                 native.Response(b"<html>private</html>", 200, {}),
                 native.Response(b"[]", 200, {}), native.Response(b"", 302, {}),
                 native.Response(b"", 403, {}), native.Response(b"x" * (native.MAX_BYTES + 1), 200, {})]
        for outcome in cases:
            with self.subTest(outcome=type(outcome).__name__), \
                    patch.object(updater, "sys", SimpleNamespace(platform="win32")), \
                    patch.object(updater, "_open_url", side_effect=[self.blocked(), self.blocked()]) as network, \
                    patch.object(native, "direct_connection_allowed", return_value=True), \
                    patch.object(native, "fetch_release", side_effect=[outcome]) as fallback:
                with self.assertRaises(updater.UpdateError):
                    updater._fetch_json_object(native.ENDPOINT, timeout=10)
                self.assertEqual(network.call_count, 2)
                self.assertEqual(fallback.call_count, 1)

    def test_normal_success_and_other_errors_never_switch_transport(self):
        cases = [self.blocked(body=b'{"error":"forbidden"}'), self.blocked(code=401),
                 self.blocked(code=429), self.blocked(headers={"Retry-After": "30"}),
                 self.blocked(body=b"<html>baidu_waf_intercept_page rate limit</html>"),
                 urllib.error.URLError(ssl.SSLCertVerificationError("private-cert")), TimeoutError()]
        with patch.object(updater, "sys", SimpleNamespace(platform="win32")), \
                patch.object(native, "fetch_release") as fallback:
            for error in cases:
                with patch.object(updater, "_open_url", side_effect=error):
                    with self.assertRaises(updater.UpdateError):
                        updater._fetch_json_value(native.ENDPOINT, timeout=10)
            with patch.object(updater, "_open_url", return_value=io.BytesIO(b'{"ok":true}')):
                self.assertEqual(updater._fetch_json_value(native.ENDPOINT, timeout=10), {"ok": True})
            fallback.assert_not_called()

    def test_nonwindows_custom_urls_and_proxy_do_not_switch(self):
        for platform, url, permitted in (("darwin", native.ENDPOINT, True),
                                         ("win32", "https://gitee.com/example/latest.json", True),
                                         ("win32", native.ENDPOINT, False)):
            with patch.object(updater, "sys", SimpleNamespace(platform=platform)), \
                    patch.object(updater, "_open_url", side_effect=self.blocked()), \
                    patch.object(native, "direct_connection_allowed", return_value=permitted), \
                    patch.object(native, "fetch_release") as fallback:
                with self.assertRaises(updater.UpdateError):
                    updater._fetch_json_value(url, timeout=10)
                fallback.assert_not_called()

    def test_compatibility_initialization_failure_preserves_original_error(self):
        with patch.object(updater, "sys", SimpleNamespace(platform="win32")), \
                patch.object(updater, "_open_url", side_effect=[self.blocked(), self.blocked()]) as network, \
                patch.object(native, "direct_connection_allowed", side_effect=OSError("private-path")), \
                patch.object(native, "fetch_release") as fallback:
            with self.assertRaisesRegex(updater.UpdateError, "HTTP 403"):
                updater._fetch_json_object(native.ENDPOINT, timeout=10)
            fallback.assert_not_called()
            self.assertEqual(network.call_count, 2)

    def test_recovery_logging_never_includes_response_body(self):
        with patch.object(updater, "sys", SimpleNamespace(platform="win32")), \
                patch.object(updater, "_open_url", side_effect=self.blocked()), \
                patch.object(native, "direct_connection_allowed", return_value=True), \
                patch.object(native, "fetch_release", return_value=native.Response(b'{"secret":"private"}', 200, {})), \
                diagnostics.session("check"):
            updater._fetch_json_value(native.ENDPOINT, timeout=10)
        messages = "\n".join(call.args[0] for call in self.log.call_args_list)
        self.assertIn('"outcome":"recovered"', messages)
        self.assertIn('"transport":"winhttp"', messages)
        self.assertNotIn("private", messages)

    def test_windows_build_diagnostic_uses_actual_build_not_compatibility_build(self):
        with patch.object(diagnostics.sys, "platform", "win32"), \
                patch.object(diagnostics.sys, "getwindowsversion", create=True,
                             return_value=SimpleNamespace(build=9200, platform_version=(10, 0, 26200))), \
                patch.object(diagnostics.platform, "win32_ver", return_value=("11", "10.0.26200", "", "")), \
                patch.object(diagnostics.platform, "release", return_value="11"), \
                patch.object(diagnostics.urllib.request, "getproxies", return_value={}), \
                diagnostics.session("check"):
            pass
        messages = "\n".join(call.args[0] for call in self.log.call_args_list)
        self.assertIn('"windows_build":26200', messages)
        self.assertNotIn('"windows_build":9200', messages)
