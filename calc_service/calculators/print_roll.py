"""
Калькулятор РУЛОННОЙ ПЕЧАТИ.

Мигрировано из js_legacy/calc/calcPrintRoll.js.
Печать на рулонном материале с постпечатной обработкой:
резка в край, проклейка, люверсовка, ламинация.
Внутри вызывает print_wide для расчёта самой печати.
"""

from __future__ import annotations

import math
from typing import Any, Dict, List, Mapping, Optional

from calculators.base import BaseCalculator, ProductionMode
from calculators.print_wide import PrintWideCalculator
from common.helpers import calc_weight, find_in_table
from common.layout import layout_on_roll
from common.markups import (
    BASE_TIME_READY,
    MARGIN_MATERIAL,
    MARGIN_OPERATION,
    get_margin,
)
from common.process_tools import (
    calc_cutting_edge,
    calc_eyelet,
    calc_gluing_banner,
)
from equipment import printer as printer_catalog
from materials import roll as roll_catalog

DEFAULT_PRINTER = "Technojet160ECO"


class PrintRollCalculator(BaseCalculator):
    """Рулонная печать (баннеры, постеры, плёнки) с постпечатной обработкой."""

    slug = "print_roll"
    name = "Рулонная печать"
    description = (
        "Расчёт широкоформатной рулонной печати с обработкой: "
        "резка, проклейка, люверсовка, ламинация."
    )

    def get_options(self) -> Dict[str, Any]:
        materials = roll_catalog.list_for_frontend()
        printers = []
        try:
            for code, spec in printer_catalog._items.items():
                if spec.cost_print_m2 > 0 or spec.meter_per_hour > 0:
                    printers.append({"code": code, "name": spec.name})
        except Exception:
            printers = [{"code": DEFAULT_PRINTER, "name": "Широкоформатный принтер"}]
        return {
            "materials": materials,
            "printers": printers,
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
                    "quantity": {"type": "integer", "minimum": 1, "description": "Количество изделий"},
                    "width": {"type": "number", "minimum": 1, "description": "Ширина изделия, мм"},
                    "height": {"type": "number", "minimum": 1, "description": "Высота изделия, мм"},
                    "material_id": {"type": "string", "description": "Код материала (из каталога roll)"},
                    "printer_code": {"type": "string"},
                    "is_cutting": {
                        "type": "array", "items": {"type": "integer"},
                        "description": "Резка в край [top, right, bottom, left]: 0/1",
                    },
                    "is_gluing": {
                        "type": "array", "items": {"type": "integer"},
                        "description": "Проклейка края [top, right, bottom, left]: 0/1",
                    },
                    "is_pocket": {
                        "type": "array", "items": {"type": "integer"},
                        "description": "Карман [top, right, bottom, left]: 0/1",
                    },
                    "is_eyelet": {
                        "type": "array", "items": {"type": "number"},
                        "description": "Люверсовка: шаг в мм по каждой стороне [top, right, bottom, left]. 0 = нет.",
                    },
                    "is_joining": {"type": "boolean", "default": False, "description": "Стыковка полотен"},
                    "is_lamination": {"type": "boolean", "default": False, "description": "Ламинация"},
                    "mode": {"type": "integer", "enum": [0, 1, 2], "default": 1},
                },
                "required": ["quantity", "width", "height", "material_id"],
            },
        }

    def get_param_schema(self) -> Dict[str, Any]:
        return {
            "slug": self.slug,
            "title": self.name,
            "params": [
                {"name": "quantity", "type": "integer", "required": True, "title": "Тираж", "validation": {"min": 1}},
                {"name": "width", "type": "number", "required": True, "title": "Ширина (мм)", "unit": "мм"},
                {"name": "height", "type": "number", "required": True, "title": "Высота (мм)", "unit": "мм"},
                {"name": "material_id", "type": "enum_cascading", "required": True, "title": "Материал", "choices": {"source": "materials:roll"}},
                {"name": "printer_code", "type": "enum", "required": False, "title": "Принтер", "default": DEFAULT_PRINTER},
                {"name": "is_cutting", "type": "string", "required": False, "title": "Резка в край"},
                {"name": "is_gluing", "type": "string", "required": False, "title": "Проклейка края"},
                {"name": "is_pocket", "type": "string", "required": False, "title": "Карман"},
                {"name": "is_eyelet", "type": "string", "required": False, "title": "Люверсовка"},
                {"name": "is_joining", "type": "boolean", "required": False, "default": False, "title": "Стыковка"},
                {"name": "is_lamination", "type": "boolean", "required": False, "default": False, "title": "Ламинация"},
                {"name": "mode", "type": "enum", "required": False, "default": 1, "title": "Режим",
                 "choices": {"inline": [{"id": 0, "title": "Эконом"}, {"id": 1, "title": "Стандарт"}, {"id": 2, "title": "Экспресс"}]}},
            ],
            "param_groups": {
                "main": ["quantity", "width", "height"],
                "material": ["material_id"],
                "equipment": ["printer_code"],
                "options": ["is_cutting", "is_gluing", "is_pocket", "is_eyelet", "is_joining", "is_lamination"],
                "mode": ["mode"],
            },
        }

    def calculate(self, params: Mapping[str, Any]) -> Dict[str, Any]:
        n = int(params.get("quantity", 1))
        width = float(params.get("width", 0))
        height = float(params.get("height", 0))
        size = [width, height]
        material_id = str(params.get("material_id", "")).strip()
        printer_code = str(params.get("printer_code", "") or DEFAULT_PRINTER).strip() or DEFAULT_PRINTER
        mode = ProductionMode(int(params.get("mode", 1)))

        is_cutting = self._parse_edge(params.get("is_cutting"))
        is_gluing = self._parse_edge(params.get("is_gluing"))
        is_pocket = self._parse_edge(params.get("is_pocket"))
        is_eyelet = self._parse_edge_float(params.get("is_eyelet"))
        is_joining = bool(params.get("is_joining", False))
        is_lamination = bool(params.get("is_lamination", False))

        try:
            printer = printer_catalog.get(printer_code)
        except KeyError:
            try:
                printer = printer_catalog.get(DEFAULT_PRINTER)
            except KeyError:
                return self._empty(mode)

        try:
            material = roll_catalog.get(material_id)
        except KeyError:
            return self._empty(mode)

        margins = list(printer.margins or [200, 20, 50, 20])
        if len(margins) < 4:
            margins = [200, 20, 50, 20]

        # Подбор оптимального размера рулона
        all_sizes = material.sizes if material.sizes else [[1700, 0]]
        max_printer = printer.max_size or [1700, 0]

        best_vol = -1.0
        best_size_material = all_sizes[0]
        best_len_material = 0.0
        best_size_print = [0.0, 0.0]

        for sz in all_sizes:
            sz_w = float(sz[0]) if len(sz) > 0 else 0
            sz_h = float(sz[1]) if len(sz) > 1 else 0

            # Проверка: помещается ли рулон в принтер
            if sz_h == 0:
                if sz_w > max_printer[0]:
                    continue
            else:
                check = layout_on_roll(1, [sz_w, sz_h], max_printer)
                if check["length"] == 0:
                    continue

            usable_w = sz_w - margins[1] - margins[3]
            if usable_w <= 0:
                continue

            roll = layout_on_roll(n, size, [usable_w, 0])
            len_mat = roll["length"]

            if is_joining and len_mat == 0:
                max_side = max(size[0], size[1])
                min_side = min(size[0], size[1])
                num_bonds = math.ceil(max_side / usable_w)
                len_mat = n * num_bonds * min_side

            if len_mat > 0:
                vol = (len_mat + margins[0] + margins[2]) * sz_w / 1_000_000
                if best_vol < 0 or vol < best_vol:
                    best_vol = vol
                    best_size_material = [sz_w, sz_h]
                    best_len_material = len_mat
                    best_size_print = [usable_w, len_mat]

        if best_len_material <= 0:
            raise ValueError("Изделие не помещается на материал")

        # Расчёт печати через print_wide
        wide_calc = PrintWideCalculator()
        cost_print_result = wide_calc.calculate({
            "quantity": n,
            "width": best_size_print[0],
            "height": best_size_print[1],
            "material_id": material_id,
            "printer_code": printer_code,
            "mode": mode.value,
        })

        # Расход материала
        material_cost_raw = float(material.get_cost(1))
        defects = printer.get_defect_rate(float(n))
        if mode.value >= 2:
            defects += defects * (mode.value - 1)

        len_with_margins = best_len_material + margins[0] + margins[2]
        len_with_defects = len_with_margins * (1 + defects)

        min_length = getattr(material, "length_min", 0) or 0
        if min_length > 0 and len_with_defects < min_length:
            len_with_defects = min_length

        cost_material = material_cost_raw * len_with_defects * best_size_material[0] / 1_000_000

        # Постпечатная обработка
        cost_opt = 0.0
        price_opt = 0.0
        time_opt = 0.0
        weight_opt = 0.0
        materials_extra: List[Dict[str, Any]] = []

        if is_cutting and any(v > 0 for v in is_cutting):
            r = calc_cutting_edge(n, size, is_cutting, mode.value)
            cost_opt += r.cost
            price_opt += r.price
            time_opt += r.time_hours

        if is_pocket and any(v > 0 for v in is_pocket):
            r = calc_gluing_banner(n, size, is_pocket, mode.value)
            cost_opt += r.cost
            price_opt += r.price
            time_opt += r.time_hours
            materials_extra.extend(r.materials)

        if is_gluing and any(v > 0 for v in is_gluing):
            r = calc_gluing_banner(n, size, is_gluing, mode.value)
            cost_opt += r.cost
            price_opt += r.price
            time_opt += r.time_hours
            materials_extra.extend(r.materials)

        if is_eyelet and any(v > 0 for v in is_eyelet):
            r = calc_eyelet(n, size, is_eyelet, mode.value)
            cost_opt += r.cost
            price_opt += r.price
            time_opt += r.time_hours
            materials_extra.extend(r.materials)
            # Автоматическая проклейка по краям с люверсами
            glue_edge = [1 if v > 0 else 0 for v in is_eyelet]
            rg = calc_gluing_banner(n, size, glue_edge, mode.value)
            cost_opt += rg.cost
            price_opt += rg.price
            time_opt += rg.time_hours
            materials_extra.extend(rg.materials)

        # Итоговый расчёт
        cost_print_val = float(cost_print_result.get("cost", 0))
        price_print_val = float(cost_print_result.get("price", 0))
        time_print_val = float(cost_print_result.get("time_hours", 0))
        time_ready_print = float(cost_print_result.get("time_ready", 0))

        margin_roll = get_margin("marginPrintRoll")
        cost = math.ceil(cost_print_val + cost_material + cost_opt)
        price = math.ceil(
            cost_material * (1 + MARGIN_MATERIAL + margin_roll)
            + (price_print_val + price_opt) * (1 + margin_roll)
        )

        time_hours = math.ceil((time_opt + time_print_val) * 100) / 100.0
        time_ready = time_hours + max(0, time_ready_print)

        weight_kg = calc_weight(
            quantity=n,
            density=getattr(material, "density", 0) or 0,
            thickness=getattr(material, "thickness", 0) or 0,
            size=size,
            density_unit=getattr(material, "density_unit", "гм2") or "гм2",
        )
        weight_kg = math.ceil((weight_kg + weight_opt) * 100) / 100.0

        materials_out: List[Dict[str, Any]] = [{
            "code": material.code,
            "name": material.description,
            "title": material.title,
            "quantity": round(len_with_defects / 1000.0, 2),
            "unit": "м",
        }]
        materials_out.extend(materials_extra)

        return {
            "cost": float(cost),
            "price": float(price),
            "unit_price": float(price) / max(1, n),
            "time_hours": time_hours,
            "time_ready": time_ready,
            "weight_kg": weight_kg,
            "materials": materials_out,
        }

    # ── helpers ────────────────────────────────────────────────────────

    @staticmethod
    def _parse_edge(val) -> Optional[List[int]]:
        if val is None or val is False:
            return None
        if isinstance(val, (list, tuple)):
            return [int(v) for v in val]
        return None

    @staticmethod
    def _parse_edge_float(val) -> Optional[List[float]]:
        if val is None or val is False:
            return None
        if isinstance(val, (list, tuple)):
            return [float(v) for v in val]
        return None

    def _empty(self, mode: ProductionMode) -> Dict[str, Any]:
        btr = BASE_TIME_READY
        idx = max(0, min(len(btr) - 1, mode.value))
        return {
            "cost": 0.0, "price": 0.0, "unit_price": 0.0,
            "time_hours": 0.0, "time_ready": float(btr[idx]),
            "weight_kg": 0.0, "materials": [],
        }
