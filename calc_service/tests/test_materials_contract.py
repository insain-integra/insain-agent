"""Контракт элемента materials: проверка в BaseCalculator.execute()."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any, Dict, Mapping

import pytest

_calc_service = Path(__file__).resolve().parent.parent
if _calc_service.name == "calc_service" and str(_calc_service) not in sys.path:
    sys.path.insert(0, str(_calc_service))

from calculators import get_calculator
from calculators.base import BaseCalculator
from calculators.metal_pins import MetalPinsCalculator
from calculators.puzzle import PuzzleCalculator


GOOD_MATERIAL = {
    "code": "PVC3",
    "name": "ПВХ Unext Strong 3 мм",
    "title": "ПВХ белый 3мм",
    "quantity": 0.25,
    "unit": "лист",
}


class _StubCalculator(BaseCalculator):
    slug = "stub"
    name = "Заглушка"

    def __init__(self, material: Dict[str, Any]):
        self._material = material

    def calculate(self, params: Mapping[str, Any]) -> Dict[str, Any]:
        return {
            "cost": 1.0, "price": 2.0, "unit_price": 2.0,
            "time_hours": 0.0, "time_ready": 1.0, "weight_kg": 0.0,
            "materials": [dict(self._material)],
        }

    def get_options(self) -> Dict[str, Any]:
        return {}

    def get_tool_schema(self) -> Dict[str, Any]:
        return {}


def _execute(**overrides: Any) -> Dict[str, Any]:
    return _StubCalculator(dict(GOOD_MATERIAL, **overrides)).execute({"quantity": 1})


def test_materials_contract_valid_passes():
    result = _execute()
    assert result["materials"][0]["name"] == GOOD_MATERIAL["name"]
    assert "share_url" in result


def test_materials_contract_integer_quantity_passes():
    assert _execute(quantity=3)["materials"][0]["quantity"] == 3


@pytest.mark.parametrize("value", ["", "   ", None])
def test_materials_contract_empty_name(value):
    with pytest.raises(ValueError, match="name"):
        _execute(name=value)


def test_materials_contract_name_equals_code():
    with pytest.raises(ValueError, match="совпадает с code"):
        _execute(name="PVC3")


@pytest.mark.parametrize("value", ["", "  ", None])
def test_materials_contract_empty_title(value):
    with pytest.raises(ValueError, match="title"):
        _execute(title=value)


def test_materials_contract_title_equals_code():
    with pytest.raises(ValueError, match="совпадает с code"):
        _execute(title="PVC3")


@pytest.mark.parametrize("value", ["10", None, True])
def test_materials_contract_quantity_not_number(value):
    with pytest.raises(ValueError, match="quantity"):
        _execute(quantity=value)


def test_materials_contract_unit_not_string():
    with pytest.raises(ValueError, match="unit"):
        _execute(unit=None)


def test_materials_contract_metal_pins_execute_checks(monkeypatch):
    """metal_pins переопределяет execute(): проверка контракта не должна теряться."""
    calc = MetalPinsCalculator()
    bad = dict(GOOD_MATERIAL, name="")
    monkeypatch.setattr(calc, "calculate", lambda params: {"materials": [bad]})
    with pytest.raises(ValueError, match="name"):
        calc.execute({"quantity": 1})


def _assert_russian_units(materials):
    assert materials
    for m in materials:
        assert m["name"].strip() and m["name"] != m["code"]
        assert not any(ch.isascii() and ch.isalpha() for ch in m["unit"]), (m["code"], m["unit"])


def test_materials_contract_puzzle_ref():
    """Эталон формы 79: name — полное имя, отличное от code, единицы по-русски."""
    result = PuzzleCalculator().execute({"quantity": 1, "puzzle_id": "Puzzle300420", "mode": 1})
    _assert_russian_units(result["materials"])


# Калькуляторы, которые раньше отдавали unit sheet / mm / m.
UNIT_CASES = [
    ("laser", {"quantity": 50, "width": 40, "height": 80, "material_id": "AcrylColor3", "mode": 1,
               "is_cut_laser": {}, "is_grave": 1, "is_grave_fill": [30, 40]}, "лист"),
    ("cut_plotter", {"quantity": 100, "width": 60, "height": 60, "material_id": "Avery500c",
                     "plotter_code": "", "difficulty": 1.3, "mode": 1}, "м"),
    ("lamination", {"quantity": 13, "width": 320, "height": 450, "material_id": "Laminat32G",
                    "laminator_code": "FGKFM360", "double_side": True, "mode": 1}, "м"),
    ("lamination", {"quantity": 100, "width": 148, "height": 105, "material_id": "LaminatA660G",
                    "laminator_code": "FGKFM360", "double_side": True, "mode": 1}, "лист"),
    ("milling", {"quantity": 10, "width": 500, "height": 1000, "material_id": "PVC3",
                 "material_mode": "isMaterial", "len_cut": 3.0, "mode": 1}, "лист"),
    ("print_sheet", {"quantity": 100, "width": 210, "height": 297, "material_id": "PaperCoated300M",
                     "color": "4+4", "printer_code": "", "mode": 1}, "лист"),
    ("print_inkjet", {"num_sheet": 10, "width": 210, "height": 297, "quality": 0, "color": "4+0",
                      "material_id": "PaperCoated115M", "printer_code": "EPSONWF7610", "mode": 1}, "лист"),
    ("print_offset", {"num_sheet": 1000, "width": 210, "height": 297, "color": "4+0",
                      "material_id": "PaperCoated115M", "mode": 1}, "лист"),
    ("sticker", {"quantity": 100, "width": 50, "height": 50, "material_id": "VHI80",
                 "color": "4+0", "mode": 1}, "лист"),
]


@pytest.mark.parametrize("slug,params,first_unit", UNIT_CASES)
def test_materials_contract_units_russian(slug, params, first_unit):
    result = get_calculator(slug).execute(params)
    _assert_russian_units(result["materials"])
    assert result["materials"][0]["unit"] == first_unit
