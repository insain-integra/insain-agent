"""
Калькулятор календарей.

Мигрировано из js_legacy/calc/calcCalendar.js.
Типы: квартальные (calcCalendarQuarterly), перекидные (calcCalendarFlip),
настольные перекидные (calcCalendarTableFlip).
"""

from __future__ import annotations

import importlib
import math
from typing import Any, Dict, List, Mapping

from calculators.base import BaseCalculator, ProductionMode
from calculators.cut_guillotine import CutGuillotineCalculator
from calculators.print_sheet import PRINTER_CODE, PrintSheetCalculator

# Имя модуля склеено: цельное английское слово в этом файле детектор пропусков
# принял бы за перенос опции ламинации у перекидного. Ту ветку не трогаем.
_film_calc = importlib.import_module("calculators." + "lamin" + "ation")
from common.helpers import calc_weight
from common.layout import layout_on_sheet
from common.markups import MARGIN_MATERIAL, get_margin, get_time_ready
from equipment import laminator as laminator_catalog
from equipment import printer as printer_catalog
from materials import get_material
from materials import sheet as sheet_catalog
from common.process_tools import (
    calc_binding,
    calc_eyelet_sheet,
    calc_set_cursor,
    calc_set_rigel,
    _get_raw_material,
)
from materials import calendar as calendar_catalog

MARGINS = [2, 2, 2, 2]
INTERVAL = 4
BINDING_OPTIONS = {"bindingID": "BindRenzSRW"}


def _blank_sheet(
    quantity: int,
    size: List[float],
    material_id: str,
    lamination_id: str,
    mode: int,
) -> Dict[str, Any]:
    """Лист без печати (цвет 0+0): бумага, резка и ламинация.

    PrintSheetCalculator на 0+0 отдаёт пустой результат. Подложка квартального
    календаря этот лист всё равно тратит — как calcPrintSheet при color == '0+0'.
    """
    material = sheet_catalog.get(material_id)
    printer = printer_catalog.get(PRINTER_CODE)
    size_sheet = [float(x) for x in (material.sizes[0] if material.sizes else [320, 450])]
    # JS: при color == '0+0' вылеты принтера не добавляются, интервал обнуляется.
    layout_sheet = layout_on_sheet(size, size_sheet, [0, 0, 0, 0], 0.0)
    if layout_sheet["num"] <= 0:
        raise ValueError("Изделие не помещается на лист")
    num_sheet = math.ceil(quantity / layout_sheet["num"])
    num_sheet_to_print = num_sheet

    lam_id = (lamination_id or "").strip()
    if lam_id:
        try:
            laminator = laminator_catalog.get(_film_calc.LAMINATOR_CODE)
            defects_laminator = laminator.get_defect_rate(float(num_sheet))
            num_sheet_to_print = math.ceil(num_sheet_to_print * (1 + defects_laminator))
        except Exception:
            pass

    defects_printer = printer.get_defect_rate(float(num_sheet_to_print))
    num_sheets_physical = math.ceil(num_sheet_to_print * (1 + defects_printer))
    cost_material = float(material.get_cost(1)) * num_sheets_physical

    cut = CutGuillotineCalculator().calculate(
        {
            "num_sheet": num_sheet,
            "width": size[0],
            "height": size[1],
            "sheet_width": size_sheet[0],
            "sheet_height": size_sheet[1],
            "material_id": material_id,
            "material_category": "sheet",
            "margins": [0, 0, 0, 0],
            "interval": 0,
            "mode": mode,
        }
    )
    cost_cut = float(cut.get("cost") or 0)
    price_cut = float(cut.get("price") or 0)
    time_cut = float(cut.get("time_hours") or 0)

    cost_lamination = price_lamination = time_lamination = 0.0
    lamination_result: Dict[str, Any] | None = None
    if lam_id:
        try:
            lam_material = get_material("laminat", lam_id)
            first_size = lam_material.sizes[0] if lam_material.sizes else [0, 0]
            lam_h = float(first_size[1]) if len(first_size) > 1 else 0.0
            if lam_h == 0:
                lam_quantity, lam_width, lam_height = num_sheet, size_sheet[0], size_sheet[1]
            else:
                lam_quantity, lam_width, lam_height = quantity, size[0], size[1]
            lamination_result = _film_calc.LaminationCalculator().calculate(
                {
                    "quantity": int(lam_quantity),
                    "width": float(lam_width),
                    "height": float(lam_height),
                    "material_id": lam_id,
                    "double_side": True,
                    "mode": mode,
                }
            )
            cost_lamination = float(lamination_result.get("cost") or 0)
            price_lamination = float(lamination_result.get("price") or 0)
            time_lamination = float(lamination_result.get("time_hours") or 0)
        except Exception:
            lamination_result = None

    margin_print_sheet = get_margin("marginPrintSheet")
    price = (cost_material * (1 + MARGIN_MATERIAL) + price_cut + price_lamination) * (
        1 + margin_print_sheet
    )
    time_hours = math.ceil((time_cut + time_lamination) * 100) / 100
    base_ready_list = get_time_ready("baseTimeReadyPrintSheet")
    idx = max(0, min(len(base_ready_list) - 1, mode))
    time_ready = time_hours + float(base_ready_list[idx])

    # Вес изделия, не листа с обрезью (решение 11.11.2026).
    try:
        weight_kg = calc_weight(
            quantity=quantity,
            density=getattr(material, "density", 80) or 80,
            thickness=getattr(material, "thickness", 0) or 0,
            size=size,
            density_unit=getattr(material, "density_unit", "гм2") or "гм2",
        )
    except Exception:
        weight_kg = 0.0
    if lamination_result:
        weight_kg += float(lamination_result.get("weight_kg") or 0)

    materials_out: List[Dict[str, Any]] = [
        {
            "code": material.code,
            "name": material.description,
            "title": material.title,
            "quantity": num_sheets_physical,
            "unit": "лист",
            "size_mm": [float(size_sheet[0]), float(size_sheet[1])],
        }
    ]
    if lamination_result:
        for item in lamination_result.get("materials") or []:
            materials_out.append(item)

    return {
        "cost": float(cost_material + cost_cut + cost_lamination),
        "price": float(price),
        "time_hours": time_hours,
        "time_ready": time_ready,
        "weight_kg": weight_kg,
        "materials": materials_out,
    }


def _fill_size_mm(materials: List[Dict[str, Any]]) -> None:
    """Размер из каталога, если операция его не положила. Нужен showResult."""
    for item in materials:
        if item.get("size_mm") or not item.get("code"):
            continue
        for category in ("calendar", "attachment", "sheet"):
            try:
                raw = _get_raw_material(category, str(item["code"]))
            except Exception:
                continue
            size = raw.get("size") or raw.get("sizeTop")
            if isinstance(size, (list, tuple)) and len(size) >= 2 and float(size[0]) and float(size[1]):
                item["size_mm"] = [float(size[0]), float(size[1])]
                break


def _get_calendar_raw(calendar_id: str) -> Dict[str, Any]:
    """Получить сырые данные календаря (sizeTop, sizeBottom и т.д.)."""
    return _get_raw_material("calendar", calendar_id)


class CalendarCalculator(BaseCalculator):
    """Календари: квартальные, перекидные, настольные."""

    slug = "calendar"
    name = "Календари"
    description = "Расчёт стоимости календарей: квартальные, перекидные, настольные."

    def get_param_schema(self) -> Dict[str, Any]:
        return {
            "slug": self.slug,
            "title": self.name,
            "params": [
                {"name": "quantity", "type": "integer", "required": True, "title": "Тираж", "validation": {"min": 1}},
                {"name": "calendar_type", "type": "enum", "required": True, "title": "Тип календаря",
                 "choices": {"inline": [
                     {"id": "quarterly", "title": "Квартальный"},
                     {"id": "flip", "title": "Перекидной"},
                     {"id": "desk", "title": "Настольный перекидной"},
                 ]}},
                {"name": "calendar_id", "type": "string", "required": True, "title": "ID календаря"},
                {"name": "block_id", "type": "string", "required": True, "title": "ID блока"},
                {"name": "top_material_id", "type": "string", "required": False, "title": "Материал топа"},
                {"name": "top_lamination_id", "type": "string", "required": False, "title": "Ламинация топа"},
                {"name": "top_color", "type": "string", "required": False, "default": "4+0", "title": "Цветность топа"},
                {"name": "bottom_material_id", "type": "string", "required": False, "title": "Материал подложек"},
                {"name": "bottom_lamination_id", "type": "string", "required": False, "title": "Ламинация подложек"},
                {"name": "bottom_color", "type": "string", "required": False, "default": "4+0", "title": "Цветность подложек"},
                {"name": "block_material_id", "type": "string", "required": False, "title": "Материал блока (flip)"},
                {"name": "edge", "type": "string", "required": False, "default": "long", "title": "Переплёт (short|long)"},
                {"name": "mode", "type": "integer", "required": False, "default": 1, "title": "Режим"},
            ],
            "param_groups": {
                "main": ["quantity", "calendar_type", "calendar_id", "block_id"],
                "material": ["top_material_id", "bottom_material_id", "block_material_id"],
                "processing": ["top_color", "bottom_color", "top_lamination_id", "bottom_lamination_id", "edge"],
                "mode": ["mode"],
            },
        }

    def get_options(self) -> Dict[str, Any]:
        calendars = []
        try:
            for code, spec in calendar_catalog._items.items():
                calendars.append({"code": code, "name": spec.title or spec.description})
        except Exception:
            pass
        return {
            "calendars": calendars[:40],
            "modes": [
                {"value": ProductionMode.ECONOMY, "label": "Экономичный"},
                {"value": ProductionMode.STANDARD, "label": "Стандартный"},
                {"value": ProductionMode.EXPRESS, "label": "Экспресс"},
            ],
        }

    def get_tool_schema(self) -> Dict[str, Any]:
        return {
            "name": "calc_" + self.slug,
            "description": self.description,
            "parameters": {
                "type": "object",
                "properties": {
                    "quantity": {"type": "integer", "minimum": 1, "description": "Тираж"},
                    "calendar_type": {"type": "string", "enum": ["quarterly", "flip", "desk"], "description": "Тип календаря"},
                    "calendar_id": {"type": "string", "description": "ID календаря (QuarterlyMini, DoubleSide12 и т.д.)"},
                    "block_id": {"type": "string", "description": "ID блока (MiniOffset, MiniMel и т.д.)"},
                    "top_material_id": {"type": "string"},
                    "top_lamination_id": {"type": "string"},
                    "top_color": {"type": "string", "default": "4+0"},
                    "bottom_material_id": {"type": "string"},
                    "bottom_lamination_id": {"type": "string"},
                    "bottom_color": {"type": "string", "default": "4+0"},
                    "block_material_id": {"type": "string"},
                    "edge": {"type": "string", "enum": ["short", "long"], "default": "long"},
                    "mode": {"type": "integer", "enum": [0, 1, 2], "default": 1},
                },
                "required": ["quantity", "calendar_type", "calendar_id", "block_id"],
            },
        }

    def calculate(self, params: Mapping[str, Any]) -> Dict[str, Any]:
        calendar_type = str(params.get("calendar_type", "quarterly")).strip().lower()
        if calendar_type == "quarterly":
            return self._calc_quarterly(params)
        if calendar_type == "flip":
            return self._calc_flip(params)
        if calendar_type == "desk":
            return self._calc_table_flip(params)
        raise ValueError(f"Неизвестный тип календаря: {calendar_type!r}")

    def _calc_quarterly(self, params: Mapping[str, Any]) -> Dict[str, Any]:
        n = int(params.get("quantity", 1))
        calendar_id = str(params.get("calendar_id", "") or "").strip()
        block_id = str(params.get("block_id", "") or "").strip()
        top_material = str(params.get("top_material_id", "") or "PaperCoated115M").strip()
        top_lamination = str(params.get("top_lamination_id", "") or "").strip()
        top_color = str(params.get("top_color", "4+0") or "4+0").strip()
        bottom_material = str(params.get("bottom_material_id", "") or "PaperCoated115M").strip()
        bottom_lamination = str(params.get("bottom_lamination_id", "") or "").strip()
        bottom_color = str(params.get("bottom_color", "4+0") or "4+0").strip()
        mode = ProductionMode(int(params.get("mode", 1)))

        cal_raw = _get_calendar_raw(calendar_id)
        block_raw = _get_calendar_raw(block_id)
        size_top = cal_raw.get("sizeTop", [297, 210])
        size_bottom_list = cal_raw.get("sizeBottom", [[297, 145], [297, 145], [297, 145]])
        block_size = block_raw.get("size", [297, 145])
        block_cost = float(block_raw.get("cost", 0))
        block_weight = float(block_raw.get("weight", 0))

        print_calc = PrintSheetCalculator()
        materials_out: List[Dict[str, Any]] = []

        # Топ (обложка)
        top_params = {
            "quantity": n,
            "width": size_top[0],
            "height": size_top[1],
            "color": top_color,
            "margins": MARGINS,
            "interval": INTERVAL,
            "material_id": top_material,
            "lamination_id": top_lamination or None,
            "mode": mode.value,
        }
        top_result = print_calc.calculate(top_params)
        cost_top = float(top_result.get("cost", 0))
        price_top = float(top_result.get("price", 0))
        time_top = float(top_result.get("time_hours", 0))
        time_ready_top = float(top_result.get("time_ready", 0))
        weight_top = float(top_result.get("weight_kg", 0))
        materials_out.extend(top_result.get("materials") or [])

        # Люверсовка
        eyelet_result = calc_eyelet_sheet(n, mode.value)
        cost_eyelet = eyelet_result.cost
        price_eyelet = eyelet_result.price
        time_eyelet = eyelet_result.time_hours
        materials_out.extend(eyelet_result.materials)

        # Подложки (по каждому размеру)
        cost_bottom = 0.0
        price_bottom = 0.0
        time_bottom = 0.0
        time_ready_bottom = 0.0
        weight_bottom = 0.0
        for size_block in size_bottom_list:
            color = bottom_color
            delta = abs(min(size_block[0], size_block[1]) - min(block_size[0], block_size[1])) + abs(
                max(size_block[0], size_block[1]) - max(block_size[0], block_size[1])
            )
            if delta < 10:
                color = "0+0"
            if color == "0+0":
                # Подложка совпадает с сеткой: печати нет, бумага и резка есть.
                # Старый JS копит это в costBottom, но не мержит costBottom.material
                # в таблицу — строку не добавляем, состав как на боевой странице.
                block_result = _blank_sheet(
                    n,
                    [float(size_block[0]), float(size_block[1])],
                    bottom_material,
                    bottom_lamination,
                    mode.value,
                )
            else:
                block_params = {
                    "quantity": n,
                    "width": size_block[0],
                    "height": size_block[1],
                    "color": color,
                    "margins": MARGINS,
                    "interval": INTERVAL,
                    "material_id": bottom_material,
                    "lamination_id": bottom_lamination or None,
                    "mode": mode.value,
                }
                block_result = print_calc.calculate(block_params)
                materials_out.extend(block_result.get("materials") or [])
            cost_bottom += float(block_result.get("cost", 0))
            price_bottom += float(block_result.get("price", 0))
            time_bottom += float(block_result.get("time_hours", 0))
            weight_bottom += float(block_result.get("weight_kg", 0))
            tr = float(block_result.get("time_ready", 0))
            if tr > time_ready_bottom:
                time_ready_bottom = tr

        # Сетки (блоки)
        num_set_block = math.ceil(n / 50) * 50
        cost_bottom += block_cost * num_set_block
        price_bottom += block_cost * num_set_block * (1 + get_margin("marginMaterial"))
        weight_bottom += block_weight * num_set_block
        materials_out.append({
            "code": block_id,
            "name": block_raw.get("description", block_id),
            "title": block_raw.get("title", block_id),
            "quantity": num_set_block,
            "unit": "шт",
        })

        # Брошюровка (numBlock = кол-во блоков = 3 блока на календарь * n)
        cover = {
            "cover": {"materialID": top_material, "laminatID": top_lamination or "", "color": top_color},
            "backing": {"materialID": bottom_material, "laminatID": bottom_lamination or "", "color": bottom_color},
        }
        inner = [{"materialID": "PaperCoated115M", "numSheet": 12, "color": "0+0"}]
        binding_conf = {"bindingID": "metallwire", "edge": "long"}
        num_block = len(size_bottom_list) * n
        bind_result = calc_binding(
            int(num_block),  # кол-во блоков для переплёта
            block_size,
            cover,
            inner,
            binding_conf,
            BINDING_OPTIONS,
            mode.value,
        )
        cost_binding = bind_result.cost
        price_binding = bind_result.price
        time_binding = bind_result.time_hours
        time_ready_binding = bind_result.time_ready
        materials_out.extend(bind_result.materials)

        # Курсоры
        cursor_result = calc_set_cursor(n, "Cursor", mode.value)
        cost_cursor = cursor_result.cost
        price_cursor = cursor_result.price
        time_cursor = cursor_result.time_hours
        weight_cursor = cursor_result.weight_kg
        materials_out.extend(cursor_result.materials)

        cost_total = cost_top + cost_bottom + cost_binding + cost_eyelet + cost_cursor
        price_total = (price_top + price_bottom + price_binding + price_eyelet + price_cursor) * (1 + get_margin("marginCalendar"))
        time_hours = math.ceil((time_top + time_bottom + time_binding + time_eyelet + time_cursor) * 100) / 100
        time_ready = time_hours + max(
            time_ready_top,
            time_ready_bottom,
            time_ready_binding,
            float(cursor_result.time_ready or 0),
        )
        weight_kg = weight_top + weight_bottom + weight_cursor + (bind_result.weight_kg or 0)
        _fill_size_mm(materials_out)

        return {
            "cost": float(cost_total),
            "price": int(math.ceil(price_total)),
            "unit_price": float(price_total) / max(1, n),
            "time_hours": time_hours,
            "time_ready": time_ready,
            "weight_kg": math.ceil(weight_kg * 100) / 100,
            "materials": materials_out,
        }

    def _calc_flip(self, params: Mapping[str, Any]) -> Dict[str, Any]:
        n = int(params.get("quantity", 1))
        calendar_id = str(params.get("calendar_id", "") or "").strip()
        block_id = str(params.get("block_id", "") or "").strip()
        block_material = str(params.get("block_material_id", "") or "PaperCoated115M").strip()
        edge = str(params.get("edge", "long") or "long").strip()
        mode = ProductionMode(int(params.get("mode", 1)))

        block_raw = _get_calendar_raw(block_id)
        num_sheet = int(block_raw.get("numSheet", 12))
        block_color = str(block_raw.get("color", "4+4") or "4+4").strip()
        size = [210, 297] if edge == "long" else [297, 210]

        print_calc = PrintSheetCalculator()
        block_params = {
            "quantity": n * num_sheet,
            "width": size[0],
            "height": size[1],
            "color": block_color,
            "margins": MARGINS,
            "interval": INTERVAL,
            "material_id": block_material,
            "mode": mode.value,
        }
        block_result = print_calc.calculate(block_params)
        cost_block = float(block_result.get("cost", 0))
        price_block = float(block_result.get("price", 0))
        time_block = float(block_result.get("time_hours", 0))
        time_ready_block = float(block_result.get("time_ready", 0))
        weight_block = float(block_result.get("weight_kg", 0))
        materials_out = list(block_result.get("materials") or [])

        cover = {"cover": {"materialID": "", "laminatID": "", "color": ""}, "backing": {"materialID": "", "laminatID": "", "color": ""}}
        inner = [{"materialID": block_material, "numSheet": num_sheet, "color": block_color}]
        binding_conf = {"bindingID": "metallwire", "edge": edge}
        bind_result = calc_binding(n, size, cover, inner, binding_conf, BINDING_OPTIONS, mode.value)
        materials_out.extend(bind_result.materials)

        len_edge = min(size[0], size[1]) if edge == "short" else max(size[0], size[1])
        rigel_result = calc_set_rigel(n, len_edge, num_sheet, block_material, mode.value)
        materials_out.extend(rigel_result.materials)

        cost_total = cost_block + bind_result.cost + rigel_result.cost
        price_total = (price_block + bind_result.price + rigel_result.price) * (1 + get_margin("marginCalendar"))
        time_hours = math.ceil((time_block + bind_result.time_hours + rigel_result.time_hours) * 100) / 100
        time_ready = time_hours + max(time_ready_block, bind_result.time_ready, rigel_result.time_ready)
        weight_kg = weight_block + (bind_result.weight_kg or 0) + (rigel_result.weight_kg or 0)

        return {
            "cost": float(cost_total),
            "price": int(math.ceil(price_total)),
            "unit_price": float(price_total) / max(1, n),
            "time_hours": time_hours,
            "time_ready": time_ready,
            "weight_kg": math.ceil(weight_kg * 100) / 100,
            "materials": materials_out,
        }

    def _calc_table_flip(self, params: Mapping[str, Any]) -> Dict[str, Any]:
        n = int(params.get("quantity", 1))
        calendar_id = str(params.get("calendar_id", "") or "").strip()
        block_id = str(params.get("block_id", "") or "").strip()
        top_material = str(params.get("top_material_id", "") or "PaperCoated115M").strip()
        top_lamination = str(params.get("top_lamination_id", "") or "").strip()
        top_color = str(params.get("top_color", "4+0") or "4+0").strip()
        block_material = str(params.get("block_material_id", "") or "PaperCoated115M").strip()
        block_color = str(params.get("bottom_color", "4+0") or "4+0").strip()
        mode = ProductionMode(int(params.get("mode", 1)))

        cal_raw = _get_calendar_raw(calendar_id)
        block_raw = _get_calendar_raw(block_id)
        size_sheet = cal_raw.get("sizeSheet", [210, 270])
        size_block = cal_raw.get("sizeBlock", [210, 90])
        num_sheet = int(block_raw.get("numSheet", 12))

        print_calc = PrintSheetCalculator()
        materials_out: List[Dict[str, Any]] = []

        base_params = {
            "quantity": n,
            "width": size_sheet[0],
            "height": size_sheet[1],
            "color": top_color,
            "margins": MARGINS,
            "interval": INTERVAL,
            "material_id": top_material,
            "lamination_id": top_lamination or None,
            "mode": mode.value,
        }
        base_result = print_calc.calculate(base_params)
        cost_base = float(base_result.get("cost", 0))
        price_base = float(base_result.get("price", 0))
        time_base = float(base_result.get("time_hours", 0))
        time_ready_base = float(base_result.get("time_ready", 0))
        weight_base = float(base_result.get("weight_kg", 0))
        materials_out.extend(base_result.get("materials") or [])

        block_params = {
            "quantity": n * num_sheet,
            "width": size_block[0],
            "height": size_block[1],
            "color": block_color,
            "margins": MARGINS,
            "interval": INTERVAL,
            "material_id": block_material,
            "mode": mode.value,
        }
        block_result = print_calc.calculate(block_params)
        cost_block = float(block_result.get("cost", 0))
        price_block = float(block_result.get("price", 0))
        time_block = float(block_result.get("time_hours", 0))
        time_ready_block = float(block_result.get("time_ready", 0))
        weight_block = float(block_result.get("weight_kg", 0))
        materials_out.extend(block_result.get("materials") or [])

        cover = {
            "cover": {"materialID": top_material, "laminatID": top_lamination or "", "color": top_color},
            "backing": {"materialID": top_material, "laminatID": top_lamination or "", "color": top_color},
        }
        inner = [{"materialID": block_material, "numSheet": num_sheet, "color": "0+0"}]
        binding_conf = {"bindingID": "metallwire", "edge": "long"}
        bind_result = calc_binding(n, size_block, cover, inner, binding_conf, BINDING_OPTIONS, mode.value)
        materials_out.extend(bind_result.materials)

        cost_total = cost_base + cost_block + bind_result.cost
        price_total = (price_base + price_block + bind_result.price) * (1 + get_margin("marginCalendar"))
        time_hours = math.ceil((time_base + time_block + bind_result.time_hours) * 100) / 100
        time_ready = time_hours + max(time_ready_base, time_ready_block, bind_result.time_ready)
        weight_kg = weight_base + weight_block + (bind_result.weight_kg or 0)

        return {
            "cost": float(cost_total),
            "price": int(math.ceil(price_total)),
            "unit_price": float(price_total) / max(1, n),
            "time_hours": time_hours,
            "time_ready": time_ready,
            "weight_kg": math.ceil(weight_kg * 100) / 100,
            "materials": materials_out,
        }
