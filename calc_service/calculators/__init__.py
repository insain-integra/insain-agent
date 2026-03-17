"""
Реестр калькуляторов сервиса.

Используется API и ботом для вызова по slug.
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
from .print_inkjet import PrintInkjetCalculator
from .print_laser import PrintLaserCalculator
from .print_offset import PrintOffsetCalculator
from .print_roll import PrintRollCalculator
from .print_sheet import PrintSheetCalculator
from .print_wide import PrintWideCalculator
from .sticker import StickerCalculator
from .poly_sticker import PolyStickerCalculator
from .uv_print import UVPrintCalculator
from .uv_badge import UVBadgeCalculator
from .cards import CardsCalculator
from .mug import MugCalculator
from .keychain import KeychainCalculator
from .flag import FlagCalculator
from .pennant import PennantCalculator
from .rollup import RollupCalculator
from .puzzle import PuzzleCalculator
from .design import DesignCalculator
from .presswall import PresswallCalculator
from .notebook import NotebookCalculator
from .metal_pins import MetalPinsCalculator
from .acrylic_prizes import AcrylicPrizesCalculator
from .embossing import EmbossingCalculator
from .pad_print import PadPrintCalculator
from .magnets import MagnetsCalculator
from .badge import BadgeCalculator
from .calendar_calc import CalendarCalculator
from .heat_press import HeatPressCalculator
from .canvas import CanvasCalculator
from .tablets import TabletsCalculator
from .shild import ShildCalculator

CALCULATORS: Dict[str, BaseCalculator] = {
    "laser": LaserCalculator(),
    "cut_plotter": CutPlotterCalculator(),
    "cut_guillotine": CutGuillotineCalculator(),
    "cut_roller": CutRollerCalculator(),
    "milling": MillingCalculator(),
    "lamination": LaminationCalculator(),
    "print_sheet": PrintSheetCalculator(),
    "print_laser": PrintLaserCalculator(),
    "print_wide": PrintWideCalculator(),
    "print_inkjet": PrintInkjetCalculator(),
    "print_roll": PrintRollCalculator(),
    "print_offset": PrintOffsetCalculator(),
    "sticker": StickerCalculator(),
    "poly_sticker": PolyStickerCalculator(),
    "uv_print": UVPrintCalculator(),
    "uv_badge": UVBadgeCalculator(),
    "cards": CardsCalculator(),
    "mug": MugCalculator(),
    "keychain": KeychainCalculator(),
    "flag": FlagCalculator(),
    "pennant": PennantCalculator(),
    "rollup": RollupCalculator(),
    "puzzle": PuzzleCalculator(),
    "design": DesignCalculator(),
    "presswall": PresswallCalculator(),
    "notebook": NotebookCalculator(),
    "metal_pins": MetalPinsCalculator(),
    "acrylic_prizes": AcrylicPrizesCalculator(),
    "embossing": EmbossingCalculator(),
    "pad_print": PadPrintCalculator(),
    "magnets": MagnetsCalculator(),
    "badge": BadgeCalculator(),
    "calendar": CalendarCalculator(),
    "heat_press": HeatPressCalculator(),
    "canvas": CanvasCalculator(),
    "tablets": TabletsCalculator(),
    "shild": ShildCalculator(),
}


def get_calculator(slug: str) -> BaseCalculator:
    """Получить калькулятор по slug."""
    if slug not in CALCULATORS:
        raise KeyError(f"Неизвестный калькулятор: {slug!r}")
    return CALCULATORS[slug]
