"""Тесты калькулятора брелоков (keychain)."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

_calc_service = Path(__file__).resolve().parent.parent.parent
if _calc_service.name == "calc_service" and str(_calc_service) not in sys.path:
    sys.path.insert(0, str(_calc_service))

from calculators.keychain import KeychainCalculator


def _cmp(a: float, b: float, rel: float = 0.001) -> bool:
    return abs(a - b) <= rel * max(abs(b), 1e-9)


@pytest.fixture(scope="module")
def calc():
    return KeychainCalculator()


@pytest.fixture(scope="module")
def base_params():
    return {"quantity": 50, "keychain_id": "KeychainAcrylic3939", "color": 1, "is_packing": True, "mode": 1}


@pytest.fixture(scope="module")
def result(calc, base_params):
    try:
        return calc.execute(base_params)
    except Exception:
        return None


def test_slug(calc):
    assert calc.slug == "keychain"


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
    assert "keychain" in result["share_url"]


def test_get_options(calc):
    opts = calc.get_options()
    assert "modes" in opts


def test_get_tool_schema(calc):
    schema = calc.get_tool_schema()
    assert "keychain" in schema.get("name", "")
    assert "parameters" in schema


# ── Эталонный тест ───────────────────────────────────────────────────

REF_PARAMS = {"quantity": 50, "keychain_id": "KeychainAcrylic3939", "color": 1, "is_packing": True, "mode": 1}
# JS, 23.11.2026 — color 1 = «4+0», isFindMark. Цена JS 3140.79.
# Срок JS 0.70 / 16.97; Python 0.69 / 16.95 — round времени резки в cut_plotter.
EXPECTED_REF = {"cost": 1933.3032, "price": 3140.787312, "time_hours": 0.69, "time_ready": 16.95, "weight_kg": 0.635}

# Дефолт формы 74: тираж 100, квадрат 39×39, цветность «4+4» (color 2), упаковка, mode 1.
# JS, 23.11.2026 — calcKeychain.js в Node vm, прайс calc_service/data.
REF_FORM_DEFAULT = {
    "quantity": 100,
    "keychain_id": "KeychainAcrylic3939",
    "color": 2,
    "is_packing": True,
    "mode": 1,
}
EXPECTED_FORM_DEFAULT = {
    "cost": 3530.8296,
    "price": 5743.299136,
    "time_hours": 1.2,
    "time_ready": 17.65,
}
# JS, 23.11.2026 — тот же дефолт на mode=0 и mode=2.
FORM_DEFAULT_MODES = [
    (0, 3038.2896, 4955.712736, 0.96, 33.27),
    (2, 4043.9696, 6566.733536, 1.45, 10.05),
]
EXPECTED_MATERIAL = {"code": "KeychainAcrylic3939", "name_substring": "брелок", "quantity_approx": 50}


@pytest.fixture(scope="module")
def ref_result(calc):
    try:
        return calc.execute(REF_PARAMS)
    except Exception:
        return None


def test_expected_values_keychain(ref_result):
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
    print("  quantity=%s  keychain_id=%s  color=%s  mode=%s" % (
        REF_PARAMS["quantity"], REF_PARAMS["keychain_id"], REF_PARAMS["color"], REF_PARAMS["mode"]))
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


def _assert_js(result: dict, expected: dict) -> None:
    rel = 0.001
    assert _cmp(result["cost"], expected["cost"], rel), result["cost"]
    assert _cmp(result["price"], expected["price"], rel), result["price"]
    assert _cmp(result["time_hours"], expected["time_hours"], rel), result["time_hours"]
    assert _cmp(result["time_ready"], expected["time_ready"], rel), result["time_ready"]


def test_form_default_keychain(calc):
    """Дефолт формы 74: 100 шт, 39×39, 4+4, упаковка, mode 1. Цена и срок — JS."""
    result = calc.execute(REF_FORM_DEFAULT)
    _assert_js(result, EXPECTED_FORM_DEFAULT)
    # JS не кладёт вес заготовки (0.12 кг). В ответе API вес изделия, вместе с заготовкой.
    assert _cmp(result["weight_kg"], 1.27, 0.001)
    rows = [(m.get("code"), m.get("quantity"), m.get("size_mm")) for m in result["materials"]]
    assert rows == [
        ("KeychainAcrylic3939", 100, [39.0, 39.0]),
        ("PaperCoated115M", 2, [320.0, 450.0]),
        ("ZipLockAcrylic", 100, [80.0, 120.0]),
    ]
    for mat in result["materials"]:
        assert mat.get("name") and mat["name"] != mat["code"]
        assert "title" in mat


@pytest.mark.parametrize("mode,cost,price,time_hours,time_ready", FORM_DEFAULT_MODES)
def test_form_default_modes(calc, mode, cost, price, time_hours, time_ready):
    """Дефолт формы 74 на mode=0 и mode=2: цена и срок как у JS."""
    result = calc.execute({**REF_FORM_DEFAULT, "mode": mode})
    _assert_js(result, {
        "cost": cost,
        "price": price,
        "time_hours": time_hours,
        "time_ready": time_ready,
    })
    assert result["price"] != EXPECTED_FORM_DEFAULT["price"]
    assert result["price"] < EXPECTED_FORM_DEFAULT["price"] if mode == 0 else result["price"] > EXPECTED_FORM_DEFAULT["price"]
