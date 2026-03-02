"""
Ядро бота Insain: агент с function calling к калькуляторам через API.

Не импортирует calc_service — только HTTP API и LLMProvider.
При инициализации загружает список калькуляторов и для каждого — опции (материалы с кодами и названиями).
Системный промпт содержит список калькуляторов и материалов, чтобы агент подбирал material_id
по запросу менеджера ("акрил 3мм", "меловка" и т.д.) без показа кодов менеджеру.
"""

from __future__ import annotations

import json
import logging
import os
from pathlib import Path
from typing import Any, Dict, List, Optional

import httpx

# Загрузка .env из корня проекта (как в llm_provider)
def _load_env() -> None:
    _env_path = Path(__file__).resolve().parent.parent / ".env"
    if not _env_path.is_file():
        return
    try:
        from dotenv import load_dotenv
        load_dotenv(_env_path)
    except ImportError:
        with open(_env_path, encoding="utf-8", errors="ignore") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, _, v = line.partition("=")
                    k, v = k.strip(), v.strip().strip("'\"").strip()
                    if k and k not in os.environ:
                        os.environ[k] = v


_load_env()

from llm_provider import LLMProvider

logger = logging.getLogger(__name__)

CALC_API_URL = os.getenv("CALC_API_URL", "http://localhost:8001").strip().rstrip("/")

MAX_HISTORY_MESSAGES = 20
HTTP_TIMEOUT = 15.0

# Блоки системного промпта (без списка калькуляторов — он подставляется в _build_system_prompt)
_PROMPT_INTRODUCTION = """Ты — ИИ-ассистент рекламно-производственной компании Инсайн.
Помогаешь менеджерам рассчитывать стоимость продукции через калькуляторы.

У тебя есть доступ к калькуляторам (function calling). Менеджер не знает внутренние коды материалов —
он пишет "акрил 3мм", "баннер", "визитки на меловке". Ты обязан сам подобрать material_id из списка
и вызвать калькулятор с правильным кодом. Коды менеджеру НЕ показывай.
"""

_PROMPT_MATERIAL_RULES = """
ПРАВИЛА ВЫБОРА МАТЕРИАЛА:

— Ты ОБЯЗАН использовать material_id из списка материалов калькулятора.
— Нельзя придумывать коды, только из списка.
— Если менеджер написал "акрил 3мм" — найди в списке подходящий код и используй его при вызове калькулятора.
— Если подходит несколько вариантов — спроси менеджера, НЕ показывая коды.
  Например: "Есть несколько вариантов акрила 3мм:
  1. Акрил белый
  2. Акрил цветной
  3. Акрил прозрачный
  Какой нужен?"
  После того как менеджер выбрал — сам подставь нужный код в вызов калькулятора.
— Коды материалов (AcrylWhite3 и т.д.) — внутренняя информация. НИКОГДА не показывай коды менеджеру. Показывай только названия.
— Если материал не подходит для данного калькулятора — скажи об этом.
  Например: "Акрил нельзя использовать для листовой печати. Для листовой печати доступны: мелованная бумага, офсетная бумага..."
— Если менеджер не указал материал — спроси.
— Если менеджер не указал размер или тираж — спроси.
— Не вызывай калькулятор, пока не определены ВСЕ параметры: quantity, width, height, material_id, mode.
— mode по умолчанию = 1 (стандартный), если менеджер не указал иное.

СОВМЕСТИМОСТЬ МАТЕРИАЛОВ И КАЛЬКУЛЯТОРОВ:
— Каждый калькулятор работает только со СВОИМИ материалами из списка.
— Если материала нет в списке калькулятора — он не подходит.
— Не предлагай материалы из другого калькулятора.
"""

_PROMPT_FORMATTING = """
ФОРМАТИРОВАНИЕ:
— НЕ используй Markdown (звёздочки, решётки).
— Используй только plain text и эмодзи.
— Для списков используй тире — или эмодзи.
— Для выделения используй ЗАГЛАВНЫЕ БУКВЫ или эмодзи.
"""

_PROMPT_RESULT_FORMAT = """
Форматируй результат расчёта так:

📋 Название калькулятора

📦 Тираж: X шт
📐 Размер: Ш×В мм
🧱 Материал: полное название (БЕЗ кода)

💰 Цена: X ₽ (X ₽/шт)
💵 Себестоимость: X ₽
⏱ Время изготовления: X ч
📅 Готовность: X раб. часов
⚖️ Вес: X кг

📦 Расход материалов:
— название: X шт/м²

🔗 Ссылка для клиента:
share_url

Никогда не показывай внутренние коды (material_id, slug и т.д.) в ответе менеджеру.
"""


class InsainAgent:
    """
    Агент с function calling: список калькуляторов и tools загружаются из API.
    Для каждого калькулятора хранятся материалы (code, name, ...) для подсказки в промпте
    и для enum в tool schema (чтобы LLM не придумывал коды).
    """

    def __init__(self, calc_api_url: Optional[str] = None):
        self.calc_api_url = (calc_api_url or CALC_API_URL).rstrip("/")
        self.llm = LLMProvider()
        self._calculators: List[Dict[str, Any]] = []
        self._tools: List[Dict[str, Any]] = []
        self._options_by_slug: Dict[str, Dict[str, Any]] = {}
        # slug -> список материалов [{code, name, thickness?, ...}] для подстановки в промпт и enum
        self.calculator_materials: Dict[str, List[Dict[str, Any]]] = {}
        self._system_prompt: str = ""
        self._load_calculators_and_tools()
        self._system_prompt = self._build_system_prompt()

    def _load_calculators_and_tools(self) -> None:
        """Загрузить список калькуляторов, для каждого — options и tool_schema. Построить tools с enum для material_id."""
        try:
            with httpx.Client(timeout=HTTP_TIMEOUT) as client:
                r = client.get(f"{self.calc_api_url}/api/v1/calculators")
                r.raise_for_status()
                self._calculators = r.json()
        except (httpx.ConnectError, httpx.TimeoutException) as e:
            logger.warning("Calc API недоступен при инициализации: %s", e)
            self._calculators = []
            self._tools = []
            self.calculator_materials = {}
            return
        except Exception as e:
            logger.exception("Ошибка загрузки калькуляторов: %s", e)
            self._calculators = []
            self._tools = []
            self.calculator_materials = {}
            return

        tools = []
        for calc in self._calculators:
            slug = calc.get("slug")
            if not slug:
                continue
            try:
                with httpx.Client(timeout=HTTP_TIMEOUT) as client:
                    opts_r = client.get(f"{self.calc_api_url}/api/v1/options/{slug}")
                    if opts_r.status_code == 200:
                        opts = opts_r.json()
                        self._options_by_slug[slug] = opts
                        materials = opts.get("materials") or []
                        self.calculator_materials[slug] = list(materials)
                    else:
                        self.calculator_materials[slug] = []

                    schema_r = client.get(f"{self.calc_api_url}/api/v1/tool_schema/{slug}")
                    schema_r.raise_for_status()
                    schema = schema_r.json()
            except Exception as e:
                logger.warning("Не удалось загрузить options/schema для %s: %s", slug, e)
                self.calculator_materials[slug] = []
                continue

            # OpenAI function calling format
            name = schema.get("name") or f"calc_{slug}"
            params = dict(schema.get("parameters") or {"type": "object", "properties": {}})
            props = params.get("properties") or {}

            # Ограничить material_id списком допустимых кодов, чтобы LLM не придумывал коды
            if "material_id" in props and self.calculator_materials.get(slug):
                codes = [m.get("code") for m in self.calculator_materials[slug] if m.get("code")]
                if codes:
                    props["material_id"] = {
                        "type": "string",
                        "description": "Код материала из списка материалов этого калькулятора. Используй ТОЛЬКО один из допустимых кодов.",
                        "enum": codes,
                    }

            tools.append({
                "type": "function",
                "function": {
                    "name": name,
                    "description": schema.get("description") or calc.get("description", ""),
                    "parameters": {**params, "properties": props},
                },
            })

        self._tools = tools
        logger.info(
            "Загружено калькуляторов: %s, tools: %s, materials по калькуляторам: %s",
            len(self._calculators),
            len(self._tools),
            {s: len(m) for s, m in self.calculator_materials.items()},
        )

    def _build_system_prompt(self) -> str:
        """
        Формирует системный промпт с актуальным списком калькуляторов и материалов из API.
        Вызывается один раз после _load_calculators_and_tools.
        """
        parts = [_PROMPT_INTRODUCTION]

        parts.append("\nДоступные калькуляторы и их материалы:\n")
        for i, calc in enumerate(self._calculators, 1):
            slug = calc.get("slug", "")
            name = calc.get("name", slug)
            desc = calc.get("description", "")
            materials = self.calculator_materials.get(slug) or []
            parts.append(f"{i}. {slug} ({name})")
            if desc:
                parts.append(f"   {desc}")
            parts.append("   Материалы:")
            for m in materials[:80]:  # ограничить длину промпта
                code = m.get("code", "")
                display_name = m.get("name", code)
                thick = m.get("thickness")
                if code:
                    if thick is not None:
                        parts.append(f"   - {code}: {display_name} ({thick} мм)")
                    else:
                        parts.append(f"   - {code}: {display_name}")
            if len(materials) > 80:
                parts.append(f"   ... и ещё {len(materials) - 80} материалов")
            if not materials:
                parts.append("   (нет списка материалов)")
            parts.append("")

        parts.append(_PROMPT_MATERIAL_RULES)
        parts.append(_PROMPT_FORMATTING)
        parts.append(_PROMPT_RESULT_FORMAT)
        parts.append("\nЕсли тебя спрашивают не о расчёте — отвечай как обычный помощник компании. Отвечай на русском языке.\n")

        return "\n".join(parts).strip()

    def get_system_prompt(self) -> str:
        """Возвращает текущий системный промпт (для отладки или тестов)."""
        return self._system_prompt or self._build_system_prompt()

    def get_tools(self) -> List[Dict[str, Any]]:
        """Список tools для function calling (из кэша после загрузки в __init__)."""
        return list(self._tools)

    def execute_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """
        Выполнить инструмент: определить slug по tool_name и вызвать POST /api/v1/calc/{slug}.
        tool_name: "calc_laser" → slug "laser".
        """
        slug = tool_name
        if slug.startswith("calc_"):
            slug = slug[5:]
        if not slug:
            return {"error": "Неизвестный калькулятор"}

        logger.info("execute_tool: %s -> slug=%s, args=%s", tool_name, slug, list(arguments.keys()))

        try:
            with httpx.Client(timeout=HTTP_TIMEOUT) as client:
                r = client.post(f"{self.calc_api_url}/api/v1/calc/{slug}", json=arguments)
                r.raise_for_status()
                result = r.json()
                logger.info("tool result keys: %s", list(result.keys()))
                return result
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 400:
                detail = (e.response.json() or {}).get("detail", str(e))
                return {"error": detail}
            return {"error": "Ошибка расчёта"}
        except (httpx.ConnectError, httpx.TimeoutException) as e:
            logger.warning("Calc API недоступен: %s", e)
            return {"error": "Сервис расчётов временно недоступен, попробуйте позже"}
        except Exception as e:
            logger.exception("execute_tool: %s", e)
            return {"error": str(e)}

    def chat(self, user_message: str, history: Optional[List[Dict[str, Any]]] = None) -> str:
        """
        Диалог с циклом function calling.
        history: список {"role": "user"|"assistant", "content": "..."}.
        Возвращает финальный текстовый ответ.
        """
        history = history or []
        if len(history) > MAX_HISTORY_MESSAGES:
            history = history[-MAX_HISTORY_MESSAGES:]

        messages: List[Dict[str, Any]] = [
            {"role": "system", "content": self._system_prompt},
            *history,
            {"role": "user", "content": user_message},
        ]

        tools = self.get_tools()
        if not tools:
            return "Сервис расчётов временно недоступен, попробуйте позже."

        max_rounds = 10
        for _ in range(max_rounds):
            try:
                result = self.llm.chat(messages, tools=tools)
            except Exception as e:
                logger.exception("LLM error: %s", e)
                return "Произошла ошибка, попробуйте переформулировать запрос."

            content = result.get("content")
            tool_calls = result.get("tool_calls")

            if content and not tool_calls:
                return (content or "").strip()

            if not tool_calls:
                return (content or "").strip() or "Нет ответа."

            assistant_msg: Dict[str, Any] = {
                "role": "assistant",
                "content": content or "",
            }
            assistant_msg["tool_calls"] = [
                {
                    "id": tc.get("id", ""),
                    "type": tc.get("type", "function"),
                    "function": {
                        "name": tc["function"]["name"],
                        "arguments": tc["function"].get("arguments", "{}"),
                    },
                }
                for tc in tool_calls
            ]
            messages.append(assistant_msg)

            for tc in tool_calls:
                name = tc["function"]["name"]
                try:
                    args_str = tc["function"].get("arguments") or "{}"
                    args = json.loads(args_str) if isinstance(args_str, str) else args_str
                except json.JSONDecodeError:
                    args = {}
                tool_result = self.execute_tool(name, args)
                tool_id = tc.get("id", "")
                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_id,
                    "content": json.dumps(tool_result, ensure_ascii=False),
                })

        return "Слишком много шагов расчёта. Попробуйте упростить запрос."
