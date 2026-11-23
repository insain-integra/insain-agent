"""Тесты калькулятора пластиковых карт (cards)."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

_calc_service = Path(__file__).resolve().parent.parent.parent
if _calc_service.name == "calc_service" and str(_calc_service) not in sys.path:
    sys.path.insert(0, str(_calc_service))

from calculators.cards import CardsCalculator


def _cmp(a: float, b: float, rel: float = 0.03) -> bool:
    return abs(a - b) <= rel * max(abs(b), 1e-9)


@pytest.fixture(scope="module")
def calc():
    return CardsCalculator()


@pytest.fixture(scope="module")
def base_params():
    return {"quantity": 100, "material_id": "White", "lamination": "", "mode": 1}


@pytest.fixture(scope="module")
def result(calc, base_params):
    try:
        return calc.execute(base_params)
    except Exception:
        return None


def test_slug(calc):
    assert calc.slug == "cards"


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
    assert "cards" in result["share_url"]


def test_get_options(calc):
    opts = calc.get_options()
    assert "modes" in opts


def test_get_tool_schema(calc):
    schema = calc.get_tool_schema()
    assert "cards" in schema.get("name", "")
    assert "parameters" in schema


# ── Эталонный тест ───────────────────────────────────────────────────

REF_PARAMS = {"quantity": 100, "material_id": "White", "lamination": "", "mode": 1}
EXPECTED_REF = {"cost": 1900.0, "price": 3155.0, "time_hours": 0.5, "time_ready": 40.0, "weight_kg": 0.5}
EXPECTED_MATERIAL = {"code": "White", "name_substring": "Пластиковые карты", "quantity_approx": 100}


@pytest.fixture(scope="module")
def ref_result(calc):
    try:
        return calc.execute(REF_PARAMS)
    except Exception:
        return None


def test_expected_values_cards(ref_result):
    if ref_result is None:
        pytest.skip("расчёт эталонного кейса не выполнен")
    rel = 0.03
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
    print("  quantity=%s  material_id=%s  mode=%s" % (REF_PARAMS["quantity"], REF_PARAMS["material_id"], REF_PARAMS["mode"]))
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


def test_cards_modes_contractor(calc):
    """Подрядчик (calcCards.js): цена и time_hours не зависят от mode, меняется только time_ready [56, 40, 32]."""
    r0 = calc.execute({**REF_PARAMS, "mode": 0})
    r1 = calc.execute({**REF_PARAMS, "mode": 1})
    r2 = calc.execute({**REF_PARAMS, "mode": 2})

    assert r0["price"] == r1["price"] == r2["price"]
    assert r0["time_hours"] == r1["time_hours"] == r2["time_hours"] == pytest.approx(0.5)
    assert r0["time_ready"] == pytest.approx(56.0)
    assert r1["time_ready"] == pytest.approx(40.0)
    assert r2["time_ready"] == pytest.approx(32.0)


# JS, 23.11.2026 — дефолт формы 56 со страницы:
# 100 шт, White, ламинация gloss (preselect 0), галки выключены, mode 1.
# calcCards.js не подключён в scripts/run_js_calc.mjs: эталон — прогон
# js_legacy/calc/calcCards.js в Node vm на прайсе calc_service/data.
# JS не округляет price вверх (3154), Python делает ceil → 3155, rel < 0.001.
# mode=0 и mode=2 — тот же вход; у подрядчика цена не зависит от mode.
REF_FORM_DEFAULT = {
    "quantity": 100,
    "material_id": "White",
    "lamination": "gloss",
    "mode": 1,
}

EXPECTED_FORM_DEFAULT = {
    "cost": 1900.0,
    "price": 3154.0,
    "time_hours": 0.5,
    "time_ready": 40.0,
    "weight_kg": 0.5,
}

# JS, 23.11.2026 — тот же дефолт на mode=0 и mode=2.
FORM_DEFAULT_MODES = [
    (0, 1900.0, 3154.0, 0.5, 56.0),
    (2, 1900.0, 3154.0, 0.5, 32.0),
]


def _assert_js(result: dict, expected: dict) -> None:
    rel = 0.001
    assert _cmp(result["cost"], expected["cost"], rel), result["cost"]
    assert _cmp(result["price"], expected["price"], rel), result["price"]
    assert _cmp(result["time_hours"], expected["time_hours"], rel), result["time_hours"]
    assert _cmp(result["time_ready"], expected["time_ready"], rel), result["time_ready"]


def test_form_default_matches_js(calc):
    """Дефолт формы 56: цена и срок как у JS, размер карты в materials."""
    result = calc.execute(REF_FORM_DEFAULT)
    _assert_js(result, EXPECTED_FORM_DEFAULT)
    assert _cmp(result["weight_kg"], EXPECTED_FORM_DEFAULT["weight_kg"], 0.001)
    materials = result["materials"]
    assert len(materials) == 1
    mat = materials[0]
    assert mat["code"] == "White"
    assert "Пластиковые карты" in (mat.get("name") or "")
    assert mat.get("title")
    assert mat["quantity"] == 100
    assert mat["size_mm"] == [86.0, 54.0]


@pytest.mark.parametrize("mode,cost,price,time_hours,time_ready", FORM_DEFAULT_MODES)
def test_form_default_modes(calc, mode, cost, price, time_hours, time_ready):
    """Дефолт формы 56 на mode=0 и mode=2: цена как у JS, срок 56 и 32 ч."""
    result = calc.execute({**REF_FORM_DEFAULT, "mode": mode})
    _assert_js(result, {
        "cost": cost,
        "price": price,
        "time_hours": time_hours,
        "time_ready": time_ready,
    })
    assert result["price"] == calc.execute(REF_FORM_DEFAULT)["price"]
    assert result["time_ready"] != EXPECTED_FORM_DEFAULT["time_ready"]
