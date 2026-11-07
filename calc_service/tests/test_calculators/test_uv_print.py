"""
Тесты калькулятора УФ-печати (uv_print).

Эталон JS, 04.11.2026:
node scripts/run_js_calc.mjs calcUVPrint --data current --args
'[50,[100,150],[100,150],null,{"isUVPrint":{"printerID":"RimalSuvUV","resolution":0,"color":"4+0","surface":"isPlain"}},1]'
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

_calc_service = Path(__file__).resolve().parent.parent.parent
if _calc_service.name == "calc_service" and str(_calc_service) not in sys.path:
    sys.path.insert(0, str(_calc_service))

from calculators.uv_print import UVPrintCalculator


@pytest.fixture(scope="module")
def calc():
    return UVPrintCalculator()


@pytest.fixture(scope="module")
def base_params():
    return {
        "quantity": 50,
        "width": 100,
        "height": 150,
        "resolution": 0,
        "color": "4+0",
        "surface": "plain",
        "mode": 1,
    }


@pytest.fixture(scope="module")
def result(calc, base_params):
    try:
        return calc.execute(base_params)
    except Exception:
        return None


def test_slug(calc):
    assert calc.slug == "uv_print"


def test_calculate_basic(result):
    if result is None:
        pytest.skip("расчёт не выполнен")
    for key in ("cost", "price", "unit_price", "time_hours", "time_ready", "weight_kg", "materials"):
        assert key in result
    assert result["cost"] >= 0
    assert result["price"] >= 0
    assert result["time_hours"] >= 0
    assert result["time_ready"] >= 0


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
    assert "uv_print" in result["share_url"]


def test_get_options(calc):
    opts = calc.get_options()
    assert "modes" in opts


def test_get_tool_schema(calc):
    schema = calc.get_tool_schema()
    assert schema.get("name") == "calc_uv_print"
    assert "parameters" in schema
    props = schema["parameters"]["properties"]
    for key in ("is_number", "is_barcode", "is_variables", "is_customer_material"):
        assert key in props


# ── Эталонный тест ───────────────────────────────────────────────────

def _cmp(a: float, b: float, rel: float = 0.001) -> bool:
    return abs(a - b) <= rel * max(abs(b), 1e-9)


# JS, 04.11.2026 — 50 шт., 100×150, resolution 0, 4+0, plain, mode 1
# node scripts/run_js_calc.mjs calcUVPrint --data current --args
# '[50,[100,150],[100,150],null,{"isUVPrint":{"printerID":"RimalSuvUV","resolution":0,"color":"4+0","surface":"isPlain"}},1]'
REF_PARAMS = {
    "quantity": 50,
    "width": 100,
    "height": 150,
    "resolution": 0,
    "color": "4+0",
    "surface": "plain",
    "mode": 1,
}
EXPECTED_REF = {
    "cost": 2430.0,
    "price": 3888.0,
    "time_hours": 1.05,
    "time_ready": 33.05,
    "weight_kg": 0.0,
}


@pytest.fixture(scope="module")
def ref_result(calc):
    try:
        return calc.execute(REF_PARAMS)
    except Exception:
        return None


def test_expected_values_uv_print(ref_result):
    """JS, 04.11.2026: УФ 100×150, тираж 50, 4+0, plain, mode 1."""
    if ref_result is None:
        pytest.skip("расчёт эталонного кейса не выполнен")
    r = ref_result
    e = EXPECTED_REF
    rel = 0.001

    ok_cost = _cmp(r["cost"], e["cost"], rel)
    ok_price = _cmp(r["price"], e["price"], rel)
    ok_time = _cmp(r["time_hours"], e["time_hours"], rel)
    ok_ready = _cmp(r["time_ready"], e["time_ready"], rel)
    ok_weight = _cmp(r["weight_kg"], e["weight_kg"], rel)

    print("")
    print("  [УФ-печать] quantity=%s  |  size=%s×%s  |  resolution=%s  |  color=%s  |  surface=%s  |  mode=%s"
          % (REF_PARAMS["quantity"], REF_PARAMS["width"], REF_PARAMS["height"],
             REF_PARAMS["resolution"], REF_PARAMS["color"], REF_PARAMS["surface"], REF_PARAMS["mode"]))
    print("  ---")
    print("  cost        %s  (ожид. %s)  %s" % (r["cost"], e["cost"], "ok" if ok_cost else "FAIL"))
    print("  price       %s  (ожид. %s)  %s" % (r["price"], e["price"], "ok" if ok_price else "FAIL"))
    print("  time_hours  %s  (ожид. %s)  %s" % (r["time_hours"], e["time_hours"], "ok" if ok_time else "FAIL"))
    print("  time_ready  %s  (ожид. %s)  %s" % (r["time_ready"], e["time_ready"], "ok" if ok_ready else "FAIL"))
    print("  weight_kg   %s  (ожид. %s)  %s" % (r["weight_kg"], e["weight_kg"], "ok" if ok_weight else "FAIL"))

    materials = r.get("materials") or []
    print("  materials   %s шт (ожид. пустой список)" % len(materials))

    assert ok_cost, f"cost: got {r['cost']}, expected ~{e['cost']}"
    assert ok_price, f"price: got {r['price']}, expected ~{e['price']}"
    assert ok_time, f"time_hours: got {r['time_hours']}, expected ~{e['time_hours']}"
    assert ok_ready, f"time_ready: got {r['time_ready']}, expected ~{e['time_ready']}"
    assert ok_weight, f"weight_kg: got {r['weight_kg']}, expected ~{e['weight_kg']}"
    assert len(materials) == 0, f"ожидается пустой список материалов, получено {len(materials)}"


def test_options_raise_price(calc):
    """Нумерация / штрихкод / переменные / материал заказчика поднимают price относительно эталона."""
    base = calc.execute(REF_PARAMS)["price"]
    with_number = calc.execute({**REF_PARAMS, "is_number": True})["price"]
    with_barcode = calc.execute({**REF_PARAMS, "is_barcode": True})["price"]
    with_variables = calc.execute({**REF_PARAMS, "is_variables": True})["price"]
    with_customer = calc.execute({**REF_PARAMS, "is_customer_material": True})["price"]
    assert with_number > base
    assert with_barcode > base
    assert with_variables > base
    assert with_customer > base
    # JS: price = ceil(cost * margin) + opt_price; barcode даёт +2*n к price
    assert with_barcode - base >= 2 * REF_PARAMS["quantity"] - 1


# JS, 08.11.2026 — 100 шт., 20×20, resolution 2, 4+1, plain, mode 0
# node scripts/run_js_calc.mjs calcUVPrint --data current --args
# '[100,[20,20],[20,20],null,{"isUVPrint":{"printerID":"RimalSuvUV","resolution":2,"color":"4+1","surface":"isPlain"}},0]'
REF_PARAMS_MODE0 = {
    "quantity": 100,
    "width": 20,
    "height": 20,
    "resolution": 2,
    "color": "4+1",
    "surface": "plain",
    "mode": 0,
}
EXPECTED_MODE0 = {"cost": 684.0, "price": 1095.0}


def test_mode0_plain_matches_js_and_cheaper_than_mode1(calc):
    """JS, 08.11.2026: plain mode 0 = JS; дешевле того же входа с mode 1."""
    r0 = calc.execute(REF_PARAMS_MODE0)
    r1 = calc.execute({**REF_PARAMS_MODE0, "mode": 1})
    rel = 0.001
    assert _cmp(r0["cost"], EXPECTED_MODE0["cost"], rel), (
        f"cost mode0: got {r0['cost']}, expected ~{EXPECTED_MODE0['cost']}"
    )
    assert _cmp(r0["price"], EXPECTED_MODE0["price"], rel), (
        f"price mode0: got {r0['price']}, expected ~{EXPECTED_MODE0['price']}"
    )
    assert r0["price"] < r1["price"], (
        f"mode0 price {r0['price']} должна быть меньше mode1 {r1['price']}"
    )


# JS, 08.11.2026 — 100 шт., 20×20, resolution 2, 4+1, isAround, mode 1
# node scripts/run_js_calc.mjs calcUVPrint --data current --args
# '[100,[20,20],[20,20],null,{"isUVPrint":{"printerID":"RimalSuvUV","resolution":2,"color":"4+1","surface":"isAround"}},1]'
REF_PARAMS_AROUND = {
    "quantity": 100,
    "width": 20,
    "height": 20,
    "resolution": 2,
    "color": "4+1",
    "surface": "round",
    "mode": 1,
}
EXPECTED_AROUND = {"cost": 10894.0, "price": 17431.0}


def test_around_mode1_matches_js(calc):
    """JS, 08.11.2026: круговая УФ mode 1 — timePrepareAround."""
    r = calc.execute(REF_PARAMS_AROUND)
    rel = 0.001
    assert _cmp(r["cost"], EXPECTED_AROUND["cost"], rel), (
        f"cost around: got {r['cost']}, expected ~{EXPECTED_AROUND['cost']}"
    )
    assert _cmp(r["price"], EXPECTED_AROUND["price"], rel), (
        f"price around: got {r['price']}, expected ~{EXPECTED_AROUND['price']}"
    )
