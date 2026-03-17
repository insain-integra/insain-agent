"""
Калькулятор наклеек.

Перенесено из js_legacy/calc/calcSticker.js.
Комбинирует: плоттерная резка + опционально печать + ламинация + монтажная плёнка.
"""

from __future__ import annotations

import math
from typing import Any, Dict, List, Mapping, Optional

from calculators.base import BaseCalculator, ProductionMode
from calculators.cut_plotter import CutPlotterCalculator
from calculators.lamination import LaminationCalculator
from calculators.print_laser import PrintLaserCalculator
from common.helpers import calc_weight
from common.markups import BASE_TIME_READY, MARGIN_MATERIAL, get_margin
from common.process_tools import calc_manual_roll
from equipment import plotter as plotter_catalog
from materials import get_material

PLOTTER_CODE = "GraphtecCE5000-60"
PRINTER_CODE = "KMBizhubC220"
MOUNTING_FILM_ID = "LGChemLC2000H"
SHEET_CATEGORIES = ("sheet", "roll")


def _find_material(material_id: str):
    """Найти материал в sheet или roll."""
    for cat in SHEET_CATEGORIES:
        try:
            return get_material(cat, material_id)
        except (KeyError, Exception):
            continue
    return None


class StickerCalculator(BaseCalculator):
    """Наклейки: плоттерная резка + опционально печать + ламинация + монтажная плёнка."""

    slug = "sticker"
    name = "Наклейки"
    description = "Расчёт наклеек: плоттерная резка + печать + ламинация."

    def get_param_schema(self) -> Dict[str, Any]:
        return {
            "slug": self.slug,
            "title": self.name,
            "params": [
                {
                    "name": "quantity",
                    "type": "integer",
                    "required": True,
                    "title": "Тираж",
                    "description": "Количество наклеек",
                    "validation": {"min": 1, "max": 100000},
                },
                {
                    "name": "width",
                    "type": "number",
                    "required": True,
                    "title": "Ширина (мм)",
                    "description": "Ширина наклейки",
                    "validation": {"min": 10, "max": 1600},
                    "unit": "мм",
                },
                {
                    "name": "height",
                    "type": "number",
                    "required": True,
                    "title": "Высота (мм)",
                    "description": "Высота наклейки",
                    "validation": {"min": 10, "max": 1600},
                    "unit": "мм",
                },
                {
                    "name": "size_item",
                    "type": "number",
                    "required": False,
                    "default": 0,
                    "title": "Размер элемента",
                    "description": "Средний размер элементов для резки (0 = ширина)",
                    "unit": "мм",
                },
                {
                    "name": "density",
                    "type": "number",
                    "required": False,
                    "default": 0,
                    "title": "Плотность заполнения",
                    "description": "0..1",
                    "validation": {"min": 0, "max": 1},
                },
                {
                    "name": "difficulty",
                    "type": "number",
                    "required": False,
                    "default": 1,
                    "title": "Сложность резки",
                    "description": "1..2 — форма без вогнутостей / с пустотами",
                    "validation": {"min": 1, "max": 2},
                },
                {
                    "name": "material_id",
                    "type": "string",
                    "required": True,
                    "title": "Материал",
                    "description": "Код материала из sheet или roll",
                },
                {
                    "name": "color",
                    "type": "string",
                    "required": False,
                    "title": "Печать",
                    "description": "Цветность: 4+0, 1+0 и т.д. Пусто — без печати",
                },
                {
                    "name": "printer_code",
                    "type": "string",
                    "required": False,
                    "title": "Принтер",
                    "description": "Код принтера (по умолчанию KMBizhubC220)",
                },
                {
                    "name": "lamination_id",
                    "type": "string",
                    "required": False,
                    "title": "Ламинация",
                    "description": "Код плёнки ламинации. Пусто — без ламинации",
                },
                {
                    "name": "is_mounting_film",
                    "type": "boolean",
                    "required": False,
                    "default": False,
                    "title": "Монтажная плёнка",
                    "description": "Накатка монтажной плёнки",
                },
                {
                    "name": "mode",
                    "type": "integer",
                    "required": False,
                    "default": int(ProductionMode.STANDARD),
                    "title": "Режим",
                    "description": "0=эконом, 1=стандарт, 2=экспресс",
                    "choices": {
                        "inline": [
                            {"id": 0, "title": "Эконом"},
                            {"id": 1, "title": "Стандарт"},
                            {"id": 2, "title": "Экспресс"},
                        ]
                    },
                },
            ],
            "param_groups": {
                "main": ["quantity", "width", "height"],
                "material": ["material_id"],
                "processing": ["color", "lamination_id", "is_mounting_film"],
                "mode": ["mode"],
            },
        }

    def get_options(self) -> Dict[str, Any]:
        materials = []
        try:
            from materials import ALL_MATERIALS
            for cat in SHEET_CATEGORIES:
                c = ALL_MATERIALS.get(cat)
                if c:
                    materials.extend(c.list_for_frontend())
        except Exception:
            pass
        return {
            "materials": materials[:80],
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
                    "quantity": {"type": "integer", "minimum": 1, "description": "Тираж, шт."},
                    "width": {"type": "number", "minimum": 1, "description": "Ширина, мм"},
                    "height": {"type": "number", "minimum": 1, "description": "Высота, мм"},
                    "size_item": {"type": "number", "description": "Средний размер элемента для резки"},
                    "density": {"type": "number", "description": "Плотность заполнения 0..1"},
                    "difficulty": {"type": "number", "description": "Сложность резки 1..2"},
                    "material_id": {"type": "string", "description": "Код материала"},
                    "color": {"type": "string", "description": "Цветность печати: 4+0, 1+0 и т.д."},
                    "printer_code": {"type": "string"},
                    "lamination_id": {"type": "string"},
                    "is_mounting_film": {"type": "boolean"},
                    "mode": {"type": "integer", "enum": [0, 1, 2]},
                },
                "required": ["quantity", "width", "height", "material_id"],
            },
        }

    def calculate(self, params: Mapping[str, Any]) -> Dict[str, Any]:
        quantity = int(params.get("quantity", 1))
        w = float(params.get("width", 0))
        h = float(params.get("height", 0))
        size = [w, h]
        size_item = float(params.get("size_item", 0) or 0)
        if size_item <= 0:
            size_item = w
        density = float(params.get("density", 0) or 0)
        difficulty = float(params.get("difficulty", 1) or 1)
        material_id = str(params.get("material_id", "") or "").strip()
        color = str(params.get("color", "") or "").strip()
        printer_code = str(params.get("printer_code", "") or PRINTER_CODE).strip() or PRINTER_CODE
        lamination_id = str(params.get("lamination_id", "") or "").strip()
        is_mounting_film = bool(params.get("is_mounting_film", False))
        mode = ProductionMode(int(params.get("mode", 1)))

        material = _find_material(material_id) if material_id else None
        if not material:
            raise ValueError(f"Материал не найден: {material_id!r}")

        # 1. Плоттерная резка
        cut_params = {
            "quantity": quantity,
            "width": w,
            "height": h,
            "material_id": material_id,
            "size_item": size_item,
            "density": density,
            "difficulty": difficulty,
            "mode": mode.value,
        }
        cut_calc = CutPlotterCalculator()
        cut_result = cut_calc.calculate(cut_params)

        cost_cut = float(cut_result.get("cost", 0))
        price_cut = float(cut_result.get("price", 0))
        time_cut = float(cut_result.get("time_hours", 0))
        cut_materials = cut_result.get("materials") or []

        # Расход материала из cut: num_sheet или length_m
        num_sheet: Optional[float] = None
        length_m: Optional[float] = None
        size_sheet: Optional[List[float]] = None
        is_roll = getattr(material, "is_roll", False)

        for m in cut_materials:
            if m.get("code") == material_id:
                qty = m.get("quantity", 0)
                unit = m.get("unit", "")
                if unit == "sheet":
                    num_sheet = float(qty)
                    size_sheet = (material.sizes[0] if material.sizes else [320, 450])[:2]
                else:
                    length_m = float(qty)
                    roll_sizes = material.sizes or [[1000, 0]]
                    first = roll_sizes[0] if isinstance(roll_sizes[0], list) else roll_sizes
                    width_mm = float(first[0]) if first else 1000
                    size_sheet = [width_mm, length_m * 1000] if length_m else [width_mm, 0]
                break

        if num_sheet is None and length_m is None:
            num_sheet = 1
            size_sheet = (material.sizes[0] if material.sizes else [320, 450])[:2]

        # 2. Стоимость материала
        cost_material = 0.0
        if is_roll and length_m is not None:
            roll_sizes = material.sizes or [[1000, 0]]
            first = roll_sizes[0] if isinstance(roll_sizes[0], list) else roll_sizes
            width_mm = float(first[0]) if first else 1000
            area_m2 = (width_mm / 1000.0) * length_m
            cost_per_m2 = float(material.get_cost(area_m2 * quantity))
            length_min = getattr(material, "length_min", 0) or 0
            if length_min > 0:
                num_min = math.ceil(length_m * 1000 / length_min)
                cost_material = cost_per_m2 * num_min * length_min / 1_000_000 * (width_mm / 1000)
            else:
                cost_material = cost_per_m2 * area_m2
        else:
            n = num_sheet or 1
            cost_per_sheet = float(material.get_cost(n))
            cost_material = cost_per_sheet * n

        # 3. Печать (только для листового материала, лазер KMBizhubC220)
        cost_print = 0.0
        price_print = 0.0
        time_print = 0.0
        weight_print = 0.0
        print_materials: List[Dict[str, Any]] = []

        if color and not is_roll and num_sheet and size_sheet:
            print_params = {
                "num_sheet": int(num_sheet),
                "width": size_sheet[0],
                "height": size_sheet[1],
                "color": color,
                "material_id": material_id,
                "printer_code": printer_code,
                "mode": mode.value,
            }
            try:
                print_calc = PrintLaserCalculator()
                print_result = print_calc.calculate(print_params)
                cost_print = float(print_result.get("cost", 0))
                price_print = float(print_result.get("price", 0))
                time_print = float(print_result.get("time_hours", 0))
                weight_print = float(print_result.get("weight_kg", 0))
                print_materials = print_result.get("materials") or []
            except Exception:
                pass

        # 4. Ламинация
        cost_lam = 0.0
        price_lam = 0.0
        time_lam = 0.0
        weight_lam = 0.0
        lam_materials: List[Dict[str, Any]] = []

        if lamination_id:
            lam_quantity = int(num_sheet) if num_sheet else quantity
            lam_w = size_sheet[0] if size_sheet else w
            lam_h = size_sheet[1] if size_sheet and not is_roll else h
            if is_roll and length_m:
                lam_quantity = 1
                lam_w = size_sheet[0] if size_sheet else w
                lam_h = length_m * 1000
            lam_params = {
                "quantity": lam_quantity,
                "width": lam_w,
                "height": lam_h,
                "material_id": lamination_id,
                "double_side": False,
                "mode": mode.value,
            }
            try:
                lam_calc = LaminationCalculator()
                lam_result = lam_calc.calculate(lam_params)
                cost_lam = float(lam_result.get("cost", 0))
                price_lam = float(lam_result.get("price", 0))
                time_lam = float(lam_result.get("time_hours", 0))
                weight_lam = float(lam_result.get("weight_kg", 0))
                lam_materials = lam_result.get("materials") or []
            except Exception:
                pass

        # 5. Монтажная плёнка
        cost_film = 0.0
        price_film = 0.0
        time_film = 0.0
        weight_film = 0.0
        film_materials: List[Dict[str, Any]] = []

        if is_mounting_film:
            try:
                film = get_material("roll", MOUNTING_FILM_ID)
                roll_result = calc_manual_roll(quantity, size, {}, mode.value)
                sum_area = quantity * (w + 20) * (h + 20) / 1_000_000
                cost_film_mat = float(film.get_cost(1)) * sum_area
                cost_film = cost_film_mat + roll_result.cost
                price_film = cost_film_mat * (1 + MARGIN_MATERIAL) + roll_result.price
                time_film = roll_result.time_hours
                weight_film = calc_weight(
                    quantity=quantity,
                    density=float(film.density or 0),
                    thickness=float(film.thickness or 80) / 1000,
                    size=size,
                    density_unit=getattr(film, "density_unit", "гм2") or "гм2",
                )
                film_width = (film.sizes[0][0] if film.sizes else 1000)
                film_materials = [{
                    "code": MOUNTING_FILM_ID,
                    "name": film.description,
                    "title": film.title,
                    "quantity": round(sum_area / (film_width / 1000) * 1000, 4),
                    "unit": "m",
                }]
            except Exception:
                pass

        # 6. Итог
        cost_total = cost_material + cost_cut + cost_print + cost_lam + cost_film
        margin_sticker = get_margin("marginSticker")
        price_total = (
            cost_material * (1 + MARGIN_MATERIAL)
            + (price_cut + price_print + price_lam + price_film) * (1 + margin_sticker)
        )
        price_total = math.ceil(price_total)

        time_hours = math.ceil((time_cut + time_print + time_lam + time_film) * 100) / 100.0
        try:
            plotter = plotter_catalog.get(PLOTTER_CODE)
            base_ready = getattr(plotter, "base_time_ready", None) or BASE_TIME_READY
        except (KeyError, AttributeError):
            base_ready = BASE_TIME_READY
        idx = max(0, min(len(base_ready) - 1, mode.value))
        time_ready = time_hours + float(base_ready[idx])

        weight_kg = calc_weight(
            quantity=quantity,
            density=float(material.density or 0),
            thickness=float(material.thickness or 0),
            size=size,
            density_unit=getattr(material, "density_unit", "гм2") or "гм2",
        )
        weight_kg += weight_lam + weight_film
        weight_kg = math.ceil(weight_kg * 100) / 100.0

        # Материалы: основной + из cut + print + lam + film
        materials_out: List[Dict[str, Any]] = []
        seen = set()
        for m in cut_materials + print_materials + lam_materials + film_materials:
            code = m.get("code", "")
            if code and code not in seen:
                seen.add(code)
                materials_out.append({
                    "code": code,
                    "name": m.get("name", m.get("description", "")),
                    "title": m.get("title", m.get("name", "")),
                    "quantity": m.get("quantity"),
                    "unit": m.get("unit", "шт"),
                })

        return {
            "cost": float(cost_total),
            "price": float(price_total),
            "unit_price": float(price_total) / max(1, quantity),
            "time_hours": time_hours,
            "time_ready": time_ready,
            "weight_kg": weight_kg,
            "materials": materials_out,
        }
