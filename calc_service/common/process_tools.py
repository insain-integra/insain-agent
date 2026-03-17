"""
Вспомогательные функции постпечатной обработки.

Мигрировано из js_legacy/calc/calcProcessTools.js.
Используются калькуляторами как строительные блоки для расчёта
стоимости операций: пробивка, скругление, биговка, люверсовка,
переплёт, упаковка, доставка, шелкография и т.д.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple

import json5

from common.helpers import find_in_table
from common.layout import layout_on_roll, layout_on_sheet
from common.markups import (
    BASE_TIME_READY,
    COST_OPERATOR,
    MARGIN_MATERIAL,
    MARGIN_OPERATION,
    get_margin,
)

# Ленивый импорт equipment и materials — чтобы не было циклических импортов
# при загрузке модуля. Реальные каталоги берутся через _tools() / _get_material().

_TOOLS_JSON = Path(__file__).parent.parent / "data" / "equipment" / "tools.json"
_MATERIALS_DIR = Path(__file__).parent.parent / "data" / "materials"

# ── Кэш сырых данных (загружается один раз) ──────────────────────────

_raw_tools_cache: Dict[str, Any] | None = None
_raw_materials_cache: Dict[str, Dict[str, Dict[str, Any]]] | None = None


def _raw_tools() -> Dict[str, Any]:
    global _raw_tools_cache
    if _raw_tools_cache is None:
        with open(_TOOLS_JSON, "r", encoding="utf-8") as f:
            _raw_tools_cache = json5.load(f)
    return _raw_tools_cache


def _raw_materials() -> Dict[str, Dict[str, Dict[str, Any]]]:
    """Все материалы из JSON с развёрнутым Default, индекс: {category: {code: {...}}}."""
    global _raw_materials_cache
    if _raw_materials_cache is not None:
        return _raw_materials_cache
    result: Dict[str, Dict[str, Dict[str, Any]]] = {}
    for path in sorted(_MATERIALS_DIR.glob("*.json")):
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json5.load(f)
            category = path.stem
            flat: Dict[str, Dict[str, Any]] = {}
            for group_id, group_data in data.items():
                if not isinstance(group_data, dict):
                    continue
                default = group_data.get("Default") or {}
                for code, raw in group_data.items():
                    if code == "Default" or not isinstance(raw, dict):
                        continue
                    merged = dict(default)
                    merged.update(raw)
                    merged["_group"] = group_id
                    flat[code] = merged
            result[category] = flat
        except Exception:
            continue
    _raw_materials_cache = result
    return result


# ── Доступ к данным ───────────────────────────────────────────────────

def _tools_catalog():
    from equipment import tools
    return tools


def _cutter_catalog():
    from equipment import cutter
    return cutter


def _get_tool(code: str):
    """Получить EquipmentSpec из каталога tools."""
    return _tools_catalog().get(code)


def _get_raw_tool(code: str) -> Dict[str, Any]:
    """Сырые данные инструмента для нестандартных полей."""
    raw = _raw_tools().get(code)
    if raw is None:
        raise KeyError(f"Инструмент не найден в tools.json: {code!r}")
    return raw


def _get_raw_material(category: str, code: str) -> Dict[str, Any]:
    """Сырые данные материала с развёрнутым Default."""
    cat = _raw_materials().get(category, {})
    raw = cat.get(code)
    if raw is None:
        raise KeyError(f"Материал {code!r} не найден в категории {category!r}")
    return raw


def _get_material(category: str, code: str):
    from materials import get_material
    return get_material(category, code)


def _find_material_across(categories: Sequence[str], code: str):
    """Найти MaterialSpec по коду в нескольких категориях."""
    from materials import get_material
    for cat in categories:
        try:
            return get_material(cat, code)
        except KeyError:
            continue
    raise ValueError(f"Параметры материала не найдены: {code!r}")


# ── Результат операции ────────────────────────────────────────────────

@dataclass
class ProcessResult:
    """Результат вспомогательной операции."""
    cost: float = 0.0
    price: float = 0.0
    time_hours: float = 0.0
    time_ready: float = 0.0
    weight_kg: float = 0.0
    materials: List[Dict[str, Any]] = field(default_factory=list)

    def merge(self, other: ProcessResult) -> ProcessResult:
        """Объединить результаты двух операций (суммирование)."""
        return ProcessResult(
            cost=self.cost + other.cost,
            price=self.price + other.price,
            time_hours=self.time_hours + other.time_hours,
            time_ready=self.time_ready + other.time_ready,
            weight_kg=self.weight_kg + other.weight_kg,
            materials=self.materials + other.materials,
        )


# ══════════════════════════════════════════════════════════════════════
#  ПОСТПЕЧАТНАЯ ОБРАБОТКА
# ══════════════════════════════════════════════════════════════════════

def calc_punching(n: int, material_id: str = "", mode: int = 1) -> ProcessResult:
    """
    Пробивка отверстий в листовой продукции.

    :param n: кол-во изделий
    :param material_id: код материала (для совместимости, не влияет на расчёт)
    :param mode: режим (0=эконом, 1=стандарт, 2=экспресс)
    """
    tool = _get_tool("Warrior")
    num_punches = n
    time_prepare = tool.time_prepare * mode
    time_process = num_punches / tool.process_per_hour + time_prepare
    cost_process = tool.depreciation_per_hour * time_process + num_punches * tool.cost_process
    cost_operator = time_process * tool.operator_cost_per_hour
    cost = cost_process + cost_operator
    margin_manual = get_margin("marginProcessManual")
    price = cost * (1 + MARGIN_OPERATION + margin_manual)
    time_hours = math.ceil(time_process * 100) / 100
    return ProcessResult(cost=cost, price=price, time_hours=time_hours)


def calc_rounding(n: int, material_id: str = "", mode: int = 1) -> ProcessResult:
    """
    Скругление углов листовой продукции.

    :param n: кол-во изделий
    :param material_id: код материала (для совместимости)
    :param mode: режим производства
    """
    tool = _get_tool("WarriorAD1")
    num_sheet_80 = n
    num_stack = math.ceil(num_sheet_80 / tool.max_sheet) if tool.max_sheet > 0 else n
    num_rounding = 4 * num_stack
    time_prepare = tool.time_prepare * mode
    time_process = num_rounding / tool.process_per_hour + time_prepare
    cost_process = tool.depreciation_per_hour * time_process + num_rounding * tool.cost_process
    cost_operator = time_process * tool.operator_cost_per_hour
    cost = cost_process + cost_operator
    margin_manual = get_margin("marginProcessManual")
    price = cost * (1 + MARGIN_OPERATION + margin_manual)
    time_hours = math.ceil(time_process * 100) / 100
    return ProcessResult(cost=cost, price=price, time_hours=time_hours)


def calc_crease(
    n: int,
    crease: int,
    size: Sequence[float],
    material_id: str = "",
    mode: int = 1,
) -> ProcessResult:
    """
    Биговка / перфорация листовой продукции.

    :param n: кол-во изделий
    :param crease: кол-во бигов на одном изделии
    :param size: размер изделия [ширина, высота], мм
    :param material_id: код материала (для совместимости)
    :param mode: режим производства
    """
    tool = _get_tool("CyklosGPM315")
    num_crease = n * crease
    tool_max_size = tool.max_size or [315, 0]
    layout = layout_on_roll(1, list(size), tool_max_size, 0)
    if layout["num"] == 0:
        raise ValueError("Размер изделия больше допустимого для биговки")
    time_prepare = tool.time_prepare * mode
    time_process = (
        num_crease / tool.process_per_hour
        + time_prepare
        + 0.5 * time_prepare * (crease - 1)
    )
    cost_process = tool.depreciation_per_hour * time_process + num_crease * tool.cost_process
    cost_operator = time_process * tool.operator_cost_per_hour
    cost = cost_process + cost_operator
    margin_manual = get_margin("marginProcessManual")
    price = cost * (1 + MARGIN_OPERATION + margin_manual)
    time_hours = math.ceil(time_process * 100) / 100
    return ProcessResult(cost=cost, price=price, time_hours=time_hours)


def calc_cutting_edge(
    n: int,
    size: Sequence[float],
    edge: Sequence[float],
    mode: int = 1,
) -> ProcessResult:
    """
    Подрезка края материала.

    :param n: кол-во изделий
    :param size: размер изделия [ширина, высота], мм
    :param edge: [top, right, bottom, left] — множитель подрезки по стороне (0 = не резать)
    :param mode: режим производства
    """
    tool = _get_tool("CuttingKnife")
    sides = [size[0], size[1], size[0], size[1]]
    sum_len = 0.0
    for i in range(4):
        if edge[i] > 0:
            if sides[i] < 1:
                sum_len += 1.0
            else:
                sum_len += sides[i] * edge[i]
    if sum_len <= 0:
        return ProcessResult()
    sum_len *= n / 1000
    time_prepare = tool.time_prepare * mode
    time_process = sum_len / tool.process_per_hour + time_prepare
    cost_process = tool.depreciation_per_hour * time_process + sum_len * tool.cost_process
    cost_operator = time_process * tool.operator_cost_per_hour
    cost = cost_process + cost_operator
    margin_manual = get_margin("marginProcessManual")
    price = cost * (1 + MARGIN_OPERATION + margin_manual)
    time_hours = math.ceil(time_process * 100) / 100
    return ProcessResult(cost=cost, price=price, time_hours=time_hours)


def calc_manual_press(n: int, material_id: str = "", mode: int = 1) -> ProcessResult:
    """
    Ручная вырубка на прессе.

    :param n: кол-во изделий
    :param material_id: код материала (для совместимости)
    :param mode: режим производства
    """
    tool = _get_tool("PressManual")
    time_prepare = tool.time_prepare * mode
    time_process = n / tool.process_per_hour + time_prepare
    cost_process = tool.depreciation_per_hour * time_process + n * tool.cost_process
    cost_operator = time_process * tool.operator_cost_per_hour
    cost = cost_process + cost_operator
    margin_manual = get_margin("marginProcessManual")
    price = cost * (1 + MARGIN_OPERATION + margin_manual)
    time_hours = math.ceil(time_process * 100) / 100
    return ProcessResult(cost=cost, price=price, time_hours=time_hours)


def calc_press(n: int, material_id: str = "", mode: int = 1) -> ProcessResult:
    """
    Вырубка на прессе.

    :param n: кол-во изделий
    :param material_id: код материала (для совместимости)
    :param mode: режим производства
    """
    tool = _get_tool("Press")
    time_prepare = tool.time_prepare * mode
    time_process = n / tool.process_per_hour + time_prepare
    cost_process = tool.depreciation_per_hour * time_process + n * tool.cost_process
    cost_operator = time_process * tool.operator_cost_per_hour
    cost = cost_process + cost_operator
    margin_manual = get_margin("marginProcessManual")
    price = cost * (1 + MARGIN_OPERATION + margin_manual)
    time_hours = math.ceil(time_process * 100) / 100
    return ProcessResult(cost=cost, price=price, time_hours=time_hours)


# ══════════════════════════════════════════════════════════════════════
#  ПЕРЕПЛЁТ И КРЕПЁЖ
# ══════════════════════════════════════════════════════════════════════

def calc_binding(
    n: int,
    size: Sequence[float],
    cover: Dict[str, Dict[str, str]],
    inner: List[Dict[str, Any]],
    binding: Dict[str, str],
    options: Dict[str, Any],
    mode: int = 1,
) -> ProcessResult:
    """
    Переплёт на металлическую пружину.

    :param n: кол-во изделий
    :param size: [ширина, высота] изделия, мм
    :param cover: {'cover': {'materialID': ...}, 'backing': {'materialID': ...}}
    :param inner: [{'materialID': ..., 'numSheet': ...}, ...]
    :param binding: {'edge': 'short'|'long'}
    :param options: {'bindingID': код переплётной машины}
    :param mode: режим производства
    """
    binding_id = options.get("bindingID", "BindRenzSRW")
    tool = _get_tool(binding_id)
    raw_tool = _get_raw_tool(binding_id)

    base_time_ready = tool.base_time_ready or BASE_TIME_READY
    idx = max(0, min(len(base_time_ready) - 1, math.ceil(mode)))
    ready_hours = float(base_time_ready[idx])

    # Нестандартные поля переплётной машины (Cyrillic 'с' в ключе JSON)
    max_sheet_crease = int(raw_tool.get("maxSheetCrease", 20))
    crease_per_hour = float(
        raw_tool.get("\u0441reasePerHour", raw_tool.get("creasePerHour", 150))
    )
    binding_per_hour = float(raw_tool.get("bindingPerHour", 100))

    # Толщина блока (в листах 80 г/м²)
    num_sheet_80 = 0.0
    cover_data = cover.get("cover", {})
    if cover_data.get("materialID"):
        try:
            mat = _get_material("sheet", cover_data["materialID"])
            num_sheet_80 += float(mat.density or 0)
        except (KeyError, TypeError):
            pass
    backing_data = cover.get("backing", {})
    if backing_data.get("materialID"):
        try:
            mat = _get_material("sheet", backing_data["materialID"])
            num_sheet_80 += float(mat.density or 0)
        except (KeyError, TypeError):
            pass
    for block in inner:
        try:
            mat = _get_material("sheet", block["materialID"])
            num_sheet_80 += float(mat.density or 0) * int(block.get("numSheet", 0))
        except (KeyError, TypeError):
            pass

    num_sheet_80 = math.ceil(num_sheet_80 / 80)
    num_stack = math.ceil(num_sheet_80 / max_sheet_crease) if max_sheet_crease > 0 else 1
    thickness_stack = num_sheet_80 / 10  # мм

    time_prepare = tool.time_prepare * mode

    edge = binding.get("edge", "long")
    length_wire = min(size[0], size[1]) if edge == "short" else max(size[0], size[1])

    tool_max_size = tool.max_size or [360, 0]
    if tool_max_size[0] > 0:
        num_stack *= math.ceil(length_wire / tool_max_size[0])

    # Подбор пружины по толщине блока
    from materials import ALL_MATERIALS
    wire_group = ALL_MATERIALS["attachment"].get_group("MetallBindindWire")
    wire = None
    wire_id = None
    wire_raw: Dict[str, Any] = {}
    for w in sorted(wire_group, key=lambda m: m.sizes[0][0] if m.sizes else 0):
        if w.sizes and w.sizes[0][0] > thickness_stack + 1:
            wire = w
            wire_id = w.code
            wire_raw = _get_raw_material("attachment", w.code)
            break
    if wire is None or wire_id is None:
        raise ValueError("Размер изделия больше допустимого для переплёта")

    wire_bobbin_len = wire.sizes[0][1] if wire.sizes and len(wire.sizes[0]) > 1 else 1
    wire_weight_per_unit = float(wire_raw.get("weight", 0))

    time_process = (
        time_prepare
        + n * num_stack / crease_per_hour
        + n / binding_per_hour
    )

    cost_material = (
        float(wire.cost or 0) / wire_bobbin_len * n * length_wire / 8.75
        if wire_bobbin_len > 0 else 0
    )
    cost_process = tool.depreciation_per_hour * time_process + n * num_stack * tool.cost_process
    cost_operator = time_process * tool.operator_cost_per_hour

    margin_manual = get_margin("marginProcessManual")
    cost = cost_process + cost_operator + cost_material
    price = (
        cost_material * (1 + MARGIN_MATERIAL + margin_manual)
        + (cost_process + cost_operator) * (1 + MARGIN_OPERATION + margin_manual)
    )

    weight_kg = math.ceil(n * length_wire / 8.75) * wire_weight_per_unit / 1000
    time_hours = math.ceil(time_process * 100) / 100
    time_ready = time_hours + ready_hours

    wire_usage = math.ceil(n * length_wire / 8.75) / wire_bobbin_len if wire_bobbin_len > 0 else 0

    materials_out = [{
        "code": wire_id,
        "name": wire.description,
        "title": wire.title,
        "quantity": round(wire_usage, 4),
        "unit": "бобин",
    }]
    return ProcessResult(
        cost=cost, price=price, time_hours=time_hours,
        time_ready=time_ready, weight_kg=weight_kg, materials=materials_out,
    )


def calc_set_staples(n: int, options: Dict[str, Any] | None = None, mode: int = 1) -> ProcessResult:
    """
    Степлирование (скрепление скобами). 2 скобы на изделие.

    :param n: кол-во изделий
    :param options: не используется в текущей версии
    :param mode: режим производства
    """
    tool = _get_tool("Bookletmac")
    staples_id = "Staples26_6"
    staples = _get_material("attachment", staples_id)
    staples_raw = _get_raw_material("attachment", staples_id)
    staples_cost_unit = float(staples.cost or 0)
    staples_weight = float(staples_raw.get("weight", 0))

    time_prepare = tool.time_prepare * mode
    time_process = n / tool.process_per_hour + time_prepare
    cost_process = tool.depreciation_per_hour * time_process + n * tool.cost_process
    cost_operator = time_process * tool.operator_cost_per_hour
    cost_material = staples_cost_unit * 2 * n

    margin_manual = get_margin("marginProcessManual")
    cost = cost_material + cost_process + cost_operator
    price = (
        cost_material * (1 + MARGIN_MATERIAL)
        + (cost_process + cost_operator) * (1 + MARGIN_OPERATION + margin_manual)
    )
    time_hours = math.ceil(time_process * 100) / 100
    weight_kg = round(staples_weight * n, 2)

    materials_out = [{
        "code": staples_id,
        "name": staples.description,
        "title": staples.title,
        "quantity": n,
        "unit": "шт",
    }]
    return ProcessResult(
        cost=cost, price=price, time_hours=time_hours,
        time_ready=time_hours, weight_kg=weight_kg, materials=materials_out,
    )


# ══════════════════════════════════════════════════════════════════════
#  ЛЮВЕРСЫ
# ══════════════════════════════════════════════════════════════════════

def calc_eyelet(
    n: int,
    size: Sequence[float],
    step: Sequence[float],
    mode: int = 1,
) -> ProcessResult:
    """
    Люверсовка баннерной продукции.

    :param n: кол-во изделий
    :param size: [ширина, высота] изделия, мм
    :param step: шаг люверсов по сторонам [top, right, bottom, left], мм (0 = нет)
    :param mode: режим производства
    """
    tool = _get_tool("AMGPPROLUX")
    margin_offset = 25  # мм, отступ от края
    sides = [size[0], size[1], size[0], size[1]]
    num_eyelet = 0
    for i in range(4):
        if step[i] > 0:
            num_eyelet += round((sides[i] - margin_offset * 2) / step[i])
            next_i = (i + 1) % 4
            if i < 3 and step[i + 1] == 0:
                num_eyelet += 1
            elif i == 3 and step[0] == 0:
                num_eyelet += 1
    if num_eyelet <= 0:
        return ProcessResult()

    num_eyelet *= n
    time_prepare = tool.time_prepare * mode
    time_process = num_eyelet / tool.process_per_hour + time_prepare
    cost_process = tool.depreciation_per_hour * time_process + num_eyelet * tool.cost_process
    cost_operator = time_process * tool.operator_cost_per_hour
    cost = cost_process + cost_operator
    margin_manual = get_margin("marginProcessManual")
    price = cost * (1 + MARGIN_OPERATION + margin_manual)
    time_hours = math.ceil(time_process * 100) / 100

    materials_out = [{
        "code": "Люверсы", "name": "Люверсы", "title": "Люверсы",
        "quantity": num_eyelet, "unit": "шт",
    }]
    return ProcessResult(cost=cost, price=price, time_hours=time_hours, materials=materials_out)


def calc_eyelet_sheet(n: int, mode: int = 1) -> ProcessResult:
    """
    Люверсовка полиграфической продукции (один люверс 4 мм на изделие).

    :param n: кол-во изделий
    :param mode: режим производства
    """
    tool = _get_tool("JOINERC4")
    num_eyelet = n
    time_prepare = tool.time_prepare * mode
    time_process = num_eyelet / tool.process_per_hour + time_prepare
    cost_process = tool.depreciation_per_hour * time_process + num_eyelet * tool.cost_process
    cost_operator = time_process * tool.operator_cost_per_hour
    cost = cost_process + cost_operator
    margin_manual = get_margin("marginProcessManual")
    price = cost * (1 + MARGIN_OPERATION + margin_manual)
    time_hours = math.ceil(time_process * 100) / 100

    materials_out = [{
        "code": "Люверсы4мм", "name": "Люверсы 4мм", "title": "Люверсы 4мм",
        "quantity": num_eyelet, "unit": "шт",
    }]
    return ProcessResult(cost=cost, price=price, time_hours=time_hours, materials=materials_out)


# ══════════════════════════════════════════════════════════════════════
#  ПРОКЛЕЙКА, НАКЛЕЙКА, НАКАТКА
# ══════════════════════════════════════════════════════════════════════

def calc_gluing_banner(
    n: int,
    size: Sequence[float],
    edge: Sequence[float],
    mode: int = 1,
) -> ProcessResult:
    """
    Проклейка края баннерной продукции.

    :param n: кол-во изделий
    :param size: [ширина, высота], мм
    :param edge: [top, right, bottom, left] — множитель проклейки стороны (0 = не клеить)
    :param mode: режим производства
    """
    tool = _get_tool("GluingBanner")
    sides = [size[0], size[1], size[0], size[1]]
    sum_len = 0.0
    for i in range(4):
        if edge[i] > 0:
            sum_len += sides[i] * edge[i]
    if sum_len <= 0:
        return ProcessResult()

    sum_len *= n / 1000
    time_prepare = tool.time_prepare * mode
    time_process = sum_len / tool.process_per_hour + time_prepare
    cost_process = tool.depreciation_per_hour * time_process + sum_len * tool.cost_process
    cost_operator = time_process * tool.operator_cost_per_hour
    cost = cost_process + cost_operator
    margin_manual = get_margin("marginProcessManual")
    price = cost * (1 + MARGIN_OPERATION + margin_manual)
    time_hours = math.ceil(time_process * 100) / 100
    return ProcessResult(cost=cost, price=price, time_hours=time_hours)


def calc_set_sticker(n: int, size: Sequence[float] = (0, 0), mode: int = 1) -> ProcessResult:
    """
    Наклейка стикера на изделие.

    :param n: кол-во изделий
    :param size: размер стикера (не влияет на расчёт)
    :param mode: режим производства
    """
    tool = _get_tool("SetSticker")
    time_prepare = tool.time_prepare * mode
    time_process = n / tool.process_per_hour + time_prepare
    cost_process = tool.depreciation_per_hour * time_process + n * tool.cost_process
    cost_operator = time_process * tool.operator_cost_per_hour
    cost = cost_process + cost_operator
    margin_manual = get_margin("marginProcessManual")
    price = (cost_process + cost_operator) * (1 + MARGIN_OPERATION + margin_manual)
    time_hours = math.ceil(time_process * 100) / 100
    return ProcessResult(cost=cost, price=price, time_hours=time_hours, time_ready=time_hours)


def calc_manual_roll(
    n: int,
    size: Sequence[float],
    options: Dict[str, Any],
    mode: int = 1,
) -> ProcessResult:
    """
    Ручная накатка плёнки на плоские поверхности.

    :param n: кол-во изделий
    :param size: [ширина, высота], мм
    :param options: {'isEdge': 'isBendEdge'|другое}
    :param mode: режим производства
    """
    raw_tool = _get_raw_tool("ManualRoll")
    tool = _get_tool("ManualRoll")
    roll_per_hour_table: List[List[float]] = raw_tool.get("rollPerHour", [[100000, 2.5]])
    edge_per_hour = float(raw_tool.get("edgePerHour", 30))

    length = 0.0
    roll_per_hour = 0.0
    area = size[0] * size[1] / 1_000_000  # м²

    param_edge = options.get("isEdge", "")
    if param_edge == "isBendEdge":
        min_area = roll_per_hour_table[0][0] if roll_per_hour_table else 0.03
        if area < min_area:
            area = min_area
            length = 0.2
            roll_per_hour = roll_per_hour_table[0][1]
        else:
            length = (size[0] + size[1]) * 2 / 1000
            table = [(float(r[0]), float(r[1])) for r in roll_per_hour_table]
            roll_per_hour = find_in_table(table, area)
    else:
        table = [(float(r[0]), float(r[1])) for r in roll_per_hour_table]
        roll_per_hour = find_in_table(table, area * n)

    sum_len = length * n
    sum_area = area * n
    time_prepare = tool.time_prepare * mode
    time_process = time_prepare
    if roll_per_hour > 0:
        time_process += sum_area / roll_per_hour
    if edge_per_hour > 0:
        time_process += sum_len / edge_per_hour

    cost_process = tool.depreciation_per_hour * time_process
    cost_operator = time_process * tool.operator_cost_per_hour
    cost = cost_process + cost_operator
    margin_manual = get_margin("marginProcessManual")
    price = cost * (1 + MARGIN_OPERATION + margin_manual)
    time_hours = math.ceil(time_process * 100) / 100
    return ProcessResult(cost=cost, price=price, time_hours=time_hours)


# ══════════════════════════════════════════════════════════════════════
#  ПОЛИМЕРНАЯ ЗАЛИВКА
# ══════════════════════════════════════════════════════════════════════

def calc_epoxy(
    n: int,
    size: Sequence[float],
    difficulty: float = 1.0,
    options: Dict[str, Any] | None = None,
    mode: int = 1,
) -> ProcessResult:
    """
    Полимерная заливка эпоксидной смолой.

    :param n: кол-во изделий
    :param size: [ширина, высота], мм
    :param difficulty: сложность формы (1=простая, >1=сложная)
    :param options: {'isLayout': True}
    :param mode: режим производства
    """
    if options is None:
        options = {}

    raw_epoxy = _get_raw_material("epoxy", "EpoxyPoly")
    epoxy_cost = float(raw_epoxy.get("cost", 0))
    epoxy_exptime = float(raw_epoxy.get("exptime", 0.25))
    epoxy = _get_material("epoxy", "EpoxyPoly")

    mixer_raw = _get_raw_tool("VacuumMixerUZLEX")
    mixer = _get_tool("VacuumMixerUZLEX")
    mixer_time_mix = float(mixer_raw.get("timeMix", 0.08))

    tool_raw = _get_raw_tool("EpoxyCoating")
    tool = _get_tool("EpoxyCoating")
    process_per_hour_arr = tool_raw.get("processPerHour", [4000, 2000, 1300])
    epoxy_per_cm2 = float(tool_raw.get("epoxyPerCM2", 0.16))

    base_time_ready = tool.base_time_ready or BASE_TIME_READY
    idx = max(0, min(len(base_time_ready) - 1, math.ceil(mode)))
    ready_hours = float(base_time_ready[idx])

    defects = tool.get_defect_rate(float(n))
    if mode > 1:
        defects += defects * (mode - 1)
    num_coating = n * (1 + defects)

    vol_coating = num_coating * size[0] * size[1] / 100  # см²
    vol_material = vol_coating * epoxy_per_cm2  # г

    # Скорость заливки зависит от сложности и площади
    if difficulty == 1:
        area_mm2 = size[0] * size[1]
        if area_mm2 <= 600:
            speed_idx = 2
        elif area_mm2 <= 3600:
            speed_idx = 1
        else:
            speed_idx = 0
    else:
        speed_idx = 2
    speed_coating = float(process_per_hour_arr[min(speed_idx, len(process_per_hour_arr) - 1)])

    time_layout = num_coating / 1800 if options.get("isLayout") else 0
    time_coating = vol_coating / speed_coating + time_layout if speed_coating > 0 else time_layout
    time_prepare_tool = tool.time_prepare * mode

    num_mix = math.ceil(time_coating / epoxy_exptime) if epoxy_exptime > 0 else 1
    time_mix = num_mix * mixer_time_mix + tool.time_prepare * mode
    time_coating += time_prepare_tool

    cost_process = mixer.depreciation_per_hour * time_mix + num_mix * mixer.cost_process
    cost_process_tool = tool.depreciation_per_hour * time_coating
    if tool.cost_process > 0:
        cost_process_tool += vol_material / tool.cost_process
    cost_process += cost_process_tool

    cost_operator = time_mix * mixer.operator_cost_per_hour
    cost_operator += time_coating * tool.operator_cost_per_hour
    cost_material = vol_material / 1000 * epoxy_cost

    cost = cost_material + cost_process + cost_operator
    price = (
        cost_material * (1 + MARGIN_MATERIAL)
        + (cost_process + cost_operator) * (1 + MARGIN_OPERATION)
    )

    time_hours = math.ceil((time_mix + time_coating) * 100) / 100
    weight_kg = round(vol_material / 1000, 2)
    time_ready = time_hours + ready_hours

    materials_out = [{
        "code": "EpoxyPoly",
        "name": epoxy.description,
        "title": epoxy.title,
        "quantity": round(vol_material / 1000, 4),
        "unit": "кг",
    }]
    return ProcessResult(
        cost=cost, price=price, time_hours=time_hours,
        time_ready=time_ready, weight_kg=weight_kg, materials=materials_out,
    )


# ══════════════════════════════════════════════════════════════════════
#  УФ-СКЛЕЙКА
# ══════════════════════════════════════════════════════════════════════

def calc_uv_gluing(n: int, size: Sequence[float], mode: int = 1) -> ProcessResult:
    """
    УФ-склейка.

    :param n: кол-во изделий
    :param size: [ширина, высота] склеиваемой детали, мм
    :param mode: режим производства
    """
    tool = _get_tool("TICUV300")
    tool_max_size = tool.max_size or [230, 260]
    layout = layout_on_sheet(list(size), tool_max_size)
    num_sheet = math.ceil(n / layout["num"]) if layout["num"] > 0 else n

    time_prepare = tool.time_prepare * mode
    time_process = num_sheet / tool.process_per_hour + time_prepare
    time_operator = time_prepare + n * (1 / 60)

    cost_process = tool.depreciation_per_hour * time_process + num_sheet * tool.cost_process
    cost_operator = time_operator * tool.operator_cost_per_hour
    cost = cost_process + cost_operator
    margin_manual = get_margin("marginProcessManual")
    price = cost * (1 + MARGIN_OPERATION + margin_manual)
    time_hours = math.ceil(time_process * 100) / 100
    return ProcessResult(cost=cost, price=price, time_hours=time_hours)


# ══════════════════════════════════════════════════════════════════════
#  УСТАНОВКА ЭЛЕМЕНТОВ
# ══════════════════════════════════════════════════════════════════════

def calc_set_cursor(n: int, cursor_id: str, mode: int = 1) -> ProcessResult:
    """
    Установка курсора на квартальный календарь.

    :param n: кол-во изделий
    :param cursor_id: код курсора из каталога calendar
    :param mode: режим производства
    """
    tool = _get_tool("SetCursor")
    cursor = _get_material("calendar", cursor_id)
    cursor_raw = _get_raw_material("calendar", cursor_id)
    cursor_cost = float(cursor.cost or 0)
    cursor_weight = float(cursor_raw.get("weight", 0))

    time_prepare = tool.time_prepare * mode
    time_process = n / tool.process_per_hour + time_prepare
    cost_process = tool.depreciation_per_hour * time_process + n * tool.cost_process
    cost_operator = time_process * tool.operator_cost_per_hour
    cost_material = cursor_cost * n

    margin_manual = get_margin("marginProcessManual")
    cost = cost_material + cost_process + cost_operator
    price = (
        cost_material * (1 + MARGIN_MATERIAL)
        + (cost_process + cost_operator) * (1 + MARGIN_OPERATION + margin_manual)
    )
    time_hours = math.ceil(time_process * 100) / 100
    weight_kg = round(cursor_weight * n, 2)

    materials_out = [{
        "code": cursor_id,
        "name": cursor.description,
        "title": cursor.title,
        "quantity": n,
        "unit": "шт",
    }]
    return ProcessResult(
        cost=cost, price=price, time_hours=time_hours,
        time_ready=time_hours, weight_kg=weight_kg, materials=materials_out,
    )


def calc_set_rigel(
    n: int,
    width: float,
    num_sheet: int,
    material_id: str,
    mode: int = 1,
) -> ProcessResult:
    """
    Установка ригеля на квартальный календарь (включает пробивку отверстий).

    :param n: кол-во изделий
    :param width: ширина стороны для ригеля, мм
    :param num_sheet: кол-во листов в пачке (не используется)
    :param material_id: код материала
    :param mode: режим производства
    """
    tool = _get_tool("SetRigel")

    rigel_id = "Rigel"
    if width <= 210:
        rigel_id += "150"
    elif width <= 297:
        rigel_id += "200"
    else:
        rigel_id += "250"

    rigel = _get_material("calendar", rigel_id)
    rigel_raw = _get_raw_material("calendar", rigel_id)
    rigel_cost = float(rigel.cost or 0)
    rigel_weight = float(rigel_raw.get("weight", 0))

    cost_punching = calc_punching(n, material_id, mode)

    time_prepare = tool.time_prepare * mode
    time_process = n / tool.process_per_hour + time_prepare
    cost_process = tool.depreciation_per_hour * time_process + n * tool.cost_process
    cost_operator = time_process * tool.operator_cost_per_hour
    cost_material = rigel_cost * n

    margin_manual = get_margin("marginProcessManual")
    cost = cost_material + cost_process + cost_operator + cost_punching.cost
    price = (
        cost_material * (1 + MARGIN_MATERIAL)
        + (cost_process + cost_operator) * (1 + MARGIN_OPERATION + margin_manual)
        + cost_punching.price
    )
    time_hours = time_process + cost_punching.time_hours
    weight_kg = round(rigel_weight / 1000 * n, 2)

    materials_out = [{
        "code": rigel_id,
        "name": rigel.description,
        "title": rigel.title,
        "quantity": n,
        "unit": "шт",
    }]
    return ProcessResult(
        cost=cost, price=price, time_hours=time_hours,
        time_ready=time_hours, weight_kg=weight_kg, materials=materials_out,
    )


def calc_set_shaft(n: int, shaft_id: str, mode: int = 1) -> ProcessResult:
    """
    Установка пластиковой палочки (флажок).

    :param n: кол-во изделий
    :param shaft_id: код палочки из каталога flag или misc
    :param mode: режим производства
    """
    tool = _get_tool("SetShaft")
    try:
        shaft = _get_material("flag", shaft_id)
        shaft_raw = _get_raw_material("flag", shaft_id)
    except KeyError:
        shaft = _get_material("misc", shaft_id)
        shaft_raw = _get_raw_material("misc", shaft_id)

    shaft_cost = float(shaft.cost or 0)
    shaft_weight = float(shaft_raw.get("weight", 0))

    time_prepare = tool.time_prepare * mode
    time_process = n / tool.process_per_hour + time_prepare
    cost_process = tool.depreciation_per_hour * time_process + n * tool.cost_process
    cost_operator = time_process * tool.operator_cost_per_hour
    cost_material = shaft_cost * n

    margin_manual = get_margin("marginProcessManual")
    cost = cost_material + cost_process + cost_operator
    price = (
        cost_material * (1 + MARGIN_MATERIAL)
        + (cost_process + cost_operator) * (1 + MARGIN_OPERATION + margin_manual)
    )
    time_hours = math.ceil(time_process * 100) / 100
    weight_kg = round(shaft_weight * n, 2)

    materials_out = [{
        "code": shaft_id,
        "name": shaft.description,
        "title": shaft.title,
        "quantity": n,
        "unit": "шт",
    }]
    return ProcessResult(
        cost=cost, price=price, time_hours=time_hours,
        time_ready=time_hours, weight_kg=weight_kg, materials=materials_out,
    )


def calc_set_rope(n: int, rope_id: str, mode: int = 1) -> ProcessResult:
    """
    Установка шнура на вымпел.

    :param n: кол-во изделий
    :param rope_id: код шнура из каталога pennant или misc
    :param mode: режим производства
    """
    tool = _get_tool("SetRope")
    try:
        rope = _get_material("pennant", rope_id)
        rope_raw = _get_raw_material("pennant", rope_id)
    except KeyError:
        rope = _get_material("misc", rope_id)
        rope_raw = _get_raw_material("misc", rope_id)

    rope_cost = float(rope.cost or 0)
    rope_weight = float(rope_raw.get("weight", 0))

    time_prepare = tool.time_prepare * mode
    time_process = n / tool.process_per_hour + time_prepare
    cost_process = tool.depreciation_per_hour * time_process + n * tool.cost_process
    cost_operator = time_process * tool.operator_cost_per_hour
    cost_material = rope_cost * n

    margin_manual = get_margin("marginProcessManual")
    cost = cost_material + cost_process + cost_operator
    price = (
        cost_material * (1 + MARGIN_MATERIAL)
        + (cost_process + cost_operator) * (1 + MARGIN_OPERATION + margin_manual)
    )
    time_hours = time_process
    weight_kg = rope_weight * n / 1000

    materials_out = [{
        "code": rope_id,
        "name": rope.description,
        "title": rope.title,
        "quantity": n,
        "unit": "шт",
    }]
    return ProcessResult(
        cost=cost, price=price, time_hours=time_hours,
        time_ready=time_hours, weight_kg=weight_kg, materials=materials_out,
    )


def calc_set_insert(n: int, mode: int = 1) -> ProcessResult:
    """
    Установка бумажной вставки в акриловую заготовку.

    :param n: кол-во изделий
    :param mode: режим производства
    """
    tool = _get_tool("SetInsert")
    time_prepare = tool.time_prepare * mode
    time_process = n / tool.process_per_hour + time_prepare
    cost_process = tool.depreciation_per_hour * time_process + n * tool.cost_process
    cost_operator = time_process * tool.operator_cost_per_hour
    cost = cost_process + cost_operator
    margin_manual = get_margin("marginProcessManual")
    price = cost * (1 + MARGIN_OPERATION + margin_manual)
    return ProcessResult(
        cost=cost, price=price, time_hours=time_process, time_ready=time_process,
    )


def calc_set_profile(
    n: int,
    segments: List[List[float]],
    profile_id: str,
    mode: int = 1,
) -> ProcessResult:
    """
    Установка профиля на стенд (пружины + уголки).

    :param n: кол-во наборов
    :param segments: [[длина_мм, кол-во], ...] — отрезки профиля
    :param profile_id: код профиля
    :param mode: режим производства
    """
    raw_tool = _get_raw_tool("SetProfile")
    tool = _get_tool("SetProfile")
    pph_spring = float(raw_tool.get("processPerHourSetSpring", 200))
    pph_corner = float(raw_tool.get("processPerHourSetCorner", 100))

    profile = _get_material("profile", profile_id)
    profile_raw = _get_raw_material("profile", profile_id)
    spring_id = profile_raw.get("spring")
    corner_id = profile_raw.get("corner")
    if not spring_id or not corner_id:
        raise ValueError(f"У профиля {profile_id!r} не указаны spring/corner")

    spring = _get_material("profile", spring_id)
    spring_raw = _get_raw_material("profile", spring_id)
    corner = _get_material("profile", corner_id)
    corner_raw = _get_raw_material("profile", corner_id)
    spring_step = float(spring_raw.get("step", 200))

    num_corner = n * sum(int(seg[1]) for seg in segments)
    num_spring = n * sum(
        math.ceil(seg[0] / spring_step + 1) * int(seg[1]) for seg in segments
    )

    time_prepare = tool.time_prepare * mode
    time_process = (
        num_spring / pph_spring
        + num_corner / pph_corner
        + time_prepare
    )
    cost_process = tool.depreciation_per_hour * time_process + n * tool.cost_process
    cost_operator = time_process * tool.operator_cost_per_hour
    cost_material = float(spring.cost or 0) * num_spring + float(corner.cost or 0) * num_corner

    margin_manual = get_margin("marginProcessManual")
    cost = cost_material + cost_process + cost_operator
    price = (
        cost_material * (1 + MARGIN_MATERIAL)
        + (cost_process + cost_operator) * (1 + MARGIN_OPERATION + margin_manual)
    )
    time_hours = time_process
    spring_weight = float(spring_raw.get("weight", 0))
    corner_weight = float(corner_raw.get("weight", 0))
    weight_kg = spring_weight / 1000 * num_spring + corner_weight / 1000 * num_corner

    materials_out = [
        {
            "code": spring_id, "name": spring.description, "title": spring.title,
            "quantity": num_spring, "unit": "шт",
        },
        {
            "code": corner_id, "name": corner.description, "title": corner.title,
            "quantity": num_corner, "unit": "шт",
        },
    ]
    return ProcessResult(
        cost=cost, price=price, time_hours=time_hours,
        time_ready=time_hours, weight_kg=weight_kg, materials=materials_out,
    )


# ══════════════════════════════════════════════════════════════════════
#  КРЕПЛЕНИЯ, КАРМАНЫ, УПАКОВКА
# ══════════════════════════════════════════════════════════════════════

def calc_attachment(n: int, attachment_id: str, mode: int = 1) -> ProcessResult:
    """
    Установка крепления (булавка, магнит, цанга и т.п.).

    :param n: кол-во креплений
    :param attachment_id: код крепления
    :param mode: режим производства
    """
    attachment = _get_material("attachment", attachment_id)
    attachment_raw = _get_raw_material("attachment", attachment_id)
    attach_cost = float(attachment.cost or 0)
    attach_weight = float(attachment_raw.get("weight", 0))

    time_prepare = 0.1 * mode
    process_per_hour = 400
    time_process = n / process_per_hour + time_prepare
    cost_operator = time_process * COST_OPERATOR
    cost_material = n * attach_cost

    cost = cost_material + cost_operator
    price = (
        cost_material * (1 + MARGIN_MATERIAL)
        + cost_operator * (1 + MARGIN_OPERATION)
    )
    time_hours = math.ceil(time_process * 100) / 100
    weight_kg = round(n * attach_weight / 1000, 2)

    materials_out = [{
        "code": attachment_id,
        "name": attachment.description,
        "title": attachment.title,
        "quantity": n,
        "unit": "шт",
    }]
    return ProcessResult(
        cost=cost, price=price, time_hours=time_hours,
        weight_kg=weight_kg, materials=materials_out,
    )


def calc_pocket(n: int, pocket_id: str, mode: int = 1) -> ProcessResult:
    """
    Установка кармана.

    :param n: кол-во карманов
    :param pocket_id: код кармана
    :param mode: режим производства
    """
    pocket = _get_material("pocket", pocket_id)
    pocket_raw = _get_raw_material("pocket", pocket_id)
    pocket_cost = float(pocket.cost or 0)
    pocket_weight = float(pocket_raw.get("weight", 0))

    time_prepare = 0.1 * mode
    process_per_hour = 400
    time_process = n / process_per_hour + time_prepare
    cost_operator = time_process * COST_OPERATOR
    cost_material = n * pocket_cost

    cost = cost_material + cost_operator
    price = (
        cost_material * (1 + MARGIN_MATERIAL)
        + cost_operator * (1 + MARGIN_OPERATION)
    )
    time_hours = math.ceil(time_process * 100) / 100
    weight_kg = round(n * pocket_weight / 1000, 2)

    materials_out = [{
        "code": pocket_id,
        "name": pocket.description,
        "title": pocket.title,
        "quantity": n,
        "unit": "шт",
    }]
    return ProcessResult(
        cost=cost, price=price, time_hours=time_hours,
        weight_kg=weight_kg, materials=materials_out,
    )


def calc_packing(
    n: int,
    size: Sequence[float],
    options: Dict[str, Any],
    mode: int = 1,
) -> ProcessResult:
    """
    Упаковка в зиплок-пакеты.

    :param n: кол-во изделий
    :param size: [ширина, высота, толщина], мм
    :param options: {'isPacking': код_пакета | ''} — '' = автоподбор
    :param mode: режим производства
    """
    from materials import ALL_MATERIALS

    pack = None
    pack_id = None

    if "isPacking" not in options:
        return ProcessResult()
    is_packing = options["isPacking"]

    if isinstance(is_packing, str) and is_packing != "":
        pack = _get_material("pack", is_packing)
        pack_id = is_packing
    else:
        thickness = size[2] if len(size) > 2 else 0
        min_size_pack = [size[0] + thickness + 5, size[1] + thickness + 5]
        pack_catalog = ALL_MATERIALS.get("pack")
        if pack_catalog:
            best_area = float("inf")
            for code, spec in pack_catalog.list_all().items():
                if not spec.sizes:
                    continue
                s = spec.sizes[0]
                sw, sh = s[0], s[1]
                fits = (
                    (sw > min_size_pack[0] and sh > min_size_pack[1])
                    or (sw > min_size_pack[1] and sh > min_size_pack[0])
                )
                if fits and sw * sh < best_area:
                    best_area = sw * sh
                    pack = spec
                    pack_id = code

    if pack is None or pack_id is None:
        return ProcessResult()

    pack_raw = _get_raw_material("pack", pack_id)
    pack_cost = float(pack.cost or 0)
    pack_weight = float(pack_raw.get("weight", 0))

    time_prepare = 0.1 * mode
    process_per_hour = 400
    time_process = n / process_per_hour + time_prepare
    cost_operator = time_process * COST_OPERATOR
    cost_material = n * pack_cost

    cost = cost_material + cost_operator
    price = (
        cost_material * (1 + MARGIN_MATERIAL)
        + cost_operator * (1 + MARGIN_OPERATION)
    )
    time_hours = math.ceil(time_process * 100) / 100
    weight_kg = round(n * pack_weight / 1000, 2)

    materials_out = [{
        "code": pack_id,
        "name": pack.description,
        "title": pack.title,
        "quantity": n,
        "unit": "шт",
    }]
    return ProcessResult(
        cost=cost, price=price, time_hours=time_hours,
        weight_kg=weight_kg, materials=materials_out,
    )


# ══════════════════════════════════════════════════════════════════════
#  НАРЕЗКА
# ══════════════════════════════════════════════════════════════════════

def calc_set_canvas_frame(
    n: int,
    size: Sequence[float],
    mode: int = 1,
) -> ProcessResult:
    """
    Натяжка холста на подрамник.

    :param n: кол-во изделий
    :param size: [ширина, высота] рамы, мм
    :param mode: режим производства
    """
    tool = _get_tool("SetCanvasFrame")
    len_sides = [size[0], size[1], size[0], size[1]]
    sum_len_m = sum(len_sides) * n / 1000.0
    if sum_len_m <= 0:
        return ProcessResult()

    time_prepare = tool.time_prepare * mode
    time_process = sum_len_m / tool.process_per_hour + time_prepare
    cost_process = tool.depreciation_per_hour * time_process + sum_len_m * tool.cost_process
    cost_operator = time_process * tool.operator_cost_per_hour
    cost = cost_process + cost_operator
    margin_manual = get_margin("marginProcessManual")
    price = cost * (1 + MARGIN_OPERATION + margin_manual)
    time_hours = math.ceil(time_process * 100) / 100
    return ProcessResult(cost=cost, price=price, time_hours=time_hours)


def calc_cut_profile(
    n: int,
    segments: List[List[float]],
    tool_id: str,
    mode: int = 1,
) -> ProcessResult:
    """
    Нарезка профиля (труб, планок) на отрезном станке.

    :param n: кол-во наборов
    :param segments: [[длина_мм, кол-во], ...] — отрезки
    :param tool_id: код отрезного устройства (напр. 'DWE713XPS')
    :param mode: режим производства
    """
    tool = _get_tool(tool_id)
    num_cut = sum(2 * n * int(seg[1]) for seg in segments)

    base_time_ready = tool.base_time_ready or BASE_TIME_READY
    idx = max(0, min(len(base_time_ready) - 1, math.ceil(mode)))
    ready_hours = float(base_time_ready[idx])

    time_prepare = tool.time_prepare * mode
    time_process = num_cut / tool.process_per_hour + time_prepare if tool.process_per_hour > 0 else time_prepare
    cost_process = tool.depreciation_per_hour * time_process + num_cut * tool.cost_process
    cost_operator = time_process * tool.operator_cost_per_hour
    cost = cost_process + cost_operator
    margin_manual = get_margin("marginProcessManual")
    price = cost * (1 + MARGIN_OPERATION + margin_manual)
    time_hours = math.ceil(time_process * 100) / 100
    time_ready = time_hours + ready_hours
    return ProcessResult(cost=cost, price=price, time_hours=time_hours, time_ready=time_ready)


def calc_cut_saber(
    num_sheet: int,
    size: Sequence[float],
    size_sheet: Sequence[float],
    material_id: str,
    cutter_id: str,
    margins: Sequence[float] | None,
    interval: float,
    mode: int = 1,
) -> ProcessResult:
    """
    Резка на сабельном резаке.

    :param num_sheet: кол-во листов для резки
    :param size: [ширина, высота] изделия, мм
    :param size_sheet: [ширина, высота] листа, мм
    :param material_id: код материала
    :param cutter_id: код резака из каталога cutter
    :param margins: поля печати [top, right, bottom, left], мм (None = без полей)
    :param interval: интервал между изделиями (0 = одним резом)
    :param mode: режим производства
    """
    def heaviside(a: float) -> int:
        return 0 if a == 0 else 1

    cutter = _cutter_catalog().get(cutter_id)
    cutter_max = cutter.max_size or [0, 0]
    if min(size_sheet[0], size_sheet[1]) > max(cutter_max[0], cutter_max[1]):
        return ProcessResult()

    layout = layout_on_sheet(list(size), list(size_sheet), margins, interval)
    if layout["num"] == 0:
        return ProcessResult()

    num_double_cut = heaviside(interval) + 1
    cols = layout["cols"]
    rows = layout["rows"]
    num_cut = 4 + (cols - 1) * num_double_cut + cols * (rows - 1) * num_double_cut
    num_cut *= num_sheet

    if num_cut <= 0:
        return ProcessResult()

    time_prepare = cutter.time_prepare * mode
    cuts_per_hour = cutter.cuts_per_hour or cutter.process_per_hour or 1
    time_cut = num_cut / cuts_per_hour + time_prepare
    cost_cut = cutter.depreciation_per_hour * time_cut + num_cut * cutter.cost_process
    cost_operator = time_cut * cutter.operator_cost_per_hour

    cost = math.ceil(cost_cut + cost_operator)
    margin_guillotine = get_margin("marginCutGuillotine")
    price = math.ceil(cost * (1 + MARGIN_OPERATION + margin_guillotine))
    time_hours = math.ceil(time_cut * 100) / 100
    return ProcessResult(cost=float(cost), price=float(price), time_hours=time_hours)


# ══════════════════════════════════════════════════════════════════════
#  ПОШИВ
# ══════════════════════════════════════════════════════════════════════

def calc_sewing_covers(
    n: int,
    size: Sequence[float],
    material_id: str,
    mode: int = 1,
) -> ProcessResult:
    """
    Пошив чехла (для прессволлов и т.п.).

    :param n: кол-во чехлов
    :param size: [ширина, высота, глубина], мм (минимум 2 элемента)
    :param material_id: код ткани из каталога presswall
    :param mode: режим производства
    """
    tool = _get_tool("Sewing")
    material = _get_material("presswall", material_id)

    base_time_ready = tool.base_time_ready or BASE_TIME_READY
    idx = max(0, min(len(base_time_ready) - 1, math.ceil(mode)))
    ready_hours = float(base_time_ready[idx])

    time_prepare = tool.time_prepare * mode
    time_process = n / tool.process_per_hour + time_prepare if tool.process_per_hour > 0 else time_prepare
    cost_process = tool.depreciation_per_hour * time_process + n * tool.cost_process
    cost_operator = time_process * tool.operator_cost_per_hour

    w = size[0]
    h = size[1] if len(size) > 1 else 0
    depth = size[2] if len(size) > 2 else 0
    size_material = [
        w + max(h, depth) + 100,
        (h + depth) / 2 * 3.14 + 100,
    ]
    mat_sizes = material.sizes[0] if material.sizes else [1000, 0]
    layout = layout_on_roll(n, size_material, mat_sizes)
    mat_cost_per_unit = float(material.cost or 0)
    cost_material = layout["length"] * mat_sizes[0] * mat_cost_per_unit / 1_000_000

    cost = cost_material + cost_process + cost_operator
    price = (
        (cost_process + cost_operator) * (1 + MARGIN_OPERATION)
        + cost_material * (1 + MARGIN_MATERIAL)
    )
    time_hours = math.ceil(time_process * 100) / 100
    time_ready = time_hours + ready_hours

    density = float(material.density or 0)
    weight_kg = n * density * size_material[0] * size_material[1] / 1_000_000

    materials_out = [{
        "code": material_id,
        "name": material.description,
        "title": material.title,
        "quantity": round(layout["length"] / 1000, 4),
        "unit": "м",
    }]
    return ProcessResult(
        cost=cost, price=price, time_hours=time_hours,
        time_ready=time_ready, weight_kg=weight_kg, materials=materials_out,
    )


# ══════════════════════════════════════════════════════════════════════
#  ДОСТАВКА
# ══════════════════════════════════════════════════════════════════════

def calc_shipment(
    n: int,
    size: Sequence[float],
    weight: float,
    cargo_id: str = "Dellin",
) -> ProcessResult:
    """
    Расчёт стоимости доставки.

    :param n: кол-во мест
    :param size: [ширина, высота, глубина] одного места, мм
    :param weight: вес одного места, кг
    :param cargo_id: 'Dellin' | 'Luch' | 'Own'
    """
    def check_fit(vol_detal: List[float], vol_box: List[float]) -> bool:
        d = sorted(vol_detal)
        b = sorted(vol_box)
        return all(d[i] <= b[i] for i in range(3))

    result = ProcessResult()

    if cargo_id == "Dellin":
        result.cost = 1000 + n * weight * 30
        result.price = result.cost * (1 + MARGIN_MATERIAL)
        result.time_hours = 0.5
        result.time_ready = 40.0

    elif cargo_id == "Luch":
        base_tariff = [
            [3, 0.004, 1, 200, 200, 200],
            [30, 0.125, 1, 250, 250, 200],
            [60, 0.25, 2, 500, 250, 200],
            [100, 0.343, 3, 750, 300, 300],
            [140, 0.5, 5, 1000, 300, 300],
            [200, 1.0, 8, 1250, 300, 300],
            [400, 2.0, 11, 3000, 400, 300],
        ]
        vol_shipment = size[0] * size[1] * size[2] / 1_000_000_000
        cost_shipment = 0.0
        for t in base_tariff:
            cost_shipment = t[3] + t[5]
            if weight <= t[0] and vol_shipment <= t[1] and n <= t[2]:
                break
        result.cost = cost_shipment
        result.price = result.cost * (1 + MARGIN_MATERIAL)
        result.time_hours = 0.5
        result.time_ready = 16.0

    elif cargo_id == "Own":
        base_cost_size = [
            [800, 800, 500, 500],
            [1000, 1400, 200, 1000],
            [4000, 2000, 200, 2000],
            [4000, 2000, 3000, 6000],
        ]
        cost_shipment = 0.0
        for params in base_cost_size:
            size_transport = [params[0], params[1], params[2]]
            for i in range(3):
                size_shipment = [size[0], size[1], size[2]]
                size_shipment[i] *= n
                if check_fit(size_shipment, size_transport):
                    if cost_shipment == 0 or cost_shipment > params[3]:
                        cost_shipment = params[3]
        result.cost = cost_shipment
        result.price = result.cost * (1 + MARGIN_MATERIAL)
        result.time_hours = 0.5
        result.time_ready = 40.0

    return result


# ══════════════════════════════════════════════════════════════════════
#  ВЫРУБНАЯ ФОРМА
# ══════════════════════════════════════════════════════════════════════

def calc_form(
    size_item: Sequence[float],
    num_items: int,
    difficulty: float = 1.0,
    mode: int = 1,
) -> ProcessResult:
    """
    Изготовление вырубной формы.

    :param size_item: [ширина, высота] одного элемента, мм
    :param num_items: кол-во элементов на форме
    :param difficulty: сложность (1=простая, >1=сложная)
    :param mode: режим производства
    """
    COST_KNIFE = 1000  # руб./мп
    MIN_COST_FORM = 1000

    base_time_ready = [32, 24, 16]
    len_form = num_items * (size_item[0] + size_item[1]) * 2 * difficulty
    cost_form = COST_KNIFE * len_form / 1000
    cost_form = max(cost_form, MIN_COST_FORM)

    cost_ship = calc_shipment(1, [200, 300, 20], 1.0, "Own")

    cost = cost_form + cost_ship.cost
    price = cost_form * (1 + MARGIN_OPERATION) + cost_ship.price
    time_ready = base_time_ready[min(mode, len(base_time_ready) - 1)] + cost_ship.time_ready

    return ProcessResult(
        cost=cost, price=price, time_hours=0, time_ready=time_ready,
    )


# ══════════════════════════════════════════════════════════════════════
#  ШЕЛКОГРАФИЯ
# ══════════════════════════════════════════════════════════════════════

def calc_silk_print(
    n: int,
    size: Sequence[float],
    color: int,
    item_id: str,
    options: Dict[str, Any] | None = None,
    mode: int = 1,
) -> ProcessResult:
    """
    Шелкография по футболкам / трансферам.

    :param n: кол-во изделий
    :param size: [ширина, высота] области печати, мм
    :param color: кол-во цветов
    :param item_id: 'tshirtwhite' | 'tshirtcolor' | 'transfer' | 'hat'
    :param options: {isRotate, isPacking10pcs, isUnPacking10pcs, isPackingIndiv, isUnPackingIndiv, isRasterPrint}
    :param mode: режим производства
    """
    if options is None:
        options = {}

    tool_map = {
        "tshirtwhite": "SilkTShirtWhite",
        "tshirtcolor": "SilkTShirtColor",
        "transfer": "SilkTransfer",
        "hat": "SilkHat",
    }
    tool_code = tool_map.get(item_id, "SilkTShirtWhite")

    raw = _get_raw_tool(tool_code)
    tool = _get_tool(tool_code)

    color_white = 0
    is_rotate = options.get("isRotate", True)
    is_packing_10 = options.get("isPacking10pcs", False)
    is_unpacking_10 = options.get("isUnPacking10pcs", False)
    is_packing_indiv = options.get("isPackingIndiv", True)
    is_unpacking_indiv = options.get("isUnPackingIndiv", True)
    coeff_mesh = 0.0

    if item_id == "tshirtcolor":
        if n < 150:
            coeff_mesh = -0.5
        color_white = 2
        is_rotate = False
    elif item_id == "transfer":
        is_rotate = False
        is_packing_indiv = False
        is_unpacking_indiv = False

    base_time_ready_arr = tool.base_time_ready or BASE_TIME_READY
    idx = max(0, min(len(base_time_ready_arr) - 1, math.ceil(mode)))
    ready_hours = float(base_time_ready_arr[idx])

    defects = tool.get_defect_rate(float(n))
    if mode > 1:
        defects += defects * (mode - 1)
    num_silk = n * (1 + defects)

    process_per_hour_arr = raw.get("processPerHour", [250])
    cost_mesh_unit = float(raw.get("costMesh", 400))
    cost_glue_arr = raw.get("costGlue", [950, 11])
    cost_paint_white_arr = raw.get("costPaintWhite", [1800, 0])
    cost_paint_arr = raw.get("costPaint", [1800, 45])
    margin_tool = float(raw.get("margin", 0.3))
    time_prepare_mesh = float(raw.get("timePrepareMesh", 0.33))
    time_adjustment_arr = raw.get("timeAdjustment", [0.3, 0.0584])
    time_mix_per_color = float(raw.get("timeMix", 0.25))
    pph_packing_indiv = raw.get("processPerHourPackingIndiv", [288, 100])
    pph_packing_10 = raw.get("processPerHourPacking10pcs", [800, 278])
    pph_rotate = float(raw.get("processPerHourRotate", 857))
    cost_operator_silk = float(raw.get("costOperatorSilk", 0))
    cost_operator_pack = float(raw.get("costOperatorPack", 0))
    coeff_overhead = float(raw.get("coeffOverhead", 2.27))
    coeff_soulfly_table = raw.get("coeffSoulfly", [[300, 0.85], [1000000, 0.70]])

    num_mesh = math.ceil(num_silk / 2000) * (color + color_white + coeff_mesh)
    cost_mesh = num_mesh * cost_mesh_unit
    cost_glue = math.ceil(num_silk / 50) * cost_glue_arr[0] * cost_glue_arr[1] / 1000
    cost_paint_white = (
        num_silk * size[0] * size[1] * cost_paint_white_arr[0] * cost_paint_white_arr[1]
        / 1_000_000_000
    )
    cost_paint = (
        num_silk * size[0] * size[1] * cost_paint_arr[0] * cost_paint_arr[1]
        / 1_000_000_000
    )
    cost_paper = 0.0
    area = size[0] * size[1] / 1_000_000
    num_sheet = num_silk

    has_paper = "costPaper" in raw
    if has_paper:
        cost_paper_arr = raw["costPaper"]
        cost_paper = num_silk * area * cost_paper_arr[0] * cost_paper_arr[1]
        part_paper: List[Tuple[float, float]] = [
            (0.015, 1 / 6), (0.0315, 0.5), (0.0609, 1.0), (0.1218, 0.2), (1.0, 2.0),
        ]
        num_sheet = num_silk * find_in_table(part_paper, area)
        if color == 1:
            cost_paint = 0.0

    cost_material = cost_mesh + cost_glue + cost_paint + cost_paper + cost_paint_white

    # Время
    time_prepare_mesh_total = time_prepare_mesh * num_mesh
    time_adjustment = time_adjustment_arr[0] + time_adjustment_arr[1] * (num_mesh - 1)
    color_idx = min(color - 1, len(process_per_hour_arr) - 1)
    time_silk_print = num_sheet / process_per_hour_arr[color_idx] if process_per_hour_arr[color_idx] > 0 else 0
    time_mix = time_mix_per_color * color / 2

    time_packing = 0.0
    if is_rotate:
        time_packing += num_silk / pph_rotate
    if is_unpacking_10:
        time_packing += num_silk / pph_packing_10[0]
    if is_unpacking_indiv:
        time_packing += num_silk / pph_packing_indiv[0]
    if is_packing_10:
        time_packing += num_silk / pph_packing_10[1]
    if is_packing_indiv:
        time_packing += num_silk / pph_packing_indiv[1]

    coeff_raster = 1.25 if options.get("isRasterPrint") else 1.0

    time_put_glue = 0.0
    time_cut_transfer = 0.0
    time_transfer = 0.0
    if has_paper:
        pph_trans_table = raw.get("processPerHourTrans", [[1, 10]])
        pph_trans = find_in_table(
            [(float(r[0]), float(r[1])) for r in pph_trans_table], area
        )
        time_transfer = num_silk / pph_trans if pph_trans > 0 else 0
        pph_glue = float(raw.get("processPerHourGlue", 250))
        time_put_glue = num_sheet / pph_glue if pph_glue > 0 else 0
        pph_cut = float(raw.get("processPerHourCut", 360))
        time_cut_transfer = num_silk / pph_cut if pph_cut > 0 else 0

    time_operator_pack = time_prepare_mesh_total + time_packing + time_put_glue + time_transfer + time_cut_transfer
    time_operator_silk = time_adjustment + time_silk_print + time_mix
    time_prepare = tool.time_prepare * mode

    cost_process = tool.depreciation_per_hour * (time_adjustment + time_silk_print + time_mix)
    op_silk = cost_operator_silk if cost_operator_silk > 0 else COST_OPERATOR
    op_pack = cost_operator_pack if cost_operator_pack > 0 else COST_OPERATOR
    cost_operator = time_operator_silk * op_silk + time_operator_pack * op_pack

    coeff_soulfly = find_in_table(
        [(float(r[0]), float(r[1])) for r in coeff_soulfly_table], float(n)
    )

    cost = (
        (cost_material + cost_process + cost_operator * (1 + coeff_overhead))
        * coeff_raster * (1 + coeff_soulfly)
    )
    price = cost * (1 + MARGIN_OPERATION)
    cost *= (1 + margin_tool)

    time_hours = math.ceil((time_operator_pack + time_operator_silk + time_prepare) * 100) / 100
    time_ready = time_hours + ready_hours

    return ProcessResult(
        cost=cost, price=price, time_hours=time_hours,
        time_ready=time_ready, weight_kg=0,
    )


# ══════════════════════════════════════════════════════════════════════
#  ЗАКАТНЫЕ ЗНАЧКИ
# ══════════════════════════════════════════════════════════════════════

def calc_button_pins(
    n: int,
    pin_id: str,
    options: Dict[str, Any],
    mode: int = 1,
) -> ProcessResult:
    """
    Изготовление закатных значков.

    При n ≤ 2000 — собственное производство (закатка + печать вставок).
    При n > 2000 — заказ у подрядчика (Амалит) + доставка.

    :param n: кол-во значков
    :param pin_id: код размера (D25, D38, D56, D78)
    :param options: {'isPacking': ...}
    :param mode: режим производства

    ВНИМАНИЕ: расчёт бумажных вставок зависит от calcSticker (ещё не мигрирован).
    В текущей версии стоимость вставок не включена — будет добавлена после миграции
    калькулятора calcSticker.js (Батч B, Фаза 2).
    """
    base_time_ready = BASE_TIME_READY
    result = ProcessResult()
    pin_size: List[float] = []

    margin_button = get_margin("marginButtonPins")

    if n <= 2000:
        pin = _get_material("pins", pin_id)
        pin_raw = _get_raw_material("pins", pin_id)
        pin_size = pin.sizes[0] if pin.sizes else [0, 0]
        pin_cost_unit = float(pin.cost or 0)
        pin_weight = float(pin_raw.get("weight", 0))

        tool_map = {"D25": "PressButtonPin25", "D38": "PressButtonPin38",
                     "D56": "PressButtonPin56", "D78": "PressButtonPin78"}
        tool_code = tool_map.get(pin_id, "PressButtonPin25")
        tool = _get_tool(tool_code)

        tool_btr = tool.base_time_ready
        if tool_btr:
            base_time_ready = tool_btr
        btr_idx = max(0, min(len(base_time_ready) - 1, math.ceil(mode)))
        ready_val = float(base_time_ready[btr_idx])

        defects = tool.get_defect_rate(float(n))
        if mode > 1:
            defects += defects * (mode - 1)
        num_with_defects = math.ceil(n * (1 + defects))

        time_prepare = tool.time_prepare * mode
        time_press = time_prepare + num_with_defects / tool.process_per_hour
        cost_process = tool.depreciation_per_hour * time_press + num_with_defects * tool.cost_process
        cost_operator = time_press * tool.operator_cost_per_hour
        cost_material = pin_cost_unit * num_with_defects

        # TODO: добавить расчёт вставок через calcSticker после миграции
        cost_insert = 0.0
        price_insert = 0.0
        time_insert = 0.0

        result.cost = cost_material + cost_process + cost_operator + cost_insert
        result.price = (
            cost_material * (1 + MARGIN_MATERIAL + margin_button)
            + (cost_process + cost_operator) * (1 + MARGIN_OPERATION + margin_button)
            + price_insert * (1 + margin_button)
        )
        result.time_hours = time_press + time_insert
        result.weight_kg = pin_weight * n / 1000
        result.materials = [{
            "code": pin_id,
            "name": pin.description,
            "title": pin.title,
            "quantity": num_with_defects,
            "unit": "шт",
        }]

        # Упаковка
        if options.get("isPacking"):
            cost_pack = calc_packing(n, [pin_size[0], pin_size[1], 5], options, mode)
            result = result.merge(cost_pack)
            result.price += cost_pack.price * margin_button

        result.time_ready = result.time_hours + ready_val

    else:
        # Заказ у подрядчика
        try:
            pin = _get_material("pins", pin_id)
            pin_raw = _get_raw_material("pins", pin_id)
        except KeyError:
            raise ValueError(f"Неизвестный размер значка: {pin_id!r}")

        pin_size = pin.sizes[0] if pin.sizes else [0, 0]
        pin_weight = float(pin_raw.get("weight", 0))
        pin_cost_unit = float(pin.cost or 0)

        # Стоимость берётся напрямую по тиражу (упрощённый расчёт)
        cost_material = pin_cost_unit * n
        time_press = 8 * (n / 2000)
        result.weight_kg = pin_weight * n / 1000

        thickness_pin = 5
        vol_shipment = pin_size[0] * pin_size[1] * thickness_pin * n * 1.1
        cube_side = vol_shipment ** (1 / 3)
        num_shipment = max(1, math.ceil(vol_shipment / (300 * 200 * 400)))
        weight_per_place = result.weight_kg / num_shipment if num_shipment > 0 else result.weight_kg

        cost_ship = calc_shipment(num_shipment, [cube_side, cube_side, cube_side], weight_per_place)

        result.cost = cost_material + cost_ship.cost
        result.price = cost_material * (1 + MARGIN_MATERIAL) + cost_ship.price
        result.time_hours = time_press + cost_ship.time_hours
        result.time_ready = cost_ship.time_ready

        result.materials = [{
            "code": pin_id,
            "name": pin.description,
            "title": pin.title,
            "quantity": n,
            "unit": "шт",
        }]

        if options.get("isPacking"):
            cost_pack = calc_packing(n, [pin_size[0], pin_size[1], 5], options, mode)
            result = result.merge(cost_pack)
            result.price += cost_pack.price * margin_button

        result.time_ready += result.time_hours

    return result
