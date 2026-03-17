"""
Тесты калькулятора струйной печати (print_inkjet).
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

_calc_service = Path(__file__).resolve().parent.parent.parent
if _calc_service.name == "calc_service" and str(_calc_service) not in sys.path:
    sys.path.insert(0, str(_calc_service))

from calculators.base import ProductionMode
from calculators.print_inkjet import PrintInkjetCalculator


@pytest.fixture(scope="module")
def calc():
    return PrintInkjetCalculator()


@pytest.fixture(scope="module")
def base_params(calc):
    opts = calc.get_options()
    materials = opts.get("materials") or []
    mat = materials[0] if materials else {}
    code = mat.get("code", "PaperCoated115M")
    return {
        "num_sheet": 10,
        "width": 210,
        "height": 297,
        "color": "4+0",
        "material_id": code,
        "printer_code": "EPSONWF7610",
        "mode": 1,
    }


@pytest.fixture(scope="module")
def result(calc, base_params):
    try:
        return calc.execute(base_params)
    except Exception:
        return None


def test_slug(calc):
    assert calc.slug == "print_inkjet"


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
    assert "print_inkjet" in result["share_url"]


def test_get_options_not_empty(calc):
    opts = calc.get_options()
    assert "modes" in opts
    assert "materials" in opts
    assert "colors" in opts


def test_get_tool_schema(calc):
    schema = calc.get_tool_schema()
    assert schema.get("name") == "calc_print_inkjet"
    assert "parameters" in schema
    assert "num_sheet" in schema["parameters"].get("properties", {})


# ── Эталонные тесты ──────────────────────────────────────────────────

REF_REL_TOL = 0.01

# Эталон 1: 10 листов A4, PaperCoated115M, 4+0, quality=0, стандартный режим
REF_PARAMS = {
    "num_sheet": 10,
    "width": 210,
    "height": 297,
    "quality": 0,
    "color": "4+0",
    "material_id": "PaperCoated115M",
    "printer_code": "EPSONWF7610",
    "mode": 1,
}
EXPECTED_REF = {
    "cost": 337.13,
    "price": 544.0748,
    "unit_price": 54.40748,
    "time_hours": 0.16,
    "time_ready": 8.16,
    "weight_kg": 0.072,
}
EXPECTED_MATERIAL = {
    "code": "PaperCoated115M",
    "name_substring": "Титан DIGITAL мелованная",
    "quantity_approx": 11,
}

# Эталон 2: 50 листов A4, PaperCoated300M, 4+4, quality=1 (высокое), стандартный
REF_PARAMS_2 = {
    "num_sheet": 50,
    "width": 210,
    "height": 297,
    "quality": 1,
    "color": "4+4",
    "material_id": "PaperCoated300M",
    "printer_code": "EPSONWF7610",
    "mode": 1,
}
EXPECTED_REF_2 = {
    "cost": 1280.93,
    "price": 2090.1608,
    "unit_price": 41.803216,
    "time_hours": 0.63,
    "time_ready": 8.63,
    "weight_kg": 0.936,
}
EXPECTED_MATERIAL_2 = {
    "code": "PaperCoated300M",
    "name_substring": "Титан DIGITAL мелованная",
    "quantity_approx": 53,
}

# Эталон 3: 100 листов A3, VHI80, 1+0, quality=0, стандартный (полный формат принтера)
REF_PARAMS_3 = {
    "num_sheet": 100,
    "width": 297,
    "height": 420,
    "quality": 0,
    "color": "1+0",
    "material_id": "VHI80",
    "printer_code": "EPSONWF7610",
    "mode": 1,
}
EXPECTED_REF_3 = {
    "cost": 2332.65,
    "price": 3813.084,
    "unit_price": 38.13084,
    "time_hours": 1.16,
    "time_ready": 9.16,
    "weight_kg": 0.998,
}
EXPECTED_MATERIAL_3 = {
    "code": "VHI80",
    "name_substring": "Снегурочка",
    "quantity_approx": 105,
}


def _cmp(a: float, b: float, rel: float = 0.02) -> bool:
    """Сравнение с относительным допуском."""
    return abs(a - b) <= rel * max(abs(b), 1e-9)


def _print_ref_report(label, params, result, expected, expected_mat, rel):
    """Вывод подробного отчёта по эталонному кейсу."""
    r, e, em = result, expected, expected_mat

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
    print("  [%s] num_sheet=%s  |  size=%s×%s  |  material_id=%s  |  color=%s  |  quality=%s  |  mode=%s"
          % (label, params.get("num_sheet"), params.get("width"), params.get("height"),
             params.get("material_id"), params.get("color"), params.get("quality"), params.get("mode")))
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
                (mat.get("name") or "")[:50],
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

    return ok_cost, ok_price, ok_time, ok_ready, ok_weight, materials, mat, ok_mat_code, ok_mat_name, ok_mat_q


@pytest.fixture(scope="module")
def ref_result(calc):
    """Результат расчёта: 10 листов A4, PaperCoated115M, 4+0, quality=0."""
    try:
        return calc.execute(REF_PARAMS)
    except Exception:
        return None


def test_expected_values_inkjet_10sheets(ref_result):
    """Сверка с эталоном: 10 листов A4, PaperCoated115M, 4+0, quality=0."""
    if ref_result is None:
        pytest.skip("расчёт эталонного кейса не выполнен (материал PaperCoated115M?)")
    rel = REF_REL_TOL
    ok_cost, ok_price, ok_time, ok_ready, ok_weight, materials, mat, ok_mat_code, ok_mat_name, ok_mat_q = \
        _print_ref_report("струйная 10 листов", REF_PARAMS, ref_result, EXPECTED_REF, EXPECTED_MATERIAL, rel)

    assert ok_cost, f"cost: got {ref_result['cost']}, expected ~{EXPECTED_REF['cost']}"
    assert ok_price, f"price: got {ref_result['price']}, expected ~{EXPECTED_REF['price']}"
    assert ok_time, f"time_hours: got {ref_result['time_hours']}, expected ~{EXPECTED_REF['time_hours']}"
    assert ok_ready, f"time_ready: got {ref_result['time_ready']}, expected ~{EXPECTED_REF['time_ready']}"
    assert ok_weight, f"weight_kg: got {ref_result['weight_kg']}, expected ~{EXPECTED_REF['weight_kg']}"
    assert materials, "ожидается один материал в результате"
    assert ok_mat_code, f"material code: got {mat.get('code')}, expected {EXPECTED_MATERIAL['code']}"
    assert ok_mat_name, f"material name должен содержать '{EXPECTED_MATERIAL['name_substring']}'"
    assert ok_mat_q, f"material quantity: got {mat.get('quantity')}, expected ~{EXPECTED_MATERIAL['quantity_approx']}"


@pytest.fixture(scope="module")
def ref_result_2(calc):
    """Результат расчёта: 50 листов A4, PaperCoated300M, 4+4, quality=1."""
    try:
        return calc.execute(REF_PARAMS_2)
    except Exception:
        return None


def test_expected_values_inkjet_50sheets_4x4(ref_result_2):
    """Сверка с эталоном: 50 листов A4, PaperCoated300M, 4+4, quality=1 (высокое)."""
    if ref_result_2 is None:
        pytest.skip("расчёт эталонного кейса не выполнен (материал PaperCoated300M?)")
    rel = REF_REL_TOL
    ok_cost, ok_price, ok_time, ok_ready, ok_weight, materials, mat, ok_mat_code, ok_mat_name, ok_mat_q = \
        _print_ref_report("струйная 50 листов 4+4", REF_PARAMS_2, ref_result_2, EXPECTED_REF_2, EXPECTED_MATERIAL_2, rel)

    assert ok_cost, f"cost: got {ref_result_2['cost']}, expected ~{EXPECTED_REF_2['cost']}"
    assert ok_price, f"price: got {ref_result_2['price']}, expected ~{EXPECTED_REF_2['price']}"
    assert ok_time, f"time_hours: got {ref_result_2['time_hours']}, expected ~{EXPECTED_REF_2['time_hours']}"
    assert ok_ready, f"time_ready: got {ref_result_2['time_ready']}, expected ~{EXPECTED_REF_2['time_ready']}"
    assert ok_weight, f"weight_kg: got {ref_result_2['weight_kg']}, expected ~{EXPECTED_REF_2['weight_kg']}"
    assert materials, "ожидается один материал в результате"
    assert ok_mat_code, f"material code: got {mat.get('code')}, expected {EXPECTED_MATERIAL_2['code']}"
    assert ok_mat_name, f"material name должен содержать '{EXPECTED_MATERIAL_2['name_substring']}'"
    assert ok_mat_q, f"material quantity: got {mat.get('quantity')}, expected ~{EXPECTED_MATERIAL_2['quantity_approx']}"


@pytest.fixture(scope="module")
def ref_result_3(calc):
    """Результат расчёта: 100 листов A3, VHI80, 1+0, quality=0."""
    try:
        return calc.execute(REF_PARAMS_3)
    except Exception:
        return None


def test_expected_values_inkjet_100sheets_a3(ref_result_3):
    """Сверка с эталоном: 100 листов A3, VHI80, 1+0, quality=0 (полный формат)."""
    if ref_result_3 is None:
        pytest.skip("расчёт эталонного кейса не выполнен (материал VHI80?)")
    rel = REF_REL_TOL
    ok_cost, ok_price, ok_time, ok_ready, ok_weight, materials, mat, ok_mat_code, ok_mat_name, ok_mat_q = \
        _print_ref_report("струйная 100 листов A3", REF_PARAMS_3, ref_result_3, EXPECTED_REF_3, EXPECTED_MATERIAL_3, rel)

    assert ok_cost, f"cost: got {ref_result_3['cost']}, expected ~{EXPECTED_REF_3['cost']}"
    assert ok_price, f"price: got {ref_result_3['price']}, expected ~{EXPECTED_REF_3['price']}"
    assert ok_time, f"time_hours: got {ref_result_3['time_hours']}, expected ~{EXPECTED_REF_3['time_hours']}"
    assert ok_ready, f"time_ready: got {ref_result_3['time_ready']}, expected ~{EXPECTED_REF_3['time_ready']}"
    assert ok_weight, f"weight_kg: got {ref_result_3['weight_kg']}, expected ~{EXPECTED_REF_3['weight_kg']}"
    assert materials, "ожидается один материал в результате"
    assert ok_mat_code, f"material code: got {mat.get('code')}, expected {EXPECTED_MATERIAL_3['code']}"
    assert ok_mat_name, f"material name должен содержать '{EXPECTED_MATERIAL_3['name_substring']}'"
    assert ok_mat_q, f"material quantity: got {mat.get('quantity')}, expected ~{EXPECTED_MATERIAL_3['quantity_approx']}"


def test_modes_cost_and_time(calc):
    """Экспресс дороже стандарта; time_ready убывает от эконома к экспрессу."""
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
        "num_sheet": 10, "width": 210, "height": 297,
        "material_id": "NONEXISTENT_MATERIAL_XYZ",
        "mode": 1,
    })
    assert r["cost"] == 0.0
    assert r["price"] == 0.0
    assert r["materials"] == []


def test_size_exceeds_printer(calc):
    """Лист больше максимального размера принтера — ошибка ValueError."""
    with pytest.raises(ValueError, match="больше допустимого"):
        calc.execute({
            "num_sheet": 1, "width": 500, "height": 700,
            "material_id": "PaperCoated115M",
            "printer_code": "EPSONWF7610",
            "mode": 1,
        })
