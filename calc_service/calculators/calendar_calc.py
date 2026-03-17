"""
Калькулятор календарей.

Мигрировано из js_legacy/calc/calcCalendar.js.
Типы: квартальные (calcCalendarQuarterly), перекидные (calcCalendarFlip),
настольные перекидные (calcCalendarTableFlip).
"""

from __future__ import annotations

import math
from typing import Any, Dict, List, Mapping

from calculators.base import BaseCalculator, ProductionMode
from calculators.print_sheet import PrintSheetCalculator
from common.markups import BASE_TIME_READY, get_margin, get_time_ready
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
            cost_bottom += float(block_result.get("cost", 0))
            price_bottom += float(block_result.get("price", 0))
            time_bottom += float(block_result.get("time_hours", 0))
            weight_bottom += float(block_result.get("weight_kg", 0))
            tr = float(block_result.get("time_ready", 0))
            if tr > time_ready_bottom:
                time_ready_bottom = tr
            materials_out.extend(block_result.get("materials") or [])

        # Сетки (блоки)
        num_set_block = math.ceil(n / 50) * 50
        cost_bottom += block_cost * num_set_block
        price_bottom += block_cost * num_set_block * (1 + 0.66)  # marginMaterial
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
        time_ready = time_hours + max(time_ready_top, time_ready_bottom, time_ready_binding)
        weight_kg = weight_top + weight_bottom + weight_cursor + (bind_result.weight_kg or 0)

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
