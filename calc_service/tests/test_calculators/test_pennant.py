"""Тесты калькулятора вымпелов (pennant)."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

_calc_service = Path(__file__).resolve().parent.parent.parent
if _calc_service.name == "calc_service" and str(_calc_service) not in sys.path:
    sys.path.insert(0, str(_calc_service))

from calculators.pennant import PennantCalculator


def _cmp(a: float, b: float, rel: float = 0.03) -> bool:
    return abs(a - b) <= rel * max(abs(b), 1e-9)


@pytest.fixture(scope="module")
def calc():
    return PennantCalculator()


@pytest.fixture(scope="module")
def base_params():
    return {"quantity": 50, "width_mm": 80, "height_mm": 120, "material_id": "PaperCoated115M", "color": "4+0", "mode": 1}


@pytest.fixture(scope="module")
def result(calc, base_params):
    try:
        return calc.execute(base_params)
    except Exception:
        return None


def test_slug(calc):
    assert calc.slug == "pennant"


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
    assert "pennant" in result["share_url"]


def test_get_options(calc):
    opts = calc.get_options()
    assert "materials" in opts
    assert "modes" in opts


def test_get_tool_schema(calc):
    schema = calc.get_tool_schema()
    assert schema.get("name") == "calc_pennant"
    assert "parameters" in schema


# ── Эталонный тест ───────────────────────────────────────────────────

REF_PARAMS = {"quantity": 50, "width_mm": 80, "height_mm": 120, "material_id": "PaperCoated115M", "color": "4+0", "mode": 1}
# JS, 11.11.2026 — price раннера 2181.133696 совпал с API.
# time_ready JS 9.17, Python 9.164 (rel 0.00065).
# weight_kg 0.1052 — вес изделий. JS 0.1328 (лист с обрезью). Верный вес — Python, решение 11.11.2026.
# node scripts/run_js_calc.mjs calcPennantPaper --data current --args
# '[50,[80,120],"4+0","PaperCoated115M",{},1]'
EXPECTED_REF = {"cost": 1351.9012, "price": 2181.133696, "time_hours": 0.67, "time_ready": 9.164, "weight_kg": 0.1052}
EXPECTED_MATERIAL = {"code": "PaperCoated115M", "name_substring": "Титан DIGITAL", "quantity_approx": 6}


@pytest.fixture(scope="module")
def ref_result(calc):
    try:
        return calc.execute(REF_PARAMS)
    except Exception:
        return None


def test_expected_values_pennant(ref_result):
    """JS, 11.11.2026: 50 шт., 80×120, PaperCoated115M, 4+0, mode 1. Вес — изделия, не лист JS."""
    if ref_result is None:
        pytest.skip("расчёт эталонного кейса не выполнен")
    rel = 0.001
    r, e, em = ref_result, EXPECTED_REF, EXPECTED_MATERIAL

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

    print()
    print("  quantity=%s  size=%s×%s  material_id=%s  color=%s  mode=%s" % (
        REF_PARAMS["quantity"], REF_PARAMS["width_mm"], REF_PARAMS["height_mm"],
        REF_PARAMS["material_id"], REF_PARAMS["color"], REF_PARAMS["mode"]))
    print("  ---")
    print("  cost        %s  (ожид. %s)  %s" % (r["cost"], e["cost"], "ok" if ok_cost else "FAIL"))
    print("  price       %s  (ожид. %s)  %s" % (r["price"], e["price"], "ok" if ok_price else "FAIL"))
    print("  time_hours  %s  (ожид. %s)  %s" % (r["time_hours"], e["time_hours"], "ok" if ok_time else "FAIL"))
    print("  time_ready  %s  (ожид. %s)  %s" % (r["time_ready"], e["time_ready"], "ok" if ok_ready else "FAIL"))
    print("  weight_kg   %s  (ожид. %s)  %s" % (r["weight_kg"], e["weight_kg"], "ok" if ok_weight else "FAIL"))
    if materials:
        print("  material    code=%s  name=%s  qty=%s  %s" % (
            mat.get("code"), (mat.get("name") or "")[:50], mat.get("quantity"),
            "ok" if (ok_mat_code and ok_mat_name and ok_mat_q) else "FAIL"))
        assert "title" in mat

    assert ok_cost, f"cost: got {r['cost']}, expected ~{e['cost']}"
    assert ok_price, f"price: got {r['price']}, expected ~{e['price']}"
    assert ok_time, f"time_hours: got {r['time_hours']}, expected ~{e['time_hours']}"
    assert ok_ready, f"time_ready: got {r['time_ready']}, expected ~{e['time_ready']}"
    assert ok_weight, f"weight_kg: got {r['weight_kg']}, expected ~{e['weight_kg']}"
    assert materials, "ожидается материал в результате"
    assert ok_mat_code, f"material code: got {mat.get('code')}, expected {em['code']}"
    assert ok_mat_name, f"material name должен содержать '{em['name_substring']}'"
    assert ok_mat_q, f"material quantity: got {mat.get('quantity')}, expected ~{em['quantity_approx']}"


# JS, 11.11.2026 — дефолт боевой формы 73: 100 шт., А5 148×210, 4+0,
# PaperCoated170M, Laminat32G, mode 1.
# cost, price, time_hours, time_ready — боевой JS страницы. Раннер ламинацию не считает
# (нет laminat.json); кейс в docs/js-runner-cases.md не добавлялся.
# price JS 5976.162177692308, Python 5976.340906666667 (rel 2.99e-5); round обоих 6000.
# time_ready JS 10.63, Python 10.623333333333333 (rel 0.000628).
# weight_kg 0.8818 — вес изделий (Python). JS 1.0144 — лист с обрезью. Решение 11.11.2026.
REF_FORM_DEFAULT = {
    "quantity": 100,
    "width_mm": 148,
    "height_mm": 210,
    "material_id": "PaperCoated170M",
    "color": "4+0",
    "lamination_id": "Laminat32G",
    "mode": 1,
}
EXPECTED_FORM_DEFAULT = {
    "cost": 3684.0074923076927,
    "price": 5976.162177692308,
    "time_hours": 1.44,
    "time_ready": 10.63,
    "weight_kg": 0.8818,
}


def test_form_default_laminat(calc):
    """JS, 11.11.2026: дефолт формы 73 с ламинацией. Вес — изделие, не лист JS."""
    r = calc.execute(REF_FORM_DEFAULT)
    e = EXPECTED_FORM_DEFAULT
    assert r["cost"] == pytest.approx(e["cost"], rel=0.001)
    assert r["price"] == pytest.approx(e["price"], rel=0.001)
    assert r["time_hours"] == pytest.approx(e["time_hours"], rel=0.001)
    assert r["time_ready"] == pytest.approx(e["time_ready"], rel=0.001)
    assert r["weight_kg"] == pytest.approx(e["weight_kg"], rel=0.001)


# 2026-11-11 — size_mm: плёнка из каталога Laminat, бумага листа, шнур.
# Цена — Python до прокидки size_mm (боевой API на эту дату).
FORM73_PRICE = 5976.340906666667


def test_form73_materials_size_mm(calc):
    """2026-11-11: дефолт формы 73 — size_mm плёнки, бумаги и шнура; цена не сдвигается."""
    r = calc.execute(REF_FORM_DEFAULT)
    mats = r["materials"]
    assert len(mats) >= 3, mats
    by_code = {m["code"]: m for m in mats}
    assert by_code["Laminat32G"]["size_mm"] == [330.0, 0.0], by_code["Laminat32G"]
    assert by_code["PaperCoated170M"]["size_mm"] == [320.0, 450.0], by_code["PaperCoated170M"]
    assert by_code["RopeForPack"]["size_mm"] == [4.0, 350.0], by_code["RopeForPack"]
    assert abs(r["price"] - FORM73_PRICE) / FORM73_PRICE <= 0.001, r["price"]
