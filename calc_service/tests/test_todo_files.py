"""Шапка файлов todo/: статус из списка docs/agents/workflow.md, «Статусы»."""

from __future__ import annotations

import re
from pathlib import Path

TODO = Path(__file__).resolve().parents[2] / "todo"

STATUS_RE = re.compile(
    r"^Статус: (?:черновик|в работе|ревью|доработка|выкатка|закрытие|готово"
    r"|заблокировано: (?:аналитик|исполнитель|ревьюер|site ops|человек|ждёт todo/[\w.-]+\.md))$"
)


def _task_files() -> list[Path]:
    return sorted(p for p in TODO.glob("*.md") if p.name != "AGENTS.md")


def test_todo_status_from_workflow_list():
    files = _task_files()
    assert files, f"нет задач в {TODO}"
    bad = []
    for path in files:
        lines = [ln for ln in path.read_text(encoding="utf-8").splitlines() if ln.startswith("Статус:")]
        if len(lines) != 1:
            bad.append(f"{path.name}: строк «Статус:» — {len(lines)}, нужна одна")
        elif not STATUS_RE.match(lines[0]):
            bad.append(f"{path.name}: «{lines[0]}» — нет в docs/agents/workflow.md, «Статусы»")
    assert not bad, "\n".join(bad)


def test_waiting_status_points_to_open_task():
    """Ожидаемая задача закрыта и удалена — статус «ждёт» надо снять."""
    bad = []
    for path in _task_files():
        m = re.search(r"^Статус: заблокировано: ждёт todo/([\w.-]+\.md)$", path.read_text(encoding="utf-8"), re.M)
        if m and not (TODO / m.group(1)).is_file():
            bad.append(f"{path.name}: todo/{m.group(1)} закрыта — поставить «Статус: черновик»")
    assert not bad, "\n".join(bad)


def test_status_regex_rejects_free_text():
    assert STATUS_RE.match("Статус: заблокировано: ждёт todo/form-flag.md")
    assert not STATUS_RE.match("Статус: заблокировано: Opus")
    assert not STATUS_RE.match("Статус: на проверке")
