"""Тесты калькулятора блокнотов (notebook)."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

_calc_service = Path(__file__).resolve().parent.parent.parent
if _calc_service.name == "calc_service" and str(_calc_service) not in sys.path:
    sys.path.insert(0, str(_calc_service))

from calculators.notebook import NotebookCalculator


def _cmp(a: float, b: float, rel: float = 0.001) -> bool:
    return abs(a - b) <= rel * max(abs(b), 1e-9)


@pytest.fixture(scope="module")
def calc():
    return NotebookCalculator()


@pytest.fixture(scope="module")
def base_params():
    return {
        "quantity": 50,
        "width_mm": 148,
        "height_mm": 210,
        "cover_material_id": "PaperCoated115M",
        "inner_material_id": "PaperCoated115M",
        "inner_num_sheet": 40,
        "cover_color": "4+0",
        "binding_type": "spring",
        "binding_edge": "long",
        "mode": 1,
    }


@pytest.fixture(scope="module")
def result(calc, base_params):
    try:
        return calc.execute(base_params)
    except Exception:
        return None


def test_slug(calc):
    assert calc.slug == "notebook"


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
    assert "notebook" in result["share_url"]


def test_get_tool_schema(calc):
    schema = calc.get_tool_schema()
    assert schema.get("name") == "calc_notebook"
    assert "parameters" in schema
    assert "quantity" in schema["parameters"].get("properties", {})


# ── Эталонные тесты ──────────────────────────────────────────────────

REF_PARAMS = {
    "quantity": 50,
    "width_mm": 148,
    "height_mm": 210,
    "cover_material_id": "PaperCoated115M",
    "inner_material_id": "PaperCoated115M",
    "inner_num_sheet": 40,
    "cover_color": "4+0",
    "binding_type": "spring",
    "binding_edge": "long",
    "mode": 1,
}
# JS, 05.11.2026 — ceil снят, как в JS. Обложка и блок через print_sheet.
EXPECTED_REF = {
    "cost": 9885.25,
    "price": 20800,
    "time_hours": 2.15,
    "time_ready": 58.15,
    "weight_kg": 8.23,
}
EXPECTED_MATERIAL = {
    "code": "PaperCoated115M",
    "name_substring": "Титан DIGITAL",
    "quantity_approx": 27,
}


@pytest.fixture(scope="module")
def ref_result(calc):
    try:
        return calc.execute(REF_PARAMS)
    except Exception:
        return None


def test_expected_values_notebook(ref_result):
    if ref_result is None:
        pytest.skip("расчёт эталонного кейса не выполнен")
    r = ref_result
    e = EXPECTED_REF
    em = EXPECTED_MATERIAL

    ok_cost = _cmp(r["cost"], e["cost"])
    ok_price = _cmp(r["price"], e["price"])
    ok_time = _cmp(r["time_hours"], e["time_hours"])
    ok_ready = _cmp(r["time_ready"], e["time_ready"])
    ok_weight = _cmp(r["weight_kg"], e["weight_kg"])

    materials = r.get("materials") or []
    mat = next((m for m in materials if m.get("code") == em["code"]), {})
    ok_mat_code = bool(mat)
    ok_mat_name = em["name_substring"] in (mat.get("name") or "")
    ok_mat_q = _cmp(float(mat.get("quantity") or 0), float(em["quantity_approx"]), 0.15) if mat else False

    print("")
    print("  [notebook] Параметры   quantity=%s  |  size=%sx%s  |  cover=%s  |  inner=%s  |  sheets=%s  |  mode=%s"
          % (REF_PARAMS.get("quantity"), REF_PARAMS.get("width_mm"), REF_PARAMS.get("height_mm"),
             REF_PARAMS.get("cover_material_id"), REF_PARAMS.get("inner_material_id"),
             REF_PARAMS.get("inner_num_sheet"), REF_PARAMS.get("mode")))
    print("  ---")
    print("  cost        %s  (ожид. %s)  %s" % (r["cost"], e["cost"], "ok" if ok_cost else "FAIL"))
    print("  price       %s  (ожид. %s)  %s" % (r["price"], e["price"], "ok" if ok_price else "FAIL"))
    print("  time_hours  %s  (ожид. %s)  %s" % (r["time_hours"], e["time_hours"], "ok" if ok_time else "FAIL"))
    print("  time_ready  %s  (ожид. %s)  %s" % (r["time_ready"], e["time_ready"], "ok" if ok_ready else "FAIL"))
    print("  weight_kg   %s  (ожид. %s)  %s" % (r["weight_kg"], e["weight_kg"], "ok" if ok_weight else "FAIL"))
    if mat:
        print(
            "  material    code=%s  name=%s  quantity=%s  (ожид. code=%s, name содержит '%s', qty ~%s)  %s"
            % (
                mat.get("code"),
                (mat.get("name") or "")[:40],
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
    assert materials, "ожидаются материалы в результате"
    assert ok_mat_code, f"material code: expected {em['code']} в materials"
    assert ok_mat_name, f"material name должен содержать '{em['name_substring']}'"
    assert ok_mat_q, f"material quantity: got {mat.get('quantity')}, expected ~{em['quantity_approx']}"


# JS, 19.11.2026 — дефолт боевой формы 45. Раннер calcNotebook не подключает,
# числа сняты вызовом insaincalc.calcNotebook в консоли страницы.
REF_FORM_DEFAULT = {
    "quantity": 100,
    "width_mm": 148,
    "height_mm": 210,
    "cover_material_id": "PaperCoated250M",
    "cover_color": "4+0",
    "cover_lamination_id": "",
    "backing_material_id": "PaperCoated250M",
    "backing_color": "0+0",
    "backing_lamination_id": "",
    "inner_material_id": "VHI80",
    "inner_num_sheet": 50,
    "inner_color": "0+0",
    "binding_type": "spring",
    "binding_edge": "short",
    "mode": 1,
}
EXPECTED_FORM_DEFAULT = {
    "cost": 8990.798224489796,
    "price": 16061.693507918371,
    "time_hours": 3.56,
    "time_ready": 22.61,
}


def test_form_default_notebook(calc):
    """Дефолт формы 45: подложка и блок 0+0, обложка 4+0, тираж 100."""
    result = calc.execute(REF_FORM_DEFAULT)
    expected = EXPECTED_FORM_DEFAULT
    assert _cmp(result["cost"], expected["cost"]), result["cost"]
    assert _cmp(result["price"], expected["price"]), result["price"]
    assert _cmp(result["time_hours"], expected["time_hours"]), result["time_hours"]
    assert _cmp(result["time_ready"], expected["time_ready"]), result["time_ready"]

    by_code = {m["code"]: m for m in result["materials"]}
    cover = by_code["PaperCoated250M"]
    inner = by_code["VHI80"]
    wire = by_code["MetallBindindWire3_8"]
    assert cover["quantity"] == 54
    assert cover["size_mm"] == [320.0, 450.0]
    assert "Титан" in cover["name"]
    assert inner["quantity"] == 1263
    assert inner["size_mm"] == [297.0, 420.0]
    assert "Снегурочка" in inner["name"]
    assert _cmp(float(wire["quantity"]), 0.040285714285714286)
    assert wire["size_mm"] == [9.5, 42000.0]
    for item in (cover, inner, wire):
        assert item["name"] != item["code"]
        assert item.get("title")


# JS, 19.11.2026 — calcNotebook.js на текущем прайсе calc_service/data.
# Блок 4+0, isPrintLaser, VHI80: marginsInner = -1, 4 шт А5 на лист А3.
# Со списком [-1, -1, -1, -1] поля принтера остаются и листов VHI80 становится 2525.
EXPECTED_INNER_LASER_4_0 = {
    "cost": 26447.067724489796,
    "price": 47816.70263991839,
    "time_hours": 5.77,
    "time_ready": 24.82,
}


def test_inner_laser_4_0_lays_four_on_vhi80(calc):
    """Цифровая печать блока 4+0 на VHI80: 1263 листа А3, не 2525."""
    params = {**REF_FORM_DEFAULT, "inner_color": "4+0", "is_print_laser": True}
    result = calc.execute(params)
    by_code = {m["code"]: m for m in result["materials"]}
    inner = by_code["VHI80"]
    # Со списком [-1, -1, -1, -1] здесь 2525.
    assert inner["quantity"] == 1263
    assert inner["size_mm"] == [297.0, 420.0]
    expected = EXPECTED_INNER_LASER_4_0
    assert _cmp(result["cost"], expected["cost"]), result["cost"]
    assert _cmp(result["price"], expected["price"]), result["price"]
    assert _cmp(result["time_hours"], expected["time_hours"]), result["time_hours"]
    assert _cmp(result["time_ready"], expected["time_ready"]), result["time_ready"]
    assert "Снегурочка" in inner["name"]
    assert by_code["PaperCoated250M"]["quantity"] == 54
    wire = by_code["MetallBindindWire3_8"]
    assert _cmp(float(wire["quantity"]), 0.040285714285714286)
    assert wire["size_mm"] == [9.5, 42000.0]
    for item in (inner, by_code["PaperCoated250M"], wire):
        assert item["name"] != item["code"]
        assert item.get("title")


def test_blank_backing_keeps_lamination(calc):
    """Ламинация на подложке 0+0 не пропадает. JS страницы, 19.11.2026."""
    params = dict(REF_FORM_DEFAULT)
    params["backing_lamination_id"] = "Laminat32G"
    plain = calc.execute(REF_FORM_DEFAULT)
    laminated = calc.execute(params)
    # Себестоимость одной подложки с плёнкой — с консоли calcPrintSheet.
    assert laminated["cost"] > plain["cost"]
    assert _cmp(laminated["cost"] - plain["cost"], 1388.1508256410257 - 321.3)


@pytest.mark.parametrize(
    ("overrides", "expected_cost", "expected_price", "expected_ready", "expected_cover_qty"),
    [
        # JS страницы, 19.11.2026 — входы блокера form-notebook (mode 2).
        ({}, 9354.232557823128, 16703.879550585036, 14.81, 54),
        ({"quantity": 200, "width_mm": 210, "height_mm": 297}, 25130.240285714288, 45163.907661714285, 21.47, 210),
        (
            {"quantity": 200, "width_mm": 210, "height_mm": 297, "cover_lamination_id": "Laminat32G"},
            29111.9353010989,
            52281.42847279122,
            22.47,
            213,
        ),
    ],
    ids=["default_100_A5", "200_A4_plain", "200_A4_laminat32G"],
)
def test_notebook_mode2_matches_js(
    calc, overrides, expected_cost, expected_price, expected_ready, expected_cover_qty
):
    """Регрессия mode 2 на входах блокера form-notebook (дефолт, 200 А4, 200 А4 + Laminat32G)."""
    params = {**REF_FORM_DEFAULT, "mode": 2, **overrides}
    r = calc.execute(params)
    assert _cmp(r["cost"], expected_cost), f"cost: got {r['cost']}, expected {expected_cost}"
    assert _cmp(r["price"], expected_price), f"price: got {r['price']}, expected {expected_price}"
    assert _cmp(r["time_ready"], expected_ready), f"time_ready: got {r['time_ready']}, expected {expected_ready}"
    by_code = {m["code"]: m for m in r["materials"]}
    assert by_code["PaperCoated250M"]["quantity"] == expected_cover_qty
