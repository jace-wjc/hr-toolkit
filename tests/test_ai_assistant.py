"""Unit tests for the cloud AI assistant backend (M1 scope).

No network access: HTTP behaviour is exercised through an injected opener and
Excel parsing runs against temporary workbooks.
"""

from __future__ import annotations

import io
import json
import tempfile
import time
import unittest
import urllib.error
from datetime import datetime
from pathlib import Path

from openpyxl import Workbook

from hr_toolkit.ai import client as ai_client
from hr_toolkit.ai.config import (
    AiConfigError,
    AiSettings,
    ProviderConfig,
    load_ai_settings,
    normalize_api_key,
    redact_api_key,
    save_ai_settings,
)
from hr_toolkit.ai.excel_context import (
    build_workbook_context,
    estimate_tokens,
    render_analysis_context,
    render_workbook_markdown,
    shrink_workbook_context,
)
from hr_toolkit.ai.history import (
    DEFAULT_TITLE,
    TITLE_MAX_CHARS,
    ConversationRecord,
    ConversationStore,
    format_updated,
    make_title,
)
from hr_toolkit.ai.markdown import markdown_to_plain, render_markdown_html, render_markdown_payload
from hr_toolkit.ai.status import (
    build_status_phrases,
    default_status_phrases,
    perception_key,
)


class StatusPhraseTests(unittest.TestCase):
    """等待首个字时的提示必须贴着这一轮实际发出去的东西。"""

    def test_image_attachment_never_claims_to_be_reading_a_spreadsheet(self):
        for seed in range(12):
            phrases = build_status_phrases(["image"], seed=seed)
            joined = "".join(phrases)
            self.assertIn("图", joined, "发了图却没说在看图：%r" % phrases)
            self.assertNotIn(
                "表格", joined, "发了图却还在说读表格（就是用户看到的那句）：%r" % phrases
            )

    def test_spreadsheet_attachment_reads_as_a_table(self):
        for seed in range(12):
            phrases = build_status_phrases(["sheet"], seed=seed)
            joined = "".join(phrases)
            self.assertNotIn("图", joined, "只发了表格却在说看图：%r" % phrases)
            self.assertTrue(
                any(marker in joined for marker in ("表格", "表头", "数据")),
                "表格附件却没有任何「表」相关的说法：%r" % phrases,
            )

    def test_mixed_attachments_mention_the_image(self):
        for seed in range(6):
            self.assertIn("图", "".join(build_status_phrases(["image", "sheet"], seed=seed)))

    def test_no_attachment_talks_about_the_question(self):
        for seed in range(6):
            joined = "".join(build_status_phrases([], seed=seed))
            self.assertNotIn("表格", joined)
            self.assertNotIn("图", joined)

    def test_perception_key_groups_attachment_kinds(self):
        self.assertEqual(perception_key([]), "none")
        self.assertEqual(perception_key(["image"]), "image")
        self.assertEqual(perception_key(["sheet"]), "sheet")
        self.assertEqual(perception_key(["image", "sheet", "sheet"]), "both")
        self.assertEqual(perception_key(["", None]), "none")

    def test_seed_is_reproducible_and_still_varies_between_turns(self):
        self.assertEqual(
            build_status_phrases(["image"], seed=5),
            build_status_phrases(["image"], seed=5),
        )
        sequences = {tuple(build_status_phrases(["sheet"], seed=n)) for n in range(8)}
        self.assertEqual(len(sequences), 1)
        self.assertIn("等待", next(iter(sequences))[0])

    def test_default_phrases_are_available_before_the_first_turn(self):
        self.assertTrue(default_status_phrases())


class AiConfigTests(unittest.TestCase):
    def test_roundtrip_persists_provider_overrides(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "ai-assistant.json"
            settings = AiSettings(
                active_provider="minimax",
                temperature=0.7,
                providers={
                    "deepseek": ProviderConfig(
                        api_key="sk-test-key-123456",
                        model="deepseek-v4-pro",
                        endpoint="",
                    )
                },
            )
            save_ai_settings(settings, path)
            loaded = load_ai_settings(path)
            self.assertEqual(loaded.active_provider, "minimax")
            self.assertEqual(loaded.temperature, 0.7)
            config = loaded.provider_config("deepseek")
            self.assertEqual(config.api_key, "sk-test-key-123456")
            self.assertEqual(config.model, "deepseek-v4-pro")
            preset = loaded.preset("deepseek")
            self.assertEqual(config.resolved_model(preset), "deepseek-v4-pro")
            self.assertEqual(
                config.resolved_endpoint(preset), preset.endpoint
            )

    def test_corrupted_file_falls_back_to_defaults(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "ai-assistant.json"
            path.write_text("{not json", encoding="utf-8")
            loaded = load_ai_settings(path)
            self.assertEqual(loaded.active_provider, "minimax")
            self.assertEqual(loaded.temperature, 0.3)
            self.assertFalse(loaded.is_ready())

    def test_problems_reports_missing_key(self):
        settings = AiSettings()
        problems = settings.problems()
        self.assertEqual(len(problems), 1)
        self.assertIn("API Key", problems[0])

    def test_unknown_provider_rejected(self):
        settings = AiSettings(active_provider="minimax")
        with self.assertRaises(AiConfigError):
            settings.preset("not-a-provider")

    def test_key_validation_and_redaction(self):
        with self.assertRaises(AiConfigError):
            normalize_api_key("bad\nkey")
        self.assertEqual(normalize_api_key("  "), "")
        self.assertEqual(redact_api_key("short"), "***")
        self.assertEqual(redact_api_key("sk-abcdef123456"), "sk-***3456")

    def test_base_url_is_completed_to_full_endpoint(self):
        from hr_toolkit.ai.config import normalize_chat_endpoint

        # 用户只填基地址：自动补全（本次线上问题的根因）
        self.assertEqual(
            normalize_chat_endpoint("minimax", "https://api.minimax.cn/v1"),
            "https://api.minimax.cn/v1/chat/completions",
        )
        # 完整地址保持原样
        full = "https://api.minimax.cn/v1/chat/completions"
        self.assertEqual(normalize_chat_endpoint("minimax", full), full)
        # 只有域名
        self.assertEqual(
            normalize_chat_endpoint("minimax", "https://api.minimaxi.com"),
            "https://api.minimaxi.com/v1/chat/completions",
        )
        # 结尾斜杠
        self.assertEqual(
            normalize_chat_endpoint("minimax", "https://api.minimax.chat/v1/"),
            "https://api.minimax.chat/v1/chat/completions",
        )
        self.assertEqual(
            normalize_chat_endpoint("deepseek", "https://api.deepseek.com"),
            "https://api.deepseek.com/v1/chat/completions",
        )
        # 老用户存过的原生接口地址不能被改写（改了就登不上了）
        legacy = "https://api.minimax.cn/v1/text/chatcompletion_v2"
        self.assertEqual(normalize_chat_endpoint("minimax", legacy), legacy)
        # 留空回落到预置地址
        settings = AiSettings()
        self.assertTrue(
            settings.provider_config("minimax").resolved_endpoint(settings.preset("minimax"))
            .endswith("/v1/chat/completions")
        )

    def test_minimax_preset_matches_official_model_list(self):
        """预置名字必须是官方文档里在用的（旧文档里的 Text-01 / VL-01 已不在列表中）。"""
        from hr_toolkit.ai.config import model_supports_vision

        preset = AiSettings().preset("minimax")
        self.assertEqual(preset.default_model, "MiniMax-M3")
        self.assertEqual(
            preset.endpoint, "https://api.minimax.cn/v1/chat/completions"
        )
        self.assertIn("MiniMax-M3", preset.models)
        self.assertIn("MiniMax-M2.7-highspeed", preset.models)
        self.assertNotIn("MiniMax-Text-01", preset.models)
        self.assertNotIn("MiniMax-VL-01", preset.models)
        # 只有 M3 支持图片，且读图判断不能只靠名字启发式（"M3" 里没有 vl/vision 字样）。
        self.assertTrue(model_supports_vision("minimax", "MiniMax-M3"))
        self.assertFalse(model_supports_vision("minimax", "MiniMax-M2.7-highspeed"))

    def test_glm_and_qwen_presets_use_the_official_openai_endpoints(self):
        """内置的四家地址必须是官方 OpenAI 兼容地址，用户不该被要求手填。"""
        from hr_toolkit.ai.config import PROVIDER_PRESETS

        self.assertEqual(
            PROVIDER_PRESETS["glm"].endpoint,
            "https://open.bigmodel.cn/api/paas/v4/chat/completions",
        )
        self.assertEqual(PROVIDER_PRESETS["glm"].default_model, "glm-5.3")
        self.assertEqual(
            PROVIDER_PRESETS["qwen"].endpoint,
            "https://token-plan.cn-beijing.maas.aliyuncs.com/compatible-mode/v1/chat/completions",
        )
        self.assertEqual(PROVIDER_PRESETS["qwen"].default_model, "qwen3.7-plus")

        # 四家的默认模型都得在自家候选表里，否则菜单里选不到正在用的那个。
        settings = AiSettings()
        for provider_id in ("deepseek", "minimax", "glm", "qwen"):
            preset = settings.preset(provider_id)
            self.assertIn(preset.default_model, preset.models, provider_id)
            resolved = settings.provider_config(provider_id).resolved_endpoint(preset)
            self.assertEqual(resolved, preset.endpoint, provider_id)
            self.assertTrue(resolved.endswith("/chat/completions"), provider_id)

    def test_endpoint_completion_respects_each_providers_version_segment(self):
        """GLM 的版本段是 /api/paas/v4、百炼是 /compatible-mode/v1，不能一律拼 /v1。"""
        from hr_toolkit.ai.config import normalize_chat_endpoint

        cases = [
            ("qwen", "https://token-plan.cn-beijing.maas.aliyuncs.com/compatible-mode/v1",
             "https://token-plan.cn-beijing.maas.aliyuncs.com/compatible-mode/v1/chat/completions"),
            ("qwen", "https://token-plan.cn-beijing.maas.aliyuncs.com/compatible-mode/v1/chat/completions",
             "https://token-plan.cn-beijing.maas.aliyuncs.com/compatible-mode/v1/chat/completions"),
            # 只有域名 → 补上该家的版本前缀
            ("glm", "https://open.bigmodel.cn",
             "https://open.bigmodel.cn/api/paas/v4/chat/completions"),
            ("qwen", "https://dashscope.aliyuncs.com",
             "https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions"),
            ("qwen", "https://dashscope-intl.aliyuncs.com",
             "https://dashscope-intl.aliyuncs.com/compatible-mode/v1/chat/completions"),
            # 官方文档里的基地址 → 接上接口路径
            ("glm", "https://open.bigmodel.cn/api/paas/v4",
             "https://open.bigmodel.cn/api/paas/v4/chat/completions"),
            ("qwen", "https://dashscope.aliyuncs.com/compatible-mode/v1",
             "https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions"),
            # 完整地址原样保留
            ("glm", "https://open.bigmodel.cn/api/paas/v4/chat/completions",
             "https://open.bigmodel.cn/api/paas/v4/chat/completions"),
        ]
        for provider_id, given, expected in cases:
            self.assertEqual(
                normalize_chat_endpoint(provider_id, given), expected, given
            )

    def test_saved_qwen_default_adopts_token_plan_without_changing_custom_urls(self):
        old = "https://dashscope.aliyuncs.com/compatible-mode/v1"
        custom = "https://example.invalid/compatible-mode/v1/chat/completions"
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "ai.json"
            for endpoint in (old, old + "/chat/completions", custom):
                settings = AiSettings(active_provider="qwen")
                config = settings.provider_config("qwen")
                config.endpoint = endpoint
                config.api_key = "test-key"
                config.model = "custom-model"
                save_ai_settings(settings, path)
                loaded = load_ai_settings(path)
                restored = loaded.provider_config("qwen")
                self.assertEqual(restored.api_key, "test-key")
                self.assertEqual(restored.model, "custom-model")
                self.assertEqual(restored.resolved_endpoint(loaded.preset()),
                                 custom if endpoint == custom else loaded.preset().endpoint)

    def test_glm_and_qwen_vision_flags_follow_the_official_lists(self):
        from hr_toolkit.ai.config import PROVIDER_PRESETS, model_supports_vision

        for model in ("glm-5.3-flash", "glm-5.3-flashx"):
            self.assertTrue(model_supports_vision("glm", model), model)
        # 纯文本的 GLM 不能被误标成能读图（之前 glm-5.3 名字里没有 v，容易漏判）
        for model in ("glm-4.6", "glm-5.3", "glm-4.7", "glm-4.5-air", "glm-4.5-flash"):
            self.assertFalse(model_supports_vision("glm", model), model)

        for model in (
            "qwen3.7-plus", "qwen3.8-max", "qwen3.8-flash",
            "qwen3-vl-plus", "qwen-vl-max", "qwen-vl-ocr",
        ):
            self.assertTrue(model_supports_vision("qwen", model), model)
        for model in ("qwen-plus", "qwen3-max", "qwen-flash", "qwen-long", "qwq-plus"):
            self.assertFalse(model_supports_vision("qwen", model), model)

        # 预置的视觉候选必须都在候选表里，否则菜单里打不了标。
        for provider_id, preset in PROVIDER_PRESETS.items():
            for model in preset.vision_models:
                self.assertIn(model, preset.models, f"{provider_id}/{model}")

    def test_user_can_add_and_remove_multiple_models(self):
        from hr_toolkit.ai.config import AiSettings, load_ai_settings, save_ai_settings

        settings = AiSettings()
        preset = settings.preset("minimax")
        config = settings.provider_config("minimax")

        # 没动过时显示预置候选
        self.assertTrue(config.uses_preset_models(preset))
        self.assertIn("MiniMax-M2.7", config.model_choices(preset))

        # 加多个自己的模型
        self.assertTrue(config.add_model(preset, "my-gateway-vl"))
        self.assertTrue(config.add_model(preset, "我的公司模型-2"))
        self.assertFalse(config.add_model(preset, "my-gateway-vl"))  # 去重
        self.assertIn("my-gateway-vl", config.model_choices(preset))
        self.assertIn("我的公司模型-2", config.model_choices(preset))

        # 删掉预置项：会先把预置列表播种进来，所以「删不掉」不会发生
        self.assertTrue(config.remove_model(preset, "MiniMax-M2.7"))
        self.assertNotIn("MiniMax-M2.7", config.model_choices(preset))
        self.assertIn("MiniMax-M3", config.model_choices(preset))

        # 落盘再读回：用户列表要活着
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "ai-assistant.json"
            save_ai_settings(settings, path)
            restored = load_ai_settings(path)
        restored_config = restored.provider_config("minimax")
        self.assertEqual(restored_config.models, config.models)
        self.assertIn("my-gateway-vl", restored_config.model_choices(restored.preset("minimax")))

    def test_removed_models_do_not_return_from_saved_active_or_custom_lists(self):
        cases = (("qwen", "qwen-plus", "qwen3.7-plus"),
                 ("glm", "glm-4.6", "glm-5.3"),
                 ("minimax", "MiniMax-M2", "MiniMax-M3"))
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "ai.json"
            for provider, removed, default in cases:
                settings = AiSettings(active_provider=provider)
                config = settings.provider_config()
                config.api_key = "test-key"
                config.model = removed
                config.models = [removed, "company-custom-model"]
                save_ai_settings(settings, path)
                loaded = load_ai_settings(path)
                actual = loaded.provider_config()
                self.assertEqual(actual.resolved_model(loaded.preset()), default)
                self.assertNotIn(removed, actual.model_choices(loaded.preset()))
                self.assertIn("company-custom-model", actual.model_choices(loaded.preset()))
                self.assertEqual(actual.api_key, "test-key")

    def test_curated_catalogs_match_requested_models(self):
        settings = AiSettings()
        self.assertEqual(settings.preset("glm").models, ("glm-5.3", "glm-5.3-flash", "glm-5.3-flashx"))
        self.assertEqual(settings.preset("minimax").models, ("MiniMax-M3", "MiniMax-M2.7-highspeed", "MiniMax-M2.7"))
        self.assertEqual(settings.preset("deepseek").models, ("deepseek-flash", "deepseek-v4-pro", "deepseek-v4-flash"))
        self.assertEqual(settings.preset("qwen").models, (
            "qwen3.7-plus", "qwen3.8-max", "qwen3.8-flash", "qwen3-vl-plus", "qwen-vl-max", "qwen-vl-ocr"))

    def test_blank_model_list_still_reports_the_active_model(self):
        from hr_toolkit.ai.config import AiSettings

        settings = AiSettings()
        preset = settings.preset("deepseek")
        config = settings.provider_config("deepseek")
        config.model = "my-own-deepseek"
        self.assertEqual(config.model_choices(preset)[0], "my-own-deepseek")

    def test_reasoning_split_only_for_minimax(self):
        from hr_toolkit.ai.client import build_payload, provider_extra

        self.assertEqual(provider_extra("minimax"), {"reasoning_split": True})
        self.assertEqual(provider_extra("deepseek"), {})
        payload = build_payload(
            [{"role": "user", "content": "hi"}],
            model="MiniMax-M3",
            stream=True,
            extra=provider_extra("minimax"),
        )
        self.assertTrue(payload["reasoning_split"])
        # extra 不能覆盖关键字段
        guarded = build_payload(
            [{"role": "user", "content": "hi"}],
            model="m",
            extra={"model": "hacked", "stream": False, "reasoning_split": True},
        )
        self.assertEqual(guarded["model"], "m")
        self.assertFalse(guarded["stream"])


def _sse_stream(chunks):
    lines = []
    for chunk in chunks:
        lines.append("data: " + json.dumps(chunk, ensure_ascii=False))
    lines.append("data: [DONE]")
    lines.append("")
    return io.BytesIO(("\n".join(lines)).encode("utf-8"))


class _FakeOpener:
    def __init__(self, response):
        self.response = response
        self.requests = []

    def __call__(self, request, **kwargs):
        self.requests.append((request, kwargs))
        return self.response


class AiClientTests(unittest.TestCase):
    def _messages(self):
        return [
            {"role": "system", "content": "你是测试助手"},
            {"role": "user", "content": "你好"},
        ]

    def test_build_payload_normalizes_roles_and_clamps_temperature(self):
        payload = ai_client.build_payload(
            [{"content": "hi"}, {"role": "assistant", "content": "ok"}],
            model="deepseek-chat",
            temperature=9.0,
            stream=True,
        )
        self.assertEqual(payload["model"], "deepseek-chat")
        self.assertEqual(payload["temperature"], 2.0)
        self.assertTrue(payload["stream"])
        self.assertEqual(payload["messages"][0]["role"], "user")

    def test_stream_chat_yields_deltas(self):
        stream = _sse_stream(
            [
                {"choices": [{"delta": {"content": "增长"}}]},
                {"choices": [{"delta": {"content": "值更好"}}]},
            ]
        )
        opener = _FakeOpener(stream)
        deltas = list(
            ai_client.stream_chat(
                self._messages(),
                endpoint="https://example.invalid/chat/completions",
                api_key="sk-test",
                model="deepseek-chat",
                opener=opener,
            )
        )
        self.assertEqual("".join(deltas), "增长值更好")
        request, kwargs = opener.requests[0]
        self.assertEqual(request.get_method(), "POST")
        self.assertEqual(request.headers.get("Authorization"), "Bearer sk-test")
        body = json.loads(request.data.decode("utf-8"))
        self.assertTrue(body["stream"])

    def test_stream_chat_reports_non_sse_body_instead_of_silent_empty_reply(self):
        """模型名写错时服务端会回 200 + 一段非流式正文；必须报错而不是留个空气泡。"""
        body = io.BytesIO(
            json.dumps({"error": "model not found"}).encode("utf-8")
        )
        opener = _FakeOpener(body)
        with self.assertRaises(ai_client.ChatError) as caught:
            list(
                ai_client.stream_chat(
                    self._messages(),
                    endpoint="https://example.invalid/v1/chat/completions",
                    api_key="sk-test",
                    model="MiniMax-Not-Real",
                    opener=opener,
                )
            )
        message = str(caught.exception)
        self.assertIn("MiniMax-Not-Real", message)
        self.assertIn("流式", message)

    def test_stream_chat_reports_empty_content(self):
        """SSE 正常但一个字符都没有：也要给出可操作的提示。"""
        stream = _sse_stream([{"choices": [{"delta": {}}]}])
        opener = _FakeOpener(stream)
        with self.assertRaises(ai_client.ChatError) as caught:
            list(
                ai_client.stream_chat(
                    self._messages(),
                    endpoint="https://example.invalid/v1/chat/completions",
                    api_key="sk-test",
                    model="MiniMax-M3",
                    opener=opener,
                )
            )
        self.assertIn("空回复", str(caught.exception))
        self.assertIn("MiniMax-M3", str(caught.exception))

    def test_stream_chat_keeps_thinking_out_of_the_visible_reply(self):
        """MiniMax 打开 reasoning_split 后思考走 reasoning_details，只取 content。"""
        stream = _sse_stream(
            [
                {"choices": [{"delta": {"reasoning_details": [{"text": "先想一下"}]}}]},
                {"choices": [{"delta": {"content": "结论：没问题"}}]},
            ]
        )
        opener = _FakeOpener(stream)
        deltas = list(
            ai_client.stream_chat(
                self._messages(),
                endpoint="https://api.minimax.cn/v1/chat/completions",
                api_key="sk-test",
                model="MiniMax-M3",
                opener=opener,
                extra=ai_client.provider_extra("minimax"),
            )
        )
        self.assertEqual("".join(deltas), "结论：没问题")
        request, _ = opener.requests[0]
        sent = json.loads(request.data.decode("utf-8"))
        self.assertTrue(sent["reasoning_split"])

    def test_chat_once_rejects_empty_reply(self):
        response = io.BytesIO(
            json.dumps({"choices": [{"message": {"content": "   "}}]}).encode("utf-8")
        )
        with self.assertRaises(ai_client.ChatError) as caught:
            ai_client.chat_once(
                self._messages(),
                endpoint="https://example.invalid/v1/chat/completions",
                api_key="sk-test",
                model="MiniMax-M3",
                opener=_FakeOpener(response),
            )
        self.assertIn("空回复", str(caught.exception))

    def test_stream_chat_raises_on_error_chunk(self):
        stream = _sse_stream(
            [{"error": {"message": "余额不足"}}]
        )
        with self.assertRaises(ai_client.ChatError) as ctx:
            list(
                ai_client.stream_chat(
                    self._messages(),
                    endpoint="https://example.invalid/chat/completions",
                    api_key="sk-test",
                    model="deepseek-chat",
                    opener=_FakeOpener(stream),
                )
            )
        self.assertIn("余额不足", str(ctx.exception))

    def test_minimax_base_resp_error_detected(self):
        stream = _sse_stream(
            [{"base_resp": {"status_code": 1004, "status_msg": "invalid api key"}}]
        )
        with self.assertRaises(ai_client.ChatError) as ctx:
            list(
                ai_client.stream_chat(
                    self._messages(),
                    endpoint="https://example.invalid/chat/completions",
                    api_key="sk-test",
                    model="MiniMax-Text-01",
                    opener=_FakeOpener(stream),
                )
            )
        self.assertIn("invalid api key", str(ctx.exception))

    def test_http_error_reports_actionable_hint(self):
        body = json.dumps({"error": {"message": "Authentication Fails"}}).encode()
        error = urllib.error.HTTPError(
            "https://example.invalid/chat/completions",
            401,
            "Unauthorized",
            email_message_headers(),
            io.BytesIO(body),
        )

        def opener(request, **kwargs):
            raise error

        with self.assertRaises(ai_client.ChatError) as ctx:
            ai_client.chat_once(
                self._messages(),
                endpoint="https://example.invalid/chat/completions",
                api_key="sk-wrong",
                model="deepseek-chat",
                opener=opener,
            )
        message = str(ctx.exception)
        self.assertIn("HTTP 401", message)
        self.assertIn("API Key", message)

    def test_url_error_reports_network_failure(self):
        def opener(request, **kwargs):
            raise urllib.error.URLError("connection refused")

        with self.assertRaises(ai_client.ChatError) as ctx:
            ai_client.chat_once(
                self._messages(),
                endpoint="https://example.invalid/chat/completions",
                api_key="sk-test",
                model="deepseek-chat",
                opener=opener,
            )
        self.assertIn("无法连接", str(ctx.exception))

    def test_missing_key_rejected_before_network(self):
        with self.assertRaises(ai_client.ChatError):
            ai_client.chat_once(
                self._messages(),
                endpoint="https://example.invalid/chat/completions",
                api_key="",
                model="deepseek-chat",
            )

    def test_stream_ignores_full_message_copy(self):
        """MiniMax 末块同时带 message 时不得重复输出整段回复。"""
        stream = _sse_stream(
            [
                {"choices": [{"delta": {"content": "接口"}}]},
                {"choices": [{"delta": {"content": "正常"}}]},
                {
                    "choices": [
                        {
                            "delta": {},
                            "finish_reason": "stop",
                            "message": {"role": "assistant", "content": "接口正常"},
                        }
                    ]
                },
            ]
        )
        deltas = list(
            ai_client.stream_chat(
                self._messages(),
                endpoint="https://example.invalid/chat/completions",
                api_key="sk-test",
                model="MiniMax-M2.7-highspeed",
                opener=_FakeOpener(stream),
            )
        )
        self.assertEqual("".join(deltas), "接口正常")

    def test_login_fail_error_explains_endpoint_hint(self):
        stream = _sse_stream(
            [{"base_resp": {"status_code": 1004, "status_msg":
             "login fail: Please carry the API secret key in the 'Authorization' field of the request header"}}]
        )
        with self.assertRaises(ai_client.ChatError) as ctx:
            list(
                ai_client.stream_chat(
                    self._messages(),
                    endpoint="https://example.invalid/chat/completions",
                    api_key="sk-test",
                    model="MiniMax-M2.7-highspeed",
                    opener=_FakeOpener(stream),
                )
            )
        message = str(ctx.exception)
        self.assertIn("login fail", message)
        self.assertIn("完整接口路径", message)

    def test_chat_once_parses_reply(self):
        payload = {
            "choices": [
                {"message": {"role": "assistant", "content": "连接正常"}}
            ]
        }
        opener = _FakeOpener(io.BytesIO(json.dumps(payload).encode("utf-8")))
        reply = ai_client.chat_once(
            self._messages(),
            endpoint="https://example.invalid/chat/completions",
            api_key="sk-test",
            model="deepseek-chat",
            opener=opener,
        )
        self.assertEqual(reply, "连接正常")


def email_message_headers():
    from email.message import Message

    return Message()


class ExcelContextTests(unittest.TestCase):
    def _make_workbook(self, path: Path):
        workbook = Workbook()
        sheet = workbook.active
        sheet.title = "汇总"
        sheet.append(["2026年8月工资表"])
        sheet.append(["姓名", "部门", "应发工资"])
        sheet.append(["张三", "一部", 3000])
        sheet.append(["李四", "二部", 2000])
        sheet.append(["王五", "一部", 1000])
        other = workbook.create_sheet("明细")
        other.append(["姓名", "备注"])
        other.append(["张三", "测试"])
        workbook.save(path)
        return path

    def test_header_detection_and_stats(self):
        with tempfile.TemporaryDirectory() as temp:
            path = self._make_workbook(Path(temp) / "工资表.xlsx")
            context = build_workbook_context(path)
            self.assertEqual(len(context.sheets), 2)
            sheet = context.sheets[0]
            self.assertEqual(sheet.name, "汇总")
            self.assertEqual(sheet.header_row, 2)
            self.assertEqual(sheet.headers, ["姓名", "部门", "应发工资"])
            self.assertEqual(sheet.total_data_rows, 3)
            stats = {stat.header: stat for stat in sheet.stats}
            self.assertIn("应发工资", stats)
            self.assertEqual(stats["应发工资"].total, 6000)
            self.assertEqual(stats["应发工资"].minimum, 1000)
            self.assertEqual(stats["应发工资"].count, 3)

    def test_grouped_header_detection_and_real_row_number(self):
        """人事表常见结构：标题行 + 空行 + 分组表头 + 分组续行 + 数据。

        老实现把最"满"的数据行当成表头，导致整表解析出 0 行数据，
        用户以为文件没发出去。这里钉死：分组表头要被选中并合并，
        且上报的 header_row 必须是工作表里的真实行号。
        """
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "社保明细.xlsx"
            workbook = Workbook()
            sheet = workbook.active
            sheet.append(["2026年8月社保明细"])  # 行1：单格标题
            sheet.append([None] * 6)  # 行2：空行，读取时应被跳过
            sheet.append(["姓名", "部门", "养老", "", "医疗", ""])  # 行3：分组表头
            sheet.append(["", "", "基数", "比例", "基数", "比例"])  # 行4：分组续行
            sheet.append(["张三", "一部", 3000, 0.08, 2000, 0.02])
            sheet.append(["李四", "二部", 2500, 0.08, 1800, 0.02])
            sheet.append(["王五", "一部", 2800, 0.08, 1900, 0.02])
            workbook.save(path)
            context = build_workbook_context(path)
            sheet_context = context.sheets[0]
            # 报真实行号（第 3 行），既不是标题行也不是 collected 下标
            self.assertEqual(sheet_context.header_row, 3)
            self.assertEqual(sheet_context.headers[0], "姓名")
            self.assertIn("养老 基数", sheet_context.headers)
            # 分组续行被吸收进表头，不会被当成数据行丢掉
            self.assertEqual(sheet_context.total_data_rows, 3)
            self.assertEqual(
                [row[0] for row in sheet_context.rows], ["张三", "李四", "王五"]
            )
            stats = {stat.header: stat for stat in sheet_context.stats}
            self.assertEqual(stats["养老 基数"].total, 8300)

    def test_shrink_workbook_context_fits_large_sheet_into_budget(self):
        """超大表应在预算内收缩而不是被拒绝：行数变少，统计仍基于全量。"""
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "大表.xlsx"
            workbook = Workbook()
            sheet = workbook.active
            sheet.append(["姓名", "金额"])
            for index in range(2000):
                sheet.append([f"员工{index + 1}", 100])
            workbook.save(path)
            context = build_workbook_context(path)
            budget = 1500
            self.assertGreater(len(render_workbook_markdown(context)), budget)
            self.assertTrue(shrink_workbook_context(context, budget))
            markdown = render_workbook_markdown(context)
            self.assertLessEqual(len(markdown), budget)
            self.assertTrue(context.sheets[0].truncated)
            self.assertLess(len(context.sheets[0].rows), 500)
            # 收缩只砍"贴给模型的行"，统计仍基于全量 2000 行
            stats = {stat.header: stat for stat in context.sheets[0].stats}
            self.assertEqual(stats["金额"].total, 200000)
            self.assertEqual(stats["金额"].count, 2000)
            # 小到塞不下的预算应如实返回 False，而不是无限循环或谎报成功
            self.assertFalse(shrink_workbook_context(context, 10))

    def test_markdown_contains_file_and_tables(self):
        with tempfile.TemporaryDirectory() as temp:
            path = self._make_workbook(Path(temp) / "工资表.xlsx")
            context = build_workbook_context(path)
            markdown = render_workbook_markdown(context)
            self.assertIn("工资表.xlsx", markdown)
            self.assertIn("| 姓名 | 部门 | 应发工资 |", markdown)
            self.assertIn("数值列统计", markdown)
            self.assertIn("6000", markdown)

    def test_truncation_keeps_head_and_tail_rows(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "大表.xlsx"
            workbook = Workbook()
            sheet = workbook.active
            sheet.append(["姓名", "金额"])
            for index in range(5):
                sheet.append([f"员工{index + 1}", (index + 1) * 100])
            workbook.save(path)
            context = build_workbook_context(path, max_rows=2)
            sheet_context = context.sheets[0]
            self.assertTrue(sheet_context.truncated)
            self.assertEqual(len(sheet_context.rows), 2)
            names = [row[0] for row in sheet_context.rows]
            self.assertEqual(names, ["员工1", "员工5"])
            markdown = render_workbook_markdown(context)
            self.assertIn("已截断", markdown)

    def test_long_cell_text_is_truncated(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "长文本.xlsx"
            workbook = Workbook()
            sheet = workbook.active
            sheet.append(["姓名", "备注"])
            sheet.append(["张三", "很" * 200])
            workbook.save(path)
            context = build_workbook_context(path)
            cell = context.sheets[0].rows[0][1]
            self.assertLessEqual(len(cell), 80)
            self.assertTrue(cell.endswith("…"))

    def test_rejects_non_excel_files(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "readme.txt"
            path.write_text("data", encoding="utf-8")
            with self.assertRaises(ValueError):
                build_workbook_context(path)

    def test_analysis_context_renders_question_and_multiple_files(self):
        with tempfile.TemporaryDirectory() as temp:
            contexts = []
            for name in ("八月.xlsx", "九月.xlsx"):
                path = Path(temp) / name
                workbook = Workbook()
                sheet = workbook.active
                sheet.append(["姓名", "应发工资"])
                sheet.append(["张三", 100])
                workbook.save(path)
                contexts.append(build_workbook_context(path))
            prompt = render_analysis_context(contexts, "谁的增长值更好？")
            self.assertIn("八月.xlsx", prompt)
            self.assertIn("九月.xlsx", prompt)
            self.assertIn("谁的增长值更好？", prompt)
            self.assertIn("共 2 个文件", prompt)
            self.assertGreater(estimate_tokens(prompt), 0)


class AiAssistantSessionTests(unittest.TestCase):
    def _settings(self):
        settings = AiSettings(active_provider="minimax")
        settings.provider_config("minimax").api_key = "sk-test"
        return settings

    def _session(self, opener):
        from hr_toolkit.ai.assistant import AiAssistantSession

        return AiAssistantSession(self._settings(), opener=opener)

    def _tiny_workbook(self, path: Path, rows):
        workbook = Workbook()
        sheet = workbook.active
        sheet.append(["姓名", "金额"])
        for name, amount in rows:
            sheet.append([name, amount])
        workbook.save(path)
        return path

    def test_attachment_lifecycle(self):
        from hr_toolkit.ai.assistant import AiAssistantSession

        session = self._session(_FakeOpener(io.BytesIO(b"{}")))
        with tempfile.TemporaryDirectory() as temp:
            path = self._tiny_workbook(Path(temp) / "a.xlsx", [("张三", 100)])
            row = session.add_attachment(path)
            self.assertEqual(row["name"], "a.xlsx")
            self.assertIn("1 行", row["summary"])
            self.assertEqual(len(session.pending_attachments()), 1)
            self.assertTrue(session.remove_attachment(0))
            self.assertFalse(session.pending_attachments())
        session.reset_conversation()

    def test_attachment_limit(self):
        from hr_toolkit.ai.assistant import MAX_ATTACHMENTS

        session = self._session(_FakeOpener(io.BytesIO(b"{}")))
        with tempfile.TemporaryDirectory() as temp:
            for index in range(MAX_ATTACHMENTS):
                path = self._tiny_workbook(Path(temp) / f"{index}.xlsx", [("张三", 1)])
                session.add_attachment(path)
            extra = self._tiny_workbook(Path(temp) / "extra.xlsx", [("张三", 1)])
            with self.assertRaises(ValueError) as ctx:
                session.add_attachment(extra)
            self.assertIn("最多", str(ctx.exception))

    def test_ask_streams_and_records_history(self):
        stream = _sse_stream(
            [
                {"choices": [{"delta": {"content": "甲表"}}]},
                {"choices": [{"delta": {"content": "增长更快"}}]},
            ]
        )
        session = self._session(_FakeOpener(stream))
        with tempfile.TemporaryDirectory() as temp:
            path = self._tiny_workbook(Path(temp) / "a.xlsx", [("张三", 100)])
            session.add_attachment(path)
            deltas = list(session.ask("谁的增长值更好？"))
        self.assertEqual("".join(deltas), "甲表增长更快")
        history = session.history()
        self.assertEqual(len(history), 2)
        self.assertEqual(history[0]["role"], "user")
        # 历史里存的是带表格正文的那条消息，下一轮追问模型才看得见表格
        self.assertIn("a.xlsx", history[0]["content"])
        self.assertIn("谁的增长值更好？", history[0]["content"])
        self.assertEqual(history[1]["role"], "assistant")
        self.assertEqual(history[1]["content"], "甲表增长更快")
        self.assertFalse(session.pending_attachments())

    def test_ask_without_question_or_attachments_rejected(self):
        session = self._session(_FakeOpener(io.BytesIO(b"{}")))
        with self.assertRaises(ValueError):
            list(session.ask(""))

    def test_ask_stop_keeps_partial_reply(self):
        stream = _sse_stream(
            [
                {"choices": [{"delta": {"content": "前半段"}}]},
                {"choices": [{"delta": {"content": "后半段"}}]},
            ]
        )
        session = self._session(_FakeOpener(stream))

        deltas = []
        generator = session.ask("问题")
        for delta in generator:
            deltas.append(delta)
            session.request_stop()
        self.assertEqual(deltas, ["前半段"])
        history = session.history()
        self.assertEqual(len(history), 2)
        self.assertIn("前半段", history[1]["content"])
        self.assertIn("已停止生成", history[1]["content"])

    def test_ask_requires_api_key(self):
        from hr_toolkit.ai.client import ChatError

        session = self._session(_FakeOpener(io.BytesIO(b"{}")))
        session.settings.provider_config("minimax").api_key = ""
        with self.assertRaises(ChatError):
            list(session.ask("你好"))

    def test_reset_clears_everything(self):
        session = self._session(_FakeOpener(io.BytesIO(b"{}")))
        session._append_history("user", "hi")
        session._append_history("assistant", "hello")
        session.reset_conversation()
        self.assertEqual(session.history(), [])
        self.assertFalse(session.pending_attachments())

    def test_context_message_includes_attachment_once(self):
        stream = _sse_stream([{"choices": [{"delta": {"content": "ok"}}]}])
        session = self._session(_FakeOpener(stream))
        with tempfile.TemporaryDirectory() as temp:
            path = self._tiny_workbook(Path(temp) / "表.xlsx", [("张三", 100)])
            session.add_attachment(path)
            # 附件由 consume_pending 交给本轮消息，而不是 build_messages 隐式消费
            batch = session.consume_pending()
            messages = session.build_messages("分析", batch)
            self.assertEqual(messages[0]["role"], "system")
            self.assertIn("表.xlsx", messages[-1]["content"])
            self.assertIn("分析", messages[-1]["content"])
            # 表内容进了会话历史，下一轮追问仍看得见附件
            list(session.ask("分析", batch))
            self.assertIn("表.xlsx", session.history()[-2]["content"])
            # 附件已经消费过，下一次只带问题
            followup = session.build_messages("继续", session.consume_pending())
        self.assertEqual(followup[-1]["content"], "继续")


class MarkdownRenderTests(unittest.TestCase):
    """模型返回的 Markdown 必须变成 Qt 富文本，而不是原样丢到界面。"""

    def test_streaming_keeps_completed_blocks_unchanged(self):
        prefix = "## Heading\n\nCompleted paragraph.\n\n"
        before = render_markdown_payload(prefix, streaming=True)["blocks"]
        after = render_markdown_payload(prefix + "Growing paragraph", streaming=True)["blocks"]
        self.assertEqual(len(before), 2)
        self.assertEqual(after[:2], before)
        self.assertEqual(len(after), 3)

    def test_streaming_balances_inline_styles_without_changing_final_source(self):
        for source, expected in (("**Important", "<b>Important</b>"), ("`employee_id", "monospace")):
            with self.subTest(source=source):
                partial = render_markdown_payload(source, streaming=True)
                self.assertIn(expected, partial["html"])
                self.assertEqual(render_markdown_payload(source)["html"], render_markdown_html(source))
        protected = render_markdown_payload("`**literal`", streaming=True)["html"]
        self.assertIn("**literal</span>", protected)
        self.assertNotIn("<b>", protected)
        unsafe = render_markdown_payload("**<img src=x>", streaming=True)["html"]
        self.assertIn("&lt;img src=x&gt;", unsafe)
        self.assertNotIn("<img", unsafe)

    def test_headings_carry_size_and_are_escaped(self):
        html = render_markdown_html("## 结论\n\n正文")
        self.assertIn('<h2 style="font-size:18px', html)
        self.assertIn("结论", html)
        self.assertIn("正文", html)
        self.assertNotIn("##", html)

    def test_inline_styles_do_not_leak_markers(self):
        html = render_markdown_html("**加粗** 与 *斜体* 与 ~~删除~~ 与 `code`")
        self.assertIn("<b>加粗</b>", html)
        self.assertIn("<i>斜体</i>", html)
        self.assertIn("<s>删除</s>", html)
        self.assertIn("monospace", html)
        for marker in ("**", "~~"):
            self.assertNotIn(marker, html)

    def test_code_span_shields_emphasis_markers(self):
        html = render_markdown_html("`a*b*c` 和 `**x**`")
        self.assertIn("a*b*c", html)
        self.assertIn("**x**", html)
        self.assertNotIn("<i>", html)
        self.assertNotIn("<b>", html)

    def test_fenced_block_is_pre_and_html_escaped(self):
        html = render_markdown_html("```python\nif a < b:\n    pass\n```")
        self.assertIn("<pre", html)
        self.assertIn("python", html)
        self.assertIn("if a &lt; b:", html)
        self.assertNotIn("```", html)

    def test_table_renders_cells_with_alignment(self):
        html = render_markdown_html("| 名称 | 金额 |\n| :--- | ---: |\n| 张三 | 100 |")
        self.assertIn("<table", html)
        self.assertIn("<tr>", html)
        self.assertIn('<td align="left"', html)
        self.assertIn('<td align="right"', html)
        self.assertIn("<b>金额</b>", html)
        self.assertIn("张三", html)

    def test_table_carries_the_ui_font_into_every_cell(self):
        """QML 富文本的表格单元格不继承控件字体，不显式带上中文会换成另一套字族。"""
        html = render_markdown_html(
            "| 名称 | 金额 |\n| --- | --- |\n| 张三 | 100 |", font_family="PingFang SC"
        )
        self.assertIn("font-family:PingFang SC", html)
        # 不传字体时不要凭空造一个 font-family 出来（Windows 车道靠系统字体回落）
        self.assertNotIn("font-family", render_markdown_html("| a |\n| --- |\n| b |"))

    def test_table_uses_the_light_grid_and_a_tinted_header(self):
        from hr_toolkit.ai.markdown import _THEMES

        html = render_markdown_html("| a | b |\n| --- | --- |\n| c | d |")
        self.assertIn('cellspacing="0"', html)
        self.assertIn('cellpadding="8"', html)
        self.assertIn(_THEMES["light"]["grid"], html)
        self.assertIn(_THEMES["light"]["head_bg"], html)
        self.assertIn(_THEMES["light"]["cell_bg"], html)
        self.assertIn('valign="top"', html)

    def test_single_column_table_is_still_a_table(self):
        """单列表格的 `| --- |` 曾经过不了分隔行判定，整块会退化成带竖线的段落。"""
        html = render_markdown_html("| 事项 |\n| --- |\n| 报销 |")
        self.assertIn("<table", html)
        self.assertIn("<b>事项</b>", html)
        self.assertIn("报销", html)
        self.assertNotIn("|", html)

    def test_native_tables_preserve_block_order_and_column_alignment(self):
        source = "## Summary\n\n| Name | Amount |\n| :---: | ---: |\n| Ann | 0 |\n\n- Done"
        result = render_markdown_payload(source)
        self.assertEqual([b["kind"] for b in result["blocks"]], ["text", "table", "text"])
        table = result["blocks"][1]
        self.assertEqual(table["alignments"], ["center", "right"])
        self.assertEqual(table["rows"], [["Ann", "0"]])
        self.assertEqual(result["html"], render_markdown_html(source))
        self.assertIn("<ul", result["blocks"][2]["html"])

    def test_table_pipes_empty_cells_and_safe_multiline_content(self):
        source = (
            "| Name | Note | Value |\n| --- | --- | --- |\n"
            "| A\\|B | `C|D`<br>Second<br />Third | |\n"
            "| Ann | <img src=x> `<br>` | 0 |\n| Bob |"
        )
        table = render_markdown_payload(source)["blocks"][0]
        self.assertEqual(len(table["headers"]), 3)
        self.assertEqual([len(row) for row in table["rows"]], [3, 3, 3])
        self.assertEqual(table["rows"][0][0], "A|B")
        self.assertIn("C|D", table["rows"][0][1])
        self.assertIn("<br>Second<br>Third", table["rows"][0][1])
        self.assertIn("—", table["rows"][0][2])
        self.assertIn("&lt;img src=x&gt;", table["rows"][1][1])
        self.assertIn("&lt;br&gt;", table["rows"][1][1])
        self.assertEqual(table["rows"][1][2], "0")
        self.assertIn("—", table["rows"][2][2])

    def test_large_table_retains_all_rows_with_bounded_width_sampling(self):
        source = "| ID | Notes |\n| ---: | --- |\n" + "\n".join(
            "| %d | Employee records pending confirmation |" % i for i in range(2000)
        )
        table = render_markdown_payload(source)["blocks"][0]
        self.assertEqual(len(table["rows"]), 2000)
        self.assertEqual(table["rows"][-1][0], "1999")
        self.assertEqual(sum(table["widths"]), 100)
        self.assertGreater(table["widths"][1], table["widths"][0])

    def test_table_grid_stays_lighter_than_the_dense_grid(self):
        """回归：网格底色再加深回原来那版，小面板里又会像 Excel 截图。"""
        from hr_toolkit.ai.markdown import _THEMES

        def brightness(color):
            return sum(int(color[index:index + 2], 16) for index in (1, 3, 5))

        self.assertGreater(brightness(_THEMES["light"]["grid"]), brightness("#E6E3DC"))
        self.assertLess(brightness(_THEMES["dark"]["grid"]), brightness("#39434F"))

    def test_nested_and_ordered_lists(self):
        nested = render_markdown_html("- 外层\n  - 内层")
        self.assertEqual(nested.count("<ul"), 2)
        self.assertEqual(nested.count("<li>"), 2)
        ordered = render_markdown_html("1. 第一\n2. 第二")
        self.assertIn("<ol", ordered)
        self.assertEqual(ordered.count("<li>"), 2)
        # 同一层级由无序切到有序时，必须先把上一个列表关掉
        switched = render_markdown_html("- 甲\n1. 乙")
        self.assertIn("</ul><ol", switched)

    def test_blockquote_and_rule(self):
        html = render_markdown_html("> 注意\n\n---")
        self.assertIn("<blockquote", html)
        self.assertIn("注意", html)
        self.assertIn("<hr", html)

    def test_links_and_html_injection_are_safe(self):
        html = render_markdown_html("见 [文档](https://example.com/a) 与 <script>x</script>")
        self.assertIn('<a href="https://example.com/a"', html)
        self.assertIn("&lt;script&gt;", html)
        self.assertNotIn("<script>", html)

    def test_palette_switches_with_theme(self):
        light = render_markdown_html("```\ncode\n```")
        dark = render_markdown_html("```\ncode\n```", dark=True)
        self.assertIn("#F3F2EE", light)
        self.assertIn("#1B2129", dark)
        self.assertNotEqual(light, dark)

    def test_markdown_to_plain_strips_markers(self):
        self.assertEqual(markdown_to_plain("## 标题\n\n**加粗** 和 `代码`"), "标题\n\n加粗 和 代码")


class ConversationHistoryTests(unittest.TestCase):
    """对话历史必须落盘、可切换、可删除，且坏文件不能拖垮助手。"""

    def _store(self, temp, **kwargs):
        return ConversationStore(Path(temp) / "ai-conversations.json", **kwargs)

    def test_create_get_remove(self):
        with tempfile.TemporaryDirectory() as temp:
            store = self._store(temp)
            record = store.create("第一次对话")
            self.assertIsNotNone(store.get(record.conversation_id))
            self.assertEqual(store.latest().conversation_id, record.conversation_id)
            self.assertTrue(store.remove(record.conversation_id))
            self.assertIsNone(store.get(record.conversation_id))
            self.assertFalse(store.remove("不存在"))
            self.assertIsNone(store.latest())

    def test_roundtrip_keeps_attachments_and_api_body(self):
        with tempfile.TemporaryDirectory() as temp:
            store = self._store(temp)
            record = store.create("会话")
            record.messages = [
                {
                    "role": "user",
                    "content": "分析",
                    "time": "10:01",
                    "apiContent": "分析\n表.xlsx 的表格",
                    "attachments": [{"name": "表.xlsx", "summary": "1 个工作表"}],
                },
                {"role": "assistant", "content": "结论如下", "time": "10:01"},
                # 非法角色在读取时应被丢弃
                {"role": "system", "content": "不该被读回来"},
            ]
            store.upsert(record)

            loaded = ConversationStore(store.path).get(record.conversation_id)
            self.assertEqual(len(loaded.messages), 2)
            self.assertEqual(loaded.messages[0]["apiContent"], "分析\n表.xlsx 的表格")
            self.assertEqual(loaded.messages[0]["attachments"][0]["name"], "表.xlsx")
            self.assertEqual(loaded.messages[1]["role"], "assistant")

    def test_corrupted_file_falls_back_to_empty(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "ai-conversations.json"
            path.write_text("{ 这不是 json", encoding="utf-8")
            store = ConversationStore(path)
            self.assertEqual(store.summaries(), [])
            self.assertIsNone(store.latest())
            store.create("新对话")
            self.assertEqual(len(ConversationStore(path).summaries()), 1)

    def test_limit_keeps_newest(self):
        with tempfile.TemporaryDirectory() as temp:
            store = self._store(temp, limit=3)
            for index in range(5):
                store.create("会话 %d" % index)
            summaries = store.summaries()
            self.assertEqual(len(summaries), 3)
            self.assertEqual(summaries[0]["title"], "会话 4")
            self.assertEqual(len(ConversationStore(store.path, limit=3).summaries()), 3)

    def test_save_is_atomic_and_leaves_no_temp_file(self):
        with tempfile.TemporaryDirectory() as temp:
            store = self._store(temp)
            store.create("会话")
            self.assertTrue(store.path.exists())
            leftovers = [p.name for p in Path(temp).iterdir() if p.name.startswith(".ai-chats-")]
            self.assertEqual(leftovers, [])

    def test_summary_prefers_last_assistant_reply(self):
        with tempfile.TemporaryDirectory() as temp:
            store = self._store(temp)
            record = store.create("会话")
            record.messages = [
                {"role": "assistant", "content": "旧的回答"},
                {"role": "user", "content": "追问"},
                {"role": "assistant", "content": "新的回答"},
            ]
            store.upsert(record)
            summary = store.summaries(now=time.time())[0]
            self.assertEqual(summary["preview"], "新的回答")
            self.assertEqual(summary["messageCount"], 3)
            self.assertEqual(summary["id"], record.conversation_id)

    def test_summary_title_falls_back_when_blank(self):
        self.assertEqual(ConversationRecord("x", title="").as_summary()["title"], DEFAULT_TITLE)

    def test_format_updated_buckets(self):
        reference = datetime(2026, 9, 21, 15, 0).timestamp()
        self.assertEqual(format_updated(datetime(2026, 9, 21, 9, 5).timestamp(), now=reference), "今天 09:05")
        self.assertEqual(format_updated(datetime(2026, 9, 20, 9, 5).timestamp(), now=reference), "昨天 09:05")
        self.assertEqual(format_updated(datetime(2026, 3, 2, 9, 5).timestamp(), now=reference), "03-02 09:05")
        self.assertEqual(format_updated(datetime(2025, 3, 2, 9, 5).timestamp(), now=reference), "2025-03-02")
        self.assertEqual(format_updated(0, now=reference), "")

    def test_make_title_strips_markers_and_truncates(self):
        self.assertEqual(make_title("").strip(), DEFAULT_TITLE)
        self.assertEqual(make_title("   \n  "), DEFAULT_TITLE)
        self.assertEqual(make_title("## 帮我看看这张表"), "帮我看看这张表")
        long_title = make_title("## " + "问" * 40)
        self.assertEqual(len(long_title), TITLE_MAX_CHARS + 1)
        self.assertTrue(long_title.endswith("…"))
        self.assertNotIn("#", long_title)



class AiReliabilityRegressionTests(unittest.TestCase):
    def session(self, response=None):
        from hr_toolkit.ai.assistant import AiAssistantSession
        settings = AiSettings()
        settings.provider_config().api_key = 'offline-test'
        return AiAssistantSession(settings, opener=_FakeOpener(response or _sse_stream([
            {'choices': [{'delta': {'content': 'answer'}}]}
        ])))

    def test_cancel_before_worker_does_not_open_network(self):
        session = self.session()
        session.prepare_request()
        session.request_stop()
        self.assertEqual(list(session.ask('question')), [])
        self.assertTrue(session.stopped)

    def test_consumed_attachments_release_slots_and_remove_correct_pending_item(self):
        from hr_toolkit.ai.assistant import Attachment, MAX_ATTACHMENTS
        session = self.session()
        session._attachments = [Attachment(Path(str(i)), str(i), '') for i in range(MAX_ATTACHMENTS)]
        sent = session.consume_pending()
        self.assertEqual(len(sent), MAX_ATTACHMENTS)
        self.assertEqual(session.attachments_summary(), [])
        session._attachments.append(Attachment(Path('new'), 'new', ''))
        self.assertTrue(session.remove_attachment(0))
        self.assertEqual(session.pending_attachments(), [])

    def test_retry_sends_saved_spreadsheet_and_image_context(self):
        from hr_toolkit.ai import images
        from unittest.mock import patch
        with tempfile.TemporaryDirectory() as folder:
            image = Path(folder) / 'image.png'
            image.write_bytes(b'\x89PNG\r\n\x1a\nimage')
            session = self.session()
            with patch('hr_toolkit.ai.assistant.stream_chat', return_value=iter(['answer'])) as send:
                list(session.ask('question', [], context_body='saved spreadsheet rows',
                                 image_rows=[{'kind': 'image', 'path': str(image), 'mime': 'image/png'}]))
            content = send.call_args.args[0][-1]['content']
            self.assertEqual(content[0]['text'], 'saved spreadsheet rows')
            self.assertTrue(content[1]['image_url']['url'].startswith('data:image/png;base64,'))
            self.assertEqual(session.last_context_body, 'saved spreadsheet rows')

    def test_whole_request_history_budget_drops_complete_old_turns(self):
        session = self.session()
        session.load_history([{'role': 'user', 'content': 'x' * 70000},
                              {'role': 'assistant', 'content': 'old'},
                              {'role': 'user', 'content': 'recent'},
                              {'role': 'assistant', 'content': 'recent answer'}])
        session.language = 'en_US'
        messages = session.build_messages('z' * 60000)
        self.assertEqual(messages[1]['content'], 'recent')
        self.assertIn('US English', messages[0]['content'])
        self.assertLess(sum(len(m['content']) for m in messages), 125000)

    def test_sse_multiline_and_truncated_response(self):
        source = io.BytesIO(b'data: {"choices":\ndata: [{"delta":{"content":"hello"}}]}\n\n')
        stream = ai_client.stream_chat([], endpoint='https://example.com', api_key='key',
                                      model='model', opener=_FakeOpener(source))
        self.assertEqual(next(stream), 'hello')
        with self.assertRaisesRegex(ai_client.ChatError, '不完整'):
            next(stream)

    def test_malformed_success_body_is_a_friendly_error(self):
        with self.assertRaises(ai_client.ChatError):
            ai_client.chat_once([], endpoint='https://example.com', api_key='key', model='model',
                                opener=_FakeOpener(io.BytesIO(b'[]')))

    def test_image_names_unique_even_with_frozen_clock(self):
        from hr_toolkit.ai.images import save_cached_image
        with tempfile.TemporaryDirectory() as folder:
            paths = {save_cached_image(b'image', directory=Path(folder)) for _ in range(100)}
            self.assertEqual(len(paths), 100)

    def test_corrupt_history_is_preserved_before_next_save(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'history.json'
            path.write_text('{broken', encoding='utf-8')
            store = ConversationStore(path)
            store.create('new')
            backups = list(path.parent.glob('history.json.corrupt-*'))
            self.assertEqual(len(backups), 1)
            self.assertEqual(backups[0].read_text(), '{broken')

    def test_failed_answer_excluded_from_restored_model_context(self):
        session = self.session()
        session.load_history([{'role': 'user', 'content': 'question'},
                              {'role': 'assistant', 'content': 'network error', 'status': 'error'}])
        self.assertNotIn('network error', str(session.build_messages('again')))

    def test_scan_limit_discloses_partial_totals(self):
        from unittest.mock import patch
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'large.xlsx'
            book = Workbook()
            sheet = book.active
            sheet.append(['Name', 'Amount'])
            for i in range(30):
                sheet.append(['Employee %d' % i, i])
            book.save(path)
            with patch('hr_toolkit.ai.excel_context.MAX_STATS_ROWS', 5):
                context = build_workbook_context(path)
            self.assertTrue(context.sheets[0].scan_limited)
            text = render_workbook_markdown(context)
            self.assertIn('不得作为全表合计', text)
            self.assertNotIn('统计基于全部数据', text)

    def test_stop_interrupts_a_blocked_socket_read(self):
        import socket
        import threading
        left, right = socket.socketpair()
        reading = threading.Event()
        control = ai_client.StreamControl()
        class Response:
            def __init__(self):
                self.reader = left.makefile("rb")
                self.fp = self.reader
            def __enter__(self):
                return self
            def __exit__(self, *args):
                self.reader.close()
                left.close()
            def readline(self, size):
                reading.set()
                return self.reader.readline(size)
        result, errors = [], []
        def run():
            try:
                result.extend(ai_client.stream_chat([], endpoint="https://example.com", api_key="key",
                              model="model", opener=lambda *a, **k: Response(), control=control))
            except Exception as exc:
                errors.append(exc)
        worker = threading.Thread(target=run, daemon=True)
        worker.start()
        try:
            self.assertTrue(reading.wait(1))
            control.cancel()
            worker.join(1)
            self.assertFalse(worker.is_alive(), "Stop did not unblock the response read")
            self.assertEqual(errors, [])
            self.assertEqual(result, [])
        finally:
            control.cancel()
            right.close()
            worker.join(1)
            left.close()

    def test_stream_cancellation_preserves_buffered_chunked_http_data(self):
        import http.client
        import socket
        left, right = socket.socketpair()
        left.settimeout(1)
        event = b'data: {"choices":[{"delta":{"content":"hello"}}]}\n\n'
        chunks = b"%x\r\n" % len(event) + event + b"\r\n"
        end = b"data: [DONE]\n\n"
        chunks += b"%x\r\n" % len(end) + end + b"\r\n0\r\n\r\n"
        try:
            right.sendall(b"HTTP/1.1 200 OK\r\nTransfer-Encoding: chunked\r\n\r\n" + chunks)
            response = http.client.HTTPResponse(left)
            response.begin()
            self.assertEqual(list(ai_client.stream_chat([], endpoint="https://example.com", api_key="key",
                             model="model", opener=lambda *a, **k: response)), ["hello"])
            self.assertTrue(response.closed)
        finally:
            right.close()
            left.close()

    def test_cancellable_socket_preserves_timeout_and_tls_retry_directions(self):
        import socket
        import ssl
        import threading
        from unittest.mock import Mock, patch
        transport = Mock()
        transport.gettimeout.return_value = 30
        transport.recv_into.side_effect = [ssl.SSLWantReadError(), ssl.SSLWantWriteError(), 3]
        reader = ai_client._CancellableSocket(transport, threading.Event())
        with patch.object(ai_client.select, "select") as wait:
            self.assertEqual(reader.recv_into(bytearray(3)), 3)
            self.assertEqual(wait.call_args_list[0].args[:2], ([transport], []))
            self.assertEqual(wait.call_args_list[1].args[:2], ([], [transport]))
        transport.setblocking.assert_called_once_with(False)
        transport.gettimeout.return_value = 0.05
        transport.recv_into.side_effect = BlockingIOError()
        reader = ai_client._CancellableSocket(transport, threading.Event())
        with patch.object(ai_client.time, "monotonic", side_effect=[1, 2]):
            with self.assertRaises(socket.timeout):
                reader.recv_into(bytearray(3))

    def test_stop_interrupts_a_partial_http_event_without_losing_worker_cleanup(self):
        import http.client
        import socket
        import threading
        left, right = socket.socketpair()
        left.settimeout(5)
        control = ai_client.StreamControl()
        reading = threading.Event()
        errors = []
        class Response(http.client.HTTPResponse):
            def readline(self, size=-1):
                reading.set()
                return super().readline(size)
        response = Response(left)
        right.sendall(b'HTTP/1.1 200 OK\r\nContent-Length: 999\r\n\r\ndata: {"choices":')
        response.begin()
        def run():
            try:
                list(ai_client.stream_chat([], endpoint="https://example.com", api_key="key",
                     model="model", opener=lambda *a, **k: response, control=control))
            except Exception as exc:
                errors.append(exc)
        worker = threading.Thread(target=run, daemon=True)
        worker.start()
        try:
            self.assertTrue(reading.wait(1))
            control.cancel()
            worker.join(1)
            self.assertFalse(worker.is_alive())
            self.assertEqual(errors, [])
            self.assertTrue(response.closed)
        finally:
            control.cancel()
            right.close()
            worker.join(1)
            left.close()

    def test_history_does_not_persist_rendered_html_and_recovers_interrupted_turn(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "history.json"
            store = ConversationStore(path)
            record = store.create("test")
            record.messages = [{"role": "assistant", "content": "", "html": "rendered data", "streaming": True}]
            store.upsert(record)
            self.assertNotIn('"html"', path.read_text())
            restored = ConversationStore(path).latest()
            self.assertEqual(restored.messages[0]["status"], "stopped")

    def test_null_bytes_cannot_collide_with_markdown_placeholders(self):
        self.assertIn("safe", render_markdown_html("\x009999\x00 `safe`"))

    def test_redirect_does_not_forward_credentials(self):
        request = urllib.request.Request("https://example.com", headers={"Authorization": "Bearer key"})
        with self.assertRaises(ai_client.ChatError):
            ai_client._NoRedirect().redirect_request(request, None, 307, "redirect", {}, "https://other.example")

    def test_image_cache_quota_preserves_existing_files(self):
        from hr_toolkit.ai.images import save_cached_image
        from unittest.mock import patch
        with tempfile.TemporaryDirectory() as folder:
            with patch("hr_toolkit.ai.images.MAX_CACHE_BYTES", 8):
                original = save_cached_image(b"first", directory=Path(folder))
                with self.assertRaisesRegex(ValueError, "缓存已满"):
                    save_cached_image(b"second", directory=Path(folder))
                self.assertEqual(original.read_bytes(), b"first")


if __name__ == "__main__":
    unittest.main()
