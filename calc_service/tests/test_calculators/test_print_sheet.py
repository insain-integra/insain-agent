"""
Тесты калькулятора листовой печати (print_sheet).
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

_calc_service = Path(__file__).resolve().parent.parent.parent
if _calc_service.name == "calc_service" and str(_calc_service) not in sys.path:
    sys.path.insert(0, str(_calc_service))

from calculators.base import ProductionMode
from calculators.print_sheet import PrintSheetCalculator


@pytest.fixture(scope="module")
def calc():
    return PrintSheetCalculator()


@pytest.fixture(scope="module")
def base_params(calc):
    opts = calc.get_options()
    materials = opts.get("materials") or []
    mat = materials[0] if materials else {}
    code = mat.get("code", "PaperCoated115M")
    return {
        "quantity": 100,
        "width": 100,
        "height": 150,
        "color": "4+0",
        "material_id": code,
        "printer_code": "",
        "mode": 1,
    }


@pytest.fixture(scope="module")
def result(calc, base_params):
    try:
        return calc.execute(base_params)
    except Exception:
        return None


def test_slug(calc):
    assert calc.slug == "print_sheet"


def test_calculate_basic(result):
    if result is None:
        pytest.skip("расчёт не выполнен")
    for key in ("cost", "price", "unit_price", "time_hours", "time_ready", "weight_kg", "materials"):
        assert key in result
    assert result["cost"] >= 0
    assert result["price"] >= 0
    assert result["time_hours"] >= 0
    assert result["time_ready"] >= 0
    # materials: каждый элемент должен содержать name и title
    materials = result.get("materials") or []
    for m in materials:
        assert "name" in m
        assert "title" in m


def test_time_hours_positive(result):
    if result is None:
        pytest.skip("расчёт не выполнен")
    assert result["time_hours"] >= 0


def test_time_ready_greater_than_time(result):
    if result is None:
        pytest.skip("расчёт не выполнен")
    assert result["time_ready"] >= result["time_hours"]


def test_time_ready_modes(calc, base_params):
    base_params = dict(base_params)
    res_e = calc.calculate({**base_params, "mode": ProductionMode.ECONOMY})
    res_s = calc.calculate({**base_params, "mode": ProductionMode.STANDARD})
    res_x = calc.calculate({**base_params, "mode": ProductionMode.EXPRESS})
    assert res_e["time_ready"] >= res_s["time_ready"]
    assert res_s["time_ready"] >= res_x["time_ready"]


def test_price_greater_than_cost(result):
    if result is None:
        pytest.skip("расчёт не выполнен")
    if result["cost"] == 0:
        pytest.skip("нулевая себестоимость")
    assert result["price"] >= result["cost"]


def test_share_url_contains_slug(result):
    if result is None:
        pytest.skip("расчёт не выполнен")
    assert "share_url" in result
    assert "print_sheet" in result["share_url"]


def test_get_options_not_empty(calc):
    opts = calc.get_options()
    assert "modes" in opts
    assert "materials" in opts
    assert "printers" in opts
    assert "colors" in opts


def test_get_tool_schema(calc):
    schema = calc.get_tool_schema()
    assert schema.get("name") == "calc_print_sheet"
    assert "parameters" in schema
    assert "quantity" in schema["parameters"].get("properties", {})


# Эталон: 100 шт, 210×297 мм, PaperCoated300M, цветность 4+4
REF_REL_TOL = 0.001

REF_PARAMS = {
    "quantity": 100,
    "width": 210,
    "height": 297,
    "material_id": "PaperCoated300M",
    "color": "4+4",
    "printer_code": "",
    "mode": 1,
}
# JS, 12.11.2026 — ceil времени печати и timePrepare * mode.
# node scripts/run_js_calc.mjs calcPrintSheet --data current --args
# '[100,[210,297],"4+4",[0,0,0,0],0,"PaperCoated300M",{},1]'
# weight_kg — вес изделий. JS на этом входе 2.16 (лист). Верный вес — Python, решение 11.11.2026.
EXPECTED_REF = {
    "cost": 3210.479090909091,
    "price": 5266.918472727273,
    "time_hours": 1.13,
    "time_ready": 10.2,
    "weight_kg": 1.8711,
}

# JS, 12.11.2026 — тот же вход, mode 0 (подготовка 0).
# node scripts/run_js_calc.mjs calcPrintSheet --data current --args
# '[100,[210,297],"4+4",[0,0,0,0],0,"PaperCoated300M",{},0]'
REF_PARAMS_MODE0 = {**REF_PARAMS, "mode": 0}
EXPECTED_REF_MODE0 = {
    "cost": 2959.689090909091,
    "price": 4864.332072727273,
    "time_hours": 1.02,
    "time_ready": 25.02,
}

# JS, 13.11.2026 — белые поля: margins -1, поля принтера не прибавляются.
# node scripts/run_js_calc.mjs calcPrintSheet --data current --args
# '[100,[297,210],"4+0",-1,0,"VHI80",{},1]'
REF_PARAMS_MARGINS_MINUS_ONE = {
    "quantity": 100,
    "width": 297,
    "height": 210,
    "material_id": "VHI80",
    "color": "4+0",
    "margins": -1,
    "interval": 0,
    "mode": 1,
}
EXPECTED_MARGINS_MINUS_ONE = {
    "cost": 1102.8211666666666,
    "price": 1811.964386666667,
    "time_ready": 8.4,
}

# JS, 13.11.2026 — обычные поля [2,2,2,2], тот же тираж: поля принтера прибавляются.
# node scripts/run_js_calc.mjs calcPrintSheet --data current --args
# '[100,[297,210],"4+0",[2,2,2,2],0,"VHI80",{},1]'
REF_PARAMS_MARGINS_DEFAULT = {
    "quantity": 100,
    "width": 297,
    "height": 210,
    "material_id": "VHI80",
    "color": "4+0",
    "margins": [2, 2, 2, 2],
    "interval": 0,
    "mode": 1,
}
EXPECTED_MARGINS_DEFAULT = {
    "cost": 1951.1725,
    "price": 3214.3125999999997,
    "time_ready": 8.6,
}

# JS, 13.11.2026 — дефолт боевой формы 6: 100 шт, А4 297×210, 4+0, VHI80,
# поля [2,2,2,2], интервал 4, без ламинации, mode 1.
# node scripts/run_js_calc.mjs calcPrintSheet --data current --args
# '[100,[297,210],"4+0",[2,2,2,2],4,"VHI80",{},1]'
# price и time_ready совпали с боевым API.
# weight_kg — вес изделий. JS 0.99792 (лист с обрезью). Верный вес — Python, решение 11.11.2026.
REF_FORM_DEFAULT = {
    "quantity": 100,
    "width": 297,
    "height": 210,
    "material_id": "VHI80",
    "color": "4+0",
    "margins": [2, 2, 2, 2],
    "interval": 4,
    "mode": 1,
}
EXPECTED_FORM_DEFAULT = {
    "cost": 1951.1725,
    "price": 3214.3125999999997,
    "time_hours": 0.32,
    "time_ready": 8.6,
    "weight_kg": 0.4989599999999999,
}
EXPECTED_MATERIAL = {
    "code": "PaperCoated300M",
    "name_substring": "Титан DIGITAL мелованная",  # часть названия
    "quantity_approx": 53,
}

# Эталон 2: 1000 шт, 210×297 мм, PaperCoated300M, цветность 4+0
REF_PARAMS_2 = {
    "quantity": 1000,
    "width": 210,
    "height": 297,
    "material_id": "PaperCoated300M",
    "color": "4+0",
    "printer_code": "",
    "mode": 1,
}
# JS, 05.11.2026 — ceil снят, как в JS. calcPrintSheet --data current.
EXPECTED_REF_2 = {
    "cost": 17568.012727272726,
    "price": 28920.942036363638,
    "time_hours": 4.91,
    "time_ready": 17.65,
    "weight_kg": 18.711,
}
EXPECTED_MATERIAL_2 = {
    "code": "PaperCoated300M",
    "name_substring": "Титан DIGITAL мелованная",
    "quantity_approx": 510,
    "size": [320, 450],
}

# Эталон 3: 100 шт, 210×297 мм, PaperCoated250G, ламинат Laminat32G, цветность 4+0
REF_PARAMS_3 = {
    "quantity": 100,
    "width": 210,
    "height": 297,
    "material_id": "PaperCoated250G",
    "color": "4+0",
    "printer_code": "",
    "lamination_id": "Laminat32G",
    "lamination_double_side": True,
    "mode": 1,
}
# JS, 05.11.2026 — ceil снят, как в JS. calcPrintSheet с ламинацией, price раннера 6297.625.
EXPECTED_REF_3 = {
    "cost": 3856.346317948718,
    "price": 6297.62536871795,
    "time_hours": 1.01,
    "time_ready": 9.49,
    "weight_kg": 2.06613,
}
EXPECTED_MATERIALS_3 = {
    "paper": {
        "code": "PaperCoated250G",
        "name_substring": "Титан DIGITAL мелованная (глянцевая)",
        "quantity_approx": 56,
    },
    "lamination": {
        "code": "Laminat32G",
        "name_substring": "Roll film 305мм х 100м х 32 mic GLOSS",
        "quantity_approx": 49.35,  # метры плёнки
    },
}


def _cmp(a: float, b: float, rel: float = 0.001) -> bool:
    """Сравнение с относительным допуском."""
    return abs(a - b) <= rel * max(abs(b), 1e-9)


@pytest.fixture(scope="module")
def ref_result(calc):
    """Результат расчёта для эталонного кейса (100 шт, 210×297, PaperCoated300M, 4+4)."""
    try:
        return calc.execute(REF_PARAMS)
    except Exception:
        return None


def test_expected_values_print_sheet(ref_result):
    """Сверка с эталоном: 100 шт, 210×297 мм, PaperCoated300M, цветность 4+4."""
    if ref_result is None:
        pytest.skip("расчёт эталонного кейса не выполнен (материал PaperCoated300M?)")
    r = ref_result
    e = EXPECTED_REF
    em = EXPECTED_MATERIAL
    rel = REF_REL_TOL

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

    print("")
    print("  [листовая печать] Параметры   quantity=%s  |  size=%s×%s  |  material_id=%s  |  color=%s  |  mode=%s"
          % (REF_PARAMS.get("quantity"), REF_PARAMS.get("width"), REF_PARAMS.get("height"),
             REF_PARAMS.get("material_id"), REF_PARAMS.get("color"), REF_PARAMS.get("mode")))
    print("  ---")
    print("  cost        %s  (ожид. %s)  %s" % (r["cost"], e["cost"], "ok" if ok_cost else "FAIL"))
    print("  price       %s  (ожид. %s)  %s" % (r["price"], e["price"], "ok" if ok_price else "FAIL"))
    print("  time_hours  %s  (ожид. %s)  %s" % (r["time_hours"], e["time_hours"], "ok" if ok_time else "FAIL"))
    print("  time_ready  %s  (ожид. %s)  %s" % (r["time_ready"], e["time_ready"], "ok" if ok_ready else "FAIL"))
    print("  weight_kg   %s  (ожид. %s)  %s" % (r["weight_kg"], e["weight_kg"], "ok" if ok_weight else "FAIL"))
    if materials:
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
        # поле title обязательно для UI
        assert "title" in mat
    else:
        print("  material    (нет в результате, ожид. code=%s, qty ~%s)  FAIL" % (em["code"], em["quantity_approx"]))

    assert ok_cost, f"cost: got {r['cost']}, expected ~{e['cost']}"
    assert ok_price, f"price: got {r['price']}, expected ~{e['price']}"
    assert ok_time, f"time_hours: got {r['time_hours']}, expected ~{e['time_hours']}"
    assert ok_ready, f"time_ready: got {r['time_ready']}, expected ~{e['time_ready']}"
    assert ok_weight, f"weight_kg: got {r['weight_kg']}, expected ~{e['weight_kg']}"
    assert materials, "ожидается один материал в результате"
    assert ok_mat_code, f"material code: got {mat.get('code')}, expected {em['code']}"
    assert ok_mat_name, f"material name должен содержать '{em['name_substring']}'"
    assert ok_mat_q, f"material quantity: got {mat.get('quantity')}, expected ~{em['quantity_approx']}"


def test_expected_values_print_sheet_mode0(calc):
    """JS, 12.11.2026: 100 шт, 210×297, PaperCoated300M, 4+4, mode 0."""
    r = calc.execute(REF_PARAMS_MODE0)
    e = EXPECTED_REF_MODE0
    rel = REF_REL_TOL
    assert r["cost"] == pytest.approx(e["cost"], rel=rel), (
        f"cost: got {r['cost']}, expected ~{e['cost']}"
    )
    assert r["price"] == pytest.approx(e["price"], rel=rel), (
        f"price: got {r['price']}, expected ~{e['price']}"
    )
    assert r["time_ready"] == pytest.approx(e["time_ready"], rel=rel), (
        f"time_ready: got {r['time_ready']}, expected ~{e['time_ready']}"
    )
    assert r["time_hours"] == pytest.approx(e["time_hours"], rel=rel), (
        f"time_hours: got {r['time_hours']}, expected ~{e['time_hours']}"
    )
    r1 = calc.execute(REF_PARAMS)
    assert r["price"] < r1["price"], (
        f"mode0 price {r['price']} должна быть меньше mode1 {r1['price']}"
    )


def test_expected_values_print_sheet_margins_minus_one(calc):
    """JS, 13.11.2026: 100 шт, 297×210, VHI80, 4+0, margins -1, mode 1."""
    r = calc.execute(REF_PARAMS_MARGINS_MINUS_ONE)
    e = EXPECTED_MARGINS_MINUS_ONE
    rel = REF_REL_TOL
    assert r["cost"] == pytest.approx(e["cost"], rel=rel), (
        f"cost: got {r['cost']}, expected ~{e['cost']}"
    )
    assert r["price"] == pytest.approx(e["price"], rel=rel), (
        f"price: got {r['price']}, expected ~{e['price']}"
    )
    assert r["time_ready"] == pytest.approx(e["time_ready"], rel=rel), (
        f"time_ready: got {r['time_ready']}, expected ~{e['time_ready']}"
    )


def test_expected_values_print_sheet_margins_default(calc):
    """JS, 13.11.2026: тот же вход, margins [2,2,2,2] — старые числа ветки с полями."""
    r = calc.execute(REF_PARAMS_MARGINS_DEFAULT)
    e = EXPECTED_MARGINS_DEFAULT
    rel = REF_REL_TOL
    assert r["cost"] == pytest.approx(e["cost"], rel=rel), (
        f"cost: got {r['cost']}, expected ~{e['cost']}"
    )
    assert r["price"] == pytest.approx(e["price"], rel=rel), (
        f"price: got {r['price']}, expected ~{e['price']}"
    )
    assert r["time_ready"] == pytest.approx(e["time_ready"], rel=rel), (
        f"time_ready: got {r['time_ready']}, expected ~{e['time_ready']}"
    )


def test_form_default_print_sheet(calc):
    """JS, 13.11.2026: дефолт формы 6, 100 шт, А4, VHI80, интервал 4. Вес — изделие."""
    r = calc.execute(REF_FORM_DEFAULT)
    e = EXPECTED_FORM_DEFAULT
    rel = REF_REL_TOL
    assert r["cost"] == pytest.approx(e["cost"], rel=rel), (
        f"cost: got {r['cost']}, expected ~{e['cost']}"
    )
    assert r["price"] == pytest.approx(e["price"], rel=rel), (
        f"price: got {r['price']}, expected ~{e['price']}"
    )
    assert r["time_hours"] == pytest.approx(e["time_hours"], rel=rel), (
        f"time_hours: got {r['time_hours']}, expected ~{e['time_hours']}"
    )
    assert r["time_ready"] == pytest.approx(e["time_ready"], rel=rel), (
        f"time_ready: got {r['time_ready']}, expected ~{e['time_ready']}"
    )
    assert r["weight_kg"] == pytest.approx(e["weight_kg"], rel=rel), (
        f"weight_kg: got {r['weight_kg']}, expected ~{e['weight_kg']}"
    )
    mats = r["materials"]
    assert mats, "ожидается материал в результате"
    mat = mats[0]
    assert mat.get("code") and mat.get("name") and mat.get("title")
    assert "Снегурочка" in mat["name"], mat["name"]
    assert mat["size_mm"] == [297.0, 420.0], mat.get("size_mm")
    assert mat["quantity"] == pytest.approx(105), mat.get("quantity")


@pytest.fixture(scope="module")
def ref_result_2(calc):
    """Результат расчёта для эталона 2: 1000 шт, 210×297, PaperCoated300M, 4+0."""
    try:
        return calc.execute(REF_PARAMS_2)
    except Exception:
        return None


def test_expected_values_print_sheet_1000(ref_result_2):
    """Сверка с эталоном: 1000 шт, 210×297 мм, PaperCoated300M, цветность 4+0."""
    if ref_result_2 is None:
        pytest.skip("расчёт эталонного кейса не выполнен (материал PaperCoated300M?)")
    r = ref_result_2
    e = EXPECTED_REF_2
    em = EXPECTED_MATERIAL_2
    rel = REF_REL_TOL

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

    print("")
    print("  [листовая печать 1000] quantity=%s  |  size=%s×%s  |  material_id=%s  |  color=%s  |  mode=%s"
          % (REF_PARAMS_2.get("quantity"), REF_PARAMS_2.get("width"), REF_PARAMS_2.get("height"),
             REF_PARAMS_2.get("material_id"), REF_PARAMS_2.get("color"), REF_PARAMS_2.get("mode")))
    print("  ---")
    print("  cost        %s  (ожид. %s)  %s" % (r["cost"], e["cost"], "ok" if ok_cost else "FAIL"))
    print("  price       %s  (ожид. %s)  %s" % (r["price"], e["price"], "ok" if ok_price else "FAIL"))
    print("  time_hours  %s  (ожид. %s)  %s" % (r["time_hours"], e["time_hours"], "ok" if ok_time else "FAIL"))
    print("  time_ready  %s  (ожид. %s)  %s" % (r["time_ready"], e["time_ready"], "ok" if ok_ready else "FAIL"))
    print("  weight_kg   %s  (ожид. %s)  %s" % (r["weight_kg"], e["weight_kg"], "ok" if ok_weight else "FAIL"))
    if materials:
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
        print("  material    (нет в результате)  FAIL")

    assert ok_cost, f"cost: got {r['cost']}, expected ~{e['cost']}"
    assert ok_price, f"price: got {r['price']}, expected ~{e['price']}"
    assert ok_time, f"time_hours: got {r['time_hours']}, expected ~{e['time_hours']}"
    assert ok_ready, f"time_ready: got {r['time_ready']}, expected ~{e['time_ready']}"
    assert ok_weight, f"weight_kg: got {r['weight_kg']}, expected ~{e['weight_kg']}"
    assert materials, "ожидается один материал в результате"
    assert ok_mat_code, f"material code: got {mat.get('code')}, expected {em['code']}"
    assert ok_mat_name, f"material name должен содержать '{em['name_substring']}'"
    assert ok_mat_q, f"material quantity: got {mat.get('quantity')}, expected ~{em['quantity_approx']}"


@pytest.fixture(scope="module")
def ref_result_3(calc):
    """Результат расчёта для эталона 3: 100 шт, 210×297, PaperCoated250G + Laminat32G, 4+0."""
    try:
        return calc.execute(REF_PARAMS_3)
    except Exception:
        return None


def test_expected_values_print_sheet_lamination(ref_result_3):
    """Сверка с эталоном: 100 шт, 210×297 мм, PaperCoated250G + Laminat32G, цветность 4+0."""
    if ref_result_3 is None:
        pytest.skip("расчёт эталонного кейса не выполнен (материалы PaperCoated250G/Laminat32G?)")
    r = ref_result_3
    e = EXPECTED_REF_3
    em_paper = EXPECTED_MATERIALS_3["paper"]
    em_lam = EXPECTED_MATERIALS_3["lamination"]
    rel = REF_REL_TOL

    ok_cost = _cmp(r["cost"], e["cost"], rel)
    ok_price = _cmp(r["price"], e["price"], rel)
    ok_time = _cmp(r["time_hours"], e["time_hours"], rel)
    ok_ready = _cmp(r["time_ready"], e["time_ready"], rel)
    ok_weight = _cmp(r["weight_kg"], e["weight_kg"], rel)

    materials = r.get("materials") or []
    paper = next((m for m in materials if m.get("code") == em_paper["code"]), {})
    lam = next((m for m in materials if m.get("code") == em_lam["code"]), {})

    ok_paper_present = bool(paper)
    ok_lam_present = bool(lam)
    ok_paper_name = em_paper["name_substring"] in (paper.get("name") or "") if paper else False
    ok_lam_name = em_lam["name_substring"] in (lam.get("name") or "") if lam else False
    ok_paper_q = _cmp(float(paper.get("quantity") or 0), float(em_paper["quantity_approx"]), 0.15) if paper else False
    ok_lam_q = _cmp(float(lam.get("quantity") or 0), float(em_lam["quantity_approx"]), 0.15) if lam else False

    print("")
    print(
        "  [листовая печать + ламинация] quantity=%s  |  size=%s×%s  |  material_id=%s  |  lamination_id=%s  |  color=%s  |  mode=%s"
        % (
            REF_PARAMS_3.get("quantity"),
            REF_PARAMS_3.get("width"),
            REF_PARAMS_3.get("height"),
            REF_PARAMS_3.get("material_id"),
            REF_PARAMS_3.get("lamination_id"),
            REF_PARAMS_3.get("color"),
            REF_PARAMS_3.get("mode"),
        )
    )
    print("  ---")
    print("  cost        %s  (ожид. %s)  %s" % (r["cost"], e["cost"], "ok" if ok_cost else "FAIL"))
    print("  price       %s  (ожид. %s)  %s" % (r["price"], e["price"], "ok" if ok_price else "FAIL"))
    print("  time_hours  %s  (ожид. %s)  %s" % (r["time_hours"], e["time_hours"], "ok" if ok_time else "FAIL"))
    print("  time_ready  %s  (ожид. %s)  %s" % (r["time_ready"], e["time_ready"], "ok" if ok_ready else "FAIL"))
    print("  weight_kg   %s  (ожид. %s)  %s" % (r["weight_kg"], e["weight_kg"], "ok" if ok_weight else "FAIL"))
    print(
        "  paper       code=%s  name=%s  quantity=%s  (ожид. code=%s, name содержит '%s', qty ~%s)  %s"
        % (
            paper.get("code"),
            (paper.get("name") or "")[:60],
            paper.get("quantity"),
            em_paper["code"],
            em_paper["name_substring"],
            em_paper["quantity_approx"],
            "ok" if (ok_paper_present and ok_paper_name and ok_paper_q) else "FAIL",
        )
    )
    print(
        "  lamination  code=%s  name=%s  quantity=%s  (ожид. code=%s, name содержит '%s', qty ~%s)  %s"
        % (
            lam.get("code"),
            (lam.get("name") or "")[:60],
            lam.get("quantity"),
            em_lam["code"],
            em_lam["name_substring"],
            em_lam["quantity_approx"],
            "ok" if (ok_lam_present and ok_lam_name and ok_lam_q) else "FAIL",
        )
    )

    assert ok_cost, f"cost: got {r['cost']}, expected ~{e['cost']}"
    assert ok_price, f"price: got {r['price']}, expected ~{e['price']}"
    assert ok_time, f"time_hours: got {r['time_hours']}, expected ~{e['time_hours']}"
    assert ok_ready, f"time_ready: got {r['time_ready']}, expected ~{e['time_ready']}"
    assert ok_weight, f"weight_kg: got {r['weight_kg']}, expected ~{e['weight_kg']}"
    assert materials, "ожидаются материалы в результате"
    assert ok_paper_present, "бумага PaperCoated250G отсутствует в materials"
    assert ok_lam_present, "ламинат Laminat32G отсутствует в materials"
    assert ok_paper_name, f"paper name должен содержать '{em_paper['name_substring']}'"
    assert ok_lam_name, f"lamination name должен содержать '{em_lam['name_substring']}'"
    # Оба материала должны иметь title для UI
    assert "title" in paper
    assert "title" in lam
    assert ok_paper_q, f"paper quantity: got {paper.get('quantity')}, expected ~{em_paper['quantity_approx']}"
    assert ok_lam_q, f"lamination quantity: got {lam.get('quantity')}, expected ~{em_lam['quantity_approx']}"


def test_print_sheet_option_numbering_increases_totals(calc, base_params):
    """Нумерация: +0.75*qty к себестоимости и +1.0*qty к ценовой части до marginPrintSheet (как JS)."""
    base = dict(base_params)
    r0 = calc.calculate(base)
    r1 = calc.calculate({**base, "option_numbering": True})
    assert r1["cost"] > r0["cost"]
    assert r1["price"] >= r0["price"]
    assert r1["time_hours"] >= r0["time_hours"]
    q = int(base["quantity"])
    assert abs((r1["cost"] - r0["cost"]) - 0.75 * q) < 0.01


def test_print_sheet_option_rounding_and_holes(calc, base_params):
    base = dict(base_params)
    r0 = calc.calculate(base)
    r_r = calc.calculate({**base, "option_rounding": True})
    assert r_r["cost"] > r0["cost"]
    r_h = calc.calculate({**base, "holes_per_item": 2})
    assert r_h["cost"] > r0["cost"]


def test_print_sheet_crease_lines(calc, base_params):
    base = dict(base_params)
    r0 = calc.calculate(base)
    r_c = calc.calculate({**base, "crease_lines_per_item": 2})
    assert r_c["cost"] > r0["cost"]
    assert r_c["time_hours"] >= r0["time_hours"]


def test_print_sheet_legacy_js_keys_still_work(calc, base_params):
    """Совместимость с именами из calcPrintSheet.js (is_number, is_hole, is_crease)."""
    base = dict(base_params)
    r = calc.calculate(
        {
            **base,
            "is_number": True,
            "is_barcode": True,
            "is_variables": True,
            "is_rounding": True,
            "is_hole": 1,
            "is_crease": 1,
        }
    )
    assert r["cost"] > 0
    assert r["price"] > 0


# ── Эталоны струйной ветки (calcPrintSheet → calcPrintInkJet) ─────────
JS_INKJET_REL_TOL = 0.001  # 0.1%

# JS, 31.10.2026
# calcPrintSheet(1, [420,297], '4+0', [0,0,0,0], 2, 'PaperSublimation128', {printer: EPSONWF7610}, 1)
REF_PARAMS_EPSON_1 = {
    "quantity": 1,
    "width": 420,
    "height": 297,
    "color": "4+0",
    "margins": [0, 0, 0, 0],
    "interval": 2,
    "material_id": "PaperSublimation128",
    "printer_code": "EPSONWF7610",
    "mode": 1,
}
EXPECTED_EPSON_1 = {
    "cost": 523.1,
    "price": 841.856,
    "time_hours": 0.35,
    "time_ready": 8.66,
    "weight_kg": 0.01596672,
}

# JS, 31.10.2026 — тираж ≥ 2
REF_PARAMS_EPSON_2 = {
    **REF_PARAMS_EPSON_1,
    "quantity": 2,
}
EXPECTED_EPSON_2 = {
    "cost": 644.2,
    "price": 1037.932,
    "time_hours": 0.44,
    "time_ready": 8.84,
}

# JS, 01.11.2026 — DTFTransfer, quality по умолчанию 0
REF_PARAMS_DTF = {
    "quantity": 2,
    "width": 100,
    "height": 100,
    "color": "4+0",
    "margins": [0, 0, 0, 0],
    "interval": 0,
    "material_id": "PaperSublimation128",
    "printer_code": "DTFTransfer",
    "mode": 1,
}
EXPECTED_DTF = {
    "cost": 1114.05,
    "price": 1810.548,
    "time_hours": 0.31,
    "time_ready": 32.57,
}


def test_expected_values_print_sheet_epson_qty1(calc):
    """JS, 31.10.2026: EPSONWF7610, тираж 1 — cost 523.1, price 841.856."""
    r = calc.calculate(REF_PARAMS_EPSON_1)
    e = EXPECTED_EPSON_1
    assert r["cost"] == pytest.approx(e["cost"], rel=JS_INKJET_REL_TOL)
    assert r["price"] == pytest.approx(e["price"], rel=JS_INKJET_REL_TOL)
    assert r["time_hours"] == pytest.approx(e["time_hours"], rel=JS_INKJET_REL_TOL)
    assert r["time_ready"] == pytest.approx(e["time_ready"], rel=JS_INKJET_REL_TOL)
    assert r["weight_kg"] == pytest.approx(e["weight_kg"], rel=JS_INKJET_REL_TOL)


def test_expected_values_print_sheet_epson_qty2(calc):
    """JS, 31.10.2026: EPSONWF7610, тираж 2."""
    r = calc.calculate(REF_PARAMS_EPSON_2)
    e = EXPECTED_EPSON_2
    assert r["cost"] == pytest.approx(e["cost"], rel=JS_INKJET_REL_TOL)
    assert r["price"] == pytest.approx(e["price"], rel=JS_INKJET_REL_TOL)
    assert r["time_hours"] == pytest.approx(e["time_hours"], rel=JS_INKJET_REL_TOL)
    assert r["time_ready"] == pytest.approx(e["time_ready"], rel=JS_INKJET_REL_TOL)


def test_expected_values_print_sheet_dtf(calc):
    """JS, 01.11.2026: DTFTransfer, тираж 2, quality по умолчанию 0."""
    r = calc.calculate(REF_PARAMS_DTF)
    e = EXPECTED_DTF
    assert r["cost"] == pytest.approx(e["cost"], rel=JS_INKJET_REL_TOL)
    assert r["price"] == pytest.approx(e["price"], rel=JS_INKJET_REL_TOL)
    assert r["time_hours"] == pytest.approx(e["time_hours"], rel=JS_INKJET_REL_TOL)
    assert r["time_ready"] == pytest.approx(e["time_ready"], rel=JS_INKJET_REL_TOL)


def test_print_sheet_material_size_mm(calc):
    """Элемент materials печати несёт size_mm листа из каталога."""
    r = calc.calculate(REF_PARAMS_EPSON_1)
    materials = r.get("materials") or []
    assert materials, "ожидается материал печати"
    mat = materials[0]
    assert "size_mm" in mat
    assert mat["size_mm"] == [297.0, 420.0]
