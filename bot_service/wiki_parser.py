"""
Парсер статей из Yandex Wiki API v1.

Загружает статьи из Wiki организации, парсит wiki-разметку в чистый текст.
Используется knowledge_base.py для обновления кэша.

Yandex Wiki API:
    GET /v1/pages?slug=<slug>&fields=content,attributes
    Заголовки: Authorization: OAuth <token>, X-Org-Id: <org_id>
    Нет эндпоинта для листинга всех страниц — нужен список slug'ов.

Настройки из .env:
    WIKI_OAUTH_TOKEN  — OAuth-токен Yandex
    WIKI_ORG_ID       — ID организации в Yandex 360
    WIKI_BASE_URL     — (опционально) базовый URL API
    WIKI_SLUGS        — (опционально) slug'и страниц через запятую
"""

from __future__ import annotations

import html as html_mod
import logging
import os
import re
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import httpx


def _load_env() -> None:
    _env_path = Path(__file__).resolve().parent.parent / ".env"
    if not _env_path.is_file():
        return
    try:
        from dotenv import load_dotenv
        load_dotenv(_env_path)
    except ImportError:
        with open(_env_path, encoding="utf-8", errors="ignore") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, _, v = line.partition("=")
                    k, v = k.strip(), v.strip().strip("'\"").strip()
                    if k and k not in os.environ:
                        os.environ[k] = v


_load_env()

logger = logging.getLogger(__name__)

WIKI_BASE_URL = (
    os.getenv("WIKI_BASE_URL", "").strip()
    or os.getenv("YANDEX_WIKI_BASE_URL", "").strip()
    or "https://api.wiki.yandex.net"
).rstrip("/")
WIKI_TOKEN = (
    os.getenv("WIKI_OAUTH_TOKEN", "").strip()
    or os.getenv("YANDEX_WIKI_TOKEN", "").strip()
)
WIKI_ORG_ID = (
    os.getenv("WIKI_ORG_ID", "").strip()
    or os.getenv("YANDEX_WIKI_ORG_ID", "").strip()
)
WIKI_TIMEOUT = 30.0

WIKI_SLUGS_RAW = os.getenv("WIKI_SLUGS", "").strip()
WIKI_SLUGS: List[str] = [s.strip() for s in WIKI_SLUGS_RAW.split(",") if s.strip()] if WIKI_SLUGS_RAW else []


@dataclass
class WikiArticle:
    """Одна статья из Wiki."""
    slug: str
    title: str
    content: str
    updated_at: Optional[datetime] = None
    tags: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "slug": self.slug,
            "title": self.title,
            "content": self.content,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "tags": self.tags,
        }


def _strip_html(raw: str) -> str:
    """Убрать HTML-теги, декодировать entities, нормализовать пробелы."""
    text = re.sub(r"<br\s*/?>", "\n", raw, flags=re.IGNORECASE)
    text = re.sub(r"</(p|div|h[1-6]|li|tr)>", "\n", text, flags=re.IGNORECASE)
    text = re.sub(r"<[^>]+>", "", text)
    text = html_mod.unescape(text)
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def _strip_wiki_markup(raw: str) -> str:
    """Очистка wiki-разметки Yandex Wiki (wysiwyg-диалект)."""
    text = re.sub(r"\{%\s*layout[^%]*%\}", "", raw)
    text = re.sub(r"\{%\s*endlayout\s*%\}", "", text)
    text = re.sub(r"\{%\s*block[^%]*%\}", "", text)
    text = re.sub(r"\{%\s*endblock\s*%\}", "", text)
    text = re.sub(r"\{\{cut\s.*?\}\}", "", text)
    text = re.sub(r"\{\{/cut\}\}", "", text)
    text = re.sub(r"\[\[(.+?)\|(.+?)\]\]", r"\2", text)
    text = re.sub(r"\[\[(.+?)\]\]", r"\1", text)
    text = re.sub(r"!\[.*?\]\(.*?\)", "", text)
    text = re.sub(r"\[(.+?)\]\(.*?\)", r"\1", text)
    text = re.sub(r"\[(.+?)\]\{.*?\}", r"\1", text)
    text = re.sub(r"%%.*?%%", "", text, flags=re.DOTALL)
    text = re.sub(r"```.*?```", "", text, flags=re.DOTALL)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


class YandexWikiParser:
    """
    Клиент для Yandex Wiki API v1.

    API не имеет эндпоинта для листинга всех страниц.
    Используется список slug'ов (из WIKI_SLUGS в .env или передан явно).
    Для каждого slug делается GET /v1/pages?slug=<slug>&fields=content,attributes.
    """

    def __init__(
        self,
        token: Optional[str] = None,
        org_id: Optional[str] = None,
        base_url: Optional[str] = None,
        slugs: Optional[List[str]] = None,
        timeout: float = WIKI_TIMEOUT,
    ):
        self.token = (token or WIKI_TOKEN).strip()
        self.org_id = (org_id or WIKI_ORG_ID).strip()
        self.base_url = (base_url or WIKI_BASE_URL).rstrip("/")
        self.slugs = slugs if slugs is not None else list(WIKI_SLUGS)
        self.timeout = timeout

    def is_available(self) -> bool:
        return bool(self.token and self.org_id)

    def _headers(self) -> Dict[str, str]:
        return {
            "Authorization": f"OAuth {self.token}",
            "X-Org-Id": self.org_id,
            "Accept": "application/json",
        }

    def fetch_page(self, slug: str) -> Optional[WikiArticle]:
        """
        Получить одну страницу с контентом.

        GET /v1/pages?slug=<slug>&fields=content,attributes
        """
        if not self.is_available():
            return None

        url = f"{self.base_url}/v1/pages"
        params = {"slug": slug, "fields": "content,attributes"}

        try:
            with httpx.Client(timeout=self.timeout) as client:
                r = client.get(url, headers=self._headers(), params=params)
                r.raise_for_status()
                item = r.json()
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                logger.debug("Wiki page not found: %s", slug)
            else:
                logger.warning("Wiki API error (page %s): %s", slug, e.response.status_code)
            return None
        except Exception as e:
            logger.exception("Wiki fetch_page(%s) error: %s", slug, e)
            return None

        title = item.get("title") or slug

        raw_content = item.get("content") or ""
        if "<" in raw_content:
            body_text = _strip_html(raw_content)
        else:
            body_text = raw_content
        body_text = _strip_wiki_markup(body_text)

        attrs = item.get("attributes") or {}
        updated = attrs.get("modified_at")
        updated_dt = None
        if updated:
            try:
                updated_dt = datetime.fromisoformat(updated.replace("Z", "+00:00"))
            except (ValueError, AttributeError):
                pass

        keywords = attrs.get("keywords") or []

        return WikiArticle(
            slug=slug,
            title=title,
            content=body_text,
            updated_at=updated_dt,
            tags=keywords,
        )

    def fetch_pages(self, limit: int = 200) -> List[WikiArticle]:
        """
        Получить все страницы из списка slug'ов (без контента).

        Yandex Wiki API не имеет листинга — используем self.slugs.
        """
        if not self.is_available():
            logger.warning("YandexWikiParser: токен или org_id не заданы, пропуск.")
            return []

        if not self.slugs:
            logger.info("YandexWikiParser: список WIKI_SLUGS пуст, нечего загружать.")
            return []

        articles: List[WikiArticle] = []
        with httpx.Client(timeout=self.timeout) as client:
            for slug in self.slugs[:limit]:
                try:
                    r = client.get(
                        f"{self.base_url}/v1/pages",
                        headers=self._headers(),
                        params={"slug": slug},
                    )
                    if r.status_code != 200:
                        continue
                    item = r.json()
                    title = item.get("title") or slug
                    articles.append(WikiArticle(slug=slug, title=title, content=""))
                except Exception as e:
                    logger.debug("Wiki fetch_pages skip %s: %s", slug, e)

        logger.info("Загружено %d страниц из Wiki (без контента).", len(articles))
        return articles

    def fetch_all_with_content(self, limit: int = 200) -> List[WikiArticle]:
        """Загрузить все страницы из WIKI_SLUGS с контентом."""
        if not self.is_available():
            logger.warning("YandexWikiParser: не настроен, пропуск.")
            return []

        if not self.slugs:
            logger.info("YandexWikiParser: WIKI_SLUGS пуст.")
            return []

        result: List[WikiArticle] = []
        for slug in self.slugs[:limit]:
            article = self.fetch_page(slug)
            if article and article.content:
                result.append(article)
                logger.debug("Wiki page loaded: %s (%d chars)", slug, len(article.content))
            else:
                logger.debug("Wiki page empty or not found: %s", slug)

        logger.info("Загружено %d страниц с контентом из Wiki.", len(result))
        return result
