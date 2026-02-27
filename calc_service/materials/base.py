from __future__ import annotations

from typing import Dict, List, Optional, Sequence, Tuple

from pydantic import BaseModel

from common.helpers import find_in_table


class MaterialSpec(BaseModel):
    """
    Описание варианта материала, развёрнутое из JSON.
    См. форматы в docs/data-formats.md.
    """

    code: str
    group: str
    name: str
    category: str

    cost: Optional[float] = None
    cost_tiers: Optional[List[Tuple[float, float]]] = None

    sizes: List[List[float]]
    min_size: Optional[List[float]] = None

    is_roll: bool = False
    roll_width: Optional[float] = None
    length_min: Optional[float] = None

    thickness: Optional[float] = None
    density: Optional[float] = None
    density_unit: str = "г/см³"
    weight_per_unit: Optional[float] = None

    available: bool = True

    def get_cost(self, quantity_or_area: float = 1.0) -> float:
        """
        Вернуть стоимость единицы (материала или площади) с учётом градаций.

        Если заданы cost_tiers, используется find_in_table([(порог, цена), ...], quantity_or_area).
        Иначе возвращается фиксированная cost (или 0.0, если она не указана).
        """
        if self.cost_tiers:
            return float(find_in_table(self.cost_tiers, float(quantity_or_area)))
        if self.cost is not None:
            return float(self.cost)
        return 0.0


class MaterialCatalog:
    """
    Каталог материалов одной категории (например, "hardsheet").
    """

    def __init__(self, category: str) -> None:
        self.category: str = category
        self._items: Dict[str, MaterialSpec] = {}
        self._groups: Dict[str, List[MaterialSpec]] = {}

    def add(self, spec: MaterialSpec) -> None:
        """
        Добавить материал в каталог.
        Последующее добавление с тем же code перезапишет имеющийся.
        """
        self._items[spec.code] = spec
        self._groups.setdefault(spec.group, []).append(spec)

    def get(self, code: str) -> MaterialSpec:
        """
        Найти материал по коду. Бросает KeyError, если не найден.
        """
        try:
            return self._items[code]
        except KeyError:
            raise KeyError(f"Unknown material code: {code!r}") from None

    def get_group(self, group: str) -> List[MaterialSpec]:
        """
        Вернуть все варианты материала в группе (может быть пустой список).
        """
        return list(self._groups.get(group, []))

    def list_all(self) -> Dict[str, MaterialSpec]:
        """
        Все материалы каталога в виде словаря code -> MaterialSpec.
        """
        return dict(self._items)

    def list_for_frontend(self) -> List[Dict[str, Optional[float] | str]]:
        """
        Список материалов для фронтенда:
        только доступные (available == True) и поля:
          - code
          - group
          - name
          - thickness
        """
        result: List[Dict[str, Optional[float] | str]] = []
        for m in self._items.values():
            if not m.available:
                continue
            result.append(
                {
                    "code": m.code,
                    "group": m.group,
                    "name": m.name,
                    "thickness": m.thickness,
                }
            )
        return result

    def filter_by_thickness(self, max_mm: float) -> List[MaterialSpec]:
        """
        Вернуть материалы с толщиной <= max_mm.
        Материалы без thickness игнорируются.
        """
        limit = float(max_mm)
        return [
            m
            for m in self._items.values()
            if m.thickness is not None and m.thickness <= limit
        ]

