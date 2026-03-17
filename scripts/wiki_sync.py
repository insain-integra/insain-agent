"""
Синхронизация Yandex Wiki → wiki_export/

Использует внутренний API Yandex Wiki (session cookies)
для поиска и выгрузки всех страниц в Markdown-файлы.

Использование:
    python scripts/wiki_sync.py --cookie-file .wiki_cookies.json
    python scripts/wiki_sync.py --help

Cookie-файл (.wiki_cookies.json) — JSON с полями:
    csrf_token, org_id, collab_org_id, cookie

Чтобы получить cookies: открыть wiki.yandex.ru в браузере,
DevTools → Network → скопировать из любого запроса к .gateway/root/wiki/*
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
from pathlib import Path

try:
    import httpx
except ImportError:
    sys.exit("httpx не установлен: pip install httpx")

BASE = "https://wiki.yandex.ru/.gateway/root/wiki"
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_OUT_DIR = PROJECT_ROOT / "wiki_export"
DEFAULT_COOKIE_FILE = PROJECT_ROOT / ".wiki_cookies.json"


def load_cookies(path: Path) -> dict:
    if not path.is_file():
        sys.exit(f"Cookie-файл не найден: {path}\nСоздайте его — см. --help.")
    data = json.loads(path.read_text(encoding="utf-8"))
    required = ["csrf_token", "org_id", "cookie"]
    for key in required:
        if not data.get(key):
            sys.exit(f"В cookie-файле отсутствует поле: {key}")
    return data


def make_headers(cookies: dict) -> dict:
    return {
        "accept": "application/json, text/plain, */*",
        "content-type": "application/json",
        "accept-language": "ru",
        "x-csrf-token": cookies["csrf_token"],
        "x-org-id": cookies["org_id"],
        "x-collab-org-id": cookies.get("collab_org_id", ""),
        "cookie": cookies["cookie"],
    }


def search_pages(client: httpx.Client, query: str, limit: int = 100) -> list[dict]:
    """Search via internal API, return list of result items."""
    r = client.post(f"{BASE}/search", json={"query": query, "limit": limit, "page": 1})
    if r.status_code != 200:
        return []
    data = r.json()
    return data.get("results", []) if isinstance(data, dict) else []


def discover_all_slugs(client: httpx.Client) -> dict[str, str]:
    """Discover all page slugs via search with various queries."""
    slugs: dict[str, str] = {}

    search_terms = [
        "а", "е", "и", "о", "у", "н", "к", "с", "в", "на", "по", "от",
        "установка", "настройка", "инструкция", "процесс", "печать",
        "материал", "оборудование", "работа", "заказ", "клиент",
        "правило", "таблица", "цена", "услуга", "продукция",
        "сервер", "программа", "шаблон", "дизайн", "резка",
        "ламинация", "баннер", "визитка", "вывеска", "наклейка",
        "1С", "CRM", "email", "телефон", "адрес",
        "обучение", "новый", "как", "где", "что",
        "файл", "документ", "форма", "отчет",
        "доступ", "пароль", "логин", "монтаж",
    ]

    for term in search_terms:
        results = search_pages(client, term)
        new = 0
        for item in results:
            slug = item.get("slug", "")
            if slug and slug not in slugs:
                slugs[slug] = item.get("title", slug)
                new += 1
        if new:
            print(f"  '{term}': +{new} (total: {len(slugs)})")
        time.sleep(0.3)

    # Derive section pages from slug paths
    sections: dict[str, str] = {}
    for slug in list(slugs.keys()):
        parts = slug.split("/")
        for i in range(1, len(parts)):
            section = "/".join(parts[:i])
            if section not in slugs and section not in sections:
                sections[section] = section
    for slug in sections:
        r = client.post(f"{BASE}/getPageDetails", json={
            "slug": slug, "fields": ["attributes"], "settings": {"lang": "ru"},
        })
        if r.status_code == 200:
            data = r.json()
            slugs[slug] = data.get("title", slug)
        time.sleep(0.1)

    slugs.setdefault("homepage", "Главная страница")
    return slugs


def fetch_and_save(client: httpx.Client, slug: str, out_dir: Path) -> bool:
    """Fetch page content and save as markdown. Returns True if saved."""
    r = client.post(f"{BASE}/getPageDetails", json={
        "slug": slug,
        "fields": ["content", "breadcrumbs", "attributes"],
        "settings": {"lang": "ru"},
    })
    if r.status_code != 200:
        return False

    data = r.json()
    title = data.get("title", slug)
    content = data.get("content", "")
    breadcrumbs = data.get("breadcrumbs", [])

    if not content.strip():
        return False

    bc_path = " > ".join(b.get("title", "") for b in breadcrumbs)
    md = f"# {title}\n\n"
    if bc_path:
        md += f"*Путь: {bc_path}*\n\n"
    md += f"*Источник: https://wiki.yandex.ru/{slug}*\n\n---\n\n"

    cleaned = content
    cleaned = re.sub(r'\{%\s*layout[^%]*%\}', '', cleaned)
    cleaned = re.sub(r'\{%\s*endlayout\s*%\}', '', cleaned)
    cleaned = re.sub(r'\{%\s*block[^%]*%\}', '', cleaned)
    cleaned = re.sub(r'\{%\s*endblock\s*%\}', '', cleaned)
    cleaned = re.sub(r'\{%\s*cut[^%]*%\}', '', cleaned)
    cleaned = re.sub(r'\{%\s*endcut\s*%\}', '', cleaned)
    cleaned = re.sub(r':file\[([^\]]*)\]\([^)]*\)(?:\{[^}]*\})?', r'[Файл: \1]', cleaned)
    cleaned = re.sub(r'!\[([^\]]*)\]\([^)]*\)(?:\{[^}]*\})?', r'[Изображение: \1]', cleaned)
    cleaned = cleaned.replace('&nbsp;', ' ')
    cleaned = re.sub(r'\n{3,}', '\n\n', cleaned)

    md += cleaned.strip() + "\n"

    safe_name = slug.replace("/", "__")
    filepath = out_dir / f"{safe_name}.md"
    filepath.write_text(md, encoding="utf-8")
    return True


def main():
    parser = argparse.ArgumentParser(
        description="Синхронизация Yandex Wiki → wiki_export/",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Cookie-файл (.wiki_cookies.json) — JSON:
{
    "csrf_token": "...:...",
    "org_id": "7032304",
    "collab_org_id": "...",
    "cookie": "Session_id=...; ..."
}

Как получить cookies:
1. Открыть wiki.yandex.ru в браузере
2. DevTools (F12) → Network
3. Нажать на любой запрос к .gateway/root/wiki/*
4. Скопировать csrf_token из x-csrf-token, org_id из x-org-id,
   collab_org_id из x-collab-org-id, cookie из cookie
""",
    )
    parser.add_argument(
        "--cookie-file", "-c",
        type=Path,
        default=DEFAULT_COOKIE_FILE,
        help=f"Путь к JSON с cookies (по умолчанию {DEFAULT_COOKIE_FILE.name})",
    )
    parser.add_argument(
        "--out-dir", "-o",
        type=Path,
        default=DEFAULT_OUT_DIR,
        help=f"Папка для выгрузки (по умолчанию {DEFAULT_OUT_DIR})",
    )
    parser.add_argument(
        "--clean", action="store_true",
        help="Удалить старые .md файлы перед выгрузкой",
    )
    args = parser.parse_args()

    cookies = load_cookies(args.cookie_file)
    headers = make_headers(cookies)
    out_dir: Path = args.out_dir
    out_dir.mkdir(parents=True, exist_ok=True)

    if args.clean:
        for old in out_dir.glob("*.md"):
            old.unlink()
        print(f"Очищена папка {out_dir}")

    client = httpx.Client(timeout=30, headers=headers, follow_redirects=False)

    print("Поиск страниц...")
    slugs = discover_all_slugs(client)
    print(f"\nНайдено {len(slugs)} страниц")

    print(f"\nВыгрузка контента в {out_dir}...")
    fetched = 0
    empty = 0
    errors = 0
    for slug in sorted(slugs):
        ok = fetch_and_save(client, slug, out_dir)
        if ok:
            fetched += 1
        else:
            r = client.post(f"{BASE}/getPageDetails", json={
                "slug": slug, "fields": ["attributes"], "settings": {"lang": "ru"},
            })
            if r.status_code == 200:
                empty += 1
            else:
                errors += 1
        time.sleep(0.2)

    client.close()

    # Save slug list for WIKI_SLUGS env var
    content_slugs = []
    for md_file in sorted(out_dir.glob("*.md")):
        name = md_file.stem.replace("__", "/")
        content_slugs.append(name)

    slugs_file = out_dir / "_slugs.txt"
    slugs_file.write_text("\n".join(content_slugs), encoding="utf-8")

    print(f"\nГотово!")
    print(f"  Выгружено: {fetched} страниц с контентом")
    print(f"  Пустые разделы: {empty}")
    print(f"  Ошибки: {errors}")
    print(f"  Файлы: {out_dir}")
    print(f"  Список slug'ов: {slugs_file}")


if __name__ == "__main__":
    main()
