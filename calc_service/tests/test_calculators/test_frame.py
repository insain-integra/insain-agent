"""Рамка стенда. Эталон calcFrame, 29.11.2026, тираж 2 и подвес HangerH35.

node (раннер с загруженным profile.json) calcFrame --data current --args
'[2,[[1000,2],[1000,2]],"AluFrame2Plus",{"isHanger":{"hangerID":"HangerH35","numHanger":2}},1]'
Стоковый scripts/run_js_calc.mjs профиль не грузит и падает на AluFrame2Plus.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

_calc_service = Path(__file__).resolve().parent.parent.parent
if str(_calc_service) not in sys.path:
    sys.path.insert(0, str(_calc_service))

from calculators.frame import FrameCalculator

# JS, 29.11.2026
EXPECTED = {
    "cost": 3118.7466666666664,
    "price": 5095.606666666667,
    "time_hours": 0.7911111111111111,
    "time_ready": 8.79111111111111,
    "weight_kg": 4.072,
}


@pytest.fixture(scope="module")
def calc():
    return FrameCalculator()


def test_frame_with_hangers_matches_js(calc):
    r = calc.execute({
        "quantity": 2,
        "profile_id": "AluFrame2Plus",
        "segments": [[1000, 2], [1000, 2]],
        "is_hanger": {"hanger_id": "HangerH35", "num_hanger": 2},
        "mode": 1,
    })
    for key in ("cost", "price", "unit_price", "time_hours", "time_ready", "weight_kg", "materials"):
        assert key in r
    assert r["cost"] == pytest.approx(EXPECTED["cost"])
    assert r["price"] == pytest.approx(EXPECTED["price"])
    assert r["time_hours"] == pytest.approx(EXPECTED["time_hours"])
    assert r["time_ready"] == pytest.approx(EXPECTED["time_ready"])
    assert r["weight_kg"] == pytest.approx(EXPECTED["weight_kg"])
    assert r["time_ready"] > r["time_hours"] > 0
    codes = {m["code"] for m in r["materials"]}
    assert "AluFrame2Plus" in codes
    assert "HangerH35" in codes
    for item in r["materials"]:
        assert item["name"] and item["name"] != item["code"]
        assert item["title"] and item["title"] != item["code"]


def test_modes_change_price(calc):
    prices = []
    readies = []
    for mode in (0, 1, 2):
        r = calc.execute({
            "quantity": 2,
            "profile_id": "AluFrame2Plus",
            "segments": [[500, 2], [400, 2]],
            "mode": mode,
        })
        prices.append(r["price"])
        readies.append(r["time_ready"])
    assert prices[0] < prices[1] < prices[2]
    assert readies[2] < readies[1] < readies[0]


def test_segment_longer_than_stick(calc):
    with pytest.raises(ValueError, match="длиннее хлыста"):
        calc.execute({
            "quantity": 1,
            "profile_id": "AluFrame2Plus",
            "segments": [[4000, 1]],
        })
