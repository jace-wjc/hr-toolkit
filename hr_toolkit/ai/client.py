"""OpenAI-compatible streaming chat client on the standard library.

Works with any Chat Completions endpoint (DeepSeek, MiniMax and compatible
services). Python 3.8 compatible: no third-party network dependency, TLS uses
``certifi`` when available exactly like the self-updater.
"""

from __future__ import annotations

import json
import ssl
import urllib.error
import urllib.request
from typing import Any, Dict, Iterator, List, Optional, Sequence

from .config import (
    AiSettings,
    normalize_api_key,
    validate_endpoint,
    validate_model,
)

DEFAULT_TIMEOUT_SECONDS = 120.0
CONNECTIVITY_TIMEOUT_SECONDS = 30.0


class ChatError(RuntimeError):
    """User-facing failure with an actionable Chinese message."""


def _ssl_context():
    try:
        import certifi

        return ssl.create_default_context(cafile=certifi.where())
    except Exception:  # pragma: no cover - only hit without certifi
        return ssl.create_default_context()


def build_payload(
    messages: Sequence[Dict[str, Any]],
    *,
    model: str,
    temperature: float = 0.3,
    stream: bool = False,
    extra: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Build the request body shared by streaming and one-shot calls.

    ``content`` may be a plain string or a list of multimodal parts
    (``{"type": "text"}`` / ``{"type": "image_url"}``); the list form must be
    passed through untouched or the images are silently dropped.

    ``extra`` carries provider-specific switches that must not leak to other
    providers (MiniMax's ``reasoning_split``, for example).
    """
    normalized: List[Dict[str, Any]] = []
    for message in messages:
        role = str(message.get("role") or "user").strip() or "user"
        raw = message.get("content")
        content: Any
        if isinstance(raw, list):
            parts: List[Dict[str, Any]] = []
            for part in raw:
                if isinstance(part, dict) and part.get("type"):
                    parts.append(part)
            content = parts if parts else ""
        else:
            content = str(raw or "")
        normalized.append({"role": role, "content": content})
    payload: Dict[str, Any] = {
        "model": model,
        "messages": normalized,
        "temperature": max(0.0, min(float(temperature), 2.0)),
        "stream": bool(stream),
    }
    for key, value in (extra or {}).items():
        if key in ("model", "messages", "stream"):
            continue
        payload[key] = value
    return payload


def _http_error_message(exc: urllib.error.HTTPError) -> str:
    status = exc.code
    detail = ""
    try:
        body = exc.read().decode("utf-8", "replace")
        try:
            data = json.loads(body)
            error = data.get("error")
            if isinstance(error, dict):
                detail = str(error.get("message") or "").strip()
            elif isinstance(error, str):
                detail = error.strip()
            base_resp = data.get("base_resp")
            if not detail and isinstance(base_resp, dict):
                detail = str(base_resp.get("status_msg") or "").strip()
        except ValueError:
            detail = body.strip()[:200]
    except Exception:
        detail = ""
    hint = {
        401: "API Key 无效或未授权，请检查设置。",
        402: "服务余额不足，请充值后重试。",
        403: "当前 Key 无权访问该模型或接口。",
        404: "服务地址或模型名称不存在，请检查设置。",
        429: "请求过于频繁或额度受限，请稍后重试。",
    }.get(status, "请稍后重试或联系管理员。")
    message = f"AI 服务返回错误（HTTP {status}）：{hint}"
    if detail:
        message += f"（{detail}）"
    return message


def _open_response(
    endpoint: str,
    payload: Dict[str, Any],
    api_key: str,
    timeout: float,
    opener,
):
    request = urllib.request.Request(
        endpoint,
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        headers={
            "Authorization": "Bearer " + api_key,
            "Content-Type": "application/json",
            "Accept": "application/json" if not payload.get("stream") else "text/event-stream",
        },
        method="POST",
    )
    try:
        return opener(request, timeout=timeout, context=_ssl_context())
    except urllib.error.HTTPError as exc:
        raise ChatError(_http_error_message(exc)) from exc
    except (urllib.error.URLError, ssl.SSLError, OSError, ValueError) as exc:
        reason = getattr(exc, "reason", None) or exc
        raise ChatError(f"无法连接 AI 服务，请检查网络：{reason}") from exc


def iter_sse_data_lines(response) -> Iterator[str]:
    """Yield decoded ``data:`` payloads from an SSE response stream."""
    for raw_line in response:
        if isinstance(raw_line, bytes):
            line = raw_line.decode("utf-8", "replace")
        else:
            line = str(raw_line)
        line = line.strip()
        if not line or line.startswith(":"):
            continue
        if not line.startswith("data:"):
            continue
        yield line[len("data:"):].strip()


def friendly_service_error(message: str) -> str:
    """Attach an actionable hint to provider error text."""
    text = str(message or "").strip()
    lowered = text.lower()
    if "login fail" in lowered or "authorization" in lowered:
        text += (
            "（请确认服务地址填的是完整接口路径，例如 "
            "https://api.minimax.cn/v1/chat/completions；"
            "只填 https://api.minimax.cn/v1 会被自动补全，若仍报错请检查 API Key 是否完整）"
        )
    elif any(
        token in lowered
        for token in ("image", "vision", "multimodal", "multi-modal", "图片", "图像")
    ) and any(
        token in lowered
        for token in ("not support", "unsupported", "invalid", "unknown", "cannot", "不支持", "无法")
    ):
        # 当前模型不吃图片：换成视觉模型才行，光重试没用。
        text += (
            "（当前模型不支持读图。请在对话框左下角的模型菜单里切换到带 VL／Vision "
            "字样的视觉模型，再到设置里确认该模型已开通）"
        )
    elif "model" in lowered and any(
        token in lowered for token in ("not found", "not exist", "invalid", "unsupported")
    ):
        text += "（请核对模型名称与控制台开通的模型是否一致）"
    elif any(token in lowered for token in ("insufficient", "balance", "quota", "arrears")):
        text += "（账户余额或调用额度不足，请充值后重试）"
    return text


def _chunk_error(chunk: Dict[str, Any]) -> str:
    error = chunk.get("error")
    if isinstance(error, dict):
        message = str(error.get("message") or "").strip()
        if message:
            return friendly_service_error(message)
    elif isinstance(error, str) and error.strip():
        return friendly_service_error(error.strip())
    base_resp = chunk.get("base_resp")  # MiniMax error envelope
    if isinstance(base_resp, dict):
        status_code = base_resp.get("status_code")
        if isinstance(status_code, int) and status_code != 0:
            return friendly_service_error(
                str(base_resp.get("status_msg") or f"服务返回错误码 {status_code}")
            )
    return ""


def _extract_stream_delta(chunk: Dict[str, Any]) -> str:
    """Return only the incremental delta text.

    MiniMax's final SSE chunk may also carry a complete ``message`` object;
    reading it here would duplicate the whole reply, so streaming only ever
    consumes ``delta``.
    """
    choices = chunk.get("choices")
    if not isinstance(choices, list) or not choices:
        return ""
    delta = choices[0].get("delta")
    if isinstance(delta, dict):
        content = delta.get("content")
        if isinstance(content, str):
            return content
    return ""


def _looks_like_model_problem(model: str) -> str:
    return (
        f"（当前模型「{model}」可能不存在、未开通，或该服务商不认这个叫法。"
        "请在对话框左下角的模型菜单里换一个，或到设置里核对模型名称与控制台是否一致）"
    )


def provider_extra(provider_id: str) -> Dict[str, Any]:
    """Provider-only request switches.

    MiniMax 的 M 系列都会「思考」，且关不掉；不加 ``reasoning_split`` 时思考内容
    会以 ``<think>…</think>`` 直接混在 ``content`` 里，用户看到的就是一屏推理。
    打开后思考走 ``reasoning_content``/``reasoning_details``，我们只取 ``content``，
    既保留模型质量又只显示答案。
    """
    if str(provider_id or "") == "minimax":
        return {"reasoning_split": True}
    return {}


def stream_chat(
    messages: Sequence[Dict[str, Any]],
    *,
    endpoint: str,
    api_key: str,
    model: str,
    temperature: float = 0.3,
    timeout: float = DEFAULT_TIMEOUT_SECONDS,
    opener=None,
    extra: Optional[Dict[str, Any]] = None,
) -> Iterator[str]:
    """Stream assistant replies as text deltas.

    ``opener`` is injectable for tests; production code uses
    :func:`urllib.request.urlopen`.

    模型名写错时服务端常常照样回 200，正文却不是流式片段（或者一个字符都没有）；
    这种情况以前会静默留下一个空气泡，用户只看到「结果无效」。这里两种都翻成明确的
    :class:`ChatError`，并把首个原始片段截断带上，方便判断到底返回了什么。
    """
    if not api_key:
        raise ChatError("尚未配置 API Key。")
    payload = build_payload(
        messages, model=model, temperature=temperature, stream=True, extra=extra
    )
    open_url = opener or urllib.request.urlopen
    response = _open_response(endpoint, payload, api_key, timeout, open_url)
    saw_chunk = False
    saw_content = False
    first_line = ""
    try:
        with response:
            for data in iter_sse_data_lines(response):
                if data == "[DONE]":
                    break
                try:
                    chunk = json.loads(data)
                except ValueError:
                    if not first_line:
                        first_line = data[:200]
                    continue
                if not isinstance(chunk, dict):
                    continue
                saw_chunk = True
                error = _chunk_error(chunk)
                if error:
                    raise ChatError(f"AI 服务返回错误：{error}")
                delta = _extract_stream_delta(chunk)
                if delta:
                    saw_content = True
                    yield delta
    except ChatError:
        raise
    except (OSError, ValueError, ssl.SSLError) as exc:
        raise ChatError(f"读取 AI 回复时中断：{exc}") from exc
    if not saw_content:
        if not saw_chunk:
            detail = f"首个片段：{first_line}" if first_line else "响应是空的"
            raise ChatError(
                f"AI 服务没有返回流式内容（{detail}）。"
                f"请确认服务地址是 OpenAI 兼容接口，例如 https://api.minimax.cn/v1/chat/completions"
                + _looks_like_model_problem(model)
            )
        raise ChatError("AI 服务返回了空回复。" + _looks_like_model_problem(model))



def chat_once(
    messages: Sequence[Dict[str, Any]],
    *,
    endpoint: str,
    api_key: str,
    model: str,
    temperature: float = 0.3,
    timeout: float = DEFAULT_TIMEOUT_SECONDS,
    opener=None,
    extra: Optional[Dict[str, Any]] = None,
) -> str:
    """Non-streaming call used for connectivity checks and simple queries."""
    if not api_key:
        raise ChatError("尚未配置 API Key。")
    payload = build_payload(
        messages, model=model, temperature=temperature, stream=False, extra=extra
    )
    open_url = opener or urllib.request.urlopen
    response = _open_response(endpoint, payload, api_key, timeout, open_url)
    try:
        with response:
            body = response.read()
    except (OSError, ssl.SSLError) as exc:
        raise ChatError(f"读取 AI 回复时中断：{exc}") from exc
    try:
        data = json.loads(body.decode("utf-8", "replace"))
    except ValueError as exc:
        raise ChatError("AI 服务返回了无法解析的内容。") from exc
    error = _chunk_error(data)
    if error:
        raise ChatError(f"AI 服务返回错误：{error}")
    choices = data.get("choices")
    if not isinstance(choices, list) or not choices:
        raise ChatError("AI 服务未返回任何回复。" + _looks_like_model_problem(model))
    message = choices[0].get("message")
    if not isinstance(message, dict) or not isinstance(message.get("content"), str):
        raise ChatError("AI 服务未返回有效回复。" + _looks_like_model_problem(model))
    content = message["content"].strip()
    if not content:
        raise ChatError("AI 服务返回了空回复。" + _looks_like_model_problem(model))
    return content


def provider_credentials(
    settings: AiSettings, provider_id: Optional[str] = None
):
    """Resolve ``(endpoint, api_key, model)`` for a settings profile."""
    preset = settings.preset(provider_id)
    config = settings.provider_config(preset.provider_id)
    endpoint = validate_endpoint(config.resolved_endpoint(preset))
    model = validate_model(config.resolved_model(preset))
    api_key = normalize_api_key(config.api_key)
    return endpoint, api_key, model


def test_connection(
    settings: AiSettings,
    provider_id: Optional[str] = None,
    opener=None,
) -> str:
    """Send a minimal ping; return the reply or raise :class:`ChatError`."""
    endpoint, api_key, model = provider_credentials(settings, provider_id)
    reply = chat_once(
        [{"role": "user", "content": "请回复：连接正常"}],
        endpoint=endpoint,
        api_key=api_key,
        model=model,
        temperature=0.0,
        timeout=CONNECTIVITY_TIMEOUT_SECONDS,
        opener=opener,
        extra=provider_extra(settings.active_provider if provider_id is None else provider_id),
    )
    return reply
