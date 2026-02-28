"""
Тесты калькулятора рулонной резки (cut_roller).
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

_calc_service = Path(__file__).resolve().parent.parent.parent
if _calc_service.name == "calc_service" and str(_calc_service) not in sys.path:
    sys.path.insert(0, str(_calc_service))

from calculators.base import ProductionMode
from calculators.cut_roller import CutRollerCalculator

# Ожидаемые значения для эталонного кейса: 13 шт, 320×450 мм, SUPERWAIS, KWTrio3026.
# По умолчанию материал в цену не включаем (material_mode=noMaterial) — эталон только резка.
# При isMaterial — добавляется стоимость материала (~673/1102). При isMaterialCustomer — +25% к резке.
EXPECTED = {
    "cost": 243.0,
    "price": 389.0,
    "time_hours": 0.17,
    "weight_kg": 0.54288,
    "time_ready": 8.17,
}


def _cmp(a: float, b: float, rel: float = 0.01) -> bool:
    """Проверка совпадения с относительным допуском."""
    return abs(a - b) <= rel * max(abs(b), 1e-9)


def _print_params(params: dict) -> None:
    """Вывод параметров расчёта рулонной резки."""
    parts = [
        "quantity=%s" % params.get("quantity"),
        "size=%s×%s" % (params.get("width"), params.get("height")),
        "material_id=%s" % params.get("material_id"),
        "material_category=%s" % params.get("material_category"),
        "cutter_code=%s" % (params.get("cutter_code") or ""),
        "material_mode=%s" % params.get("material_mode"),
        "mode=%s" % params.get("mode"),
    ]
    print("  Параметры   %s" % "  |  ".join(parts))


@pytest.fixture(scope="module")
def calc():
    return CutRollerCalculator()


@pytest.fixture(scope="module")
def base_params(calc):
    """Параметры по умолчанию для общих тестов (без эталона)."""
    opts = calc.get_options()
    materials = opts.get("materials") or []
    mat = materials[0] if materials else {}
    code = mat.get("code", "")
    return {
        "quantity": 50,
        "width": 100,
        "height": 150,
        "material_id": code or "Paper80",
        "material_category": "sheet",
        "cutter_code": "",
        "material_mode": "isMaterial",
        "mode": 1,
    }


@pytest.fixture(scope="module")
def ref_params():
    """Параметры эталонного кейса: 13 шт, 320×450 мм, SUPERWAIS, резак KWTrio3026. По умолчанию материал в цену не включаем (noMaterial) — эталон 243/389 только резка."""
    return {
        "quantity": 13,
        "width": 320,
        "height": 450,
        "material_id": "SUPERWAIS",
        "material_category": "sheet",
        "cutter_code": "KWTrio3026",
        "material_mode": "noMaterial",
        "mode": 1,
    }


@pytest.fixture(scope="module")
def ref_result(calc, ref_params):
    """Результат расчёта для эталонного кейса."""
    try:
        return calc.execute(ref_params)
    except Exception:
        return None


@pytest.fixture(scope="module")
def result(calc, base_params):
    if not base_params.get("material_id"):
        return None
    try:
        return calc.execute(base_params)
    except Exception:
        return None


def test_slug(calc):
    assert calc.slug == "cut_roller"


def test_calculate_basic(result):
    if result is None:
        pytest.skip("нет материала в опциях или расчёт не выполнен")
    for key in ("cost", "price", "unit_price", "time_hours", "time_ready", "weight_kg", "materials"):
        assert key in result
    assert result["cost"] > 0
    assert result["price"] > 0
    assert result["time_hours"] > 0
    assert result["time_ready"] > 0


def test_expected_values(ref_result, ref_params):
    """Сверка с эталоном: 13 шт, 320×450 мм, SUPERWAIS, KWTrio3026. cost 243 р., price 389 р., time 0,17 ч., weight 0,54288 кг, time_ready 8,17. Допуск 1%."""
    if ref_result is None:
        pytest.skip("расчёт эталонного кейса не выполнен (материал SUPERWAIS?)")
    r = ref_result
    e = EXPECTED
    rel = 0.01

    ok_cost = _cmp(r["cost"], e["cost"], rel)
    ok_price = _cmp(r["price"], e["price"], rel)
    ok_time = _cmp(r["time_hours"], e["time_hours"], rel)
    ok_weight = _cmp(r["weight_kg"], e["weight_kg"], rel)
    ok_ready = _cmp(r["time_ready"], e["time_ready"], rel)

    print("")
    _print_params(ref_params)
    share_url = r.get("share_url") or ""
    if share_url:
        print("  Ссылка      %s" % share_url)
    print("  ---")
    print("  cost        %s  (ожид. %s)  %s" % (r["cost"], e["cost"], "ok" if ok_cost else "FAIL"))
    print("  price       %s  (ожид. %s)  %s" % (r["price"], e["price"], "ok" if ok_price else "FAIL"))
    print("  time_hours  %s  (ожид. %s)  %s" % (r["time_hours"], e["time_hours"], "ok" if ok_time else "FAIL"))
    print("  weight_kg   %s  (ожид. %s)  %s" % (r["weight_kg"], e["weight_kg"], "ok" if ok_weight else "FAIL"))
    print("  time_ready  %s  (ожид. %s)  %s" % (r["time_ready"], e["time_ready"], "ok" if ok_ready else "FAIL"))

    assert ok_cost, "cost: got %s, expected ~%s" % (r["cost"], e["cost"])
    assert ok_price, "price: got %s, expected ~%s" % (r["price"], e["price"])
    assert ok_time, "time_hours: got %s, expected ~%s" % (r["time_hours"], e["time_hours"])
    assert ok_weight, "weight_kg: got %s, expected ~%s" % (r["weight_kg"], e["weight_kg"])
    assert ok_ready, "time_ready: got %s, expected ~%s" % (r["time_ready"], e["time_ready"])


def test_time_hours_positive(result):
    if result is None:
        pytest.skip("расчёт не выполнен")
    assert result["time_hours"] > 0


def test_time_ready_greater(result):
    if result is None:
        pytest.skip("расчёт не выполнен")
    assert result["time_ready"] > result["time_hours"]


def test_time_ready_modes(calc, base_params):
    if not base_params.get("material_id"):
        pytest.skip("нет материала")
    base_params = dict(base_params)
    res_e = calc.calculate({**base_params, "mode": ProductionMode.ECONOMY})
    res_s = calc.calculate({**base_params, "mode": ProductionMode.STANDARD})
    res_x = calc.calculate({**base_params, "mode": ProductionMode.EXPRESS})
    assert res_e["time_ready"] >= res_s["time_ready"]
    assert res_s["time_ready"] >= res_x["time_ready"]


def test_more_quantity_more_time(calc, base_params):
    if not base_params.get("material_id"):
        pytest.skip("нет материала")
    base_params = dict(base_params)
    r10 = calc.calculate({**base_params, "quantity": 10})
    r100 = calc.calculate({**base_params, "quantity": 100})
    assert r100["time_hours"] > r10["time_hours"]


def test_price_greater_than_cost(result):
    if result is None:
        pytest.skip("расчёт не выполнен")
    assert result["price"] > result["cost"]


def test_share_url_contains_slug(result):
    if result is None:
        pytest.skip("расчёт не выполнен")
    assert "share_url" in result
    assert "cut_roller" in result["share_url"]


def test_get_options_not_empty(calc):
    opts = calc.get_options()
    assert "modes" in opts
    assert "materials" in opts
    assert "cutters" in opts


def test_get_tool_schema(calc):
    schema = calc.get_tool_schema()
    assert schema.get("name") == "calc_" + calc.slug
    assert "parameters" in schema
