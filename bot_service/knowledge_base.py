"""
База знаний: кэш статей Wiki + поиск по ключевым словам.

Этап 1: простой keyword-based поиск по текстовым фрагментам.
Этап 2 (будущее): pgvector + эмбеддинги для семантического поиска.

Источники данных (приоритет):
1. Yandex Wiki API (если настроен WIKI_OAUTH_TOKEN)
2. Локальные markdown-файлы из wiki_export/

Настройки из .env:
    KB_REFRESH_HOURS — интервал обновления кэша (по умолчанию 6)
    WIKI_FALLBACK_DIR или KB_LOCAL_DIR — путь к локальным markdown-файлам
"""

from __future__ import annotations

import json
import logging
import os
import re
import threading
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from wiki_parser import WikiArticle, YandexWikiParser

logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parent.parent
_kb_dir_raw = (
    os.getenv("WIKI_FALLBACK_DIR", "").strip()
    or os.getenv("KB_LOCAL_DIR", "").strip()
    or ""
)
if _kb_dir_raw:
    _kb_dir_path = Path(_kb_dir_raw)
    KB_LOCAL_DIR = str(_kb_dir_path if _kb_dir_path.is_absolute() else PROJECT_ROOT / _kb_dir_path)
else:
    KB_LOCAL_DIR = str(PROJECT_ROOT / "wiki_export")
KB_CACHE_FILE = PROJECT_ROOT / "data" / "kb_cache.json"
KB_REFRESH_HOURS = int(os.getenv("KB_REFRESH_HOURS", "6") or "6")
KB_MAX_CONTEXT_CHARS = 6000


def _tokenize(text: str) -> List[str]:
    """Простая токенизация: lowercase, слова >= 2 символов."""
    return [w for w in re.findall(r"[а-яёa-z0-9]+", text.lower()) if len(w) >= 2]


def _snippet(text: str, query_tokens: List[str], max_len: int = 400) -> str:
    """Извлечь фрагмент текста вокруг первого совпадения с query."""
    text_lower = text.lower()
    best_pos = len(text)
    for tok in query_tokens:
        pos = text_lower.find(tok)
        if 0 <= pos < best_pos:
            best_pos = pos

    if best_pos >= len(text):
        return text[:max_len]

    start = max(0, best_pos - max_len // 4)
    end = min(len(text), start + max_len)
    snippet = text[start:end]
    if start > 0:
        snippet = "..." + snippet
    if end < len(text):
        snippet = snippet + "..."
    return snippet


class KnowledgeBase:
    """
    База знаний для LLM-агента.

    Поддерживает:
    - Загрузка из Yandex Wiki API
    - Загрузка из локальных .md файлов
    - Keyword-based поиск
    - Генерация контекста для LLM
    """

    def __init__(
        self,
        wiki_parser: Optional[YandexWikiParser] = None,
        local_dir: Optional[str] = None,
        cache_file: Optional[Path] = None,
    ):
        self._parser = wiki_parser or YandexWikiParser()
        self._local_dir = Path(local_dir or KB_LOCAL_DIR)
        self._cache_file = cache_file or KB_CACHE_FILE
        self._articles: List[WikiArticle] = []
        self._last_refresh: Optional[datetime] = None
        self._lock = threading.Lock()
        self._load_cache()

    @property
    def article_count(self) -> int:
        return len(self._articles)

    def _load_cache(self) -> None:
        """Загрузить кэш из файла, если он свежий."""
        if not self._cache_file.is_file():
            return
        try:
            data = json.loads(self._cache_file.read_text(encoding="utf-8"))
            refreshed = data.get("refreshed_at")
            if refreshed:
                refreshed_dt = datetime.fromisoformat(refreshed)
                now = datetime.now(timezone.utc).replace(tzinfo=None)
                if now - refreshed_dt > timedelta(hours=KB_REFRESH_HOURS * 2):
                    logger.info("KB cache устарел (%s), будет перезагружен.", refreshed)
                    return
                self._last_refresh = refreshed_dt

            articles_raw = data.get("articles") or []
            for a in articles_raw:
                updated = a.get("updated_at")
                updated_dt = None
                if updated:
                    try:
                        updated_dt = datetime.fromisoformat(updated)
                    except (ValueError, TypeError):
                        pass
                self._articles.append(WikiArticle(
                    slug=a.get("slug", ""),
                    title=a.get("title", ""),
                    content=a.get("content", ""),
                    updated_at=updated_dt,
                    tags=a.get("tags") or [],
                ))
            logger.info("KB: загружено %d статей из кэша.", len(self._articles))
        except Exception as e:
            logger.warning("KB: ошибка загрузки кэша: %s", e)

    def _save_cache(self) -> None:
        """Сохранить текущий кэш в файл."""
        try:
            self._cache_file.parent.mkdir(parents=True, exist_ok=True)
            data = {
                "refreshed_at": datetime.now(timezone.utc).replace(tzinfo=None).isoformat(),
                "articles": [a.to_dict() for a in self._articles],
            }
            self._cache_file.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
            logger.info("KB: кэш сохранён (%d статей).", len(self._articles))
        except Exception as e:
            logger.warning("KB: ошибка сохранения кэша: %s", e)

    def _load_local_files(self) -> List[WikiArticle]:
        """Загрузить статьи из локальных .md файлов."""
        articles: List[WikiArticle] = []
        if not self._local_dir.is_dir():
            return articles

        for md_file in sorted(self._local_dir.glob("**/*.md")):
            try:
                text = md_file.read_text(encoding="utf-8").strip()
                if not text:
                    continue
                rel_path = md_file.relative_to(self._local_dir)
                slug = str(rel_path).replace("\\", "/").replace(".md", "")
                slug = slug.replace("__", "/")
                title_match = re.match(r"^#\s+(.+)", text)
                title = title_match.group(1).strip() if title_match else slug
                articles.append(WikiArticle(
                    slug=slug,
                    title=title,
                    content=text,
                    updated_at=datetime.fromtimestamp(md_file.stat().st_mtime),
                ))
            except Exception as e:
                logger.warning("KB: ошибка чтения %s: %s", md_file, e)

        logger.info("KB: загружено %d статей из локальных файлов.", len(articles))
        return articles

    def refresh(self, force: bool = False) -> int:
        """
        Обновить базу знаний.

        Возвращает количество загруженных статей.
        """
        with self._lock:
            if not force and self._last_refresh:
                elapsed = datetime.now(timezone.utc).replace(tzinfo=None) - self._last_refresh
                if elapsed < timedelta(hours=KB_REFRESH_HOURS):
                    logger.debug("KB: кэш свежий (%.1f ч назад), пропуск.", elapsed.total_seconds() / 3600)
                    return len(self._articles)

            articles: List[WikiArticle] = []

            if self._parser.is_available():
                try:
                    wiki_articles = self._parser.fetch_all_with_content(limit=200)
                    articles.extend(wiki_articles)
                    logger.info("KB: загружено %d статей из Wiki API.", len(wiki_articles))
                except Exception as e:
                    logger.error("KB: ошибка загрузки из Wiki API: %s", e)

            local_articles = self._load_local_files()
            existing_slugs = {a.slug for a in articles}
            for la in local_articles:
                if la.slug not in existing_slugs:
                    articles.append(la)

            self._articles = articles
            self._last_refresh = datetime.now(timezone.utc).replace(tzinfo=None)
            self._save_cache()

            logger.info("KB: всего %d статей после обновления.", len(self._articles))
            return len(self._articles)

    def search(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """
        Keyword-based поиск по базе знаний.

        Возвращает список найденных статей с релевантностью.
        """
        if not self._articles:
            self.refresh()

        if not self._articles:
            return []

        query_tokens = _tokenize(query)
        if not query_tokens:
            return [{"slug": a.slug, "title": a.title, "score": 0} for a in self._articles[:limit]]

        scored: List[tuple] = []
        for article in self._articles:
            text = f"{article.title} {article.content}".lower()
            text_tokens = set(_tokenize(text))
            score = 0
            for qt in query_tokens:
                if qt in text_tokens:
                    score += 1
                    count = text.count(qt)
                    score += min(count, 5) * 0.2
                if qt in article.title.lower():
                    score += 2
                for tag in article.tags:
                    if qt in tag.lower():
                        score += 1.5
            if score > 0:
                scored.append((article, score))

        scored.sort(key=lambda x: x[1], reverse=True)

        results = []
        for article, score in scored[:limit]:
            snippet = _snippet(article.content, query_tokens, max_len=300)
            results.append({
                "slug": article.slug,
                "title": article.title,
                "snippet": snippet,
                "score": round(score, 2),
                "tags": article.tags,
            })

        return results

    def get_context(self, query: str, max_chars: int = KB_MAX_CONTEXT_CHARS) -> str:
        """
        Сформировать контекст из базы знаний для LLM.

        Возвращает текстовый блок с релевантными статьями.
        """
        results = self.search(query, limit=5)
        if not results:
            return ""

        chunks: List[str] = []
        total_chars = 0

        for r in results:
            slug = r["slug"]
            article = next((a for a in self._articles if a.slug == slug), None)
            if not article or not article.content:
                continue

            query_tokens = _tokenize(query)
            snippet = _snippet(article.content, query_tokens, max_len=1200)
            header = f"## {article.title}\n"
            chunk = header + snippet

            if total_chars + len(chunk) > max_chars:
                remaining = max_chars - total_chars
                if remaining > 100:
                    chunk = chunk[:remaining] + "..."
                    chunks.append(chunk)
                break

            chunks.append(chunk)
            total_chars += len(chunk)

        if not chunks:
            return ""

        return "Информация из базы знаний:\n\n" + "\n\n".join(chunks)

    def get_all_titles(self) -> List[Dict[str, str]]:
        """Список всех статей (slug + title) — для обзора содержимого KB."""
        if not self._articles:
            self.refresh()
        return [{"slug": a.slug, "title": a.title} for a in self._articles]
