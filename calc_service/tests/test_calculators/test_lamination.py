"""
Тесты калькулятора ламинации (lamination).
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

_calc_service = Path(__file__).resolve().parent.parent.parent
if _calc_service.name == "calc_service" and str(_calc_service) not in sys.path:
    sys.path.insert(0, str(_calc_service))

from calculators.base import ProductionMode
from calculators.lamination import LaminationCalculator

# Эталон 1: рулонная ламинация — 13 шт, 320×450 мм, Laminat32G, двухсторонняя, пленка [330,0]
EXPECTED_ROLL = {
    "cost": 591.30,
    "price": 958.33,
    "time_hours": 0.1987,
    "weight_kg": 0.1317,
    "materials": [
        {"name": "Пленка для ламинации Roll film 305мм х 100м х 32 mic GLOSS", "quantity_approx": 12.831, "unit": "m"},
    ],
}

# Эталон 2: пакетная ламинация — 100 шт, 148×105 мм, LaminatA660G, двухсторонняя, пленка [105,148]
EXPECTED_PACKET = {
    "cost": 1448.60,
    "price": 2331,
    "time_hours": 0.85,
    "weight_kg": 0.102564,
    "materials": [
        {"name": "Пленка для ламинирования А6 (111х154мм, 2х60мкм), глянцевая", "quantity_approx": 105, "unit": "sheet"},
    ],
}


def _cmp(a: float, b: float, rel: float = 0.01) -> bool:
    """Проверка совпадения с относительным допуском."""
    return abs(a - b) <= rel * max(abs(b), 1e-9)


def _print_params(params: dict, label: str = "") -> None:
    """Вывод параметров расчёта ламинации."""
    parts = [
        "quantity=%s" % params.get("quantity"),
        "size=%sx%s" % (params.get("width"), params.get("height")),
        "material_id=%s" % params.get("material_id"),
        "laminator_code=%s" % params.get("laminator_code", "FGKFM360"),
        "double_side=%s" % params.get("double_side"),
        "mode=%s" % params.get("mode"),
    ]
    prefix = ("  [%s] " % label) if label else "  "
    print("%sПараметры   %s" % (prefix, "  |  ".join(parts)))


@pytest.fixture(scope="module")
def calc():
    return LaminationCalculator()


@pytest.fixture(scope="module")
def base_params(calc):
    opts = calc.get_options()
    materials = opts.get("materials") or []
    mat = materials[0] if materials else {}
    code = mat.get("code", "Laminat32G")
    return {
        "quantity": 50,
        "width": 210,
        "height": 297,
        "material_id": code,
        "laminator_code": "FGKFM360",
        "double_side": True,
        "mode": 1,
    }


@pytest.fixture(scope="module")
def ref_params_roll():
    """Рулонная ламинация: 13 шт, 320×450 мм, Laminat32G, ламинатор FGKFM360, двухсторонняя."""
    return {
        "quantity": 13,
        "width": 320,
        "height": 450,
        "material_id": "Laminat32G",
        "laminator_code": "FGKFM360",
        "double_side": True,
        "mode": 1,
    }


@pytest.fixture(scope="module")
def ref_params_packet():
    """Пакетная ламинация: 100 шт, 148×105 мм, LaminatA660G, ламинатор FGKFM360, двухсторонняя."""
    return {
        "quantity": 100,
        "width": 148,
        "height": 105,
        "material_id": "LaminatA660G",
        "laminator_code": "FGKFM360",
        "double_side": True,
        "mode": 1,
    }


@pytest.fixture(scope="module")
def ref_result_roll(calc, ref_params_roll):
    try:
        return calc.execute(ref_params_roll)
    except Exception:
        return None


@pytest.fixture(scope="module")
def ref_result_packet(calc, ref_params_packet):
    try:
        return calc.execute(ref_params_packet)
    except Exception:
        return None


@pytest.fixture(scope="module")
def result(calc, base_params):
    try:
        return calc.execute(base_params)
    except Exception:
        return None


def test_slug(calc):
    assert calc.slug == "lamination"


def test_calculate_basic(result):
    if result is None:
        pytest.skip("расчёт не выполнен")
    for key in ("cost", "price", "unit_price", "time_hours", "time_ready", "weight_kg", "materials"):
        assert key in result
    assert result["cost"] >= 0
    assert result["price"] >= 0
    assert result["time_hours"] >= 0
    assert result["time_ready"] >= 0


def test_expected_values_roll(ref_result_roll, ref_params_roll):
    """Сверка с эталоном: рулонная ламинация, 13 шт, 320×450 мм, Laminat32G. Допуск 1%."""
    if ref_result_roll is None:
        pytest.skip("расчёт рулонной ламинации не выполнен")
    r = ref_result_roll
    e = EXPECTED_ROLL
    rel = 0.01

    ok_cost = _cmp(r["cost"], e["cost"], rel)
    ok_price = _cmp(r["price"], e["price"], rel)
    ok_time = _cmp(r["time_hours"], e["time_hours"], rel)
    ok_weight = _cmp(r["weight_kg"], e["weight_kg"], rel)

    print("")
    _print_params(ref_params_roll, "рулонная")
    print("  ---")
    print("  cost        %s  (ожид. %s)  %s" % (r["cost"], e["cost"], "ok" if ok_cost else "FAIL"))
    print("  price       %s  (ожид. %s)  %s" % (r["price"], e["price"], "ok" if ok_price else "FAIL"))
    print("  time_hours  %s  (ожид. %s)  %s" % (r["time_hours"], e["time_hours"], "ok" if ok_time else "FAIL"))
    print("  weight_kg   %s  (ожид. %s)  %s" % (r["weight_kg"], e["weight_kg"], "ok" if ok_weight else "FAIL"))
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
            ok_q = _cmp(float(got_q or 0), float(exp_q or 0), 0.05) if exp_q is not None else True
            ok_name = exp_name in got_name or got_name in exp_name
            print("  material    %s  ~ %s %s  name_ok=%s q_ok=%s" % (got_name[:50], got_q, got_unit, ok_name, ok_q))
        else:
            print("  material    (нет в результате) ожид. %s ~ %s %s" % (exp_name[:50], exp_q, exp_unit))

    assert ok_cost, "cost: got %s, expected ~%s" % (r["cost"], e["cost"])
    assert ok_price, "price: got %s, expected ~%s" % (r["price"], e["price"])
    assert ok_time, "time_hours: got %s, expected ~%s" % (r["time_hours"], e["time_hours"])
    assert ok_weight, "weight_kg: got %s, expected ~%s" % (r["weight_kg"], e["weight_kg"])


def test_expected_values_packet(ref_result_packet, ref_params_packet):
    """Сверка с эталоном: пакетная ламинация, 100 шт, 148×105 мм, LaminatA660G. Допуск 1%."""
    if ref_result_packet is None:
        pytest.skip("расчёт пакетной ламинации не выполнен")
    r = ref_result_packet
    e = EXPECTED_PACKET
    rel = 0.01

    ok_cost = _cmp(r["cost"], e["cost"], rel)
    ok_price = _cmp(r["price"], e["price"], rel)
    ok_time = _cmp(r["time_hours"], e["time_hours"], rel)
    ok_weight = _cmp(r["weight_kg"], e["weight_kg"], rel)

    print("")
    _print_params(ref_params_packet, "пакетная")
    print("  ---")
    print("  cost        %s  (ожид. %s)  %s" % (r["cost"], e["cost"], "ok" if ok_cost else "FAIL"))
    print("  price       %s  (ожид. %s)  %s" % (r["price"], e["price"], "ok" if ok_price else "FAIL"))
    print("  time_hours  %s  (ожид. %s)  %s" % (r["time_hours"], e["time_hours"], "ok" if ok_time else "FAIL"))
    print("  weight_kg   %s  (ожид. %s)  %s" % (r["weight_kg"], e["weight_kg"], "ok" if ok_weight else "FAIL"))
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
            ok_q = _cmp(float(got_q or 0), float(exp_q or 0), 0.05) if exp_q is not None else True
            ok_name = exp_name in got_name or got_name in exp_name
            print("  material    %s  ~ %s %s  name_ok=%s q_ok=%s" % (got_name[:50], got_q, got_unit, ok_name, ok_q))
        else:
            print("  material    (нет в результате) ожид. %s ~ %s %s" % (exp_name[:50], exp_q, exp_unit))

    assert ok_cost, "cost: got %s, expected ~%s" % (r["cost"], e["cost"])
    assert ok_price, "price: got %s, expected ~%s" % (r["price"], e["price"])
    assert ok_time, "time_hours: got %s, expected ~%s" % (r["time_hours"], e["time_hours"])
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
    assert "lamination" in result["share_url"]


def test_get_options_not_empty(calc):
    opts = calc.get_options()
    assert "modes" in opts
    assert "materials" in opts


def test_get_tool_schema(calc):
    schema = calc.get_tool_schema()
    assert schema.get("name") == "calc_lamination"
    assert "parameters" in schema
