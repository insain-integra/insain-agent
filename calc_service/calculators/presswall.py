"""
Калькулятор ПРЕССВОЛЛОВ.

Мигрировано из js_legacy/calc/calcPresswall.js.
Широкоформатные баннеры на стендах: печать + каркас (профили) + опции (аренда, чехол).
"""

from __future__ import annotations

import math
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional, Tuple

import json5

from calculators.base import BaseCalculator, ProductionMode
from calculators.print_roll import PrintRollCalculator
from common.markups import MARGIN_MATERIAL, get_margin
from common.process_tools import calc_cut_profile, calc_sewing_covers
from materials import presswall as presswall_catalog
from materials import roll as roll_catalog

PRESSWALL_JSON = Path(__file__).parent.parent / "data" / "materials" / "presswall.json"
TOOL_CUT = "DWE4257"
PRINTER_DEFAULT = "TechnojetXR720"
COVER_MATERIAL = "Oxford600D"
RENT_PER_DAY = 400


def _load_presswall_data() -> Dict[str, Any]:
    with open(PRESSWALL_JSON, "r", encoding="utf-8") as f:
        return json5.load(f)


def _get_presswall_config(presswall_id: str) -> Tuple[Dict[str, Any], Dict[str, float], List[List[float]], Optional[List[float]]]:
    """
    Получить конфиг прессвола: (merged_config, materials_quantities, segments, size_banner).
    materials_quantities: {item_id: quantity_per_unit}
    """
    data = _load_presswall_data()
    for group_id, group_data in data.items():
        if not isinstance(group_data, dict):
            continue
        default = group_data.get("Default", {}) or {}
        for code, raw in group_data.items():
            if code == "Default":
                continue
            if not isinstance(raw, dict) or code != presswall_id:
                continue
            merged = dict(default)
            merged.update(raw)
            # Материалы: только числовые значения (количество)
            materials_qt: Dict[str, float] = {}
            for k, v in merged.items():
                if k in ("sizeBanner", "segments", "description", "title", "size", "material"):
                    continue
                if isinstance(v, (int, float)):
                    materials_qt[k] = float(v)
            segments = merged.get("segments") or []
            if isinstance(segments, list):
                segments = [[float(s[0]), float(s[1])] for s in segments if isinstance(s, (list, tuple)) and len(s) >= 2]
            size_banner = merged.get("sizeBanner")
            if isinstance(size_banner, (list, tuple)) and len(size_banner) >= 2:
                size_banner = [float(size_banner[0]), float(size_banner[1])]
            else:
                size_banner = None
            return merged, materials_qt, segments, size_banner
    raise KeyError(f"Прессвол {presswall_id!r} не найден")


class PresswallCalculator(BaseCalculator):
    """Прессволлы: баннер + каркас + опции."""

    slug = "presswall"
    name = "Прессволлы"
    description = "Расчёт прессволлов: печать баннера + каркас + опционально аренда, чехол."

    def get_options(self) -> Dict[str, Any]:
        data = _load_presswall_data()
        variants: List[Dict[str, str]] = []
        for group_id, group_data in data.items():
            if not isinstance(group_data, dict):
                continue
            for code, raw in group_data.items():
                if code == "Default" or not isinstance(raw, dict):
                    continue
                if "sizeBanner" in raw or "segments" in raw or "cost" in raw:
                    variants.append({
                        "code": code,
                        "name": raw.get("title") or raw.get("description") or code,
                    })
        banner_materials = []
        try:
            banner_group = roll_catalog.get_group("Banner")
            if banner_group:
                for m in banner_group:
                    banner_materials.append({"code": m.code, "name": m.title or m.description})
        except Exception:
            pass
        if not banner_materials:
            banner_materials = [
                {"code": "BannerFronlitCoat400", "name": "Баннер Fronlit 400г/м²"},
                {"code": "BannerFronlitLamin440", "name": "Баннер Fronlit ламинированный 440г/м²"},
            ]
        return {
            "presswall_types": variants,
            "banner_materials": banner_materials,
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
                    "presswall_id": {"type": "string", "description": "Тип прессвола (Joker30_20_eyelet и т.п.)"},
                    "material_id": {"type": "string", "description": "Код баннерного материала (Banner)"},
                    "is_presswall": {"type": "boolean", "default": True, "description": "Включить каркас"},
                    "is_rent": {"type": "integer", "description": "Дней аренды (0 = нет)"},
                    "is_bag": {"type": "string", "description": "Код чехла (bag160, bag210) или пусто"},
                    "mode": {"type": "integer", "enum": [0, 1, 2], "default": 1},
                },
                "required": ["quantity", "presswall_id"],
            },
        }

    def get_param_schema(self) -> Dict[str, Any]:
        return {
            "slug": self.slug,
            "title": self.name,
            "params": [
                {"name": "quantity", "type": "integer", "required": True, "title": "Тираж", "validation": {"min": 1}},
                {"name": "presswall_id", "type": "string", "required": True, "title": "Тип прессвола"},
                {"name": "material_id", "type": "string", "required": False, "title": "Материал баннера"},
                {"name": "is_presswall", "type": "boolean", "required": False, "default": True, "title": "Каркас"},
                {"name": "is_rent", "type": "integer", "required": False, "default": 0, "title": "Дней аренды"},
                {"name": "is_bag", "type": "string", "required": False, "title": "Чехол"},
                {"name": "mode", "type": "enum", "required": False, "default": 1, "title": "Режим",
                 "choices": {"inline": [{"id": 0, "title": "Эконом"}, {"id": 1, "title": "Стандарт"}, {"id": 2, "title": "Экспресс"}]}},
            ],
            "param_groups": {"main": ["quantity", "presswall_id"], "material": ["material_id"], "options": ["is_presswall", "is_rent", "is_bag"], "mode": ["mode"]},
        }

    def calculate(self, params: Mapping[str, Any]) -> Dict[str, Any]:
        n = int(params.get("quantity", 1))
        presswall_id = str(params.get("presswall_id", "")).strip()
        material_id = str(params.get("material_id", "") or "").strip()
        is_presswall = bool(params.get("is_presswall", True))
        is_rent_days = int(params.get("is_rent", 0) or 0)
        is_bag_id = str(params.get("is_bag", "") or "").strip()
        mode = ProductionMode(int(params.get("mode", 1)))

        if not presswall_id:
            raise ValueError("Не указан тип прессвола (presswall_id)")

        _, materials_qt, segments, size_banner = _get_presswall_config(presswall_id)

        cost_cut = 0.0
        price_cut = 0.0
        time_cut = 0.0
        time_ready_cut = 0.0
        weight_cut = 0.0
        cost_materials = 0.0
        cost_rent = 0.0
        weight_kg = 0.0
        materials_out: List[Dict[str, Any]] = []

        # Каркас: материалы + нарезка профиля
        pw_data = _load_presswall_data()
        mat_group = pw_data.get("Material", {}) or {}
        if not isinstance(mat_group, dict):
            mat_group = {}
        mat_default = mat_group.get("Default", {}) or {}

        if is_presswall and materials_qt:
            for item_id, qty_per_unit in materials_qt.items():
                try:
                    item = presswall_catalog.get(item_id)
                except KeyError:
                    continue
                qty_total = n * qty_per_unit
                cost_materials += qty_total * float(item.cost or 0)
                mat_raw = dict(mat_default)
                mat_raw.update(mat_group.get(item_id, {}))
                item_weight = float(mat_raw.get("weight", 0))
                weight_kg += qty_total * item_weight
                materials_out.append({
                    "code": item_id,
                    "name": item.description,
                    "title": item.title,
                    "quantity": qty_total,
                    "unit": "шт",
                })
            if segments:
                r = calc_cut_profile(n, segments, TOOL_CUT, mode.value)
                cost_cut = r.cost
                price_cut = r.price
                time_cut = r.time_hours
                time_ready_cut = r.time_ready

        # Аренда
        if is_rent_days > 0:
            cost_rent = n * RENT_PER_DAY * is_rent_days

        # Печать баннера
        cost_banner = 0.0
        price_banner = 0.0
        time_banner = 0.0
        time_ready_banner = 0.0
        weight_banner = 0.0
        if material_id and size_banner:
            try:
                roll_catalog.get(material_id)
            except KeyError:
                material_id = "BannerFronlitCoat400"
            print_calc = PrintRollCalculator()
            banner_result = print_calc.calculate({
                "quantity": n,
                "width": size_banner[0],
                "height": size_banner[1],
                "material_id": material_id,
                "printer_code": PRINTER_DEFAULT,
                "mode": mode.value,
            })
            cost_banner = float(banner_result.get("cost", 0))
            price_banner = float(banner_result.get("price", 0))
            time_banner = float(banner_result.get("time_hours", 0))
            time_ready_banner = float(banner_result.get("time_ready", 0))
            weight_banner = float(banner_result.get("weight_kg", 0))
            materials_out.extend(banner_result.get("materials", []))

        # Чехол
        cost_bag = 0.0
        price_bag = 0.0
        time_bag = 0.0
        time_ready_bag = 0.0
        weight_bag = 0.0
        if is_bag_id:
            try:
                bag_raw = _load_presswall_data()
                bag_config = None
                for group_id, group_data in bag_raw.items():
                    if is_bag_id in group_data and isinstance(group_data.get(is_bag_id), dict):
                        bag_config = group_data[is_bag_id]
                        break
                if bag_config and "size" in bag_config:
                    bag_size = bag_config["size"]
                    if isinstance(bag_size, (list, tuple)) and len(bag_size) >= 2:
                        r = calc_sewing_covers(n, list(bag_size), COVER_MATERIAL, mode.value)
                        cost_bag = r.cost
                        price_bag = r.price
                        time_bag = r.time_hours
                        time_ready_bag = r.time_ready
                        weight_bag = r.weight_kg
                        materials_out.extend(r.materials)
            except Exception:
                pass

        # Итог (как в JS)
        margin_pw = get_margin("marginPresswall")
        cost = cost_cut + cost_banner + cost_materials + cost_bag + cost_rent
        price = (
            (cost_cut + price_banner + price_bag) * (1 + margin_pw)
            + (cost_materials + cost_rent) * (1 + MARGIN_MATERIAL + margin_pw)
        )
        time_hours = math.ceil((time_cut + time_banner + time_bag) * 100) / 100
        time_ready = time_hours + max(time_ready_cut, time_ready_banner, time_ready_bag)
        weight_kg += weight_banner + weight_bag

        return {
            "cost": math.ceil(cost),
            "price": math.ceil(price),
            "unit_price": math.ceil(price) / max(1, n),
            "time_hours": time_hours,
            "time_ready": time_ready,
            "weight_kg": round(weight_kg, 2),
            "materials": materials_out,
        }
