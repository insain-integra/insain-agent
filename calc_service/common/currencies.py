"""
Курсы валют из data/common.json (USD, EUR).
Загрузка через json5. reload() — перечитать из файла.
"""
import json5
from pathlib import Path
from typing import Union

_DATA_PATH = Path(__file__).resolve().parent.parent / "data" / "common.json"


def _load_rates() -> dict:
    with open(_DATA_PATH, "r", encoding="utf-8") as f:
        return json5.load(f)


def _read_rates() -> tuple[float, float]:
    data = _load_rates()
    usd = float(data.get("USD", 95))
    eur = float(data.get("EUR", 100))
    return usd, eur


_usd, _eur = _read_rates()
USD_RATE: float = _usd
EUR_RATE: float = _eur


def parse_currency(value: Union[str, int, float]) -> float:
    """
    Конвертация в рубли или возврат числа как float.
    "$11600" → 11600 * USD_RATE
    "€500" → 500 * EUR_RATE
    750 → 750.0, "750" → 750.0
    """
    if isinstance(value, (int, float)):
        return float(value)
    s = value.strip()
    if s.startswith("$"):
        return float(s[1:].replace(" ", "")) * USD_RATE
    if s.startswith("€"):
        return float(s[1:].replace(" ", "")) * EUR_RATE
    return float(s.replace(" ", "").replace(",", "."))


def usd_to_rub(usd: float) -> float:
    """Доллары → рубли по текущему курсу."""
    return usd * USD_RATE


def eur_to_rub(eur: float) -> float:
    """Евро → рубли по текущему курсу."""
    return eur * EUR_RATE


def reload() -> None:
    """Перечитать курсы USD и EUR из data/common.json."""
    global USD_RATE, EUR_RATE
    USD_RATE, EUR_RATE = _read_rates()
