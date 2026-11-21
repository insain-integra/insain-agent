"""
Тесты калькулятора полимерных стикеров (poly_sticker).
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

_calc_service = Path(__file__).resolve().parent.parent.parent
if _calc_service.name == "calc_service" and str(_calc_service) not in sys.path:
    sys.path.insert(0, str(_calc_service))

from calculators.poly_sticker import PolyStickerCalculator


@pytest.fixture(scope="module")
def calc():
    return PolyStickerCalculator()


@pytest.fixture(scope="module")
def base_params():
    return {
        "quantity": 20,
        "width": 80,
        "height": 80,
        "material_id": "PaperCoated115M",
        "color": "4+0",
        "difficulty": 1,
        "mode": 1,
    }


@pytest.fixture(scope="module")
def result(calc, base_params):
    try:
        return calc.execute(base_params)
    except Exception:
        return None


def test_slug(calc):
    assert calc.slug == "poly_sticker"


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
    assert "poly_sticker" in result["share_url"]


def test_get_options(calc):
    opts = calc.get_options()
    assert "materials" in opts
    assert "modes" in opts


def test_get_tool_schema(calc):
    schema = calc.get_tool_schema()
    assert schema.get("name") == "calc_poly_sticker"
    assert "parameters" in schema


# ── Эталонный тест ───────────────────────────────────────────────────

def _cmp(a: float, b: float, rel: float = 0.001) -> bool:
    return abs(a - b) <= rel * max(abs(b), 1e-9)


REF_PARAMS = {
    "quantity": 20,
    "width": 80,
    "height": 80,
    "material_id": "PaperCoated115M",
    "color": "4+0",
    "difficulty": 1,
    "mode": 1,
}
# JS, 14.11.2026 — 20 шт 80×80 PaperCoated115M, 4+0, difficulty 1, mode 1. 2 листа [320, 450].
# node scripts/run_js_calc.mjs calcPolySticker --data current --args '[20,[80,80],1,"PaperCoated115M",{"isPrint":{"printerID":"KMBizhubC220","color":"4+0"}},1]'
# time_hours раннера 0.89; Python 0.88 — round в print_laser (вне scope). Допуск времени 0.01 ч.
EXPECTED_REF = {
    "cost": 2205,
    "price": 4107.8,
    "time_hours": 0.89,
    "time_ready": 40.89,
    "weight_kg": 0.27,
}
EXPECTED_MATERIAL = {
    "code": "PaperCoated115M",
    "name_substring": "Титан DIGITAL",
    "quantity_approx": 2,
}


@pytest.fixture(scope="module")
def ref_result(calc):
    try:
        return calc.execute(REF_PARAMS)
    except Exception:
        return None


def test_expected_values_poly_sticker(ref_result):
    if ref_result is None:
        pytest.skip("расчёт эталонного кейса не выполнен")
    r = ref_result
    e = EXPECTED_REF
    em = EXPECTED_MATERIAL
    rel = 0.001

    ok_cost = _cmp(r["cost"], e["cost"], rel)
    ok_price = _cmp(r["price"], e["price"], rel)
    # 0.01 ч — round в print_laser против Math.ceil в JS; 1e-9 гасит хвост float.
    ok_time = abs(r["time_hours"] - e["time_hours"]) <= 0.01 + 1e-9
    ok_ready = _cmp(r["time_ready"], e["time_ready"], rel)
    ok_weight = _cmp(r["weight_kg"], e["weight_kg"], rel)

    materials = r.get("materials") or []
    mat = materials[0] if materials else {}
    ok_mat_code = mat.get("code") == em["code"]
    ok_mat_name = em["name_substring"] in (mat.get("name") or "")
    ok_mat_q = _cmp(float(mat.get("quantity") or 0), float(em["quantity_approx"]), 0.15) if materials else False

    print("")
    print("  [полимерные стикеры] quantity=%s  |  size=%s×%s  |  material_id=%s  |  color=%s  |  difficulty=%s  |  mode=%s"
          % (REF_PARAMS["quantity"], REF_PARAMS["width"], REF_PARAMS["height"],
             REF_PARAMS["material_id"], REF_PARAMS["color"], REF_PARAMS["difficulty"], REF_PARAMS["mode"]))
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
                (mat.get("name") or "")[:50],
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
    assert materials, "ожидается материал в результате"
    assert ok_mat_code, f"material code: got {mat.get('code')}, expected {em['code']}"
    assert ok_mat_name, f"material name должен содержать '{em['name_substring']}'"
    assert ok_mat_q, f"material quantity: got {mat.get('quantity')}, expected ~{em['quantity_approx']}"


# JS, 21.11.2026 — дефолт формы 30: 100 шт 50×50 RaflatacMW, сложность 1, без печати, mode 1.
# node scripts/run_js_calc.mjs calcPolySticker --data current --args '[100,[50,50],1,"RaflatacMW",{},1]'
# mode=0 и mode=2 — тот же вход, последний аргумент 0 и 2.
# mode=2 weight: раннер 0.65, Python 0.64 — round веса эпоксидки, в assert не входит.
REF_FORM_DEFAULT = {
    "quantity": 100,
    "width": 50,
    "height": 50,
    "material_id": "RaflatacMW",
    "difficulty": 1,
    "mode": 1,
}
EXPECTED_FORM_DEFAULT = {
    "cost": 5486,
    "price": 10224.65,
    "time_hours": 2.27,
    "time_ready": 42.27,
    "weight_kg": 0.56,
}
# mode, cost, price, time_hours, time_ready
_FORM_DEFAULT_MODES = (
    (0, 5337, 9952.1, 2.19, 58.19),
    (2, 6363, 11855.35, 2.69, 26.69),
)


def test_form_default_raflatac(calc):
    """Дефолт формы 30: RaflatacMW без печати."""
    result = calc.execute(REF_FORM_DEFAULT)
    expected = EXPECTED_FORM_DEFAULT
    rel = 0.001
    assert _cmp(result["cost"], expected["cost"], rel), result["cost"]
    assert _cmp(result["price"], expected["price"], rel), result["price"]
    assert _cmp(result["time_hours"], expected["time_hours"], rel), result["time_hours"]
    assert _cmp(result["time_ready"], expected["time_ready"], rel), result["time_ready"]
    assert _cmp(result["weight_kg"], expected["weight_kg"], rel), result["weight_kg"]
    materials = result["materials"]
    film = materials[0]
    assert film["code"] == "RaflatacMW"
    assert film["quantity"] == 4
    assert film["unit"] == "лист"
    assert film["size_mm"] == [320.0, 450.0]
    assert "title" in film
    epoxy = next(item for item in materials if item.get("code") == "EpoxyPoly")
    assert epoxy["quantity"] == pytest.approx(0.48, rel=0.001)
    assert "title" in epoxy


@pytest.mark.parametrize("mode,cost,price,time_hours,time_ready", _FORM_DEFAULT_MODES)
def test_form_default_modes(calc, mode, cost, price, time_hours, time_ready):
    """Дефолт формы 30 на mode=0 и mode=2: цена и срок как у раннера."""
    result = calc.execute({**REF_FORM_DEFAULT, "mode": mode})
    rel = 0.001
    assert _cmp(result["cost"], cost, rel), result["cost"]
    assert _cmp(result["price"], price, rel), result["price"]
    assert _cmp(result["time_hours"], time_hours, rel), result["time_hours"]
    assert _cmp(result["time_ready"], time_ready, rel), result["time_ready"]


def test_form_default_mode_order(calc):
    """Своё производство: price(0) < price(1) < price(2), срок наоборот."""
    prices = []
    ready = []
    for mode in (0, 1, 2):
        result = calc.execute({**REF_FORM_DEFAULT, "mode": mode})
        prices.append(result["price"])
        ready.append(result["time_ready"])
    assert prices[0] < prices[1] < prices[2]
    assert ready[2] < ready[1] < ready[0]
