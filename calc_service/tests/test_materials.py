from __future__ import annotations

from pathlib import Path

import pytest

from materials.base import MaterialCatalog, MaterialSpec
from materials.loader import load_catalog


DATA_DIR = Path(__file__).resolve().parent.parent / "data" / "materials"


def test_load_hardsheet():
    catalog = load_catalog("hardsheet.json")
    all_items = catalog.list_all()
    assert len(all_items) > 0


def test_load_all_material_files():
    json_files = sorted(DATA_DIR.glob("*.json"))
    # В документации указано 11 файлов материалов
    assert len(json_files) == 11

    total = 0
    for path in json_files:
        catalog = load_catalog(path.name)
        total += len(catalog.list_all())

    assert total > 0


def test_material_has_required_fields():
    catalog = load_catalog("hardsheet.json")
    for spec in catalog.list_all().values():
        assert spec.name
        assert spec.sizes
        assert spec.cost is not None or spec.cost_tiers is not None


def test_get_cost_fixed():
    spec = MaterialSpec(
        code="T1",
        group="G",
        name="Fixed cost material",
        category="test",
        cost=750.0,
        sizes=[[100.0, 100.0]],
    )
    assert spec.get_cost(1) == pytest.approx(750.0)
    assert spec.get_cost(10) == pytest.approx(750.0)


def test_get_cost_tiered():
    spec = MaterialSpec(
        code="T2",
        group="G",
        name="Tiered cost material",
        category="test",
        cost=None,
        cost_tiers=[(10, 800.0), (50, 700.0)],
        sizes=[[100.0, 100.0]],
    )
    assert spec.get_cost(5) == pytest.approx(800.0)
    assert spec.get_cost(30) == pytest.approx(700.0)
    assert spec.get_cost(999) == pytest.approx(700.0)


def test_catalog_get_missing():
    catalog = MaterialCatalog(category="test")
    with pytest.raises(KeyError):
        catalog.get("does-not-exist")

