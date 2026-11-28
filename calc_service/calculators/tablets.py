"""
Калькулятор ТАБЛИЧЕК.

Мигрировано из js_legacy/calc/calcTablets.js.
Информационные таблички: резка (роликовый резак / лазер / металл), УФ,
экосольвентная/латексная печать с накаткой, аппликация плёнками, сублимация, карманы, рамка.

Перенесено: ручная резка на роликовом резаке (CutRoller, is_cut_manual),
ручная резка металла (is_cut_manual_metal), сублимация, лазерная резка с гравировкой,
УФ-печать (с двойным нанесением), экосольвентная/латексная печать на плёнке ORAJET3640
с ручной накаткой (PrintRollCalculator + calc_manual_roll, is_print),
аппликация плёнками (StickerCalculator + calc_manual_roll, is_film),
оклейка фона таблички плёнкой (CutRoller KWTrio3026 + calc_manual_roll, is_background_film),
режим учёта материала (material_mode);
карманы (PocketsCalculator), рамка и подвесы (FrameCalculator),
EVA-пена (CutRoller KeencutEvolutionE2 + calc_manual_roll, is_eva_foam).

Список «не перенесено» (см. scripts/js_port_gaps_allowed.txt, префикс calcTablets):
- фрезерная резка (опция фрезеровки, вызов calcMilling),
- древко и клеевой слой на этапе табличек.
"""

from __future__ import annotations

import math
from typing import Any, Dict, List, Mapping, MutableMapping, Sequence

from calculators.base import BaseCalculator, ProductionMode, material_line
from calculators.cut_roller import CutRollerCalculator
from calculators.frame import FrameCalculator
from calculators.heat_press import HeatPressCalculator
from calculators.laser import LaserCalculator
from calculators.pockets import PocketsCalculator
from calculators.print_roll import DEFAULT_PRINTER as DEFAULT_ROLL_PRINTER, PrintRollCalculator
from calculators.sticker import StickerCalculator
from calculators.uv_print import UVPrintCalculator
from common.layout import layout_on_sheet
from common.markups import (
    MARGIN_MATERIAL,
    get_margin,
)
from common.process_tools import (
    calc_cut_saber,
    calc_manual_roll,
)
from materials import hardsheet as hardsheet_catalog, pocket as pocket_catalog, profile as profile_catalog

DEFAULT_PROFILE = "AluFrame2Plus"
DEFAULT_UV_PRINTER = "RimalSuvUV"


def _pick(mapping: Mapping[str, Any], *keys: str, default: Any = None) -> Any:
    for key in keys:
        if key in mapping and mapping[key] is not None:
            return mapping[key]
    return default


def _normalize_surface(surface: Any) -> str:
    text = str(surface or "plain").strip()
    if text in ("isPlain", "plain"):
        return "plain"
    if text in ("isRound", "round"):
        return "round"
    return text


def _is_truthy_option(val: Any) -> bool:
    if isinstance(val, str):
        return val.strip().lower() not in ("", "0", "false", "no", "none")
    return bool(val)


def _normalize_cut_laser(raw: Any) -> Dict[str, float]:
    if not isinstance(raw, Mapping):
        return {"len_cut": 0.0, "size_item": 0.0, "density": 0.0, "difficulty": 1.0}
    return {
        "len_cut": float(_pick(raw, "len_cut", "lenCut", default=0) or 0),
        "size_item": float(_pick(raw, "size_item", "sizeItem", default=0) or 0),
        "density": float(_pick(raw, "density", default=0) or 0),
        "difficulty": float(_pick(raw, "difficulty", default=1) or 1),
    }


def _from_process(res: Any) -> Dict[str, Any]:
    return {
        "cost": float(res.cost),
        "price": float(res.price),
        "time_hours": float(res.time_hours),
        "time_ready": float(res.time_ready),
        "weight_kg": float(res.weight_kg),
        "materials": list(res.materials or []),
    }


class TabletsCalculator(BaseCalculator):
    """Таблички: резка, УФ, сублимация, карманы, рамка."""

    slug = "tablets"
    name = "Таблички"
    description = "Расчёт стоимости информационных табличек: база, печать, карманы, рамка."

    def get_options(self) -> Dict[str, Any]:
        materials = hardsheet_catalog.list_for_frontend()
        pockets = pocket_catalog.list_for_frontend()
        profiles = profile_catalog.list_for_frontend()
        return {
            "materials": materials,
            "pockets": pockets,
            "profiles": profiles,
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
                    "width": {"type": "number", "minimum": 1, "description": "Ширина, мм"},
                    "height": {"type": "number", "minimum": 1, "description": "Высота, мм"},
                    "material_id": {"type": "string", "description": "Код материала hardsheet"},
                    "material_mode": {
                        "type": "string",
                        "enum": ["isMaterial", "isMaterialCustomer", "noMaterial"],
                        "default": "isMaterial",
                        "description": "Режим учёта материала",
                    },
                    "is_cut_manual": {
                        "type": "string",
                        "description": "Id резака для ручной резки на роликовом резаке (например KeencutEvolutionE2)",
                    },
                    "is_cut_manual_metal": {
                        "type": "string",
                        "description": "Id резака для ручной резки металла (например AccusheadPro12)",
                    },
                    "is_sublimation": {"type": "boolean", "default": False, "description": "Сублимация через heat_press"},
                    "is_cut_laser": {
                        "type": "object",
                        "description": "Параметры лазерной резки (size_item/sizeItem, len_cut/lenCut, density, difficulty)",
                    },
                    "is_grave": {"type": "integer", "description": "Индекс детализации гравировки"},
                    "is_grave_fill": {
                        "type": "array",
                        "items": {"type": "number"},
                        "minItems": 2,
                        "maxItems": 2,
                        "description": "Область сплошной гравировки [w, h], мм",
                    },
                    "is_uv_print": {
                        "type": "object",
                        "description": "УФ-печать: printer_id/printerID, resolution, surface, color, size",
                    },
                    "is_print": {
                        "type": "object",
                        "description": (
                            "Экосольвентная/латексная печать на плёнке ORAJET3640 с накаткой: "
                            "printer_id/printerID (Technojet160ECO, HPLatex335), "
                            "double_application/isDoubleApplication, is_edge/isEdge (isCutEdge, isBendEdge), "
                            "is_lamination/isLamination, size"
                        ),
                    },
                    "is_edge": {
                        "type": "string",
                        "enum": ["isCutEdge", "isBendEdge"],
                        "default": "isCutEdge",
                        "description": "Обработка края плёнки при печати (isCutEdge / isBendEdge)",
                    },
                    "is_lamination": {
                        "type": "boolean",
                        "default": False,
                        "description": "Широкоформатная ламинация плёнки при печати",
                    },
                    "is_film": {
                        "type": "object",
                        "description": (
                            "Аппликация плёнками (StickerCalculator + calc_manual_roll): "
                            "material_id/materialID, size [w, h], size_item/sizeItem, density, "
                            "difficulty, color (число цветов), double_application/isDoubleApplication"
                        ),
                    },
                    "is_background_film": {
                        "type": "object",
                        "description": (
                            "Оклейка фона таблички плёнкой (CutRoller KWTrio3026 + calc_manual_roll): "
                            "material_id/materialID ('0' — без оклейки), is_edge/isEdge (isCutEdge, isBendEdge), size [w, h]"
                        ),
                    },
                    "pocket_id": {"type": "string", "description": "Код кармана (опционально)"},
                    "pocket_count": {"type": "integer", "default": 1, "description": "Кол-во карманов на изделие"},
                    "is_frame": {"type": "boolean", "default": False, "description": "Рамка из профиля"},
                    "frame_profile_id": {"type": "string", "description": "Код профиля рамки"},
                    "frame_segments": {"type": "array", "description": "Сегменты рамки [[длина, кол-во], ...]"},
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
                {"name": "material_id", "type": "enum_cascading", "required": True, "title": "Материал", "choices": {"source": "materials:hardsheet"}},
                {"name": "material_mode", "type": "enum", "required": False, "default": "isMaterial", "title": "Материал в цене",
                 "choices": {"inline": [{"id": "isMaterial", "title": "Учитывать"}, {"id": "noMaterial", "title": "Не учитывать"}, {"id": "isMaterialCustomer", "title": "Материал заказчика (+25%)"}]}},
                {"name": "is_cut_manual", "type": "string", "required": False, "title": "Роликовый резак"},
                {"name": "is_cut_manual_metal", "type": "string", "required": False, "title": "Резак металла"},
                {"name": "is_sublimation", "type": "boolean", "required": False, "default": False, "title": "Сублимация"},
                {"name": "is_cut_laser", "type": "object", "required": False, "title": "Лазерная резка"},
                {"name": "is_grave", "type": "integer", "required": False, "title": "Гравировка (разрешение)"},
                {"name": "is_grave_fill", "type": "array", "required": False, "title": "Область гравировки"},
                {"name": "is_uv_print", "type": "object", "required": False, "title": "УФ-печать"},
                {"name": "is_print", "type": "object", "required": False, "title": "Печать на плёнке (экосольвент/латекс)"},
                {"name": "is_edge", "type": "enum", "required": False, "default": "isCutEdge", "title": "Обработка края плёнки",
                 "choices": {"inline": [{"id": "isCutEdge", "title": "Подрезка"}, {"id": "isBendEdge", "title": "Подгибка"}]}},
                {"name": "is_lamination", "type": "boolean", "required": False, "default": False, "title": "Ламинация плёнки"},
                {"name": "is_film", "type": "object", "required": False, "title": "Аппликация плёнками"},
                {"name": "is_background_film", "type": "object", "required": False, "title": "Оклейка фона плёнкой"},
                {"name": "pocket_id", "type": "enum", "required": False, "title": "Карман", "choices": {"source": "materials:pocket"}},
                {"name": "pocket_count", "type": "integer", "required": False, "default": 1, "title": "Карманов на изделие"},
                {"name": "is_frame", "type": "boolean", "required": False, "default": False, "title": "Рамка"},
                {"name": "frame_profile_id", "type": "enum", "required": False, "title": "Профиль рамки", "default": DEFAULT_PROFILE, "choices": {"source": "materials:profile"}},
                {"name": "mode", "type": "enum", "required": False, "default": 1, "title": "Режим",
                 "choices": {"inline": [{"id": 0, "title": "Эконом"}, {"id": 1, "title": "Стандарт"}, {"id": 2, "title": "Экспресс"}]}},
            ],
            "param_groups": {
                "main": ["quantity", "width", "height"],
                "material": ["material_id", "material_mode"],
                "cut": ["is_cut_manual", "is_cut_manual_metal", "is_cut_laser", "is_grave", "is_grave_fill"],
                "print": ["is_uv_print", "is_print", "is_edge", "is_lamination", "is_film", "is_background_film", "is_sublimation"],
                "options": ["pocket_id", "pocket_count", "is_frame", "frame_profile_id"],
                "mode": ["mode"],
            },
        }

    def _cut_manual(
        self,
        n: int,
        size: Sequence[float],
        material_id: str,
        cutter_id: str,
        material_mode: str,
        mode: int,
    ) -> Dict[str, Any]:
        return CutRollerCalculator().calculate({
            "quantity": n,
            "width": size[0],
            "height": size[1],
            "material_id": material_id,
            "cutter_code": cutter_id,
            "material_mode": material_mode,
            "mode": mode,
        })

    def _cut_manual_metal(
        self,
        n: int,
        size: Sequence[float],
        material_id: str,
        cutter_id: str,
        mode: int,
    ) -> Dict[str, Any]:
        margins = [0.0, 0.0, 0.0, 0.0]
        interval = 1.0
        size_sheet: List[float] = [210.0, 297.0]
        layout = layout_on_sheet(size, size_sheet, margins, interval)
        if layout["num"] == 0:
            size_sheet = [420.0, 297.0]
            layout = layout_on_sheet(size, size_sheet, margins, interval)
            if layout["num"] == 0:
                raise ValueError("Изделие не помещается на материал")
        num_sheet = n / layout["num"]
        cut = calc_cut_saber(
            num_sheet=num_sheet,
            size=size,
            size_sheet=size_sheet,
            material_id=material_id,
            cutter_id=cutter_id,
            margins=margins,
            interval=interval,
            mode=mode,
        )
        material = hardsheet_catalog.get(material_id)
        sheet = material.sizes[0] if material.sizes else [3050.0, 2050.0]
        area_material = n * (size[0] + interval) * (size[1] + interval)
        num_material_sheet = area_material / (sheet[0] * sheet[1])
        cost = float(cut.cost) + num_material_sheet * float(material.cost or 0)
        price = float(cut.price) + num_material_sheet * float(material.cost or 0) * (1 + MARGIN_MATERIAL)
        weight = float(cut.weight_kg) + (
            area_material * float(material.thickness or 0) * float(material.density or 0) / 1_000_000.0
        )
        return {
            "cost": cost,
            "price": price,
            "time_hours": float(cut.time_hours),
            "time_ready": float(cut.time_ready),
            "weight_kg": weight,
            "materials": [
                material_line(
                    code=material_id,
                    name=material.description,
                    title=material.title,
                    quantity=num_material_sheet,
                    unit="лист",
                    size_mm=[float(sheet[0]), float(sheet[1])],
                )
            ],
        }

    def _sublimation(
        self,
        n: int,
        size: Sequence[float],
        mode: int,
    ) -> Dict[str, Any]:
        size_print: List[float] = [210.0, 297.0]
        margins = [5.0, 5.0, 5.0, 5.0]
        interval = 1.0
        layout = layout_on_sheet(size, size_print, margins, interval)
        if layout["num"] == 0:
            size_print = [420.0, 297.0]
            layout = layout_on_sheet(size, size_print, margins, interval)
            if layout["num"] == 0:
                raise ValueError("Изделие не помещается на материал")
        num_sheet = math.ceil(n / layout["num"])
        return HeatPressCalculator().calculate({
            "quantity": num_sheet,
            "width": size_print[0],
            "height": size_print[1],
            "transfer_type": "sublimation",
            "item_type": "metal",
            "mode": mode,
        })

    def _uv_print(
        self,
        n: int,
        size: Sequence[float],
        raw: Any,
        mode: int,
        *,
        is_customer_material: bool = False,
    ) -> Dict[str, Any]:
        opts: Mapping[str, Any] = raw if isinstance(raw, Mapping) else {}
        size_print_raw = _pick(opts, "size")
        if isinstance(size_print_raw, (list, tuple)) and len(size_print_raw) >= 2:
            size_print = [float(size_print_raw[0]), float(size_print_raw[1])]
        else:
            size_print = [float(size[0]), float(size[1])]
        printer = str(
            _pick(opts, "printer_id", "printerID", "printer_code", default=DEFAULT_UV_PRINTER)
            or DEFAULT_UV_PRINTER
        ).strip() or DEFAULT_UV_PRINTER
        return UVPrintCalculator().calculate({
            "quantity": n,
            "width": size_print[0],
            "height": size_print[1],
            "item_width": size_print[0],
            "item_height": size_print[1],
            "resolution": int(_pick(opts, "resolution", default=0) or 0),
            "color": str(_pick(opts, "color", default="4+0") or "4+0").strip(),
            "surface": _normalize_surface(_pick(opts, "surface", default="plain")),
            "double_application": bool(
                _pick(opts, "double_application", "isDoubleApplication", "is_double_application", default=False)
            ),
            "is_customer_material": is_customer_material,
            "printer_code": printer,
            "mode": mode,
        })

    def _print_roll(
        self,
        n: int,
        size: Sequence[float],
        raw: Any,
        mode: int,
        *,
        default_edge: Any = None,
        default_lamination: Any = None,
    ) -> List[Dict[str, Any]]:
        opts: Mapping[str, Any] = raw if isinstance(raw, Mapping) else {}
        size_print_raw = _pick(opts, "size")
        if isinstance(size_print_raw, (list, tuple)) and len(size_print_raw) >= 2:
            size_print = [float(size_print_raw[0]), float(size_print_raw[1])]
        else:
            size_print = [float(size[0]), float(size[1])]
        printer = str(
            _pick(opts, "printer_id", "printerID", "printer_code", default=DEFAULT_ROLL_PRINTER)
            or DEFAULT_ROLL_PRINTER
        ).strip() or DEFAULT_ROLL_PRINTER
        double_app = bool(
            _pick(opts, "double_application", "isDoubleApplication", "is_double_application", default=False)
        )
        n_print = n * (2 if double_app else 1)

        edge_raw = _pick(opts, "is_edge", "isEdge", "edge", default=default_edge)
        edge = str(edge_raw or "isCutEdge").strip() or "isCutEdge"
        lam_raw = _pick(
            opts,
            "is_lamination",
            "isLamination",
            "lamination_id",
            "lamination",
            default=default_lamination,
        )
        is_lamination = _is_truthy_option(lam_raw)

        print_part = PrintRollCalculator().calculate({
            "quantity": n_print,
            "width": size_print[0],
            "height": size_print[1],
            "material_id": "ORAJET3640",
            "printer_code": printer,
            "is_lamination": is_lamination,
            "mode": mode,
        })
        roll_res = calc_manual_roll(
            n_print,
            size_print,
            {"isEdge": edge},
            mode,
        )
        return [print_part, _from_process(roll_res)]

    def _film_application(
        self,
        n: int,
        size: Sequence[float],
        raw: Any,
        mode: int,
    ) -> List[Dict[str, Any]]:
        opts: Mapping[str, Any] = raw if isinstance(raw, Mapping) else {}
        film_material_id = str(_pick(opts, "material_id", "materialID", default="") or "").strip()
        if not film_material_id or film_material_id == "0":
            raise ValueError("Не выбрана плёнка для аппликации")

        size_raw = _pick(opts, "size")
        if (
            isinstance(size_raw, (list, tuple))
            and len(size_raw) >= 2
            and float(size_raw[0] or 0) > 0
            and float(size_raw[1] or 0) > 0
        ):
            size_app = [float(size_raw[0]), float(size_raw[1])]
        else:
            size_app = [float(size[0]), float(size[1])]

        size_item = float(_pick(opts, "size_item", "sizeItem", default=0) or 0)
        if size_item <= 0:
            size_item = size_app[0]
        density = float(_pick(opts, "density", default=0) or 0)
        difficulty = float(_pick(opts, "difficulty", default=1) or 1)
        color_count = int(float(_pick(opts, "color", default=1) or 1))
        if color_count < 1:
            color_count = 1
        double_app = bool(
            _pick(opts, "double_application", "isDoubleApplication", "is_double_application", default=False)
        )
        n_film = n * (2 if double_app else 1) * color_count

        sticker_part = StickerCalculator().calculate({
            "quantity": n_film,
            "width": size_app[0],
            "height": size_app[1],
            "size_item": size_item,
            "density": density,
            "difficulty": difficulty,
            "material_id": film_material_id,
            "is_mounting_film": True,
            "mode": mode,
        })
        roll_res = calc_manual_roll(n_film, size, {}, mode)
        return [sticker_part, _from_process(roll_res)]

    def _background_film(
        self,
        n: int,
        size: Sequence[float],
        raw: Any,
        mode: int,
        *,
        raw_film: Any = None,
    ) -> List[Dict[str, Any]]:
        opts: Mapping[str, Any] = raw if isinstance(raw, Mapping) else {}
        bg_material_id = str(_pick(opts, "material_id", "materialID", default="") or "").strip()
        if not bg_material_id or bg_material_id == "0":
            return []

        size_raw = _pick(opts, "size")
        if (
            isinstance(size_raw, (list, tuple))
            and len(size_raw) >= 2
            and float(size_raw[0] or 0) > 0
            and float(size_raw[1] or 0) > 0
        ):
            size_bg = [float(size_raw[0]), float(size_raw[1])]
        else:
            size_bg = [float(size[0]), float(size[1])]

        edge = (
            str(_pick(opts, "is_edge", "isEdge", "edge", default="isCutEdge") or "isCutEdge").strip()
            or "isCutEdge"
        )

        # Как в calcTablets.js: doubleApplication = options.get('isFilm')['isBackgroundFilm'] ? 2 : 1
        # (расхождение формы с полем 3313 и функции calcTablets.js не исправляем).
        film_opts: Mapping[str, Any] = raw_film if isinstance(raw_film, Mapping) else {}
        double_bg = _is_truthy_option(_pick(film_opts, "isBackgroundFilm", "is_background_film", default=False))
        n_bg = n * (2 if double_bg else 1)

        cut_part = CutRollerCalculator().calculate({
            "quantity": n_bg,
            "width": size_bg[0],
            "height": size_bg[1],
            "material_id": bg_material_id,
            "cutter_code": "KWTrio3026",
            "material_mode": "isMaterial",
            "mode": mode,
        })
        # В calcTablets.js costCutBackgroundFilm.timeReady не входит в Math.max(...timeReady).
        cut_part_no_ready = {**cut_part, "time_ready": 0.0}
        roll_res = calc_manual_roll(n_bg, size_bg, {"isEdge": edge}, mode)
        return [cut_part_no_ready, _from_process(roll_res)]

    def _pocket_items(self, params: Mapping[str, Any]) -> List[Mapping[str, Any]]:
        raw = params.get("is_pocket")
        if raw is None:
            raw = params.get("isPocket")
        if isinstance(raw, Mapping):
            return [raw]
        if isinstance(raw, (list, tuple)):
            return [item for item in raw if isinstance(item, Mapping)]
        pocket_id = params.get("pocket_id")
        if pocket_id:
            return [{
                "pocket_id": pocket_id,
                "n": params.get("pocket_count", 1),
            }]
        return []

    def _pockets_part(self, n: int, items: Sequence[Mapping[str, Any]], mode: int) -> Dict[str, Any] | None:
        """Сумма calcPockets. time_ready — максимум по карманам, как в calcTablets."""
        cost = price = time_hours = weight = ready = 0.0
        materials: List[Dict[str, Any]] = []
        used = False
        for item in items:
            pocket_n = float(_pick(item, "n", "count", default=1) or 0)
            if pocket_n <= 0:
                continue
            pocket_id = str(_pick(item, "pocket_id", "pocketID", default="") or "").strip()
            size = _pick(item, "size", default=None)
            width = height = 0.0
            if isinstance(size, (list, tuple)) and len(size) >= 2:
                width, height = float(size[0] or 0), float(size[1] or 0)
            border = str(_pick(item, "border_id", "borderID", default="") or "")
            material_id = str(_pick(item, "material_id", "materialID", default="") or "")
            res = PocketsCalculator().calculate({
                "quantity": pocket_n * n,
                "pocket_id": pocket_id,
                "width": width,
                "height": height,
                "material_id": material_id,
                "border_id": border,
                "mode": mode,
            })
            used = True
            cost += float(res["cost"])
            price += float(res["price"])
            time_hours += float(res["time_hours"])
            weight += float(res["weight_kg"])
            ready = max(ready, float(res["time_ready"]))
            materials.extend(res.get("materials") or [])
        if not used:
            return None
        return {
            "cost": cost,
            "price": price,
            "time_hours": time_hours,
            "time_ready": ready,
            "weight_kg": weight,
            "materials": materials,
        }

    def _frame_part(
        self,
        n: int,
        size: Sequence[float],
        params: Mapping[str, Any],
        mode: int,
    ) -> Dict[str, Any] | None:
        """Рамка. time_ready рамки в Math.max calcTablets не входит — здесь 0."""
        raw = params.get("is_frame")
        if raw is None:
            raw = params.get("isFrame")
        if raw is None or raw is False:
            return None
        if isinstance(raw, str) and raw.strip().lower() in ("", "0", "false", "no"):
            return None
        segments = None
        if isinstance(raw, Mapping):
            profile_id = str(_pick(raw, "profile_id", "profileID", default="") or "").strip()
            segments = raw.get("segments")
        elif raw is True:
            profile_id = str(params.get("frame_profile_id") or DEFAULT_PROFILE).strip() or DEFAULT_PROFILE
            segments = params.get("frame_segments")
        else:
            profile_id = str(raw).strip()
            segments = params.get("frame_segments")
        if not profile_id or profile_id in ("no", "0"):
            return None
        if not segments:
            segments = [[size[0], 2], [size[1], 2]]
        hanger = params.get("is_hanger")
        if hanger is None:
            hanger = params.get("isHanger")
        res = FrameCalculator().calculate({
            "quantity": n,
            "profile_id": profile_id,
            "segments": segments,
            "is_hanger": hanger if isinstance(hanger, Mapping) else {},
            "mode": mode,
        })
        return {
            "cost": float(res["cost"]),
            "price": float(res["price"]),
            "time_hours": float(res["time_hours"]),
            "time_ready": 0.0,
            "weight_kg": float(res["weight_kg"]),
            "materials": list(res.get("materials") or []),
        }

    def _eva_parts(self, n: int, raw: Any, mode: int) -> List[Dict[str, Any]]:
        """EVA: резка и накатка. Их timeReady в максимум calcTablets не входят."""
        if not isinstance(raw, Mapping):
            return []
        eva_id = str(_pick(raw, "eva_foam_id", "evaFoamID", default="") or "").strip()
        if not eva_id or eva_id in ("no", "0"):
            return []
        size_raw = _pick(raw, "size", default=None)
        if not isinstance(size_raw, (list, tuple)) or len(size_raw) < 2:
            raise ValueError("Не задан размер EVA-листа")
        size_foam = [float(size_raw[0]), float(size_raw[1])]
        if size_foam[0] <= 0 or size_foam[1] <= 0:
            raise ValueError("Размер EVA-листа должен быть положительным")
        cut = self._cut_manual(n, size_foam, eva_id, "KeencutEvolutionE2", "isMaterial", mode)
        roll = calc_manual_roll(n, size_foam, {}, mode)
        roll_part = _from_process(roll)
        roll_part["weight_kg"] = 0.0
        roll_part["time_ready"] = 0.0
        cut["time_ready"] = 0.0
        return [cut, roll_part]

    def calculate(self, params: Mapping[str, Any]) -> Dict[str, Any]:
        n = int(params.get("quantity", 1))
        width = float(params.get("width", 0))
        height = float(params.get("height", 0))
        size = [width, height]
        material_id = str(params.get("material_id", "")).strip()
        material_mode = str(params.get("material_mode", "isMaterial") or "isMaterial").strip() or "isMaterial"
        mode = ProductionMode(int(params.get("mode", 1)))

        is_cut_manual = params.get("is_cut_manual")
        is_cut_manual_metal = params.get("is_cut_manual_metal")
        is_sublimation = bool(params.get("is_sublimation", False))
        has_cut_laser = "is_cut_laser" in params and params.get("is_cut_laser") is not None
        is_grave = params.get("is_grave")
        is_grave_fill = params.get("is_grave_fill")
        has_uv = "is_uv_print" in params and params.get("is_uv_print") is not None
        raw_print = params.get("is_print")
        has_print = raw_print is not None and raw_print is not False
        raw_film = params.get("is_film")
        has_film = raw_film is not None and raw_film is not False
        raw_bg_film = params.get("is_background_film")
        has_bg_film = raw_bg_film is not None and raw_bg_film is not False

        raw_eva = params.get("is_eva_foam")
        if raw_eva is None:
            raw_eva = params.get("isEVAFoam")

        if width <= 0 or height <= 0:
            raise ValueError("Ширина и высота должны быть положительными")
        if not material_id:
            raise ValueError("material_id обязателен")

        parts: List[Dict[str, Any]] = []

        # Ручная резка на роликовом резаке + материал (calcCutRoller)
        if is_cut_manual and not is_cut_manual_metal:
            cutter_id = (
                "KeencutEvolutionE2"
                if is_cut_manual is True
                else str(is_cut_manual).strip()
            )
            if cutter_id:
                parts.append(self._cut_manual(n, size, material_id, cutter_id, material_mode, mode.value))

        # Ручная резка металла + материал (calcCutSaber + раскладка A4/A3)
        if is_cut_manual_metal:
            cutter_id = str(is_cut_manual_metal).strip()
            if cutter_id:
                parts.append(self._cut_manual_metal(n, size, material_id, cutter_id, mode.value))

        # Лазерная резка (+ гравировка)
        if has_cut_laser or is_grave is not None:
            laser_params: MutableMapping[str, Any] = {
                "quantity": n,
                "width": width,
                "height": height,
                "material_id": material_id,
                "material_mode": material_mode,
                "mode": mode.value,
            }
            if has_cut_laser:
                laser_params["is_cut_laser"] = _normalize_cut_laser(params.get("is_cut_laser"))
            if is_grave is not None:
                laser_params["is_grave"] = int(is_grave)
            if is_grave_fill is not None:
                laser_params["is_grave_fill"] = is_grave_fill
            parts.append(LaserCalculator().calculate(laser_params))

        # Сублимация (calcHeatPress на раскладке A4/A3)
        if is_sublimation:
            parts.append(self._sublimation(n, size, mode.value))

        # УФ-печать поверх резки, не вместо
        if has_uv:
            parts.append(
                self._uv_print(
                    n,
                    size,
                    params.get("is_uv_print"),
                    mode.value,
                    is_customer_material=(material_mode == "isMaterialCustomer"),
                )
            )

        # Нанесение плёнкой с экосольвентной/латексной печатью (calcPrintRoll + calcManualRoll)
        if has_print:
            parts.extend(
                self._print_roll(
                    n,
                    size,
                    raw_print,
                    mode.value,
                    default_edge=params.get("is_edge"),
                    default_lamination=params.get("is_lamination"),
                )
            )

        # Нанесение аппликации плёнками (calcSticker + calcManualRoll)
        if has_film:
            parts.extend(self._film_application(n, size, raw_film, mode.value))

        # Оклейка фона таблички плёнкой (calcCutRoller KWTrio3026 + calcManualRoll)
        if has_bg_film:
            parts.extend(self._background_film(n, size, raw_bg_film, mode.value, raw_film=raw_film))

        pocket_part = self._pockets_part(n, self._pocket_items(params), mode.value)
        if pocket_part:
            parts.append(pocket_part)

        frame_part = self._frame_part(n, size, params, mode.value)
        if frame_part:
            parts.append(frame_part)

        if raw_eva is not None and raw_eva is not False:
            parts.extend(self._eva_parts(n, raw_eva, mode.value))

        cost_total = sum(float(p["cost"]) for p in parts)
        price_parts = sum(float(p["price"]) for p in parts)
        time_total = sum(float(p["time_hours"]) for p in parts)
        weight_total = sum(float(p["weight_kg"]) for p in parts)
        time_ready_components = [float(p["time_ready"]) for p in parts]
        materials_out: List[Dict[str, Any]] = []
        for p in parts:
            materials_out.extend(p.get("materials") or [])

        margin_tablet = get_margin("marginTablets")
        price_total = price_parts * (1 + margin_tablet)
        time_hours = math.ceil(time_total * 100) / 100.0
        # Как в JS: result.time + Math.max(...component.timeReady)
        time_ready = time_hours + (max(time_ready_components) if time_ready_components else 0.0)
        weight_kg = math.ceil(weight_total * 100) / 100.0

        return {
            "cost": float(cost_total),
            "price": float(price_total),
            "unit_price": round(float(price_total) / max(1, n), 2),
            "time_hours": time_hours,
            "time_ready": time_ready,
            "weight_kg": weight_kg,
            "materials": materials_out,
        }
