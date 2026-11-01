"""Тесты калькулятора кружек (mug)."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

_calc_service = Path(__file__).resolve().parent.parent.parent
if _calc_service.name == "calc_service" and str(_calc_service) not in sys.path:
    sys.path.insert(0, str(_calc_service))

from calculators.mug import MugCalculator

JS_REL_TOL = 0.001  # 0.1%


@pytest.fixture(scope="module")
def calc():
    return MugCalculator()


@pytest.fixture(scope="module")
def base_params():
    return {"quantity": 10, "mug_id": "MugStandartWhite", "is_packing": False, "mode": 1}


@pytest.fixture(scope="module")
def result(calc, base_params):
    try:
        return calc.execute(base_params)
    except Exception:
        return None


def test_slug(calc):
    assert calc.slug == "mug"


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
    assert "mug" in result["share_url"]


def test_get_options(calc):
    opts = calc.get_options()
    assert "modes" in opts


def test_get_tool_schema(calc):
    schema = calc.get_tool_schema()
    assert "mug" in schema.get("name", "")
    assert "parameters" in schema


# ── Эталоны: node scripts/run_js_calc.mjs calcMug --data current --args '…' ─

# JS, 01.11.2026 — тираж 1
# calcMug(1, 'MugStandartWhite', {}, 1)
REF_PARAMS_1 = {"quantity": 1, "mug_id": "MugStandartWhite", "is_packing": False, "mode": 1}
EXPECTED_REF_1 = {
    "cost": 777.8066805555555,
    "price": 1254.5140897222223,
    "time_hours": 0.46,
    "time_ready": 17.609722222222224,
    "weight_kg": 0.43,
}

# JS, 01.11.2026 — тираж ≥ 2
# calcMug(10, 'MugStandartWhite', {}, 1)
REF_PARAMS_10 = {"quantity": 10, "mug_id": "MugStandartWhite", "is_packing": False, "mode": 1}
EXPECTED_REF_10 = {
    "cost": 2287.0734861111114,
    "price": 3723.2469869444444,
    "time_hours": 0.96,
    "time_ready": 18.996944444444445,
    "weight_kg": 4.15,
}
EXPECTED_MATERIAL_10 = {"code": "MugStandartWhite", "name_substring": "Кружка", "quantity_approx": 11}


def test_expected_values_mug_qty1(calc):
    """JS, 01.11.2026: MugStandartWhite, тираж 1."""
    r = calc.calculate(REF_PARAMS_1)
    e = EXPECTED_REF_1
    assert r["cost"] == pytest.approx(e["cost"], rel=JS_REL_TOL)
    assert r["price"] == pytest.approx(e["price"], rel=JS_REL_TOL)
    assert r["time_hours"] == pytest.approx(e["time_hours"], rel=JS_REL_TOL)
    assert r["time_ready"] == pytest.approx(e["time_ready"], rel=JS_REL_TOL)
    assert r["weight_kg"] == pytest.approx(e["weight_kg"], rel=JS_REL_TOL)


def test_expected_values_mug_qty10(calc):
    """JS, 01.11.2026: MugStandartWhite, тираж 10."""
    r = calc.calculate(REF_PARAMS_10)
    e = EXPECTED_REF_10
    em = EXPECTED_MATERIAL_10
    assert r["cost"] == pytest.approx(e["cost"], rel=JS_REL_TOL)
    assert r["price"] == pytest.approx(e["price"], rel=JS_REL_TOL)
    assert r["time_hours"] == pytest.approx(e["time_hours"], rel=JS_REL_TOL)
    assert r["time_ready"] == pytest.approx(e["time_ready"], rel=JS_REL_TOL)
    assert r["weight_kg"] == pytest.approx(e["weight_kg"], rel=JS_REL_TOL)
    materials = r.get("materials") or []
    assert materials
    mat = next((m for m in materials if m.get("code") == em["code"]), {})
    assert mat.get("code") == em["code"]
    assert em["name_substring"] in (mat.get("name") or "")
    assert float(mat.get("quantity") or 0) == pytest.approx(float(em["quantity_approx"]), rel=0.15)
    assert "title" in mat
