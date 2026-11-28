"""
Карманы для стендов.

Порт insaincalc.calcPockets из js_legacy/calc/calcTablets.js.
Каталожный карман считается в режиме 0: в JS mode сбрасывается,
если pocketID найден в справочнике. Наценка marginTablets
накладывается здесь один раз, как в calcPockets; calcTablets
умножает цену ещё раз.
"""

from __future__ import annotations

import math
from typing import Any, Dict, List, Mapping, Optional, Sequence

from calculators.base import BaseCalculator, material_line, parse_mode
from calculators.laser import LaserCalculator
from common.markups import COST_OPERATOR, MARGIN_MATERIAL, MARGIN_OPERATION, get_margin
from common.process_tools import calc_put_tape
from materials import pocket as pocket_catalog


def _size_of(raw: Mapping[str, Any], fallback: Sequence[float]) -> List[float]:
    size = raw.get("size")
    if isinstance(size, (list, tuple)) and len(size) >= 2:
        return [float(size[0]), float(size[1])]
    if len(fallback) >= 2 and float(fallback[0]) > 0 and float(fallback[1]) > 0:
        return [float(fallback[0]), float(fallback[1])]
    raise ValueError("Не задан размер кармана")


class PocketsCalculator(BaseCalculator):
    """Один карман: заготовка или лазер, монтаж, окантовка."""

    slug = "pockets"
    name = "Карманы"
    description = "Расчёт кармана для стенда: заготовка, скотч или крепёж, окантовка."
    is_public = False

    def get_options(self) -> Dict[str, Any]:
        return {"pockets": pocket_catalog.list_for_frontend()}

    def get_tool_schema(self) -> Dict[str, Any]:
        return {
            "name": "calc_pockets",
            "description": self.description,
            "parameters": {
                "type": "object",
                "properties": {
                    "quantity": {"type": "integer", "minimum": 1},
                    "pocket_id": {"type": "string"},
                    "width": {"type": "number"},
                    "height": {"type": "number"},
                    "material_id": {"type": "string"},
                    "border_id": {"type": "string"},
                    "mode": {"type": "integer"},
                },
                "required": ["quantity"],
            },
        }

    def calculate(self, params: Mapping[str, Any]) -> Dict[str, Any]:
        n = int(params.get("quantity", 1) or 0)
        if n < 1:
            raise ValueError("Количество карманов должно быть положительным")
        pocket_id = str(params.get("pocket_id", "") or "").strip()
        material_id = str(params.get("material_id", "") or "").strip()
        border_id = str(params.get("border_id", "") or "").strip()
        if border_id in ("", "0", "no", "No"):
            border_id = ""
        fallback_size = [float(params.get("width") or 0), float(params.get("height") or 0)]
        mode = int(parse_mode(params.get("mode", 1)))

        raw: Optional[Dict[str, Any]] = None
        if pocket_id:
            try:
                from common.process_tools import _get_raw_material

                raw = _get_raw_material("pocket", pocket_id)
            except KeyError:
                raw = None
        if raw is not None:
            # Как в calcPockets: стандартный карман из справочника не ждёт подготовку.
            mode = 0
            size = _size_of(raw, fallback_size)
            material_id = str(raw.get("materialID") or material_id or "")
        else:
            if not pocket_id and not material_id:
                raise ValueError("Не выбран карман")
            size = _size_of({}, fallback_size)
            raw = {"size": size, "materialID": material_id}

        materials: List[Dict[str, Any]] = []
        pocket_cost = 0.0
        pocket_price = 0.0
        pocket_time = 0.0
        pocket_ready = 0.0
        pocket_weight = 0.0

        if raw.get("cost") is None:
            if not material_id:
                raise ValueError("Не задан материал кармана")
            laser = LaserCalculator().calculate({
                "quantity": n,
                "width": size[0],
                "height": size[1],
                "material_id": material_id,
                "material_mode": "isMaterial",
                "is_cut_laser": {
                    "size_item": min(size[0], size[1]),
                    "density": 0,
                    "difficulty": 1,
                    "len_cut": 0,
                },
                "mode": mode,
            })
            pocket_cost = float(laser["cost"])
            pocket_price = float(laser["price"])
            pocket_time = float(laser["time_hours"])
            pocket_ready = float(laser["time_ready"])
            pocket_weight = float(laser["weight_kg"])
            materials.extend(laser.get("materials") or [])
        else:
            spec = pocket_catalog.get(pocket_id)
            unit_cost = float(raw.get("cost") or 0)
            pocket_cost = unit_cost * n
            pocket_price = pocket_cost * (1 + MARGIN_MATERIAL)
            pocket_weight = float(raw.get("weight") or 0) * n / 1000
            size_mm = [float(x) for x in raw.get("size") or size]
            materials.append(material_line(
                code=pocket_id,
                name=spec.description,
                title=spec.title,
                quantity=n,
                unit="шт",
                size_mm=size_mm,
            ))

        put_cost = 0.0
        put_price = 0.0
        put_time = 0.0
        put_ready = 0.0
        put_weight = 0.0
        mount = str(raw.get("mountID") or "")
        if mount == "tape":
            tape_id = str(raw.get("tapeID") or "")
            tape_segments = [[1, size[0]], [2, size[1]]]
            if tape_id:
                taped = calc_put_tape(n, tape_segments, tape_id, 2, mode)
                put_cost += taped.cost
                put_price += taped.price
                put_time += taped.time_hours
                put_weight += taped.weight_kg
                put_ready = max(put_ready, taped.time_ready)
                materials.extend(taped.materials)
            if border_id:
                border = calc_put_tape(n, tape_segments, border_id, 2, mode)
                put_cost += border.cost
                put_price += border.price
                put_time += border.time_hours
                put_weight += border.weight_kg
                put_ready = max(put_ready, border.time_ready)
                materials.extend(border.materials)
            time_put = n * 2 / 60
            cost_operator = time_put * COST_OPERATOR
            put_cost += cost_operator
            put_price += cost_operator * (1 + MARGIN_OPERATION)
            put_time += time_put
        elif mount in ("metalcap", "standoff"):
            from common.process_tools import _get_material, _get_raw_material

            time_put = 0.0
            furn_cost = 0.0
            furn_weight = 0.0
            for item in raw.get("setFasteners") or []:
                fastener_id = str(item[0])
                num_fastener = float(item[1]) * n
                fastener = _get_material("attachment", fastener_id)
                fastener_raw = _get_raw_material("attachment", fastener_id)
                time_put += 0.5 / 60 * num_fastener
                furn_cost += float(fastener.cost or 0) * num_fastener
                furn_weight += float(fastener_raw.get("weight") or 0) * num_fastener / 1000
                materials.append(material_line(
                    code=fastener_id,
                    name=fastener.description,
                    title=fastener.title,
                    quantity=num_fastener,
                    unit="шт",
                    size_mm=[float(x) for x in (fastener_raw.get("size") or [0, 0])],
                ))
            cost_operator = time_put * COST_OPERATOR
            put_cost += furn_cost + cost_operator
            put_price += furn_cost * (1 + MARGIN_MATERIAL) + cost_operator * (1 + MARGIN_OPERATION)
            put_time += time_put
            put_weight += furn_weight

        margin_tablets = get_margin("marginTablets")
        cost = pocket_cost + put_cost
        price = (pocket_price + put_price) * (1 + margin_tablets)
        time_hours = pocket_time + put_time
        weight_kg = pocket_weight + put_weight
        time_ready = time_hours + max(pocket_ready, put_ready)
        return {
            "cost": float(cost),
            "price": float(price),
            "unit_price": round(float(price) / n, 2),
            "time_hours": float(time_hours),
            "time_ready": float(time_ready),
            "weight_kg": float(weight_kg),
            "materials": materials,
        }
