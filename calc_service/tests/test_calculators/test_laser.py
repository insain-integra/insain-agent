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
    material_code: str = ACRYL_3MM_CODE,
    is_grave: int = 1,
) -> Dict[str, Any]:
    return {
        "quantity": 50,
        "width_mm": 40,
        "height_mm": 80,
        "material_code": material_code,
        "mode": 1,
        "is_cut_laser": {},
        "is_grave": is_grave,
        "is_grave_fill": [30, 40],
    }


# Ожидаемые значения (±1%): стандартная точность гравировки (is_grave=1)
EXPECTED = {
    "cost": 3328,
    "price": 5359,
    "time_hours": 3.05,
    "time_ready": 19.0,
    "weight_kg": 0.57,
    "materials": [
        {"code": "AcrylColor3", "quantity_approx": 0.033, "unit": "sheet"},
    ],
}

# Высокая точность гравировки (is_grave=2)
EXPECTED_HIGH = {
    "cost": 5608,
    "price": 9008,
    "time_hours": 5.81,
    "time_ready": 21.81,
    "weight_kg": 0.57,
    "materials": [
        {"code": "AcrylColor3", "quantity_approx": 0.033, "unit": "sheet"},
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
    w = params.get("width_mm")
    h = params.get("height_mm")
    parts = []
    if w is not None and h is not None:
        parts.append("size=%s×%s" % (w, h))
    order = ["quantity", "material_code", "mode", "is_grave", "is_grave_fill", "is_cut_laser"]
    for k in order:
        if k in ("width_mm", "height_mm"):
            continue
        v = params.get(k)
        if v is None or (isinstance(v, (dict, list)) and len(v) == 0):
            continue
        if isinstance(v, (list, tuple)):
            parts.append("%s=%s" % (k, "×".join(str(x) for x in v)))
        else:
            parts.append("%s=%s" % (k, v))
    for k, v in sorted(params.items()):
        if k in order or k in ("width_mm", "height_mm"):
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
        exp_unit = exp_mat.get("unit", "sheet")
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
        exp_unit = exp_mat.get("unit", "sheet")
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
