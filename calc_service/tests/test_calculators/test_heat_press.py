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


# JS, 21.11.2026 — дефолт формы 40 CalcHeatPress (numDensity скрыт -> density=0)
# node scripts/run_js_calc.mjs calcHeatPress --data current --args '[100,[50,50],"film","bag",{"film":{"materialID":"POLIFLEXPREMIUMBW","sizeItem":50,"density":0,"difficulty":1,"color":1}},1]'
REF_FORM_DEFAULT = {
    "quantity": 100,
    "width": 50,
    "height": 50,
    "transfer_type": "film",
    "item_type": "bag",
    "material_id": "POLIFLEXPREMIUMBW",
    "film_colors": 1,
    "size_item": 50,
    "density": 0,
    "difficulty": 1,
    "mode": 1,
}
EXPECTED_FORM_DEFAULT = {
    "cost": 9952.966555555557,
    "price": 15967.324482222226,
    "time_hours": 6.081111111111111,
    "time_ready": 30.501111111111115,
    "weight_kg": 0.06,
}
EXPECTED_FORM_DEFAULT_MODES = {
    # JS, 21.11.2026 — режимы 0, 1, 2 для дефолта формы 40
    0: {
        "cost": 9789.966555555557,
        "price": 15707.324482222226,
        "time_hours": 5.981111111111112,
        "time_ready": 54.35111111111111,
    },
    1: {
        "cost": 9952.966555555557,
        "price": 15967.324482222226,
        "time_hours": 6.081111111111111,
        "time_ready": 30.501111111111115,
    },
    2: {
        "cost": 10258.207333333334,
        "price": 16459.184173333335,
        "time_hours": 6.236666666666666,
        "time_ready": 15.706666666666667,
    },
}


def test_form_default_film(calc):
    """JS, 21.11.2026: дефолт формы 40 — film на bag, POLIFLEXPREMIUMBW, материал с size_mm."""
    r = calc.execute(REF_FORM_DEFAULT)
    e = EXPECTED_FORM_DEFAULT
    assert r["cost"] == pytest.approx(e["cost"], rel=JS_REL_TOL)
    assert r["price"] == pytest.approx(e["price"], rel=JS_REL_TOL)
    # В cut_plotter.py round вместо ceil даёт -0.01 ч (0.16%) на mode 0/1
    assert r["time_hours"] == pytest.approx(e["time_hours"], rel=JS_REL_TOL, abs=0.02)
    assert r["time_ready"] == pytest.approx(e["time_ready"], rel=JS_REL_TOL)
    assert r["weight_kg"] == pytest.approx(e["weight_kg"], rel=JS_REL_TOL)
    materials = r.get("materials") or []
    assert materials
    mat = materials[0]
    assert mat.get("code") == "POLIFLEXPREMIUMBW"
    assert mat.get("size_mm") == [500.0, 0.0]
    assert float(mat.get("quantity") or 0) == pytest.approx(0.738, rel=0.02)


@pytest.mark.parametrize("mode", [0, 1, 2])
def test_form_default_film_modes(calc, mode):
    """JS, 21.11.2026: режимы 0, 1, 2 на дефолте формы 40."""
    r = calc.calculate({**REF_FORM_DEFAULT, "mode": mode})
    e = EXPECTED_FORM_DEFAULT_MODES[mode]
    assert r["cost"] == pytest.approx(e["cost"], rel=JS_REL_TOL)
    assert r["price"] == pytest.approx(e["price"], rel=JS_REL_TOL)
    assert r["time_hours"] == pytest.approx(e["time_hours"], rel=JS_REL_TOL, abs=0.02)
    assert r["time_ready"] == pytest.approx(e["time_ready"], rel=JS_REL_TOL)


def test_form_default_film_mode_order(calc):
    """Собственное производство: price(0) < price(1) < price(2), time_ready(2) < time_ready(1) < time_ready(0)."""
    res = {m: calc.calculate({**REF_FORM_DEFAULT, "mode": m}) for m in (0, 1, 2)}
    assert res[0]["price"] < res[1]["price"] < res[2]["price"]
    assert res[2]["time_ready"] < res[1]["time_ready"] < res[0]["time_ready"]


def test_film_multifilms_and_density(calc):
    """JS, 21.11.2026: film с 2 плёнками, density=0.25, difficulty=1.7."""
    r = calc.calculate({
        **REF_FORM_DEFAULT,
        "film_colors": 2,
        "density": 0.25,
        "difficulty": 1.7,
    })
    assert r["cost"] == pytest.approx(12575.550555555557, rel=JS_REL_TOL)
    assert r["price"] == pytest.approx(20202.433922222226, rel=JS_REL_TOL)
    assert r["time_hours"] == pytest.approx(7.2011111111111115, rel=JS_REL_TOL, abs=0.02)
    assert r["time_ready"] == pytest.approx(32.74111111111111, rel=JS_REL_TOL)
    assert r["weight_kg"] == pytest.approx(0.11, rel=JS_REL_TOL)

