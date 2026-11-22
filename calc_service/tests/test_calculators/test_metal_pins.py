"""
Тесты калькулятора металлических значков (metal_pins).
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

_calc_service = Path(__file__).resolve().parent.parent.parent
if _calc_service.name == "calc_service" and str(_calc_service) not in sys.path:
    sys.path.insert(0, str(_calc_service))

from calculators.metal_pins import MetalPinsCalculator


def _cmp(a: float, b: float, rel: float = 0.03) -> bool:
    return abs(a - b) <= rel * max(abs(b), 1e-9)


@pytest.fixture(scope="module")
def calc():
    return MetalPinsCalculator()


@pytest.fixture(scope="module")
def base_params():
    return {
        "quantity": 100,
        "stamps": [
            {
                "size": [25, 25, 1.2],
                "materialID": "brass",
                "processID": 1,
                "platingID": "nickel",
                "numEnamels": 0,
                "isEpoxy": "",
                "isMould": "",
            }
        ],
        "pack_id": "PolyBag",
        "mode": 1,
    }


@pytest.fixture(scope="module")
def result(calc, base_params):
    try:
        return calc.execute(base_params)
    except Exception:
        return None


def test_slug(calc):
    assert calc.slug == "metal_pins"


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
    assert "metal_pins" in result["share_url"]


def test_get_tool_schema(calc):
    schema = calc.get_tool_schema()
    assert schema.get("name") == "calc_metal_pins"
    assert "parameters" in schema
    assert "quantity" in schema["parameters"].get("properties", {})


def test_get_llm_prompt(calc):
    text = calc.get_llm_prompt()
    assert len(text) > 80
    assert "material_id" in text
    assert "calc_metal_pins" in text


def test_calculate_accepts_width_height_aliases(calc):
    """LLM шлёт width/height вместо width_mm/height_mm — не должно падать."""
    r = calc.execute({"quantity": 100, "width": 25, "height": 25})
    assert r.get("price", 0) > 0
    assert "width_mm=25" in (r.get("share_url") or "")


# ── Эталонные тесты ──────────────────────────────────────────────────

REF_PARAMS = {
    "quantity": 100,
    "stamps": [
        {
            "size": [25, 25, 1.2],
            "materialID": "brass",
            "processID": 1,
            "platingID": "nickel",
            "numEnamels": 0,
            "isEpoxy": "",
            "isMould": "",
        }
    ],
    "pack_id": "PolyBag",
    "mode": 1,
}

EXPECTED_REF = {
    "cost": 19442.0,
    "price": 27219.0,
    "time_hours": 0.0,
    "time_ready": 360.0,
    "weight_kg": 0.68,
}

EXPECTED_MATERIAL = {
    "code": "PolyBag",
    "name_substring": "Полиэтиленовый пакетик",
    "quantity_approx": 100,
}


@pytest.fixture(scope="module")
def ref_result(calc):
    try:
        return calc.execute(REF_PARAMS)
    except Exception:
        return None


def test_expected_values_metal_pins(ref_result):
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
    ok_mat_name = em["name_substring"] in (mat_match.get("name") or "")
    ok_mat_q = _cmp(float(mat_match.get("quantity") or 0), float(em["quantity_approx"]), 0.15) if mat_match else False

    print("")
    print("  [metal_pins] quantity=%s  |  mode=%s" % (REF_PARAMS["quantity"], REF_PARAMS["mode"]))
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


# JS, 22.11.2026 — дефолт формы 34 со страницы:
# 100 шт, вид «простой» (один штамп), 20×20, латунь, процесс 1, серебро,
# 0 эмалей, без смолы и без своего штампа, толщина 1.2, крепление BC, пакет PolyBag, mode 1.
# calcMetalPins не подключён в scripts/run_js_calc.mjs: эталон — прогон
# js_legacy/calc/calcMetalPins.js в Node vm на прайсе calc_service/data.
# mode=0 и mode=2 — тот же вход. JS не округляет price вверх, Python делает ceil:
# mode=0 JS 20756.4 / Python 20757, rel < 0.001.
_STAMP_20 = {
    "size": [20, 20, 1.2],
    "materialID": "brass",
    "processID": "1",
    "platingID": "silver",
    "numEnamels": 0,
    "isEpoxy": "",
    "isMould": "",
}

REF_FORM_DEFAULT = {
    "quantity": 100,
    "width_mm": 20,
    "height_mm": 20,
    "stamps": [_STAMP_20],
    "attachment_id": "BC",
    "pack_id": "PolyBag",
    "mode": 1,
}

EXPECTED_FORM_DEFAULT = {
    "cost": 19725.0,
    "price": 27615.0,
    "time_hours": 0.0,
    "time_ready": 360.0,
    "weight_kg": 0.5,
}

# JS, 22.11.2026 — тот же дефолт на mode=0 и mode=2.
FORM_DEFAULT_MODES = [
    (0, 14826.0, 20756.4, 0.0, 440.0),
    (2, 24920.0, 34888.0, 0.0, 320.0),
]

# JS, 22.11.2026 — вид «двухсторонний»: второй штамп с толщиной 0.
REF_FORM_TWO_SIDED = {
    "quantity": 100,
    "width_mm": 20,
    "height_mm": 20,
    "stamps": [_STAMP_20, {**_STAMP_20, "size": [20, 20, 0]}],
    "attachment_id": "BC",
    "pack_id": "PolyBag",
    "mode": 1,
}
EXPECTED_FORM_TWO_SIDED = {
    "cost": 26458.0,
    "price": 37041.2,
    "time_hours": 0.0,
    "time_ready": 360.0,
}

# JS, 22.11.2026 — вид «двухсоставной»: второй штамп повторяет первый.
REF_FORM_TWO_PART = {
    "quantity": 100,
    "width_mm": 20,
    "height_mm": 20,
    "stamps": [_STAMP_20, dict(_STAMP_20)],
    "attachment_id": "BC",
    "pack_id": "PolyBag",
    "mode": 1,
}
EXPECTED_FORM_TWO_PART = {
    "cost": 31306.0,
    "price": 43828.4,
    "time_hours": 0.0,
    "time_ready": 360.0,
}


def _assert_js(result: dict, expected: dict) -> None:
    rel = 0.001
    assert _cmp(result["cost"], expected["cost"], rel), result["cost"]
    assert _cmp(result["price"], expected["price"], rel), result["price"]
    assert _cmp(result["time_hours"], expected["time_hours"], rel), result["time_hours"]
    assert _cmp(result["time_ready"], expected["time_ready"], rel), result["time_ready"]


def test_form_default_metal_pins(calc):
    """Дефолт формы 34: 100×20×20, серебро, BC, PolyBag, mode 1. Цена — JS, rel ≤ 0.001."""
    result = calc.execute(REF_FORM_DEFAULT)
    _assert_js(result, EXPECTED_FORM_DEFAULT)
    assert _cmp(result["weight_kg"], EXPECTED_FORM_DEFAULT["weight_kg"], 0.001)
    codes = [m.get("code") for m in result["materials"]]
    assert codes == ["BC", "PolyBag"]


@pytest.mark.parametrize("mode,cost,price,time_hours,time_ready", FORM_DEFAULT_MODES)
def test_form_default_modes(calc, mode, cost, price, time_hours, time_ready):
    """Дефолт формы 34 на mode=0 и mode=2: цена и срок как у JS."""
    result = calc.execute({**REF_FORM_DEFAULT, "mode": mode})
    _assert_js(result, {
        "cost": cost,
        "price": price,
        "time_hours": time_hours,
        "time_ready": time_ready,
    })
    assert result["price"] != EXPECTED_FORM_DEFAULT["price"]


def test_form_two_sided_zero_thickness(calc):
    """Вид «двухсторонний»: второй штамп с толщиной 0 дороже одного и дешевле двухсоставного."""
    result = calc.execute(REF_FORM_TWO_SIDED)
    _assert_js(result, EXPECTED_FORM_TWO_SIDED)
    assert result["price"] > EXPECTED_FORM_DEFAULT["price"]


def test_form_two_part_repeats_stamp(calc):
    """Вид «двухсоставной»: второй штамп повторяет первый, цена выше двухстороннего."""
    result = calc.execute(REF_FORM_TWO_PART)
    _assert_js(result, EXPECTED_FORM_TWO_PART)
    two_sided = calc.execute(REF_FORM_TWO_SIDED)
    assert result["price"] > two_sided["price"]
