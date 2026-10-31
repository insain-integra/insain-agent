"""
Ратчет пропусков порта JS: scripts/js_port_gaps_allowed.txt только уменьшается.

Устранили пропуск — удалите строку из файла и уменьшите MAX_ALLOWED в том же коммите.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts" / "js_port_gaps.py"
ALLOWED = ROOT / "scripts" / "js_port_gaps_allowed.txt"

MAX_ALLOWED = 78


def _allowed_lines() -> list[str]:
    return [s for s in ALLOWED.read_text(encoding="utf-8").splitlines() if s.strip()]


def _run(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(SCRIPT), *args],
        capture_output=True,
        text=True,
        encoding="utf-8",
        cwd=ROOT,
    )


def test_allowed_file_only_shrinks():
    lines = _allowed_lines()
    assert len(lines) <= MAX_ALLOWED, (
        f"В {ALLOWED.name} {len(lines)} строк, больше MAX_ALLOWED={MAX_ALLOWED}: "
        "новые пропуски порта не добавляются, их переносят в Python"
    )
    assert len(lines) == len(set(lines)), "в файле пропусков есть повторы"


def test_check_ok_on_repo():
    r = _run("--check")
    assert r.returncode == 0, r.stdout + r.stderr
    assert r.stdout.strip() == "ok"


def test_check_fails_on_new_gap(tmp_path):
    lines = _allowed_lines()
    p = tmp_path / "allowed.txt"
    p.write_text("\n".join(lines[1:]) + "\n", encoding="utf-8")
    r = _run("--check", "--allowed", str(p))
    assert r.returncode == 1
    assert f"новый пропуск: {lines[0]}" in r.stdout


def test_check_fails_on_fixed_gap(tmp_path):
    p = tmp_path / "allowed.txt"
    p.write_text("\n".join(_allowed_lines() + ["calcFoo option isBar"]) + "\n", encoding="utf-8")
    r = _run("--check", "--allowed", str(p))
    assert r.returncode == 1
    assert "пропуск устранён, удалите строку: calcFoo option isBar" in r.stdout


def test_report_follows_call_chain():
    r = _run("calcPlaque")
    assert r.returncode == 0, r.stdout + r.stderr
    assert "calcPlaque ->" in r.stdout
    blocks = {b.splitlines()[0].split(" ->")[0]: b for b in r.stdout.strip().split("\n\n")}
    assert "calcTablets" in blocks
    missing = [s for s in blocks["calcTablets"].splitlines() if s.startswith("нет в Python:")]
    assert missing and "isSublimation" in missing[0]
