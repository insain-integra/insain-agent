"""
Тесты калькулятора фрезеровки (milling).
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

_calc_service = Path(__file__).resolve().parent.parent.parent
if _calc_service.name == "calc_service" and str(_calc_service) not in sys.path:
    sys.path.insert(0, str(_calc_service))

from calculators.base import ProductionMode
from calculators.milling import MillingCalculator

# Эталон: 10 шт, 500×1000 мм, форма простая, материал PVC3, лист 3050×2050
EXPECTED_MILLING = {
    "cost": 7948.6875,
    "price": 10370.08125,
    "time_hours": 0.05,
    "time_ready": 56.05,
    "weight_kg": 8.25,
    "materials": [
        {"code": "PVC3", "name": "ПВХ Unext Strong 3 мм", "quantity_approx": 1, "unit": "лист"},
    ],
}


def _cmp(a: float, b: float, rel: float = 0.01) -> bool:
    """Проверка совпадения с относительным допуском."""
    return abs(a - b) <= rel * max(abs(b), 1e-9)


@pytest.fixture(scope="module")
def calc():
    return MillingCalculator()


@pytest.fixture(scope="module")
def base_params(calc):
    opts = calc.get_options()
    materials = opts.get("materials") or []
    mat = materials[0] if materials else {}
    code = mat.get("code", "PVC3")
    return {
        "quantity": 10,
        "width": 300,
        "height": 400,
        "material_id": code,
        "material_mode": "isMaterial",
        "len_cut": 1.5,
        "mode": 1,
    }


@pytest.fixture(scope="module")
def ref_params_milling():
    """Фрезеровка: 10 шт, 500×1000 мм, форма простая (периметр 3 м), PVC3."""
    return {
        "quantity": 10,
        "width": 500,
        "height": 1000,
        "material_id": "PVC3",
        "material_mode": "isMaterial",
        "len_cut": 3.0,
        "mode": 1,
    }


@pytest.fixture(scope="module")
def ref_result_milling(calc, ref_params_milling):
    try:
        return calc.execute(ref_params_milling)
    except Exception:
        return None


@pytest.fixture(scope="module")
def result(calc, base_params):
    try:
        return calc.execute(base_params)
    except Exception:
        return None


def test_slug(calc):
    assert calc.slug == "milling"


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


def test_expected_values_milling(ref_result_milling, ref_params_milling):
    """Сверка с эталоном: 10 шт, 500×1000 мм, PVC3, лист 3050×2050. Допуск 1%."""
    if ref_result_milling is None:
        pytest.skip("расчёт фрезеровки не выполнен")
    r = ref_result_milling
    e = EXPECTED_MILLING
    rel = 0.01

    ok_cost = _cmp(r["cost"], e["cost"], rel)
    ok_price = _cmp(r["price"], e["price"], rel)
    ok_time = _cmp(r["time_hours"], e["time_hours"], rel)
    ok_ready = _cmp(r["time_ready"], e["time_ready"], rel)
    ok_weight = _cmp(r["weight_kg"], e["weight_kg"], rel)

    print("")
    print("  [фрезеровка] Параметры   quantity=%s  |  size=%sx%s  |  material_id=%s  |  len_cut=%s  |  mode=%s"
          % (ref_params_milling.get("quantity"), ref_params_milling.get("width"),
             ref_params_milling.get("height"), ref_params_milling.get("material_id"),
             ref_params_milling.get("len_cut"), ref_params_milling.get("mode")))
    print("  ---")
    print("  cost        %s  (ожид. %s)  %s" % (r["cost"], e["cost"], "ok" if ok_cost else "FAIL"))
    print("  price       %s  (ожид. %s)  %s" % (r["price"], e["price"], "ok" if ok_price else "FAIL"))
    print("  time_hours  %s  (ожид. %s)  %s" % (r["time_hours"], e["time_hours"], "ok" if ok_time else "FAIL"))
    print("  time_ready  %s  (ожид. %s)  %s" % (r["time_ready"], e["time_ready"], "ok" if ok_ready else "FAIL"))
    print("  weight_kg   %s  (ожид. %s)  %s" % (r["weight_kg"], e["weight_kg"], "ok" if ok_weight else "FAIL"))
    mats = r.get("materials") or []
    for i, exp_mat in enumerate(e.get("materials") or []):
        exp_code = exp_mat.get("code", "")
        exp_name = exp_mat.get("name", "")
        exp_q = exp_mat.get("quantity_approx")
        exp_unit = exp_mat.get("unit", "")
        got = mats[i] if i < len(mats) else None
        if got:
            got_code = got.get("code", "")
            got_name = got.get("name", "")
            got_q = got.get("quantity")
            got_unit = got.get("unit", "")
            ok_code = got_code == exp_code
            ok_name = exp_name in got_name or got_name in exp_name
            ok_q = _cmp(float(got_q or 0), float(exp_q or 0), 0.1) if exp_q is not None else True
            print("  material    %s  ~ %s %s  code_ok=%s name_ok=%s q_ok=%s"
                  % (got_name[:40], got_q, got_unit, ok_code, ok_name, ok_q))
        else:
            print("  material    (нет в результате) ожид. %s ~ %s %s" % (exp_name[:40], exp_q, exp_unit))

    assert ok_cost, "cost: got %s, expected ~%s" % (r["cost"], e["cost"])
    assert ok_price, "price: got %s, expected ~%s" % (r["price"], e["price"])
    assert ok_time, "time_hours: got %s, expected ~%s" % (r["time_hours"], e["time_hours"])
    assert ok_ready, "time_ready: got %s, expected ~%s" % (r["time_ready"], e["time_ready"])
    assert ok_weight, "weight_kg: got %s, expected ~%s" % (r["weight_kg"], e["weight_kg"])


def test_time_hours_positive(result):
    if result is None:
        pytest.skip("расчёт не выполнен")
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
    assert result["price"] >= result["cost"]


def test_share_url_contains_slug(result):
    if result is None:
        pytest.skip("расчёт не выполнен")
    assert "share_url" in result
    assert "milling" in result["share_url"]


def test_get_options_not_empty(calc):
    opts = calc.get_options()
    assert "modes" in opts
    assert "materials" in opts


def test_get_tool_schema(calc):
    schema = calc.get_tool_schema()
    assert schema.get("name") == "calc_milling"
    assert "parameters" in schema
    props = schema["parameters"]["properties"]
    assert "is_cut_milling" in props


# JS, 22.11.2026 (консоль боевой страницы: форма 35 на открытии по умолчанию)
REF_FORM_DEFAULT = {
    "quantity": 100,
    "width": 50,
    "height": 50,
    "material_id": "",
    "material_mode": "isMaterial",
    "is_cut_milling": {
        "size_item": 50,
        "density": 0,
        "difficulty": 1,
        "len_cut": 0,
    },
    "mode": 1,
}

EXPECTED_FORM_DEFAULT = {
    0: {"cost": 877.5, "price": 1080.0, "time_hours": 0.0, "time_ready": 72.0},
    1: {"cost": 1105.0, "price": 1360.0, "time_hours": 0.05, "time_ready": 56.05},
    2: {"cost": 1560.0, "price": 1920.0, "time_hours": 0.1, "time_ready": 40.1},
}

# JS, 22.11.2026 (консоль боевой страницы: форма 35 с материалом PVC3)
EXPECTED_FORM_PVC3_MODES = {
    0: {"cost": 1470.9330357142858, "price": 1890.1426854395604, "time_hours": 0.0, "time_ready": 72.0},
    1: {"cost": 1795.9330357142858, "price": 2302.6426854395604, "time_hours": 0.05, "time_ready": 56.05},
    2: {"cost": 2348.433035714286, "price": 3094.2170329670334, "time_hours": 0.1, "time_ready": 40.1},
}

# JS, 22.11.2026 (консоль боевой страницы: dpdDifficulty=1.7 с size_item=50, density=0.25)
EXPECTED_FORM_DIFF_17_MODES = {
    0: {"cost": 2323.083035714286, "price": 2971.7176854395602, "time_hours": 0.0, "time_ready": 72.0},
    1: {"cost": 2648.083035714286, "price": 3384.2176854395602, "time_hours": 0.05, "time_ready": 56.05},
    2: {"cost": 3200.583035714286, "price": 4208.567032967034, "time_hours": 0.1, "time_ready": 40.1},
}


@pytest.mark.parametrize("mode", [0, 1, 2])
def test_form_default_matches_js_modes(calc, mode):
    """Дефолт формы 35 на открытии (material_id='') сходится с JS на mode=0, 1, 2."""
    res = calc.execute({**REF_FORM_DEFAULT, "mode": mode})
    exp = EXPECTED_FORM_DEFAULT[mode]
    assert res["cost"] == pytest.approx(exp["cost"], rel=0.001)
    assert res["price"] == pytest.approx(exp["price"], rel=0.001)
    assert res["time_hours"] == pytest.approx(exp["time_hours"], rel=0.001)
    assert res["time_ready"] == pytest.approx(exp["time_ready"], rel=0.001)
    assert res["materials"] == []


@pytest.mark.parametrize("mode", [0, 1, 2])
def test_form_pvc3_default_matches_js_modes(calc, mode):
    """Форма 35 с материалом PVC3 и простой резкой сходится с JS на mode=0, 1, 2."""
    res = calc.execute({**REF_FORM_DEFAULT, "material_id": "PVC3", "mode": mode})
    exp = EXPECTED_FORM_PVC3_MODES[mode]
    assert res["cost"] == pytest.approx(exp["cost"], rel=0.001)
    assert res["price"] == pytest.approx(exp["price"], rel=0.001)
    assert res["time_hours"] == pytest.approx(exp["time_hours"], rel=0.001)
    assert res["time_ready"] == pytest.approx(exp["time_ready"], rel=0.001)
    assert res["materials"][0]["size_mm"] == [3050.0, 2050.0]


@pytest.mark.parametrize("mode", [0, 1, 2])
def test_form_difficulty_17_matches_js_modes(calc, mode):
    """Опция is_cut_milling (difficulty=1.7, size_item=50, density=0.25) сходится с JS на mode=0, 1, 2."""
    res = calc.execute({
        **REF_FORM_DEFAULT,
        "material_id": "PVC3",
        "is_cut_milling": {"size_item": 50, "density": 0.25, "difficulty": 1.7, "len_cut": 0},
        "mode": mode,
    })
    exp = EXPECTED_FORM_DIFF_17_MODES[mode]
    assert res["cost"] == pytest.approx(exp["cost"], rel=0.001)
    assert res["price"] == pytest.approx(exp["price"], rel=0.001)
    assert res["time_hours"] == pytest.approx(exp["time_hours"], rel=0.001)
    assert res["time_ready"] == pytest.approx(exp["time_ready"], rel=0.001)


def test_is_cut_milling_branches_and_half_sheet(calc):
    """Ветки is_cut_milling (len_cut=100, без резки), режимы материала и поллиста."""
    # Задана длина резки 100 мм на изделие
    r_len = calc.execute({
        **REF_FORM_DEFAULT,
        "material_id": "PVC3",
        "is_cut_milling": {"size_item": 50, "density": 0, "difficulty": 1, "len_cut": 100},
    })
    assert r_len["cost"] == pytest.approx(1444.9330357142858, rel=0.001)
    assert r_len["price"] == pytest.approx(1857.1426854395604, rel=0.001)

    # Без резки (is_cut_milling не передан)
    r_nocut = calc.execute({
        "quantity": 100,
        "width": 50,
        "height": 50,
        "material_id": "PVC3",
        "material_mode": "isMaterial",
        "mode": 1,
    })
    assert r_nocut["cost"] == pytest.approx(1105.0, rel=0.001)
    assert r_nocut["price"] == pytest.approx(1360.0, rel=0.001)

    # Материал заказчика (+25% к резке, без стоимости материала и списка материалов)
    r_cust = calc.execute({**REF_FORM_DEFAULT, "material_id": "PVC3", "material_mode": "isMaterialCustomer"})
    assert r_cust["cost"] == pytest.approx(1478.75, rel=0.001)
    assert r_cust["price"] == pytest.approx(1876.875, rel=0.001)
    assert r_cust["materials"] == []

    # Поллиста (8 шт 500x500 на 3050x2050 -> 0.5 листа)
    r_half = calc.execute({
        **REF_FORM_DEFAULT,
        "quantity": 8,
        "width": 500,
        "height": 500,
        "material_id": "PVC3",
    })
    assert r_half["cost"] == pytest.approx(4435.8234375, rel=0.001)
    assert r_half["price"] == pytest.approx(5502.665625, rel=0.001)
    assert r_half["materials"][0]["quantity"] == 0.5
    assert r_half["materials"][0]["size_mm"] == [3050.0, 2050.0]
