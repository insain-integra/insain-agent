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


def test_dashboard_render_ignores_today_and_git(monkeypatch):
    dash = _load("dashboard")
    base = dash.render()

    class FutureDate(dash.date):
        @classmethod
        def today(cls):
            return cls(2099, 1, 1)

    def no_git(*args, **kwargs):
        raise AssertionError("дашборд не должен вызывать git: в CI клон с fetch-depth 1")

    monkeypatch.setattr(dash, "date", FutureDate)
    monkeypatch.setattr("subprocess.check_output", no_git)
    monkeypatch.setattr("subprocess.run", no_git)
    assert dash.render() == base, "render() зависит от текущей даты"


def test_active_time_halves_long_turns():
    from datetime import datetime, timedelta

    close = _load("close_task")
    t0 = datetime(2026, 11, 5, 10, 0)
    minutes = [0, 10, 25, 57, 57 + 2 * 24 * 60]
    stamps = [t0 + timedelta(minutes=n) for n in minutes]
    # 10 и 15 — целиком; 32 мин — 0.5 × 32 = 16; два дня — не больше 30
    assert close.active_time(stamps) == timedelta(minutes=10 + 15 + 16 + 30)
    assert close.active_time([t0]) == timedelta()


def test_active_time_counts_last_turn_to_chat_end():
    """Чат с одним промптом: ход до конца чата, а не ноль."""
    from datetime import datetime, timedelta

    close = _load("close_task")
    t0 = datetime(2026, 11, 8, 2, 15)
    assert close.active_time([t0], t0 + timedelta(minutes=9)) == timedelta(minutes=9)
    assert close.active_time([t0], t0 + timedelta(hours=3)) == timedelta(minutes=30)
    assert close.active_time([t0], t0 - timedelta(minutes=5)) == timedelta()


def test_chat_period_uses_chat_dates_not_task_file():
    from datetime import datetime

    close = _load("close_task")
    stamps = [datetime(2026, 11, 7, 19, 11), datetime(2026, 11, 7, 20, 5)]
    assert close.chat_period(stamps) == "2026-11-07 — 2026-11-07 (1 дн.)"
    assert close.chat_period([]) == ""


def test_close_marks_links_to_closed_task(tmp_path, monkeypatch):
    close = _load("close_task")
    todo = tmp_path / "todo"
    todo.mkdir()
    epic = todo / "EPIC-x.md"
    epic.write_text("- `todo/form-a.md` — копия\n1. Довести todo/form-a.md\n- `todo/form-ab.md`\n", encoding="utf-8")
    monkeypatch.setattr(close, "TODO", todo)
    assert close._mark_closed_links("form-a.md", "2026-11-07") == ["EPIC-x.md"]
    text = epic.read_text(encoding="utf-8")
    assert "todo/form-a.md" not in text
    assert text.count("`form-a` (закрыто 2026-11-07") == 2
    assert "`todo/form-ab.md`" in text


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
