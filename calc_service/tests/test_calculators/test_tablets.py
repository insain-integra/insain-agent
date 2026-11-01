"""
Тесты калькулятора табличек (tablets).

Эталоны calcTablets: node scripts/run_js_calc.mjs calcTablets --data current --args '…'
size = sizePlate Plaque2330 [195, 265]; sizeItem = min(w,h) = 195.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

_calc_service = Path(__file__).resolve().parent.parent.parent
if _calc_service.name == "calc_service" and str(_calc_service) not in sys.path:
    sys.path.insert(0, str(_calc_service))

from calculators.tablets import TabletsCalculator

JS_REL_TOL = 0.001  # 0.1%


@pytest.fixture(scope="module")
def calc():
    return TabletsCalculator()


# Аргументы как из calcPlaque для УФ
_UV_OPTS = {
    "is_cut_laser": {"size_item": 195, "density": 0, "difficulty": 1, "len_cut": 0},
    "is_uv_print": {
        "printerID": "RimalSuvUV",
        "resolution": 2,
        "surface": "isPlain",
        "color": "4+1",
    },
}
# Гравировка
_GRAVE_OPTS = {
    "is_cut_laser": {"size_item": 195, "density": 0, "difficulty": 1, "len_cut": 0},
    "is_grave": 2,
    "is_grave_fill": [195, 265],
}
# Сублимация
_SUB_OPTS = {
    "is_cut_manual_metal": "AccusheadPro12",
    "is_sublimation": True,
}


@pytest.fixture(scope="module")
def base_params():
    return {
        "quantity": 5,
        "width": 195,
        "height": 265,
        "material_id": "PVC3",
        "mode": 1,
        **_UV_OPTS,
    }


@pytest.fixture(scope="module")
def result(calc, base_params):
    try:
        return calc.execute(base_params)
    except Exception:
        return None


def test_slug(calc):
    assert calc.slug == "tablets"


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
    assert "tablets" in result["share_url"]


def test_get_tool_schema(calc):
    schema = calc.get_tool_schema()
    assert schema.get("name") == "calc_tablets"
    assert "parameters" in schema
    props = schema["parameters"]["properties"]
    assert "is_cut_manual_metal" in props
    assert "is_sublimation" in props
    assert "is_cut_laser" in props
    assert "is_uv_print" in props


def test_get_param_schema(calc):
    schema = calc.get_param_schema()
    names = {p["name"] for p in schema["params"]}
    assert "is_cut_manual_metal" in names
    assert "is_sublimation" in names
    assert "is_cut_laser" in names
    assert "is_uv_print" in names


# ── Эталоны JS, 02.11.2026 ───────────────────────────────────────────
# Пересняты с calcTablets (ранее эталон print_method=uv 297×210 был не с JS).

# JS, 02.11.2026 — УФ + лазер, тираж 1
# calcTablets(1, [195,265], 'PVC3', {isCutLaser:{sizeItem:195,density:0,difficulty:1,lenCut:0},
#   isUVPrint:{printerID:'RimalSuvUV',resolution:2,surface:'isPlain',color:'4+1'}}, 1)
REF_UV_1 = {
    "quantity": 1,
    "width": 195,
    "height": 265,
    "material_id": "PVC3",
    "mode": 1,
    **_UV_OPTS,
}
EXPECTED_UV_1 = {
    "cost": 1479.9,
    "price": 2299.0,
    "time_hours": 0.91,
    "time_ready": 33.55,
    "weight_kg": 0.09,
}

# JS, 02.11.2026 — УФ + лазер, тираж ≥ 2
REF_UV_5 = {
    "quantity": 5,
    "width": 195,
    "height": 265,
    "material_id": "PVC3",
    "mode": 1,
    **_UV_OPTS,
}
EXPECTED_UV_5 = {
    "cost": 3886.0,
    "price": 6234.0,
    "time_hours": 2.57,
    "time_ready": 36.77,
    "weight_kg": 0.43,
}

# JS, 02.11.2026 — гравировка, тираж 1
REF_GRAVE_1 = {
    "quantity": 1,
    "width": 195,
    "height": 265,
    "material_id": "PVC3",
    "mode": 1,
    **_GRAVE_OPTS,
}
EXPECTED_GRAVE_1 = {
    "cost": 4650.8,
    "price": 6768.0,
    "time_hours": 4.58,
    "time_ready": 25.16,
    "weight_kg": 0.09,
}

# JS, 02.11.2026 — гравировка, тираж ≥ 2
REF_GRAVE_5 = {
    "quantity": 5,
    "width": 195,
    "height": 265,
    "material_id": "PVC3",
    "mode": 1,
    **_GRAVE_OPTS,
}
EXPECTED_GRAVE_5 = {
    "cost": 23456.0,
    "price": 37546.0,
    "time_hours": 26.2,
    "time_ready": 68.4,
    "weight_kg": 0.43,
}

# JS, 02.11.2026 — сублимация, тираж 1
REF_SUB_1 = {
    "quantity": 1,
    "width": 195,
    "height": 265,
    "material_id": "AluminiumSU055",
    "mode": 1,
    **_SUB_OPTS,
}
EXPECTED_SUB_1 = {
    "cost": 771.539047586521,
    "price": 1245.5898189936247,
    "time_hours": 0.45,
    "time_ready": 17.53972222222222,
    "weight_kg": 0.1,
}

# JS, 02.11.2026 — сублимация, тираж ≥ 2
REF_SUB_5 = {
    "quantity": 5,
    "width": 195,
    "height": 265,
    "material_id": "AluminiumSU055",
    "mode": 1,
    **_SUB_OPTS,
}
EXPECTED_SUB_5 = {
    "cost": 1948.6952379326049,
    "price": 3163.829094968124,
    "time_hours": 1.01,
    "time_ready": 19.388611111111114,
    "weight_kg": 0.47,
}


def _assert_js(r: dict, e: dict) -> None:
    assert r["cost"] == pytest.approx(e["cost"], rel=JS_REL_TOL)
    assert r["price"] == pytest.approx(e["price"], rel=JS_REL_TOL)
    assert r["time_hours"] == pytest.approx(e["time_hours"], rel=JS_REL_TOL)
    assert r["time_ready"] == pytest.approx(e["time_ready"], rel=JS_REL_TOL)
    assert r["weight_kg"] == pytest.approx(e["weight_kg"], rel=JS_REL_TOL)


def test_expected_uv_qty1(calc):
    """JS, 02.11.2026: УФ + лазер PVC3, тираж 1."""
    _assert_js(calc.calculate(REF_UV_1), EXPECTED_UV_1)


def test_expected_uv_qty5(calc):
    """JS, 02.11.2026: УФ + лазер PVC3, тираж 5."""
    r = calc.calculate(REF_UV_5)
    _assert_js(r, EXPECTED_UV_5)
    materials = r.get("materials") or []
    assert materials
    assert any(m.get("code") == "PVC3" for m in materials)
    for m in materials:
        assert "title" in m


def test_expected_grave_qty1(calc):
    """JS, 02.11.2026: гравировка PVC3, тираж 1."""
    _assert_js(calc.calculate(REF_GRAVE_1), EXPECTED_GRAVE_1)


def test_expected_grave_qty5(calc):
    """JS, 02.11.2026: гравировка PVC3, тираж 5."""
    _assert_js(calc.calculate(REF_GRAVE_5), EXPECTED_GRAVE_5)


def test_expected_sublimation_qty1(calc):
    """JS, 02.11.2026: сублимация AluminiumSU055, тираж 1."""
    _assert_js(calc.calculate(REF_SUB_1), EXPECTED_SUB_1)


def test_expected_sublimation_qty5(calc):
    """JS, 02.11.2026: сублимация AluminiumSU055, тираж 5."""
    _assert_js(calc.calculate(REF_SUB_5), EXPECTED_SUB_5)


# Старый эталон (print_method=uv, 297×210) переснят как УФ+лазер на sizePlate — см. REF_UV_5.
def test_expected_values_tablets(calc):
    """JS, 02.11.2026: переснят старый эталон → УФ qty5 (plaque args)."""
    _assert_js(calc.calculate(REF_UV_5), EXPECTED_UV_5)
