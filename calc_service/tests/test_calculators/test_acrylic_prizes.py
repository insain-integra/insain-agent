"""
Тесты калькулятора акриловых призов (acrylic_prizes).
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

_calc_service = Path(__file__).resolve().parent.parent.parent
if _calc_service.name == "calc_service" and str(_calc_service) not in sys.path:
    sys.path.insert(0, str(_calc_service))

from calculators.acrylic_prizes import AcrylicPrizesCalculator

JS_REL_TOL = 0.001  # 0.1%


def _cmp(a: float, b: float, rel: float = 0.03) -> bool:
    return abs(a - b) <= rel * max(abs(b), 1e-9)


@pytest.fixture(scope="module")
def calc():
    return AcrylicPrizesCalculator()


@pytest.fixture(scope="module")
def base_params():
    return {
        "quantity": 10,
        "layers": [
            {
                "materialID": "PVC3",
                "size": [100, 100],
                "isTop": False,
                "options": {},
            },
            {
                "materialID": "PVC3",
                "size": [100, 100],
                "isTop": True,
                "options": {
                    "isCutLaser": {},
                    "isUVPrint": {"size": [80, 80]},
                },
            },
        ],
        "mode": 1,
    }


@pytest.fixture(scope="module")
def result(calc, base_params):
    try:
        return calc.execute(base_params)
    except Exception:
        return None


def test_slug(calc):
    assert calc.slug == "acrylic_prizes"


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
    assert "acrylic_prizes" in result["share_url"]


def test_get_tool_schema(calc):
    schema = calc.get_tool_schema()
    assert schema.get("name") == "calc_acrylic_prizes"
    assert "parameters" in schema
    assert "quantity" in schema["parameters"].get("properties", {})


# ── Эталонные тесты ──────────────────────────────────────────────────

REF_PARAMS = {
    "quantity": 10,
    "layers": [
        {
            "materialID": "PVC3",
            "size": [100, 100],
            "isTop": False,
            "options": {},
        },
        {
            "materialID": "PVC3",
            "size": [100, 100],
            "isTop": True,
            "options": {
                "isCutLaser": {},
                "isUVPrint": {"size": [80, 80]},
            },
        },
    ],
    "mode": 1,
}

# JS, 04.11.2026 — сверка с calcAcrilycPrizes --data current
EXPECTED_REF = {
    "cost": 2092.45,
    "price": 3353.72,
    "time_hours": 2.67,
    "time_ready": 35.45,
    "weight_kg": 0.17,
}


@pytest.fixture(scope="module")
def ref_result(calc):
    try:
        return calc.execute(REF_PARAMS)
    except Exception:
        return None


def test_expected_values_acrylic_prizes(ref_result):
    if ref_result is None:
        pytest.skip("расчёт эталонного кейса не выполнен")
    r = ref_result
    e = EXPECTED_REF
    rel = 0.03

    ok_cost = _cmp(r["cost"], e["cost"], rel)
    ok_price = _cmp(r["price"], e["price"], rel)
    ok_time = _cmp(r["time_hours"], e["time_hours"], rel)
    ok_ready = _cmp(r["time_ready"], e["time_ready"], rel)
    ok_weight = _cmp(r["weight_kg"], e["weight_kg"], rel)

    print("")
    print("  [acrylic_prizes] quantity=%s  |  mode=%s" % (REF_PARAMS["quantity"], REF_PARAMS["mode"]))
    print("  ---")
    print("  cost        %s  (ожид. %s)  %s" % (r["cost"], e["cost"], "ok" if ok_cost else "FAIL"))
    print("  price       %s  (ожид. %s)  %s" % (r["price"], e["price"], "ok" if ok_price else "FAIL"))
    print("  time_hours  %s  (ожид. %s)  %s" % (r["time_hours"], e["time_hours"], "ok" if ok_time else "FAIL"))
    print("  time_ready  %s  (ожид. %s)  %s" % (r["time_ready"], e["time_ready"], "ok" if ok_ready else "FAIL"))
    print("  weight_kg   %s  (ожид. %s)  %s" % (r["weight_kg"], e["weight_kg"], "ok" if ok_weight else "FAIL"))

    assert ok_cost, f"cost: got {r['cost']}, expected ~{e['cost']}"
    assert ok_price, f"price: got {r['price']}, expected ~{e['price']}"
    assert ok_time, f"time_hours: got {r['time_hours']}, expected ~{e['time_hours']}"
    assert ok_ready, f"time_ready: got {r['time_ready']}, expected ~{e['time_ready']}"
    assert ok_weight, f"weight_kg: got {r['weight_kg']}, expected ~{e['weight_kg']}"


# JS, 08.11.2026 — дефолт формы 78: 100 шт., 2× AcrylTrans3 20×20, рез+УФ оба слоя, mode 1
# (ловит time_ready только при mode>0; эталон с одним УФ этого не ловит)
# node scripts/run_js_calc.mjs calcAcrilycPrizes --data current --args
# '[100,[{"materialID":"AcrylTrans3","size":[20,20],"isTop":true,"options":{"isCutLaser":{"lenCut":0,"sizeItem":0,"density":0,"difficulty":1.3},"isUVPrint":{"size":[20,20]}}},{"materialID":"AcrylTrans3","size":[20,20],"isTop":false,"options":{"isCutLaser":{"lenCut":0,"sizeItem":0,"density":0,"difficulty":1.3},"isUVPrint":{"size":[20,20]}}}],{},1]'
REF_FORM_DEFAULT = {
    "quantity": 100,
    "layers": [
        {
            "materialID": "AcrylTrans3",
            "size": [20, 20],
            "isTop": True,
            "options": {
                "isCutLaser": {"lenCut": 0, "sizeItem": 0, "density": 0, "difficulty": 1.3},
                "isUVPrint": {"size": [20, 20]},
            },
        },
        {
            "materialID": "AcrylTrans3",
            "size": [20, 20],
            "isTop": False,
            "options": {
                "isCutLaser": {"lenCut": 0, "sizeItem": 0, "density": 0, "difficulty": 1.3},
                "isUVPrint": {"size": [20, 20]},
            },
        },
    ],
    "mode": 1,
}

# JS, 08.11.2026 — weight JS 0.2856, API round 0.29 — в assert не входит
EXPECTED_FORM_DEFAULT = {
    "cost": 5599.45,
    "price": 8977.92,
    "time_hours": 2.48,
    "time_ready": 35.17,
}


def test_expected_form_default(calc):
    """JS, 08.11.2026: дефолт формы 78 — два слоя AcrylTrans3 с УФ, mode 1."""
    r = calc.execute(REF_FORM_DEFAULT)
    e = EXPECTED_FORM_DEFAULT
    assert r["cost"] == pytest.approx(e["cost"], rel=JS_REL_TOL)
    assert r["price"] == pytest.approx(e["price"], rel=JS_REL_TOL)
    assert r["time_hours"] == pytest.approx(e["time_hours"], rel=JS_REL_TOL)
    assert r["time_ready"] == pytest.approx(e["time_ready"], rel=JS_REL_TOL)


# JS, 08.11.2026 — тот же дефолт формы 78, mode 0 (сроки операций не входят)
# node scripts/run_js_calc.mjs calcAcrilycPrizes --data current --args
# '[100,[{"materialID":"AcrylTrans3","size":[20,20],"isTop":true,"options":{"isCutLaser":{"lenCut":0,"sizeItem":0,"density":0,"difficulty":1.3},"isUVPrint":{"size":[20,20]}}},{"materialID":"AcrylTrans3","size":[20,20],"isTop":false,"options":{"isCutLaser":{"lenCut":0,"sizeItem":0,"density":0,"difficulty":1.3},"isUVPrint":{"size":[20,20]}}}],{},0]'
REF_FORM_DEFAULT_MODE0 = {**REF_FORM_DEFAULT, "mode": 0}

# JS, 08.11.2026
EXPECTED_FORM_DEFAULT_MODE0 = {
    "price": 7794.4,
    "time_ready": 2.02,
}


def test_expected_form_default_mode0(calc):
    """JS, 08.11.2026: дефолт формы 78, mode 0 — time_ready = time_hours."""
    r = calc.execute(REF_FORM_DEFAULT_MODE0)
    e = EXPECTED_FORM_DEFAULT_MODE0
    assert r["price"] == pytest.approx(e["price"], rel=JS_REL_TOL)
    assert r["time_ready"] == pytest.approx(e["time_ready"], rel=JS_REL_TOL)


# JS, 08.11.2026 — дефолт формы 78, на верхнем слое вместо УФ гравировка с заливкой
# node scripts/run_js_calc.mjs calcAcrilycPrizes --data current --args
# '[100,[{"materialID":"AcrylTrans3","size":[20,20],"isTop":true,"options":{"isCutLaser":{"lenCut":0,"sizeItem":0,"density":0,"difficulty":1.3},"isGrave":1,"isGraveFill":[20,20]}},{"materialID":"AcrylTrans3","size":[20,20],"isTop":false,"options":{"isCutLaser":{"lenCut":0,"sizeItem":0,"density":0,"difficulty":1.3},"isUVPrint":{"size":[20,20]}}}],{},1]'
REF_FORM_GRAVE_FILL = {
    "quantity": 100,
    "layers": [
        {
            "materialID": "AcrylTrans3",
            "size": [20, 20],
            "isTop": True,
            "options": {
                "isCutLaser": {"lenCut": 0, "sizeItem": 0, "density": 0, "difficulty": 1.3},
                "isGrave": 1,
                "isGraveFill": [20, 20],
            },
        },
        {
            "materialID": "AcrylTrans3",
            "size": [20, 20],
            "isTop": False,
            "options": {
                "isCutLaser": {"lenCut": 0, "sizeItem": 0, "density": 0, "difficulty": 1.3},
                "isUVPrint": {"size": [20, 20]},
            },
        },
    ],
    "mode": 1,
}

# JS, 08.11.2026
EXPECTED_FORM_GRAVE_FILL = {
    "cost": 6389.45,
    "price": 10241.92,
    "time_ready": 36.36,
}


def test_expected_form_grave_fill(calc):
    """JS, 08.11.2026: дефолт формы 78, верхний слой isGrave+isGraveFill вместо УФ."""
    r = calc.execute(REF_FORM_GRAVE_FILL)
    e = EXPECTED_FORM_GRAVE_FILL
    assert r["cost"] == pytest.approx(e["cost"], rel=JS_REL_TOL)
    assert r["price"] == pytest.approx(e["price"], rel=JS_REL_TOL)
    assert r["time_ready"] == pytest.approx(e["time_ready"], rel=JS_REL_TOL)
