from __future__ import annotations

from abc import ABC, abstractmethod
from enum import IntEnum
from typing import Any, Dict, Mapping, TypedDict, Literal, List

from urllib.parse import urlencode

from config import SITE_URL


class ParamDef(TypedDict, total=False):
    """
    Описание одного входного параметра калькулятора для агента/фронта.

    Поля:
        name: системное имя параметра (ключ в params).
        type: базовый тип параметра (integer, number, string, boolean, enum, enum_cascading).
        required: обязательный ли параметр для корректного вызова калькулятора.
        default: дефолтное значение, если пользователь его не указал.
        title: краткое название для UI.
        description: подробное описание / подсказка.
        validation: ограничения на значение (например, {"min": 1, "max": 100}).
        unit: единица измерения (мм, м², шт и т.п.) или None.
        choices: источник вариантов для enum-параметров:
            {"source": "materials:hardsheet"} или {"inline": [...]}.
    """

    name: str
    type: Literal["integer", "number", "string", "boolean", "enum", "enum_cascading"]
    required: bool
    default: Any
    title: str
    description: str
    validation: Dict[str, Any] | None
    unit: str | None
    choices: Dict[str, Any] | None


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
    # По умолчанию калькулятор публичный (виден в /api/v1/calculators и агенту).
    # Базовые/служебные калькуляторы можно пометить is_public = False,
    # чтобы они не светились менеджеру, но оставались доступны по slug для внутренних вызовов.
    is_public: bool = True

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

    def get_param_schema(self) -> Dict[str, Any]:
        """
        Детальная схема параметров калькулятора для агента / фронтенда.

        Ожидаемый формат:
            {
                "slug": "laser",
                "title": "Лазерная резка",
                "params": [ParamDef, ...],
                "param_groups": {
                    "main": ["quantity", "width_mm"],
                    "material": ["material_type"],
                    "mode": ["mode"]
                }
            }

        Базовая реализация возвращает пустую схему и должна быть
        переопределена в конкретных калькуляторах по мере необходимости.
        """
        return {
            "slug": self.slug,
            "title": self.name or self.__class__.__name__,
            "params": [],
            "param_groups": {},
        }

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

    def get_required_params(self) -> List[str]:
        """
        Вернуть список обязательных параметров калькулятора.

        Базируется на поле required в схемe, возвращаемой get_param_schema().
        """
        schema = self.get_param_schema()
        params: List[ParamDef] = schema.get("params", [])  # type: ignore[assignment]
        return [p["name"] for p in params if p.get("required")]

    def get_default_values(self) -> Dict[str, Any]:
        """
        Вернуть словарь name → default для параметров с заданным значением по умолчанию.

        Полезно для инициализации форм и автодополнения параметров агента.
        """
        schema = self.get_param_schema()
        params: List[ParamDef] = schema.get("params", [])  # type: ignore[assignment]
        defaults: Dict[str, Any] = {}
        for p in params:
            if "default" in p and p["default"] is not None:
                defaults[p["name"]] = p["default"]
        return defaults

