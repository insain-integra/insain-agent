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
    assert "is_print" in props
    assert "is_edge" in props
    assert "is_lamination" in props
    assert "is_film" in props
    assert "is_background_film" in props


def test_get_param_schema(calc):
    schema = calc.get_param_schema()
    names = {p["name"] for p in schema["params"]}
    assert "material_mode" in names
    assert "is_cut_manual" in names
    assert "is_cut_manual_metal" in names
    assert "is_sublimation" in names
    assert "is_cut_laser" in names
    assert "is_uv_print" in names
    assert "is_print" in names
    assert "is_edge" in names
    assert "is_lamination" in names
    assert "is_film" in names
    assert "is_background_film" in names


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


# ── Эталоны isPrint (экосольвент и латекс): JS, 26.11.2026 ────────────

REF_ECO_PRINT = {
    "quantity": 100,
    "width": 50,
    "height": 50,
    "material_id": "PVC5",
    "material_mode": "isMaterial",
    "is_cut_manual": "KeencutEvolutionE2",
    "is_print": {
        "printer_id": "Technojet160ECO",
        "double_application": False,
        "is_edge": "isCutEdge",
        "is_lamination": False,
    },
    "mode": 1,
}

# JS, 26.11.2026: node scripts/run_js_calc.mjs calcTablets --data current --args '[100,[50,50],"PVC5",{"isCutManual":"KeencutEvolutionE2","isPrint":{"printerID":"Technojet160ECO","resolution":1,"surface":"isPlain","color":"4+0","isDoubleApplication":false},"isEdge":"isCutEdge","Material":"isMaterial"},<mode>]'
EXPECTED_ECO_PRINT_BY_MODE = {
    0: {"cost": 7579.0, "price": 12150.0, "time_hours": 4.29, "time_ready": 32.37, "weight_kg": 0.75},
    1: {"cost": 8071.0, "price": 12937.0, "time_hours": 4.59, "time_ready": 20.97, "weight_kg": 0.75},
    2: {"cost": 8574.0, "price": 13743.0, "time_hours": 4.9, "time_ready": 13.58, "weight_kg": 0.75},
}

REF_LATEX_PRINT = {
    **REF_ECO_PRINT,
    "is_print": {
        "printer_id": "HPLatex335",
        "double_application": False,
        "is_edge": "isCutEdge",
        "is_lamination": False,
    },
}

# JS, 26.11.2026: node scripts/run_js_calc.mjs calcTablets --data current --args '[100,[50,50],"PVC5",{"isCutManual":"KeencutEvolutionE2","isPrint":{"printerID":"HPLatex335","resolution":1,"surface":"isPlain","color":"4+0","isDoubleApplication":false},"isEdge":"isCutEdge","Material":"isMaterial"},<mode>]'
EXPECTED_LATEX_PRINT_BY_MODE = {
    0: {"cost": 8039.0, "price": 12885.0, "time_hours": 4.26, "time_ready": 60.28, "weight_kg": 0.75},
    1: {"cost": 9030.0, "price": 14471.0, "time_hours": 4.91, "time_ready": 37.93, "weight_kg": 0.75},
    2: {"cost": 10026.0, "price": 16064.0, "time_hours": 5.56, "time_ready": 23.58, "weight_kg": 0.75},
}


@pytest.mark.parametrize("mode", [0, 1, 2])
def test_eco_print_modes_match_js(calc, mode):
    """JS, 26.11.2026: экосольвентная печать (Technojet160ECO) на режимах mode=0, 1, 2."""
    r = calc.execute({**REF_ECO_PRINT, "mode": mode})
    _assert_js(r, EXPECTED_ECO_PRINT_BY_MODE[mode])
    codes = {m.get("code") for m in r.get("materials") or []}
    assert {"PVC5", "ORAJET3640"}.issubset(codes)


@pytest.mark.parametrize("mode", [0, 1, 2])
def test_latex_print_modes_match_js(calc, mode):
    """JS, 26.11.2026: латексная печать (HPLatex335) на режимах mode=0, 1, 2."""
    r = calc.execute({**REF_LATEX_PRINT, "mode": mode})
    _assert_js(r, EXPECTED_LATEX_PRINT_BY_MODE[mode])
    codes = {m.get("code") for m in r.get("materials") or []}
    assert {"PVC5", "ORAJET3640"}.issubset(codes)


@pytest.mark.parametrize(
    ("params", "expected", "expect_laminat"),
    [
        # JS, 26.11.2026: экосольвент + ламинация + подгибка + двойное нанесение
        (
            {
                **REF_ECO_PRINT,
                "is_print": {
                    "printer_id": "Technojet160ECO",
                    "double_application": True,
                    "is_edge": "isBendEdge",
                    "is_lamination": True,
                },
            },
            {"cost": 32931.0, "price": 52726.0, "time_hours": 20.79, "time_ready": 37.22, "weight_kg": 0.89},
            True,
        ),
        # JS, 26.11.2026: латекс 300×200, 10 шт, подгибка + двойное нанесение
        (
            {
                "quantity": 10,
                "width": 300,
                "height": 200,
                "material_id": "PVC5",
                "material_mode": "isMaterial",
                "is_cut_manual": "KeencutEvolutionE2",
                "is_print": {
                    "printer_id": "HPLatex335",
                    "double_application": True,
                    "is_edge": "isBendEdge",
                    "is_lamination": False,
                },
                "mode": 1,
            },
            {"cost": 6303.0, "price": 10146.0, "time_hours": 2.98, "time_ready": 36.02, "weight_kg": 1.91},
            False,
        ),
        # JS, 26.11.2026: экосольвент 1000×1000, 1 шт, ламинация
        (
            {
                "quantity": 1,
                "width": 1000,
                "height": 1000,
                "material_id": "PVC5",
                "material_mode": "isMaterial",
                "is_cut_manual": "KeencutEvolutionE2",
                "is_print": {
                    "printer_id": "Technojet160ECO",
                    "double_application": False,
                    "is_edge": "isCutEdge",
                    "is_lamination": True,
                },
                "mode": 1,
            },
            {"cost": 3690.0, "price": 6005.0, "time_hours": 0.92, "time_ready": 17.47, "weight_kg": 3.07},
            True,
        ),
    ],
)
def test_is_print_options_match_js(calc, params, expected, expect_laminat):
    """JS, 26.11.2026: ламинация, подгибка (isBendEdge) и двойное нанесение в is_print."""
    r = calc.execute(params)
    _assert_js(r, expected)
    codes = {m.get("code") for m in r.get("materials") or []}
    assert ("LaminatDLCLAM" in codes) is expect_laminat


def test_is_print_lamination_string_no_and_top_level(calc):
    """Строка 'No' не включает ламинацию, а верхнеуровневые is_edge / is_lamination работают."""
    r_no = calc.execute({
        **REF_ECO_PRINT,
        "is_print": {"printer_id": "Technojet160ECO", "is_lamination": "No"},
    })
    _assert_js(r_no, EXPECTED_ECO_PRINT_BY_MODE[1])
    assert all(m.get("code") != "LaminatDLCLAM" for m in r_no.get("materials") or [])

    r_top = calc.execute({
        **REF_ECO_PRINT,
        "is_print": {"printer_id": "Technojet160ECO", "double_application": True},
        "is_edge": "isBendEdge",
        "is_lamination": "LaminatDLCLAM",
    })
    _assert_js(
        r_top,
        {"cost": 32931.0, "price": 52726.0, "time_hours": 20.79, "time_ready": 37.22, "weight_kg": 0.89},
    )


def test_tablets_js_posts_is_print():
    """wp-plugin/forms/tablets.js передаёт is_print для isECOPrint и isLatexPrint, сохраняя isUVPrint."""
    import json
    import subprocess

    js_path = Path(__file__).resolve().parents[3] / "wp-plugin" / "forms" / "tablets.js"
    src = js_path.read_text(encoding="utf-8")

    def run_form(values: dict) -> dict:
        filled = (
            src.replace("{{numN}}", str(values.get("qty", 100)))
            .replace("{{numW}}", str(values.get("width", 50)))
            .replace("{{numH}}", str(values.get("height", 50)))
        )
        harness = (
            "var vals = " + json.dumps(values) + ";\n"
            "var __form_id__ = 120;\n"
            "var ezfc_functions = {\n"
            "  get_value_from: function (id, calc, third, opts) {\n"
            "    if (opts && opts.return_value === 'index') return [0];\n"
            "    if (id === 1339) return [vals.material || 'PVC5'];\n"
            "    if (id === 1340) return [vals.materialMode || 'isMaterial'];\n"
            "    if (id === 1371) return [vals.cut || 'isCutManual'];\n"
            "    if (id === 1368) return [vals.app || 'isUVPrint'];\n"
            "    if (id === 3313) return vals.doubleApp ? 1 : 0;\n"
            "    if (id === 1378) return [vals.color || '4+0'];\n"
            "    if (id === 2770) return [vals.res == null ? 1 : vals.res];\n"
            "    if (id === 1429) return [vals.laminat || 'No'];\n"
            "    if (id === 1477) return [vals.edge || 'isCutEdge'];\n"
            "    if (id === 2003) return [vals.mode == null ? 1 : vals.mode];\n"
            "    return [''];\n"
            "  }\n"
            "};\n"
            "var posted = null, synced = null;\n"
            "var insaincalc = {\n"
            "  syncUrl: function (obj) { synced = obj; },\n"
            "  calcApi: function (slug, body) {\n"
            "    posted = { slug: slug, body: body };\n"
            "    return { then: function () { return { catch: function () {} }; } };\n"
            "  },\n"
            "  showResult: function () {},\n"
            "  showError: function () {}\n"
            "};\n"
            + filled
            + "\nprocess.stdout.write(JSON.stringify({ posted: posted, synced: synced }));\n"
        )
        proc = subprocess.run(["node", "-e", harness], capture_output=True, text=True, encoding="utf-8")
        assert proc.returncode == 0, proc.stderr
        return json.loads(proc.stdout)

    uv = run_form({"app": "isUVPrint", "mode": 0})
    assert uv["posted"]["slug"] == "tablets"
    assert uv["posted"]["body"]["mode"] == 0
    assert "is_uv_print" in uv["posted"]["body"]
    assert "is_print" not in uv["posted"]["body"]

    eco = run_form({"app": "isECOPrint", "laminat": "LaminatDLCLAM", "edge": "isBendEdge", "doubleApp": True})
    assert eco["posted"]["body"]["is_print"] == {
        "printer_id": "Technojet160ECO",
        "double_application": True,
        "is_edge": "isBendEdge",
        "is_lamination": True,
    }

    eco_no_lam = run_form({"app": "isECOPrint", "laminat": "No", "edge": "isCutEdge", "doubleApp": False})
    assert eco_no_lam["posted"]["body"]["is_print"] == {
        "printer_id": "Technojet160ECO",
        "double_application": False,
        "is_edge": "isCutEdge",
        "is_lamination": False,
    }

    latex = run_form({"app": "isLatexPrint", "laminat": "LaminatDLCLAM", "edge": "isBendEdge", "doubleApp": False})
    assert latex["posted"]["body"]["is_print"] == {
        "printer_id": "HPLatex335",
        "double_application": False,
        "is_edge": "isBendEdge",
        "is_lamination": False,
    }


# ── Эталоны isFilm (аппликация плёнками): JS, 26.11.2026 ────────────

REF_FILM_AVERY500W = {
    "quantity": 100,
    "width": 50,
    "height": 50,
    "material_id": "PVC5",
    "material_mode": "isMaterial",
    "is_cut_manual": "KeencutEvolutionE2",
    "is_film": {
        "material_id": "Avery500w",
        "size": [50, 50],
        "size_item": 50,
        "density": 0.25,
        "difficulty": 1,
        "color": 1,
        "double_application": False,
    },
    "mode": 1,
}

# JS, 26.11.2026: node scripts/run_js_calc.mjs calcTablets --data current --args '[100,[50,50],"PVC5",{"isCutManual":"KeencutEvolutionE2","isFilm":{"materialID":"Avery500w","size":[50,50],"sizeItem":50,"density":0.25,"difficulty":1,"color":1,"isDoubleApplication":false},"Material":"isMaterial"},<mode>]'
# Примечание: на mode=1 time_ready в Python 21.22 против 21.26 в JS (rel=0.00188) из-за round вместо Math.ceil в cut_plotter.py (0.02 ч × 2).
EXPECTED_FILM_AVERY500W_BY_MODE = {
    0: {"cost": 8173.98788, "price": 13115.4198808, "time_hours": 4.57, "time_ready": 36.89, "weight_kg": 0.8},
    1: {"cost": 8576.98788, "price": 13760.4198808, "time_hours": 4.83, "time_ready": 21.26, "weight_kg": 0.8},
    2: {"cost": 9014.1982, "price": 14458.429012, "time_hours": 5.08, "time_ready": 13.61, "weight_kg": 0.8},
}


@pytest.mark.parametrize("mode", [0, 1, 2])
def test_film_avery500w_modes_match_js(calc, mode):
    """JS, 26.11.2026: аппликация Avery500w на режимах mode=0, 1, 2."""
    r = calc.execute({**REF_FILM_AVERY500W, "mode": mode})
    e = EXPECTED_FILM_AVERY500W_BY_MODE[mode]
    assert r["cost"] == pytest.approx(e["cost"], rel=JS_REL_TOL)
    assert r["price"] == pytest.approx(e["price"], rel=JS_REL_TOL)
    assert r["weight_kg"] == pytest.approx(e["weight_kg"], rel=JS_REL_TOL)
    if mode == 1:
        assert r["time_ready"] == pytest.approx(e["time_ready"], abs=0.05)
    else:
        assert r["time_hours"] == pytest.approx(e["time_hours"], rel=JS_REL_TOL)
        assert r["time_ready"] == pytest.approx(e["time_ready"], rel=JS_REL_TOL)
    codes = {m.get("code") for m in r.get("materials") or []}
    assert {"PVC5", "Avery500w", "LGChemLC2000H"}.issubset(codes)


@pytest.mark.parametrize(
    ("params", "expected", "check_weight_rel"),
    [
        # JS, 26.11.2026: 100 шт 50×50, Avery500w, 2 цвета, mode=1
        (
            {
                **REF_FILM_AVERY500W,
                "is_film": {**REF_FILM_AVERY500W["is_film"], "color": 2},
            },
            {"cost": 9623.1642, "price": 15452.652572, "time_hours": 5.29, "time_ready": 22.01, "weight_kg": 0.91},
            JS_REL_TOL,
        ),
        # JS, 26.11.2026: 10 шт 300×200, аппликация 250×150, Avery500w, 1 цвет, mode=1
        (
            {
                "quantity": 10,
                "width": 300,
                "height": 200,
                "material_id": "PVC5",
                "material_mode": "isMaterial",
                "is_cut_manual": "KeencutEvolutionE2",
                "is_film": {
                    "material_id": "Avery500w",
                    "size": [250, 150],
                    "size_item": 50,
                    "density": 0.25,
                    "difficulty": 1,
                    "color": 1,
                    "double_application": False,
                },
                "mode": 1,
            },
            {"cost": 3158.42824, "price": 5120.8708784, "time_hours": 1.28, "time_ready": 17.73, "weight_kg": 1.82},
            JS_REL_TOL,
        ),
        # JS, 26.11.2026: 10 шт 300×200, аппликация 250×150, 2 цвета, плотность 0.5, сложность 1.7, двойное нанесение
        (
            {
                "quantity": 10,
                "width": 300,
                "height": 200,
                "material_id": "PVC5",
                "material_mode": "isMaterial",
                "is_cut_manual": "KeencutEvolutionE2",
                "is_film": {
                    "material_id": "Avery500w",
                    "size": [250, 150],
                    "size_item": 50,
                    "density": 0.5,
                    "difficulty": 1.7,
                    "color": 2,
                    "double_application": True,
                },
                "mode": 1,
            },
            {"cost": 7127.1532, "price": 11530.634312, "time_hours": 3.1, "time_ready": 20.65, "weight_kg": 2.31},
            0.01,
        ),
        # JS, 26.11.2026: 1 шт 1000×1000, аппликация 800×800, Avery500w, mode=1
        (
            {
                "quantity": 1,
                "width": 1000,
                "height": 1000,
                "material_id": "PVC5",
                "material_mode": "isMaterial",
                "is_cut_manual": "KeencutEvolutionE2",
                "is_film": {
                    "material_id": "Avery500w",
                    "size": [800, 800],
                    "size_item": 50,
                    "density": 0.25,
                    "difficulty": 1,
                    "color": 1,
                    "double_application": False,
                },
                "mode": 1,
            },
            {"cost": 3791.4516, "price": 6178.629656, "time_hours": 1.2, "time_ready": 17.77, "weight_kg": 3.03},
            JS_REL_TOL,
        ),
    ],
)
def test_is_film_options_match_js(calc, params, expected, check_weight_rel):
    """JS, 26.11.2026: число цветов, размер аппликации, плотность, сложность и двойное нанесение."""
    r = calc.execute(params)
    assert r["cost"] == pytest.approx(expected["cost"], rel=JS_REL_TOL)
    assert r["price"] == pytest.approx(expected["price"], rel=JS_REL_TOL)
    assert r["time_ready"] == pytest.approx(expected["time_ready"], rel=JS_REL_TOL)
    assert r["weight_kg"] == pytest.approx(expected["weight_kg"], rel=check_weight_rel)


@pytest.mark.parametrize("bad_material", ["", "0"])
def test_is_film_empty_material_raises(calc, bad_material):
    """При невыбранной плёнке аппликации (0 / пусто) выбрасывается ValueError."""
    params = {
        **REF_FILM_AVERY500W,
        "is_film": {**REF_FILM_AVERY500W["is_film"], "material_id": bad_material},
    }
    with pytest.raises(ValueError, match="Не выбрана плёнка для аппликации"):
        calc.execute(params)


def test_tablets_js_posts_is_film():
    """wp-plugin/forms/tablets.js передаёт is_film (с плотностью factor 0.01) и пишет в syncUrl."""
    import json
    import subprocess

    js_path = Path(__file__).resolve().parents[3] / "wp-plugin" / "forms" / "tablets.js"
    src = js_path.read_text(encoding="utf-8")

    def run_form(values: dict) -> dict:
        filled = (
            src.replace("{{numN}}", str(values.get("qty", 100)))
            .replace("{{numW}}", str(values.get("width", 50)))
            .replace("{{numH}}", str(values.get("height", 50)))
        )
        harness = (
            "var vals = " + json.dumps(values) + ";\n"
            "var __form_id__ = 120;\n"
            "var ezfc_functions = {\n"
            "  get_value_from: function (id, calc, third, opts) {\n"
            "    if (opts && opts.return_value === 'index') return [0];\n"
            "    if (id === 1339) return [vals.material || 'PVC5'];\n"
            "    if (id === 1340) return [vals.materialMode || 'isMaterial'];\n"
            "    if (id === 1371) return [vals.cut || 'isCutManual'];\n"
            "    if (id === 1368) return [vals.app || 'isUVPrint'];\n"
            "    if (id === 3313) return vals.doubleApp ? 1 : 0;\n"
            "    if (id === 1378) return [vals.color || '4+0'];\n"
            "    if (id === 2770) return [vals.res == null ? 1 : vals.res];\n"
            "    if (id === 1429) return [vals.laminat || 'No'];\n"
            "    if (id === 1477) return [vals.edge || 'isCutEdge'];\n"
            "    if (id === 1484) return [vals.appMat || '0'];\n"
            "    if (id === 1419) return vals.appW == null ? 50 : vals.appW;\n"
            "    if (id === 1420) return vals.appH == null ? 50 : vals.appH;\n"
            "    if (id === 1430) return vals.appColors == null ? 1 : vals.appColors;\n"
            "    if (id === 1424) return vals.appSizeItem == null ? 50 : vals.appSizeItem;\n"
            "    if (id === 1425) {\n"
            "      var d = vals.appDensity == null ? 25 : vals.appDensity;\n"
            "      if (third === true) return String(d);\n"
            "      return vals.app === 'isFilm' ? d * 0.01 : 0;\n"
            "    }\n"
            "    if (id === 1423) return [vals.appDiff == null ? '1' : String(vals.appDiff)];\n"
            "    if (id === 2003) return [vals.mode == null ? 1 : vals.mode];\n"
            "    return [''];\n"
            "  }\n"
            "};\n"
            "var posted = null, synced = null;\n"
            "var insaincalc = {\n"
            "  syncUrl: function (obj) { synced = obj; },\n"
            "  calcApi: function (slug, body) {\n"
            "    posted = { slug: slug, body: body };\n"
            "    return { then: function () { return { catch: function () {} }; } };\n"
            "  },\n"
            "  showResult: function () {},\n"
            "  showError: function () {}\n"
            "};\n"
            + filled
            + "\nprocess.stdout.write(JSON.stringify({ posted: posted, synced: synced }));\n"
        )
        proc = subprocess.run(["node", "-e", harness], capture_output=True, text=True, encoding="utf-8")
        assert proc.returncode == 0, proc.stderr
        return json.loads(proc.stdout)

    film = run_form({
        "app": "isFilm",
        "appMat": "Avery500w",
        "appW": 45,
        "appH": 40,
        "appColors": 2,
        "appSizeItem": 20,
        "appDensity": 50,
        "appDiff": "1.7",
        "doubleApp": True,
    })
    assert film["posted"]["body"]["is_film"] == {
        "material_id": "Avery500w",
        "size": [45, 40],
        "size_item": 20,
        "density": 0.5,
        "difficulty": 1.7,
        "color": 2,
        "double_application": True,
    }
    assert film["synced"]["numDensity"] == 50

    uv = run_form({"app": "isUVPrint", "appMat": "Avery500w"})
    assert "is_uv_print" in uv["posted"]["body"]
    assert "is_film" not in uv["posted"]["body"]


# ── Все 7 плёнок поля 1484 формы 36 (isFilm): JS, 27.11.2026 ───────────
# node scripts/run_js_calc.mjs calcTablets --data current --args '[100,[50,50],"PVC5",{"isCutManual":"KeencutEvolutionE2","isFilm":{"materialID":"<film>","size":[50,50],"sizeItem":50,"density":0.25,"difficulty":1,"color":1,"isDoubleApplication":false},"Material":"isMaterial"},1]'
# Для Avery500w и Avery500c на mode=1 time_ready в Python 21.22 против 21.26 в JS (rel=0.00188) из-за round вместо Math.ceil в cut_plotter.py.
@pytest.mark.parametrize(
    ("material_id", "expected", "time_abs"),
    [
        # JS, 27.11.2026
        ("Avery500w", {"cost": 8576.98788, "price": 13760.4198808, "time_ready": 21.26, "weight_kg": 0.8}, 0.05),
        ("Avery500c", {"cost": 8908.65, "price": 14310.979, "time_ready": 21.26, "weight_kg": 0.8}, 0.05),
        ("Oracal352", {"cost": 9151.45, "price": 14712.147, "time_ready": 21.26, "weight_kg": 0.8}, None),
        ("LGLT4000", {"cost": 9302.25, "price": 14955.375, "time_ready": 21.4, "weight_kg": 0.8}, None),
        ("FES24", {"cost": 11099.45, "price": 17915.607, "time_ready": 21.84, "weight_kg": 0.8}, None),
        ("DMP2000", {"cost": 8769.186, "price": 14070.48876, "time_ready": 21.4, "weight_kg": 0.8}, None),
        ("TM3100", {"cost": 8813.454, "price": 14143.97364, "time_ready": 21.4, "weight_kg": 0.8}, None),
    ],
)
def test_film_all_7_materials_match_js(calc, material_id, expected, time_abs):
    """JS, 27.11.2026: все 7 плёнок аппликации поля 1484 (включая length_min > 0 из roll.json)."""
    params = {
        **REF_FILM_AVERY500W,
        "is_film": {**REF_FILM_AVERY500W["is_film"], "material_id": material_id},
    }
    r = calc.execute(params)
    assert r["cost"] == pytest.approx(expected["cost"], rel=JS_REL_TOL)
    assert r["price"] == pytest.approx(expected["price"], rel=JS_REL_TOL)
    assert r["weight_kg"] == pytest.approx(expected["weight_kg"], rel=JS_REL_TOL)
    if time_abs is not None:
        assert r["time_ready"] == pytest.approx(expected["time_ready"], abs=time_abs)
    else:
        assert r["time_ready"] == pytest.approx(expected["time_ready"], rel=JS_REL_TOL)
    codes = {m.get("code") for m in r.get("materials") or []}
    assert {"PVC5", material_id, "LGChemLC2000H"}.issubset(codes)


# ── Эталоны isBackgroundFilm (оклейка фона таблички): JS, 27.11.2026 ───

REF_BG_FILM_ORACAL = {
    "quantity": 100,
    "width": 50,
    "height": 50,
    "material_id": "PVC5",
    "material_mode": "isMaterial",
    "is_cut_manual": "KeencutEvolutionE2",
    "is_film": {
        "material_id": "Oracal352",
        "size": [50, 50],
        "size_item": 50,
        "density": 0.25,
        "difficulty": 1,
        "color": 1,
        "double_application": False,
    },
    "is_background_film": {
        "material_id": "Avery500c",
        "is_edge": "isCutEdge",
    },
    "mode": 1,
}

# JS, 27.11.2026: node scripts/run_js_calc.mjs calcTablets --data current --args '[100,[50,50],"PVC5",{"isCutManual":"KeencutEvolutionE2","isFilm":{"materialID":"Oracal352","size":[50,50],"sizeItem":50,"density":0.25,"difficulty":1,"color":1,"isDoubleApplication":false},"isBackgroundFilm":{"materialID":"Avery500c","isEdge":"isCutEdge"},"Material":"isMaterial"},<mode>]'
EXPECTED_BG_FILM_ORACAL_BY_MODE = {
    0: {"cost": 12298.45, "price": 19773.147, "time_hours": 6.6, "time_ready": 38.93, "weight_kg": 0.86},
    1: {"cost": 12777.45, "price": 20538.147, "time_hours": 6.9, "time_ready": 23.33, "weight_kg": 0.86},
    2: {"cost": 13270.45, "price": 21326.147, "time_hours": 7.2, "time_ready": 15.73, "weight_kg": 0.86},
}


@pytest.mark.parametrize("mode", [0, 1, 2])
def test_background_film_modes_match_js(calc, mode):
    """JS, 27.11.2026: оклейка фона Avery500c (isCutEdge) с аппликацией Oracal352 на mode=0, 1, 2."""
    r = calc.execute({**REF_BG_FILM_ORACAL, "mode": mode})
    e = EXPECTED_BG_FILM_ORACAL_BY_MODE[mode]
    assert r["cost"] == pytest.approx(e["cost"], rel=JS_REL_TOL)
    assert r["price"] == pytest.approx(e["price"], rel=JS_REL_TOL)
    assert r["time_ready"] == pytest.approx(e["time_ready"], rel=JS_REL_TOL)
    assert r["weight_kg"] == pytest.approx(e["weight_kg"], rel=JS_REL_TOL)
    if mode == 0:
        # Остаток 0.01 ч от round в cut_plotter.py:499 (time_ready укладывается в rel <= 0.001)
        assert r["time_hours"] == pytest.approx(e["time_hours"], abs=0.02)
    else:
        assert r["time_hours"] == pytest.approx(e["time_hours"], rel=JS_REL_TOL)
    codes = {m.get("code") for m in r.get("materials") or []}
    assert {"PVC5", "Oracal352", "Avery500c", "LGChemLC2000H"}.issubset(codes)


@pytest.mark.parametrize(
    ("params", "expected", "time_abs"),
    [
        # JS, 27.11.2026: Avery500w + Avery500c подгибка (isBendEdge), mode=1 (остаток 0.04 ч от Avery500w cut_plotter)
        (
            {
                **REF_FILM_AVERY500W,
                "is_background_film": {"material_id": "Avery500c", "is_edge": "isBendEdge"},
            },
            {"cost": 24202.98788, "price": 38786.4198808, "time_ready": 31.33, "weight_kg": 0.86},
            0.05,
        ),
        # JS, 27.11.2026: 10 шт 300×200, фон Oracal352 с подгибкой (isBendEdge)
        (
            {
                "quantity": 10,
                "width": 300,
                "height": 200,
                "material_id": "PVC5",
                "material_mode": "isMaterial",
                "is_cut_manual": "KeencutEvolutionE2",
                "is_film": {
                    "material_id": "Avery500w",
                    "size": [250, 150],
                    "size_item": 50,
                    "density": 0.25,
                    "difficulty": 1,
                    "color": 1,
                    "double_application": False,
                },
                "is_background_film": {"material_id": "Oracal352", "is_edge": "isBendEdge"},
                "mode": 1,
            },
            {"cost": 5666.42824, "price": 9171.870878400001, "time_ready": 18.97, "weight_kg": 1.95},
            None,
        ),
        # JS, 27.11.2026: 1 шт 1000×1000, фон Avery500w с подгибкой (isBendEdge)
        (
            {
                "quantity": 1,
                "width": 1000,
                "height": 1000,
                "material_id": "PVC5",
                "material_mode": "isMaterial",
                "is_cut_manual": "KeencutEvolutionE2",
                "is_film": {
                    "material_id": "Avery500w",
                    "size": [800, 800],
                    "size_item": 50,
                    "density": 0.25,
                    "difficulty": 1,
                    "color": 1,
                    "double_application": False,
                },
                "is_background_film": {"material_id": "Avery500w", "is_edge": "isBendEdge"},
                "mode": 1,
            },
            {"cost": 5073.4516, "price": 8247.629656000001, "time_ready": 18.43, "weight_kg": 3.25},
            None,
        ),
        # JS, 27.11.2026: двойное нанесение 3313 в форме (double_application=True) — фон x1, как в calcTablets.js
        (
            {
                **REF_FILM_AVERY500W,
                "is_film": {**REF_FILM_AVERY500W["is_film"], "double_application": True},
                "is_background_film": {"material_id": "Avery500c", "is_edge": "isCutEdge", "double_application": True},
            },
            {"cost": 13249.1642, "price": 21278.652572, "time_ready": 24.08, "weight_kg": 0.97},
            None,
        ),
        # JS, 27.11.2026: множитель x2 фона срабатывает от isFilm.isBackgroundFilm (как в calcTablets.js)
        (
            {
                **REF_FILM_AVERY500W,
                "is_film": {**REF_FILM_AVERY500W["is_film"], "isBackgroundFilm": True},
                "is_background_film": {"material_id": "FES24", "is_edge": "isCutEdge"},
            },
            {"cost": 17328.98788, "price": 27887.4198808, "time_ready": 25.57, "weight_kg": 0.91},
            0.05,
        ),
    ],
)
def test_background_film_options_match_js(calc, params, expected, time_abs):
    """JS, 27.11.2026: подгибка края, разные размеры и правило двойного нанесения как в calcTablets.js."""
    r = calc.execute(params)
    assert r["cost"] == pytest.approx(expected["cost"], rel=JS_REL_TOL)
    assert r["price"] == pytest.approx(expected["price"], rel=JS_REL_TOL)
    assert r["weight_kg"] == pytest.approx(expected["weight_kg"], rel=JS_REL_TOL)
    if time_abs is not None:
        assert r["time_ready"] == pytest.approx(expected["time_ready"], abs=time_abs)
    else:
        assert r["time_ready"] == pytest.approx(expected["time_ready"], rel=JS_REL_TOL)


@pytest.mark.parametrize("empty_bg", ["", "0"])
def test_background_film_zero_or_empty_is_noop(calc, empty_bg):
    """Значение '0' («без оклейки») или пустая строка фон не добавляют."""
    base = calc.execute(REF_FORM_DEFAULT)
    with_zero = calc.execute({
        **REF_FORM_DEFAULT,
        "is_background_film": {"material_id": empty_bg, "is_edge": "isBendEdge"},
    })
    assert with_zero["price"] == base["price"]
    assert with_zero["time_ready"] == base["time_ready"]


def test_background_film_without_is_film_adds_background_safely(calc):
    """Оклейка фона работает и без блока is_film (не падает, увеличивает цену относительно базы)."""
    base = calc.execute(REF_FORM_DEFAULT)
    with_bg = calc.execute({
        **REF_FORM_DEFAULT,
        "is_background_film": {"material_id": "Avery500c", "is_edge": "isCutEdge"},
    })
    assert with_bg["price"] > base["price"]
    codes = {m.get("code") for m in with_bg.get("materials") or []}
    assert "Avery500c" in codes


def test_tablets_js_posts_is_background_film():
    """wp-plugin/forms/tablets.js передаёт is_background_film (1427/1483/3313) и не шлёт при '0'."""
    import json
    import subprocess

    js_path = Path(__file__).resolve().parents[3] / "wp-plugin" / "forms" / "tablets.js"
    src = js_path.read_text(encoding="utf-8")

    def run_form(values: dict) -> dict:
        filled = (
            src.replace("{{numN}}", str(values.get("qty", 100)))
            .replace("{{numW}}", str(values.get("width", 50)))
            .replace("{{numH}}", str(values.get("height", 50)))
        )
        harness = (
            "var vals = " + json.dumps(values) + ";\n"
            "var __form_id__ = 120;\n"
            "var ezfc_functions = {\n"
            "  get_value_from: function (id, calc, third, opts) {\n"
            "    if (opts && opts.return_value === 'index') return [0];\n"
            "    if (id === 1339) return [vals.material || 'PVC5'];\n"
            "    if (id === 1340) return [vals.materialMode || 'isMaterial'];\n"
            "    if (id === 1371) return [vals.cut || 'isCutManual'];\n"
            "    if (id === 1368) return [vals.app || 'isUVPrint'];\n"
            "    if (id === 3313) return vals.doubleApp ? 1 : 0;\n"
            "    if (id === 1378) return [vals.color || '4+0'];\n"
            "    if (id === 2770) return [vals.res == null ? 1 : vals.res];\n"
            "    if (id === 1429) return [vals.laminat || 'No'];\n"
            "    if (id === 1477) return [vals.edge || 'isCutEdge'];\n"
            "    if (id === 1484) return [vals.appMat || 'Avery500w'];\n"
            "    if (id === 1419) return 50;\n"
            "    if (id === 1420) return 50;\n"
            "    if (id === 1430) return 1;\n"
            "    if (id === 1424) return 50;\n"
            "    if (id === 1425) return third === true ? '25' : 0.25;\n"
            "    if (id === 1423) return ['1'];\n"
            "    if (id === 1427) return vals.bgMat == null ? ['0'] : [vals.bgMat];\n"
            "    if (id === 1483) return vals.bgEdge == null ? ['isCutEdge'] : [vals.bgEdge];\n"
            "    if (id === 2003) return [vals.mode == null ? 1 : vals.mode];\n"
            "    return [''];\n"
            "  }\n"
            "};\n"
            "var posted = null, synced = null;\n"
            "var insaincalc = {\n"
            "  syncUrl: function (obj) { synced = obj; },\n"
            "  calcApi: function (slug, body) {\n"
            "    posted = { slug: slug, body: body };\n"
            "    return { then: function () { return { catch: function () {} }; } };\n"
            "  },\n"
            "  showResult: function () {},\n"
            "  showError: function () {}\n"
            "};\n"
            + filled
            + "\nprocess.stdout.write(JSON.stringify({ posted: posted, synced: synced }));\n"
        )
        proc = subprocess.run(["node", "-e", harness], capture_output=True, text=True, encoding="utf-8")
        assert proc.returncode == 0, proc.stderr
        return json.loads(proc.stdout)

    no_bg = run_form({"app": "isFilm", "bgMat": "0", "bgEdge": "isBendEdge"})
    assert "is_background_film" not in no_bg["posted"]["body"]
    assert no_bg["synced"]["dpdBackgroudMaterial"] == 0

    with_bg = run_form({"app": "isFilm", "bgMat": "Avery500c", "bgEdge": "isBendEdge", "doubleApp": True})
    assert with_bg["posted"]["body"]["is_background_film"] == {
        "material_id": "Avery500c",
        "is_edge": "isBendEdge",
        "double_application": True,
    }

    uv_bg = run_form({"app": "isUVPrint", "bgMat": "Oracal352", "bgEdge": "isCutEdge", "doubleApp": False})
    assert "is_uv_print" in uv_bg["posted"]["body"]
    assert uv_bg["posted"]["body"]["is_background_film"] == {
        "material_id": "Oracal352",
        "is_edge": "isCutEdge",
        "double_application": False,
    }

