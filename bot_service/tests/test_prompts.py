"""Тесты промптов роутера и калькулятора (prompts.py)."""

from __future__ import annotations

import sys
from pathlib import Path

_bot_service = Path(__file__).resolve().parent.parent
if str(_bot_service) not in sys.path:
    sys.path.insert(0, str(_bot_service))

from prompts import (
    build_calc_system_prompt,
    build_calc_system_prompt_full,
    build_product_categories,
    build_product_index,
    build_router_system_prompt,
)


def test_build_product_index():
    """Индекс продуктов содержит slug и title доступных продуктов."""
    products = [
        {
            "product_slug": "foo_bar",
            "title": "Тестовый продукт",
            "available": True,
            "keywords": ["a", "b"],
        }
    ]
    text = build_product_index(products)
    assert "foo_bar" in text
    assert "Тестовый продукт" in text


def test_build_product_categories():
    """Категории сгруппированы по меткам (не пустая строка для известных category)."""
    products = [
        {"product_slug": "p1", "title": "Листовка А4", "category": "print", "available": True},
        {"product_slug": "p2", "title": "Бейдж", "category": "badges", "available": True},
    ]
    text = build_product_categories(products)
    assert "Печатная продукция" in text
    assert "Бейджи и значки" in text
    assert "Листовка А4" in text
    assert "Бейдж" in text


def test_build_router_system_prompt_contains_disambiguation():
    """Роутер содержит блок различения похожих продуктов."""
    prompt = build_router_system_prompt("- demo — Demo")
    assert "РАЗЛИЧЕНИЕ ПОХОЖИХ ПРОДУКТОВ" in prompt


def test_build_calc_system_prompt_algorithmic():
    """Промпт расчёта содержит пошаговый алгоритм."""
    text = build_calc_system_prompt(
        slug="laser",
        tool_name="calc_laser",
        calculator_description="Лазер",
    )
    assert "ПОШАГОВЫЙ АЛГОРИТМ" in text
    assert "ШАГ 1" in text


def test_build_calc_system_prompt_with_product_context():
    """С контекстом продукта появляются заголовок и DEFAULTS."""
    text = build_calc_system_prompt(
        slug="badge",
        tool_name="calc_badge",
        product_title="Бейджи с УФ-печатью",
        product_defaults={"quantity": 100, "width": 50},
        product_disambiguation="Уточнение для модели.",
    )
    assert "Бейджи с УФ-печатью" in text
    assert "DEFAULTS" in text
    assert "quantity = 100" in text
    assert "width = 50" in text
    assert "Уточнение для модели." in text


def test_build_calc_system_prompt_full_with_products():
    """Полный промпт с продуктами — блок категорий продукции из продуктов."""
    products = [
        {"product_slug": "x", "title": "Календарь настенный", "category": "calendar", "available": True},
    ]
    text = build_calc_system_prompt_full([], products=products)
    assert "КАТЕГОРИИ ПРОДУКЦИИ" in text
    assert "Календари" in text
    assert "Календарь настенный" in text


def test_build_calc_system_prompt_full_fallback():
    """Без списка продуктов — старый формат списка калькуляторов (имя и slug в скобках)."""
    calculators = [
        {"slug": "laser", "name": "Лазерная резка"},
    ]
    text = build_calc_system_prompt_full(calculators, products=None)
    assert "КАТЕГОРИИ ПРОДУКЦИИ" in text
    assert "Лазерная резка (laser)" in text
