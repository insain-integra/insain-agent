"""
Тесты калькулятора закатных значков (button_pins).
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

_calc_service = Path(__file__).resolve().parent.parent.parent
if _calc_service.name == "calc_service" and str(_calc_service) not in sys.path:
    sys.path.insert(0, str(_calc_service))

from calculators.button_pins import ButtonPinsCalculator

REQUIRED = ("cost", "price", "unit_price", "time_hours", "time_ready", "weight_kg", "materials")


def _cmp(got: float, expected: float, rel: float = 0.001) -> bool:
    return abs(got - expected) <= rel * max(abs(expected), 1e-9)


@pytest.fixture(scope="module")
def calc():
    return ButtonPinsCalculator()


# JS scripts/run_js_calc.mjs calcButtonPins --data current, 17.11.2026
# '[2,"D38",{},1]'
REF_PARAMS = {
    "quantity": 2,
    "pin_id": "D38",
    "mode": 1,
}
EXPECTED_REF = {
    "cost": 519.3422813333333,
    "price": 759.88388712,
    "unit_price": 379.94,
    "time_hours": 0.27,
    "time_ready": 16.27,
    "weight_kg": 0.0108,
}
# time_hours/time_ready: cut_plotter и lamination отдают время через round,
# раннер — ceil. Расхождение 0.02 ч, цену не двигает.
TIME_ABS = 0.03

# '[2500,"D38",{},1]' — ветка Амалит, 17.11.2026
AMALIT_PARAMS = {
    "quantity": 2500,
    "pin_id": "D38",
    "mode": 1,
}
EXPECTED_AMALIT = {
    "cost": 28905,
    "price": 47982.30000000001,
    "unit_price": 19.19,
    "time_hours": 10.5,
    "time_ready": 50.5,
    "weight_kg": 13.5,
}


@pytest.fixture(scope="module")
def ref_result(calc):
    return calc.execute(REF_PARAMS)


def test_slug(calc):
    assert calc.slug == "button_pins"


def test_required_fields_and_materials(ref_result):
    for key in REQUIRED:
        assert key in ref_result
    assert ref_result["time_ready"] > ref_result["time_hours"] > 0
    materials = ref_result["materials"]
    assert materials
    codes = []
    for item in materials:
        assert item.get("code")
        assert isinstance(item.get("name"), str) and item["name"].strip()
        assert isinstance(item.get("title"), str) and item["title"].strip()
        assert item["name"].strip() != str(item["code"])
        assert item["title"].strip() != str(item["code"])
        codes.append(item["code"])
    assert "D38" in codes
    assert "ColotechPlus90M" in codes


def test_share_url(ref_result):
    assert "share_url" in ref_result
    assert "button_pins" in ref_result["share_url"]


def test_get_options(calc):
    opts = calc.get_options()
    assert "pins" in opts and "modes" in opts
    codes = [item["code"] for item in opts["pins"]]
    assert codes == ["D25", "D38", "D56", "D78"]


def test_get_tool_schema(calc):
    schema = calc.get_tool_schema()
    assert schema.get("name") == "calc_button_pins"
    assert "pin_id" in schema["parameters"]["properties"]
    assert "quantity" in schema["parameters"]["required"]


def test_expected_values_own_production(ref_result):
    """Себестоимость и цена — раннер JS, rel ≤ 0.001."""
    e = EXPECTED_REF
    assert _cmp(ref_result["cost"], e["cost"]), f"cost: {ref_result['cost']}"
    assert _cmp(ref_result["price"], e["price"]), f"price: {ref_result['price']}"
    assert _cmp(ref_result["unit_price"], e["unit_price"]), f"unit_price: {ref_result['unit_price']}"
    assert _cmp(ref_result["weight_kg"], e["weight_kg"])
    assert abs(ref_result["time_hours"] - e["time_hours"]) <= TIME_ABS
    assert abs(ref_result["time_ready"] - e["time_ready"]) <= TIME_ABS
    pin = next(item for item in ref_result["materials"] if item["code"] == "D38")
    assert "38" in pin["name"]
    assert pin["quantity"] == 3


def test_expected_values_amalit(calc):
    result = calc.execute(AMALIT_PARAMS)
    e = EXPECTED_AMALIT
    assert _cmp(result["cost"], e["cost"]), result["cost"]
    assert _cmp(result["price"], e["price"]), result["price"]
    assert _cmp(result["unit_price"], e["unit_price"]), result["unit_price"]
    assert _cmp(result["time_hours"], e["time_hours"])
    assert _cmp(result["time_ready"], e["time_ready"])
    assert _cmp(result["weight_kg"], e["weight_kg"])
    assert result["time_ready"] > result["time_hours"] > 0


def test_modes_and_larger_quantity(calc):
    economy = calc.calculate({**REF_PARAMS, "mode": 0})
    standard = calc.calculate({**REF_PARAMS, "mode": 1})
    express = calc.calculate({**REF_PARAMS, "mode": 2})
    for result in (economy, standard, express):
        assert result["time_ready"] > result["time_hours"] > 0
    assert economy["time_ready"] > standard["time_ready"] > express["time_ready"]
    larger = calc.calculate({**REF_PARAMS, "quantity": 100})
    assert larger["time_hours"] > standard["time_hours"]
    assert larger["price"] > standard["price"]


def test_packing_increases_price(calc):
    plain = calc.calculate(REF_PARAMS)
    packed = calc.calculate({**REF_PARAMS, "is_packing": True})
    assert packed["price"] > plain["price"]
    assert packed["time_hours"] > plain["time_hours"]


def test_unknown_pin_raises(calc):
    with pytest.raises(ValueError, match="размер значка"):
        calc.calculate({"quantity": 2, "pin_id": "D99", "mode": 1})


def test_bad_quantity_raises(calc):
    with pytest.raises(ValueError, match="Тираж"):
        calc.calculate({"quantity": 0, "pin_id": "D38", "mode": 1})


def test_bad_mode_raises(calc):
    with pytest.raises(ValueError, match="режим"):
        calc.calculate({"quantity": 2, "pin_id": "D38", "mode": 9})


# Дефолт формы 12: numN=100, dpdSize preselect 0 → D25, упаковка выключена, режим 1.
# node scripts/run_js_calc.mjs calcButtonPins --data current --args '[100,"D25",{},1]' — 17.11.2026
REF_FORM_DEFAULT = {
    "quantity": 100,
    "pin_id": "D25",
    "mode": 1,
}
EXPECTED_FORM_DEFAULT = {
    "cost": 2346.9722813333333,
    "price": 3513.86888712,
    "time_hours": 0.93,
    "time_ready": 16.93,
    "weight_kg": 0.25,
}


def test_form_default_button_pins(calc):
    """Дефолт формы 12: 100×D25, без упаковки, стандарт. Цена — раннер, rel ≤ 0.001."""
    result = calc.execute(REF_FORM_DEFAULT)
    expected = EXPECTED_FORM_DEFAULT
    assert _cmp(result["cost"], expected["cost"]), result["cost"]
    assert _cmp(result["price"], expected["price"]), result["price"]
    assert abs(result["time_hours"] - expected["time_hours"]) <= TIME_ABS
    assert abs(result["time_ready"] - expected["time_ready"]) <= TIME_ABS
    assert _cmp(result["weight_kg"], expected["weight_kg"])
