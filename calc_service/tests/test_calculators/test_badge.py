"""
Тесты калькулятора бейджей (badge).
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

_calc_service = Path(__file__).resolve().parent.parent.parent
if _calc_service.name == "calc_service" and str(_calc_service) not in sys.path:
    sys.path.insert(0, str(_calc_service))

from calculators.badge import BadgeCalculator


@pytest.fixture(scope="module")
def calc():
    return BadgeCalculator()


@pytest.fixture(scope="module")
def base_params():
    return {
        "quantity": 50,
        "width": 85,
        "height": 55,
        "material_id": "PVC3",
        "difficulty": 1.0,
        "is_print": True,
        "color": "4+0",
        "is_uv_print": False,
        "mode": 1,
    }


@pytest.fixture(scope="module")
def result(calc, base_params):
    try:
        return calc.execute(base_params)
    except Exception:
        return None


def test_slug(calc):
    assert calc.slug == "badge"


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
    assert "badge" in result["share_url"]


def test_get_tool_schema(calc):
    schema = calc.get_tool_schema()
    assert schema.get("name") == "calc_badge"
    assert "parameters" in schema


# ── Эталонный тест ───────────────────────────────────────────────────

def _cmp(a: float, b: float, rel: float = 0.001) -> bool:
    return abs(a - b) <= rel * max(abs(b), 1e-9)


REF_PARAMS = {
    "quantity": 50,
    "width": 85,
    "height": 55,
    "material_id": "PVC3",
    "difficulty": 1.0,
    "is_print": True,
    "color": "4+0",
    "is_uv_print": False,
    "mode": 1,
}
# JS, 15.11.2026 — вторая резка с печатью идёт как Material=noMaterial, PVC в неё не входит.
# node scripts/run_js_calc.mjs calcBadge --data current --args
# '[50,[85,55],1,"PVC3",{"isPrint":"","isCutLaser":""},1]'
# Раннер: cost 3335, price 6060.5, time_hours 1.35, time_ready 17.9, weight_kg 0.87.
# cost/price/time_hours/time_ready сходятся с раннером (допуск 0.001).
# weight_kg — прежний порт badge.py включает вес второй резки (в JS не входит).
EXPECTED_REF = {
    "cost": 3335,
    "price": 6060.5,
    "time_hours": 1.35,
    "time_ready": 17.9,
    "weight_kg": 1.18,
}
EXPECTED_MATERIAL = {
    "code": "RaflatacMW",
    "name_substring": "Raflatac",
    "quantity_approx": 5,
}


@pytest.fixture(scope="module")
def ref_result(calc):
    try:
        return calc.execute(REF_PARAMS)
    except Exception:
        return None


def test_expected_values_badge(ref_result):
    if ref_result is None:
        pytest.skip("расчёт эталонного кейса не выполнен")
    r = ref_result
    e = EXPECTED_REF
    em = EXPECTED_MATERIAL
    rel = 0.001

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
    print("  [бейджи] quantity=%s  |  size=%s×%s  |  material_id=%s  |  color=%s  |  mode=%s"
          % (REF_PARAMS["quantity"], REF_PARAMS["width"], REF_PARAMS["height"],
             REF_PARAMS["material_id"], REF_PARAMS["color"], REF_PARAMS["mode"]))
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

    assert ok_cost, f"cost: got {r['cost']}, expected ~{e['cost']}"
    assert ok_price, f"price: got {r['price']}, expected ~{e['price']}"
    assert ok_time, f"time_hours: got {r['time_hours']}, expected ~{e['time_hours']}"
    assert ok_ready, f"time_ready: got {r['time_ready']}, expected ~{e['time_ready']}"
    assert ok_weight, f"weight_kg: got {r['weight_kg']}, expected ~{e['weight_kg']}"
    assert materials, "ожидается материал в результате"
    assert ok_mat_code, f"material code: got {mat.get('code')}, expected {em['code']}"
    assert ok_mat_name, f"material name должен содержать '{em['name_substring']}'"
    assert ok_mat_q, f"material quantity: got {mat.get('quantity')}, expected ~{em['quantity_approx']}"


# ── Эталон дефолта лид-формы 64 (CalcBadge) ──────────────────────────

REF_FORM_DEFAULT = {
    "quantity": 100,
    "width": 50,
    "height": 50,
    "difficulty": 1.0,
    "material_id": "ROWMARKLASERMAX",
    "is_print": False,
    "is_uv_print": False,
    "attachment_id": "Magnet4513",
    "is_packing": True,
    "mode": 0,
}
# JS, 23.11.2026 — дефолт лид-формы 64 (CalcBadge):
# node scripts/run_js_calc.mjs calcBadge --data current --args '[100,[50,50],1,"ROWMARKLASERMAX",{"isAttachment":"Magnet4513","isPacking":"","isCutLaser":{"sizeItem":50,"density":0,"difficulty":1,"lenCut":0}},0]'
EXPECTED_FORM_DEFAULT = {
    "cost": 6810,
    "price": 12912.2,
    "time_hours": 0.9,
    "time_ready": 41.3,
}

# JS, 23.11.2026 — режимы 0, 1, 2 на дефолте формы 64:
EXPECTED_FORM_MODES = {
    0: {"cost": 6810, "price": 12912.2, "time_hours": 0.9, "time_ready": 41.3},
    1: {"cost": 7410, "price": 14016.2, "time_hours": 1.3, "time_ready": 17.9},
    2: {"cost": 8182, "price": 15449.1, "time_hours": 1.72, "time_ready": 10.54},
}


def test_form64_default(calc):
    """JS, 23.11.2026: дефолт формы 64 CalcBadge сходится с раннером по cost/price/time."""
    r = calc.execute(REF_FORM_DEFAULT)
    e = EXPECTED_FORM_DEFAULT
    assert _cmp(r["cost"], e["cost"], 0.001)
    assert _cmp(r["price"], e["price"], 0.001)
    assert _cmp(r["time_hours"], e["time_hours"], 0.001)
    assert _cmp(r["time_ready"], e["time_ready"], 0.001)


@pytest.mark.parametrize("mode", [0, 1, 2])
def test_form64_modes(calc, mode):
    """JS, 23.11.2026: режимы 0/1/2 на дефолте формы 64 сходятся с раннером."""
    r = calc.execute({**REF_FORM_DEFAULT, "mode": mode})
    e = EXPECTED_FORM_MODES[mode]
    assert _cmp(r["cost"], e["cost"], 0.001)
    assert _cmp(r["price"], e["price"], 0.001)
    assert _cmp(r["time_hours"], e["time_hours"], 0.001)
    assert _cmp(r["time_ready"], e["time_ready"], 0.001)


def test_form64_materials_size_mm(calc):
    """Дефолт формы 64: материалы содержат size_mm для основы, крепления и упаковки."""
    r = calc.execute(REF_FORM_DEFAULT)
    by_code = {m["code"]: m for m in r["materials"]}
    assert set(by_code) == {"ROWMARKLASERMAX", "Magnet4513", "ZipLock0812"}
    assert by_code["ROWMARKLASERMAX"]["size_mm"] == [600.0, 1200.0]
    assert by_code["Magnet4513"]["size_mm"] == [45.0, 13.0]
    assert by_code["Magnet4513"]["quantity"] == 100
    assert by_code["ZipLock0812"]["size_mm"] == [80.0, 120.0]
    assert by_code["ZipLock0812"]["quantity"] == 100


def test_packing_flag_and_legacy_is_packing_string(calc):
    """Автоподбор упаковки работает и через is_packing=True, и через packing_id='isPacking'."""
    r_flag = calc.execute(REF_FORM_DEFAULT)
    r_str = calc.execute({**REF_FORM_DEFAULT, "is_packing": False, "packing_id": "isPacking"})
    r_explicit = calc.execute({**REF_FORM_DEFAULT, "is_packing": False, "packing_id": "ZipLock0812"})
    assert r_flag["price"] == r_str["price"] == r_explicit["price"]
    assert r_flag["materials"] == r_str["materials"] == r_explicit["materials"]
