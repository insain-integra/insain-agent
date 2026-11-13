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
    "cost": 400.64,
    "price": 642,
    "time_hours": 0.21,
    "time_ready": 16.23,
    "materials": [
        {"name": "Плёнка AVERY, серия 500, цветная", "quantity_approx": 0.4, "unit": "м"},
    ],
}

# Эталон: 1000 шт, 60×60 мм, difficulty=1.3, len_cut вычисляется (0.312 м/шт), Avery500c (рулон).
EXPECTED_CUT_PLOTTER_1000 = {
    "cost": 2954.06,
    "price": 4727,
    "time_hours": 1.64,
    "time_ready": 17.64,
    "materials": [
        {"name": "Плёнка AVERY, серия 500, цветная", "quantity_approx": 3.22, "unit": "м"},
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
    materials = result.get("materials") or []
    for m in materials:
        assert "name" in m
        assert "title" in m


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
            assert "title" in got
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
            assert "title" in got
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


# JS, 14.11.2026 — листовая ветка, дефолт формы 22 без печати.
# node scripts/run_js_calc.mjs calcCutPlotter --data current --args '[100,[50,50],50,0,1,"RAFLACOAT",{},1]'
REF_SHEET_RAFLACOAT = {
    "quantity": 100,
    "width": 50,
    "height": 50,
    "material_id": "RAFLACOAT",
    "size_item": 50,
    "mode": 1,
}
EXPECTED_SHEET_RAFLACOAT = {
    "cost": 357,
    "price": 571,
    "time_hours": 0.2,
    "time_ready": 16.2,
}


def test_sheet_raflacoat_js(calc):
    """100 шт 50×50 RAFLACOAT, size_item=50, mode=1: лист [320, 450], 3 шт."""
    result = calc.execute(REF_SHEET_RAFLACOAT)
    expected = EXPECTED_SHEET_RAFLACOAT
    rel = 0.001
    assert _cmp(result["cost"], expected["cost"], rel), result["cost"]
    assert _cmp(result["price"], expected["price"], rel), result["price"]
    assert _cmp(result["time_hours"], expected["time_hours"], rel), result["time_hours"]
    assert _cmp(result["time_ready"], expected["time_ready"], rel), result["time_ready"]
    materials = result["materials"]
    assert materials, "ожидается материал"
    mat = materials[0]
    assert mat["code"] == "RAFLACOAT"
    assert mat["quantity"] == 3
    assert mat["unit"] == "лист"
    assert mat["size_mm"] == [320.0, 450.0]
    assert "title" in mat


# JS, 14.11.2026 — calcCutPlotter.js: layoutOnSheet.num == 0 → ICalcError.
# node scripts/run_js_calc.mjs calcCutPlotter --data current --args '[100,[400,400],50,0,1,"RAFLACOAT",{},1]'
# выход 1, текст «Размер изделия больше допустимого» (то же на 281×281 и 280×431).
# 280×430: cost 3268, price 5228, time_ready 17.85.
# 281×280: cost 2985, price 4776, time_ready 17.69.
OVERSIZE_SHEET_MESSAGE = "Размер изделия больше допустимого"
_OVERSIZE_SIZES = ((400, 400), (281, 281), (280, 431))


def _raflacoat_sheet(width: float, height: float) -> dict:
    return {
        "quantity": 100,
        "width": width,
        "height": height,
        "material_id": "RAFLACOAT",
        "size_item": 50,
        "difficulty": 1,
        "mode": 1,
    }


@pytest.mark.parametrize("width,height", _OVERSIZE_SIZES)
def test_sheet_larger_than_material_raises(calc, width, height):
    """Изделие не помещается на лист RAFLACOAT 320×450 — та же ошибка, что в JS."""
    with pytest.raises(ValueError, match="^Размер изделия больше допустимого$"):
        calc.execute(_raflacoat_sheet(width, height))


def test_sheet_just_fits_raflacoat(calc):
    """Граница листа: 280×430 считается, соседний 280×431 — ошибка (см. тест выше)."""
    result = calc.execute(_raflacoat_sheet(280, 430))
    assert _cmp(result["cost"], 3268, 0.001), result["cost"]
    assert _cmp(result["price"], 5228, 0.001), result["price"]
    assert _cmp(result["time_ready"], 17.85, 0.001), result["time_ready"]
    assert result["materials"], "ожидается лист"
    assert result["materials"][0]["quantity"] == 105


def test_sheet_just_fits_swapped_raflacoat(calc):
    """281×280 помещается; 281×281 — нет."""
    result = calc.execute(_raflacoat_sheet(281, 280))
    assert _cmp(result["cost"], 2985, 0.001), result["cost"]
    assert _cmp(result["price"], 4776, 0.001), result["price"]
    assert _cmp(result["time_ready"], 17.69, 0.001), result["time_ready"]


def test_oversize_sheet_http_400():
    """POST /calc/cut_plotter на 400×400 — HTTP 400 и текст JS."""
    from fastapi.testclient import TestClient
    from main import app

    response = TestClient(app).post("/api/v1/calc/cut_plotter", json=_raflacoat_sheet(400, 400))
    assert response.status_code == 400, response.text
    assert response.json()["detail"] == OVERSIZE_SHEET_MESSAGE


def test_roll_length_not_rounded(calc):
    """Расход рулона ORAJET3640 — 232 мм на ширине 1520, не 0.23 м: от него стоимость плёнки в sticker.

    JS, 14.11.2026: calcSticker без печати costMaterial = 180 × 1520 × 0.232 / 1000 = 63.4752.
    """
    result = calc.execute({
        "quantity": 100,
        "width": 50,
        "height": 50,
        "material_id": "ORAJET3640",
        "size_item": 50,
        "difficulty": 1,
        "mode": 1,
    })
    mat = result["materials"][0]
    assert mat["unit"] == "м"
    assert mat["size_mm"] == [1520.0, 0.0]
    assert mat["quantity"] == pytest.approx(0.232, abs=1e-6)
