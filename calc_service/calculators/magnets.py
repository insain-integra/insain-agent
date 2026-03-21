"""
Магниты: два публичных калькулятора.

Источник логики: js_legacy/calc/calcMagnets.js
- calcAcrylicMagnets → calc_acrylic_magnets / MagnetAcrylicCalculator (slug magnet_acrylic)
- calcMagnetLamination → calc_laminated_magnets / MagnetLaminatedCalculator (slug magnet_laminated)
"""

from __future__ import annotations

import math
from typing import Any, Dict, List, Mapping

from calculators.base import BaseCalculator, ProductionMode
from calculators.print_sheet import PrintSheetCalculator
from calculators.cut_guillotine import CutGuillotineCalculator
from common.markups import BASE_TIME_READY, MARGIN_MATERIAL, get_margin
from common.process_tools import calc_packing, calc_set_insert
from materials import get_material
from materials import magnet as magnet_catalog

DEFAULT_INSERT_MATERIAL = "PaperCoated115M"
DEFAULT_PRINT_MATERIAL = "RAFLACOAT"
# Глянцевая плёнка 32 мкм (рулон) — ламинация ламинированных магнитов по умолчанию
DEFAULT_LAMINATED_MAGNET_LAMINATION = "Laminat32G"
ZIPLOCK_ACRYLIC = "ZipLockAcrylic"

# Ламинированные магниты: выбор только по толщине винила без клевого слоя (каталог hardsheet MagnetVinil).
LAMINATED_MAGNET_VINYL_CODES: tuple[str, ...] = (
    "MagnetVinil04",
    "MagnetVinil07",
    "MagnetVinil09",
)

def _acrylic_choices() -> List[Dict[str, Any]]:
    return [
        {"id": m["code"], "title": m.get("title", m.get("name", m["code"]))}
        for m in magnet_catalog.list_for_frontend()
    ]


def _laminated_vinyl_choices() -> List[Dict[str, Any]]:
    """Толщина магнитного винила: 0.4 / 0.7 / 0.9 мм (MagnetVinil04, 07, 09)."""
    out: List[Dict[str, Any]] = []
    for code in LAMINATED_MAGNET_VINYL_CODES:
        try:
            spec = get_material("hardsheet", code)
        except KeyError:
            continue
        title = (spec.description or spec.title or code).strip()
        out.append({"id": code, "title": title, "description": spec.description})
    return out


def calc_acrylic_magnets(params: Mapping[str, Any]) -> Dict[str, Any]:
    """Акриловые магниты: заготовка + печать вставки + установка вставки + упаковка."""
    from common.process_tools import _get_raw_material

    quantity = int(params.get("quantity", 1))
    magnet_id = str(params.get("magnet_id", "") or "MagnetAcrylic6565")
    color = int(params.get("color", 1) or 1)
    is_packing = bool(params.get("is_packing", True))
    mode = ProductionMode(int(params.get("mode", 1)))

    try:
        magnet = magnet_catalog.get(magnet_id)
    except KeyError:
        allowed = ", ".join(c["id"] for c in _acrylic_choices())
        raise ValueError(
            f"Неверный код заготовки magnet_id: {magnet_id!r}. "
            f"Допустим только код из каталога: {allowed}."
        ) from None
    try:
        raw = _get_raw_material("magnet", magnet_id)
    except KeyError:
        raw = {}
    size = list(raw.get("size", magnet.sizes[0] if magnet.sizes else [65, 65]))
    size_insert = list(raw.get("sizeInsert", size))

    color_str = "4+4" if color >= 2 else "4+0"

    cost_blank = float(magnet.cost or 0) * quantity
    price_blank = cost_blank * (1 + MARGIN_MATERIAL)
    weight_blank = float(raw.get("weight", 20)) * quantity / 1000.0

    mat_blank = {
        "code": magnet_id,
        "name": magnet.description,
        "title": magnet.title,
        "quantity": quantity,
        "unit": "шт",
    }

    print_calc = PrintSheetCalculator()
    print_params = {
        "quantity": quantity,
        "width": size_insert[0],
        "height": size_insert[1],
        "material_id": DEFAULT_INSERT_MATERIAL,
        "color": color_str,
        "lamination_id": "",
        "mode": mode.value,
    }
    print_result = print_calc.calculate(print_params)
    cost_insert = float(print_result.get("cost", 0))
    price_insert = float(print_result.get("price", 0))
    time_insert = float(print_result.get("time_hours", 0))
    weight_insert = float(print_result.get("weight_kg", 0))
    time_ready_insert = float(print_result.get("time_ready", 0))
    materials_insert = print_result.get("materials", [])

    set_insert = calc_set_insert(quantity, mode.value)
    cost_set = set_insert.cost
    price_set = set_insert.price
    time_set = set_insert.time_hours
    time_ready_set = set_insert.time_ready

    cost_pack = 0.0
    price_pack = 0.0
    time_pack = 0.0
    time_ready_pack = 0.0
    weight_pack = 0.0
    materials_pack: List[Dict[str, Any]] = []
    if is_packing:
        pack_options = {"isPacking": ZIPLOCK_ACRYLIC}
        pack_size = [size[0], size[1], 5]
        pack_result = calc_packing(quantity, pack_size, pack_options, mode.value)
        cost_pack = pack_result.cost
        price_pack = pack_result.price
        time_pack = pack_result.time_hours
        time_ready_pack = pack_result.time_ready
        weight_pack = pack_result.weight_kg
        materials_pack = pack_result.materials

    margin = get_margin("marginMagnet") or get_margin("marginAcrylicKeychain")
    cost = cost_insert + cost_set + cost_blank + cost_pack
    price = (price_insert + price_set + price_blank + price_pack) * (1 + margin)

    time_hours = time_insert + time_set + time_pack
    time_ready = time_hours + max(time_ready_insert, time_ready_set, time_ready_pack)
    weight_kg = weight_insert + weight_blank + weight_pack

    materials: List[Dict[str, Any]] = [mat_blank] + materials_insert + materials_pack

    return {
        "cost": float(round(cost, 2)),
        "price": float(round(price, 2)),
        "unit_price": float(round(price, 2)) / max(1, quantity),
        "time_hours": float(round(time_hours, 2)),
        "time_ready": float(time_ready),
        "weight_kg": float(round(weight_kg, 3)),
        "materials": materials,
    }


def calc_laminated_magnets(params: Mapping[str, Any]) -> Dict[str, Any]:
    """Ламинированные магниты: печать + ламинация + магнитный винил + резка."""
    from common.layout import layout_on_sheet

    quantity = int(params.get("quantity", 1))
    material_id = str(params.get("magnet_id", "") or "MagnetVinil04")
    width = float(params.get("width_mm", 0) or params.get("width", 90))
    height = float(params.get("height_mm", 0) or params.get("height", 54))
    lamination_id = str(params.get("lamination_id", "") or "").strip()
    if not lamination_id:
        lamination_id = DEFAULT_LAMINATED_MAGNET_LAMINATION
    # По умолчанию без упаковки; true — добавить зип-лок (опционально).
    is_packing = bool(params.get("is_packing", False))
    mode = ProductionMode(int(params.get("mode", 1)))

    if width <= 0 or height <= 0:
        raise ValueError("Для ламинированных магнитов укажите ширину и высоту")

    if material_id not in LAMINATED_MAGNET_VINYL_CODES:
        allowed = ", ".join(LAMINATED_MAGNET_VINYL_CODES)
        raise ValueError(
            f"Укажите толщину магнитного винила (magnet_id): {allowed} "
            f"(0.4 / 0.7 / 0.9 мм). Получено: {material_id!r}"
        )

    size = [width, height]
    color_str = "4+0"
    size_sheet = [320.0, 450.0]

    try:
        magnet_vinyl = get_material("hardsheet", material_id)
    except KeyError:
        raise ValueError(f"Магнитный винил не найден: {material_id!r}")

    layout = layout_on_sheet(size, size_sheet, [2, 2, 2, 2], 4)
    num_per_sheet = layout.get("num", 1) or 1
    num_sheets = math.ceil(quantity / num_per_sheet) if num_per_sheet > 0 else quantity

    print_calc = PrintSheetCalculator()
    print_params = {
        "quantity": quantity,
        "width": width,
        "height": height,
        "material_id": DEFAULT_PRINT_MATERIAL,
        "color": color_str,
        "lamination_id": lamination_id,
        "lamination_double_side": True,
        "mode": mode.value,
    }
    print_result = print_calc.calculate(print_params)
    cost_print = float(print_result.get("cost", 0))
    price_print = float(print_result.get("price", 0))
    time_print = float(print_result.get("time_hours", 0))
    time_ready_print = float(print_result.get("time_ready", 0))
    weight_print = float(print_result.get("weight_kg", 0))
    materials_print = print_result.get("materials", [])

    vinyl_sizes = magnet_vinyl.sizes or [[620, 0]]
    size_vinyl = list(vinyl_sizes[0]) if vinyl_sizes else [620, 0]
    sheet_w = size_vinyl[0]
    sheet_h = size_vinyl[1] if len(size_vinyl) > 1 and size_vinyl[1] > 0 else 450.0
    area_m2 = (sheet_w / 1000.0) * (sheet_h / 1000.0) * num_sheets
    cost_vinyl = float(magnet_vinyl.cost or 0) * area_m2
    price_vinyl = cost_vinyl * (1 + MARGIN_MATERIAL)

    cut_calc = CutGuillotineCalculator()
    cut_params = {
        "num_sheet": num_sheets,
        "width": width,
        "height": height,
        "sheet_width": size_sheet[0],
        "sheet_height": size_sheet[1],
        "material_id": material_id,
        "material_category": "hardsheet",
        "margins": [2, 2, 2, 2],
        "interval": 4,
        "mode": mode.value,
    }
    cut_result = cut_calc.calculate(cut_params)
    cost_cut = float(cut_result.get("cost", 0))
    price_cut = float(cut_result.get("price", 0))
    time_cut = float(cut_result.get("time_hours", 0))

    cost_pack = 0.0
    price_pack = 0.0
    time_pack = 0.0
    weight_pack = 0.0
    materials_pack: List[Dict[str, Any]] = []
    if is_packing:
        pack_options = {"isPacking": "ZipLock1015"}
        pack_size = [width, height, 1]
        pack_result = calc_packing(quantity, pack_size, pack_options, mode.value)
        cost_pack = pack_result.cost
        price_pack = pack_result.price
        time_pack = pack_result.time_hours
        weight_pack = pack_result.weight_kg
        materials_pack = pack_result.materials

    margin = get_margin("marginMagnet") or get_margin("marginBadge")
    cost = cost_print + cost_vinyl + cost_cut + cost_pack
    price = (price_print + price_vinyl + price_cut + price_pack) * (1 + margin)

    time_hours = time_print + time_cut + time_pack
    time_ready = time_hours + max(
        time_ready_print, float(BASE_TIME_READY[min(mode.value, len(BASE_TIME_READY) - 1)])
    )
    weight_kg = weight_print + weight_pack

    mat_vinyl = {
        "code": material_id,
        "name": magnet_vinyl.description,
        "title": magnet_vinyl.title,
        "quantity": round(area_m2, 4),
        "unit": "m2",
    }
    materials = [mat_vinyl] + materials_print + materials_pack

    return {
        "cost": float(math.ceil(cost)),
        "price": float(math.ceil(price)),
        "unit_price": float(math.ceil(price)) / max(1, quantity),
        "time_hours": math.ceil(time_hours * 100) / 100.0,
        "time_ready": time_ready,
        "weight_kg": round(weight_kg, 2),
        "materials": materials,
    }


class MagnetAcrylicCalculator(BaseCalculator):
    """Акриловые магниты: только заготовки из каталога magnet.json; размеры заданы заготовкой."""

    slug = "magnet_acrylic"
    name = "Акриловые магниты"
    description = (
        "Расчёт акриловых магнитов: заготовка только из каталога (фиксированные формы и размеры), "
        "печать вставки, установка, упаковка. Произвольные мм не задаются."
    )
    keywords = [
        "акриловые магниты",
        "магнит акриловый",
        "магниты акриловые",
        "acrylic magnet",
        "магнит с акрилом",
    ]

    def get_param_schema(self) -> Dict[str, Any]:
        choices = _acrylic_choices()
        return {
            "slug": self.slug,
            "title": self.name,
            "params": [
                {
                    "name": "quantity",
                    "type": "integer",
                    "required": True,
                    "title": "Тираж",
                    "validation": {"min": 1, "max": 10000},
                },
                {
                    "name": "magnet_id",
                    "type": "enum",
                    "required": True,
                    "title": "Заготовка",
                    "description": "Акриловая заготовка (размер в названии)",
                    "choices": {"inline": choices},
                },
                {
                    "name": "color",
                    "type": "integer",
                    "required": False,
                    "default": 1,
                    "title": "Печать",
                    "description": "1 — односторонняя, 2 — двухсторонняя",
                    "choices": {
                        "inline": [
                            {"id": 1, "title": "Односторонняя"},
                            {"id": 2, "title": "Двухсторонняя"},
                        ]
                    },
                },
                {
                    "name": "is_packing",
                    "type": "boolean",
                    "required": False,
                    "default": True,
                    "title": "Упаковка",
                },
                {
                    "name": "mode",
                    "type": "enum",
                    "required": False,
                    "default": int(ProductionMode.STANDARD),
                    "title": "Режим",
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
                "main": ["quantity", "magnet_id"],
                "options": ["color", "is_packing"],
                "mode": ["mode"],
            },
        }

    def get_options(self) -> Dict[str, Any]:
        return {
            "magnets": magnet_catalog.list_for_frontend(),
            "modes": [
                {"value": 0, "label": "Экономичный"},
                {"value": 1, "label": "Стандартный"},
                {"value": 2, "label": "Экспресс"},
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
                    "magnet_id": {
                        "type": "string",
                        "description": (
                            "Только код из enum в схеме. Не придумывай формы/размеры — в каталоге только перечисленные варианты."
                        ),
                    },
                    "color": {"type": "integer", "minimum": 1, "maximum": 2, "description": "1 или 2 стороны печати"},
                    "is_packing": {"type": "boolean", "default": True},
                    "mode": {"type": "integer", "enum": [0, 1, 2], "default": 1},
                },
                "required": ["quantity", "magnet_id"],
            },
        }

    def get_llm_prompt(self) -> str:
        # Явный список из каталога — иначе модель подставляет вымышленные «круг 50 мм», «40×40» и т.п.
        variants = []
        for c in _acrylic_choices():
            label = (c.get("title") or c.get("id") or "").strip()
            if label:
                variants.append(label)
        catalog_lines = "\n".join(f"  — {v}" for v in variants) if variants else "  (каталог пуст)"
        allowed_codes = [str(c["id"]) for c in _acrylic_choices() if c.get("id")]
        codes_str = ", ".join(allowed_codes) if allowed_codes else "(каталог пуст)"
        return (
            "Тираж (quantity) и заготовка magnet_id — только из enum в схеме инструмента.\n"
            "В вызове calc_magnet_acrylic поле magnet_id должно быть РОВНО одним из кодов заготовки из каталога "
            f"(никаких других строк): {codes_str}. "
            "Запрещено выдумывать magnet_id — "
            "только перечисленные выше коды.\n"
            "Пользователю называй заготовки по человекочитаемым названиям (ниже), коды ему не показывай:\n"
            f"{catalog_lines}\n"
            "Если пользователь не выбрал — перечисли этот же список названий. "
            "Если назвал размеры в мм — сопоставь с ближайшей заготовкой из каталога и подставь соответствующий код magnet_id из списка выше. "
            "При наличии quantity и корректного magnet_id — сразу calc_magnet_acrylic."
        )

    def calculate(self, params: Mapping[str, Any]) -> Dict[str, Any]:
        return calc_acrylic_magnets(params)


class MagnetLaminatedCalculator(BaseCalculator):
    """Ламинированные магниты: размер изделия + толщина магнитного винила."""

    slug = "magnet_laminated"
    name = "Ламинированные магниты"
    description = (
        "Расчёт ламинированных магнитов: печать + ламинация + магнитный винил + резка. "
        "Ширина и высота изделия в мм. Толщина винила на выбор: 0.4 / 0.7 / 0.9 мм (MagnetVinil04, 07, 09). "
        "Ламинация по умолчанию — глянец 32 мкм (Laminat32G). Упаковка (зип-лок) по умолчанию не включена."
    )
    keywords = [
        "ламинированные магниты",
        "магнит ламинированный",
        "магнит на виниле",
        "магнитный винил",
        "laminated magnet",
    ]

    def get_param_schema(self) -> Dict[str, Any]:
        vchoices = _laminated_vinyl_choices()
        return {
            "slug": self.slug,
            "title": self.name,
            "params": [
                {
                    "name": "quantity",
                    "type": "integer",
                    "required": True,
                    "title": "Тираж",
                    "validation": {"min": 1, "max": 10000},
                },
                {
                    "name": "magnet_id",
                    "type": "enum",
                    "required": True,
                    "title": "Толщина магнитного винила",
                    "description": "Толщина 0.4 / 0.7 / 0.9 мм — коды MagnetVinil04, MagnetVinil07, MagnetVinil09.",
                    "choices": {"inline": vchoices},
                },
                {
                    "name": "width_mm",
                    "type": "number",
                    "required": True,
                    "title": "Ширина (мм)",
                    "validation": {"min": 10, "max": 500},
                    "unit": "мм",
                },
                {
                    "name": "height_mm",
                    "type": "number",
                    "required": True,
                    "title": "Высота (мм)",
                    "validation": {"min": 10, "max": 500},
                    "unit": "мм",
                },
                {
                    "name": "lamination_id",
                    "type": "string",
                    "required": False,
                    "title": "Ламинация",
                    "description": (
                        "Код плёнки из каталога ламинации. По умолчанию — глянцевая 32 мкм (Laminat32G); "
                        "передай другой код, если пользователь просит другую плёнку."
                    ),
                    "default": DEFAULT_LAMINATED_MAGNET_LAMINATION,
                },
                {
                    "name": "is_packing",
                    "type": "boolean",
                    "required": False,
                    "default": False,
                    "title": "Упаковка (зип-лок)",
                    "description": "По умолчанию без упаковки; true — добавить зип-лок в расчёт.",
                },
                {
                    "name": "mode",
                    "type": "enum",
                    "required": False,
                    "default": int(ProductionMode.STANDARD),
                    "title": "Режим",
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
                "main": ["quantity", "magnet_id", "width_mm", "height_mm"],
                "options": ["lamination_id", "is_packing"],
                "mode": ["mode"],
            },
        }

    def get_options(self) -> Dict[str, Any]:
        return {
            "vinyls": _laminated_vinyl_choices(),
            "modes": [
                {"value": 0, "label": "Экономичный"},
                {"value": 1, "label": "Стандартный"},
                {"value": 2, "label": "Экспресс"},
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
                    "magnet_id": {
                        "type": "string",
                        "description": (
                            "Толщина винила: MagnetVinil04 (0.4 мм), MagnetVinil07 (0.7 мм) или MagnetVinil09 (0.9 мм)."
                        ),
                    },
                    "width_mm": {"type": "number", "description": "Ширина изделия, мм"},
                    "height_mm": {"type": "number", "description": "Высота изделия, мм"},
                    "lamination_id": {
                        "type": "string",
                        "description": (
                            "Плёнка ламинации; по умолчанию глянец 32 мкм — Laminat32G (можно не передавать)."
                        ),
                        "default": DEFAULT_LAMINATED_MAGNET_LAMINATION,
                    },
                    "is_packing": {
                        "type": "boolean",
                        "default": False,
                        "description": "Упаковка зип-лок; по умолчанию false (без упаковки).",
                    },
                    "mode": {"type": "integer", "enum": [0, 1, 2], "default": 1},
                },
                "required": ["quantity", "magnet_id", "width_mm", "height_mm"],
            },
        }

    def get_llm_prompt(self) -> str:
        return (
            "Ламинированные магниты: тираж, width_mm, height_mm, magnet_id из enum (толщина винила 0.4 / 0.7 / 0.9 мм). "
            "lamination_id не спрашивай, если пользователь не просит другую плёнку: по умолчанию глянцевая 32 мкм (Laminat32G). "
            "Упаковку (is_packing) не спрашивай без запроса: по умолчанию без зип-лока; true — только если пользователь хочет упаковку. "
            "Собери обязательные поля и вызови calc_magnet_laminated."
        )

    def calculate(self, params: Mapping[str, Any]) -> Dict[str, Any]:
        return calc_laminated_magnets(params)
