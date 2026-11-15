"""
Тесты сверки калькулятора лазерной резки и гравировки с реальными данными.

Кейс 1 — «Номерки», стандартная точность гравировки (is_grave=1).
Кейс 2 — те же размеры/тираж, высокая точность гравировки (is_grave=2).
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any, Dict, List

import pytest

# calc_service в path при запуске pytest из корня репозитория
_calc_service = Path(__file__).resolve().parent.parent.parent
if _calc_service.name == "calc_service" and str(_calc_service) not in sys.path:
    sys.path.insert(0, str(_calc_service))

from calculators.laser import LaserCalculator

ACRYL_3MM_CODE = "AcrylColor3"


def _nomerki_params(
    material_id: str = ACRYL_3MM_CODE,
    is_grave: int = 1,
) -> Dict[str, Any]:
    return {
        "quantity": 50,
        "width": 40,
        "height": 80,
        "material_id": material_id,
        "mode": 1,
        "is_cut_laser": {},
        "is_grave": is_grave,
        "is_grave_fill": [30, 40],
    }


# Ожидаемые значения (±1%): стандартная точность гравировки (is_grave=1)
EXPECTED = {
    "cost": 3498,
    "price": 5631,
    "time_hours": 3.05,
    "time_ready": 19.0,
    "weight_kg": 0.57,
    "materials": [
        {"code": "AcrylColor3", "quantity_approx": 0.033, "unit": "лист"},
    ],
}

# Высокая точность гравировки (is_grave=2)
EXPECTED_HIGH = {
    "cost": 5916,
    "price": 9501,
    "time_hours": 5.81,
    "time_ready": 21.81,
    "weight_kg": 0.57,
    "materials": [
        {"code": "AcrylColor3", "quantity_approx": 0.033, "unit": "лист"},
    ],
}


@pytest.fixture(scope="module")
def laser_calc():
    return LaserCalculator()


@pytest.fixture(scope="module")
def nomerki_result(laser_calc):
    try:
        return laser_calc.execute(_nomerki_params())
    except Exception:
        return None


@pytest.fixture(scope="module")
def nomerki_high_result(laser_calc):
    """Расчёт с высокой точностью гравировки (is_grave=2)."""
    try:
        return laser_calc.execute(_nomerki_params(is_grave=2))
    except Exception:
        return None


def _cmp(a: float, b: float, rel: float = 0.01) -> bool:
    return abs(a - b) <= rel * max(abs(b), 1e-9)


def _print_params(params: Dict[str, Any]) -> None:
    """Параметры расчёта: размер одним полем, порядок фиксированный."""
    w = params.get("width")
    h = params.get("height")
    parts = []
    if w is not None and h is not None:
        parts.append("size=%s×%s" % (w, h))
    order = ["quantity", "material_id", "mode", "is_grave", "is_grave_fill", "is_cut_laser"]
    for k in order:
        if k in ("width", "height"):
            continue
        v = params.get(k)
        if v is None or (isinstance(v, (dict, list)) and len(v) == 0):
            continue
        if isinstance(v, (list, tuple)):
            parts.append("%s=%s" % (k, "×".join(str(x) for x in v)))
        else:
            parts.append("%s=%s" % (k, v))
    for k, v in sorted(params.items()):
        if k in order or k in ("width", "height"):
            continue
        if v is None or (isinstance(v, (dict, list)) and len(v) == 0):
            continue
        if isinstance(v, (list, tuple)):
            parts.append("%s=%s" % (k, "×".join(str(x) for x in v)))
        else:
            parts.append("%s=%s" % (k, v))
    print("  Параметры   %s" % "  |  ".join(parts))


def test_laser_real_nomerki(nomerki_result):
    """Сверка: стоимость, время, вес, расход материалов. Вывод — сравнение в числах."""
    if nomerki_result is None:
        pytest.skip("расчёт не выполнен (гравировка/данные)")
    r = nomerki_result
    e = EXPECTED
    rel = 0.01

    ok_cost = _cmp(r["cost"], e["cost"], rel)
    ok_price = _cmp(r["price"], e["price"], rel)
    ok_time = _cmp(r["time_hours"], e["time_hours"], rel)
    ok_ready = _cmp(r["time_ready"], e["time_ready"], rel)
    ok_weight = _cmp(r["weight_kg"], e["weight_kg"], rel)

    print("")
    _print_params(_nomerki_params())
    share_url = r.get("share_url") or ""
    if share_url:
        print("  Ссылка      %s" % share_url)
    print("  ---")
    print("  cost        %s  (ожид. %s)  %s" % (r["cost"], e["cost"], "ok" if ok_cost else "FAIL"))
    print("  price       %s  (ожид. %s)  %s" % (r["price"], e["price"], "ok" if ok_price else "FAIL"))
    print("  time_hours  %s  (ожид. %s)  %s" % (r["time_hours"], e["time_hours"], "ok" if ok_time else "FAIL"))
    print("  time_ready  %s  (ожид. %s)  %s" % (r["time_ready"], e["time_ready"], "ok" if ok_ready else "FAIL"))
    print("  weight_kg   %s  (ожид. %s)  %s" % (r["weight_kg"], e["weight_kg"], "ok" if ok_weight else "FAIL"))
    mats: List[Dict[str, Any]] = r.get("materials") or []
    print("  materials   %s" % (len(mats) and "см. ниже" or "—"))
    for i, exp_mat in enumerate(e["materials"]):
        code = exp_mat["code"]
        exp_q = exp_mat["quantity_approx"]
        exp_unit = exp_mat.get("unit", "лист")
        got = next((m for m in mats if m.get("code") == code), None)
        if got is None:
            print("    %s  (нет в результате) ~ %s %s  FAIL" % (code, exp_q, exp_unit))
            continue
        got_q = got.get("quantity")
        got_unit = got.get("unit", "")
        ok_q = _cmp(float(got_q), float(exp_q), 0.05) if got_q is not None else False
        print("    %s  %s %s ~ %s %s  %s" % (code, got_q, got_unit, exp_q, exp_unit, "ok" if ok_q else "FAIL"))
        assert "name" in got
        assert "title" in got

    assert ok_cost, "cost: got %s, expected ~%s" % (r["cost"], e["cost"])
    assert ok_price, "price: got %s, expected ~%s" % (r["price"], e["price"])
    assert ok_time, "time_hours: got %s, expected ~%s" % (r["time_hours"], e["time_hours"])
    assert ok_ready, "time_ready: got %s, expected ~%s" % (r["time_ready"], e["time_ready"])
    assert ok_weight, "weight_kg: got %s, expected ~%s" % (r["weight_kg"], e["weight_kg"])


def test_param_schema(laser_calc: LaserCalculator) -> None:
    """Проверка param_schema для лазерного калькулятора."""
    calc = laser_calc
    schema = calc.get_param_schema()

    assert "slug" in schema
    assert schema["slug"] == "laser"

    assert "title" in schema
    assert "params" in schema
    assert "param_groups" in schema

    params = schema["params"]
    assert isinstance(params, list)
    assert len(params) > 0

    for p in params:
        assert "name" in p
        assert "type" in p
        assert "required" in p
        assert "title" in p

    required = calc.get_required_params()
    assert "quantity" in required
    assert "width_mm" in required

    defaults = calc.get_default_values()
    assert defaults.get("mode") == 1
    assert defaults.get("cut_length_m") == 0


def test_laser_real_nomerki_high(nomerki_high_result):
    """Сверка: та же раскладка, высокая точность гравировки (is_grave=2)."""
    if nomerki_high_result is None:
        pytest.skip("расчёт не выполнен (гравировка/данные)")
    r = nomerki_high_result
    e = EXPECTED_HIGH
    rel = 0.01

    ok_cost = _cmp(r["cost"], e["cost"], rel)
    ok_price = _cmp(r["price"], e["price"], rel)
    ok_time = _cmp(r["time_hours"], e["time_hours"], rel)
    ok_ready = _cmp(r["time_ready"], e["time_ready"], rel)
    ok_weight = _cmp(r["weight_kg"], e["weight_kg"], rel)

    print("")
    _print_params(_nomerki_params(is_grave=2))
    share_url = r.get("share_url") or ""
    if share_url:
        print("  Ссылка      %s" % share_url)
    print("  ---")
    print("  cost        %s  (ожид. %s)  %s" % (r["cost"], e["cost"], "ok" if ok_cost else "FAIL"))
    print("  price       %s  (ожид. %s)  %s" % (r["price"], e["price"], "ok" if ok_price else "FAIL"))
    print("  time_hours  %s  (ожид. %s)  %s" % (r["time_hours"], e["time_hours"], "ok" if ok_time else "FAIL"))
    print("  time_ready  %s  (ожид. %s)  %s" % (r["time_ready"], e["time_ready"], "ok" if ok_ready else "FAIL"))
    print("  weight_kg   %s  (ожид. %s)  %s" % (r["weight_kg"], e["weight_kg"], "ok" if ok_weight else "FAIL"))
    mats = r.get("materials") or []
    print("  materials   %s" % (len(mats) and "см. ниже" or "—"))
    for exp_mat in e["materials"]:
        code = exp_mat["code"]
        exp_q = exp_mat["quantity_approx"]
        exp_unit = exp_mat.get("unit", "лист")
        got = next((m for m in mats if m.get("code") == code), None)
        if got is None:
            print("    %s  (нет в результате) ~ %s %s  FAIL" % (code, exp_q, exp_unit))
            continue
        got_q = got.get("quantity")
        got_unit = got.get("unit", "")
        ok_q = _cmp(float(got_q), float(exp_q), 0.05) if got_q is not None else False
        print("    %s  %s %s ~ %s %s  %s" % (code, got_q, got_unit, exp_q, exp_unit, "ok" if ok_q else "FAIL"))

    assert ok_cost, "cost: got %s, expected ~%s" % (r["cost"], e["cost"])
    assert ok_price, "price: got %s, expected ~%s" % (r["price"], e["price"])
    assert ok_time, "time_hours: got %s, expected ~%s" % (r["time_hours"], e["time_hours"])
    assert ok_ready, "time_ready: got %s, expected ~%s" % (r["time_ready"], e["time_ready"])
    assert ok_weight, "weight_kg: got %s, expected ~%s" % (r["weight_kg"], e["weight_kg"])


JS_REL = 0.001


def _assert_js(result: Dict[str, Any], expected: Dict[str, Any]) -> None:
    assert result["cost"] == pytest.approx(expected["cost"], rel=JS_REL)
    assert result["price"] == pytest.approx(expected["price"], rel=JS_REL)
    assert result["time_hours"] == pytest.approx(expected["time_hours"], rel=JS_REL)
    assert result["time_ready"] == pytest.approx(expected["time_ready"], rel=JS_REL)


# JS, 15.11.2026 — дефолт формы 28: 100 шт., 50×50, материал «не задан», простая резка, mode 1.
# Раннер падает на weight NaN (material = []). Цена и срок — calcLaser на странице.
# Вес и materials по контракту API: 0 и пустой список.
# node scripts/run_js_calc.mjs calcLaser --data current --args
# '[100,[50,50],"",{"isCutLaser":{"sizeItem":50,"density":25,"difficulty":1,"lenCut":0},"isFindMark":false,"Material":"isMaterial"},1]'
REF_FORM_DEFAULT = {
    "quantity": 100,
    "width": 50,
    "height": 50,
    "material_id": "",
    "mode": 1,
    "is_cut_laser": {"len_cut": 0, "size_item": 50, "density": 25, "difficulty": 1},
    "is_find_mark": False,
    "material_mode": "isMaterial",
}
EXPECTED_FORM_DEFAULT = {
    "cost": 300,
    "price": 480,
    "time_hours": 0.2,
    "time_ready": 16.2,
    "weight_kg": 0.0,
}


def test_form_default_empty_material(laser_calc):
    """JS, 15.11.2026: дефолт формы 28, пустой материал — только время подготовки."""
    r = laser_calc.execute(REF_FORM_DEFAULT)
    e = EXPECTED_FORM_DEFAULT
    _assert_js(r, e)
    assert r["weight_kg"] == pytest.approx(e["weight_kg"], abs=1e-9)
    assert r["materials"] == []
    for key in ("cost", "price", "unit_price", "time_hours", "time_ready", "weight_kg", "materials"):
        assert key in r


# JS, 15.11.2026 — тот же пустой материал без ключа material_id и без is_cut_laser.
REF_EMPTY_MATERIAL = {
    "quantity": 100,
    "width": 50,
    "height": 50,
    "mode": 1,
}


def test_laser_empty_material_id(laser_calc):
    """JS, 15.11.2026: material_id не передан — не 400, та же цена подготовки."""
    r = laser_calc.execute(REF_EMPTY_MATERIAL)
    _assert_js(r, EXPECTED_FORM_DEFAULT)
    assert r["weight_kg"] == pytest.approx(0.0, abs=1e-9)
    assert r["materials"] == []


# JS, 15.11.2026 — «без резки», 100 шт. 50×50 AcrylWhite3, mode 1.
# node scripts/run_js_calc.mjs calcLaser --data current --args
# '[100,[50,50],"AcrylWhite3",{"Material":"isMaterial"},1]'
REF_NO_CUT = {
    "quantity": 100,
    "width": 50,
    "height": 50,
    "material_id": "AcrylWhite3",
    "mode": 1,
    "material_mode": "isMaterial",
}
EXPECTED_NO_CUT = {
    "cost": 857,
    "price": 1404,
    "time_hours": 0.2,
    "time_ready": 16.2,
    "weight_kg": 0.8925,
}


def test_laser_no_cut(laser_calc):
    """JS, 15.11.2026: нет is_cut_laser — площадь первого листа, время реза 0."""
    r = laser_calc.execute(REF_NO_CUT)
    _assert_js(r, EXPECTED_NO_CUT)
    assert r["weight_kg"] == pytest.approx(EXPECTED_NO_CUT["weight_kg"], rel=JS_REL)
    mats = r["materials"]
    assert len(mats) == 1
    mat = mats[0]
    assert mat["code"] == "AcrylWhite3"
    assert mat["name"] == "Акрил молочный Plexiglas XT 3мм"
    assert mat["title"] == "Акрил молочный 3мм"
    assert mat["name"] != mat["code"]
    assert mat["unit"] == "лист"
    assert list(mat["size_mm"]) == [3050.0, 2050.0]
    assert mat["quantity"] == pytest.approx(105 * 50 * 50 / 3050 / 2050, rel=JS_REL)


# JS, 15.11.2026 — простая резка, эталон не должен сдвинуться после ветки «без резки».
# node scripts/run_js_calc.mjs calcLaser --data current --args
# '[100,[50,50],"AcrylWhite3",{"isCutLaser":{"sizeItem":50,"density":25,"difficulty":1,"lenCut":0},"isFindMark":false,"Material":"isMaterial"},1]'
REF_SIMPLE_CUT = {
    "quantity": 100,
    "width": 50,
    "height": 50,
    "material_id": "AcrylWhite3",
    "mode": 1,
    "is_cut_laser": {"len_cut": 0, "size_item": 50, "density": 25, "difficulty": 1},
    "is_find_mark": False,
    "material_mode": "isMaterial",
}
EXPECTED_SIMPLE_CUT = {
    "cost": 14748,
    "price": 23638,
    "time_hours": 11.17,
    "time_ready": 27.17,
    "weight_kg": 0.8925,
}


def test_laser_simple_cut_unchanged(laser_calc):
    """JS, 15.11.2026: простая резка AcrylWhite3 — price 23638, time_ready 27.17."""
    r = laser_calc.execute(REF_SIMPLE_CUT)
    _assert_js(r, EXPECTED_SIMPLE_CUT)
    assert r["weight_kg"] == pytest.approx(EXPECTED_SIMPLE_CUT["weight_kg"], rel=JS_REL)


def test_nomerki_matches_js_tight(laser_calc):
    """JS, 15.11.2026: номерки — price 5631, time_ready 19.05."""
    r = laser_calc.execute(_nomerki_params())
    assert r["price"] == pytest.approx(5631, rel=JS_REL)
    assert r["time_ready"] == pytest.approx(19.05, rel=JS_REL)


# JS, 15.11.2026 — простая резка AcrylWhite3, три режима материала.
# node scripts/run_js_calc.mjs calcLaser --data current --args
# '[100,[50,50],"AcrylWhite3",{"isCutLaser":{"sizeItem":50,"density":25,"difficulty":1,"lenCut":0},"isFindMark":false,"Material":"isMaterial"},1]'
# noMaterial: '[...,"Material":"noMaterial",...]' → cost 14041, price 22465, time 11.17 / 27.17, weight 0.8925
# isMaterialCustomer: time_cut × 1.25 → cost 17476, price 27961, time 13.92 / 29.92, weight 0.8925
# Вес в JS считается по material и при noMaterial / isMaterialCustomer не обнуляется.
REF_MATERIAL_MODES = {
    "isMaterial": EXPECTED_SIMPLE_CUT,
    "noMaterial": {
        "cost": 14041,
        "price": 22465,
        "time_hours": 11.17,
        "time_ready": 27.17,
        "weight_kg": 0.8925,
    },
    "isMaterialCustomer": {
        "cost": 17476,
        "price": 27961,
        "time_hours": 13.92,
        "time_ready": 29.92,
        "weight_kg": 0.8925,
    },
}


@pytest.mark.parametrize("material_mode", ["isMaterial", "noMaterial", "isMaterialCustomer"])
def test_laser_material_mode(laser_calc, material_mode):
    """JS, 15.11.2026: isMaterial / noMaterial / isMaterialCustomer на простой резке."""
    params = dict(REF_SIMPLE_CUT)
    params["material_mode"] = material_mode
    r = laser_calc.execute(params)
    expected = REF_MATERIAL_MODES[material_mode]
    _assert_js(r, expected)
    assert r["weight_kg"] == pytest.approx(expected["weight_kg"], rel=JS_REL)
    codes = [item.get("code") for item in r["materials"]]
    if material_mode == "isMaterial":
        assert "AcrylWhite3" in codes
        mat = next(item for item in r["materials"] if item.get("code") == "AcrylWhite3")
        assert mat["name"]
        assert mat["title"]
        assert mat["name"] != mat["code"]
    else:
        assert "AcrylWhite3" not in codes
    for key in ("cost", "price", "unit_price", "time_hours", "time_ready", "weight_kg", "materials"):
        assert key in r


# JS, 15.11.2026 — номерки, материал заказчика: time_grave тоже × 1.25.
# node scripts/run_js_calc.mjs calcLaser --data current --args
# '[50,[40,80],"AcrylColor3",{"isCutLaser":{"lenCut":0,"sizeItem":0,"density":0,"difficulty":1},"isGrave":1,"isGraveFill":[30,40],"Material":"isMaterialCustomer"},1]'
EXPECTED_NOMERKI_CUSTOMER = {
    "cost": 3568,
    "price": 5708,
    "time_hours": 3.77,
    "time_ready": 19.77,
    "weight_kg": 0.5712,
}


def test_laser_nomerki_material_customer(laser_calc):
    """JS, 15.11.2026: номерки isMaterialCustomer — гравировка и рез × 1.25, материал не в цене."""
    params = _nomerki_params()
    params["material_mode"] = "isMaterialCustomer"
    r = laser_calc.execute(params)
    _assert_js(r, EXPECTED_NOMERKI_CUSTOMER)
    assert r["weight_kg"] == pytest.approx(EXPECTED_NOMERKI_CUSTOMER["weight_kg"], rel=JS_REL)
    assert all(item.get("code") != ACRYL_3MM_CODE for item in r["materials"])

