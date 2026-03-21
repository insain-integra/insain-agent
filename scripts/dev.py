#!/usr/bin/env python3
"""
Запуск и остановка локально: сервис калькуляторов (uvicorn) и Telegram-бот.

Примеры:
  python scripts/dev.py start all
  python scripts/dev.py stop calc
  python scripts/dev.py status
  python scripts/dev.py restart bot

Переменные окружения (опционально):
  CALC_HOST   — по умолчанию 127.0.0.1
  CALC_PORT   — по умолчанию 8001
"""

from __future__ import annotations

import argparse
import os
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RUN_DIR = ROOT / ".run"
CALC_HOST = os.environ.get("CALC_HOST", "127.0.0.1")
CALC_PORT = int(os.environ.get("CALC_PORT", "8001"))


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
    print(f"calc: запущен uvicorn PID {proc.pid} → http://{CALC_HOST}:{CALC_PORT}")


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


def main() -> None:
    parser = argparse.ArgumentParser(description="Запуск/остановка calc_service и бота")
    parser.add_argument(
        "action",
        choices=("start", "stop", "restart", "status"),
        help="действие",
    )
    parser.add_argument(
        "service",
        nargs="?",
        default="all",
        choices=("calc", "bot", "all"),
        help="какой сервис (по умолчанию all)",
    )
    args = parser.parse_args()

    if args.action == "status":
        cmd_status()
        return

    if args.action == "restart":
        order = ["calc", "bot"] if args.service == "all" else [args.service]
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
        if args.service in ("calc", "all"):
            cmd_start_calc()
        if args.service in ("bot", "all"):
            cmd_start_bot()
        return

    if args.action == "stop":
        if args.service in ("bot", "all"):
            cmd_stop_bot()
        if args.service in ("calc", "all"):
            cmd_stop_calc()
        return


if __name__ == "__main__":
    main()
