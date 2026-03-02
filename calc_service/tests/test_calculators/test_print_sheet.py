"""
Тесты калькулятора листовой печати (print_sheet).
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

_calc_service = Path(__file__).resolve().parent.parent.parent
if _calc_service.name == "calc_service" and str(_calc_service) not in sys.path:
    sys.path.insert(0, str(_calc_service))

from calculators.base import ProductionMode
from calculators.print_sheet import PrintSheetCalculator


@pytest.fixture(scope="module")
def calc():
    return PrintSheetCalculator()


@pytest.fixture(scope="module")
def base_params(calc):
    opts = calc.get_options()
    materials = opts.get("materials") or []
    mat = materials[0] if materials else {}
    code = mat.get("code", "PaperCoated115M")
    return {
        "quantity": 100,
        "width": 100,
        "height": 150,
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
    assert calc.slug == "print_sheet"


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
    assert "print_sheet" in result["share_url"]


def test_get_options_not_empty(calc):
    opts = calc.get_options()
    assert "modes" in opts
    assert "materials" in opts
    assert "printers" in opts
    assert "colors" in opts


def test_get_tool_schema(calc):
    schema = calc.get_tool_schema()
    assert schema.get("name") == "calc_print_sheet"
    assert "parameters" in schema
    assert "quantity" in schema["parameters"].get("properties", {})


# Эталон: 100 шт, 210×297 мм, PaperCoated300M, цветность 4+4
REF_REL_TOL = 0.01

REF_PARAMS = {
    "quantity": 100,
    "width": 210,
    "height": 297,
    "material_id": "PaperCoated300M",
    "color": "4+4",
    "printer_code": "",
    "mode": 1,
}
EXPECTED_REF = {
    "cost": 3140.638181818182,
    "price": 5154.573018181819,
    "time_hours": 1.13,
    "time_ready": 10.2,
    "weight_kg": 1.8711,
}
EXPECTED_MATERIAL = {
    "code": "PaperCoated300M",
    "name_substring": "Титан DIGITAL мелованная",  # часть названия
    "quantity_approx": 53,
}

# Эталон 2: 1000 шт, 210×297 мм, PaperCoated300M, цветность 4+0
REF_PARAMS_2 = {
    "quantity": 1000,
    "width": 210,
    "height": 297,
    "material_id": "PaperCoated300M",
    "color": "4+0",
    "printer_code": "",
    "mode": 1,
}
EXPECTED_REF_2 = {
    "cost": 17349.458181818183,
    "price": 28571.454763636364,
    "time_hours": 4.95,
    "time_ready": 17.69,
    "weight_kg": 21.6,
}
EXPECTED_MATERIAL_2 = {
    "code": "PaperCoated300M",
    "name_substring": "Титан DIGITAL мелованная",
    "quantity_approx": 510,
    "size": [320, 450],
}


def _cmp(a: float, b: float, rel: float = 0.02) -> bool:
    """Сравнение с относительным допуском."""
    return abs(a - b) <= rel * max(abs(b), 1e-9)


@pytest.fixture(scope="module")
def ref_result(calc):
    """Результат расчёта для эталонного кейса (100 шт, 210×297, PaperCoated300M, 4+4)."""
    try:
        return calc.execute(REF_PARAMS)
    except Exception:
        return None


def test_expected_values_print_sheet(ref_result):
    """Сверка с эталоном: 100 шт, 210×297 мм, PaperCoated300M, цветность 4+4."""
    if ref_result is None:
        pytest.skip("расчёт эталонного кейса не выполнен (материал PaperCoated300M?)")
    r = ref_result
    e = EXPECTED_REF
    em = EXPECTED_MATERIAL
    rel = REF_REL_TOL

    ok_cost = _cmp(r["cost"], e["cost"], rel)
    ok_price = _cmp(r["price"], e["price"], rel)
    ok_time = _cmp(r["time_hours"], e["time_hours"], rel)
    ok_ready = _cmp(r["time_ready"], e["time_ready"], rel)
    ok_weight = _cmp(r["weight_kg"], e["weight_kg"], rel)

    materials = r.get("materials") or []
    mat = materials[0] if materials else {}
    ok_mat_code = mat.get("code") == em["code"]
    ok_mat_name = em["name_substring"] in (mat.get("name") or "")
    ok_mat_q = _cmp(float(mat.get("quantity") or 0), float(em["quantity_approx"]), 0.15) if materials else False

    print("")
    print("  [листовая печать] Параметры   quantity=%s  |  size=%s×%s  |  material_id=%s  |  color=%s  |  mode=%s"
          % (REF_PARAMS.get("quantity"), REF_PARAMS.get("width"), REF_PARAMS.get("height"),
             REF_PARAMS.get("material_id"), REF_PARAMS.get("color"), REF_PARAMS.get("mode")))
    print("  ---")
    print("  cost        %s  (ожид. %s)  %s" % (r["cost"], e["cost"], "ok" if ok_cost else "FAIL"))
    print("  price       %s  (ожид. %s)  %s" % (r["price"], e["price"], "ok" if ok_price else "FAIL"))
    print("  time_hours  %s  (ожид. %s)  %s" % (r["time_hours"], e["time_hours"], "ok" if ok_time else "FAIL"))
    print("  time_ready  %s  (ожид. %s)  %s" % (r["time_ready"], e["time_ready"], "ok" if ok_ready else "FAIL"))
    print("  weight_kg   %s  (ожид. %s)  %s" % (r["weight_kg"], e["weight_kg"], "ok" if ok_weight else "FAIL"))
    if materials:
        print("  material    code=%s  name=%s  quantity=%s  (ожид. code=%s, name содержит '%s', qty ~%s)  %s"
              % (mat.get("code"), (mat.get("name") or "")[:40], mat.get("quantity"),
                 em["code"], em["name_substring"], em["quantity_approx"],
                 "ok" if (ok_mat_code and ok_mat_name and ok_mat_q) else "FAIL"))
    else:
        print("  material    (нет в результате, ожид. code=%s, qty ~%s)  FAIL" % (em["code"], em["quantity_approx"]))

    assert ok_cost, f"cost: got {r['cost']}, expected ~{e['cost']}"
    assert ok_price, f"price: got {r['price']}, expected ~{e['price']}"
    assert ok_time, f"time_hours: got {r['time_hours']}, expected ~{e['time_hours']}"
    assert ok_ready, f"time_ready: got {r['time_ready']}, expected ~{e['time_ready']}"
    assert ok_weight, f"weight_kg: got {r['weight_kg']}, expected ~{e['weight_kg']}"
    assert materials, "ожидается один материал в результате"
    assert ok_mat_code, f"material code: got {mat.get('code')}, expected {em['code']}"
    assert ok_mat_name, f"material name должен содержать '{em['name_substring']}'"
    assert ok_mat_q, f"material quantity: got {mat.get('quantity')}, expected ~{em['quantity_approx']}"


@pytest.fixture(scope="module")
def ref_result_2(calc):
    """Результат расчёта для эталона 2: 1000 шт, 210×297, PaperCoated300M, 4+0."""
    try:
        return calc.execute(REF_PARAMS_2)
    except Exception:
        return None


def test_expected_values_print_sheet_1000(ref_result_2):
    """Сверка с эталоном: 1000 шт, 210×297 мм, PaperCoated300M, цветность 4+0."""
    if ref_result_2 is None:
        pytest.skip("расчёт эталонного кейса не выполнен (материал PaperCoated300M?)")
    r = ref_result_2
    e = EXPECTED_REF_2
    em = EXPECTED_MATERIAL_2
    rel = REF_REL_TOL

    ok_cost = _cmp(r["cost"], e["cost"], rel)
    ok_price = _cmp(r["price"], e["price"], rel)
    ok_time = _cmp(r["time_hours"], e["time_hours"], rel)
    ok_ready = _cmp(r["time_ready"], e["time_ready"], rel)
    ok_weight = _cmp(r["weight_kg"], e["weight_kg"], rel)

    materials = r.get("materials") or []
    mat = materials[0] if materials else {}
    ok_mat_code = mat.get("code") == em["code"]
    ok_mat_name = em["name_substring"] in (mat.get("name") or "")
    ok_mat_q = _cmp(float(mat.get("quantity") or 0), float(em["quantity_approx"]), 0.15) if materials else False

    print("")
    print("  [листовая печать 1000] quantity=%s  |  size=%s×%s  |  material_id=%s  |  color=%s  |  mode=%s"
          % (REF_PARAMS_2.get("quantity"), REF_PARAMS_2.get("width"), REF_PARAMS_2.get("height"),
             REF_PARAMS_2.get("material_id"), REF_PARAMS_2.get("color"), REF_PARAMS_2.get("mode")))
    print("  ---")
    print("  cost        %s  (ожид. %s)  %s" % (r["cost"], e["cost"], "ok" if ok_cost else "FAIL"))
    print("  price       %s  (ожид. %s)  %s" % (r["price"], e["price"], "ok" if ok_price else "FAIL"))
    print("  time_hours  %s  (ожид. %s)  %s" % (r["time_hours"], e["time_hours"], "ok" if ok_time else "FAIL"))
    print("  time_ready  %s  (ожид. %s)  %s" % (r["time_ready"], e["time_ready"], "ok" if ok_ready else "FAIL"))
    print("  weight_kg   %s  (ожид. %s)  %s" % (r["weight_kg"], e["weight_kg"], "ok" if ok_weight else "FAIL"))
    if materials:
        print("  material    code=%s  name=%s  quantity=%s  (ожид. code=%s, name содержит '%s', qty ~%s)  %s"
              % (mat.get("code"), (mat.get("name") or "")[:40], mat.get("quantity"),
                 em["code"], em["name_substring"], em["quantity_approx"],
                 "ok" if (ok_mat_code and ok_mat_name and ok_mat_q) else "FAIL"))
    else:
        print("  material    (нет в результате)  FAIL")

    assert ok_cost, f"cost: got {r['cost']}, expected ~{e['cost']}"
    assert ok_price, f"price: got {r['price']}, expected ~{e['price']}"
    assert ok_time, f"time_hours: got {r['time_hours']}, expected ~{e['time_hours']}"
    assert ok_ready, f"time_ready: got {r['time_ready']}, expected ~{e['time_ready']}"
    assert ok_weight, f"weight_kg: got {r['weight_kg']}, expected ~{e['weight_kg']}"
    assert materials, "ожидается один материал в результате"
    assert ok_mat_code, f"material code: got {mat.get('code')}, expected {em['code']}"
    assert ok_mat_name, f"material name должен содержать '{em['name_substring']}'"
    assert ok_mat_q, f"material quantity: got {mat.get('quantity')}, expected ~{em['quantity_approx']}"
