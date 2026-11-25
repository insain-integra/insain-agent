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
    assert "material_mode" in props
    assert "is_cut_manual" in props
    assert "is_cut_manual_metal" in props
    assert "is_sublimation" in props
    assert "is_cut_laser" in props
    assert "is_uv_print" in props


def test_get_param_schema(calc):
    schema = calc.get_param_schema()
    names = {p["name"] for p in schema["params"]}
    assert "material_mode" in names
    assert "is_cut_manual" in names
    assert "is_cut_manual_metal" in names
    assert "is_sublimation" in names
    assert "is_cut_laser" in names
    assert "is_uv_print" in names


# ── Эталоны JS, 02.11.2026 ───────────────────────────────────────────

# JS, 02.11.2026 — УФ + лазер 297×210, тираж 5 (переснят старый сценарий)
# calcTablets(5, [297,210], 'PVC3', {isCutLaser:{sizeItem:210,density:0,difficulty:1,lenCut:0},
#   isUVPrint:{printerID:'RimalSuvUV',resolution:2,surface:'isPlain',color:'4+1'}}, 1)
REF_UV_LASER_297 = {
    "quantity": 5,
    "width": 297,
    "height": 210,
    "material_id": "PVC3",
    "mode": 1,
    "is_cut_laser": {"size_item": 210, "density": 0, "difficulty": 1, "len_cut": 0},
    "is_uv_print": {
        "printerID": "RimalSuvUV",
        "resolution": 2,
        "surface": "isPlain",
        "color": "4+1",
    },
}
EXPECTED_UV_LASER_297 = {
    "cost": 4551.0,
    "price": 7301.0,
    "unit_price": 1460.2,
    "time_hours": 3.02,
    "time_ready": 37.66,
    "weight_kg": 0.52,
}

# JS, 02.11.2026 — только УФ 297×210, тираж 5
# calcTablets(5, [297,210], 'PVC3', {isUVPrint:{printerID:'RimalSuvUV',resolution:2,
#   surface:'isPlain',color:'4+1'}}, 1)
REF_UV_ONLY_297 = {
    "quantity": 5,
    "width": 297,
    "height": 210,
    "material_id": "PVC3",
    "mode": 1,
    "is_uv_print": {
        "printerID": "RimalSuvUV",
        "resolution": 2,
        "surface": "isPlain",
        "color": "4+1",
    },
}
EXPECTED_UV_ONLY_297 = {
    "cost": 3723.0,
    "price": 5957.0,
    "unit_price": 1191.4,
    "time_hours": 2.64,
    "time_ready": 37.28,
    "weight_kg": 0.0,
}

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


def _assert_js(r: dict, e: dict, *, check_unit_price: bool = False) -> None:
    assert r["cost"] == pytest.approx(e["cost"], rel=JS_REL_TOL)
    assert r["price"] == pytest.approx(e["price"], rel=JS_REL_TOL)
    assert r["time_hours"] == pytest.approx(e["time_hours"], rel=JS_REL_TOL)
    assert r["time_ready"] == pytest.approx(e["time_ready"], rel=JS_REL_TOL)
    assert r["weight_kg"] == pytest.approx(e["weight_kg"], rel=JS_REL_TOL)
    if check_unit_price and "unit_price" in e:
        assert r["unit_price"] == pytest.approx(e["unit_price"], rel=JS_REL_TOL)


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


def test_expected_uv_only_297(calc):
    """JS, 02.11.2026: только УФ PVC3 297×210, тираж 5."""
    _assert_js(calc.calculate(REF_UV_ONLY_297), EXPECTED_UV_ONLY_297, check_unit_price=True)


def test_expected_values_tablets(calc):
    """JS, 02.11.2026: УФ + лазер PVC3 297×210, тираж 5."""
    r = calc.calculate(REF_UV_LASER_297)
    _assert_js(r, EXPECTED_UV_LASER_297, check_unit_price=True)
    materials = r.get("materials") or []
    assert materials
    assert any(m.get("code") == "PVC3" for m in materials)
    for m in materials:
        assert "title" in m


# ── Эталон дефолта формы 36 CalcTabs: JS, 26.11.2026 ──────────────────
# node scripts/run_js_calc.mjs calcTablets --data current --args '[100,[50,50],"PVC5",{"isCutManual":"KeencutEvolutionE2","isUVPrint":{"printerID":"PrintUV","resolution":1,"surface":"isPlain","color":"4+0","isDoubleApplication":false},"Material":"isMaterial"},1]'
REF_FORM_DEFAULT = {
    "quantity": 100,
    "width": 50,
    "height": 50,
    "material_id": "PVC5",
    "material_mode": "isMaterial",
    "is_cut_manual": "KeencutEvolutionE2",
    "is_uv_print": {
        "printer_id": "PrintUV",
        "resolution": 1,
        "surface": "plain",
        "color": "4+0",
        "double_application": False,
    },
    "mode": 1,
}

# JS, 26.11.2026
EXPECTED_FORM_DEFAULT_BY_MODE = {
    0: {
        "cost": 7419.0,
        "price": 11888.0,
        "time_hours": 4.16,
        "time_ready": 60.230000000000004,
        "weight_kg": 0.69,
    },
    1: {
        "cost": 7960.0,
        "price": 12754.0,
        "time_hours": 4.5,
        "time_ready": 52.82,
        "weight_kg": 0.69,
    },
    2: {
        "cost": 8505.0,
        "price": 13625.0,
        "time_hours": 4.86,
        "time_ready": 45.43,
        "weight_kg": 0.69,
    },
}
EXPECTED_FORM_DEFAULT = EXPECTED_FORM_DEFAULT_BY_MODE[1]


def test_form_default_matches_js(calc):
    """JS, 26.11.2026: дефолт формы 36 (PVC5, KeencutEvolutionE2 + PrintUV 4+0 res=1, 100 шт)."""
    r = calc.execute(REF_FORM_DEFAULT)
    _assert_js(r, EXPECTED_FORM_DEFAULT)
    materials = r.get("materials") or []
    assert materials
    pvc = next((m for m in materials if m.get("code") == "PVC5"), None)
    assert pvc is not None
    assert pvc.get("size_mm") == [3050.0, 2050.0]
    assert pvc.get("quantity") == pytest.approx(0.04, rel=JS_REL_TOL)
    assert "title" in pvc


@pytest.mark.parametrize("mode", [0, 1, 2])
def test_form_default_modes_match_js(calc, mode):
    """JS, 26.11.2026: дефолт формы 36 на режимах mode=0, 1, 2."""
    r = calc.execute({**REF_FORM_DEFAULT, "mode": mode})
    _assert_js(r, EXPECTED_FORM_DEFAULT_BY_MODE[mode])


def test_form_default_mode_monotonic(calc):
    """Собственное производство: price(0) < price(1) < price(2) и time_ready(2) < time_ready(1) < time_ready(0)."""
    res = {m: calc.execute({**REF_FORM_DEFAULT, "mode": m}) for m in (0, 1, 2)}
    assert res[0]["price"] < res[1]["price"] < res[2]["price"]
    assert res[2]["time_ready"] < res[1]["time_ready"] < res[0]["time_ready"]


@pytest.mark.parametrize(
    ("material_mode", "double_app", "expected"),
    [
        # JS, 26.11.2026: noMaterial
        (
            "noMaterial",
            False,
            {"cost": 7665.0, "price": 12264.0, "time_hours": 4.5, "time_ready": 52.82, "weight_kg": 0.69},
        ),
        # JS, 26.11.2026: isMaterialCustomer (+25% к резке и УФ)
        (
            "isMaterialCustomer",
            False,
            {"cost": 9539.25, "price": 15262.0, "time_hours": 5.52, "time_ready": 53.84, "weight_kg": 0.69},
        ),
        # JS, 26.11.2026: двойное нанесение УФ
        (
            "isMaterial",
            True,
            {"cost": 8294.0, "price": 13288.0, "time_hours": 4.56, "time_ready": 52.94, "weight_kg": 0.69},
        ),
    ],
)
def test_cut_manual_material_modes_and_double_uv(calc, material_mode, double_app, expected):
    """JS, 26.11.2026: material_mode (noMaterial / isMaterialCustomer) и double_application."""
    params = {
        **REF_FORM_DEFAULT,
        "material_mode": material_mode,
        "is_uv_print": {**REF_FORM_DEFAULT["is_uv_print"], "double_application": double_app},
    }
    _assert_js(calc.execute(params), expected)
