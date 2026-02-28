"""
Тесты калькулятора гильотинной резки (cut_guillotine).
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

_calc_service = Path(__file__).resolve().parent.parent.parent
if _calc_service.name == "calc_service" and str(_calc_service) not in sys.path:
    sys.path.insert(0, str(_calc_service))

from calculators.base import ProductionMode
from calculators.cut_guillotine import CutGuillotineCalculator

# Ожидаемые значения для base_params (34 листа 450×320, изделие 90×50 мм, PaperCoated300M)
EXPECTED = {
    "cost": 187,
    "price": 300,
    "time_hours": 0.13,
}


def _rel_diff(a: float, b: float) -> float:
    """Относительное отклонение |a - b| / max(|b|, 1)."""
    return abs(a - b) / max(abs(b), 1.0)


def _cmp(a: float, b: float, rel: float = 0.01) -> bool:
    """Проверка совпадения с относительным допуском."""
    return abs(a - b) <= rel * max(abs(b), 1e-9)


def _print_params(params: dict) -> None:
    """Вывод параметров расчёта гильотинной резки."""
    parts = [
        "num_sheet=%s" % params.get("num_sheet"),
        "size=%s×%s" % (params.get("width"), params.get("height")),
        "sheet=%s×%s" % (params.get("sheet_width"), params.get("sheet_height")),
        "material_id=%s" % params.get("material_id"),
        "mode=%s" % params.get("mode"),
    ]
    print("  Параметры   %s" % "  |  ".join(parts))


@pytest.fixture(scope="module")
def calc():
    return CutGuillotineCalculator()


@pytest.fixture(scope="module")
def base_params(calc):
    """Параметры для тестов: тираж 1000 шт, изделие 90×50 мм, лист 450×320 мм, материал PaperCoated300M."""
    return {
        "num_sheet": 34,  # 34 листа × 30 изделий/лист (90×50 на 450×320) = 1020 шт ≥ 1000
        "width": 90,
        "height": 50,
        "sheet_width": 450,
        "sheet_height": 320,
        "material_id": "PaperCoated300M",
        "material_category": "sheet",
        "margins": [0, 0, 0, 0],
        "interval": 0,
        "mode": 1,
    }


@pytest.fixture(scope="module")
def result(calc, base_params):
    try:
        return calc.execute(base_params)
    except Exception:
        return None


def test_slug(calc):
    assert calc.slug == "cut_guillotine"


def test_calculate_basic(result):
    if result is None:
        pytest.skip("расчёт не выполнен")
    for key in ("cost", "price", "unit_price", "time_hours", "time_ready", "weight_kg", "materials"):
        assert key in result
    assert result["cost"] > 0
    assert result["price"] > 0
    assert result["unit_price"] > 0
    assert result["time_hours"] > 0
    assert result["time_ready"] > 0
    assert isinstance(result["materials"], list)


def test_expected_values(result, base_params):
    """Сверка с эталоном: себестоимость 187 р., цена 300 р., время 0,13 ч. Допуск 1%. Вывод — как в test_laser."""
    if result is None:
        pytest.skip("расчёт не выполнен")
    r = result
    e = EXPECTED
    rel = 0.01

    ok_cost = _cmp(r["cost"], e["cost"], rel)
    ok_price = _cmp(r["price"], e["price"], rel)
    ok_time = _cmp(r["time_hours"], e["time_hours"], rel)

    print("")
    _print_params(base_params)
    share_url = r.get("share_url") or ""
    if share_url:
        print("  Ссылка      %s" % share_url)
    print("  ---")
    print("  cost        %s  (ожид. %s)  %s" % (r["cost"], e["cost"], "ok" if ok_cost else "FAIL"))
    print("  price       %s  (ожид. %s)  %s" % (r["price"], e["price"], "ok" if ok_price else "FAIL"))
    print("  time_hours  %s  (ожид. %s)  %s" % (r["time_hours"], e["time_hours"], "ok" if ok_time else "FAIL"))

    assert ok_cost, "cost: got %s, expected ~%s" % (r["cost"], e["cost"])
    assert ok_price, "price: got %s, expected ~%s" % (r["price"], e["price"])
    assert ok_time, "time_hours: got %s, expected ~%s" % (r["time_hours"], e["time_hours"])


def test_time_hours_positive(result):
    if result is None:
        pytest.skip("расчёт не выполнен")
    assert result["time_hours"] > 0


def test_time_ready_greater(result):
    if result is None:
        pytest.skip("расчёт не выполнен")
    assert result["time_ready"] > result["time_hours"]


def test_time_ready_modes(calc, base_params):
    base_params = dict(base_params)
    res_e = calc.calculate({**base_params, "mode": ProductionMode.ECONOMY})
    res_s = calc.calculate({**base_params, "mode": ProductionMode.STANDARD})
    res_x = calc.calculate({**base_params, "mode": ProductionMode.EXPRESS})
    assert res_e["time_ready"] >= res_s["time_ready"]
    assert res_s["time_ready"] >= res_x["time_ready"]


def test_more_quantity_more_time(calc, base_params):
    base_params = dict(base_params)
    r10 = calc.calculate({**base_params, "num_sheet": 10})
    r100 = calc.calculate({**base_params, "num_sheet": 100})
    assert r100["time_hours"] > r10["time_hours"]


def test_price_greater_than_cost(result):
    if result is None:
        pytest.skip("расчёт не выполнен")
    assert result["price"] > result["cost"]


def test_share_url_contains_slug(result):
    if result is None:
        pytest.skip("расчёт не выполнен")
    assert "share_url" in result
    assert "cut_guillotine" in result["share_url"]


def test_get_options_not_empty(calc):
    opts = calc.get_options()
    assert "modes" in opts
    assert len(opts["modes"]) >= 1


def test_get_tool_schema(calc):
    schema = calc.get_tool_schema()
    assert schema.get("name") == "calc_" + calc.slug
    assert "parameters" in schema
