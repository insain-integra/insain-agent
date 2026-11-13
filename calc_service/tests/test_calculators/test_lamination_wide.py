"""
Тесты калькулятора широкоформатной ламинации (lamination_wide).
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

_calc_service = Path(__file__).resolve().parent.parent.parent
if _calc_service.name == "calc_service" and str(_calc_service) not in sys.path:
    sys.path.insert(0, str(_calc_service))

from calculators import CALCULATORS
from calculators.lamination_wide import LaminationWideCalculator

REQUIRED_FIELDS = ("cost", "price", "unit_price", "time_hours", "time_ready", "weight_kg", "materials")


@pytest.fixture(scope="module")
def calc():
    return LaminationWideCalculator()


def _cmp(a: float, b: float, rel: float = 0.001) -> bool:
    return abs(a - b) <= rel * max(abs(b), 1e-9)


def test_registered():
    assert "lamination_wide" in CALCULATORS
    assert CALCULATORS["lamination_wide"].slug == "lamination_wide"


# JS, 14.11.2026 — calcLaminationWide, прайс calc_service/data. timeReady в JS не задаётся (0).
# node scripts/run_js_calc.mjs calcLaminationWide --data current --args '[1,[1270,0],1]'
# node scripts/run_js_calc.mjs calcLaminationWide --data current --args '[10,[1000,500],1]'
# node scripts/run_js_calc.mjs calcLaminationWide --data current --args '[3,[1500,2000],2]'
# node scripts/run_js_calc.mjs calcLaminationWide --data current --args '[3,[1500,2000],0]'
REF_CASES = [
    (
        {"quantity": 1, "width": 1270, "height": 0, "mode": 1},
        {"cost": 465.0, "price": 753.0, "time_hours": 0.01, "weight_kg": 0.09},
    ),
    (
        {"quantity": 10, "width": 1000, "height": 500, "mode": 1},
        {"cost": 2394.75, "price": 3877.95, "time_hours": 0.06, "weight_kg": 0.46},
    ),
    (
        {"quantity": 3, "width": 1500, "height": 2000, "mode": 2},
        {"cost": 4436.1, "price": 7183.62, "time_hours": 0.1, "weight_kg": 0.84},
    ),
    (
        {"quantity": 3, "width": 1500, "height": 2000, "mode": 0},
        {"cost": 4310.55, "price": 6980.31, "time_hours": 0.1, "weight_kg": 0.82},
    ),
]


@pytest.mark.parametrize("params,expected", REF_CASES)
def test_expected_values_js(calc, params, expected):
    r = calc.execute(params)
    assert _cmp(r["cost"], expected["cost"]), r["cost"]
    assert _cmp(r["price"], expected["price"]), r["price"]
    assert _cmp(r["unit_price"], expected["price"] / params["quantity"]), r["unit_price"]
    assert r["time_hours"] == pytest.approx(expected["time_hours"])
    assert r["weight_kg"] == pytest.approx(expected["weight_kg"])


def test_response_fields_and_materials(calc):
    r = calc.execute({"quantity": 10, "width": 1000, "height": 500, "mode": 1})
    for key in REQUIRED_FIELDS:
        assert key in r, key
    assert "share_url" in r
    materials = r["materials"]
    assert len(materials) == 1
    mat = materials[0]
    for key in ("code", "name", "title"):
        assert mat.get(key), key
    assert mat["code"] == "LaminatDLCLAM"
    assert mat["unit"] == "м"
    assert mat["size_mm"] == [1520.0, 0.0]
    # 10 × 0,5 м² × 1,03 брака = 5,15 м² на ширине 1,52 м
    assert mat["quantity"] == pytest.approx(5.15 / 1.52, abs=1e-4)


def test_time_ready_after_time_hours(calc):
    r = calc.execute({"quantity": 10, "width": 1000, "height": 500, "mode": 1})
    assert r["time_ready"] > r["time_hours"] > 0


def test_minimum_one_square_meter(calc):
    """Меньше 1 м² считается как 1 м²."""
    small = calc.execute({"quantity": 1, "width": 100, "height": 100, "mode": 1})
    zero = calc.execute({"quantity": 1, "width": 1520, "height": 0, "mode": 1})
    assert small["price"] == pytest.approx(zero["price"])


def test_bigger_quantity_more_time(calc):
    small = calc.execute({"quantity": 10, "width": 1000, "height": 1000, "mode": 1})
    big = calc.execute({"quantity": 100, "width": 1000, "height": 1000, "mode": 1})
    assert big["time_hours"] > small["time_hours"]
    assert big["price"] > small["price"]


@pytest.mark.parametrize(
    "params,message",
    [
        ({"quantity": 0, "width": 1000, "height": 500}, "Тираж"),
        ({"quantity": 1, "width": 0, "height": 500}, "Размер"),
        ({"quantity": 1, "width": 1000, "height": -1}, "Размер"),
    ],
)
def test_invalid_input(calc, params, message):
    with pytest.raises(ValueError, match=message):
        calc.execute(params)


def test_http_post():
    from fastapi.testclient import TestClient
    from main import app

    response = TestClient(app).post(
        "/api/v1/calc/lamination_wide",
        json={"quantity": 10, "width": 1000, "height": 500, "mode": 1},
    )
    assert response.status_code == 200, response.text
    assert _cmp(response.json()["price"], 3877.95)


def test_tool_schema(calc):
    schema = calc.get_tool_schema()
    assert schema["name"] == "calc_lamination_wide"
    assert set(schema["parameters"]["properties"]) == {"quantity", "width", "height", "mode"}
