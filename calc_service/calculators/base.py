from __future__ import annotations

from abc import ABC, abstractmethod
from enum import IntEnum
from typing import Any, Dict, Mapping

from urllib.parse import urlencode

from config import SITE_URL


class ProductionMode(IntEnum):
    """
    Режим производства для калькуляторов.
    """

    ECONOMY = 0
    STANDARD = 1
    EXPRESS = 2


class BaseCalculator(ABC):
    """
    Базовый класс калькулятора.

    Наследники должны определить:
      - slug: машинное имя калькулятора (используется в URL)
      - name: человекочитаемое название
      - description: краткое описание
    """

    slug: str = ""
    name: str = ""
    description: str = ""

    @abstractmethod
    def calculate(self, params: Mapping[str, Any]) -> Dict[str, Any]:
        """
        Основная логика расчёта.

        Должна вернуть словарь с полями, описанными в CLAUDE.md:
          - cost, price, unit_price
          - time_hours, time_ready
          - weight_kg
          - materials
        Поле share_url будет добавлено автоматически в execute().
        """

    @abstractmethod
    def get_options(self) -> Dict[str, Any]:
        """
        Опции для фронтенда / Telegram-бота:
        списки материалов, оборудования, предустановки и т.д.
        """

    @abstractmethod
    def get_tool_schema(self) -> Dict[str, Any]:
        """
        Описание входных параметров для LLM (function calling / tools).
        """

    def make_share_url(self, params: Mapping[str, Any]) -> str:
        """
        Сформировать share URL для результата расчёта.

        Формат:
            {SITE_URL}/calculator/{slug}/?{urlencode(params)}
        Списки (напр. is_grave_fill=[30, 40]) приводятся к одному параметру "30,40".
        """
        base = SITE_URL.rstrip("/")
        slug = self.slug or self.__class__.__name__.lower()
        # Списки — в один параметр через запятую, чтобы не дублировать ключ в URL
        flat: Dict[str, str] = {}
        for k, v in params.items():
            if v is None or (isinstance(v, (dict, list)) and len(v) == 0):
                continue
            if isinstance(v, (list, tuple)):
                flat[k] = ",".join(str(x) for x in v)
            else:
                flat[k] = str(v)
        query = urlencode(flat)
        return f"{base}/calculator/{slug}/?{query}" if query else f"{base}/calculator/{slug}/"

    def execute(self, params: Mapping[str, Any]) -> Dict[str, Any]:
        """
        Выполнить расчёт и добавить share_url к результату.
        """
        result = dict(self.calculate(params))
        # Добавляем share_url только если его ещё нет
        if "share_url" not in result:
            result["share_url"] = self.make_share_url(params)
        return result

