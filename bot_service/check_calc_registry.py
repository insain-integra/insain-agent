#!/usr/bin/env python3
"""
Сравнение реестра калькуляторов в локальном коде (calc_service) с тем, что отдаёт API.

Запуск из корня репозитория:
  python bot_service/check_calc_registry.py

Переменная окружения CALC_API_URL (или .env в корне) — адрес calc_service.

Код выхода: 0 — расхождений нет, все проверки пройдены; 1 — ошибка или есть расхождения.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path


def _load_env() -> None:
    root = Path(__file__).resolve().parent.parent
    env_path = root / ".env"
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
                    k, v = k.strip(), v.strip().strip("'\"")
                    if k and k not in os.environ:
                        os.environ[k] = v


def main() -> int:
    _load_env()

    root = Path(__file__).resolve().parent.parent
    calc_dir = root / "calc_service"
    if not (calc_dir / "calculators").is_dir():
        print(f"Не найден каталог calc_service: {calc_dir}", file=sys.stderr)
        return 1

    sys.path.insert(0, str(calc_dir))
    try:
        from calculators import CALCULATORS
    except ImportError as e:
        print(f"Импорт calc_service: {e}", file=sys.stderr)
        return 1

    try:
        import httpx
    except ImportError:
        print("Установите: pip install httpx", file=sys.stderr)
        return 1

    base = os.getenv("CALC_API_URL", "http://localhost:8001").strip().rstrip("/")
    print(f"CALC_API_URL = {base}\n")

    local_public = {
        slug
        for slug, calc in CALCULATORS.items()
        if getattr(calc, "is_public", True)
    }

    try:
        r = httpx.get(f"{base}/api/v1/calculators", timeout=30.0)
        r.raise_for_status()
    except httpx.HTTPStatusError as e:
        print(f"GET /api/v1/calculators → HTTP {e.response.status_code}", file=sys.stderr)
        print(e.response.text[:800], file=sys.stderr)
        return 1
    except (httpx.ConnectError, httpx.TimeoutException) as e:
        print(f"Сервис недоступен: {e}", file=sys.stderr)
        return 1

    data = r.json()
    if not isinstance(data, list):
        print("Ответ /calculators не список", file=sys.stderr)
        return 1

    api_slugs = {str(c.get("slug") or "").strip() for c in data if c.get("slug")}
    print(f"На сервере (публичные): {len(api_slugs)} калькуляторов")
    print(f"В локальном коде (is_public): {len(local_public)} калькуляторов\n")

    only_local = sorted(local_public - api_slugs)
    only_api = sorted(api_slugs - local_public)

    ok = True

    if only_local:
        ok = False
        print("[WARN] Есть в коде, но НЕ в ответе API (нужен деплой calc_service или проверьте URL):")
        for s in only_local:
            print(f"   - {s}")
        print()

    if only_api:
        ok = False
        print("[WARN] Есть в API, но не совпадает с локальным is_public-реестром (обновите репозиторий или ветку):")
        for s in only_api:
            print(f"   - {s}")
        print()

    if not only_local and not only_api:
        print("[OK] Список slug (публичные) совпадает.\n")

    # Smoke-тесты: минимальный набор тел POST (проверка, что /calc/{slug} не 404).
    smoke_bodies: dict[str, dict] = {
        "magnet_acrylic": {
            "quantity": 1,
            "magnet_id": "MagnetAcrylic6565",
            "color": 1,
            "is_packing": True,
            "mode": 1,
        },
    }

    # При расхождении списков или CALC_CHECK_FULL=1 — GET tool_schema для всех slug с сервера.
    full_schema_check = bool(only_local or only_api or os.getenv("CALC_CHECK_FULL", "").strip())
    slugs_schema: set[str] = set(api_slugs) if full_schema_check else set()
    if not full_schema_check:
        for s in smoke_bodies:
            if s in api_slugs:
                slugs_schema.add(s)

    failed_schema: list[str] = []
    failed_post: list[str] = []

    for slug in sorted(slugs_schema):
        ts = httpx.get(f"{base}/api/v1/tool_schema/{slug}", timeout=30.0)
        if ts.status_code != 200:
            failed_schema.append(f"{slug} → HTTP {ts.status_code}")
            ok = False
            continue

        body = smoke_bodies.get(slug)
        if body is None:
            continue

        pr = httpx.post(f"{base}/api/v1/calc/{slug}", json=body, timeout=60.0)
        if pr.status_code != 200:
            failed_post.append(f"{slug} → HTTP {pr.status_code} {pr.text[:200]!r}")
            ok = False

    if failed_schema:
        print("Ошибки GET /api/v1/tool_schema/{slug}:")
        for line in failed_schema:
            print(f"   {line}")
        print()

    if failed_post:
        print("Ошибки POST /api/v1/calc/{slug} (smoke-тест):")
        for line in failed_post:
            print(f"   {line}")
        print()
    else:
        ran_smoke = [s for s in smoke_bodies if s in api_slugs and s in slugs_schema]
        if ran_smoke:
            print(f"[OK] Smoke POST для {', '.join(sorted(ran_smoke))}\n")

    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
