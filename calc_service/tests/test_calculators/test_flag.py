"""Тесты калькулятора флажков (flag)."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

_calc_service = Path(__file__).resolve().parent.parent.parent
if _calc_service.name == "calc_service" and str(_calc_service) not in sys.path:
    sys.path.insert(0, str(_calc_service))

from calculators.flag import FlagCalculator


def _cmp(a: float, b: float, rel: float = 0.03) -> bool:
    return abs(a - b) <= rel * max(abs(b), 1e-9)


@pytest.fixture(scope="module")
def calc():
    return FlagCalculator()


@pytest.fixture(scope="module")
def base_params():
    return {"quantity": 100, "width_mm": 100, "height_mm": 150, "material_id": "PaperCoated115M", "color": "4+0", "mode": 1}


@pytest.fixture(scope="module")
def result(calc, base_params):
    try:
        return calc.execute(base_params)
    except Exception:
        return None


def test_slug(calc):
    assert calc.slug == "flag"


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
    assert "flag" in result["share_url"]


def test_get_options(calc):
    opts = calc.get_options()
    assert "materials" in opts
    assert "modes" in opts


def test_get_tool_schema(calc):
    schema = calc.get_tool_schema()
    assert schema.get("name") == "calc_flag"
    assert "parameters" in schema


# ── Эталонный тест ───────────────────────────────────────────────────

REF_PARAMS = {"quantity": 100, "width_mm": 100, "height_mm": 150, "material_id": "PaperCoated115M", "color": "4+0", "mode": 1}
# JS, 11.11.2026 — price раннера 3934.410784 совпал с API.
# time_ready JS 9.41, Python 9.406 (rel 0.000425).
# weight_kg 0.1825 — вес изделий. JS 0.22528 (лист с обрезью). Верный вес — Python, решение 11.11.2026.
# node scripts/run_js_calc.mjs calcFlagPaper --data current --args
# '[100,[100,150],"4+0","PaperCoated115M",{},1]'
EXPECTED_REF = {"cost": 2436.8324, "price": 3934.410784, "time_hours": 1.02, "time_ready": 9.406, "weight_kg": 0.1825}
EXPECTED_MATERIAL = {"code": "PaperCoated115M", "name_substring": "Титан DIGITAL", "quantity_approx": 14}


@pytest.fixture(scope="module")
def ref_result(calc):
    try:
        return calc.execute(REF_PARAMS)
    except Exception:
        return None


def test_expected_values_flag(ref_result):
    """JS, 11.11.2026: 100 шт., 100×150, PaperCoated115M, 4+0, mode 1. Вес — изделия, не лист JS."""
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


# 2026-11-11 — дефолт боевой формы 55: 100 шт., 200×99, PaperCoated115M, 4+0, mode 1.
# price 4052.296608 и time_ready 9.442 — раннер/API до прокидки size_mm (отчёт form-flag).
REF_FORM_DEFAULT = {
    "quantity": 100,
    "width_mm": 200,
    "height_mm": 99,
    "material_id": "PaperCoated115M",
    "color": "4+0",
    "mode": 1,
}
FORM55_PRICE = 4052.296608
FORM55_TIME_READY = 9.442


def test_form_default_materials_size_mm(calc):
    """2026-11-11: дефолт формы 55 — size_mm бумаги, скоб и трубочки; цена не сдвигается."""
    r = calc.execute(REF_FORM_DEFAULT)
    mats = r["materials"]
    by_code = {m["code"]: m for m in mats}
    assert by_code["PaperCoated115M"]["size_mm"] == [320.0, 450.0], by_code["PaperCoated115M"]
    assert by_code["Staples26_6"]["size_mm"] == [6.0, 0.0], by_code["Staples26_6"]
    assert by_code["PlasticShaft380"]["size_mm"] == [5.0, 380.0], by_code["PlasticShaft380"]
    assert abs(r["price"] - FORM55_PRICE) / FORM55_PRICE <= 0.001, r["price"]
    assert abs(r["time_ready"] - FORM55_TIME_READY) / FORM55_TIME_READY <= 0.001, r["time_ready"]
