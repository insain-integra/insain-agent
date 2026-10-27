"""Ротация logs/token_usage.jsonl: предел размера и один архивный файл."""

from __future__ import annotations

import json
import sys
from pathlib import Path

_bot_service = Path(__file__).resolve().parent.parent
if str(_bot_service) not in sys.path:
    sys.path.insert(0, str(_bot_service))

from token_analyzer import TokenAnalyzer


def _entry(marker: str) -> dict:
    return {"timestamp": "2026-10-25T00:00:00", "marker": marker}


def test_rotates_to_single_archive_when_size_reached(tmp_path: Path) -> None:
    log_path = tmp_path / "token_usage.jsonl"
    analyzer = TokenAnalyzer(log_path=log_path, max_log_bytes=40)

    analyzer.save_to_file(_entry("first"))
    assert log_path.is_file()
    assert not log_path.with_name("token_usage.jsonl.1").exists()

    first_text = log_path.read_text(encoding="utf-8")
    assert log_path.stat().st_size >= analyzer.max_log_bytes

    analyzer.save_to_file(_entry("second"))
    archive = log_path.with_name("token_usage.jsonl.1")
    assert archive.read_text(encoding="utf-8") == first_text
    active = [json.loads(line) for line in log_path.read_text(encoding="utf-8").splitlines()]
    assert [row["marker"] for row in active] == ["second"]

    analyzer.save_to_file(_entry("third"))
    archived = [json.loads(line) for line in archive.read_text(encoding="utf-8").splitlines()]
    assert [row["marker"] for row in archived] == ["second"]
    active = [json.loads(line) for line in log_path.read_text(encoding="utf-8").splitlines()]
    assert [row["marker"] for row in active] == ["third"]
    assert sorted(tmp_path.glob("token_usage.jsonl*")) == sorted([log_path, archive])


def test_default_log_limit_is_eight_mebibytes() -> None:
    assert TokenAnalyzer.DEFAULT_MAX_LOG_BYTES == 8 * 1024 * 1024
