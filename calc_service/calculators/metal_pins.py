"""
Калькулятор МЕТАЛЛИЧЕСКИХ ЗНАЧКОВ (штамповка).

Мигрировано из js_legacy/calc/calcMetalPins.js.
Металлические значки со штамповкой: заготовка, штамп, эмали, покрытие, эпоксидная смола.
Включает доставку из Китая, крепления и упаковку.
"""

from __future__ import annotations

import math
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional

import json5

from calculators.base import BaseCalculator, ProductionMode
from common.markups import COST_OPERATOR, get_margin
from common.currencies import USD_RATE

_METALPINS_JSON = Path(__file__).parent.parent / "data" / "equipment" / "metalpins.json"

_metalpins_cache: Optional[Dict[str, Any]] = None


def _load_metalpins() -> Dict[str, Any]:
    global _metalpins_cache
    if _metalpins_cache is None:
        with open(_METALPINS_JSON, "r", encoding="utf-8") as f:
            _metalpins_cache = json5.load(f)
    return _metalpins_cache


def _find_in_table(table: List[List[float]], value: float, col: int = 1) -> float:
    """Найти значение в таблице [порог, ...] по первому порогу >= value."""
    for row in table:
        if len(row) > 0 and value <= row[0]:
            return float(row[col]) if col < len(row) else float(row[0])
    if table:
        last = table[-1]
        return float(last[col]) if col < len(last) else float(last[0])
    return 0.0


def _find_scale_index(scale: List[float], n: int) -> int:
    """Индекс в ScalePCS для тиража n (1-based)."""
    for i, thresh in enumerate(scale):
        if n <= thresh:
            return i + 1
    return len(scale) + 1


class MetalPinsCalculator(BaseCalculator):
    """Металлические значки (штамповка): заготовка, штамп, эмали, покрытие."""

    slug = "metal_pins"
    name = "Металлические значки"
    description = "Расчёт металлических значков со штамповкой: заготовка, штамп, эмали, покрытие, доставка из Китая."
    keywords = [
        "значки",
        "значок",
        "металлические значки",
        "металлический значок",
        "pin",
        "pins",
        "badge",
        "badges",
        "значки штампованные",
        "значки с эмалью",
    ]

    def get_param_schema(self) -> Dict[str, Any]:
        return {
            "slug": self.slug,
            "title": self.name,
            "params": [
                {"name": "quantity", "type": "integer", "required": True, "title": "Тираж", "validation": {"min": 1, "max": 10000}},
                {"name": "width_mm", "type": "number", "required": True, "title": "Ширина, мм", "default": 25},
                {
                    "name": "height_mm",
                    "type": "number",
                    "required": True,
                    "title": "Высота, мм",
                    "description": "По умолчанию = ширина",
                },
                {"name": "process", "type": "string", "required": False, "title": "Технология", "default": "2d",
                 "enum": ["soft_enamel", "2d", "3d", "casting", "silk_screen", "offset"]},
                {"name": "num_enamels", "type": "integer", "required": False, "title": "Кол-во цветов эмали", "default": 0},
                {"name": "plating", "type": "string", "required": False, "title": "Покрытие", "default": "nickel",
                 "enum": ["nickel", "gold", "silver", "cooper", "bronze", "blacknickel",
                          "anticsilver", "anticgold", "anticnickel", "anticcooper", "anticbronze"]},
                {"name": "is_epoxy", "type": "boolean", "required": False, "title": "Эпоксидная смола", "default": False},
                {"name": "metal", "type": "string", "required": False, "title": "Металл", "default": "brass",
                 "enum": ["brass", "aluminum", "steel", "stainlesssteel"]},
                {"name": "attachment_id", "type": "string", "required": False, "title": "Крепление",
                 "enum": ["BC", "BC2", "PinMetal", "SafetyPin", "Screw", "TieClip", "Magnet17", "Magnet4513"]},
                {"name": "pack_id", "type": "string", "required": False, "title": "Упаковка",
                 "enum": ["PolyBag", "AcrylicBox30", "AcrylicBox40", "AcrylicBox50"]},
                {"name": "mode", "type": "integer", "required": False, "default": int(ProductionMode.STANDARD), "title": "Режим"},
            ],
            "param_groups": {
                "main": ["quantity", "width_mm", "height_mm"],
                "options": ["process", "num_enamels", "plating", "is_epoxy", "metal", "attachment_id", "pack_id"],
                "mode": ["mode"],
            },
        }

    def get_options(self) -> Dict[str, Any]:
        data = _load_metalpins()
        attachment = data.get("Attachment", {})
        pack = data.get("Pack", {})
        return {
            "attachments": [{"code": k, "name": v.get("name", k)} for k, v in attachment.items() if isinstance(v, dict) and "cost" in v],
            "packs": [{"code": k, "name": v.get("name", k)} for k, v in pack.items() if isinstance(v, dict)],
            "modes": [
                {"value": ProductionMode.ECONOMY, "label": "Экономичный"},
                {"value": ProductionMode.STANDARD, "label": "Стандартный"},
                {"value": ProductionMode.EXPRESS, "label": "Экспресс"},
            ],
        }

    PROCESS_MAP = {
        # 0‑й столбец в CostStamp/CostPins — размер, поэтому все технологии
        # начинаются с processID=1 (штамповка 2D).
        "soft_enamel": 1,
        "мягкая эмаль": 1,
        "2d": 1,
        "штамповка": 1,
        "штамповка 2d": 1,
        "3d": 2,
        "штамповка 3d": 2,
        "casting": 3,
        "литьё": 3,
        "литье": 3,
        "silk_screen": 4,
        "шелкография": 4,
        "offset": 5,
        "офсет": 5,
        "офсетная печать": 5,
    }

    PLATING_MAP = {
        "серебро": "silver", "никель": "nickel", "золото": "gold",
        "медь": "cooper", "бронза": "bronze",
        "черный никель": "blacknickel", "чёрный никель": "blacknickel",
        "антик серебро": "anticsilver", "антик золото": "anticgold",
        "антик медь": "anticcooper", "антик бронза": "anticbronze",
        "антик никель": "anticnickel",
    }

    def get_llm_prompt(self) -> str:
        return (
            "Это металлические значки (штамповка), не листовка и не акриловый брелок.\n"
            "Обязательны только тираж и размер (ширина и высота, мм). "
            "Если пользователь назвал тираж и оба размера — сразу вызывай calc_metal_pins.\n"
            "Поля metal, plating, process, крепление, упаковка — enum с default в схеме; "
            "не спрашивай их, пока пользователь сам не попросит другой вариант.\n"
            "Не спрашивай про листовой материал, акрил, ПВХ, меловку — для этого калькулятора "
            "нет material_id; search_materials для «подобрать материал» не используй."
        )

    def get_tool_schema(self) -> Dict[str, Any]:
        return {
            "name": "calc_" + self.slug,
            "description": self.description,
            "parameters": {
                "type": "object",
                "properties": {
                    "quantity": {"type": "integer", "minimum": 1, "description": "Тираж значков"},
                    "width_mm": {
                        "type": "number",
                        "description": "Ширина значка, мм. Обязательный параметр.",
                    },
                    "height_mm": {
                        "type": "number",
                        "description": "Высота значка, мм. Обязательный параметр.",
                    },
                    "process": {
                        "type": "string",
                        "enum": ["soft_enamel", "2d", "3d", "casting", "silk_screen", "offset"],
                        "description": "Технология: soft_enamel (мягкая эмаль), 2d (штамповка), 3d, casting (литьё), silk_screen (шелкография), offset (офсет)",
                    },
                    "num_enamels": {"type": "integer", "default": 0, "description": "Количество цветов эмали (0 = без эмали)"},
                    "plating": {
                        "type": "string", "default": "nickel",
                        "enum": ["nickel", "gold", "silver", "cooper", "bronze", "blacknickel",
                                 "anticsilver", "anticgold", "anticnickel", "anticcooper", "anticbronze"],
                        "description": "Покрытие: nickel, gold, silver, cooper, bronze и antic-варианты",
                    },
                    "is_epoxy": {"type": "boolean", "default": False, "description": "Заливка эпоксидной смолой"},
                    "metal": {
                        "type": "string", "default": "brass",
                        "enum": ["brass", "aluminum", "steel", "stainlesssteel"],
                        "description": "Металл: brass (латунь), aluminum, steel, stainlesssteel",
                    },
                    "attachment_id": {
                        "type": "string",
                        "enum": ["BC", "BC2", "PinMetal", "SafetyPin", "Screw", "TieClip", "Magnet17", "Magnet4513"],
                        "description": "Крепление: BC (игла-цанга), PinMetal (булавка), SafetyPin (безопасная булавка), Screw (винтовое), Magnet17/Magnet4513 (магнит)",
                    },
                    "pack_id": {
                        "type": "string",
                        "enum": ["PolyBag", "AcrylicBox30", "AcrylicBox40", "AcrylicBox50"],
                        "description": "Упаковка: PolyBag (пакетик), AcrylicBox30/40/50 (коробочка)",
                    },
                    "mode": {"type": "integer", "enum": [0, 1, 2], "default": 1},
                },
                "required": ["quantity", "width_mm", "height_mm"],
            },
        }

    @staticmethod
    def _normalize_input_params(params: Mapping[str, Any]) -> Dict[str, Any]:
        """
        Сайт/LLM иногда передают width/height вместо width_mm/height_mm — иначе float(None) → 500.
        Квадрат: если задана только одна сторона, вторая = ей же.
        """
        p = dict(params)
        if p.get("width_mm") is None and p.get("width") is not None:
            p["width_mm"] = p.pop("width")
        if p.get("height_mm") is None and p.get("height") is not None:
            p["height_mm"] = p.pop("height")
        wm, hm = p.get("width_mm"), p.get("height_mm")
        if wm is not None and hm is None:
            p["height_mm"] = wm
        elif hm is not None and wm is None:
            p["width_mm"] = hm
        return p

    def _resolve_process_id(self, value: Any) -> int:
        if isinstance(value, int):
            return value if value > 0 else 1
        s = str(value).strip().lower()
        # 0 ломал выбор колонки в CostStamp (берётся размер вместо цены)
        return self.PROCESS_MAP.get(s, 1)

    def _coerce_mode(self, raw: Any) -> ProductionMode:
        try:
            v = int(raw)
            if v in (0, 1, 2):
                return ProductionMode(v)
        except (TypeError, ValueError):
            pass
        return ProductionMode.STANDARD

    def _resolve_plating_id(self, value: Any) -> str:
        s = str(value).strip().lower()
        return self.PLATING_MAP.get(s, s)

    def _build_stamps_from_params(self, params: Mapping[str, Any]) -> List[Dict[str, Any]]:
        """Build stamps array from simplified flat parameters."""
        data = _load_metalpins()
        tool = data.get("MetalPins", {})
        standart_t = tool.get("StandartT", [[30, 1.2], [40, 1.4], [60, 2.0], [80, 2.5], [100, 3.0]])

        try:
            width = float(params.get("width_mm"))
            height = float(params.get("height_mm"))
        except (TypeError, ValueError):
            raise ValueError(
                "Укажите ширину и высоту значка в мм: width_mm и height_mm (или width и height)."
            ) from None
        thickness = _find_in_table(standart_t, math.sqrt((width**2 + height**2) / 2), 1)

        process_id = self._resolve_process_id(params.get("process", "2d"))
        num_enamels = int(params.get("num_enamels", 0))
        plating_id = self._resolve_plating_id(params.get("plating", "nickel"))
        is_epoxy = bool(params.get("is_epoxy", False))
        material_id = str(params.get("metal", "brass") or "brass")

        return [{
            "size": [width, height, thickness],
            "processID": process_id,
            "numEnamels": num_enamels,
            "platingID": plating_id,
            "isEpoxy": is_epoxy,
            "isMould": False,
            "materialID": material_id,
        }]

    def calculate(self, params: Mapping[str, Any]) -> Dict[str, Any]:
        params = self._normalize_input_params(params)
        n = int(params.get("quantity", 1))
        stamps = params.get("stamps", None)
        attachment_id = str(params.get("attachment_id", "") or "").strip()
        pack_id = str(params.get("pack_id", "") or "").strip()
        mode = self._coerce_mode(params.get("mode", 1))

        if not stamps or not isinstance(stamps, list):
            stamps = self._build_stamps_from_params(params)

        data = _load_metalpins()
        tool = data.get("MetalPins", {})
        attachment_cat = data.get("Attachment", {})
        pack_cat = data.get("Pack", {})

        base_time_ready = tool.get("baseTimeReady", [440, 360, 320])
        idx = max(0, min(len(base_time_ready) - 1, math.ceil(mode.value)))
        base_ready = float(base_time_ready[idx])
        defects = float(tool.get("defects", 0.05))
        tool_margin = float(tool.get("margin", 0.35))
        cost_operator_hr = float(tool.get("costOperator", 0)) or COST_OPERATOR
        usd = USD_RATE

        cost_pins = 0.0
        weight_pins = 0.0
        materials_out: List[Dict[str, Any]] = []

        scale_pcs = tool.get("ScalePCS", [50, 100, 200, 300, 500, 1000, 10000])
        cost_pins_table = tool.get("CostPins", [])
        standart_t = tool.get("StandartT", [[30, 1.2], [40, 1.4], [60, 2.0], [80, 2.5], [100, 3.0]])
        cost_stamp_table = tool.get("CostStamp", [])
        cost_enamels_table = tool.get("CostEnamels", [[30, 0.02], [40, 0.027], [50, 0.033], [60, 0.04], [65, 0.044], [70, 0.047], [75, 0.05], [80, 0.054], [90, 0.06], [100, 0.067]])
        cost_plating = tool.get("CostPlating", {})
        cost_epoxy_arr = tool.get("CostEpoxy", [0.01, 0.0025])
        min_cost_stamp = float(tool.get("minCostStamp", 15))
        weight_table = tool.get("Weight", {"brass": 8.8, "aluminum": 2.6, "steel": 7.8, "stainlesssteel": 7.9})

        index_scale = _find_scale_index(scale_pcs, n)

        for stamp_data in stamps:
            if not isinstance(stamp_data, dict):
                continue
            size = stamp_data.get("size", [0, 0, 0])
            if len(size) < 3:
                size = [float(size[0]) if len(size) > 0 else 0, float(size[1]) if len(size) > 1 else 0, 0]
            else:
                size = [float(size[0]), float(size[1]), float(size[2])]
            process_id = int(stamp_data.get("processID", 0))
            num_enamels = int(stamp_data.get("numEnamels", 0))
            plating_id = str(stamp_data.get("platingID", "nickel") or "nickel")
            is_epoxy = bool(stamp_data.get("isEpoxy", False))
            is_mould = bool(stamp_data.get("isMould", False))
            material_id = str(stamp_data.get("materialID", "brass") or "brass")

            cost_pin = 0.0
            if size[2] > 0:
                aver_size = math.sqrt((size[0] ** 2 + size[1] ** 2) / 2)
                cost_pin = _find_in_table(cost_pins_table, aver_size, index_scale)
                standart_t_val = _find_in_table(standart_t, aver_size, 1)
                delta_t = math.ceil((size[2] - standart_t_val) / 0.2) * 0.06
                if delta_t < 0:
                    delta_t = 0
                cost_pin = cost_pin * (1 + delta_t)

            max_size = max(size[0], size[1])
            cost_stamp = 0.0
            if is_mould:
                cost_stamp = min_cost_stamp
            else:
                cost_stamp = _find_in_table(cost_stamp_table, max_size, min(process_id, 5))

            cost_enamels = _find_in_table(cost_enamels_table, max_size, 1) * num_enamels
            cost_plating_val = float(cost_plating.get(plating_id, 0))
            cost_epoxy_val = 0.0
            if is_epoxy:
                cost_epoxy_val = cost_epoxy_arr[0] + cost_epoxy_arr[1] * size[0] * size[1] / 100

            cost_pins += (cost_pin + cost_enamels + cost_plating_val + cost_epoxy_val) * n + cost_stamp
            density = float(weight_table.get(material_id, 8.8))
            weight_pins += size[0] * size[1] * size[2] * density * n / 1_000_000

        time_operator = float(tool.get("timePrepare", 2)) * mode.value
        cost_operator = time_operator * cost_operator_hr / usd

        cost_attachment = 0.0
        weight_attachment = 0.0
        if attachment_id:
            att = attachment_cat.get(attachment_id, {})
            if isinstance(att, dict) and "cost" in att:
                cost_attachment = float(att["cost"]) * n
                weight_attachment = float(att.get("weight", 0)) * n / 1000
                materials_out.append({
                    "code": attachment_id,
                    "name": att.get("name", attachment_id),
                    "title": att.get("name", attachment_id),
                    "quantity": n,
                    "unit": "шт",
                })

        cost_pack = 0.0
        weight_pack = 0.0
        if pack_id:
            p = pack_cat.get(pack_id, {})
            if isinstance(p, dict):
                cost_pack = float(p.get("cost", 0)) * n
                weight_pack = float(p.get("weight", 0)) * n / 1000
                materials_out.append({
                    "code": pack_id,
                    "name": p.get("name", pack_id),
                    "title": p.get("name", pack_id),
                    "quantity": n,
                    "unit": "шт",
                })

        total_weight = weight_pins + weight_attachment + weight_pack
        total_weight_ceil = math.ceil(total_weight)
        calc_weight = total_weight_ceil
        if mode.value >= 1 or calc_weight < 1:
            calc_weight = max(1, calc_weight)

        cost_shipment_china_rus = tool.get("CostShipmentChinaToRussia", [5.2, 10, 17])
        cost_ship_china_rus = float(cost_shipment_china_rus[min(mode.value, len(cost_shipment_china_rus) - 1)])
        cost_shipment_china = float(tool.get("CostShipmentChina", 3))
        cost_shipment_russia = tool.get("CostShipmentRussia", [1100, 30])

        cost_shipment = (
            calc_weight * cost_ship_china_rus
            + max(cost_shipment_china * total_weight_ceil, 5)
            + (cost_shipment_russia[0] + total_weight_ceil * cost_shipment_russia[1]) / usd
        )

        cost_total = (cost_pins + cost_attachment + cost_pack + cost_shipment + cost_operator) * (1 + defects) * (1 + tool_margin) * usd
        cost_total = math.ceil(cost_total)
        margin_pins = get_margin("marginMetalPins")
        price = math.ceil(cost_total * (1 + margin_pins))

        weight_kg = math.ceil((weight_pins + weight_attachment + weight_pack) * 100) / 100

        return {
            "cost": float(cost_total),
            "price": int(price),
            "unit_price": float(price) / max(1, n),
            "time_hours": 0.0,
            "time_ready": base_ready,
            "weight_kg": weight_kg,
            "materials": materials_out,
        }

    def execute(self, params: Mapping[str, Any]) -> Dict[str, Any]:
        """Нормализуем имена полей до share_url (width → width_mm), чтобы ссылка совпадала с сайтом."""
        norm = self._normalize_input_params(params)
        result = dict(self.calculate(norm))
        if "share_url" not in result:
            result["share_url"] = self.make_share_url(norm)
        return result
