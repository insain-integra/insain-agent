#!/usr/bin/env python3
"""
Запуск и остановка локально: сервис калькуляторов (uvicorn) и Telegram-бот.

Примеры:
  python scripts/dev.py start all
  python scripts/dev.py stop calc
  python scripts/dev.py status
  python scripts/dev.py restart bot
  python scripts/dev.py check
  python scripts/dev.py wt-add <имя> [--force]
  python scripts/dev.py wt-check <имя>
  python scripts/dev.py wt-rm <имя>
  python scripts/dev.py lock acquire <prod|merge> <имя> [--force]
  python scripts/dev.py lock release <prod|merge> <имя> [--force]
  python scripts/dev.py lock status
  python scripts/dev.py usage <выгрузка Usage из Cursor.csv>

Переменные окружения (опционально):
  CALC_HOST   — по умолчанию 127.0.0.1
  CALC_PORT   — по умолчанию 8001 (в параллельном worktree задайте свой, например 8011)
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import fnmatch
import json
import os
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RUN_DIR = ROOT / ".run"
CALC_HOST = os.environ.get("CALC_HOST", "127.0.0.1")
CALC_PORT = int(os.environ.get("CALC_PORT", "8001"))
ACTIVE_TASK_STATUSES = {"в работе", "ревью", "доработка", "выкатка", "закрытие"}
LOCK_RESOURCES = ("prod", "merge")
SKIP_TODO_FILES = {"AGENTS.md", "_template.md", "_template-epic.md"}


def _is_windows() -> bool:
    return sys.platform == "win32"


def _ensure_run_dir() -> None:
    RUN_DIR.mkdir(parents=True, exist_ok=True)


def _pid_path(name: str) -> Path:
    return RUN_DIR / f"{name}.pid"


def _read_pid(name: str) -> int | None:
    p = _pid_path(name)
    if not p.is_file():
        return None
    try:
        return int(p.read_text(encoding="utf-8").strip())
    except (ValueError, OSError):
        return None


def _write_pid(name: str, pid: int) -> None:
    _ensure_run_dir()
    _pid_path(name).write_text(str(pid), encoding="utf-8")


def _remove_pid(name: str) -> None:
    p = _pid_path(name)
    if p.is_file():
        p.unlink()


def _pid_listening_on_port(port: int) -> int | None:
    """Вернуть PID процесса, слушающего TCP port (Windows / Unix)."""
    try:
        if _is_windows():
            out = subprocess.check_output(
                ["netstat", "-ano"], text=True, encoding="utf-8", errors="replace"
            )
            for line in out.splitlines():
                if f":{port}" in line and "LISTENING" in line.upper():
                    parts = line.split()
                    if parts:
                        try:
                            return int(parts[-1])
                        except ValueError:
                            continue
        else:
            try:
                out = subprocess.check_output(
                    ["ss", "-lntp"], text=True, stderr=subprocess.DEVNULL
                )
            except (FileNotFoundError, subprocess.CalledProcessError):
                out = subprocess.check_output(
                    ["lsof", "-i", f"TCP:{port}", "-sTCP:LISTEN", "-t", "-n", "-P"],
                    text=True,
                )
            for line in out.splitlines():
                m = re.search(r"pid=(\d+)", line) or re.search(r"^(\d+)", line.strip())
                if m:
                    return int(m.group(1))
    except (subprocess.CalledProcessError, FileNotFoundError, OSError):
        pass
    return None


def _kill_pid(pid: int, tree: bool = True) -> bool:
    if pid <= 0:
        return False
    try:
        if _is_windows():
            args = ["taskkill", "/F", "/PID", str(pid)]
            if tree:
                args.insert(1, "/T")
            r = subprocess.run(args, capture_output=True, text=True)
            return r.returncode == 0
        else:
            try:
                os.kill(pid, 15)
            except ProcessLookupError:
                return False
            return True
    except OSError:
        return False


def _process_exists(pid: int) -> bool:
    if pid <= 0:
        return False
    try:
        if _is_windows():
            r = subprocess.run(
                ["tasklist", "/FI", f"PID eq {pid}"],
                capture_output=True,
                text=True,
            )
            return str(pid) in (r.stdout or "")
        os.kill(pid, 0)
        return True
    except (ProcessLookupError, OSError):
        return False


def cmd_start_calc() -> None:
    if _read_pid("calc") and _process_exists(_read_pid("calc") or 0):
        print("calc: уже запущен (PID из .run/calc.pid).")
        return
    existing = _pid_listening_on_port(CALC_PORT)
    if existing:
        print(f"calc: порт {CALC_PORT} занят PID {existing}. Остановите процесс или: python scripts/dev.py stop calc")
        return

    cwd = ROOT / "calc_service"
    cmd = [
        sys.executable,
        "-m",
        "uvicorn",
        "main:app",
        "--host",
        CALC_HOST,
        "--port",
        str(CALC_PORT),
        "--reload",
    ]
    proc = subprocess.Popen(cmd, cwd=cwd)
    _write_pid("calc", proc.pid)
    print(f"calc: запущен uvicorn PID {proc.pid} -> http://{CALC_HOST}:{CALC_PORT}")


def cmd_start_bot() -> None:
    pid = _read_pid("bot")
    if pid and _process_exists(pid):
        print("bot: уже запущен (PID из .run/bot.pid).")
        return

    cwd = ROOT / "bot_service"
    cmd = [sys.executable, "bot.py"]
    proc = subprocess.Popen(cmd, cwd=cwd)
    _write_pid("bot", proc.pid)
    print(f"bot: запущен PID {proc.pid} (bot_service/bot.py)")


def cmd_stop_calc() -> None:
    pid = _read_pid("calc")
    if pid and not _process_exists(pid):
        _remove_pid("calc")
        pid = None

    killed = False
    if pid and _process_exists(pid):
        if _kill_pid(pid, tree=True):
            print(f"calc: остановлен PID {pid} (дерево процессов).")
            killed = True
        else:
            print(f"calc: не удалось завершить PID {pid}.")
    _remove_pid("calc")

    port_pid = _pid_listening_on_port(CALC_PORT)
    if port_pid and (not pid or port_pid != pid):
        if _kill_pid(port_pid, tree=True):
            print(f"calc: остановлен процесс на порту {CALC_PORT} (PID {port_pid}).")
            killed = True
        else:
            print(f"calc: порт {CALC_PORT} всё ещё занят PID {port_pid} — завершите вручную.")
    elif not killed and not port_pid:
        print("calc: не запущен (порт свободен).")


def cmd_stop_bot() -> None:
    pid = _read_pid("bot")
    if pid and _process_exists(pid):
        if _kill_pid(pid, tree=False):
            print(f"bot: остановлен PID {pid}.")
        else:
            print(f"bot: не удалось завершить PID {pid}.")
    else:
        print("bot: PID-файл отсутствует или процесс не найден.")
    _remove_pid("bot")


def cmd_check() -> None:
    """pytest calc_service и bot_service. Ненулевой код, если упала любая сюита.

    Локально сначала пересобирает docs/dashboard.md (он меняется от любой смены статуса задачи).
    В CI (переменная CI) не пересобирает: там тест сверяет закоммиченный файл.
    """
    if not os.environ.get("CI"):
        sys.path.insert(0, str(Path(__file__).parent))
        from dashboard import write as dash_write

        dash_write()
    suites = ("calc_service/tests", "bot_service/tests")
    for suite in suites:
        rc = subprocess.call(
            [sys.executable, "-m", "pytest", suite, "-q", "--tb=short", "--disable-warnings"], cwd=ROOT
        )
        if rc != 0:
            sys.exit(rc)


def _git_out(*args: str, cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", "-c", "core.quotepath=off", *args],
        cwd=cwd or ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )


def _normalize_task_name(raw: str) -> str:
    name = raw.strip().replace("\\", "/")
    if "/" in name:
        name = name.rsplit("/", 1)[-1]
    name = name.removesuffix(".md")
    if not name or not re.fullmatch(r"[A-Za-z0-9._-]+", name):
        sys.exit(f"некорректное имя задачи: {raw!r}")
    return name


def _require_main_repo_root() -> None:
    if not (ROOT / ".git").is_dir():
        sys.exit("команда выполняется только из основной папки репозитория (не из worktree)")
    r = _git_out("branch", "--show-current")
    if r.returncode != 0 or r.stdout.strip() != "main":
        cur = r.stdout.strip() or "?"
        sys.exit(f"основная папка должна быть на ветке main (сейчас: {cur!r})")


def _git_common_dir(cwd: Path | None = None) -> Path:
    r = _git_out("rev-parse", "--git-common-dir", cwd=cwd or ROOT)
    if r.returncode != 0 or not r.stdout.strip():
        sys.exit(r.stderr.strip() or "не удалось определить общий каталог .git")
    p = Path(r.stdout.strip())
    if not p.is_absolute():
        p = (cwd or ROOT) / p
    return p.resolve()


def _main_repo_root(cwd: Path | None = None) -> Path:
    common = _git_common_dir(cwd)
    return common.parent if common.name == ".git" else ROOT


def _locks_dir(cwd: Path | None = None) -> Path:
    return _git_common_dir(cwd) / "insain-locks"


def _list_worktrees(cwd: Path | None = None) -> list[tuple[Path, str]]:
    """Вернуть список (путь, ветка) из `git worktree list --porcelain`."""
    r = _git_out("worktree", "list", "--porcelain", cwd=cwd or ROOT)
    if r.returncode != 0:
        return []
    items: list[tuple[Path, str]] = []
    cur_path: Path | None = None
    cur_branch = ""
    for line in r.stdout.splitlines() + [""]:
        if not line.strip():
            if cur_path is not None:
                items.append((cur_path, cur_branch))
            cur_path = None
            cur_branch = ""
        elif line.startswith("worktree "):
            cur_path = Path(line[len("worktree ") :].strip()).resolve()
        elif line.startswith("branch "):
            ref = line[len("branch ") :].strip()
            cur_branch = ref.removeprefix("refs/heads/")
    return items


def _extract_todo_files(text: str) -> list[str]:
    """Извлечь пути/маски из раздела «## Файлы» задачи."""
    m = re.search(r"^## Файлы\s*$", text, re.M)
    if not m:
        return []
    rest = text[m.end() :]
    nxt = re.search(r"^## ", rest, re.M)
    section = rest[: nxt.start()] if nxt else rest

    found: list[str] = []
    for raw_line in section.splitlines():
        line = raw_line.strip()
        if not line.startswith("- "):
            continue
        ticks = re.findall(r"`([^`]+)`", line)
        candidates = ticks if ticks else re.findall(r"[\w.<>*?-]+(?:/[\w.<>*?-]+)+", line)
        for c in candidates:
            norm = c.strip().replace("\\", "/").lstrip("./")
            if "/" in norm or norm.endswith((".py", ".js", ".md", ".json", ".php", ".sh", ".yml")):
                if norm not in found:
                    found.append(norm)
    return found


def _paths_overlap(a: str, b: str) -> bool:
    pa = re.sub(r"<[^>]+>", "*", a)
    pb = re.sub(r"<[^>]+>", "*", b)
    return a == b or fnmatch.fnmatch(a, pb) or fnmatch.fnmatch(b, pa)


def _todo_status(text: str) -> str:
    for ln in text.splitlines():
        if ln.startswith("Статус:"):
            return ln[len("Статус:") :].strip()
    return ""


def find_file_conflicts(name: str, repo_root: Path | None = None) -> list[tuple[str, list[str]]]:
    """Найти пересечения «## Файлы» задачи name с активными задачами."""
    root = repo_root or ROOT
    todo_dir = root / "todo"
    target = todo_dir / f"{name}.md"
    if not target.is_file():
        return []
    my_files = _extract_todo_files(target.read_text(encoding="utf-8"))
    if not my_files:
        return []

    active_wt_tasks = {
        branch.removeprefix("task/")
        for _p, branch in _list_worktrees(root)
        if branch.startswith("task/")
    }

    conflicts: list[tuple[str, list[str]]] = []
    for path in sorted(todo_dir.glob("*.md")):
        if path.name in SKIP_TODO_FILES or path.name.startswith("EPIC-"):
            continue
        other = path.stem
        if other == name:
            continue
        text = path.read_text(encoding="utf-8")
        status = _todo_status(text)
        if other not in active_wt_tasks and status not in ACTIVE_TASK_STATUSES:
            continue
        other_files = _extract_todo_files(text)
        overlaps = sorted({mf for mf in my_files for of in other_files if _paths_overlap(mf, of)})
        if overlaps:
            conflicts.append((other, overlaps))
    return conflicts


def cmd_wt_add(raw_name: str, force: bool = False) -> Path:
    """Создать worktree ..\\insain-agent-<имя> на ветке task/<имя> от main."""
    _require_main_repo_root()
    name = _normalize_task_name(raw_name)
    todo_rel = f"todo/{name}.md"
    todo_file = ROOT / "todo" / f"{name}.md"
    if not todo_file.is_file():
        sys.exit(f"нет файла {todo_rel} на main")

    tracked = _git_out("ls-files", "--error-unmatch", "--", todo_rel)
    dirty = _git_out("status", "--porcelain", "--", todo_rel)
    if tracked.returncode != 0 or dirty.stdout.strip():
        sys.exit(f"{todo_rel} не закоммичен в main — сначала закоммитьте файл задачи")

    wt_path = (ROOT.parent / f"{ROOT.name}-{name}").resolve()
    branch = f"task/{name}"
    existing_wts = dict(_list_worktrees(ROOT))
    if wt_path in existing_wts:
        if existing_wts[wt_path] == branch:
            print(f"worktree уже существует: {wt_path} (ветка {branch})")
            return wt_path
        sys.exit(f"папка {wt_path} уже привязана к ветке {existing_wts[wt_path]!r}, ожидалась {branch!r}")

    if wt_path.exists():
        sys.exit(f"папка уже существует: {wt_path}")

    if not force:
        conflicts = find_file_conflicts(name, ROOT)
        if conflicts:
            details = "; ".join(f"{t}: {', '.join(fs)}" for t, fs in conflicts)
            sys.exit(
                f"пересечение «## Файлы» с активными задачами ({details}). "
                "Дождитесь их закрытия или передайте --force"
            )

    has_branch = _git_out("show-ref", "--verify", "--quiet", f"refs/heads/{branch}").returncode == 0
    args = ["worktree", "add", str(wt_path), branch] if has_branch else ["worktree", "add", str(wt_path), "-b", branch, "main"]
    res = _git_out(*args)
    if res.returncode != 0:
        sys.exit(res.stderr.strip() or res.stdout.strip() or f"не удалось создать worktree {wt_path}")

    print(f"worktree создан: {wt_path} (ветка {branch})")
    print(f"Рабочая папка задачи: {wt_path}")
    return wt_path


def cmd_wt_check(raw_name: str) -> None:
    """Проверить изоляцию: основная папка чистая на main, worktree задачи на task/<имя>."""
    name = _normalize_task_name(raw_name)
    main_root = _main_repo_root(ROOT)
    wt_path = (main_root.parent / f"{main_root.name}-{name}").resolve()
    branch = f"task/{name}"

    errors: list[str] = []
    main_branch = _git_out("branch", "--show-current", cwd=main_root)
    cur_main = main_branch.stdout.strip() if main_branch.returncode == 0 else "?"
    if cur_main != "main":
        errors.append(f"основная папка {main_root} на ветке {cur_main!r}, должна быть на 'main'")

    main_status = _git_out("status", "--porcelain", cwd=main_root)
    dirty_lines = [ln for ln in main_status.stdout.splitlines() if ln.strip()]
    if dirty_lines:
        preview = ", ".join(dirty_lines[:5])
        errors.append(f"незакоммиченные правки в основной папке {main_root}: {preview}")

    wts = dict(_list_worktrees(main_root))
    if wt_path not in wts:
        errors.append(f"worktree {wt_path} не найден (создайте: python scripts/dev.py wt-add {name})")
    elif wts[wt_path] != branch:
        errors.append(f"worktree {wt_path} на ветке {wts[wt_path]!r}, ожидалась {branch!r}")

    if errors:
        sys.exit("Нарушена изоляция worktree:\n- " + "\n- ".join(errors))

    print(f"изоляция ok: main чистый ({main_root}), worktree {wt_path} ({branch})")


def cmd_wt_rm(raw_name: str) -> None:
    """Удалить worktree ..\\insain-agent-<имя> и слитую ветку task/<имя>."""
    _require_main_repo_root()
    name = _normalize_task_name(raw_name)
    wt_path = ROOT.parent / f"{ROOT.name}-{name}"
    branch = f"task/{name}"

    if wt_path.exists():
        res = _git_out("worktree", "remove", str(wt_path))
        if res.returncode != 0:
            sys.exit(res.stderr.strip() or res.stdout.strip() or f"не удалось удалить worktree {wt_path}")
        print(f"worktree удалён: {wt_path}")
    else:
        _git_out("worktree", "prune")
        print(f"worktree отсутствует: {wt_path}")

    has_branch = _git_out("show-ref", "--verify", "--quiet", f"refs/heads/{branch}").returncode == 0
    if has_branch:
        del_res = _git_out("branch", "-d", branch)
        if del_res.returncode != 0:
            sys.exit(del_res.stderr.strip() or del_res.stdout.strip() or f"ветка {branch} не удалена")
        print(f"ветка удалена: {branch}")


def _read_lock(path: Path) -> dict[str, str]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {}
    except (OSError, json.JSONDecodeError):
        return {}


def cmd_lock_acquire(resource: str, raw_name: str, force: bool = False) -> None:
    if resource not in LOCK_RESOURCES:
        sys.exit(f"неизвестный ресурс {resource!r}; доступно: {', '.join(LOCK_RESOURCES)}")
    name = _normalize_task_name(raw_name)
    locks_dir = _locks_dir(ROOT)
    locks_dir.mkdir(parents=True, exist_ok=True)
    lock_file = locks_dir / f"{resource}.lock"

    payload = json.dumps(
        {
            "resource": resource,
            "task": name,
            "cwd": str(ROOT),
            "acquired_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        },
        ensure_ascii=False,
        indent=2,
    )

    if not force:
        try:
            fd = os.open(lock_file, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o644)
            with os.fdopen(fd, "w", encoding="utf-8") as fh:
                fh.write(payload + "\n")
            print(f"lock {resource}: захвачен задачей {name}")
            return
        except FileExistsError:
            cur = _read_lock(lock_file)
            holder = cur.get("task", "?")
            if holder == name:
                lock_file.write_text(payload + "\n", encoding="utf-8")
                print(f"lock {resource}: подтверждён задачей {name}")
                return
            since = cur.get("acquired_at", "?")
            sys.exit(
                f"ресурс {resource!r} занят задачей {holder!r} (с {since}). "
                f"Дождитесь завершения или снимите: python scripts/dev.py lock release {resource} {holder} --force"
            )

    lock_file.write_text(payload + "\n", encoding="utf-8")
    print(f"lock {resource}: принудительно захвачен задачей {name}")


def cmd_lock_release(resource: str, raw_name: str, force: bool = False) -> None:
    if resource not in LOCK_RESOURCES:
        sys.exit(f"неизвестный ресурс {resource!r}; доступно: {', '.join(LOCK_RESOURCES)}")
    name = _normalize_task_name(raw_name)
    lock_file = _locks_dir(ROOT) / f"{resource}.lock"
    if not lock_file.is_file():
        print(f"lock {resource}: не был занят")
        return
    cur = _read_lock(lock_file)
    holder = cur.get("task", "?")
    if holder != name and not force:
        sys.exit(f"lock {resource} удерживает задача {holder!r}, а не {name!r} (для сброса — --force)")
    lock_file.unlink()
    print(f"lock {resource}: освобождён (была задача {holder})")


def cmd_lock_status() -> None:
    locks_dir = _locks_dir(ROOT)
    any_lock = False
    for resource in LOCK_RESOURCES:
        lf = locks_dir / f"{resource}.lock"
        if lf.is_file():
            any_lock = True
            cur = _read_lock(lf)
            print(f"  {resource}: занят задачей {cur.get('task', '?')} (с {cur.get('acquired_at', '?')})")
    if not any_lock:
        print("locks: свободен (prod, merge)")


def cmd_status() -> None:
    print(f"CALC_API: http://{CALC_HOST}:{CALC_PORT}")
    cp = _read_pid("calc")
    if cp and _process_exists(cp):
        print(f"calc: running PID {cp} (из .run/calc.pid)")
    else:
        lp = _pid_listening_on_port(CALC_PORT)
        if lp:
            print(f"calc: порт {CALC_PORT} слушает PID {lp} (не из dev.py)")
        else:
            print("calc: не запущен")

    bp = _read_pid("bot")
    if bp and _process_exists(bp):
        print(f"bot:  running PID {bp} (из .run/bot.pid)")
    else:
        print("bot:  не запущен (или запущен не через dev.py)")

    wt = _git_out("worktree", "list")
    if wt.returncode == 0:
        lines = [ln for ln in wt.stdout.splitlines() if ln.strip()]
        if len(lines) > 1:
            print("worktrees:")
            for ln in lines:
                print(f"  {ln}")
    cmd_lock_status()


def main() -> None:
    parser = argparse.ArgumentParser(description="Запуск/остановка calc_service и бота")
    parser.add_argument(
        "action",
        choices=(
            "start",
            "stop",
            "restart",
            "status",
            "check",
            "close",
            "dashboard",
            "usage",
            "wt-add",
            "wt-check",
            "wt-rm",
            "lock",
        ),
        help="действие",
    )
    parser.add_argument(
        "args",
        nargs="*",
        help="аргументы команды",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="игнорировать блокировку/пересечение (для wt-add и lock)",
    )
    args = parser.parse_args()
    first = args.args[0] if args.args else None

    if args.action == "wt-add":
        if not first:
            sys.exit("нужно имя задачи: python scripts/dev.py wt-add <имя>")
        cmd_wt_add(first, force=args.force)
        return

    if args.action == "wt-check":
        if not first:
            sys.exit("нужно имя задачи: python scripts/dev.py wt-check <имя>")
        cmd_wt_check(first)
        return

    if args.action == "wt-rm":
        if not first:
            sys.exit("нужно имя задачи: python scripts/dev.py wt-rm <имя>")
        cmd_wt_rm(first)
        return

    if args.action == "lock":
        if not first:
            sys.exit("использование: python scripts/dev.py lock <acquire|release|status> [prod|merge] [<имя>]")
        if first == "status":
            cmd_lock_status()
            return
        if len(args.args) < 3:
            sys.exit(f"использование: python scripts/dev.py lock {first} <prod|merge> <имя>")
        sub, resource, task_name = args.args[0], args.args[1], args.args[2]
        if sub == "acquire":
            cmd_lock_acquire(resource, task_name, force=args.force)
        elif sub == "release":
            cmd_lock_release(resource, task_name, force=args.force)
        else:
            sys.exit("подкоманда lock: acquire, release или status")
        return

    if args.action == "usage":
        if not first:
            sys.exit("нужен CSV из кабинета Cursor: python scripts/dev.py usage <файл.csv>")
        sys.path.insert(0, str(Path(__file__).parent))
        from usage_report import main as usage_main

        usage_main(first)
        return

    if args.action == "check":
        cmd_check()
        return

    if args.action == "dashboard":
        sys.path.insert(0, str(Path(__file__).parent))
        from dashboard import write as dash_write

        print(dash_write())
        return

    if args.action == "close":
        if not first:
            sys.exit("нужно имя задачи: python scripts/dev.py close <имя>")
        sys.path.insert(0, str(Path(__file__).parent))
        from close_task import close as close_task

        close_task(first)
        return

    if args.action == "status":
        cmd_status()
        return

    svc = first or "all"
    if svc not in ("calc", "bot", "all"):
        sys.exit("сервис: calc, bot или all")

    if args.action == "restart":
        order = ["calc", "bot"] if svc == "all" else [svc]
        for s in order:
            if s == "calc":
                cmd_stop_calc()
            else:
                cmd_stop_bot()
        for s in order:
            if s == "calc":
                cmd_start_calc()
            else:
                cmd_start_bot()
        return

    if args.action == "start":
        if svc in ("calc", "all"):
            cmd_start_calc()
        if svc in ("bot", "all"):
            cmd_start_bot()
        return

    if args.action == "stop":
        if svc in ("bot", "all"):
            cmd_stop_bot()
        if svc in ("calc", "all"):
            cmd_stop_calc()
        return


if __name__ == "__main__":
    main()
