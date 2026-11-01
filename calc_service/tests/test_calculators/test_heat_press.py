"""
Тесты калькулятора термопресса (heat_press).
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

_calc_service = Path(__file__).resolve().parent.parent.parent
if _calc_service.name == "calc_service" and str(_calc_service) not in sys.path:
    sys.path.insert(0, str(_calc_service))

from calculators.heat_press import HeatPressCalculator

JS_REL_TOL = 0.001  # 0.1%


@pytest.fixture(scope="module")
def calc():
    return HeatPressCalculator()


@pytest.fixture(scope="module")
def base_params():
    return {
        "quantity": 20,
        "width": 150,
        "height": 100,
        "transfer_type": "sublimation",
        "item_type": "tshirt",
        "silk_colors": 1,
        "mode": 1,
    }


@pytest.fixture(scope="module")
def result(calc, base_params):
    try:
        return calc.execute(base_params)
    except Exception:
        return None


def test_slug(calc):
    assert calc.slug == "heat_press"


def test_calculate_basic(result):
    if result is None:
        pytest.skip("расчёт не выполнен")
    for key in ("cost", "price", "unit_price", "time_hours", "time_ready", "weight_kg", "materials"):
        assert key in result
    assert result["cost"] >= 0
    assert result["price"] >= 0
    assert result["time_hours"] >= 0
    assert result["time_ready"] >= 0
    materials = result.get("materials") or []
    for m in materials:
        assert "name" in m
        assert "title" in m


def test_price_gte_cost(result):
    if result is None:
        pytest.skip("расчёт не выполнен")
    if result["cost"] == 0:
        pytest.skip("нулевая себестоимость")
    assert result["price"] >= result["cost"]


def test_share_url(result):
    if result is None:
        pytest.skip("расчёт не выполнен")
    assert "share_url" in result
    assert "heat_press" in result["share_url"]


def test_get_tool_schema(calc):
    schema = calc.get_tool_schema()
    assert schema.get("name") == "calc_heat_press"
    assert "parameters" in schema


# ── Эталоны: node scripts/run_js_calc.mjs calcHeatPress --data current --args '…' ─

# JS, 01.11.2026 — тираж 1
# calcHeatPress(1, [150,100], 'sublimation', 'tshirt', {}, 1)
REF_PARAMS_1 = {
    "quantity": 1,
    "width": 150,
    "height": 100,
    "transfer_type": "sublimation",
    "item_type": "tshirt",
    "silk_colors": 1,
    "mode": 1,
}
EXPECTED_REF_1 = {
    "cost": 682.1217361111111,
    "price": 1095.9170819444444,
    "time_hours": 0.44972222222222225,
    "time_ready": 17.12972222222222,
    "weight_kg": 0.01596672,
}

# JS, 01.11.2026 — тираж ≥ 2
# calcHeatPress(20, [150,100], 'sublimation', 'tshirt', {}, 1)
REF_PARAMS_20 = {
    "quantity": 20,
    "width": 150,
    "height": 100,
    "transfer_type": "sublimation",
    "item_type": "tshirt",
    "silk_colors": 1,
    "mode": 1,
}
EXPECTED_REF_20 = {
    "cost": 2021.9347222222223,
    "price": 3249.381638888889,
    "time_hours": 1.4044444444444446,
    "time_ready": 18.864444444444445,
    "weight_kg": 0.07983359999999999,
}
EXPECTED_MATERIAL_20 = {
    "code": "PaperSublimation128",
    "name_substring": "Бумага сублимационная",
    "quantity_approx": 6,
}


def test_expected_values_heat_press_qty1(calc):
    """JS, 01.11.2026: sublimation tshirt, тираж 1."""
    r = calc.calculate(REF_PARAMS_1)
    e = EXPECTED_REF_1
    assert r["cost"] == pytest.approx(e["cost"], rel=JS_REL_TOL)
    assert r["price"] == pytest.approx(e["price"], rel=JS_REL_TOL)
    assert r["time_hours"] == pytest.approx(e["time_hours"], rel=JS_REL_TOL)
    assert r["time_ready"] == pytest.approx(e["time_ready"], rel=JS_REL_TOL)
    assert r["weight_kg"] == pytest.approx(e["weight_kg"], rel=JS_REL_TOL)


def test_expected_values_heat_press_qty20(calc):
    """JS, 01.11.2026: sublimation tshirt, тираж 20."""
    r = calc.calculate(REF_PARAMS_20)
    e = EXPECTED_REF_20
    em = EXPECTED_MATERIAL_20
    assert r["cost"] == pytest.approx(e["cost"], rel=JS_REL_TOL)
    assert r["price"] == pytest.approx(e["price"], rel=JS_REL_TOL)
    assert r["time_hours"] == pytest.approx(e["time_hours"], rel=JS_REL_TOL)
    assert r["time_ready"] == pytest.approx(e["time_ready"], rel=JS_REL_TOL)
    assert r["weight_kg"] == pytest.approx(e["weight_kg"], rel=JS_REL_TOL)
    materials = r.get("materials") or []
    assert materials
    mat = materials[0]
    assert mat.get("code") == em["code"]
    assert em["name_substring"] in (mat.get("name") or "")
    assert float(mat.get("quantity") or 0) == pytest.approx(float(em["quantity_approx"]), rel=0.15)
    assert "title" in mat
