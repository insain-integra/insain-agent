"""
Тесты калькуляторов магнитов: magnet_acrylic, magnet_laminated.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

_calc_service = Path(__file__).resolve().parent.parent.parent
if _calc_service.name == "calc_service" and str(_calc_service) not in sys.path:
    sys.path.insert(0, str(_calc_service))

from calculators.magnets import (
    LAMINATED_MAGNET_VINYL_CODES,
    SHAPE_NONSTANDART,
    SHAPE_RECTANGULAR,
    SHAPE_RECTANGULAR_ROUNDED,
    SHAPE_STANDART,
    VALID_SHAPES,
    MagnetAcrylicCalculator,
    MagnetLaminatedCalculator,
    calc_laminated_magnets,
)


def _cmp(a: float, b: float, rel: float = 0.03) -> bool:
    return abs(a - b) <= rel * max(abs(b), 1e-9)


@pytest.fixture(scope="module")
def calc():
    return MagnetAcrylicCalculator()


@pytest.fixture(scope="module")
def base_params():
    return {
        "quantity": 100,
        "magnet_id": "MagnetAcrylic6565",
        "color": 1,
        "is_packing": True,
        "mode": 1,
    }


@pytest.fixture(scope="module")
def result(calc, base_params):
    try:
        return calc.execute(base_params)
    except Exception:
        return None


def test_slug(calc):
    assert calc.slug == "magnet_acrylic"


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
    assert "magnet_acrylic" in result["share_url"]


def test_get_tool_schema(calc):
    schema = calc.get_tool_schema()
    assert schema.get("name") == "calc_magnet_acrylic"
    assert "parameters" in schema
    assert "quantity" in schema["parameters"].get("properties", {})


# ── Эталонные тесты (акрил) ───────────────────────────────────────────

REF_PARAMS = {
    "quantity": 100,
    "magnet_id": "MagnetAcrylic6565",
    "color": 1,
    "is_packing": True,
    "mode": 1,
}

EXPECTED_REF = {
    "cost": 3046.69,
    "price": 4971.0,
    "time_hours": 0.99,
    "time_ready": 9.346,
    "weight_kg": 2.137,
}

EXPECTED_MATERIAL = {
    "code": "MagnetAcrylic6565",
    "name_substring": "магнит",
    "quantity_approx": 100,
}


@pytest.fixture(scope="module")
def ref_result(calc):
    try:
        return calc.execute(REF_PARAMS)
    except Exception:
        return None


def test_expected_values_magnet_acrylic(ref_result):
    if ref_result is None:
        pytest.skip("расчёт эталонного кейса не выполнен")
    r = ref_result
    e = EXPECTED_REF
    em = EXPECTED_MATERIAL
    rel = 0.03

    ok_cost = _cmp(r["cost"], e["cost"], rel)
    ok_price = _cmp(r["price"], e["price"], rel)
    ok_time = _cmp(r["time_hours"], e["time_hours"], rel)
    ok_ready = _cmp(r["time_ready"], e["time_ready"], rel)
    ok_weight = _cmp(r["weight_kg"], e["weight_kg"], rel)

    materials = r.get("materials") or []
    mat_match = next((m for m in materials if m.get("code") == em["code"]), {})
    ok_mat_code = bool(mat_match)
    ok_mat_name = em["name_substring"].lower() in (mat_match.get("name") or "").lower()
    ok_mat_q = _cmp(float(mat_match.get("quantity") or 0), float(em["quantity_approx"]), 0.15) if mat_match else False

    print("")
    print(
        "  [magnet_acrylic] quantity=%s  |  magnet_id=%s  |  mode=%s"
        % (REF_PARAMS["quantity"], REF_PARAMS["magnet_id"], REF_PARAMS["mode"])
    )
    print("  ---")
    print("  cost        %s  (ожид. %s)  %s" % (r["cost"], e["cost"], "ok" if ok_cost else "FAIL"))
    print("  price       %s  (ожид. %s)  %s" % (r["price"], e["price"], "ok" if ok_price else "FAIL"))
    print("  time_hours  %s  (ожид. %s)  %s" % (r["time_hours"], e["time_hours"], "ok" if ok_time else "FAIL"))
    print("  time_ready  %s  (ожид. %s)  %s" % (r["time_ready"], e["time_ready"], "ok" if ok_ready else "FAIL"))
    print("  weight_kg   %s  (ожид. %s)  %s" % (r["weight_kg"], e["weight_kg"], "ok" if ok_weight else "FAIL"))
    if mat_match:
        print(
            "  material    code=%s  name=%s  quantity=%s  (ожид. code=%s, name содержит '%s', qty ~%s)  %s"
            % (
                mat_match.get("code"),
                (mat_match.get("name") or "")[:50],
                mat_match.get("quantity"),
                em["code"],
                em["name_substring"],
                em["quantity_approx"],
                "ok" if (ok_mat_code and ok_mat_name and ok_mat_q) else "FAIL",
            )
        )
        assert "title" in mat_match

    assert ok_cost, f"cost: got {r['cost']}, expected ~{e['cost']}"
    assert ok_price, f"price: got {r['price']}, expected ~{e['price']}"
    assert ok_time, f"time_hours: got {r['time_hours']}, expected ~{e['time_hours']}"
    assert ok_ready, f"time_ready: got {r['time_ready']}, expected ~{e['time_ready']}"
    assert ok_weight, f"weight_kg: got {r['weight_kg']}, expected ~{e['weight_kg']}"
    assert ok_mat_code, f"material code {em['code']} не найден в materials"
    assert ok_mat_name, f"material name должен содержать '{em['name_substring']}'"
    assert ok_mat_q, f"material quantity: got {mat_match.get('quantity')}, expected ~{em['quantity_approx']}"


# ── Отдельные калькуляторы magnet_acrylic / magnet_laminated ─────────


@pytest.fixture(scope="module")
def calc_acrylic():
    return MagnetAcrylicCalculator()


@pytest.fixture(scope="module")
def calc_laminated():
    return MagnetLaminatedCalculator()


def test_magnet_acrylic_slug_and_execute(calc_acrylic):
    assert calc_acrylic.slug == "magnet_acrylic"
    r = calc_acrylic.execute(
        {
            "quantity": 100,
            "magnet_id": "MagnetAcrylic6565",
            "color": 1,
            "is_packing": True,
            "mode": 1,
        }
    )
    assert "cost" in r and "share_url" in r
    assert "magnet_acrylic" in r["share_url"]
    schema = calc_acrylic.get_tool_schema()
    assert schema.get("name") == "calc_magnet_acrylic"


def test_magnet_acrylic_invalid_magnet_id_raises(calc_acrylic):
    with pytest.raises(ValueError, match="Неверный код заготовки"):
        calc_acrylic.execute(
            {
                "quantity": 1,
                "magnet_id": "TotallyFakeCode999",
                "color": 1,
                "is_packing": True,
                "mode": 1,
            }
        )


def test_magnet_laminated_slug_and_execute(calc_laminated):
    assert calc_laminated.slug == "magnet_laminated"
    r = calc_laminated.execute(
        {
            "quantity": 50,
            "magnet_id": "MagnetVinil04",
            "width_mm": 90,
            "height_mm": 54,
            "mode": 1,
        }
    )
    assert "cost" in r and "share_url" in r
    assert "magnet_laminated" in r["share_url"]
    schema = calc_laminated.get_tool_schema()
    assert schema.get("name") == "calc_magnet_laminated"


def test_magnet_laminated_vinyl_only_three_codes(calc_laminated):
    schema = calc_laminated.get_param_schema()
    magnet_param = next(p for p in schema["params"] if p["name"] == "magnet_id")
    ids = {c["id"] for c in magnet_param["choices"]["inline"]}
    assert ids == set(LAMINATED_MAGNET_VINYL_CODES)


def test_laminated_magnets_reject_glue_vinyl():
    with pytest.raises(ValueError, match="Укажите толщину магнитного винила"):
        calc_laminated_magnets(
            {
                "quantity": 10,
                "magnet_id": "MagnetVinilGlue04",
                "width_mm": 50,
                "height_mm": 50,
            }
        )


# ── Эталонный тест: ламинированные магниты rectangular (сверка с JS) ──

# Вход: 100шт 100×100мм MagnetVinil04 (0.4мм), mode=1, rectangular, без опций
LAMINATED_REF_PARAMS = {
    "quantity": 100,
    "magnet_id": "MagnetVinil04",
    "width_mm": 100,
    "height_mm": 100,
    "shape": "rectangular",
    "mode": 1,
}

# Выход JS-калькулятора (эталон):
LAMINATED_REF_EXPECTED = {
    "cost": 2860,
    "price": 5329.1,
    "time_hours": 1.25,
    "time_ready": 9.79,
    "weight_kg": 2.14,
}

LAMINATED_REF_MATERIALS = {
    "Laminat32G": {
        "name_substring": "Пленка для ламинации",
        "quantity": 9.306,
        "unit_hint": "m",
    },
    "RAFLACOAT": {
        "name_substring": "Самоклеящаяся бумага RAFLACOAT",
        "quantity": 11,
        "unit_hint": "sheet",
    },
    "MagnetVinil04": {
        "name_substring": "Магнитный винил",
        "quantity": 2.2,
        "unit_hint": "mm",
    },
}


@pytest.fixture(scope="module")
def laminated_ref_result(calc_laminated):
    return calc_laminated.execute(LAMINATED_REF_PARAMS)


def test_laminated_ref_cost(laminated_ref_result):
    """Себестоимость: JS=2860."""
    got = laminated_ref_result["cost"]
    exp = LAMINATED_REF_EXPECTED["cost"]
    assert _cmp(got, exp, 0.02), f"cost: got {got}, expected ~{exp}"


def test_laminated_ref_price(laminated_ref_result):
    """Цена с наценкой: JS=5329.1."""
    got = laminated_ref_result["price"]
    exp = LAMINATED_REF_EXPECTED["price"]
    assert _cmp(got, exp, 0.02), f"price: got {got}, expected ~{exp}"


def test_laminated_ref_time(laminated_ref_result):
    """Время изготовления: JS=1.25ч."""
    got = laminated_ref_result["time_hours"]
    exp = LAMINATED_REF_EXPECTED["time_hours"]
    assert _cmp(got, exp, 0.05), f"time_hours: got {got}, expected ~{exp}"


def test_laminated_ref_time_ready(laminated_ref_result):
    """Время готовности: JS=9.79ч."""
    got = laminated_ref_result["time_ready"]
    exp = LAMINATED_REF_EXPECTED["time_ready"]
    assert _cmp(got, exp, 0.05), f"time_ready: got {got}, expected ~{exp}"


def test_laminated_ref_weight(laminated_ref_result):
    """Вес тиража: JS=2.14кг."""
    got = laminated_ref_result["weight_kg"]
    exp = LAMINATED_REF_EXPECTED["weight_kg"]
    assert _cmp(got, exp, 0.10), f"weight_kg: got {got}, expected ~{exp}"


def test_laminated_ref_materials(laminated_ref_result):
    """Расход материалов: 3 позиции с заданными количествами."""
    materials = laminated_ref_result.get("materials", [])
    mat_by_code = {m["code"]: m for m in materials}

    for code, expected in LAMINATED_REF_MATERIALS.items():
        assert code in mat_by_code, f"Материал {code} не найден в results. Есть: {list(mat_by_code.keys())}"
        m = mat_by_code[code]
        assert expected["name_substring"].lower() in (m.get("name") or "").lower(), (
            f"{code}: name={m.get('name')!r} не содержит {expected['name_substring']!r}"
        )
        got_qty = float(m.get("quantity", 0))
        exp_qty = expected["quantity"]
        assert _cmp(got_qty, exp_qty, 0.05), (
            f"{code}: quantity={got_qty}, expected ~{exp_qty}"
        )
        assert "title" in m, f"{code}: поле title отсутствует"


def test_laminated_ref_shape_in_result(laminated_ref_result):
    """Результат содержит shape и shape_label."""
    assert laminated_ref_result["shape"] == SHAPE_RECTANGULAR
    assert laminated_ref_result["shape_label"] == "Прямоугольная"
    assert "difficulty" not in laminated_ref_result


def test_laminated_ref_summary(laminated_ref_result):
    """Сводный вывод всех значений для визуальной сверки."""
    r = laminated_ref_result
    e = LAMINATED_REF_EXPECTED
    lines = [
        "",
        f"  [magnet_laminated] 100шт 100×100мм MagnetVinil04 shape={r.get('shape')} mode=1",
        "  ---",
        f"  cost        {r['cost']}  (ожид. {e['cost']})  {'ok' if _cmp(r['cost'], e['cost'], 0.02) else 'FAIL'}",
        f"  price       {r['price']}  (ожид. {e['price']})  {'ok' if _cmp(r['price'], e['price'], 0.02) else 'FAIL'}",
        f"  time_hours  {r['time_hours']}  (ожид. {e['time_hours']})  {'ok' if _cmp(r['time_hours'], e['time_hours'], 0.05) else 'FAIL'}",
        f"  time_ready  {r['time_ready']}  (ожид. {e['time_ready']})  {'ok' if _cmp(r['time_ready'], e['time_ready'], 0.05) else 'FAIL'}",
        f"  weight_kg   {r['weight_kg']}  (ожид. {e['weight_kg']})  {'ok' if _cmp(r['weight_kg'], e['weight_kg'], 0.10) else 'FAIL'}",
    ]
    materials = r.get("materials", [])
    mat_by_code = {m["code"]: m for m in materials}
    for code, exp_m in LAMINATED_REF_MATERIALS.items():
        m = mat_by_code.get(code, {})
        got_q = m.get("quantity", "N/A")
        exp_q = exp_m["quantity"]
        ok = _cmp(float(got_q), exp_q, 0.05) if isinstance(got_q, (int, float)) else False
        lines.append(f"  {code:20s}  qty={got_q}  (ожид. {exp_q})  {'ok' if ok else 'FAIL'}")
    print("\n".join(lines))


# ── Тесты формы (shape) ──────────────────────────────────────────────

SHAPE_BASE_PARAMS = {
    "quantity": 100,
    "magnet_id": "MagnetVinil04",
    "width_mm": 80,
    "height_mm": 80,
    "mode": 1,
}


def test_shape_rectangular_default(calc_laminated):
    """Без shape → rectangular (самый дешёвый: сабельный резак, без полей)."""
    r = calc_laminated.execute({**SHAPE_BASE_PARAMS})
    assert r["shape"] == SHAPE_RECTANGULAR
    assert r["shape_label"] == "Прямоугольная"
    assert "difficulty" not in r
    assert r["price"] > 0


def test_shape_rectangular_rounded(calc_laminated):
    """rectangular_rounded дороже rectangular (добавляется скругление)."""
    r_rect = calc_laminated.execute({**SHAPE_BASE_PARAMS, "shape": "rectangular"})
    r_round = calc_laminated.execute({**SHAPE_BASE_PARAMS, "shape": "rectangular_rounded"})

    assert r_round["shape"] == SHAPE_RECTANGULAR_ROUNDED
    assert r_round["shape_label"] == "Прямоугольная со скруглением"
    assert r_round["price"] > r_rect["price"], "скругление должно увеличить цену"
    assert r_round["time_hours"] > r_rect["time_hours"], "скругление добавляет время"


def test_shape_standart(calc_laminated):
    """standart дороже rectangular (поля + вырубка вместо сабельного резака)."""
    r_rect = calc_laminated.execute({**SHAPE_BASE_PARAMS, "shape": "rectangular"})
    r_std = calc_laminated.execute({**SHAPE_BASE_PARAMS, "shape": "standart"})

    assert r_std["shape"] == SHAPE_STANDART
    assert r_std["shape_label"] == "Стандартная форма (из каталога)"
    assert "difficulty" not in r_std
    assert r_std["price"] > r_rect["price"], "standart должен быть дороже rectangular"


def test_shape_nonstandart(calc_laminated):
    """nonstandart — самый дорогой: изготовление формы + вырубка."""
    r_std = calc_laminated.execute({**SHAPE_BASE_PARAMS, "shape": "standart"})
    r_ns = calc_laminated.execute({**SHAPE_BASE_PARAMS, "shape": "nonstandart", "difficulty": 1.3})

    assert r_ns["shape"] == SHAPE_NONSTANDART
    assert r_ns["shape_label"] == "Нестандартная форма (изготовление)"
    assert r_ns["difficulty"] == 1.3
    assert r_ns["price"] > r_std["price"], "nonstandart с формой должен быть дороже standart"
    assert r_ns["time_ready"] > r_std["time_ready"], "изготовление формы увеличивает время готовности"


def test_shape_nonstandart_difficulty_increases_price(calc_laminated):
    """Более высокая сложность → дороже форма (размер достаточно большой, чтобы превысить MIN_COST_FORM)."""
    big = {**SHAPE_BASE_PARAMS, "width_mm": 300, "height_mm": 300}
    r_easy = calc_laminated.execute({**big, "shape": "nonstandart", "difficulty": 1.0})
    r_hard = calc_laminated.execute({**big, "shape": "nonstandart", "difficulty": 1.7})
    assert r_hard["price"] > r_easy["price"], "difficulty=1.7 должен быть дороже 1.0"


def test_tool_schema_has_shape_and_difficulty(calc_laminated):
    """tool_schema содержит shape и difficulty."""
    schema = calc_laminated.get_tool_schema()
    props = schema["parameters"]["properties"]
    assert "shape" in props
    assert set(props["shape"]["enum"]) == set(VALID_SHAPES)
    assert "difficulty" in props
    assert set(props["difficulty"]["enum"]) == {1.0, 1.3, 1.7}


# ── Эталонный тест: полимерные магниты (JS calcMagnetLamination + isEpoxy) ───

# Вход: 100шт 50×50мм MagnetVinil04, прямоугольная форма, полимерная заливка
POLYMER_REF_PARAMS = {
    "quantity": 100,
    "magnet_id": "MagnetVinil04",
    "width_mm": 50,
    "height_mm": 50,
    "shape": "rectangular",
    "is_epoxy": True,
    "mode": 1,
}

# Выход JS-калькулятора (эталон). Агрегаты допускают ~5% отклонения из-за округлений Python/JS.
POLYMER_REF_EXPECTED = {
    "cost": 6483,
    "price": 12078.45,
    "time_hours": 2.97,
    "time_ready": 45.14,
    "weight_kg": 1.17,
}

POLYMER_REF_MATERIALS = {
    "EpoxyPoly": {"quantity": 0.48},
    "RaflatacMW": {"quantity": 4},
    "MagnetVinil04": {"quantity": 0.88},
}


@pytest.fixture(scope="module")
def polymer_ref_result(calc_laminated):
    return calc_laminated.execute(POLYMER_REF_PARAMS)


def test_polymer_ref_cost(polymer_ref_result):
    got = polymer_ref_result["cost"]
    exp = POLYMER_REF_EXPECTED["cost"]
    assert _cmp(got, exp, 0.05), f"cost: got {got}, expected ~{exp}"


def test_polymer_ref_price(polymer_ref_result):
    got = polymer_ref_result["price"]
    exp = POLYMER_REF_EXPECTED["price"]
    assert _cmp(got, exp, 0.05), f"price: got {got}, expected ~{exp}"


def test_polymer_ref_time(polymer_ref_result):
    got = polymer_ref_result["time_hours"]
    exp = POLYMER_REF_EXPECTED["time_hours"]
    assert _cmp(got, exp, 0.06), f"time_hours: got {got}, expected ~{exp}"


def test_polymer_ref_time_ready(polymer_ref_result):
    got = polymer_ref_result["time_ready"]
    exp = POLYMER_REF_EXPECTED["time_ready"]
    assert _cmp(got, exp, 0.05), f"time_ready: got {got}, expected ~{exp}"


def test_polymer_ref_weight(polymer_ref_result):
    got = polymer_ref_result["weight_kg"]
    exp = POLYMER_REF_EXPECTED["weight_kg"]
    assert _cmp(got, exp, 0.05), f"weight_kg: got {got}, expected ~{exp}"


def test_polymer_ref_materials(polymer_ref_result):
    mat_by_code = {m["code"]: m for m in polymer_ref_result.get("materials", [])}
    for code, exp in POLYMER_REF_MATERIALS.items():
        assert code in mat_by_code, f"материал {code} отсутствует: {list(mat_by_code.keys())}"
        got_q = float(mat_by_code[code].get("quantity", 0))
        assert _cmp(got_q, exp["quantity"], 0.02), (
            f"{code}: quantity={got_q}, expected ~{exp['quantity']}"
        )


def test_polymer_ref_shape_and_labels(polymer_ref_result):
    assert polymer_ref_result["shape"] == "rectangular"
    assert polymer_ref_result["shape_label"] == "Прямоугольная"
    assert "difficulty" not in polymer_ref_result


def test_polymer_ref_summary(polymer_ref_result):
    r = polymer_ref_result
    e = POLYMER_REF_EXPECTED
    print("")
    print("  [magnet_laminated polymer] 100шт 50×50мм rectangular is_epoxy=True")
    print("  ---")
    print(f"  cost        {r['cost']}  (ожид. JS {e['cost']})")
    print(f"  price       {r['price']}  (ожид. JS {e['price']})")
    print(f"  time_hours  {r['time_hours']}  (ожид. JS {e['time_hours']})")
    print(f"  time_ready  {r['time_ready']}  (ожид. JS {e['time_ready']})")
    print(f"  weight_kg   {r['weight_kg']}  (ожид. JS {e['weight_kg']})")


# ── Полимерные магниты (is_epoxy=True) ───────────────────────────────

def test_laminated_epoxy_basic(calc_laminated):
    """is_epoxy=True увеличивает стоимость и добавляет EpoxyPoly в материалы."""
    base = {
        "quantity": 100,
        "magnet_id": "MagnetVinil04",
        "width_mm": 50,
        "height_mm": 50,
        "mode": 1,
    }
    r_plain = calc_laminated.execute({**base, "is_epoxy": False})
    r_epoxy = calc_laminated.execute({**base, "is_epoxy": True})

    assert r_epoxy["cost"] > r_plain["cost"], "с заливкой себестоимость должна быть выше"
    assert r_epoxy["price"] > r_plain["price"], "с заливкой цена должна быть выше"
    assert r_epoxy["time_hours"] > r_plain["time_hours"], "с заливкой время должно быть больше"

    epoxy_mat = [m for m in r_epoxy["materials"] if m.get("code") == "EpoxyPoly"]
    assert len(epoxy_mat) == 1, "в материалах должна быть смола EpoxyPoly"
    assert epoxy_mat[0]["quantity"] > 0


def test_laminated_epoxy_uses_raflatac(calc_laminated):
    """При is_epoxy=True материал печати — RaflatacMW, а не RAFLACOAT."""
    r = calc_laminated.execute({
        "quantity": 50,
        "magnet_id": "MagnetVinil04",
        "width_mm": 40,
        "height_mm": 40,
        "is_epoxy": True,
        "mode": 1,
    })
    mat_codes = [m.get("code") for m in r.get("materials", [])]
    assert "RaflatacMW" in mat_codes, f"Ожидался RaflatacMW в материалах, получено: {mat_codes}"
    assert "RAFLACOAT" not in mat_codes, "RAFLACOAT не должен быть при is_epoxy=True"


def test_laminated_epoxy_tool_schema_has_is_epoxy(calc_laminated):
    schema = calc_laminated.get_tool_schema()
    props = schema["parameters"]["properties"]
    assert "is_epoxy" in props
    assert props["is_epoxy"]["type"] == "boolean"
