"""Command-line demo for the AI assistant backend (M1 milestone).

Streams a comparison analysis of two or more Excel tables through the
configured OpenAI-compatible provider (DeepSeek / MiniMax). The API key is
read from ``--api-key`` or the ``HR_TOOLKIT_AI_KEY`` environment variable and
is never written to disk by this script.

Example:
    python scripts/ai_assistant_demo.py 表1.xlsx 表2.xlsx \
        --question "这两张表有什么区别，谁的增长值更好？" \
        --provider deepseek --api-key sk-xxx
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from hr_toolkit.ai.client import (
    ChatError,
    provider_credentials,
    provider_extra,
    stream_chat,
)
from hr_toolkit.ai.config import (
    PROVIDER_PRESETS,
    AiSettings,
    load_ai_settings,
    normalize_api_key,
)
from hr_toolkit.ai.excel_context import (
    build_workbook_context,
    estimate_tokens,
    render_analysis_context,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="AI 助手后端演示：多表对比分析")
    parser.add_argument("tables", nargs="+", help="要对比的 Excel 文件（.xlsx/.xls），至少一个")
    parser.add_argument("-q", "--question", default="这些表之间有什么区别和联系？请分析。")
    parser.add_argument(
        "--provider",
        choices=sorted(PROVIDER_PRESETS),
        default=None,
        help="服务商（默认读取设置文件，否则 deepseek）",
    )
    parser.add_argument("--api-key", default=None, help="API Key（或用环境变量 HR_TOOLKIT_AI_KEY）")
    parser.add_argument("--model", default=None, help="覆盖默认模型名")
    parser.add_argument("--endpoint", default=None, help="覆盖服务地址")
    parser.add_argument("--temperature", type=float, default=0.3)
    return parser


def main(argv=None) -> int:
    args = build_parser().parse_args(argv)
    settings = load_ai_settings()
    provider_id = args.provider or settings.active_provider
    if provider_id not in PROVIDER_PRESETS:
        print(f"未知服务商：{provider_id}", file=sys.stderr)
        return 2

    config = settings.provider_config(provider_id)
    preset = PROVIDER_PRESETS[provider_id]
    api_key = normalize_api_key(args.api_key) if args.api_key else config.api_key
    if not api_key:
        import os

        api_key = normalize_api_key(os.environ.get("HR_TOOLKIT_AI_KEY", ""))
    if not api_key:
        print(
            f"未配置 {preset.label} 的 API Key：请使用 --api-key 或设置环境变量 HR_TOOLKIT_AI_KEY。",
            file=sys.stderr,
        )
        return 2
    endpoint = args.endpoint or config.resolved_endpoint(preset)
    model = args.model or config.resolved_model(preset)

    contexts = []
    for raw_path in args.tables:
        path = Path(raw_path).expanduser()
        print(f"解析：{path.name} …", file=sys.stderr)
        contexts.append(build_workbook_context(path))
    prompt = render_analysis_context(contexts, args.question)
    print(f"上下文约 {estimate_tokens(prompt)} tokens，开始分析。", file=sys.stderr)

    try:
        for delta in stream_chat(
            [
                {
                    "role": "system",
                    "content": "你是人事数据分析助手，用简体中文回答，结论明确、数字准确。",
                },
                {"role": "user", "content": prompt},
            ],
            endpoint=endpoint,
            api_key=api_key,
            model=model,
            temperature=args.temperature,
            extra=provider_extra(preset.provider_id),
        ):
            sys.stdout.write(delta)
            sys.stdout.flush()
    except ChatError as exc:
        print(f"\n分析失败：{exc}", file=sys.stderr)
        return 1
    print()
    return 0


if __name__ == "__main__":
    sys.exit(main())
