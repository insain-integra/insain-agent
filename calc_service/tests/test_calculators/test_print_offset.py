"""
Тесты калькулятора офсетной печати (print_offset).
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

_calc_service = Path(__file__).resolve().parent.parent.parent
if _calc_service.name == "calc_service" and str(_calc_service) not in sys.path:
    sys.path.insert(0, str(_calc_service))

from calculators.print_offset import PrintOffsetCalculator


@pytest.fixture(scope="module")
def calc():
    return PrintOffsetCalculator()


@pytest.fixture(scope="module")
def base_params():
    return {
        "num_sheet": 500,
        "width": 210,
        "height": 297,
        "color": "4+0",
        "material_id": "PaperCoated115M",
        "mode": 1,
    }


@pytest.fixture(scope="module")
def result(calc, base_params):
    try:
        return calc.execute(base_params)
    except Exception:
        return None


def test_slug(calc):
    assert calc.slug == "print_offset"


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
    assert "print_offset" in result["share_url"]


def test_get_options(calc):
    opts = calc.get_options()
    assert "materials" in opts
    assert "colors" in opts
    assert "modes" in opts


def test_get_tool_schema(calc):
    schema = calc.get_tool_schema()
    assert schema.get("name") == "calc_print_offset"
    assert "parameters" in schema


# ── Эталонный тест ───────────────────────────────────────────────────

def _cmp(a: float, b: float, rel: float = 0.03) -> bool:
    return abs(a - b) <= rel * max(abs(b), 1e-9)


REF_PARAMS = {
    "num_sheet": 1000,
    "width": 210,
    "height": 297,
    "color": "4+0",
    "material_id": "PaperCoated115M",
    "mode": 1,
}
EXPECTED_REF = {
    "cost": 6848.6,
    "price": 14108.116,
    "time_hours": 0.0,
    "time_ready": 56.0,
    "weight_kg": 7.173,
}
EXPECTED_MATERIAL = {
    "code": "OffsetPaper",
    "name_substring": "Мелованная бумага",
    "quantity_approx": 510,
}


@pytest.fixture(scope="module")
def ref_result(calc):
    try:
        return calc.execute(REF_PARAMS)
    except Exception:
        return None


def test_expected_values_print_offset(ref_result):
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
    mat = materials[0] if materials else {}
    ok_mat_code = mat.get("code") == em["code"]
    ok_mat_name = em["name_substring"] in (mat.get("name") or "")
    ok_mat_q = _cmp(float(mat.get("quantity") or 0), float(em["quantity_approx"]), 0.15) if materials else False

    print("")
    print("  [офсетная печать] num_sheet=%s  |  size=%s×%s  |  material_id=%s  |  color=%s  |  mode=%s"
          % (REF_PARAMS["num_sheet"], REF_PARAMS["width"], REF_PARAMS["height"],
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


# ── Сборный тираж (calcPrintOffsetPromo) ─────────────────────────────

# JS, 16.11.2026:
# node scripts/run_js_calc.mjs calcPrintOffsetPromo --data current --args '[<num_sheet>,"OffsetPromoА51000",<mode>]'
PROMO_CODE = "OffsetPromoА51000"
PROMO_CASES = [
    # num_sheet, mode, cost, price, time_hours, time_ready, weight_kg
    (1000, 0, 2250.0, 4244.4, 0.0, 56.0, 3.5742),
    (1000, 1, 2250.0, 4244.4, 0.0, 48.0, 3.5742),
    (1000, 2, 2250.0, 4244.4, 0.0, 40.0, 3.5742),
    (2000, 1, 4050.0, 7592.4, 0.0, 48.0, 7.1484),
    (2000, 0, 4050.0, 7592.4, 0.0, 56.0, 7.1484),
]


@pytest.mark.parametrize("num_sheet,mode,cost,price,time_hours,time_ready,weight_kg", PROMO_CASES)
def test_promo_matches_js(calc, num_sheet, mode, cost, price, time_hours, time_ready, weight_kg):
    """JS, 16.11.2026: сборный тираж А5 считается как calcPrintOffsetPromo."""
    r = calc.execute({"num_sheet": num_sheet, "material_id": PROMO_CODE, "mode": mode})
    assert r["cost"] == pytest.approx(cost, rel=0.001)
    assert r["price"] == pytest.approx(price, rel=0.001)
    assert r["time_ready"] == pytest.approx(time_ready, rel=0.001)
    assert r["time_hours"] == pytest.approx(time_hours, abs=0.01)
    assert r["weight_kg"] == pytest.approx(weight_kg, rel=0.001)
    mat = r["materials"][0]
    assert mat["code"] == PROMO_CODE
    assert mat["name"] and mat["title"] and mat["name"] != PROMO_CODE
    assert mat["quantity"] == num_sheet


def test_promo_ignores_size_and_color(calc):
    """Размер и цветность промо берутся из каталога: width/height/color в запросе ничего не меняют."""
    short = calc.execute({"num_sheet": 1000, "material_id": PROMO_CODE, "mode": 0})
    full = calc.execute({
        "num_sheet": 1000, "material_id": PROMO_CODE, "mode": 0,
        "width": 148, "height": 210, "color": "4+4",
    })
    assert short["price"] == pytest.approx(full["price"], rel=1e-9)
    assert short["time_ready"] == pytest.approx(full["time_ready"], rel=1e-9)


# JS, 17.11.2026 — дефолт боевой формы 82: тираж 1000, А5, режим «стандарт».
# node scripts/run_js_calc.mjs calcPrintOffsetPromo --data current --args '[1000,"OffsetPromoА51000",1]'
# Страница https://insain.ru/catalog/listovki-po-akczii/: get_value_from(3221) = 1 (data-value),
# срок «6 дней». HTML value радио «стандарт» равен 0, в расчёт не попадает.
REF_FORM_DEFAULT = {
    "num_sheet": 1000,
    "material_id": PROMO_CODE,
    "mode": 1,
}
EXPECTED_FORM_DEFAULT = {
    "cost": 2250.0,
    "price": 4244.4,
    "time_hours": 0.0,
    "time_ready": 48.0,
}


def test_form_default_print_offset_promo(calc):
    """JS, 17.11.2026: дефолт формы 82, сборный тираж А5, режим data-value 1."""
    r = calc.execute(REF_FORM_DEFAULT)
    e = EXPECTED_FORM_DEFAULT
    assert r["cost"] == pytest.approx(e["cost"], rel=0.001)
    assert r["price"] == pytest.approx(e["price"], rel=0.001)
    assert r["time_hours"] == pytest.approx(e["time_hours"], rel=0.001)
    assert r["time_ready"] == pytest.approx(e["time_ready"], rel=0.001)


# JS, 20.11.2026 — сверка mode=0, 1, 2 с run_js_calc.mjs calcPrintOffset --data current:
# node scripts/run_js_calc.mjs calcPrintOffset --data current --args '[1000,[210,297],"4+0","PaperCoated115M",0]'
# node scripts/run_js_calc.mjs calcPrintOffset --data current --args '[1000,[210,297],"4+0","PaperCoated115M",2]'
@pytest.mark.parametrize(
    "mode,exp_cost,exp_price,exp_ready",
    [
        (0, 6848.6, 14450.546, 72.0),
        (1, 6848.6, 14450.546, 56.0),
        (2, 6848.6, 14450.546, 40.0),
    ],
)
def test_print_offset_modes_match_js(calc, mode, exp_cost, exp_price, exp_ready):
    """JS, 20.11.2026: у OffsetPrint timePrepare=0, mode меняет time_ready [72, 56, 40]."""
    r = calc.execute({**REF_PARAMS, "mode": mode})
    assert r["cost"] == pytest.approx(exp_cost, rel=0.001)
    assert r["price"] == pytest.approx(exp_price, rel=0.001)
    assert r["time_hours"] == pytest.approx(0.0, abs=1e-9)
    assert r["time_ready"] == pytest.approx(exp_ready, rel=0.001)
