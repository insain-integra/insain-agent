"""Контракт режимов производства (ProductionMode: 0=эконом, 1=стандарт, 2=экспресс).

Проверяет:
1. Хелперы mode в calculators/base.py (parse_mode, calc_time_prepare, apply_mode_defects, pick_time_ready).
2. Все зарегистрированные CALCULATORS на mode ∈ {0, 1, 2}:
   - time_hours(0) <= time_hours(1) <= time_hours(2);
   - time_ready(2) <= time_ready(1) <= time_ready(0) (кроме явных документированных исключений);
   - price(0) <= price(1) <= price(2) и строгое price(0) < price(1) < price(2) для собственного
     производства (с явным задокументированным списком исключений — подрядчики, timePrepare=0 и т. п.).
3. Статическую AST-проверку кода калькуляторов и common/process_tools.py:
   - запрет max(1, mode...) в расчётах (кроме документированной логистики milling.py → cost_ship);
   - запрет mode or 1 / params.get("mode") or 1 при чтении режима.
"""

from __future__ import annotations

import ast
import sys
from pathlib import Path
from typing import Any, Dict, List, Mapping, Set, Tuple

import pytest

_calc_service = Path(__file__).resolve().parent.parent
if _calc_service.name == "calc_service" and str(_calc_service) not in sys.path:
    sys.path.insert(0, str(_calc_service))

from calculators import CALCULATORS, get_calculator
from calculators.base import (
    ProductionMode,
    apply_mode_defects,
    calc_time_prepare,
    parse_mode,
    pick_time_ready,
)


# ── Репрезентативные входы для всех зарегистрированных калькуляторов ────

MODE_CONTRACT_CASES: Dict[str, Dict[str, Any]] = {
    "acrylic_prizes": {
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
    },
    "badge": {
        "quantity": 50,
        "width": 85,
        "height": 55,
        "material_id": "PVC3",
        "difficulty": 1.0,
        "is_print": True,
        "color": "4+0",
        "is_uv_print": False,
    },
    "button_pins": {"quantity": 100, "pin_id": "D25"},
    "calendar": {
        "quantity": 100,
        "calendar_type": "quarterly",
        "calendar_id": "QuarterlyMini",
        "block_id": "MiniOffset",
        "top_material_id": "PaperCoated115M",
        "top_color": "4+0",
        "bottom_material_id": "PaperCoated115M",
        "bottom_color": "4+0",
    },
    "frame": {
        "quantity": 2,
        "profile_id": "AluFrame2Plus",
        "segments": [[1000, 2], [1000, 2]],
    },
    "canvas": {
        "quantity": 2,
        "width": 400,
        "height": 300,
        "material_id": "CanvasDLCNM320",
        "printer_code": "HPLatex335",
        "is_frame": True,
        "frame_id": "CanvasFrame4520",
    },
    "cards": {"quantity": 100, "material_id": "White", "lamination": ""},
    "cut_guillotine": {
        "num_sheet": 50,
        "width": 90,
        "height": 50,
        "sheet_width": 320,
        "sheet_height": 450,
        "material_id": "PaperCoated300M",
    },
    "cut_plotter": {
        "quantity": 100,
        "width": 60,
        "height": 60,
        "material_id": "Avery500c",
        "plotter_code": "",
        "difficulty": 1.3,
    },
    "cut_roller": {
        "quantity": 20,
        "width": 210,
        "height": 297,
        "material_id": "PaperCoated115M",
    },
    "design": {"quantity": 1, "design_id": "DesignCard", "difficulty": 2},
    "embossing": {
        "quantity": 500,
        "cliche_width_mm": 50,
        "cliche_height_mm": 30,
        "embossing_type": "foil",
        "item_type": "diary",
        "is_cliche": True,
    },
    "flag": {
        "quantity": 100,
        "width_mm": 200,
        "height_mm": 99,
        "material_id": "PaperCoated115M",
        "color": "4+0",
    },
    "heat_press": {
        "quantity": 1,
        "width": 150,
        "height": 100,
        "transfer_type": "sublimation",
        "item_type": "tshirt",
        "silk_colors": 1,
    },
    "keychain": {
        "quantity": 50,
        "keychain_id": "KeychainAcrylic3939",
        "color": 1,
        "is_packing": True,
    },
    "lamination": {
        "quantity": 13,
        "width": 320,
        "height": 450,
        "material_id": "Laminat32G",
        "laminator_code": "FGKFM360",
        "double_side": True,
    },
    "lamination_wide": {"quantity": 2, "width": 1000, "height": 1000},
    "laser": {
        "quantity": 50,
        "width": 40,
        "height": 80,
        "material_id": "AcrylColor3",
        "is_cut_laser": {},
        "is_grave": 1,
        "is_grave_fill": [30, 40],
    },
    "magnet_acrylic": {
        "quantity": 100,
        "magnet_id": "MagnetAcrylic6565",
        "color": 1,
        "is_packing": True,
    },
    "magnet_laminated": {
        "quantity": 50,
        "width": 60,
        "height": 60,
        "magnet_id": "MagnetVinil04",
    },
    "metal_pins": {
        "quantity": 100,
        "stamps": [
            {
                "size": [25, 25, 1.2],
                "materialID": "brass",
                "processID": 1,
                "platingID": "nickel",
                "numEnamels": 0,
                "isEpoxy": "",
                "isMould": "",
            }
        ],
        "pack_id": "PolyBag",
    },
    "milling": {
        "quantity": 10,
        "width": 500,
        "height": 1000,
        "material_id": "PVC3",
        "material_mode": "isMaterial",
        "len_cut": 3.0,
    },
    "mug": {"quantity": 1, "mug_id": "MugStandartWhite", "is_packing": False},
    "notebook": {
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
    },
    "pad_print": {
        "quantity": 500,
        "color": 1,
        "size_item": "isSmallItems",
        "width_mm": 30,
        "height_mm": 20,
        "depth_mm": 5,
        "is_pantone": False,
        "is_packing": False,
        "material_mode": "isMaterial",
    },
    "pennant": {
        "quantity": 100,
        "width_mm": 148,
        "height_mm": 210,
        "material_id": "PaperCoated170M",
        "color": "4+0",
        "lamination_id": "Laminat32G",
    },
    "pockets": {
        "quantity": 2,
        "width": 100,
        "height": 80,
        "material_id": "PET05",
        "pocket_id": "NoSuchPocket",
    },
    "plaque": {
        "quantity": 2,
        "plaque_id": "Plaque2330",
        "material_id": "PVC3",
        "application": "isUVPrint",
    },
    "poly_sticker": {
        "quantity": 20,
        "width": 80,
        "height": 80,
        "material_id": "PaperCoated115M",
        "color": "4+0",
        "difficulty": 1,
    },
    "poly_sticker_pack": {
        "quantity": 20,
        "width": 80,
        "height": 80,
        "material_id": "PaperCoated115M",
        "num_stickers": 5,
        "sticker_size": 30,
        "sticker_difficulty": 1.0,
        "is_background": False,
        "print_method": "KMBizhubC220",
    },
    "presswall": {
        "quantity": 1,
        "presswall_id": "Joker30_20_eyelet",
        "material_id": "",
        "is_presswall": True,
        "is_rent": 0,
        "is_eyelet": [300, 300, 300, 300],
    },
    "print_inkjet": {
        "num_sheet": 10,
        "width": 210,
        "height": 297,
        "quality": 0,
        "color": "4+0",
        "material_id": "PaperCoated115M",
        "printer_code": "EPSONWF7610",
    },
    "print_laser": {
        "num_sheet": 50,
        "width": 320,
        "height": 450,
        "material_id": "PaperCoated300M",
        "color": "4+4",
        "printer_code": "",
    },
    "print_offset": {
        "num_sheet": 1000,
        "width": 210,
        "height": 297,
        "color": "4+0",
        "material_id": "PaperCoated115M",
    },
    "print_roll": {
        "quantity": 1,
        "width": 1189,
        "height": 841,
        "material_id": "ORAJET3640",
        "printer_code": "Technojet160ECO",
    },
    "print_sheet": {
        "quantity": 100,
        "width": 297,
        "height": 210,
        "material_id": "VHI80",
        "color": "4+0",
        "margins": [2, 2, 2, 2],
        "interval": 4,
    },
    "print_wide": {
        "quantity": 1,
        "width": 1000,
        "height": 1000,
        "material_id": "BannerFronlitCoat400",
        "printer_code": "Technojet160ECO",
    },
    "puzzle": {"quantity": 1, "puzzle_id": "Puzzle300420"},
    "rollup": {
        "quantity": 1,
        "rollup_id": "Rollup_econom_85",
        "material_id": "BannerFronlitCoat400",
    },
    "shild": {
        "quantity": 10,
        "width": 297,
        "height": 210,
        "material_id": "PVC3",
        "print_method": "uv",
        "is_packing": False,
    },
    "sticker": {
        "quantity": 100,
        "width": 50,
        "height": 50,
        "material_id": "RAFLACOAT",
        "size_item": 50,
    },
    "tablets": {
        "quantity": 5,
        "width": 300,
        "height": 200,
        "material_id": "PVC3",
        "is_cut_laser": {},
    },
    "uv_badge": {
        "quantity": 100,
        "width": 85,
        "height": 54,
        "material_id": "PVC3",
        "color": "4+0",
    },
    "uv_print": {
        "quantity": 50,
        "width": 100,
        "height": 150,
        "resolution": 0,
        "color": "4+0",
        "surface": "plain",
    },
}

# Явно задокументированные исключения для строгого неравенства price(0) < price(1) < price(2):
# - подрядчики с фиксированной ценой от тиража (cards, offset_promo / print_offset);
# - оборудование с timePrepare=0 в JSON (print_offset, cut_guillotine, cut_roller, lamination_wide);
# - составные расчёты с фиксированным режимом подрасчёта как в js_legacy (plaque: mode=1).
NON_STRICT_PRICE_EXCEPTIONS: Dict[str, str] = {
    "cards": "Подрядчик (calcCards.js): цена и time_hours фиксированы, mode меняет только time_ready.",
    "print_offset": "У OffsetPrint timePrepare=0 (а offset_promo — подрядчик): цена не зависит от mode.",
    "plaque": "В calcPlaque (JS стр. 640) пластина считается в mode=1; цена и срок фиксированы.",
    "cut_guillotine": "В cutter.json у гильотины timePrepare=0; mode меняет только time_ready.",
    "cut_roller": "В cutter.json у роликового резака timePrepare=0; mode меняет только time_ready.",
    "lamination_wide": "В laminator.json timePrepare=0.0: price(0) == price(1) < price(2) (рост брака в экспрессе).",
}

# Явно задокументированные исключения для time_ready(2) <= time_ready(1) <= time_ready(0):
TIME_READY_MODE_EXCEPTIONS: Dict[str, str] = {
    "acrylic_prizes": (
        "В calcAcrilycPrizes.js срок готовности операций берётся только при mode > 0, "
        "поэтому при mode=0 time_ready == time_hours (эталон test_acrylic_prizes.py)."
    ),
}


# ── 1. Тесты единых хелперов mode ──────────────────────────────────────

def test_parse_mode_preserves_zero():
    assert parse_mode(0) == ProductionMode.ECONOMY
    assert parse_mode("0") == ProductionMode.ECONOMY
    assert parse_mode(ProductionMode.ECONOMY) == ProductionMode.ECONOMY
    assert parse_mode(1) == ProductionMode.STANDARD
    assert parse_mode(2) == ProductionMode.EXPRESS
    assert parse_mode(None) == ProductionMode.STANDARD
    assert parse_mode("") == ProductionMode.STANDARD
    assert parse_mode("  ") == ProductionMode.STANDARD
    assert parse_mode(None, default=ProductionMode.ECONOMY) == ProductionMode.ECONOMY


def test_calc_time_prepare_standard_formula():
    assert calc_time_prepare(0.25, ProductionMode.ECONOMY) == pytest.approx(0.0)
    assert calc_time_prepare(0.25, ProductionMode.STANDARD) == pytest.approx(0.25)
    assert calc_time_prepare(0.25, ProductionMode.EXPRESS) == pytest.approx(0.50)
    assert calc_time_prepare(0.0, 2) == pytest.approx(0.0)


def test_apply_mode_defects_standard_formula():
    assert apply_mode_defects(0.05, ProductionMode.ECONOMY) == pytest.approx(0.05)
    assert apply_mode_defects(0.05, ProductionMode.STANDARD) == pytest.approx(0.05)
    assert apply_mode_defects(0.05, ProductionMode.EXPRESS) == pytest.approx(0.10)
    assert apply_mode_defects(0.0, 2) == pytest.approx(0.0)


def test_pick_time_ready_zero_based_and_clamped():
    times = [40.0, 16.0, 8.0]
    assert pick_time_ready(times, 0) == pytest.approx(40.0)
    assert pick_time_ready(times, 1) == pytest.approx(16.0)
    assert pick_time_ready(times, 2) == pytest.approx(8.0)
    assert pick_time_ready(times, -5) == pytest.approx(40.0)
    assert pick_time_ready(times, 5) == pytest.approx(8.0)
    assert pick_time_ready(None, 1, fallback=[24.0, 8.0, 1.0]) == pytest.approx(8.0)
    assert pick_time_ready([], 0, fallback=[]) == pytest.approx(0.0)


# ── 2. Покрытие и контракт всех CALCULATORS на mode ∈ {0, 1, 2} ────────

def test_all_registered_calculators_have_mode_case():
    """Каждый зарегистрированный калькулятор обязан иметь кейс в MODE_CONTRACT_CASES."""
    registered = set(CALCULATORS.keys())
    covered = set(MODE_CONTRACT_CASES.keys())
    missing = sorted(registered - covered)
    extra = sorted(covered - registered)
    assert not missing, f"Нет кейсов в MODE_CONTRACT_CASES для: {missing}"
    assert not extra, f"Лишние ключи в MODE_CONTRACT_CASES: {extra}"


@pytest.mark.parametrize("slug", sorted(CALCULATORS.keys()))
def test_calculator_mode_contract(slug: str):
    """Контракт mode ∈ {0, 1, 2} для каждого калькулятора из CALCULATORS."""
    calc = get_calculator(slug)
    params = MODE_CONTRACT_CASES[slug]

    results = {m: calc.execute({**params, "mode": m}) for m in (0, 1, 2)}
    p0, p1, p2 = (float(results[m]["price"]) for m in (0, 1, 2))
    h0, h1, h2 = (float(results[m]["time_hours"]) for m in (0, 1, 2))
    r0, r1, r2 = (float(results[m]["time_ready"]) for m in (0, 1, 2))

    # Неубывание времени работы: time_hours(0) <= time_hours(1) <= time_hours(2)
    assert h0 <= h1 + 1e-9, f"{slug}: time_hours(0)={h0} > time_hours(1)={h1}"
    assert h1 <= h2 + 1e-9, f"{slug}: time_hours(1)={h1} > time_hours(2)={h2}"

    # Невозрастание срока готовности: time_ready(2) <= time_ready(1) <= time_ready(0)
    if slug in TIME_READY_MODE_EXCEPTIONS:
        # Для acrylic_prizes mode=1 vs mode=2 всё равно монотонно убывает
        assert r2 <= r1 + 1e-9, f"{slug}: time_ready(2)={r2} > time_ready(1)={r1}"
    else:
        assert r2 <= r1 + 1e-9, f"{slug}: time_ready(2)={r2} > time_ready(1)={r1}"
        assert r1 <= r0 + 1e-9, f"{slug}: time_ready(1)={r1} > time_ready(0)={r0}"

    # Неубывание цены: price(0) <= price(1) <= price(2)
    assert p0 <= p1 + 1e-9, f"{slug}: price(0)={p0} > price(1)={p1}"
    assert p1 <= p2 + 1e-9, f"{slug}: price(1)={p1} > price(2)={p2}"

    # Строгое price(0) < price(1) < price(2) для собственного производства
    if slug not in NON_STRICT_PRICE_EXCEPTIONS:
        assert p0 < p1, f"{slug}: ожидалось строгое price(0)={p0} < price(1)={p1}"
        assert p1 < p2, f"{slug}: ожидалось строгое price(1)={p1} < price(2)={p2}"
    elif slug == "lamination_wide":
        # timePrepare=0, но брак в экспрессе удваивается
        assert p0 == pytest.approx(p1)
        assert p1 < p2


def test_contractor_and_flat_mode_branches():
    """Проверка подрядных и плоских веток: offset_promo, button_pins > 2000 (Амалит), rollup без полотна."""
    # 1. offset_promo — подрядчик, цена плоская, срок убывает
    promo_calc = get_calculator("print_offset")
    promo = [
        promo_calc.execute({"num_sheet": 1000, "material_id": "OffsetPromoА51000", "mode": m})
        for m in (0, 1, 2)
    ]
    assert promo[0]["price"] == promo[1]["price"] == promo[2]["price"]
    assert promo[2]["time_ready"] < promo[1]["time_ready"] < promo[0]["time_ready"]

    # 2. button_pins > 2000 — подрядчик Амалит, цена и срок фиксированы
    pins_calc = get_calculator("button_pins")
    amalit = [
        pins_calc.execute({"quantity": 3000, "pin_id": "D25", "mode": m})
        for m in (0, 1, 2)
    ]
    assert amalit[0]["price"] == amalit[1]["price"] == amalit[2]["price"]
    assert amalit[0]["time_ready"] == amalit[1]["time_ready"] == amalit[2]["time_ready"]

    # 3. rollup без полотна — только стенд + доставка, цена плоская, срок убывает
    rollup_calc = get_calculator("rollup")
    stand_only = [
        rollup_calc.execute({"quantity": 1, "rollup_id": "Rollup_econom_85", "material_id": "", "mode": m})
        for m in (0, 1, 2)
    ]
    assert stand_only[0]["price"] == stand_only[1]["price"] == stand_only[2]["price"]
    assert stand_only[2]["time_ready"] < stand_only[1]["time_ready"] < stand_only[0]["time_ready"]


# ── 3. Статические AST-проверки антипаттернов mode ─────────────────────

# Допустимые места с max(1, mode...) — только логистика, не time_prepare:
ALLOWED_MAX_ONE_MODE: Set[Tuple[str, str]] = {
    ("milling.py", "cost_ship"),
}


def _expr_references_mode(node: ast.AST) -> bool:
    """True, если AST-узел содержит переменную/атрибут/ключ, связанный с mode."""
    for sub in ast.walk(node):
        if isinstance(sub, ast.Name) and "mode" in sub.id.lower():
            return True
        if isinstance(sub, ast.Constant) and isinstance(sub.value, str) and sub.value == "mode":
            return True
    return False


def _is_const_one(node: ast.AST) -> bool:
    return isinstance(node, ast.Constant) and type(node.value) is int and node.value == 1


def _is_standard_mode_const(node: ast.AST) -> bool:
    if _is_const_one(node):
        return True
    if isinstance(node, ast.Attribute) and node.attr == "STANDARD":
        return True
    return False


def _find_max_one_mode_violations(
    tree: ast.AST,
    filename: str,
    allowed: Set[Tuple[str, str]] = ALLOWED_MAX_ONE_MODE,
) -> List[str]:
    """Найти все вызовы max(1, mode...) вне явно разрешённой логистики."""
    violations: List[str] = []

    def _visit(node: ast.AST, target_name: str = "") -> None:
        cur_target = target_name
        if isinstance(node, ast.Assign):
            names = [t.id for t in node.targets if isinstance(t, ast.Name)]
            cur_target = names[0] if names else target_name
        elif isinstance(node, ast.AugAssign) and isinstance(node.target, ast.Name):
            cur_target = node.target.id
        elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
            cur_target = node.target.id

        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "max":
            has_one = any(_is_const_one(arg) for arg in node.args)
            has_mode = any(_expr_references_mode(arg) for arg in node.args)
            if has_one and has_mode and (filename, cur_target) not in allowed:
                violations.append(
                    f"{filename}:{getattr(node, 'lineno', '?')}: запрещённый max(1, mode...) "
                    f"(цель={cur_target or '<выражение>'})"
                )

        for child in ast.iter_child_nodes(node):
            _visit(child, cur_target)

    _visit(tree)
    return violations


def _find_mode_or_one_violations(tree: ast.AST, filename: str) -> List[str]:
    """Найти антипаттерн `mode or 1` / `params.get('mode') or 1` (съедает mode=0)."""
    violations: List[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.BoolOp) and isinstance(node.op, ast.Or):
            has_mode = any(_expr_references_mode(v) for v in node.values)
            has_one = any(_is_standard_mode_const(v) for v in node.values)
            if has_mode and has_one:
                violations.append(
                    f"{filename}:{getattr(node, 'lineno', '?')}: запрещённый `mode or 1` "
                    f"(режим 0 превращается в 1; используйте parse_mode)"
                )
    return violations


def _source_files_to_check() -> List[Path]:
    calcs = sorted((_calc_service / "calculators").glob("*.py"))
    process_tools = _calc_service / "common" / "process_tools.py"
    return calcs + ([process_tools] if process_tools.is_file() else [])


def test_no_max_one_mode_in_calculators_ast():
    """Статическая проверка: в калькуляторах и process_tools нет max(1, mode...) на time_prepare."""
    violations: List[str] = []
    for path in _source_files_to_check():
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=path.name)
        violations.extend(_find_max_one_mode_violations(tree, path.name))
    assert not violations, "\n".join(violations)


def test_no_mode_or_one_in_calculators_ast():
    """Статическая проверка: в калькуляторах и process_tools нет `mode or 1`."""
    violations: List[str] = []
    for path in _source_files_to_check():
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=path.name)
        violations.extend(_find_mode_or_one_violations(tree, path.name))
    assert not violations, "\n".join(violations)


def test_ast_checkers_catch_regressions():
    """Самопроверка: AST-чекеры действительно ловят max(1, mode.value) и mode or 1."""
    bad_max_prepare = ast.parse("time_prepare = (tool.time_prepare or 0.1) * max(1, mode.value)")
    assert _find_max_one_mode_violations(bad_max_prepare, "demo.py")

    bad_max_call = ast.parse("cost_cliche = _calc_cliche(size, max(1, mode.value))")
    assert _find_max_one_mode_violations(bad_max_call, "demo.py")

    allowed_milling_ship = ast.parse("cost_ship *= max(1, mode.value)")
    assert not _find_max_one_mode_violations(allowed_milling_ship, "milling.py")

    bad_or_1 = ast.parse("mode = int(params.get('mode') or 1)")
    assert _find_mode_or_one_violations(bad_or_1, "demo.py")

    bad_or_std = ast.parse("m = mode or ProductionMode.STANDARD")
    assert _find_mode_or_one_violations(bad_or_std, "demo.py")
