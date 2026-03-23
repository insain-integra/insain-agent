"""Тесты реестра продуктов (products.json, loader, products/__init__)."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

_calc_service = Path(__file__).resolve().parent.parent
if str(_calc_service) not in sys.path:
    sys.path.insert(0, str(_calc_service))

from calculators import CALCULATORS
from products import get_product, get_products_for_calc, list_available
from products.loader import ProductSpec, _PRODUCTS_FILE, load_products


def test_load_products():
    """products.json загружается без ошибок, возвращается непустой словарь."""
    products = load_products()
    assert isinstance(products, dict)
    assert len(products) > 0


def test_all_products_have_required_fields():
    """У каждого продукта есть product_slug, title, base_calc_slug."""
    for p in load_products().values():
        assert p.product_slug
        assert isinstance(p.product_slug, str)
        assert p.title
        assert isinstance(p.title, str)
        assert p.base_calc_slug
        assert isinstance(p.base_calc_slug, str)


def test_product_slugs_unique():
    """В исходном JSON нет дублирующихся product_slug (последний не должен перетирать)."""
    raw = json.loads(_PRODUCTS_FILE.read_text(encoding="utf-8"))
    assert isinstance(raw, list)
    slugs = [str(item.get("product_slug") or "").strip() for item in raw if isinstance(item, dict)]
    slugs = [s for s in slugs if s]
    assert len(slugs) == len(set(slugs)), f"дубликаты: {[s for s in slugs if slugs.count(s) > 1]}"


def test_base_calc_slugs_exist():
    """Каждый base_calc_slug есть в CALCULATORS."""
    for p in load_products().values():
        assert p.base_calc_slug in CALCULATORS, (
            f"продукт {p.product_slug}: неизвестный калькулятор {p.base_calc_slug!r}"
        )


def test_get_product_valid():
    """get_product('print_sheet') возвращает ожидаемый продукт."""
    p = get_product("print_sheet")
    assert isinstance(p, ProductSpec)
    assert p.product_slug == "print_sheet"
    assert p.base_calc_slug == "print_sheet"
    assert "листов" in p.title.lower() or "Листов" in p.title


def test_get_product_invalid():
    """get_product для несуществующего slug — KeyError."""
    with pytest.raises(KeyError, match="nonexistent"):
        get_product("nonexistent")


def test_get_products_for_calc():
    """Несколько продуктов с base_calc_slug 'badge'."""
    items = get_products_for_calc("badge")
    assert len(items) >= 2
    assert all(p.base_calc_slug == "badge" for p in items)


def test_list_available():
    """Все записи list_available() имеют available=True."""
    for p in list_available():
        assert p.available is True


def test_product_to_router_entry():
    """to_router_entry() — непустая строка, содержит slug и title."""
    p = get_product("print_sheet")
    line = p.to_router_entry()
    assert isinstance(line, str)
    assert len(line.strip()) > 0
    assert "print_sheet" in line
    assert p.title in line


def test_product_matches_query():
    """matches_query('бейдж') для бейдж-продуктов возвращает True."""
    badge_products = get_products_for_calc("badge")
    assert badge_products
    matched = [p for p in badge_products if p.matches_query("бейдж")]
    assert matched, "ожидалось хотя бы одно совпадение по ключевому слову «бейдж»"


def test_product_to_api_dict():
    """to_api_dict() содержит ожидаемые ключи."""
    p = get_product("print_sheet")
    d = p.to_api_dict()
    for key in (
        "product_slug",
        "title",
        "base_calc_slug",
        "category",
        "defaults",
        "keywords",
        "disambiguation",
        "available",
    ):
        assert key in d
    assert isinstance(d["defaults"], dict)


def test_product_categories():
    """Не меньше 5 уникальных значений category среди всех продуктов."""
    cats = {p.category for p in load_products().values() if p.category}
    assert len(cats) >= 5
