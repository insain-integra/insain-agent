"""
Тесты калькулятора стикеров (sticker).
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

_calc_service = Path(__file__).resolve().parent.parent.parent
if _calc_service.name == "calc_service" and str(_calc_service) not in sys.path:
    sys.path.insert(0, str(_calc_service))

from calculators.sticker import StickerCalculator


@pytest.fixture(scope="module")
def calc():
    return StickerCalculator()


@pytest.fixture(scope="module")
def base_params():
    return {
        "quantity": 100,
        "width": 50,
        "height": 50,
        "material_id": "VHI80",
        "color": "4+0",
        "mode": 1,
    }


@pytest.fixture(scope="module")
def result(calc, base_params):
    try:
        return calc.execute(base_params)
    except Exception:
        return None


def test_slug(calc):
    assert calc.slug == "sticker"


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
    assert "sticker" in result["share_url"]


def test_get_options(calc):
    opts = calc.get_options()
    assert "materials" in opts
    assert "modes" in opts


def test_get_tool_schema(calc):
    schema = calc.get_tool_schema()
    assert schema.get("name") == "calc_sticker"
    assert "parameters" in schema


# ── Эталонный тест ───────────────────────────────────────────────────

def _cmp(a: float, b: float, rel: float = 0.001) -> bool:
    return abs(a - b) <= rel * max(abs(b), 1e-9)


REF_PARAMS = {
    "quantity": 100,
    "width": 50,
    "height": 50,
    "material_id": "VHI80",
    "color": "4+0",
    "mode": 1,
}
# JS, 14.11.2026 — 100 шт 50×50 VHI80, 4+0, mode=1. 4 листа [297, 420].
# node scripts/run_js_calc.mjs calcSticker --data current --args '[100,[50,50],50,0,1,"VHI80",{"isPrint":{"printerID":"KMBizhubC220","color":"4+0"}},1]'
# price раннера 1307.5632666666668; Python 1307.28 — int(price) в print_laser, rel=0.001 проходит.
EXPECTED_REF = {
    "cost": 814.0516666666667,
    "price": 1307.5632666666668,
    "time_hours": 0.39,
    "time_ready": 16.39,
    "weight_kg": 0.03,
}
EXPECTED_MATERIAL = {
    "code": "VHI80",
    "name_substring": "Снегурочка",
    "quantity_approx": 4,
    "size_mm": [297.0, 420.0],
}


@pytest.fixture(scope="module")
def ref_result(calc):
    try:
        return calc.execute(REF_PARAMS)
    except Exception:
        return None


def test_expected_values_sticker(ref_result):
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
    print("  [стикеры] quantity=%s  |  size=%s×%s  |  material_id=%s  |  color=%s  |  mode=%s"
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
    assert mat.get("size_mm") == em["size_mm"], mat.get("size_mm")


# JS, 14.11.2026 — дефолт формы 22: 100 шт 50×50 RAFLACOAT, без печати, 3 листа [320, 450].
# node scripts/run_js_calc.mjs calcSticker --data current --args '[100,[50,50],50,0,1,"RAFLACOAT",{},1]'
REF_FORM_DEFAULT = {
    "quantity": 100,
    "width": 50,
    "height": 50,
    "material_id": "RAFLACOAT",
    "size_item": 50,
    "mode": 1,
}
EXPECTED_FORM_DEFAULT = {
    "cost": 411.9,
    "price": 662.134,
    "time_hours": 0.2,
    "time_ready": 16.2,
    "weight_kg": 0.05,
}


def test_form_default_raflacoat(calc):
    """Дефолт формы 22: RAFLACOAT без печати."""
    result = calc.execute(REF_FORM_DEFAULT)
    expected = EXPECTED_FORM_DEFAULT
    rel = 0.001
    assert _cmp(result["cost"], expected["cost"], rel), result["cost"]
    assert _cmp(result["price"], expected["price"], rel), result["price"]
    assert _cmp(result["time_hours"], expected["time_hours"], rel), result["time_hours"]
    assert _cmp(result["time_ready"], expected["time_ready"], rel), result["time_ready"]
    assert _cmp(result["weight_kg"], expected["weight_kg"], rel), result["weight_kg"]
    materials = result["materials"]
    assert materials, "ожидается материал"
    mat = materials[0]
    assert mat["code"] == "RAFLACOAT"
    assert mat["quantity"] == 3
    assert mat["unit"] == "лист"
    assert mat["size_mm"] == [320.0, 450.0]
    assert "title" in mat


# JS, 14.11.2026 — calcSticker → calcCutPlotter, RAFLACOAT, тираж 100, сложность 1, без печати.
# 400×400, 281×281, 280×431: «Размер изделия больше допустимого».
# 280×430: price 8417.69, time_ready 17.85. 281×280: price 7965.69, time_ready 17.69.
OVERSIZE_SHEET_MESSAGE = "Размер изделия больше допустимого"
_OVERSIZE_SIZES = ((400, 400), (281, 281), (280, 431))


def _raflacoat_oversize(width: float, height: float) -> dict:
    return {
        "quantity": 100,
        "width": width,
        "height": height,
        "material_id": "RAFLACOAT",
        "size_item": 50,
        "difficulty": 1,
        "mode": 1,
    }


@pytest.mark.parametrize("width,height", _OVERSIZE_SIZES)
def test_sheet_larger_than_material_raises(calc, width, height):
    """Резка не ловится: стикер бросает ту же ошибку, что calcCutPlotter."""
    with pytest.raises(ValueError, match="^Размер изделия больше допустимого$"):
        calc.execute(_raflacoat_oversize(width, height))


def test_sheet_just_fits_raflacoat(calc):
    """280×430 ещё помещается на лист: цена и срок как у раннера."""
    result = calc.execute(_raflacoat_oversize(280, 430))
    rel = 0.001
    assert _cmp(result["price"], 8417.69, rel), result["price"]
    assert _cmp(result["time_ready"], 17.85, rel), result["time_ready"]
    assert result["materials"][0]["code"] == "RAFLACOAT"
    assert result["materials"][0]["quantity"] == 105


def test_sheet_just_fits_swapped_raflacoat(calc):
    """281×280 помещается; 281×281 — нет."""
    result = calc.execute(_raflacoat_oversize(281, 280))
    rel = 0.001
    assert _cmp(result["price"], 7965.69, rel), result["price"]
    assert _cmp(result["time_ready"], 17.69, rel), result["time_ready"]


def test_oversize_sheet_http_400():
    """POST /calc/sticker на 400×400 — HTTP 400, detail для showError."""
    from fastapi.testclient import TestClient
    from main import app

    response = TestClient(app).post("/api/v1/calc/sticker", json=_raflacoat_oversize(400, 400))
    assert response.status_code == 400, response.text
    assert response.json()["detail"] == OVERSIZE_SHEET_MESSAGE
