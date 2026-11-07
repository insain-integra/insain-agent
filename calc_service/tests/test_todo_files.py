"""Шапка файлов todo/: статус из списка docs/agents/workflow.md, «Статусы»."""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TODO = ROOT / "todo"
VISION = ROOT / "docs" / "vision.md"
SKIP = {"AGENTS.md", "_template.md", "_template-epic.md"}
GOAL_RE = re.compile(r"^Цель: (?:G[1-7]|отложено)\b")

STATUS_RE = re.compile(
    r"^Статус: (?:черновик|в работе|ревью|доработка|выкатка|закрытие|готово"
    r"|заблокировано: (?:аналитик|исполнитель|ревьюер|site ops|человек|ждёт todo/[\w.-]+\.md))$"
)


def _task_files() -> list[Path]:
    return sorted(p for p in TODO.glob("*.md") if p.name not in SKIP)


def _epics() -> list[Path]:
    return sorted(TODO.glob("EPIC-*.md"))


def test_todo_status_from_workflow_list():
    files = sorted(p for p in TODO.glob("*.md") if p.name != "AGENTS.md")
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


def test_epic_has_vision_goal():
    vis = VISION.read_text(encoding="utf-8")
    bad = []
    for path in _epics():
        lines = [ln for ln in path.read_text(encoding="utf-8").splitlines() if ln.startswith("Цель:")]
        head = next((ln for ln in lines if GOAL_RE.match(ln)), None)
        if not head:
            bad.append(f"{path.name}: нет «Цель: G1…G7» или «Цель: отложено»")
            continue
        m = re.match(r"^Цель: (G[1-7])\b", head)
        if m and m.group(1) not in vis:
            bad.append(f"{path.name}: {m.group(1)} нет в docs/vision.md")
    assert not bad, "\n".join(bad)


def test_epic_todo_links_exist():
    bad = []
    for path in _epics():
        text = path.read_text(encoding="utf-8")
        for name in re.findall(r"`todo/([\w.-]+\.md)`", text):
            if not (TODO / name).is_file():
                bad.append(f"{path.name} → todo/{name} нет на диске")
    assert not bad, "\n".join(bad)


def test_status_regex_rejects_free_text():
    assert STATUS_RE.match("Статус: заблокировано: ждёт todo/form-flag.md")
    assert not STATUS_RE.match("Статус: заблокировано: Opus")
    assert not STATUS_RE.match("Статус: на проверке")
