"""
Реестр калькуляторов сервиса.

Используется API и ботом для вызова по slug.

Калькуляторы: laser, cut_plotter, cut_guillotine, cut_roller, milling,
lamination, print_sheet, print_laser.
"""

from __future__ import annotations

from typing import Dict

from .base import BaseCalculator
from .cut_guillotine import CutGuillotineCalculator
from .cut_plotter import CutPlotterCalculator
from .cut_roller import CutRollerCalculator
from .lamination import LaminationCalculator
from .laser import LaserCalculator
from .milling import MillingCalculator
from .print_laser import PrintLaserCalculator
from .print_sheet import PrintSheetCalculator

CALCULATORS: Dict[str, BaseCalculator] = {
    "laser": LaserCalculator(),
    "cut_plotter": CutPlotterCalculator(),
    "cut_guillotine": CutGuillotineCalculator(),
    "cut_roller": CutRollerCalculator(),
    "milling": MillingCalculator(),
    "lamination": LaminationCalculator(),
    "print_sheet": PrintSheetCalculator(),
    "print_laser": PrintLaserCalculator(),
}


def get_calculator(slug: str) -> BaseCalculator:
    """Получить калькулятор по slug."""
    if slug not in CALCULATORS:
        raise KeyError(f"Неизвестный калькулятор: {slug!r}")
    return CALCULATORS[slug]
