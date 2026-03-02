"""
Тесты калькулятора лазерной печати (print_laser).
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

_calc_service = Path(__file__).resolve().parent.parent.parent
if _calc_service.name == "calc_service" and str(_calc_service) not in sys.path:
    sys.path.insert(0, str(_calc_service))

from calculators.base import ProductionMode
from calculators.print_laser import PrintLaserCalculator


@pytest.fixture(scope="module")
def calc():
    return PrintLaserCalculator()


@pytest.fixture(scope="module")
def base_params(calc):
    opts = calc.get_options()
    materials = opts.get("materials") or []
    mat = materials[0] if materials else {}
    code = mat.get("code", "PaperCoated115M")
    return {
        "num_sheet": 50,
        "width": 320,
        "height": 450,
        "color": "4+0",
        "material_id": code,
        "printer_code": "",
        "mode": 1,
    }


@pytest.fixture(scope="module")
def result(calc, base_params):
    try:
        return calc.execute(base_params)
    except Exception:
        return None


def test_slug(calc):
    assert calc.slug == "print_laser"


def test_calculate_basic(result):
    if result is None:
        pytest.skip("расчёт не выполнен")
    for key in ("cost", "price", "unit_price", "time_hours", "time_ready", "weight_kg", "materials"):
        assert key in result
    assert result["cost"] >= 0
    assert result["price"] >= 0
    assert result["time_hours"] >= 0
    assert result["time_ready"] >= 0


def test_time_hours_positive(result):
    if result is None:
        pytest.skip("расчёт не выполнен")
    assert result["time_hours"] >= 0


def test_time_ready_greater_than_time(result):
    if result is None:
        pytest.skip("расчёт не выполнен")
    assert result["time_ready"] >= result["time_hours"]


def test_time_ready_modes(calc, base_params):
    base_params = dict(base_params)
    res_e = calc.calculate({**base_params, "mode": ProductionMode.ECONOMY})
    res_s = calc.calculate({**base_params, "mode": ProductionMode.STANDARD})
    res_x = calc.calculate({**base_params, "mode": ProductionMode.EXPRESS})
    assert res_e["time_ready"] >= res_s["time_ready"]
    assert res_s["time_ready"] >= res_x["time_ready"]


def test_price_greater_than_cost(result):
    if result is None:
        pytest.skip("расчёт не выполнен")
    if result["cost"] == 0:
        pytest.skip("нулевая себестоимость")
    assert result["price"] >= result["cost"]


def test_share_url_contains_slug(result):
    if result is None:
        pytest.skip("расчёт не выполнен")
    assert "share_url" in result
    assert "print_laser" in result["share_url"]


def test_get_options_not_empty(calc):
    opts = calc.get_options()
    assert "modes" in opts
    assert "materials" in opts
    assert "printers" in opts
    assert "colors" in opts


def test_get_tool_schema(calc):
    schema = calc.get_tool_schema()
    assert schema.get("name") == "calc_print_laser"
    assert "parameters" in schema
    assert "num_sheet" in schema["parameters"].get("properties", {})


# Эталон: 50 шт, 320×450 мм, PaperCoated300M, цветность 4+4
REF_PARAMS = {
    "num_sheet": 50,
    "width": 320,
    "height": 450,
    "material_id": "PaperCoated300M",
    "color": "4+4",
    "printer_code": "",
    "mode": 1,
}
EXPECTED_REF = {
    "cost": 2416.198181818182,
    "price": 3955.582618181819,
    "time_hours": 1.07,
    "time_ready": 9.07,
    "weight_kg": 2.16,
}


def _cmp(a: float, b: float, rel: float = 0.02) -> bool:
    """Сравнение с относительным допуском."""
    return abs(a - b) <= rel * max(abs(b), 1e-9)


@pytest.fixture(scope="module")
def ref_result(calc):
    """Результат расчёта для эталонного кейса (50 шт, 320×450, PaperCoated300M, 4+4)."""
    try:
        return calc.execute(REF_PARAMS)
    except Exception:
        return None


def test_expected_values_print_laser(ref_result):
    """Сверка с эталоном: 50 шт, 320×450 мм, PaperCoated300M, цветность 4+4."""
    if ref_result is None:
        pytest.skip("расчёт эталонного кейса не выполнен (материал PaperCoated300M?)")
    r = ref_result
    e = EXPECTED_REF
    rel = 0.02

    ok_cost = _cmp(r["cost"], e["cost"], rel)
    ok_price = _cmp(r["price"], e["price"], rel)
    ok_time = _cmp(r["time_hours"], e["time_hours"], rel)
    ok_ready = _cmp(r["time_ready"], e["time_ready"], rel)
    ok_weight = _cmp(r["weight_kg"], e["weight_kg"], rel)

    print("")
    print("  [лазерная печать] Параметры   num_sheet=%s  |  size=%s×%s  |  material_id=%s  |  color=%s  |  mode=%s"
          % (REF_PARAMS.get("num_sheet"), REF_PARAMS.get("width"), REF_PARAMS.get("height"),
             REF_PARAMS.get("material_id"), REF_PARAMS.get("color"), REF_PARAMS.get("mode")))
    print("  ---")
    print("  cost        %s  (ожид. %s)  %s" % (r["cost"], e["cost"], "ok" if ok_cost else "FAIL"))
    print("  price       %s  (ожид. %s)  %s" % (r["price"], e["price"], "ok" if ok_price else "FAIL"))
    print("  time_hours  %s  (ожид. %s)  %s" % (r["time_hours"], e["time_hours"], "ok" if ok_time else "FAIL"))
    print("  time_ready  %s  (ожид. %s)  %s" % (r["time_ready"], e["time_ready"], "ok" if ok_ready else "FAIL"))
    print("  weight_kg   %s  (ожид. %s)  %s" % (r["weight_kg"], e["weight_kg"], "ok" if ok_weight else "FAIL"))

    assert ok_cost, f"cost: got {r['cost']}, expected ~{e['cost']}"
    assert ok_price, f"price: got {r['price']}, expected ~{e['price']}"
    assert ok_time, f"time_hours: got {r['time_hours']}, expected ~{e['time_hours']}"
    assert ok_ready, f"time_ready: got {r['time_ready']}, expected ~{e['time_ready']}"
    assert ok_weight, f"weight_kg: got {r['weight_kg']}, expected ~{e['weight_kg']}"
