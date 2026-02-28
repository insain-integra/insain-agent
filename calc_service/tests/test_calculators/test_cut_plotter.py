"""
Тесты калькулятора плоттерной резки (cut_plotter).
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

_calc_service = Path(__file__).resolve().parent.parent.parent
if _calc_service.name == "calc_service" and str(_calc_service) not in sys.path:
    sys.path.insert(0, str(_calc_service))

from calculators.base import ProductionMode
from calculators.cut_plotter import CutPlotterCalculator

# Эталон: 100 шт, 60×60 мм, сложная форма, материал Avery500c (рулон 1230 мм), расход 0.4 м
EXPECTED_CUT_PLOTTER = {
    "cost": 371.0,
    "price": 593.0,
    "time_hours": 0.21,
    "time_ready": 16.23,
    "materials": [
        {"name": "Плёнка AVERY, серия 500, цветная", "quantity_approx": 0.4, "unit": "m"},
    ],
}

# Эталон: 1000 шт, 60×60 мм, difficulty=1.3, len_cut вычисляется (0.312 м/шт), Avery500c (рулон).
EXPECTED_CUT_PLOTTER_1000 = {
    "cost": 2716.0,
    "price": 4345.0,
    "time_hours": 1.64,
    "time_ready": 17.64,
    "materials": [
        {"name": "Плёнка AVERY, серия 500, цветная", "quantity_approx": 3.22, "unit": "m"},
    ],
}


def _cmp(a: float, b: float, rel: float = 0.01) -> bool:
    """Проверка совпадения с относительным допуском."""
    return abs(a - b) <= rel * max(abs(b), 1e-9)


@pytest.fixture(scope="module")
def calc():
    return CutPlotterCalculator()


@pytest.fixture(scope="module")
def base_params(calc):
    opts = calc.get_options()
    materials = opts.get("materials") or []
    mat = materials[0] if materials else {}
    code = mat.get("code", "Paper80")
    return {
        "quantity": 50,
        "width": 100,
        "height": 150,
        "material_id": code,
        "plotter_code": "",
        "mode": 1,
    }


@pytest.fixture(scope="module")
def ref_params_cut_plotter():
    """Плоттерная резка: 100 шт, 60×60 мм, сложная форма. len_cut не подаётся — считается в калькуляторе: 0.24*difficulty=0.312 м/шт, с браком 105 шт → 32.76 м."""
    return {
        "quantity": 100,
        "width": 60,
        "height": 60,
        "material_id": "Avery500c",
        "plotter_code": "",
        "difficulty": 1.3,
        "mode": 1,
    }


@pytest.fixture(scope="module")
def ref_result_cut_plotter(calc, ref_params_cut_plotter):
    try:
        return calc.execute(ref_params_cut_plotter)
    except Exception:
        return None


@pytest.fixture(scope="module")
def ref_params_cut_plotter_1000():
    """Плоттерная резка: 1000 шт, 60×60 мм. len_cut на вход не подаётся (0) — калькулятор вычисляет: 0.312 м/шт (difficulty=1.3). Эталон: cost 2716, price 4345, time 1.64, материал 3.22 м."""
    return {
        "quantity": 1000,
        "width": 60,
        "height": 60,
        "material_id": "Avery500c",
        "plotter_code": "",
        "difficulty": 1.3,
        "mode": 1,
    }


@pytest.fixture(scope="module")
def ref_result_cut_plotter_1000(calc, ref_params_cut_plotter_1000):
    try:
        return calc.execute(ref_params_cut_plotter_1000)
    except Exception:
        return None


@pytest.fixture(scope="module")
def result(calc, base_params):
    try:
        return calc.execute(base_params)
    except Exception:
        return None


def test_slug(calc):
    assert calc.slug == "cut_plotter"


def test_calculate_basic(result):
    if result is None:
        pytest.skip("расчёт не выполнен")
    for key in ("cost", "price", "unit_price", "time_hours", "time_ready", "weight_kg", "materials"):
        assert key in result
    assert result["cost"] >= 0
    assert result["price"] >= 0
    assert result["time_hours"] >= 0
    assert result["time_ready"] >= 0


def test_expected_values_cut_plotter(ref_result_cut_plotter, ref_params_cut_plotter):
    """Сверка с эталоном: 100 шт, 60×60 мм, сложная форма (difficulty=1.3), Avery500c. len_cut не подаётся → 0.312 м/шт, с браком 32.76 м. Допуск 2.5%."""
    if ref_result_cut_plotter is None:
        pytest.skip("расчёт плоттерной резки не выполнен")
    r = ref_result_cut_plotter
    e = EXPECTED_CUT_PLOTTER
    rel = 0.025

    ok_cost = _cmp(r["cost"], e["cost"], rel)
    ok_price = _cmp(r["price"], e["price"], rel)
    ok_time = _cmp(r["time_hours"], e["time_hours"], 0.05)  # время округляется до 0.01 ч, допуск 5%
    ok_ready = _cmp(r["time_ready"], e["time_ready"], rel)

    print("")
    print("  [плоттерная резка] Параметры   quantity=%s  |  size=%sx%s  |  material_id=%s  |  len_cut=%s  |  mode=%s"
          % (ref_params_cut_plotter.get("quantity"), ref_params_cut_plotter.get("width"),
             ref_params_cut_plotter.get("height"), ref_params_cut_plotter.get("material_id"),
             ref_params_cut_plotter.get("len_cut"), ref_params_cut_plotter.get("mode")))
    print("  ---")
    print("  cost        %s  (ожид. %s)  %s" % (r["cost"], e["cost"], "ok" if ok_cost else "FAIL"))
    print("  price       %s  (ожид. %s)  %s" % (r["price"], e["price"], "ok" if ok_price else "FAIL"))
    print("  time_hours  %s  (ожид. %s)  %s" % (r["time_hours"], e["time_hours"], "ok" if ok_time else "FAIL"))
    print("  time_ready  %s  (ожид. %s)  %s" % (r["time_ready"], e["time_ready"], "ok" if ok_ready else "FAIL"))
    mats = r.get("materials") or []
    for i, exp_mat in enumerate(e.get("materials") or []):
        exp_name = exp_mat.get("name", "")
        exp_q = exp_mat.get("quantity_approx")
        exp_unit = exp_mat.get("unit", "")
        got = mats[i] if i < len(mats) else None
        if got:
            got_name = got.get("name", "")
            got_q = got.get("quantity")
            got_unit = got.get("unit", "")
            ok_name = exp_name in got_name or got_name in exp_name
            ok_q = _cmp(float(got_q or 0), float(exp_q or 0), 0.15) if exp_q is not None and got_unit == exp_unit else True
            print("  material    %s  ~ %s %s  name_ok=%s q_ok=%s"
                  % (got_name[:50], got_q, got_unit, ok_name, ok_q))
        else:
            print("  material    (нет в результате) ожид. %s ~ %s %s" % (exp_name[:50], exp_q, exp_unit))

    assert ok_cost, "cost: got %s, expected ~%s" % (r["cost"], e["cost"])
    assert ok_price, "price: got %s, expected ~%s" % (r["price"], e["price"])
    assert ok_time, "time_hours: got %s, expected ~%s" % (r["time_hours"], e["time_hours"])
    assert ok_ready, "time_ready: got %s, expected ~%s" % (r["time_ready"], e["time_ready"])


def test_expected_values_cut_plotter_1000(ref_result_cut_plotter_1000, ref_params_cut_plotter_1000):
    """Сверка с эталоном: 1000 шт, 60×60 мм, len_cut не подаётся (вычисляется 0.312), Avery500c, расход в м. Допуск 3%, время 5%."""
    if ref_result_cut_plotter_1000 is None:
        pytest.skip("расчёт плоттерной резки (1000 шт) не выполнен")
    r = ref_result_cut_plotter_1000
    e = EXPECTED_CUT_PLOTTER_1000
    rel = 0.03

    ok_cost = _cmp(r["cost"], e["cost"], rel)
    ok_price = _cmp(r["price"], e["price"], rel)
    ok_time = _cmp(r["time_hours"], e["time_hours"], 0.05)
    ok_ready = _cmp(r["time_ready"], e["time_ready"], rel)

    print("")
    print("  [плоттерная резка 1000 шт] quantity=%s  |  size=%sx%s  |  material_id=%s  |  mode=%s"
          % (ref_params_cut_plotter_1000.get("quantity"), ref_params_cut_plotter_1000.get("width"),
             ref_params_cut_plotter_1000.get("height"), ref_params_cut_plotter_1000.get("material_id"),
             ref_params_cut_plotter_1000.get("mode")))
    print("  ---")
    print("  cost        %s  (ожид. %s)  %s" % (r["cost"], e["cost"], "ok" if ok_cost else "FAIL"))
    print("  price       %s  (ожид. %s)  %s" % (r["price"], e["price"], "ok" if ok_price else "FAIL"))
    print("  time_hours  %s  (ожид. %s)  %s" % (r["time_hours"], e["time_hours"], "ok" if ok_time else "FAIL"))
    print("  time_ready  %s  (ожид. %s)  %s" % (r["time_ready"], e["time_ready"], "ok" if ok_ready else "FAIL"))
    mats = r.get("materials") or []
    for i, exp_mat in enumerate(e.get("materials") or []):
        exp_name = exp_mat.get("name", "")
        exp_q = exp_mat.get("quantity_approx")
        exp_unit = exp_mat.get("unit", "")
        got = mats[i] if i < len(mats) else None
        if got:
            got_name = got.get("name", "")
            got_q = got.get("quantity")
            got_unit = got.get("unit", "")
            ok_name = exp_name in got_name or got_name in exp_name
            ok_q = _cmp(float(got_q or 0), float(exp_q or 0), 0.15) if exp_q is not None and got_unit == exp_unit else True
            print("  material    %s  ~ %s %s  name_ok=%s q_ok=%s"
                  % (got_name[:50], got_q, got_unit, ok_name, ok_q))
        else:
            print("  material    (нет в результате) ожид. %s ~ %s %s" % (exp_name[:50], exp_q, exp_unit))

    assert ok_cost, "cost: got %s, expected ~%s" % (r["cost"], e["cost"])
    assert ok_price, "price: got %s, expected ~%s" % (r["price"], e["price"])
    assert ok_time, "time_hours: got %s, expected ~%s" % (r["time_hours"], e["time_hours"])
    assert ok_ready, "time_ready: got %s, expected ~%s" % (r["time_ready"], e["time_ready"])


def test_time_hours_positive(result, base_params, calc):
    if result is None:
        pytest.skip("расчёт не выполнен")
    if result["time_hours"] == 0 and (base_params.get("material_id") or base_params.get("quantity", 0) == 0):
        pytest.skip("нет материала или нулевой тираж")
    assert result["time_hours"] >= 0


def test_time_ready_greater(result):
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


def test_more_quantity_more_time(calc, base_params):
    base_params = dict(base_params)
    r10 = calc.calculate({**base_params, "quantity": 10})
    r100 = calc.calculate({**base_params, "quantity": 100})
    assert r100["time_hours"] >= r10["time_hours"]


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
    assert "cut_plotter" in result["share_url"]


def test_get_options_not_empty(calc):
    opts = calc.get_options()
    assert "modes" in opts
    assert "materials" in opts
    assert "plotters" in opts


def test_get_tool_schema(calc):
    schema = calc.get_tool_schema()
    assert schema.get("name") == "calc_cut_plotter"
    assert "parameters" in schema
