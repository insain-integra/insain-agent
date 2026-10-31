#!/usr/bin/env python3
"""
Пропуски порта старого JS (js_legacy/calc/*.js) в calc_service.

Для каждой функции insaincalc.calcX: опции (options.has/get('…')), вызовы
insaincalc.calc…( и то, чего нет в Python-модуле порта.

  python scripts/js_port_gaps.py              — отчёт по всем функциям
  python scripts/js_port_gaps.py calcPlaque   — функция и вся цепочка её вызовов
  python scripts/js_port_gaps.py --list       — пропуски строками файла допустимых
  python scripts/js_port_gaps.py --check [--allowed PATH]
                                              — сверка с scripts/js_port_gaps_allowed.txt

Опция перенесена, если её имя есть в модуле как есть или в snake_case
(isCutManualMetal → is_cut_manual_metal / cut_manual_metal). Вызов перенесён,
если модуль импортирует Python-порт вызываемой функции (или это тот же модуль).
JS разбирается как текст: Node не нужен.
"""

from __future__ import annotations

import argparse
import ast
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Set

ROOT = Path(__file__).resolve().parent.parent
JS_DIR = ROOT / "js_legacy" / "calc"
PY_ROOT = ROOT / "calc_service"
DEFAULT_ALLOWED = Path(__file__).resolve().parent / "js_port_gaps_allowed.txt"

# calcX → Python-порт: «пакет.модуль» или «пакет.модуль:функция».
# С функцией вызов считается перенесённым, только если импортировано это имя.
# Функции без записи — пропуск «нет порта».
PORTS: Dict[str, str] = {
    "calcAcrilycPrizes": "calculators.acrylic_prizes",
    "calcBadge": "calculators.badge",
    "calcCalendarQuarterly": "calculators.calendar_calc",
    "calcCalendarFlip": "calculators.calendar_calc",
    "calcCalendarTableFlip": "calculators.calendar_calc",
    "calcCanvas": "calculators.canvas",
    "calcSetCanvasFrame": "common.process_tools:calc_set_canvas_frame",
    "calcPlasticCards": "calculators.cards",
    "calcCutGuillotine": "calculators.cut_guillotine",
    "calcCutPlotter": "calculators.cut_plotter",
    "calcCutRoller": "calculators.cut_roller",
    "calcDesign": "calculators.design",
    "calcEmbossing": "calculators.embossing",
    "calcCliсhe": "calculators.embossing",
    "calcFlagPaper": "calculators.flag",
    "calcHeatPress": "calculators.heat_press",
    "calcAcrylicKeychain": "calculators.keychain",
    "calcLamination": "calculators.lamination",
    "calcLaminationRoll": "common.process_tools:calc_lamination_roll",
    "calcLaser": "calculators.laser",
    "calcLayoutOnSheet": "common.layout:layout_on_sheet",
    "calcLayoutOnRoll": "common.layout:layout_on_roll",
    "calcMagnetLamination": "calculators.magnets",
    "calcAcrylicMagnets": "calculators.magnets",
    "calcMetalPins": "calculators.metal_pins",
    "calcMilling": "calculators.milling",
    "calcMug": "calculators.mug",
    "calcNotebook": "calculators.notebook",
    "calcPadPrint": "calculators.pad_print",
    "calcPennantPaper": "calculators.pennant",
    "calcPolySticker": "calculators.poly_sticker",
    "calcPolyStickerPack": "calculators.poly_sticker_pack",
    "calcPresswall": "calculators.presswall",
    "calcPrintInkJet": "calculators.print_inkjet",
    "calcPrintLaser": "calculators.print_laser",
    "calcPrintOffset": "calculators.print_offset",
    "calcPrintRoll": "calculators.print_roll",
    "calcPrintSheet": "calculators.print_sheet",
    "calcPrintWide": "calculators.print_wide",
    "calcPuzzle": "calculators.puzzle",
    "calcRollup": "calculators.rollup",
    "calcShildSublimaton": "calculators.shild",
    "calcSticker": "calculators.sticker",
    "calcTablets": "calculators.tablets",
    "calcPlaque": "calculators.plaque",
    "calcUVBadge": "calculators.uv_badge",
    "calcUVPrint": "calculators.uv_print",
    "calcDateReady": "common.holidays:add_working_hours",
    "calcWeight": "common.helpers:calc_weight",
    "calcPunching": "common.process_tools:calc_punching",
    "calcRounding": "common.process_tools:calc_rounding",
    "calcCrease": "common.process_tools:calc_crease",
    "calcBinding": "common.process_tools:calc_binding",
    "calcSetStaples": "common.process_tools:calc_set_staples",
    "calcEyelet": "common.process_tools:calc_eyelet",
    "calcEyeletSheet": "common.process_tools:calc_eyelet_sheet",
    "calcGluingBanner": "common.process_tools:calc_gluing_banner",
    "calcCuttingEdge": "common.process_tools:calc_cutting_edge",
    "calcSetCursor": "common.process_tools:calc_set_cursor",
    "calcSetSticker": "common.process_tools:calc_set_sticker",
    "calcSetRigel": "common.process_tools:calc_set_rigel",
    "calcEpoxy": "common.process_tools:calc_epoxy",
    "calcAttachment": "common.process_tools:calc_attachment",
    "calcPocket": "common.process_tools:calc_pocket",
    "calcPacking": "common.process_tools:calc_packing",
    "calcManualRoll": "common.process_tools:calc_manual_roll",
    "calcSilkPrint": "common.process_tools:calc_silk_print",
    "calcButtonPins": "common.process_tools:calc_button_pins",
    "calcShipment": "common.process_tools:calc_shipment",
    "calcCutProfile": "common.process_tools:calc_cut_profile",
    "calcSewingCovers": "common.process_tools:calc_sewing_covers",
    "calcCutSaber": "common.process_tools:calc_cut_saber",
    "calcManualPress": "common.process_tools:calc_manual_press",
    "calcPress": "common.process_tools:calc_press",
    "calcForm": "common.process_tools:calc_form",
    "calcSetShaft": "common.process_tools:calc_set_shaft",
    "calcSetRope": "common.process_tools:calc_set_rope",
    "calcSetProfile": "common.process_tools:calc_set_profile",
    "calcSetInsert": "common.process_tools:calc_set_insert",
    "calcUVGluing": "common.process_tools:calc_uv_gluing",
}

DEF_RE = re.compile(r"insaincalc\.(calc\w+)\s*=\s*function\b")
CALL_RE = re.compile(r"insaincalc\.(calc\w+)\s*\(")
OPTION_RE = re.compile(r"\boptions\.(?:has|get)\(\s*(['\"`])([^'\"`]+?)\1\s*\)")
NO_PORT = "нет порта"


@dataclass
class JsFunc:
    name: str
    file: str
    options: List[str] = field(default_factory=list)
    calls: List[str] = field(default_factory=list)


@dataclass
class PyModule:
    text: str
    imports: Set[str]  # «модуль» и «модуль:имя»


def strip_js_comments(src: str) -> str:
    """Убирает // и /* */ комментарии, не трогая строки."""
    out: List[str] = []
    i, n = 0, len(src)
    quote: Optional[str] = None
    while i < n:
        c = src[i]
        if quote:
            out.append(c)
            if c == "\\" and i + 1 < n:
                out.append(src[i + 1])
                i += 2
                continue
            if c == quote:
                quote = None
            i += 1
            continue
        if c in "'\"`":
            quote = c
            out.append(c)
            i += 1
            continue
        if src.startswith("//", i):
            j = src.find("\n", i)
            i = n if j < 0 else j
            continue
        if src.startswith("/*", i):
            j = src.find("*/", i + 2)
            i = n if j < 0 else j + 2
            out.append(" ")
            continue
        out.append(c)
        i += 1
    return "".join(out)


def _unique(items: List[str]) -> List[str]:
    return list(dict.fromkeys(items))


def parse_js(js_dir: Path = JS_DIR) -> Dict[str, JsFunc]:
    funcs: Dict[str, JsFunc] = {}
    for path in sorted(js_dir.glob("*.js")):
        src = strip_js_comments(path.read_text(encoding="utf-8", errors="replace"))
        defs = list(DEF_RE.finditer(src))
        for k, m in enumerate(defs):
            end = defs[k + 1].start() if k + 1 < len(defs) else len(src)
            body = src[m.end():end]
            funcs[m.group(1)] = JsFunc(
                name=m.group(1),
                file=path.name,
                options=_unique([o.group(2) for o in OPTION_RE.finditer(body)]),
                calls=_unique([c.group(1) for c in CALL_RE.finditer(body)]),
            )
    return funcs


def module_of(port: str) -> str:
    return port.split(":", 1)[0]


def module_path(module: str) -> Path:
    return PY_ROOT.joinpath(*module.split(".")).with_suffix(".py")


def load_py_module(module: str) -> PyModule:
    text = module_path(module).read_text(encoding="utf-8")
    package = module.rsplit(".", 1)[0]
    imports: Set[str] = set()
    for node in ast.walk(ast.parse(text)):
        if isinstance(node, ast.Import):
            imports.update(a.name for a in node.names)
        elif isinstance(node, ast.ImportFrom):
            base = node.module or ""
            if node.level:
                base = f"{package}.{base}" if base else package
            imports.add(base)
            for a in node.names:
                imports.add(f"{base}:{a.name}")
                imports.add(f"{base}.{a.name}")
    return PyModule(text=text, imports=imports)


def snake_variants(name: str) -> List[str]:
    snake = re.sub(r"(?<=[a-z0-9])(?=[A-Z])|(?<=[A-Z])(?=[A-Z][a-z])", "_", name).lower()
    variants = [name, snake]
    if snake.startswith("is_") and len(snake) > 3:
        variants.append(snake[3:])
    return _unique(variants)


def has_word(text: str, word: str) -> bool:
    return re.search(rf"(?<![A-Za-z0-9_]){re.escape(word)}(?![A-Za-z0-9_])", text) is not None


def call_ported(own_module: str, py: PyModule, callee: str) -> bool:
    port = PORTS.get(callee)
    if port is None:
        return False
    if module_of(port) == own_module:
        return True
    return port in py.imports


def gaps_of(func: JsFunc, cache: Dict[str, PyModule]) -> List[str]:
    """Пропуски функции в формате строк файла допустимых, без имени функции."""
    port = PORTS.get(func.name)
    if port is None:
        return ["module"]
    module = module_of(port)
    if module not in cache:
        cache[module] = load_py_module(module)
    py = cache[module]
    gaps = [
        f"option {o}" for o in func.options
        if not any(has_word(py.text, v) for v in snake_variants(o))
    ]
    gaps += [f"call {c}" for c in func.calls if not call_ported(module, py, c)]
    return gaps


def chain(funcs: Dict[str, JsFunc], start: str) -> List[str]:
    order: List[str] = []
    stack = [start]
    while stack:
        name = stack.pop()
        if name in order or name not in funcs:
            continue
        order.append(name)
        stack.extend(reversed(funcs[name].calls))
    return order


def report_block(func: JsFunc, gaps: List[str]) -> str:
    port = PORTS.get(func.name)
    target = module_path(module_of(port)).relative_to(ROOT).as_posix() if port else NO_PORT
    return "\n".join([
        f"{func.name} -> {target}",
        f"options: {', '.join(func.options)}",
        f"calls: {', '.join(func.calls)}",
        f"нет в Python: {', '.join(gaps)}",
    ])


def all_gap_lines(funcs: Dict[str, JsFunc]) -> List[str]:
    cache: Dict[str, PyModule] = {}
    return [f"{name} {g}" for name, f in funcs.items() for g in gaps_of(f, cache)]


def read_allowed(path: Path) -> List[str]:
    return [s.strip() for s in path.read_text(encoding="utf-8").splitlines() if s.strip()]


def check(funcs: Dict[str, JsFunc], allowed_path: Path) -> int:
    actual = all_gap_lines(funcs)
    allowed = read_allowed(allowed_path)
    allowed_set, actual_set = set(allowed), set(actual)
    problems = [f"новый пропуск: {g}" for g in actual if g not in allowed_set]
    problems += [f"пропуск устранён, удалите строку: {g}" for g in allowed if g not in actual_set]
    if problems:
        print("\n".join(problems))
        return 1
    print("ok")
    return 0


def main(argv: Optional[List[str]] = None) -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description="Пропуски порта js_legacy/calc в calc_service")
    parser.add_argument("func", nargs="?", help="имя JS-функции, например calcPlaque")
    parser.add_argument("--check", action="store_true", help="сверить с файлом допустимых пропусков")
    parser.add_argument("--list", action="store_true", help="вывести пропуски строками файла допустимых")
    parser.add_argument("--allowed", type=Path, default=DEFAULT_ALLOWED, help="файл допустимых пропусков")
    args = parser.parse_args(argv)

    funcs = parse_js()
    if args.check:
        return check(funcs, args.allowed)
    if args.list:
        print("\n".join(all_gap_lines(funcs)))
        return 0
    if args.func and args.func not in funcs:
        print(f"Функция {args.func} не найдена в {JS_DIR.relative_to(ROOT).as_posix()}")
        return 2
    names = chain(funcs, args.func) if args.func else list(funcs)
    cache: Dict[str, PyModule] = {}
    print("\n\n".join(report_block(funcs[n], gaps_of(funcs[n], cache)) for n in names))
    return 0


if __name__ == "__main__":
    sys.exit(main())
