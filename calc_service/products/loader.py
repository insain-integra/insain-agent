"""
Загрузчик продуктов из data/products.json.

Каждый продукт — обёртка над базовым калькулятором:
product_slug + title + base_calc_slug + defaults + keywords + disambiguation.
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

_DATA_DIR = Path(__file__).resolve().parent.parent / "data"
_PRODUCTS_FILE = _DATA_DIR / "products.json"


@dataclass
class ProductSpec:
    """Спецификация одного продукта (обёртка над калькулятором)."""

    product_slug: str
    title: str
    base_calc_slug: str
    url: str = ""
    category: str = ""
    defaults: Dict[str, Any] = field(default_factory=dict)
    keywords: List[str] = field(default_factory=list)
    disambiguation: str = ""
    available: bool = True

    def matches_query(self, query: str) -> bool:
        """Проверка совпадения запроса с ключевыми словами/заголовком."""
        q = query.lower().strip()
        if not q:
            return False
        if q in self.title.lower():
            return True
        return any(q in kw.lower() for kw in self.keywords)

    def to_router_entry(self) -> str:
        """Строка для индекса роутера: slug — title. disambiguation. keywords."""
        parts = [f"- {self.product_slug} — {self.title}"]
        if self.disambiguation:
            parts[0] += f". {self.disambiguation}"
        if self.keywords:
            kw = ", ".join(self.keywords[:6])
            parts[0] += f" [{kw}]"
        return parts[0]

    def to_api_dict(self) -> Dict[str, Any]:
        """Представление для API: включает defaults (нужны боту для промта исполнителя)."""
        return {
            "product_slug": self.product_slug,
            "title": self.title,
            "base_calc_slug": self.base_calc_slug,
            "category": self.category,
            "defaults": dict(self.defaults),
            "keywords": self.keywords,
            "disambiguation": self.disambiguation,
            "available": self.available,
        }

    def to_api_dict_full(self) -> Dict[str, Any]:
        """Полное представление для API (с defaults и url)."""
        d = self.to_api_dict()
        d["url"] = self.url
        d["defaults"] = dict(self.defaults)
        return d


def load_products(path: Optional[Path] = None) -> Dict[str, ProductSpec]:
    """
    Загрузить продукты из JSON.

    Возвращает dict: product_slug → ProductSpec.
    Продукты с дублирующимися slug — предупреждение, последний побеждает.
    """
    fpath = path or _PRODUCTS_FILE
    if not fpath.is_file():
        logger.warning("Файл продуктов не найден: %s", fpath)
        return {}

    try:
        raw = json.loads(fpath.read_text(encoding="utf-8"))
    except Exception as e:
        logger.error("Ошибка чтения products.json: %s", e)
        return {}

    if not isinstance(raw, list):
        logger.error("products.json должен быть массивом, получено: %s", type(raw).__name__)
        return {}

    products: Dict[str, ProductSpec] = {}
    for item in raw:
        if not isinstance(item, dict):
            continue
        slug = str(item.get("product_slug") or "").strip()
        if not slug:
            logger.warning("Продукт без product_slug пропущен: %s", item.get("title"))
            continue
        base = str(item.get("base_calc_slug") or "").strip()
        if not base:
            logger.warning("Продукт %s: base_calc_slug пустой, пропущен", slug)
            continue
        if slug in products:
            logger.warning("Дублирующийся product_slug: %s", slug)

        products[slug] = ProductSpec(
            product_slug=slug,
            title=str(item.get("title") or slug),
            base_calc_slug=base,
            url=str(item.get("url") or ""),
            category=str(item.get("category") or ""),
            defaults=dict(item.get("defaults") or {}),
            keywords=list(item.get("keywords") or []),
            disambiguation=str(item.get("disambiguation") or ""),
            available=bool(item.get("available", True)),
        )

    logger.info("Загружено продуктов: %s (доступных: %s)", len(products), sum(1 for p in products.values() if p.available))
    return products
