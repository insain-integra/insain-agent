"""
Тесты калькулятора стикерпаков с полимерной заливкой (poly_sticker_pack).
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

_calc_service = Path(__file__).resolve().parent.parent.parent
if _calc_service.name == "calc_service" and str(_calc_service) not in sys.path:
    sys.path.insert(0, str(_calc_service))

from calculators.poly_sticker_pack import PolyStickerPackCalculator


@pytest.fixture(scope="module")
def calc():
    return PolyStickerPackCalculator()


@pytest.fixture(scope="module")
def base_params():
    # Остальные поля — значения по умолчанию из get_tool_schema.
    return {
        "quantity": 20,
        "width": 80,
        "height": 80,
        "material_id": "PaperCoated115M",
        "num_stickers": 5,
        "sticker_size": 30,
        "sticker_difficulty": 1.0,
        "is_background": False,
        "print_method": "KMBizhubC220",
        "mode": 1,
    }


@pytest.fixture(scope="module")
def result(calc, base_params):
    return calc.execute(base_params)


def test_slug(calc):
    assert calc.slug == "poly_sticker_pack"


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
    assert "poly_sticker_pack" in result["share_url"]


def test_get_options(calc):
    opts = calc.get_options()
    assert "materials" in opts
    assert "modes" in opts


def test_get_tool_schema(calc):
    schema = calc.get_tool_schema()
    assert schema.get("name") == "calc_poly_sticker_pack"
    assert "parameters" in schema


def test_zero_area_raises(calc, base_params):
    params = dict(base_params)
    params["width"] = 0
    with pytest.raises(ValueError, match="Размер стикерпака должен быть > 0"):
        calc.calculate(params)


# ── Эталонный тест ───────────────────────────────────────────────────

def _cmp(a: float, b: float, rel: float = 0.03) -> bool:
    return abs(a - b) <= rel * max(abs(b), 1e-9)


REF_PARAMS = {
    "quantity": 20,
    "width": 80,
    "height": 80,
    "material_id": "PaperCoated115M",
    "num_stickers": 5,
    "sticker_size": 30,
    "sticker_difficulty": 1.0,
    "is_background": False,
    "print_method": "KMBizhubC220",
    "mode": 1,
}
EXPECTED_REF = {
    "cost": 3231,
    "price": 5983.45,
    "unit_price": 299.17,
    "time_hours": 1.68,
    "time_ready": 41.68,
    "weight_kg": 0.19,
}
EXPECTED_MATERIAL = {
    "code": "PaperCoated115M",
    "name_substring": "Титан DIGITAL",
    "quantity_approx": 1,
}


@pytest.fixture(scope="module")
def ref_result(calc):
    return calc.execute(REF_PARAMS)


def test_expected_values_poly_sticker_pack(ref_result):
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
    mat = next((m for m in materials if m.get("code") == em["code"]), {})
    ok_mat_code = mat.get("code") == em["code"]
    ok_mat_name = em["name_substring"] in (mat.get("name") or "")
    ok_mat_q = _cmp(float(mat.get("quantity") or 0), float(em["quantity_approx"]), 0.15) if mat else False

    print("")
    print("  [стикерпаки] quantity=%s  |  size=%s×%s  |  material_id=%s  |  num_stickers=%s  |  sticker_size=%s  |  mode=%s"
          % (REF_PARAMS["quantity"], REF_PARAMS["width"], REF_PARAMS["height"],
             REF_PARAMS["material_id"], REF_PARAMS["num_stickers"], REF_PARAMS["sticker_size"], REF_PARAMS["mode"]))
    print("  ---")
    print("  cost        %s  (ожид. %s)  %s" % (r["cost"], e["cost"], "ok" if ok_cost else "FAIL"))
    print("  price       %s  (ожид. %s)  %s" % (r["price"], e["price"], "ok" if ok_price else "FAIL"))
    print("  unit_price  %s  (ожид. %s)  %s" % (r["unit_price"], e["unit_price"], "ok" if ok_unit else "FAIL"))
    print("  time_hours  %s  (ожид. %s)  %s" % (r["time_hours"], e["time_hours"], "ok" if ok_time else "FAIL"))
    print("  time_ready  %s  (ожид. %s)  %s" % (r["time_ready"], e["time_ready"], "ok" if ok_ready else "FAIL"))
    print("  weight_kg   %s  (ожид. %s)  %s" % (r["weight_kg"], e["weight_kg"], "ok" if ok_weight else "FAIL"))
    if mat:
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
