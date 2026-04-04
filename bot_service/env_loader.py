"""Загрузка .env из корня проекта (общий модуль для bot_service)."""

from __future__ import annotations

import os
from pathlib import Path


def load_env() -> None:
    """Загрузить переменные окружения из .env в корне проекта."""
    env_path = Path(__file__).resolve().parent.parent / ".env"
    if not env_path.is_file():
        return
    try:
        from dotenv import load_dotenv
        load_dotenv(env_path)
    except ImportError:
        with open(env_path, encoding="utf-8", errors="ignore") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, _, v = line.partition("=")
                    k, v = k.strip(), v.strip().strip("'\"").strip()
                    if k and k not in os.environ:
                        os.environ[k] = v
