"""
Реестр продуктов (обёртки над калькуляторами).

Продукт = пользовательская сущность на сайте insain.ru.
Несколько продуктов могут использовать один и тот же базовый калькулятор
с разными defaults и контекстом (ключевые слова, disambiguation, категория).

Используется агентом для маршрутизации: роутер выбирает product_slug,
исполнитель получает base_calc_slug + defaults + промт-контекст.
"""

from __future__ import annotations

from typing import Dict, List, Optional

from .loader import load_products, ProductSpec

ALL_PRODUCTS: Dict[str, ProductSpec] = load_products()


def get_product(product_slug: str) -> ProductSpec:
    """Получить продукт по slug. KeyError если не найден."""
    if product_slug not in ALL_PRODUCTS:
        raise KeyError(f"Неизвестный продукт: {product_slug!r}")
    return ALL_PRODUCTS[product_slug]


def get_products_for_calc(calc_slug: str) -> List[ProductSpec]:
    """Все продукты, использующие данный базовый калькулятор."""
    return [p for p in ALL_PRODUCTS.values() if p.base_calc_slug == calc_slug]


def list_available() -> List[ProductSpec]:
    """Только доступные продукты (available=True)."""
    return [p for p in ALL_PRODUCTS.values() if p.available]


def list_all() -> List[ProductSpec]:
    """Все продукты включая недоступные."""
    return list(ALL_PRODUCTS.values())
