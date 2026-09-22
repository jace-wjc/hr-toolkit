"""AI assistant settings: provider presets, API keys and persistence.

Keys are stored only in the per-user settings file next to ``workspace-ui.json``
and are never written to run logs or crash reports. All persistence helpers are
side-effect free apart from the explicit save call so they can be unit tested
without touching the real user profile.
"""

from __future__ import annotations

import json
import os
import re
import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

from hr_toolkit.common.paths import user_app_data_dir

SETTINGS_FILENAME = "ai-assistant.json"
DEFAULT_PROVIDER = "minimax"
DEFAULT_TEMPERATURE = 0.3

_MAX_API_KEY_LENGTH = 200
_MAX_MODEL_LENGTH = 120
_MAX_ENDPOINT_LENGTH = 500
_CONTROL_CHARACTER = re.compile(r"[\x00-\x1f\x7f]")


class AiConfigError(ValueError):
    """Raised when persisted or supplied settings are unusable."""


@dataclass(frozen=True)
class ProviderPreset:
    provider_id: str
    label: str
    endpoint: str
    default_model: str
    # 相对基地址的接口路径；用户只填 https://域名/v1 时自动补全。
    chat_path: str = ""
    # 只有域名（没带版本段）时要补的版本前缀，例如 GLM 的 /api/paas/v4、
    # 百炼的 /compatible-mode/v1。留空表示用 OpenAI 通用的 /v1。
    api_prefix: str = ""
    # 面板里「切换模型」菜单直接给出的候选；用户仍可自己增删（见 ProviderConfig.models）。
    models: tuple = ()
    # 明确能读图的模型：面板里会打「可读图」标，也会在这里优先推荐。
    vision_models: tuple = ()
    # 预置候选的来源说明，显示在模型菜单底部，方便用户对照官方文档。
    models_note: str = ""


# MiniMax 用 OpenAI 兼容接口（https://api.minimax.cn/v1/chat/completions）。
# 只有 MiniMax-M3 支持在消息里放 image_url 图片块，M2.x 系列是纯文本；
# 别再用 /v1/text/chatcompletion_v2 —— 那是原生接口，不认 OpenAI 的 content 多段格式。
MINIMAX_MODELS: tuple = (
    "MiniMax-M3",
    "MiniMax-M2.7-highspeed",
    "MiniMax-M2.7",
)

# 智谱 GLM：OpenAI 兼容地址是 https://open.bigmodel.cn/api/paas/v4/chat/completions
# 仅保留 5.x 系列；Flash 的视觉能力需要显式标记。
GLM_MODELS: tuple = (
    "glm-5.3",
    "glm-5.3-flash",
    "glm-5.3-flashx",
)

# 阿里云百炼（通义千问）：使用客户指定的 Token Plan OpenAI 兼容地址。
# 基地址后追加 /chat/completions，供客户端直接发送请求。
# 当前推荐及读图能力：https://help.aliyun.com/zh/model-studio/models
# https://help.aliyun.com/zh/model-studio/vision （2026-09-22）
# 按客户要求移除旧版文字模型。
QWEN_MODELS: tuple = (
    "qwen3.7-plus",
    "qwen3.8-max",
    "qwen3.8-flash",
    "qwen3-vl-plus",
    "qwen-vl-max",
    "qwen-vl-ocr",
)

PROVIDER_PRESETS: Dict[str, ProviderPreset] = {
    "deepseek": ProviderPreset(
        "deepseek",
        "DeepSeek",
        "https://api.deepseek.com/chat/completions",
        "deepseek-flash",
        chat_path="/chat/completions",
        # https://api-docs.deepseek.com/updates/ (2026-09-10)
        models=("deepseek-flash", "deepseek-v4-pro", "deepseek-v4-flash"),
        vision_models=("deepseek-flash", "deepseek-v4-flash"),
        models_note="deepseek-flash 对应 V4.1 Flash；deepseek-v4-pro 对应 V4 Pro 0813。V4 Flash 0731 已下线，deepseek-v4-flash 仅为兼容名称，当前转至 V4.1 Flash。",
    ),
    "minimax": ProviderPreset(
        "minimax",
        "MiniMax",
        "https://api.minimax.cn/v1/chat/completions",
        "MiniMax-M3",
        chat_path="/chat/completions",
        models=MINIMAX_MODELS,
        vision_models=("MiniMax-M3",),
        models_note="MiniMax-M3 支持图片，M2.x 系列只认文字。",
    ),
    "glm": ProviderPreset(
        "glm",
        "智谱 GLM",
        "https://open.bigmodel.cn/api/paas/v4/chat/completions",
        "glm-5.3",
        chat_path="/chat/completions",
        api_prefix="/api/paas/v4",
        models=GLM_MODELS,
        vision_models=("glm-5.3-flash", "glm-5.3-flashx"),
        models_note="GLM-5.3-Flash 和 GLM-5.3-FlashX 支持图片；GLM-5.3 仅支持文字。",
    ),
    "qwen": ProviderPreset(
        "qwen",
        "通义千问",
        "https://token-plan.cn-beijing.maas.aliyuncs.com/compatible-mode/v1/chat/completions",
        "qwen3.7-plus",
        chat_path="/chat/completions",
        api_prefix="/compatible-mode/v1",
        models=QWEN_MODELS,
        vision_models=(
            "qwen3.7-plus", "qwen3.8-max", "qwen3.8-flash",
            "qwen3-vl-plus", "qwen-vl-max", "qwen-vl-ocr",
        ),
        models_note="Qwen3.7-Plus、Qwen3.8-Max / Flash 和 Qwen-VL 支持图片。",
    ),
}

# Remove the explicitly retired menu entries from persisted catalogs, including
# the active model (otherwise model_choices would prepend it again).
_REMOVED_MENU_MODELS = {
    "qwen": {"qwen-plus", "qwen3-max", "qwen-flash", "qwen-long", "qwq-plus"},
    "glm": {"glm-4.6", "glm-4.7", "glm-4.5-air", "glm-4.5-flash", "glm-4.6v", "glm-4v-flash"},
    "minimax": {"MiniMax-M2.5-highspeed", "MiniMax-M2.5", "MiniMax-M2.1-highspeed", "MiniMax-M2.1", "MiniMax-M2"},
    "deepseek": {"deepseek-chat", "deepseek-reasoner", "deepseek-v4-flash-vision-exp"},
}


# 模型名里出现这些片段就认为它能读图。只是启发式：真正能否读图以服务端为准，
# 所以只用于界面提示（打标/提醒），绝不据此拦截请求。
# 4v/5v/6v 是智谱的写法（glm-4v-flash、glm-4.6v、glm-5v-turbo），
# -vl/vl- 是通义与多数开源多模态的写法；纯文本模型名里不会出现这些片段。
_VISION_NAME_MARKERS = (
    "vision",
    "omni",
    "-vl",
    "vl-",
    "4v",
    "5v",
    "6v",
    "-v-",
    "v-preview",
)



# 已经包含完整接口路径的地址（用户从官方文档直接复制）保持原样。
_COMPLETE_CHAT_SUFFIXES = (
    "/chat/completions",
    "/chatcompletion_v2",
    "/chatcompletion",
)

# 地址末尾已经带了版本段（/v1、/v4、/compatible-mode/v1 …）时，只差接口路径。
_VERSION_SEGMENT = re.compile(r"/v\d+(?:/|$)")


def normalize_chat_endpoint(provider_id: str, value: str) -> str:
    """Accept a base URL or a complete endpoint; always return the full path.

    MiniMax and DeepSeek document a base URL (``https://api.minimax.cn/v1``)
    plus a separate chat path. Posting to the bare base returns a confusing
    gateway error, so a base URL is completed with the provider's chat path.

    各家版本段写法不同：OpenAI 系是 ``/v1``，智谱是 ``/api/paas/v4``，
    百炼是 ``/compatible-mode/v1``。所以「只填域名」时补的前缀取自预设
    （``api_prefix``），而不是一律拼 ``/v1``。
    """
    preset = PROVIDER_PRESETS.get(provider_id)
    endpoint = (value or "").strip().rstrip("/")
    if not endpoint:
        endpoint = (preset.endpoint if preset else "").rstrip("/")
    if not endpoint:
        return ""
    lowered = endpoint.lower()
    if any(lowered.endswith(suffix) for suffix in _COMPLETE_CHAT_SUFFIXES):
        return endpoint
    path = preset.chat_path if preset else ""
    if not path:
        return endpoint
    # 形如 https://域名/v1 或 https://域名/api/paas/v4 的基地址 → 直接接接口路径。
    if _VERSION_SEGMENT.search(lowered):
        return endpoint + path
    # 只给了域名 → 域名 + 服务商版本前缀 + 接口路径。
    prefix = (preset.api_prefix if preset else "") or "/v1"
    return endpoint + prefix + path


_MAX_USER_MODELS = 40


@dataclass
class ProviderConfig:
    """User overrides for one provider; empty strings fall back to presets."""

    api_key: str = ""
    model: str = ""
    endpoint: str = ""
    # 用户自己在模型菜单里增删的那份列表。为空表示「还没动过」，
    # 此时菜单显示预置候选；一旦增删过就以这份列表为准（见 model_choices）。
    models: List[str] = field(default_factory=list)

    def resolved_endpoint(self, preset: ProviderPreset) -> str:
        return normalize_chat_endpoint(preset.provider_id, self.endpoint or preset.endpoint)

    def resolved_model(self, preset: ProviderPreset) -> str:
        return self.model or preset.default_model

    def _catalog(self, preset: ProviderPreset) -> List[str]:
        """当前列表来源：用户动过就用用户的，否则用预置候选。"""
        source = self.models if self.models else list(preset.models)
        catalog: List[str] = []
        for candidate in source:
            name = str(candidate or "").strip()
            if name and name not in catalog:
                catalog.append(name)
        return catalog

    def model_choices(self, preset: ProviderPreset) -> List[str]:
        """当前可切换的模型：正在用的 + 列表里的（去重保序）。"""
        choices: List[str] = []
        for candidate in (self.resolved_model(preset),) + tuple(self._catalog(preset)):
            name = str(candidate or "").strip()
            if name and name not in choices:
                choices.append(name)
        return choices

    def uses_preset_models(self, preset: ProviderPreset) -> bool:
        """列表还是预置的、没被用户改过。"""
        return not self.models

    def add_model(self, preset: ProviderPreset, name: str) -> bool:
        """把模型加进用户列表；返回是否真的新增。"""
        value = validate_model(name)
        catalog = self._catalog(preset)
        if value in catalog:
            return False
        if len(catalog) >= _MAX_USER_MODELS:
            raise AiConfigError(f"模型最多保留 {_MAX_USER_MODELS} 个，请先删掉不用的。")
        catalog.append(value)
        self.models = catalog
        return True

    def remove_model(self, preset: ProviderPreset, name: str) -> bool:
        """从用户列表里删掉一个模型。

        用户没动过列表时先按预置候选播种再删，否则「预置项删不掉」。
        """
        value = str(name or "").strip()
        if not value:
            return False
        catalog = self._catalog(preset)
        if value not in catalog:
            return False
        catalog.remove(value)
        self.models = catalog
        return True

    def model_is_vision(self, preset: ProviderPreset) -> bool:
        return model_supports_vision(preset.provider_id, self.resolved_model(preset))



@dataclass
class AiSettings:
    active_provider: str = DEFAULT_PROVIDER
    temperature: float = DEFAULT_TEMPERATURE
    providers: Dict[str, ProviderConfig] = field(default_factory=dict)

    def preset(self, provider_id: Optional[str] = None) -> ProviderPreset:
        key = provider_id or self.active_provider
        preset = PROVIDER_PRESETS.get(key)
        if preset is None:
            raise AiConfigError(f"未知的 AI 服务商：{key}")
        return preset

    def provider_config(self, provider_id: Optional[str] = None) -> ProviderConfig:
        key = provider_id or self.active_provider
        self.preset(key)  # validates the id first
        return self.providers.setdefault(key, ProviderConfig())

    def is_ready(self, provider_id: Optional[str] = None) -> bool:
        try:
            config = self.provider_config(provider_id)
        except AiConfigError:
            return False
        return bool(normalize_api_key(config.api_key))

    def problems(self) -> List[str]:
        """Return human-readable blocking issues for the active provider."""
        issues: List[str] = []
        try:
            config = self.provider_config()
        except AiConfigError as exc:
            return [str(exc)]
        if not normalize_api_key(config.api_key):
            issues.append(
                f"尚未配置 {self.preset().label} 的 API Key，请先在设置中填写。"
            )
        try:
            validate_model(config.resolved_model(self.preset()))
            validate_endpoint(config.resolved_endpoint(self.preset()))
        except AiConfigError as exc:
            issues.append(str(exc))
        return issues


def model_supports_vision(provider_id: str, model: str) -> bool:
    """启发式判断某个模型能否读图。

    预置的 ``vision_models`` 优先；其次看模型名里的常见视觉标记。
    只用于界面提示——请求照发，能否读图最终以服务端返回为准，
    这样万一标记过时也不会把可用模型拦下来。
    """
    name = str(model or "").strip()
    if not name:
        return False
    preset = PROVIDER_PRESETS.get(str(provider_id or ""))
    if preset is not None and name in tuple(preset.vision_models):
        return True
    lowered = name.lower()
    return any(marker in lowered for marker in _VISION_NAME_MARKERS)


def vision_model_choices(preset: Optional[ProviderPreset]) -> List[str]:
    """该服务商的视觉模型候选（去重保序）。"""
    if preset is None:
        return []
    choices: List[str] = []
    for candidate in tuple(preset.vision_models):
        name = str(candidate or "").strip()
        if name and name not in choices:
            choices.append(name)
    return choices


def normalize_api_key(value: Any) -> str:
    """Trim and validate an API key without restricting its character set."""
    if not isinstance(value, str):
        return ""
    key = value.strip()
    if not key:
        return ""
    if len(key) > _MAX_API_KEY_LENGTH or _CONTROL_CHARACTER.search(key):
        raise AiConfigError("API Key 格式不正确，请重新复制。")
    return key


def redact_api_key(value: str) -> str:
    """Mask a key for safe display and logging."""
    key = (value or "").strip()
    if len(key) <= 8:
        return "***"
    return key[:3] + "***" + key[-4:]


def validate_model(value: str) -> str:
    model = (value or "").strip()
    if not model:
        raise AiConfigError("模型名称不能为空。")
    if len(model) > _MAX_MODEL_LENGTH or _CONTROL_CHARACTER.search(model):
        raise AiConfigError("模型名称不合法。")
    return model


def validate_endpoint(value: str) -> str:
    endpoint = (value or "").strip()
    if not endpoint.startswith(("https://", "http://")):
        raise AiConfigError("服务地址必须以 http:// 或 https:// 开头。")
    if len(endpoint) > _MAX_ENDPOINT_LENGTH or _CONTROL_CHARACTER.search(endpoint):
        raise AiConfigError("服务地址不合法。")
    return endpoint


def default_settings_path() -> Path:
    return user_app_data_dir("config") / "HRToolkit" / SETTINGS_FILENAME


def load_ai_settings(path: Optional[Path] = None) -> AiSettings:
    """Load settings; missing or corrupted files fall back to defaults."""
    target = Path(path) if path is not None else default_settings_path()
    try:
        raw = json.loads(target.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return AiSettings()
    except (OSError, ValueError):
        return AiSettings()
    if not isinstance(raw, dict):
        return AiSettings()

    settings = AiSettings()
    active = str(raw.get("activeProvider") or DEFAULT_PROVIDER).strip()
    if active in PROVIDER_PRESETS:
        settings.active_provider = active
    try:
        temperature = float(raw.get("temperature", DEFAULT_TEMPERATURE))
    except (TypeError, ValueError):
        temperature = DEFAULT_TEMPERATURE
    settings.temperature = min(max(temperature, 0.0), 2.0)

    providers_raw = raw.get("providers")
    if isinstance(providers_raw, dict):
        for provider_id in PROVIDER_PRESETS:
            entry = providers_raw.get(provider_id)
            if not isinstance(entry, dict):
                continue
            config = ProviderConfig()
            try:
                config.api_key = normalize_api_key(entry.get("apiKey"))
                model = str(entry.get("model") or "").strip()
                if model:
                    config.model = validate_model(model)
                endpoint = str(entry.get("endpoint") or "").strip()
                if endpoint:
                    config.endpoint = validate_endpoint(endpoint)
                    # Earlier settings dialogs saved the old preset as an
                    # explicit override. Let those installations adopt the
                    # corrected default without changing other custom URLs.
                    if provider_id == "qwen" and normalize_chat_endpoint(provider_id, config.endpoint) == (
                        "https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions"
                    ):
                        config.endpoint = ""
                models = entry.get("models")
                if isinstance(models, list):
                    seen: List[str] = []
                    for item in models:
                        name = str(item or "").strip()
                        if not name or name in seen:
                            continue
                        try:
                            seen.append(validate_model(name))
                        except AiConfigError:
                            # 单个坏名字不能连累整条 provider 配置（API Key 得留住）。
                            continue
                    config.models = seen[: _MAX_USER_MODELS]
            except AiConfigError:
                # Drop invalid fragments instead of failing the whole file.
                continue
            removed = _REMOVED_MENU_MODELS.get(provider_id, set())
            config.models = [name for name in config.models if name not in removed]
            if config.model in removed:
                config.model = ""
            if provider_id == "deepseek" and config.models == ["deepseek-flash", "deepseek-v4-pro"]:
                config.models = []
            settings.providers[provider_id] = config
    return settings


def save_ai_settings(settings: AiSettings, path: Optional[Path] = None) -> Path:
    """Atomically persist settings and return the written path."""
    target = Path(path) if path is not None else default_settings_path()
    providers_payload: Dict[str, Any] = {}
    for provider_id, config in settings.providers.items():
        if provider_id not in PROVIDER_PRESETS:
            continue
        providers_payload[provider_id] = {
            "apiKey": config.api_key,
            "model": config.model,
            "endpoint": config.endpoint,
            "models": list(config.models),
        }
    payload = {
        "activeProvider": settings.active_provider,
        "temperature": settings.temperature,
        "providers": providers_payload,
    }
    target.parent.mkdir(parents=True, exist_ok=True)
    handle = tempfile.NamedTemporaryFile(
        "w", encoding="utf-8", dir=str(target.parent), prefix=".ai-assistant-", delete=False
    )
    try:
        with handle:
            json.dump(payload, handle, ensure_ascii=False, indent=2)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(handle.name, target)
    except BaseException:
        try:
            os.unlink(handle.name)
        except OSError:
            pass
        raise
    return target
