from __future__ import annotations

from math import isclose

import pytest

from common.helpers import calc_weight, find_in_table
from common.currencies import parse_currency
from common.layout import layout_on_roll, layout_on_sheet
from common.markups import BASE_TIME_READY, get_margin


def test_find_in_table():
    table = [(10, 100), (50, 80), (100, 60)]

    assert find_in_table(table, 30) == 80  # обычный случай
    assert find_in_table(table, 5) == 100  # ниже первого порога
    assert find_in_table(table, 999) == 60  # выше последнего порога


def test_calc_weight_gsm3():
    # ПВХ 3 мм, лист 3050x2050, плотность 0.55 г/см³, 1 лист
    w_kg = calc_weight(
        quantity=1,
        density=0.55,
        thickness=3.0,
        size=[3050, 2050],
        density_unit="гсм3",
    )
    # Ожидаем ~10.3 кг (точнее около 10.3166)
    assert isclose(w_kg, 10.3, rel_tol=0.02)


def test_calc_weight_gm2():
    # Бумага 150 г/м², лист 1000x1000 мм (1 м²), 10 листов → 1.5 кг
    w_kg = calc_weight(
        quantity=10,
        density=150.0,
        thickness=0.0,
        size=[1000, 1000],
        density_unit="гм2",
    )
    assert isclose(w_kg, 1.5, rel_tol=1e-6)


def test_parse_currency_usd():
    assert parse_currency("$100") == 9500.0


def test_parse_currency_eur():
    assert parse_currency("€100") == 10000.0


def test_parse_currency_rub():
    assert parse_currency(750) == 750.0


def test_get_margin():
    assert get_margin("marginBadge") == pytest.approx(0.2)
    assert get_margin("marginButtonPins") == pytest.approx(-0.1)
    assert get_margin("marginDoesNotExist") == 0.0


def test_base_time_ready():
    assert BASE_TIME_READY == [24, 8, 1]


def test_layout_on_sheet():
    # Изделие 100x100 на листе 1000x500 → 10 колонок × 5 строк = 50 шт
    r = layout_on_sheet([100, 100], [1000, 500])
    assert r["num"] == 50
    assert r["cols"] == 10
    assert r["rows"] == 5


def test_layout_on_roll_basic():
    # Рулон 620 мм, изделие 100x150, нужно 25 шт.
    # По логике calcLayoutOnRoll из JS выбирается более экономичный вариант:
    # 4 в ряд, 7 рядов = 28 шт, длина = 7 * 100 = 700 мм.
    r = layout_on_roll(25, [100, 150], [620, 0])
    assert r["num"] == 25
    assert r["length"] == pytest.approx(700.0)

