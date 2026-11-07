"""Дашборд совпадает со скриптом; close отказывается без «Было / стало»."""

from __future__ import annotations

import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / "scripts"


def _load(name: str):
    path = SCRIPTS / f"{name}.py"
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_dashboard_file_matches_render():
    dash = _load("dashboard")
    path = ROOT / "docs" / "dashboard.md"
    assert path.is_file(), "нет docs/dashboard.md — python scripts/dev.py dashboard"
    got = path.read_text(encoding="utf-8").replace("\r\n", "\n")
    exp = dash.render().replace("\r\n", "\n")
    assert got == exp, "docs/dashboard.md устарел: python scripts/dev.py dashboard"


def test_close_requires_result(tmp_path, monkeypatch):
    close = _load("close_task")
    todo = tmp_path / "todo"
    todo.mkdir()
    (todo / "empty.md").write_text(
        "# empty\n\nСтатус: ревью\n\n## Журнал передач\n\n- 07.11.2026 — Implementer, Grok — сдано\n\n## Результат\n\n- Было / стало:\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(close, "TODO", todo)
    monkeypatch.setattr(close, "ROOT", tmp_path)
    try:
        close.close("empty")
    except SystemExit as exc:
        assert "Было / стало" in str(exc)
    else:
        raise AssertionError("close должен отказаться без «Было / стало»")
