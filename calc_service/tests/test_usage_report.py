"""Сводка расхода ИИ-агентов по CSV Usage из Cursor: семейства моделей, кэш, запись в usage.md."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / "scripts"

CSV = (
    '"Date","Kind","Model","Max Mode","Input (w/ Cache Write)","Input (w/o Cache Write)",'
    '"Cache Read","Output Tokens","Total Tokens","Cost"\n'
    '"2026-11-02T10:00:00.000Z","Included","claude-opus-5-5-thinking","No","1000","0","8000","1000","10000","0.60"\n'
    '"2026-11-03T10:00:00.000Z","Included","grok-4.7-high-fast","No","0","2000","27000","1000","30000","0.00"\n'
    '"2026-11-08T10:00:00.000Z","Included","auto","No","0","1000","8000","1000","10000","Included"\n'
)


def _load():
    spec = importlib.util.spec_from_file_location("usage_report", SCRIPTS / "usage_report.py")
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    sys.modules["usage_report"] = mod
    spec.loader.exec_module(mod)
    return mod


def test_family_by_model_name():
    u = _load()
    assert u.family("claude-opus-5-5-thinking") == "Opus"
    assert u.family("grok-4.7-high-fast") == "Grok"
    assert u.family("auto") == "Auto"
    assert u.family("gpt-5.5") == "Прочие"


def test_parse_shares_and_cache(tmp_path):
    u = _load()
    p = tmp_path / "usage.csv"
    p.write_text(CSV, encoding="utf-8")
    rep = u.parse(p)
    assert (rep.first, rep.last) == ("2026-11-02", "2026-11-08")
    assert rep.total.requests == 3
    assert rep.by_family["Opus"].cost == 0.6
    assert rep.by_family["Auto"].cost == 0.0
    line = u.row(rep)
    assert line.startswith("| 2026-11-02 — 2026-11-08 | 3 | 0.1 | 0.60 |")
    assert "20% ток. / 100% $" in line
    assert "60% ток. / 0% $" in line
    # вход 1000+0+2000+1000 и кэш 8000+27000+8000 → 43000 / 47000
    assert line.endswith("| 91% |")


def test_write_replaces_same_period(tmp_path):
    u = _load()
    p = tmp_path / "usage.csv"
    p.write_text(CSV, encoding="utf-8")
    md = tmp_path / "usage.md"
    md.write_text("# Расход\n\n" + u.HEADER + "\n", encoding="utf-8")
    rep = u.parse(p)
    u.write(rep, md)
    u.write(rep, md)
    text = md.read_text(encoding="utf-8")
    assert text.count("| 2026-11-02 — 2026-11-08 |") == 1


def test_usage_md_has_table():
    u = _load()
    assert u.HEADER in (ROOT / "docs" / "history" / "usage.md").read_text(encoding="utf-8")
