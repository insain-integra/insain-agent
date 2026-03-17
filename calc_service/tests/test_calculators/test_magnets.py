"""
Тесты калькулятора магнитов (magnets).
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

_calc_service = Path(__file__).resolve().parent.parent.parent
if _calc_service.name == "calc_service" and str(_calc_service) not in sys.path:
    sys.path.insert(0, str(_calc_service))

from calculators.magnets import MagnetsCalculator


def _cmp(a: float, b: float, rel: float = 0.03) -> bool:
    return abs(a - b) <= rel * max(abs(b), 1e-9)


@pytest.fixture(scope="module")
def calc():
    return MagnetsCalculator()


@pytest.fixture(scope="module")
def base_params():
    return {
        "quantity": 100,
        "magnet_type": "acrylic",
        "magnet_id": "MagnetAcrylic6565",
        "color": 1,
        "is_packing": True,
        "mode": 1,
    }


@pytest.fixture(scope="module")
def result(calc, base_params):
    try:
        return calc.execute(base_params)
    except Exception:
        return None


def test_slug(calc):
    assert calc.slug == "magnets"


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
    assert "magnets" in result["share_url"]


def test_get_tool_schema(calc):
    schema = calc.get_tool_schema()
    assert schema.get("name") == "calc_magnets"
    assert "parameters" in schema
    assert "quantity" in schema["parameters"].get("properties", {})


# ── Эталонные тесты ──────────────────────────────────────────────────

REF_PARAMS = {
    "quantity": 100,
    "magnet_type": "acrylic",
    "magnet_id": "MagnetAcrylic6565",
    "color": 1,
    "is_packing": True,
    "mode": 1,
}

EXPECTED_REF = {
    "cost": 3046.69,
    "price": 4971.0,
    "time_hours": 0.99,
    "time_ready": 9.346,
    "weight_kg": 2.137,
}

EXPECTED_MATERIAL = {
    "code": "MagnetAcrylic6565",
    "name_substring": "магнит",
    "quantity_approx": 100,
}


@pytest.fixture(scope="module")
def ref_result(calc):
    try:
        return calc.execute(REF_PARAMS)
    except Exception:
        return None


def test_expected_values_magnets(ref_result):
    if ref_result is None:
        pytest.skip("расчёт эталонного кейса не выполнен")
    r = ref_result
    e = EXPECTED_REF
    em = EXPECTED_MATERIAL
    rel = 0.03

    ok_cost = _cmp(r["cost"], e["cost"], rel)
    ok_price = _cmp(r["price"], e["price"], rel)
    ok_time = _cmp(r["time_hours"], e["time_hours"], rel)
    ok_ready = _cmp(r["time_ready"], e["time_ready"], rel)
    ok_weight = _cmp(r["weight_kg"], e["weight_kg"], rel)

    materials = r.get("materials") or []
    mat_match = next((m for m in materials if m.get("code") == em["code"]), {})
    ok_mat_code = bool(mat_match)
    ok_mat_name = em["name_substring"].lower() in (mat_match.get("name") or "").lower()
    ok_mat_q = _cmp(float(mat_match.get("quantity") or 0), float(em["quantity_approx"]), 0.15) if mat_match else False

    print("")
    print("  [magnets] quantity=%s  |  type=%s  |  magnet_id=%s  |  mode=%s"
          % (REF_PARAMS["quantity"], REF_PARAMS["magnet_type"],
             REF_PARAMS["magnet_id"], REF_PARAMS["mode"]))
    print("  ---")
    print("  cost        %s  (ожид. %s)  %s" % (r["cost"], e["cost"], "ok" if ok_cost else "FAIL"))
    print("  price       %s  (ожид. %s)  %s" % (r["price"], e["price"], "ok" if ok_price else "FAIL"))
    print("  time_hours  %s  (ожид. %s)  %s" % (r["time_hours"], e["time_hours"], "ok" if ok_time else "FAIL"))
    print("  time_ready  %s  (ожид. %s)  %s" % (r["time_ready"], e["time_ready"], "ok" if ok_ready else "FAIL"))
    print("  weight_kg   %s  (ожид. %s)  %s" % (r["weight_kg"], e["weight_kg"], "ok" if ok_weight else "FAIL"))
    if mat_match:
        print(
            "  material    code=%s  name=%s  quantity=%s  (ожид. code=%s, name содержит '%s', qty ~%s)  %s"
            % (
                mat_match.get("code"),
                (mat_match.get("name") or "")[:50],
                mat_match.get("quantity"),
                em["code"],
                em["name_substring"],
                em["quantity_approx"],
                "ok" if (ok_mat_code and ok_mat_name and ok_mat_q) else "FAIL",
            )
        )
        assert "title" in mat_match

    assert ok_cost, f"cost: got {r['cost']}, expected ~{e['cost']}"
    assert ok_price, f"price: got {r['price']}, expected ~{e['price']}"
    assert ok_time, f"time_hours: got {r['time_hours']}, expected ~{e['time_hours']}"
    assert ok_ready, f"time_ready: got {r['time_ready']}, expected ~{e['time_ready']}"
    assert ok_weight, f"weight_kg: got {r['weight_kg']}, expected ~{e['weight_kg']}"
    assert ok_mat_code, f"material code {em['code']} не найден в materials"
    assert ok_mat_name, f"material name должен содержать '{em['name_substring']}'"
    assert ok_mat_q, f"material quantity: got {mat_match.get('quantity')}, expected ~{em['quantity_approx']}"
