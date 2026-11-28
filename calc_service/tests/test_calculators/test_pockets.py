"""Карманы стенда. Эталон частей — раннер calcLaser и calcPutTape, 29.11.2026."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

_calc_service = Path(__file__).resolve().parent.parent.parent
if str(_calc_service) not in sys.path:
    sys.path.insert(0, str(_calc_service))

from calculators.pockets import PocketsCalculator


@pytest.fixture(scope="module")
def calc():
    return PocketsCalculator()


def test_catalog_pocket_fields(calc):
    r = calc.execute({
        "quantity": 2,
        "pocket_id": "PocketAcrylicA4V",
        "border_id": "Avery500c",
        "mode": 1,
    })
    for key in ("cost", "price", "unit_price", "time_hours", "time_ready", "weight_kg", "materials"):
        assert key in r
    assert r["price"] > 0
    assert r["time_ready"] > r["time_hours"] > 0
    assert r["unit_price"] == pytest.approx(round(r["price"] / 2, 2))
    for item in r["materials"]:
        assert item["code"]
        assert item["name"] and item["name"] != item["code"]
        assert item["title"] and item["title"] != item["code"]


def test_catalog_pocket_ignores_mode(calc):
    """JS сбрасывает mode в 0, если карман есть в справочнике."""
    prices = [
        calc.execute({"quantity": 1, "pocket_id": "PocketPETA4V", "border_id": "Avery500c", "mode": m})["price"]
        for m in (0, 1, 2)
    ]
    assert prices[0] == pytest.approx(prices[1]) == pytest.approx(prices[2])


def test_quantity_required(calc):
    with pytest.raises(ValueError, match="Количество"):
        calc.execute({"quantity": 0, "pocket_id": "PocketPETA4V"})
