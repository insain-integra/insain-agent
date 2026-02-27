from __future__ import annotations

from pathlib import Path

import pytest

from common.markups import BASE_TIME_READY
from equipment import ALL_EQUIPMENT, get_all_equipment_options, get_equipment
from equipment.base import LaserSpec, LookupTable
from equipment.loader import load_generic_catalog, load_laser_catalog


DATA_DIR = Path(__file__).resolve().parent.parent / "data" / "equipment"


def test_lookup_table():
    table = LookupTable([(0.5, 200), (1.0, 120), (2.0, 60)])

    assert table.find(0.3) == 200
    assert table.find(0.5) == 200
    assert table.find(1.5) == 60
    assert table.find(5.0) == 60


def test_laser_catalog_loaded():
    from equipment import laser

    assert len(laser._items) > 0  # type: ignore[attr-defined]
    for spec in laser._items.values():  # type: ignore[attr-defined]
        assert isinstance(spec, LaserSpec)


def test_all_equipment_categories():
    assert set(ALL_EQUIPMENT.keys()) == {
        "laser",
        "printer",
        "plotter",
        "cutter",
        "laminator",
        "milling",
        "heatpress",
        "cards",
        "metalpins",
        "design",
        "tools",
    }


def test_each_category_loads():
    for category, catalog in ALL_EQUIPMENT.items():
        assert catalog is not None


def test_get_equipment_existing():
    # Берём первый лазер из каталога
    from equipment import laser

    code = next(iter(laser._items.keys()))  # type: ignore[attr-defined]
    spec = get_equipment("laser", code)
    assert spec.name


def test_get_equipment_missing():
    with pytest.raises(KeyError):
        get_equipment("laser", "does-not-exist")


def test_laser_has_cut_speed():
    from equipment import laser

    spec = next(iter(laser._items.values()))  # type: ignore[attr-defined]
    assert isinstance(spec, LaserSpec)
    # Для толщины 1 мм скорость должна быть > 0
    assert spec.get_cut_speed(1.0) > 0.0


def test_laser_consumables():
    from equipment import laser

    spec = next(iter(laser._items.values()))  # type: ignore[attr-defined]
    assert spec.consumables_per_hour > 0.0


def test_laser_depreciation():
    from equipment import laser

    spec = next(iter(laser._items.values()))  # type: ignore[attr-defined]
    assert spec.depreciation_per_hour > 0.0


def test_get_time_ready_default():
    # У большинства инструментов baseTimeReady не задан,
    # например Warrior в tools.json.
    catalog = load_generic_catalog("tools.json")
    spec = catalog.get("Warrior")
    assert spec.base_time_ready is None
    assert spec.get_time_ready(2) == BASE_TIME_READY[1]


def test_defect_rate():
    from equipment import laser

    # У лазера есть таблица дефектов
    spec = next(iter(laser._items.values()))  # type: ignore[attr-defined]
    rate = spec.get_defect_rate(10)
    assert 0.0 <= rate <= 1.0


def test_get_all_equipment_options():
    options = get_all_equipment_options()
    assert isinstance(options, dict)
    assert len(options) == 11
    # У каждой категории должен быть хотя бы пустой dict
    for cat, mapping in options.items():
        assert isinstance(mapping, dict)

