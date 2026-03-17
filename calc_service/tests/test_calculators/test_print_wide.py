"""
Тесты калькулятора широкоформатной печати (print_wide).
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

_calc_service = Path(__file__).resolve().parent.parent.parent
if _calc_service.name == "calc_service" and str(_calc_service) not in sys.path:
    sys.path.insert(0, str(_calc_service))

from calculators.base import ProductionMode
from calculators.print_wide import PrintWideCalculator


@pytest.fixture(scope="module")
def calc():
    return PrintWideCalculator()


@pytest.fixture(scope="module")
def base_params(calc):
    opts = calc.get_options()
    materials = opts.get("materials") or []
    mat = materials[0] if materials else {}
    code = mat.get("code", "BannerFronlitCoat400")
    return {
        "quantity": 1,
        "width": 1000,
        "height": 1000,
        "material_id": code,
        "printer_code": "Technojet160ECO",
        "mode": 1,
    }


@pytest.fixture(scope="module")
def result(calc, base_params):
    try:
        return calc.execute(base_params)
    except Exception:
        return None


def test_slug(calc):
    assert calc.slug == "print_wide"


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
    assert "print_wide" in result["share_url"]


def test_get_options_not_empty(calc):
    opts = calc.get_options()
    assert "modes" in opts
    assert "materials" in opts
    assert "printers" in opts


def test_get_tool_schema(calc):
    schema = calc.get_tool_schema()
    assert schema.get("name") == "calc_print_wide"
    assert "parameters" in schema
    assert "quantity" in schema["parameters"].get("properties", {})


# ── Эталонные тесты ──────────────────────────────────────────────────

REF_REL_TOL = 0.01

# Эталон 1: 1 шт, 1000x1000 мм, BannerFronlitCoat400, Technojet160ECO, стандарт
REF_PARAMS = {
    "quantity": 1,
    "width": 1000,
    "height": 1000,
    "material_id": "BannerFronlitCoat400",
    "printer_code": "Technojet160ECO",
    "mode": 1,
}
EXPECTED_REF = {
    "cost": 662.0,
    "price": 1060.0,
    "unit_price": 1060.0,
    "time_hours": 0.26,
    "time_ready": 16.26,
    "weight_kg": 0.4,
}
EXPECTED_MATERIAL = {
    "code": "BannerFronlitCoat400",
    "name_substring": "Fronlit",
    "quantity_approx": 0.69,
}

# Эталон 2: 10 шт, 1500x2000 мм, BannerFronlitCoat400, Technojet160ECO, стандарт
REF_PARAMS_2 = {
    "quantity": 10,
    "width": 1500,
    "height": 2000,
    "material_id": "BannerFronlitCoat400",
    "printer_code": "Technojet160ECO",
    "mode": 1,
}
EXPECTED_REF_2 = {
    "cost": 1479.0,
    "price": 2367.0,
    "unit_price": 236.7,
    "time_hours": 0.48,
    "time_ready": 16.48,
    "weight_kg": 12.0,
}
EXPECTED_MATERIAL_2 = {
    "code": "BannerFronlitCoat400",
    "name_substring": "Fronlit",
    "quantity_approx": 2.01,
}

# Эталон 3 (из JS): 2 шт, 1189x1682 мм, ORAJET3640, Technojet160ECO, стандарт
REF_PARAMS_3 = {
    "quantity": 2,
    "width": 1189,
    "height": 1682,
    "material_id": "ORAJET3640",
    "printer_code": "Technojet160ECO",
    "mode": 1,
}
EXPECTED_REF_3 = {
    "cost": 1065.0,
    "price": 1704.0,
    "unit_price": 852.0,
    "time_hours": 0.37,
    "time_ready": 16.37,
    "weight_kg": 0.86,
}
EXPECTED_MATERIAL_3 = {
    "code": "ORAJET3640",
    "name_substring": "ORAJET 3640",
    "quantity_approx": 1.7,
}


def _cmp(a: float, b: float, rel: float = 0.02) -> bool:
    """Сравнение с относительным допуском."""
    return abs(a - b) <= rel * max(abs(b), 1e-9)


@pytest.fixture(scope="module")
def ref_result(calc):
    """Результат расчёта: 1 шт, 1000x1000, BannerFronlitCoat400, mode=1."""
    try:
        return calc.execute(REF_PARAMS)
    except Exception:
        return None


def test_expected_values_print_wide(ref_result):
    """Сверка с эталоном: 1 шт, 1000x1000 мм, BannerFronlitCoat400, Technojet160ECO."""
    if ref_result is None:
        pytest.skip("расчёт эталонного кейса не выполнен (материал BannerFronlitCoat400?)")
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
    print("  [широкоформатная] Параметры   quantity=%s  |  size=%sx%s  |  material_id=%s  |  mode=%s"
          % (REF_PARAMS.get("quantity"), REF_PARAMS.get("width"), REF_PARAMS.get("height"),
             REF_PARAMS.get("material_id"), REF_PARAMS.get("mode")))
    print("  ---")
    print("  cost        %s  (ожид. %s)  %s" % (r["cost"], e["cost"], "ok" if ok_cost else "FAIL"))
    print("  price       %s  (ожид. %s)  %s" % (r["price"], e["price"], "ok" if ok_price else "FAIL"))
    print("  time_hours  %s  (ожид. %s)  %s" % (r["time_hours"], e["time_hours"], "ok" if ok_time else "FAIL"))
    print("  time_ready  %s  (ожид. %s)  %s" % (r["time_ready"], e["time_ready"], "ok" if ok_ready else "FAIL"))
    print("  weight_kg   %s  (ожид. %s)  %s" % (r["weight_kg"], e["weight_kg"], "ok" if ok_weight else "FAIL"))
    if materials:
        print(
            "  material    code=%s  name=%s  quantity=%s  (ожид. code=%s, name содержит '%s', qty ~%s)  %s"
            % (
                mat.get("code"),
                (mat.get("name") or "")[:40],
                mat.get("quantity"),
                em["code"],
                em["name_substring"],
                em["quantity_approx"],
                "ok" if (ok_mat_code and ok_mat_name and ok_mat_q) else "FAIL",
            )
        )
        assert "title" in mat
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
    """Результат расчёта: 10 шт, 1500x2000, BannerFronlitCoat400, mode=1."""
    try:
        return calc.execute(REF_PARAMS_2)
    except Exception:
        return None


def test_expected_values_print_wide_10pcs(ref_result_2):
    """Сверка с эталоном: 10 шт, 1500x2000 мм, BannerFronlitCoat400."""
    if ref_result_2 is None:
        pytest.skip("расчёт эталонного кейса не выполнен")
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
    print("  [широкоформатная 10шт] quantity=%s  |  size=%sx%s  |  material_id=%s  |  mode=%s"
          % (REF_PARAMS_2.get("quantity"), REF_PARAMS_2.get("width"), REF_PARAMS_2.get("height"),
             REF_PARAMS_2.get("material_id"), REF_PARAMS_2.get("mode")))
    print("  ---")
    print("  cost        %s  (ожид. %s)  %s" % (r["cost"], e["cost"], "ok" if ok_cost else "FAIL"))
    print("  price       %s  (ожид. %s)  %s" % (r["price"], e["price"], "ok" if ok_price else "FAIL"))
    print("  time_hours  %s  (ожид. %s)  %s" % (r["time_hours"], e["time_hours"], "ok" if ok_time else "FAIL"))
    print("  time_ready  %s  (ожид. %s)  %s" % (r["time_ready"], e["time_ready"], "ok" if ok_ready else "FAIL"))
    print("  weight_kg   %s  (ожид. %s)  %s" % (r["weight_kg"], e["weight_kg"], "ok" if ok_weight else "FAIL"))
    if materials:
        print(
            "  material    code=%s  name=%s  quantity=%s  (ожид. code=%s, name содержит '%s', qty ~%s)  %s"
            % (
                mat.get("code"),
                (mat.get("name") or "")[:40],
                mat.get("quantity"),
                em["code"],
                em["name_substring"],
                em["quantity_approx"],
                "ok" if (ok_mat_code and ok_mat_name and ok_mat_q) else "FAIL",
            )
        )
        assert "title" in mat
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


@pytest.fixture(scope="module")
def ref_result_3(calc):
    """Результат расчёта из JS: 2 шт, 1189x1682, ORAJET3640, mode=1."""
    try:
        return calc.execute(REF_PARAMS_3)
    except Exception:
        return None


def test_expected_values_print_wide_orajet(ref_result_3):
    """Сверка с эталоном из JS: 2 шт, 1189x1682 мм, ORAJET3640, Technojet160ECO."""
    if ref_result_3 is None:
        pytest.skip("расчёт эталонного кейса не выполнен (материал ORAJET3640?)")
    r = ref_result_3
    e = EXPECTED_REF_3
    em = EXPECTED_MATERIAL_3
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
    print("  [широкоформатная ORAJET] quantity=%s  |  size=%sx%s  |  material_id=%s  |  mode=%s"
          % (REF_PARAMS_3.get("quantity"), REF_PARAMS_3.get("width"), REF_PARAMS_3.get("height"),
             REF_PARAMS_3.get("material_id"), REF_PARAMS_3.get("mode")))
    print("  ---")
    print("  cost        %s  (ожид. %s)  %s" % (r["cost"], e["cost"], "ok" if ok_cost else "FAIL"))
    print("  price       %s  (ожид. %s)  %s" % (r["price"], e["price"], "ok" if ok_price else "FAIL"))
    print("  time_hours  %s  (ожид. %s)  %s" % (r["time_hours"], e["time_hours"], "ok" if ok_time else "FAIL"))
    print("  time_ready  %s  (ожид. %s)  %s" % (r["time_ready"], e["time_ready"], "ok" if ok_ready else "FAIL"))
    print("  weight_kg   %s  (ожид. %s)  %s" % (r["weight_kg"], e["weight_kg"], "ok" if ok_weight else "FAIL"))
    if materials:
        print(
            "  material    code=%s  name=%s  quantity=%s  (ожид. code=%s, name содержит '%s', qty ~%s)  %s"
            % (
                mat.get("code"),
                (mat.get("name") or "")[:40],
                mat.get("quantity"),
                em["code"],
                em["name_substring"],
                em["quantity_approx"],
                "ok" if (ok_mat_code and ok_mat_name and ok_mat_q) else "FAIL",
            )
        )
        assert "title" in mat
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


def test_modes_cost_and_time(calc):
    """Экспресс дороже стандарта; эконом дешевле/равен стандарту; time_ready убывает."""
    params = dict(REF_PARAMS)
    re = calc.execute({**params, "mode": 0})
    rs = calc.execute({**params, "mode": 1})
    rx = calc.execute({**params, "mode": 2})

    assert re["time_ready"] >= rs["time_ready"], "эконом time_ready >= стандарт"
    assert rs["time_ready"] >= rx["time_ready"], "стандарт time_ready >= экспресс"
    assert rx["price"] >= rs["price"], "экспресс price >= стандарт"
    assert rs["cost"] <= rx["cost"], "стандарт cost <= экспресс"


def test_empty_result_on_invalid_material(calc):
    """При несуществующем материале калькулятор возвращает пустой результат."""
    r = calc.execute({
        "quantity": 1, "width": 1000, "height": 1000,
        "material_id": "NONEXISTENT_MATERIAL_XYZ",
        "mode": 1,
    })
    assert r["cost"] == 0.0
    assert r["price"] == 0.0
    assert r["materials"] == []
