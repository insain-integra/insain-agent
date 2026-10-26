"""
Тесты калькулятора наградных плакеток (plaque).
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

_calc_service = Path(__file__).resolve().parent.parent.parent
if _calc_service.name == "calc_service" and str(_calc_service) not in sys.path:
    sys.path.insert(0, str(_calc_service))

from calculators.plaque import PlaqueCalculator


@pytest.fixture(scope="module")
def calc():
    return PlaqueCalculator()


@pytest.fixture(scope="module")
def base_params():
    return {
        "quantity": 1,
        "plaque_id": "Plaque2330",
        "material_id": "PVC3",
        "application": "isUVPrint",
        "mode": 1,
    }


@pytest.fixture(scope="module")
def result(calc, base_params):
    return calc.execute(base_params)


def test_slug(calc):
    assert calc.slug == "plaque"


def test_calculate_basic(result):
    for key in ("cost", "price", "unit_price", "time_hours", "time_ready", "weight_kg", "materials"):
        assert key in result
    assert result["cost"] >= 0
    assert result["price"] >= 0
    assert result["unit_price"] >= 0
    assert result["time_hours"] >= 0
    assert result["time_ready"] >= 0
    assert result["weight_kg"] >= 0
    materials = result.get("materials") or []
    assert materials
    for m in materials:
        assert "code" in m
        assert "name" in m
        assert "title" in m


def test_price_gte_cost(result):
    assert result["price"] >= result["cost"]


def test_share_url(result):
    assert "share_url" in result
    assert "plaque" in result["share_url"]


def test_get_options(calc):
    opts = calc.get_options()
    for key in ("plaques", "materials", "applications", "modes"):
        assert key in opts
    codes = [m.get("code") for m in opts["materials"]]
    assert "PVC3" in codes


def test_get_tool_schema(calc):
    schema = calc.get_tool_schema()
    assert schema.get("name") == "calc_plaque"
    assert "parameters" in schema


def test_no_application(calc, base_params):
    params = dict(base_params)
    params["application"] = "noApplication"
    result = calc.calculate(params)
    materials = result["materials"]
    assert len(materials) == 1
    assert materials[0]["code"] == params["plaque_id"]
    assert result["time_hours"] == 0
    assert result["time_ready"] > 0


def test_empty_plaque_id_raises(calc, base_params):
    params = dict(base_params)
    params["plaque_id"] = ""
    with pytest.raises(ValueError, match="plaque_id обязателен"):
        calc.calculate(params)


def test_empty_material_id_raises(calc, base_params):
    params = dict(base_params)
    params["material_id"] = ""
    with pytest.raises(ValueError, match="material_id обязателен"):
        calc.calculate(params)


def test_unknown_application_raises(calc, base_params):
    params = dict(base_params)
    params["application"] = "unknown"
    with pytest.raises(ValueError, match="Неизвестный способ нанесения"):
        calc.calculate(params)


# ── Эталонный тест ───────────────────────────────────────────────────

def _cmp(a: float, b: float, rel: float = 0.03) -> bool:
    return abs(a - b) <= rel * max(abs(b), 1e-9)


REF_PARAMS = {
    "quantity": 2,
    "plaque_id": "Plaque2330",
    "material_id": "PVC3",
    "application": "isUVPrint",
    "mode": 1,
}
EXPECTED_REF = {
    "cost": 2062.0,
    "price": 4906,
    "unit_price": 2453.0,
    "time_hours": 0.37,
    "time_ready": 32.74,
    "weight_kg": 1.17,
}
EXPECTED_MATERIAL = {
    "code": "Plaque2330",
    "name_substring": "Дощечка-плакетка",
    "quantity_approx": 2,
}


@pytest.fixture(scope="module")
def ref_result(calc):
    return calc.execute(REF_PARAMS)


def test_expected_values_plaque(ref_result):
    r = ref_result
    e = EXPECTED_REF
    em = EXPECTED_MATERIAL
    rel = 0.03

    ok_cost = _cmp(r["cost"], e["cost"], rel)
    ok_price = _cmp(r["price"], e["price"], rel)
    ok_unit = _cmp(r["unit_price"], e["unit_price"], rel)
    ok_time = _cmp(r["time_hours"], e["time_hours"], rel)
    ok_ready = _cmp(r["time_ready"], e["time_ready"], rel)
    ok_weight = _cmp(r["weight_kg"], e["weight_kg"], rel)

    materials = r.get("materials") or []
    mat = materials[0] if materials else {}
    ok_mat_code = mat.get("code") == em["code"]
    ok_mat_name = em["name_substring"] in (mat.get("name") or "")
    ok_mat_q = _cmp(float(mat.get("quantity") or 0), float(em["quantity_approx"]), 0.15) if materials else False

    print("")
    print("  [плакетки] quantity=%s  |  plaque_id=%s  |  material_id=%s  |  application=%s  |  mode=%s"
          % (REF_PARAMS["quantity"], REF_PARAMS["plaque_id"], REF_PARAMS["material_id"],
             REF_PARAMS["application"], REF_PARAMS["mode"]))
    print("  ---")
    print("  cost        %s  (ожид. %s)  %s" % (r["cost"], e["cost"], "ok" if ok_cost else "FAIL"))
    print("  price       %s  (ожид. %s)  %s" % (r["price"], e["price"], "ok" if ok_price else "FAIL"))
    print("  unit_price  %s  (ожид. %s)  %s" % (r["unit_price"], e["unit_price"], "ok" if ok_unit else "FAIL"))
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
    assert ok_unit, f"unit_price: got {r['unit_price']}, expected ~{e['unit_price']}"
    assert ok_time, f"time_hours: got {r['time_hours']}, expected ~{e['time_hours']}"
    assert ok_ready, f"time_ready: got {r['time_ready']}, expected ~{e['time_ready']}"
    assert ok_weight, f"weight_kg: got {r['weight_kg']}, expected ~{e['weight_kg']}"
    assert materials, "ожидается материал в результате"
    assert ok_mat_code, f"material code: got {mat.get('code')}, expected {em['code']}"
    assert ok_mat_name, f"material name должен содержать '{em['name_substring']}'"
    assert ok_mat_q, f"material quantity: got {mat.get('quantity')}, expected ~{em['quantity_approx']}"
