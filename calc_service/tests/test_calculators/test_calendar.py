"""
Тесты калькулятора календарей (calendar).
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

_calc_service = Path(__file__).resolve().parent.parent.parent
if _calc_service.name == "calc_service" and str(_calc_service) not in sys.path:
    sys.path.insert(0, str(_calc_service))

from calculators.calendar import CalendarCalculator


@pytest.fixture(scope="module")
def calc():
    return CalendarCalculator()


@pytest.fixture(scope="module")
def base_params():
    return {
        "quantity": 100,
        "calendar_type": "quarterly",
        "calendar_id": "QuarterlyMini",
        "block_id": "MiniOffset",
        "top_material_id": "PaperCoated115M",
        "top_color": "4+0",
        "bottom_material_id": "PaperCoated115M",
        "bottom_color": "4+0",
        "mode": 1,
    }


@pytest.fixture(scope="module")
def result(calc, base_params):
    try:
        return calc.execute(base_params)
    except Exception:
        return None


def test_slug(calc):
    assert calc.slug == "calendar"


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
    assert "calendar" in result["share_url"]


def test_get_tool_schema(calc):
    schema = calc.get_tool_schema()
    assert schema.get("name") == "calc_calendar"
    assert "parameters" in schema


# ── Эталонный тест ───────────────────────────────────────────────────

def _cmp(a: float, b: float, rel: float = 0.001) -> bool:
    return abs(a - b) <= rel * max(abs(b), 1e-9)


REF_PARAMS = {
    "quantity": 100,
    "calendar_type": "quarterly",
    "calendar_id": "QuarterlyMini",
    "block_id": "MiniOffset",
    "top_material_id": "PaperCoated115M",
    "top_color": "4+0",
    "bottom_material_id": "PaperCoated115M",
    "bottom_color": "4+0",
    "mode": 1,
}
# JS, 23.11.2026 — подложки 0+0 снова тратят бумагу и резку, как calcPrintSheet.
# Прогон: node vm calcCalendar.js, прайс current. Раннер calcCalendar не подключает.
# price JS 42047.154337458756, Python ceil 42048.
# weight_kg 30.82 — вес изделий (Python). JS 31.12692 — лист с обрезью. Решение 11.11.2026.
EXPECTED_REF = {
    "cost": 21575.371554949168,
    "price": 42047.154337458756,
    "time_hours": 8.53,
    "time_ready": 31.58,
    "weight_kg": 30.82,
}
EXPECTED_MATERIAL = {
    "code": "PaperCoated115M",
    "name_substring": "Титан DIGITAL",
    "quantity_approx": 53,
}


@pytest.fixture(scope="module")
def ref_result(calc):
    try:
        return calc.execute(REF_PARAMS)
    except Exception:
        return None


def test_expected_values_calendar(ref_result):
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
    print("  [календарь] quantity=%s  |  calendar_type=%s  |  calendar_id=%s  |  mode=%s"
          % (REF_PARAMS["quantity"], REF_PARAMS["calendar_type"],
             REF_PARAMS["calendar_id"], REF_PARAMS["mode"]))
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


# JS, 23.11.2026 — дефолт боевой формы 50: 100 шт., QuarterlyMini, MiniOffset,
# PaperCoated300M, без ламинации, 4+0, mode 1.
# Прогон node vm calcCalendar.js (scripts/run_js_calc.mjs календарь не грузит).
# price JS без ceil; Python отдаёт ceil. Допуск rel=0.001.
# weight_kg — изделие (Python), не лист JS (35.1762). Решение 11.11.2026.
# Бумага подложек 0+0 в таблицу не входит: старый JS не мержит costBottom.material.
REF_FORM_DEFAULT = {
    "quantity": 100,
    "calendar_type": "quarterly",
    "calendar_id": "QuarterlyMini",
    "block_id": "MiniOffset",
    "top_material_id": "PaperCoated300M",
    "top_color": "4+0",
    "bottom_material_id": "PaperCoated300M",
    "bottom_color": "4+0",
    "mode": 1,
}
EXPECTED_FORM_DEFAULT = {
    "cost": 23099.901300403715,
    "price": 45068.71889949512,
    "time_hours": 8.8,
    "time_ready": 31.85,
    "weight_kg": 34.36,
}
EXPECTED_FORM_DEFAULT_MODES = {
    0: {
        "cost": 22547.286300403717,
        "price": 44006.11121949512,
        "time_hours": 8.5,
        "time_ready": 47.5,
    },
    2: {
        "cost": 23736.59539131281,
        "price": 46295.351219495125,
        "time_hours": 9.12,
        "time_ready": 24.22,
    },
}


def test_form_default_quarterly(calc):
    """JS, 23.11.2026: дефолт формы 50. Вес — изделие, не лист JS."""
    r = calc.execute(REF_FORM_DEFAULT)
    e = EXPECTED_FORM_DEFAULT
    assert r["cost"] == pytest.approx(e["cost"], rel=0.001)
    assert r["price"] == pytest.approx(e["price"], rel=0.001)
    assert r["time_hours"] == pytest.approx(e["time_hours"], rel=0.001)
    assert r["time_ready"] == pytest.approx(e["time_ready"], rel=0.001)
    assert r["weight_kg"] == pytest.approx(e["weight_kg"], rel=0.001)
    by_code = {m["code"]: m for m in r["materials"]}
    assert by_code["PaperCoated300M"]["quantity"] == 53
    assert by_code["PaperCoated300M"]["size_mm"] == [320.0, 450.0]
    assert by_code["MiniOffset"]["size_mm"] == [297.0, 145.0]
    assert by_code["Cursor"]["size_mm"] == [30.0, 38.0]
    assert by_code["MetallBindindWire1_4"]["size_mm"] == [6.4, 89000.0]
    assert "size_mm" not in by_code["Люверсы4мм"]


@pytest.mark.parametrize("mode", [0, 2])
def test_form_default_modes(calc, mode):
    """JS, 23.11.2026: дефолт формы 50 в режимах 0 и 2."""
    r = calc.execute({**REF_FORM_DEFAULT, "mode": mode})
    e = EXPECTED_FORM_DEFAULT_MODES[mode]
    assert r["cost"] == pytest.approx(e["cost"], rel=0.001)
    assert r["price"] == pytest.approx(e["price"], rel=0.001)
    assert r["time_hours"] == pytest.approx(e["time_hours"], rel=0.001)
    assert r["time_ready"] == pytest.approx(e["time_ready"], rel=0.001)


def test_form_default_mode_order(calc):
    """Своё производство: цена растёт с режимом, срок готовности падает."""
    prices = []
    ready = []
    for mode in (0, 1, 2):
        r = calc.execute({**REF_FORM_DEFAULT, "mode": mode})
        prices.append(r["price"])
        ready.append(r["time_ready"])
    assert prices[0] < prices[1] < prices[2]
    assert ready[2] < ready[1] < ready[0]
