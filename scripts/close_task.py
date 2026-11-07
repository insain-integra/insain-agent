"""Закрыть задачу: журнал, «ждёт», BACKLOG, дашборд, удалить файл. Коммит не делает."""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from datetime import date, datetime, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(Path(__file__).parent))
TODO = ROOT / "todo"
LOG = ROOT / "docs" / "history" / "log.md"
BACKLOG = ROOT / "BACKLOG.md"
SKIP_TODO = {"AGENTS.md", "_template.md", "_template-epic.md"}

MONTHS = {
    "Jan": 1,
    "Feb": 2,
    "Mar": 3,
    "Apr": 4,
    "May": 5,
    "Jun": 6,
    "Jul": 7,
    "Aug": 8,
    "Sep": 9,
    "Oct": 10,
    "Nov": 11,
    "Dec": 12,
}


def _git(*args: str) -> str:
    try:
        return subprocess.check_output(
            ["git", *args],
            cwd=ROOT,
            text=True,
            encoding="utf-8",
            errors="replace",
        ).strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        return ""


def _section(text: str, heading: str) -> str:
    m = re.search(rf"^## {re.escape(heading)}\s*$", text, re.M)
    if not m:
        return ""
    rest = text[m.end() :]
    nxt = re.search(r"^## ", rest, re.M)
    return rest[: nxt.start()] if nxt else rest


def _field(section: str, name: str) -> str:
    m = re.search(rf"^-\s*{re.escape(name)}:\s*(.*)$", section, re.M)
    return (m.group(1).strip() if m else "").strip("—- ").strip()


def _parse_cursor_ts(raw: str) -> datetime | None:
    m = re.search(
        r"(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+(\d{1,2}),\s+(\d{4}),\s+(\d{1,2}):(\d{2})\s*(AM|PM)?",
        raw,
    )
    if not m:
        iso = re.search(r"(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2})", raw)
        if iso:
            try:
                return datetime.fromisoformat(iso.group(1))
            except ValueError:
                return None
        return None
    month, day, year, hour, minute, ampm = m.groups()
    h = int(hour)
    if ampm == "PM" and h != 12:
        h += 12
    if ampm == "AM" and h == 12:
        h = 0
    try:
        return datetime(int(year), MONTHS[month], int(day), h, int(minute))
    except ValueError:
        return None


def _transcript_dirs() -> list[Path]:
    found: list[Path] = []
    env = os.environ.get("CURSOR_TRANSCRIPTS")
    if env:
        found.append(Path(env))
    home = Path.home()
    found.append(home / ".cursor" / "projects" / "d-Projects-insain-agent" / "agent-transcripts")
    found.extend(home.glob(".cursor/projects/*/agent-transcripts"))
    uniq: list[Path] = []
    seen: set[str] = set()
    for p in found:
        key = str(p.resolve()) if p.exists() else str(p)
        if key in seen:
            continue
        seen.add(key)
        if p.is_dir():
            uniq.append(p)
    return uniq


def _walk_jsonl(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""


IDLE_CAP = timedelta(minutes=30)


def active_time(stamps: list[datetime], cap: timedelta = IDLE_CAP) -> timedelta:
    """Сумма пауз между сообщениями; пауза длиннее cap — перерыв, не считается."""
    total = timedelta()
    ordered = sorted(stamps)
    for a, b in zip(ordered, ordered[1:]):
        if b - a <= cap:
            total += b - a
    return total


def _period(first: datetime | date, last: datetime | date) -> str:
    a, b = first.strftime("%Y-%m-%d"), last.strftime("%Y-%m-%d")
    days = (datetime.strptime(b, "%Y-%m-%d") - datetime.strptime(a, "%Y-%m-%d")).days + 1
    return f"{a} — {b} ({days} дн.)"


def chat_period(stamps: list[datetime]) -> str:
    """Период работы — от первого до последнего сообщения в чатах задачи."""
    return _period(min(stamps), max(stamps)) if stamps else ""


def hours_from_chats(task_name: str) -> tuple[int, int, float, str, str]:
    """Сессии задачи, сообщений человека, активные часы, пояснение, период по чатам.

    Сессия задачи — чат, в первом сообщении которого есть todo/<имя>; чаты, где задачу
    только упоминают (оркестрация, соседние задачи), не считаются.
    """
    needles = (f"todo/{task_name}.md", f"todo/{task_name}")
    files: list[Path] = []
    for d in _transcript_dirs():
        files.extend(d.rglob("*.jsonl"))
    sessions = 0
    user_msgs = 0
    total = timedelta()
    all_stamps: list[datetime] = []
    for path in files:
        raw = _walk_jsonl(path)
        if not any(n in raw for n in needles):
            continue
        user_blobs: list[str] = []
        for line in raw.splitlines():
            try:
                obj = json.loads(line)
            except json.JSONDecodeError:
                continue
            if obj.get("role") == "user":
                user_blobs.append(json.dumps(obj, ensure_ascii=False))
        if not user_blobs or not any(n in user_blobs[0] for n in needles):
            continue
        sessions += 1
        stamps: list[datetime] = []
        for blob in user_blobs:
            user_msgs += blob.count("<user_query>") or 1
            for m in re.finditer(r"<timestamp>(.*?)</timestamp>", blob):
                ts = _parse_cursor_ts(m.group(1))
                if ts:
                    stamps.append(ts)
        total += active_time(stamps)
        all_stamps.extend(stamps)
    hours = round(total.total_seconds() / 3600, 1)
    if sessions == 0:
        return 0, 0, 0.0, "чаты Cursor не найдены", ""
    note = f"{sessions} чатов Cursor, {user_msgs} сообщ. человека, {hours} ч активных"
    return sessions, user_msgs, hours, note, chat_period(all_stamps)


def git_period(task_name: str) -> str:
    dates = _git("log", "--format=%cs", "--", f"todo/{task_name}.md")
    if not dates:
        return "—"
    lines = [ln for ln in dates.splitlines() if ln]
    first, last = lines[-1], lines[0]
    try:
        return _period(datetime.strptime(first, "%Y-%m-%d"), datetime.strptime(last, "%Y-%m-%d"))
    except ValueError:
        return f"{first} — {last}"


def git_commits(task_name: str) -> str:
    out = _git("log", "--oneline", "--", f"todo/{task_name}.md")
    hashes = " ".join(ln.split()[0] for ln in out.splitlines()[:8] if ln)
    return hashes or "—"


def _mark_closed_links(closed_file: str, day: str) -> list[str]:
    """Ссылки `todo/<имя>.md` в оставшихся задачах и эпиках → закрыто, запись в журнале."""
    changed: list[str] = []
    stem = closed_file[:-3]
    link = re.compile(rf"`?todo/{re.escape(closed_file)}`?")
    repl = f"`{stem}` (закрыто {day}, `docs/history/log.md`)"
    for path in TODO.glob("*.md"):
        if path.name in SKIP_TODO:
            continue
        text = path.read_text(encoding="utf-8")
        new = link.sub(repl, text)
        if new != text:
            path.write_text(new, encoding="utf-8", newline="\n")
            changed.append(path.name)
    return changed


def _unlock(closed_file: str) -> list[str]:
    changed: list[str] = []
    needle = f"Статус: заблокировано: ждёт todo/{closed_file}"
    for path in TODO.glob("*.md"):
        if path.name in SKIP_TODO:
            continue
        text = path.read_text(encoding="utf-8")
        if needle not in text:
            continue
        path.write_text(
            text.replace(needle, "Статус: черновик", 1),
            encoding="utf-8",
            newline="\n",
        )
        changed.append(path.name)
    return changed


def _backlog_findings(task_name: str, section: str) -> None:
    items = []
    for ln in section.splitlines():
        s = ln.strip()
        if s.startswith("- ") and s not in {"- —", "- -"}:
            items.append(s[2:].strip())
    items = [i for i in items if i and i != "—"]
    if not items:
        return
    extra = "\n".join(f"- Из `{task_name}`: {i}" for i in items)
    cur = BACKLOG.read_text(encoding="utf-8")
    if "## Найдено вне scope" not in cur:
        cur = cur.rstrip() + "\n\n## Найдено вне scope\n\n" + extra + "\n"
    else:
        cur = cur.rstrip() + "\n" + extra + "\n"
    BACKLOG.write_text(cur, encoding="utf-8", newline="\n")


def _insert_log(entry: str) -> None:
    text = LOG.read_text(encoding="utf-8")
    m = re.search(r"^## \d{4}-\d{2}-\d{2} ", text, re.M)
    if not m:
        LOG.write_text(text.rstrip() + "\n\n" + entry + "\n", encoding="utf-8", newline="\n")
        return
    LOG.write_text(text[: m.start()] + entry + "\n\n" + text[m.start() :], encoding="utf-8", newline="\n")


def close(name: str) -> None:
    name = name.removesuffix(".md")
    path = TODO / f"{name}.md"
    if not path.is_file():
        raise SystemExit(f"нет файла {path}")
    text = path.read_text(encoding="utf-8")
    result = _section(text, "Результат")
    journal = _section(text, "Журнал передач")
    findings = _section(text, "Найдено вне scope")
    bylo = _field(result, "Было / стало") or _field(result, "Было")
    stalo = _field(result, "Стало")
    if not bylo and not stalo:
        raise SystemExit(
            "В «Результате» пусто «Было / стало». Заполните и повторите close."
        )
    if not journal.strip() or journal.strip() in {"—", "-"}:
        raise SystemExit("Пустой «Журнал передач». Заполните строку сессии и повторите close.")

    title_m = re.search(r"^#\s+(.+)$", text, re.M)
    title = title_m.group(1).strip() if title_m else name
    heading = datetime.now().strftime("%Y-%m-%d")
    sessions, user_msgs, hours, chat_note, period = hours_from_chats(name)
    models = []
    for key in ("Implementer", "Reviewer", "Site ops"):
        m = re.search(rf"^{key}:\s*(.+)$", text, re.M)
        if m and "не нужен" not in m.group(1):
            models.append(f"{key} — {m.group(1).strip()}")
    bylo_stalo = bylo if " / " in bylo or stalo else (f"{bylo} / {stalo}".strip(" /"))
    entry = "\n".join(
        [
            f"## {heading} — {title}",
            "",
            f"- Период: {period or git_period(name)}",
            f"- Часы человека: {user_msgs} сообщ. в чатах Cursor; активно {hours} ч (паузы > 30 мин не в счёт)"
            + (f" ({chat_note})" if sessions == 0 else ""),
            f"- Работа агентов: {chat_note}; {'; '.join(models) or 'модели — из шапки'}",
            f"- Было / стало: {bylo_stalo}",
            "- Эффект: —",
            f"- Источник: задача `todo/{name}.md`, коммиты {git_commits(name)}",
        ]
    )
    _insert_log(entry)
    unlocked = _unlock(path.name)
    _backlog_findings(name, findings)
    path.unlink()
    relinked = _mark_closed_links(path.name, heading)
    from dashboard import write as dash_write

    dash_write()
    print(f"закрыто: {name}.md")
    if unlocked:
        print("снят «ждёт»:", ", ".join(unlocked))
    if relinked:
        print("ссылки помечены закрытыми:", ", ".join(relinked))
    print("журнал и дашборд обновлены; коммит отдельно")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        raise SystemExit("usage: python scripts/close_task.py <имя>")
    close(sys.argv[1])
