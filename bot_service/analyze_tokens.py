"""
Утилита для анализа логов расхода токенов.

Использование:
    python analyze_tokens.py logs/token_usage.jsonl
    python analyze_tokens.py logs/token_usage.jsonl --top 10
    python analyze_tokens.py logs/token_usage.jsonl --component tools
"""

from __future__ import annotations

import argparse
from typing import Optional

from token_analyzer import TokenUsageStats


def main(argv: Optional[list[str]] = None) -> None:
    parser = argparse.ArgumentParser(description="Анализ логов расхода токенов LLM.")
    parser.add_argument("logfile", help="Путь к JSONL-файлу с логами")
    parser.add_argument(
        "--top",
        type=int,
        help="Показать N самых дорогих запросов",
    )
    parser.add_argument(
        "--component",
        help="Разбивка по компоненту: system|history|tools|user",
    )

    args = parser.parse_args(argv)

    stats = TokenUsageStats()
    stats.load_from_file(args.logfile)

    if args.top:
        stats.print_top_expensive(args.top)
    elif args.component:
        stats.print_component_breakdown(args.component)
    else:
        stats.print_report()


if __name__ == "__main__":
    main()

