"""
Калькулятор БЛОКНОТОВ.

Мигрировано из js_legacy/calc/calcNotebook.js.
Обложка (печать) + внутренний блок (печать) + переплёт (пружина или скобы).
"""

from __future__ import annotations

import math
from typing import Any, Dict, List, Mapping, Optional

from calculators.base import BaseCalculator, ProductionMode
from calculators.cut_guillotine import CutGuillotineCalculator
from calculators.lamination import LAMINATOR_CODE, LaminationCalculator
from calculators.print_offset import PrintOffsetCalculator
from calculators.print_sheet import PRINTER_CODE, PrintSheetCalculator
from common.helpers import calc_weight
from common.layout import layout_on_sheet
from common.markups import MARGIN_MATERIAL, get_margin, get_time_ready
from common.process_tools import calc_binding, calc_set_staples
from equipment import laminator as laminator_catalog
from equipment import printer as printer_catalog
from materials import get_material
from materials import sheet as sheet_catalog

# Размер A4 для расчёта раскладки внутреннего блока
SIZE_A4 = [320, 225]


def _merge_materials(a: List[Dict[str, Any]], b: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Объединить списки материалов (суммировать quantity по code)."""
    by_code: Dict[str, Dict[str, Any]] = {}
    for m in a + b:
        code = m.get("code", "")
        if code in by_code:
            q = by_code[code].get("quantity", 0)
            by_code[code]["quantity"] = q + m.get("quantity", 0)
        else:
            by_code[code] = dict(m)
    return list(by_code.values())


def _ensure_size_mm(materials: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Дописать size_mm из каталога, если расчёт переплёта его не положил."""
    out: List[Dict[str, Any]] = []
    for raw in materials:
        item = dict(raw)
        if not item.get("size_mm") and item.get("code"):
            for category in ("attachment", "sheet"):
                try:
                    spec = get_material(category, str(item["code"]))
                except Exception:
                    continue
                if spec.sizes:
                    item["size_mm"] = [float(x) for x in spec.sizes[0]]
                    break
        out.append(item)
    return out


def _combine_jobs(parts: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Сложить две стороны обложки: время готовности — максимум, как в calcNotebook."""
    cost = price = time_hours = weight = 0.0
    time_ready = 0.0
    materials: List[Dict[str, Any]] = []
    for part in parts:
        cost += float(part.get("cost") or 0)
        price += float(part.get("price") or 0)
        time_hours += float(part.get("time_hours") or 0)
        weight += float(part.get("weight_kg") or 0)
        time_ready = max(time_ready, float(part.get("time_ready") or 0))
        materials = _merge_materials(materials, part.get("materials") or [])
    return {
        "cost": cost,
        "price": price,
        "time_hours": time_hours,
        "time_ready": time_ready,
        "weight_kg": weight,
        "materials": materials,
    }


def _blank_sheet(
    quantity: int,
    size: List[float],
    material_id: str,
    lamination_id: Optional[str],
    mode: int,
) -> Dict[str, Any]:
    """Лист без печати (цвет 0+0): бумага, резка и ламинация.

    PrintSheetCalculator на 0+0 отдаёт пустой результат. Подложка и пустой блок
    блокнота этот лист всё равно тратят — как calcPrintSheet при color == '0+0'.
    """
    material = sheet_catalog.get(material_id)
    printer = printer_catalog.get(PRINTER_CODE)
    size_sheet = [float(x) for x in (material.sizes[0] if material.sizes else [320, 450])]
    max_printer = list(printer.max_size or [320, 450])
    # JS: при color == '0+0' вылеты принтера не добавляются, интервал обнуляется.
    layout_sheet = layout_on_sheet(size, size_sheet, [0, 0, 0, 0], 0.0)
    if layout_sheet["num"] <= 0:
        raise ValueError("Изделие не помещается на лист")
    num_sheet = math.ceil(quantity / layout_sheet["num"])
    num_sheet_to_print = num_sheet

    lam_id = (lamination_id or "").strip()
    if lam_id:
        try:
            laminator = laminator_catalog.get(LAMINATOR_CODE)
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
    lamination_result: Optional[Dict[str, Any]] = None
    if lam_id:
        try:
            lam_material = get_material("laminat", lam_id)
            first_size = lam_material.sizes[0] if lam_material.sizes else [0, 0]
            lam_h = float(first_size[1]) if len(first_size) > 1 else 0.0
            if lam_h == 0:
                lam_quantity, lam_width, lam_height = num_sheet, size_sheet[0], size_sheet[1]
            else:
                lam_quantity, lam_width, lam_height = quantity, size[0], size[1]
            lamination_result = LaminationCalculator().calculate(
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


class NotebookCalculator(BaseCalculator):
    """Блокноты: обложка + внутренний блок + переплёт."""

    slug = "notebook"
    name = "Блокноты"
    description = "Расчёт блокнотов: печать обложки и внутреннего блока, переплёт на пружину или скобами."

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
                    "description": "Количество блокнотов",
                    "validation": {"min": 1, "max": 10000},
                },
                {
                    "name": "width_mm",
                    "type": "number",
                    "required": True,
                    "title": "Ширина (мм)",
                    "description": "Ширина изделия",
                    "validation": {"min": 50, "max": 400},
                    "unit": "мм",
                },
                {
                    "name": "height_mm",
                    "type": "number",
                    "required": True,
                    "title": "Высота (мм)",
                    "description": "Высота изделия",
                    "validation": {"min": 50, "max": 400},
                    "unit": "мм",
                },
                {
                    "name": "cover_material_id",
                    "type": "string",
                    "required": True,
                    "title": "Материал обложки",
                    "description": "Код бумаги для обложки (sheet)",
                },
                {
                    "name": "cover_color",
                    "type": "string",
                    "required": False,
                    "default": "4+0",
                    "title": "Цветность обложки",
                    "choices": {"inline": [
                        {"id": "1+0", "title": "1+0"}, {"id": "4+0", "title": "4+0"},
                        {"id": "1+1", "title": "1+1"}, {"id": "4+1", "title": "4+1"}, {"id": "4+4", "title": "4+4"},
                    ]},
                },
                {
                    "name": "cover_lamination_id",
                    "type": "string",
                    "required": False,
                    "title": "Ламинация обложки",
                },
                {
                    "name": "backing_material_id",
                    "type": "string",
                    "required": False,
                    "title": "Материал подложки",
                    "description": "Если не задан — тот же, что у обложки",
                },
                {
                    "name": "backing_color",
                    "type": "string",
                    "required": False,
                    "title": "Цветность подложки",
                    "description": "Если не задана — как у обложки. 0+0 — лист без печати",
                },
                {
                    "name": "backing_lamination_id",
                    "type": "string",
                    "required": False,
                    "title": "Ламинация подложки",
                },
                {
                    "name": "inner_material_id",
                    "type": "string",
                    "required": True,
                    "title": "Материал блока",
                    "description": "Код бумаги для внутреннего блока",
                },
                {
                    "name": "inner_num_sheet",
                    "type": "integer",
                    "required": True,
                    "title": "Листов в блоке",
                    "validation": {"min": 1, "max": 200},
                },
                {
                    "name": "inner_color",
                    "type": "string",
                    "required": False,
                    "default": "1+0",
                    "title": "Цветность блока",
                },
                {
                    "name": "binding_type",
                    "type": "string",
                    "required": False,
                    "default": "spring",
                    "title": "Тип переплёта",
                    "choices": {"inline": [
                        {"id": "spring", "title": "Пружина"},
                        {"id": "staples", "title": "Скобы"},
                    ]},
                },
                {
                    "name": "binding_edge",
                    "type": "string",
                    "required": False,
                    "default": "long",
                    "title": "Сторона переплёта",
                    "choices": {"inline": [
                        {"id": "short", "title": "По короткой стороне"},
                        {"id": "long", "title": "По длинной стороне"},
                    ]},
                },
                {
                    "name": "is_print_laser",
                    "type": "boolean",
                    "required": False,
                    "default": False,
                    "title": "Цифровая печать блока",
                    "description": "Не отдавать внутренний блок на офсет",
                },
                {
                    "name": "mode",
                    "type": "integer",
                    "required": False,
                    "default": int(ProductionMode.STANDARD),
                    "title": "Режим",
                },
            ],
            "param_groups": {
                "main": ["quantity", "width_mm", "height_mm"],
                "cover": [
                    "cover_material_id", "cover_color", "cover_lamination_id",
                    "backing_material_id", "backing_color", "backing_lamination_id",
                ],
                "inner": ["inner_material_id", "inner_num_sheet", "inner_color"],
                "binding": ["binding_type", "binding_edge"],
                "mode": ["mode"],
            },
        }

    def get_options(self) -> Dict[str, Any]:
        materials = sheet_catalog.list_for_frontend()
        return {
            "materials": materials[:60],
            "colors": ["1+0", "4+0", "1+1", "4+1", "4+4"],
            "binding_types": ["spring", "staples"],
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
                    "quantity": {"type": "integer", "minimum": 1, "description": "Тираж блокнотов"},
                    "width_mm": {"type": "number", "minimum": 50, "description": "Ширина, мм"},
                    "height_mm": {"type": "number", "minimum": 50, "description": "Высота, мм"},
                    "cover_material_id": {"type": "string", "description": "Код бумаги обложки"},
                    "cover_color": {"type": "string", "default": "4+0"},
                    "cover_lamination_id": {"type": "string"},
                    "inner_material_id": {"type": "string", "description": "Код бумаги блока"},
                    "inner_num_sheet": {"type": "integer", "minimum": 1, "description": "Листов в блоке"},
                    "inner_color": {"type": "string", "default": "1+0"},
                    "binding_type": {"type": "string", "enum": ["spring", "staples"], "default": "spring"},
                    "binding_edge": {"type": "string", "enum": ["short", "long"], "default": "long"},
                    "backing_material_id": {"type": "string", "description": "Код бумаги подложки"},
                    "backing_color": {"type": "string", "description": "Цветность подложки"},
                    "backing_lamination_id": {"type": "string"},
                    "is_print_laser": {"type": "boolean", "default": False},
                    "mode": {"type": "integer", "enum": [0, 1, 2], "default": 1},
                },
                "required": ["quantity", "width_mm", "height_mm", "cover_material_id", "inner_material_id", "inner_num_sheet"],
            },
        }

    def calculate(self, params: Mapping[str, Any]) -> Dict[str, Any]:
        n = int(params.get("quantity", 1))
        width = float(params.get("width_mm", 0))
        height = float(params.get("height_mm", 0))
        size = [width, height]
        mode = ProductionMode(int(params.get("mode", 1)))

        cover_material_id = str(params.get("cover_material_id", "") or "").strip()
        cover_color = str(params.get("cover_color", "4+0") or "4+0").strip()
        cover_lamination_id = str(params.get("cover_lamination_id", "") or "").strip()
        backing_material_id = str(params.get("backing_material_id") or "").strip() or cover_material_id
        backing_color = str(params.get("backing_color") or "").strip() or cover_color
        if "backing_lamination_id" in params:
            backing_lamination_id = str(params.get("backing_lamination_id") or "").strip()
        else:
            backing_lamination_id = cover_lamination_id
        inner_material_id = str(params.get("inner_material_id", "") or "").strip()
        inner_num_sheet = int(params.get("inner_num_sheet", 1))
        inner_color = str(params.get("inner_color", "1+0") or "1+0").strip()
        binding_type = str(params.get("binding_type", "spring") or "spring").strip()
        binding_edge = str(params.get("binding_edge", "long") or "long").strip()

        if not cover_material_id or not inner_material_id:
            raise ValueError("Укажите материал обложки и блока")

        num_with_defects = n

        def _one_face(qty: int, material_id: str, color: str, lamination_id: str) -> Dict[str, Any]:
            # 0+0 — чистый лист. PrintSheetCalculator его обнуляет, считаем здесь.
            if color == "0+0":
                return _blank_sheet(qty, size, material_id, lamination_id, mode.value)
            return PrintSheetCalculator().calculate(
                {
                    "quantity": qty,
                    "width": size[0],
                    "height": size[1],
                    "color": color,
                    "margins": [2, 2, 2, 2],
                    "interval": 4,
                    "material_id": material_id,
                    "lamination_id": lamination_id or None,
                    "lamination_double_side": True,
                    "mode": mode.value,
                }
            )

        # Обложка и подложка одной печатью 2*n, если материал, ламинация и цвет совпали.
        same_face = (
            cover_material_id == backing_material_id
            and cover_lamination_id == backing_lamination_id
            and cover_color == backing_color
        )
        if same_face:
            cost_covers = _one_face(2 * num_with_defects, cover_material_id, cover_color, cover_lamination_id)
        else:
            cost_covers = _combine_jobs(
                [
                    _one_face(num_with_defects, cover_material_id, cover_color, cover_lamination_id),
                    _one_face(num_with_defects, backing_material_id, backing_color, backing_lamination_id),
                ]
            )

        # Внутренний блок
        layout_a4 = layout_on_sheet(size, SIZE_A4, None, 0.0)
        num_sheet_a4 = math.ceil(num_with_defects * inner_num_sheet / layout_a4["num"]) if layout_a4["num"] > 0 else 0

        use_offset = (
            layout_a4["num"] > 0
            and num_sheet_a4 >= 1000
            and not params.get("is_print_laser")
            and not (inner_color == "0+0" and math.ceil(num_with_defects / layout_a4["num"]) <= 200)
        )

        cost_inners: Dict[str, Any] = {"cost": 0.0, "price": 0.0, "time_hours": 0.0, "time_ready": 0.0, "weight_kg": 0.0, "materials": []}
        is_offset = False

        if use_offset:
            print_offset = PrintOffsetCalculator()
            offset_params = {
                "num_sheet": num_with_defects * inner_num_sheet,
                "width": size[0],
                "height": size[1],
                "color": inner_color,
                "material_id": inner_material_id,
                "mode": mode.value,
            }
            inner_result = print_offset.calculate(offset_params)
            cost_inners = inner_result
            if num_sheet_a4 > 2500:
                is_offset = True
        else:
            if inner_color == "0+0":
                inner_result = _blank_sheet(
                    num_with_defects * inner_num_sheet, size, inner_material_id, None, mode.value
                )
            else:
                margins_inner = [2, 2, 2, 2]
                interval_inner = 4
                if inner_material_id == "VHI80":
                    # JS calcNotebook.js:61 — ровно -1, без полей принтера.
                    margins_inner = -1
                    interval_inner = 0
                inner_params = {
                    "quantity": num_with_defects * inner_num_sheet,
                    "width": size[0],
                    "height": size[1],
                    "color": inner_color,
                    "margins": margins_inner,
                    "interval": interval_inner,
                    "material_id": inner_material_id,
                    "lamination_id": None,
                    "lamination_double_side": True,
                    "mode": mode.value,
                }
                inner_result = PrintSheetCalculator().calculate(inner_params)
            cost_inners = inner_result

        # Переплёт
        cover = {
            "cover": {"materialID": cover_material_id, "laminatID": cover_lamination_id or "", "color": cover_color},
            "backing": {
                "materialID": backing_material_id,
                "laminatID": backing_lamination_id or "",
                "color": backing_color,
            },
        }
        inner = [{"materialID": inner_material_id, "numSheet": inner_num_sheet, "color": inner_color}]
        binding = {"edge": binding_edge}
        options_binding = {"bindingID": "BindOffset" if is_offset else "BindRenzSRW"}

        if binding_type == "staples":
            cost_binding = calc_set_staples(n, None, mode.value)
        else:
            cost_binding = calc_binding(n, size, cover, inner, binding, options_binding, mode.value)

        # Итог
        cost_total = cost_covers["cost"] + cost_inners["cost"] + cost_binding.cost
        price_total = cost_covers["price"] + cost_inners["price"] + cost_binding.price
        margin_notebook = get_margin("marginNotebook")
        price = (price_total) * (1 + margin_notebook)
        price = math.ceil(price)

        time_hours = math.ceil((cost_covers["time_hours"] + cost_inners["time_hours"] + cost_binding.time_hours) * 100) / 100
        time_ready = time_hours + max(
            cost_covers.get("time_ready", 0),
            cost_inners.get("time_ready", 0),
            cost_binding.time_ready,
        )
        weight_kg = cost_covers.get("weight_kg", 0) + cost_inners.get("weight_kg", 0) + cost_binding.weight_kg

        materials_out = _merge_materials(
            cost_covers.get("materials", []),
            cost_inners.get("materials", []),
        )
        materials_out = _ensure_size_mm(_merge_materials(materials_out, cost_binding.materials))

        return {
            "cost": float(cost_total),
            "price": int(price),
            "unit_price": float(price) / max(1, n),
            "time_hours": time_hours,
            "time_ready": time_ready,
            "weight_kg": round(weight_kg, 2),
            "materials": materials_out,
        }
