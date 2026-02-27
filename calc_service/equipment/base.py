from __future__ import annotations

from typing import Dict, List, Optional, Sequence, Tuple, Any

from pydantic import BaseModel, Field

from common.markups import BASE_TIME_READY, COST_OPERATOR


class LookupTable:
    """
    Таблица вида [(порог, значение), ...] с поиском по первому порогу ≥ value.
    """

    def __init__(self, data: Sequence[Sequence[float]]) -> None:
        if not data:
            raise ValueError("LookupTable data must not be empty")
        # Нормализуем кортежи и сортируем по порогу
        self._data: List[Tuple[float, float]] = sorted(
            [(float(th), float(val)) for th, val in data],
            key=lambda pair: pair[0],
        )

    def find(self, value: float) -> float:
        """
        Вернуть значение для первого порога ≥ value.
        Если такого порога нет — вернуть последнее значение.
        """
        x = float(value)
        last_val = self._data[-1][1]
        for threshold, val in self._data:
            if x <= threshold:
                return val
        return last_val


class EquipmentSpec(BaseModel):
    """
    Базовая модель оборудования.
    См. docs/data-formats.md для структуры JSON.
    """

    code: str
    name: str
    category: str

    max_size: Optional[List[float]] = None
    margins: Optional[List[float]] = None

    purchase_cost: float = 0.0
    depreciation_years: float = 10.0
    work_days_year: int = 250
    hours_per_day: float = 4.0

    cost_operator: float = 0.0  # 0 = брать из common

    time_prepare: float = 0.0  # часов
    time_load: float = 0.0  # часов

    base_time_ready: Optional[List[float]] = None  # [экономичный, стандартный, экспресс]

    defect_table: Optional[List[Tuple[float, float]]] = None

    available: bool = True

    @property
    def depreciation_per_hour(self) -> float:
        """
        Амортизация оборудования в руб./час.
        """
        years = float(self.depreciation_years)
        days = float(self.work_days_year)
        hours = float(self.hours_per_day)
        denom = years * days * hours
        if denom <= 0:
            return 0.0
        return float(self.purchase_cost) / denom

    @property
    def operator_cost_per_hour(self) -> float:
        """
        Стоимость часа оператора.
        Если cost_operator == 0, берём глобальное значение из common.markups.
        """
        if self.cost_operator > 0:
            return float(self.cost_operator)
        return float(COST_OPERATOR)

    def get_defect_rate(self, quantity: float) -> float:
        """
        Вернуть процент брака для заданного тиража.
        Если таблица не задана — 0.0.
        """
        if not self.defect_table:
            return 0.0
        table = LookupTable(self.defect_table)
        return float(table.find(float(quantity)))

    def get_time_ready(self, mode: int) -> float:
        """
        Вернуть базовый срок изготовления в рабочих часах для режима.

        mode: 1 — экономичный, 2 — стандартный, 3 — экспресс.
        Индекс зажимается в пределах массива.
        """
        times = self.base_time_ready or BASE_TIME_READY
        if not times:
            return 0.0
        idx = max(0, min(len(times) - 1, int(mode) - 1))
        return float(times[idx])


class LaserSpec(EquipmentSpec):
    """
    Спецификация лазерного оборудования.
    """

    cut_speed_table: List[Tuple[float, float]] = Field(default_factory=list)
    grave_speed_table: List[float] = Field(default_factory=list)

    laser_tube_cost: float = 0.0
    laser_tube_life_hours: float = 1.0

    power_cost_per_kwh: float = 0.0
    power_consumption_kwh: float = 0.0

    cost_cut_extra: float = 0.0
    cost_grave_extra: float = 0.0

    @property
    def consumables_per_hour(self) -> float:
        """
        Себестоимость расходников в руб./час:
        трубка + электроэнергия.
        """
        tube_part = 0.0
        if self.laser_tube_life_hours > 0:
            tube_part = self.laser_tube_cost / self.laser_tube_life_hours
        power_part = self.power_cost_per_kwh * self.power_consumption_kwh
        return float(tube_part + power_part)

    def get_cut_speed(self, thickness_mm: float) -> float:
        """
        Скорость резки (м/час) в зависимости от толщины, через LookupTable.
        """
        if not self.cut_speed_table:
            return 0.0
        table = LookupTable(self.cut_speed_table)
        return float(table.find(float(thickness_mm)))

    def get_grave_speed(self, resolution_index: int) -> float:
        """
        Скорость гравировки (м²/час) по индексу в grave_speed_table.

        resolution_index — целый индекс (0, 1, 2, ...).
        Если индекс выходит за границы, берётся ближайшее допустимое значение.
        """
        if not self.grave_speed_table:
            return 0.0
        idx = max(0, min(len(self.grave_speed_table) - 1, int(resolution_index)))
        return float(self.grave_speed_table[idx])


class EquipmentCatalog:
    """
    Каталог оборудования одной категории (например, 'laser', 'printer').
    """

    def __init__(self, category: str) -> None:
        self.category: str = category
        self._items: Dict[str, EquipmentSpec] = {}

    def add(self, spec: EquipmentSpec) -> None:
        self._items[spec.code] = spec

    def get(self, code: str) -> EquipmentSpec:
        try:
            return self._items[code]
        except KeyError:
            raise KeyError(f"Unknown equipment code: {code!r}") from None

    def find_for_width(self, width_mm: float) -> Optional[EquipmentSpec]:
        """
        Найти оборудование с минимальной подходящей шириной max_size[0] ≥ width_mm.
        Если подходящего нет — вернуть None.
        """
        target = float(width_mm)
        best: Optional[EquipmentSpec] = None
        best_width: Optional[float] = None

        for spec in self._items.values():
            if not spec.max_size or len(spec.max_size) == 0:
                continue
            w = float(spec.max_size[0])
            if w < target:
                continue
            if best is None or w < best_width:
                best = spec
                best_width = w

        return best

