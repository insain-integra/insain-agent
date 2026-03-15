"""
Ядро бота Insain: одноступенчатый агент с function calling.

LLM видит все калькуляторы (tools) + search_materials, сама выбирает нужный.
Результат расчёта форматируется в Python (_format_calc_result).
"""

from __future__ import annotations

import json
import logging
import os
from pathlib import Path
from typing import Any, Dict, List, Optional

import httpx


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

SYSTEM_PROMPT = (
    "Ты — ассистент компании Инсайн. Рассчитываешь стоимость через калькуляторы (tools).\n"
    "Для подбора material_id/lamination_id вызови search_materials(slug, query), из результата подставь id.\n"
    "Коды менеджеру не показывай. mode: 0=эконом, 1=стандарт, 2=экспресс (по умолчанию 1).\n"
    "При пересчёте (смена параметра) вызывай калькулятор заново. Результат покажу я — не придумывай цены и ссылки.\n"
    "Ответы: plain text, без Markdown. Отвечай на русском."
)

SEARCH_MATERIALS_TOOL: Dict[str, Any] = {
    "type": "function",
    "function": {
        "name": "search_materials",
        "description": (
            "Поиск материалов для калькулятора по запросу (название, плотность, толщина). "
            "Вернёт список {id, title}. Подставь id в material_id или lamination_id калькулятора."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "slug": {"type": "string", "description": "slug калькулятора (print_sheet, laser, milling, lamination, cut_plotter и т.д.)"},
                "query": {"type": "string", "description": "меловка 115, акрил 3мм, плёнка 32мкм. Пустая строка — все материалы."},
                "param": {"type": "string", "description": "material (по умолчанию) или lamination", "enum": ["material", "lamination"]},
            },
            "required": ["slug", "query"],
        },
    },
}


class InsainAgent:
    """
    Одноступенчатый агент: LLM видит все tools (search_materials + калькуляторы),
    сама выбирает нужный, сама задаёт уточняющие вопросы.
    """

    def __init__(self, calc_api_url: Optional[str] = None):
        self.calc_api_url = (calc_api_url or CALC_API_URL).rstrip("/")
        self.llm = LLMProvider()
        self._calculators: List[Dict[str, Any]] = []
        self._tools: List[Dict[str, Any]] = []
        self._param_schemas: Dict[str, Dict[str, Any]] = {}
        self._options_by_slug: Dict[str, Dict[str, Any]] = {}
        self.calculator_materials: Dict[str, List[Dict[str, Any]]] = {}
        self._load_calculators_and_tools()

    def _load_calculators_and_tools(self) -> None:
        """
        Загрузить калькуляторы и их схемы.

        - /api/v1/calculators        → список калькуляторов
        - /api/v1/param_schema/{slug} → детальная схема параметров
        - /api/v1/tool_schema/{slug}  → компактная схема для LLM (function calling)
        - /api/v1/options/{slug}      → опции (материалы и т.д.)

        На основе tool_schema строим tools с enum для material_id.
        """
        try:
            with httpx.Client(timeout=HTTP_TIMEOUT) as client:
                r = client.get(f"{self.calc_api_url}/api/v1/calculators")
                r.raise_for_status()
                self._calculators = r.json()
        except (httpx.ConnectError, httpx.TimeoutException) as e:
            logger.warning("Calc API недоступен при инициализации: %s", e)
            self._calculators = []
            self._tools = []
            self._param_schemas = {}
            self.calculator_materials = {}
            return
        except Exception as e:
            logger.exception("Ошибка загрузки калькуляторов: %s", e)
            self._calculators = []
            self._tools = []
            self._param_schemas = {}
            self.calculator_materials = {}
            return

        tools = []
        # Переиспользуем один HTTP-клиент для всех запросов
        with httpx.Client(timeout=HTTP_TIMEOUT) as client:
            for calc in self._calculators:
                slug = calc.get("slug")
                if not slug:
                    continue
                try:
                    # Детальная схема параметров
                    ps_r = client.get(f"{self.calc_api_url}/api/v1/param_schema/{slug}")
                    if ps_r.status_code == 200:
                        self._param_schemas[slug] = ps_r.json()

                    # Опции (материалы и т.д.)
                    opts_r = client.get(f"{self.calc_api_url}/api/v1/options/{slug}")
                    if opts_r.status_code == 200:
                        opts = opts_r.json()
                        self._options_by_slug[slug] = opts
                        materials = opts.get("materials") or []
                        self.calculator_materials[slug] = list(materials)
                    else:
                        self.calculator_materials[slug] = []

                    # Компактная схема инструмента для LLM
                    schema_r = client.get(f"{self.calc_api_url}/api/v1/tool_schema/{slug}")
                    schema_r.raise_for_status()
                    schema = schema_r.json()
                except Exception as e:
                    logger.warning("Не удалось загрузить схемы/опции для %s: %s", slug, e)
                    self.calculator_materials[slug] = []
                    continue

                # OpenAI function calling format
                name = schema.get("name") or f"calc_{slug}"
                params = dict(schema.get("parameters") or {"type": "object", "properties": {}})
                props = params.get("properties") or {}

                # material_id/lamination_id: без списка в description — LLM получает коды через search_materials.
                for param_key, param_hint in (("material_id", "material"), ("lamination_id", "lamination")):
                    if param_key not in props:
                        continue
                    orig = props.get(param_key) or {}
                    props[param_key] = {
                        **orig,
                        "type": "string",
                        "description": orig.get("description") or (
                            f"Код из результата search_materials(slug, query, param='{param_hint}'). Подставь поле id."
                        ),
                    }

                # color для листовой/лазерной печати: явный enum, чтобы LLM всегда передавал цветность.
                if slug in ("print_sheet", "print_laser") and "color" in props:
                    props["color"] = {
                        **(props.get("color") or {}),
                        "type": "string",
                        "enum": ["1+0", "4+0", "1+1", "4+1", "4+4"],
                        "description": "Цветность печати. 4+0 — односторонняя цветная, 4+4 — двусторонняя цветная. Обязательно передавай при вызове (по умолчанию 4+0).",
                    }

                tools.append({
                    "type": "function",
                    "function": {
                        "name": name,
                        "description": schema.get("description") or calc.get("description", ""),
                        "parameters": {**params, "properties": props},
                    },
                })

        self._tools = [SEARCH_MATERIALS_TOOL] + tools
        logger.info(
            "Загружено калькуляторов: %s, tools: %s, materials по калькуляторам: %s",
            len(self._calculators),
            len(self._tools),
            {s: len(m) for s, m in self.calculator_materials.items()},
        )

    def get_system_prompt(self) -> str:
        return SYSTEM_PROMPT

    def get_tools(self) -> List[Dict[str, Any]]:
        return list(self._tools)

    def _find_calculator_meta(self, slug: str) -> Dict[str, Any]:
        """Найти описание калькулятора по slug в загруженном списке."""
        for c in self._calculators:
            if c.get("slug") == slug:
                return c
        return {}

    @staticmethod
    def _mode_label(mode: Any) -> str:
        """Срочность: 0 → эконом, 1 → стандарт, 2 → экспресс."""
        try:
            v = int(mode)
            if v == 0:
                return "эконом"
            if v == 2:
                return "экспресс"
            return "стандарт"
        except (TypeError, ValueError):
            return "стандарт"

    def _format_calc_result(
        self,
        tool_name: str,
        args: Dict[str, Any],
        result: Dict[str, Any],
    ) -> str:
        """
        Форматирование результата расчёта: расширенные параметры, без slug в заголовке.
        Параметры выводим все значимые; опциональные (например ламинация) — только если заданы.
        """
        slug = tool_name
        if slug.startswith("calc_"):
            slug = slug[5:]

        if "error" in result:
            err = str(result.get("error") or "Неизвестная ошибка.")
            return f"Не удалось выполнить расчёт: {err}"

        meta = self._find_calculator_meta(slug)
        calc_title = meta.get("name") or slug

        quantity = args.get("quantity") or args.get("num_sheet") or args.get("n") or args.get("count")
        try:
            quantity = int(quantity) if quantity is not None else None
        except Exception:
            quantity = None

        w = args.get("width_mm") or args.get("width")
        h = args.get("height_mm") or args.get("height")
        try:
            w = float(w) if w is not None else None
            h = float(h) if h is not None else None
        except Exception:
            w = h = None

        materials = result.get("materials") or []
        material_title = "материал не указан"
        if materials:
            material_title = materials[0].get("title") or materials[0].get("name") or material_title

        cost = float(result.get("cost") or 0)
        price = float(result.get("price") or 0)
        unit_price = float(result.get("unit_price") or 0)
        time_hours = float(result.get("time_hours") or 0)
        time_ready = float(result.get("time_ready") or 0)
        weight_kg = float(result.get("weight_kg") or 0)
        share_url = result.get("share_url") or ""

        # Блок параметров расчёта (расширенный)
        params_lines: List[str] = []
        if quantity is not None:
            params_lines.append(f"Тираж\t{quantity}")
        if w is not None and h is not None:
            params_lines.append(f"Ширина, мм\t{int(w)}")
            params_lines.append(f"Высота, мм\t{int(h)}")

        # Цветность — для листовой и лазерной печати всегда выводим
        color = (args.get("color") or "").strip() or "4+0"
        if slug in ("print_sheet", "print_laser"):
            params_lines.append(f"Цветность печати\t{color}")

        params_lines.append(f"Материал\t{material_title}")

        # Ламинация — только если задана (второй материал в результате или lamination_id в args)
        if slug == "print_sheet":
            lamination_id = (args.get("lamination_id") or "").strip()
            if lamination_id and len(materials) > 1:
                lam_title = materials[1].get("title") or materials[1].get("name") or "ламинация"
                params_lines.append(f"Ламинация\t{lam_title}")
            elif lamination_id:
                params_lines.append("Ламинация\tда")

        mode = args.get("mode", 1)
        params_lines.append(f"Срочность\t{self._mode_label(mode)}")

        lines: List[str] = []
        lines.append(calc_title)
        lines.append("")
        lines.append("\n".join(params_lines))

        suspicious = (price == 0) or (cost == 0) or (time_hours == 0)
        lines.append("")
        lines.append(f"💰 Цена: {price:.2f} ₽ ({unit_price:.2f} ₽/шт)" if price else "💰 Цена: 0 ₽")
        lines.append(f"💵 Себестоимость: {cost:.2f} ₽")
        lines.append(f"⏱ Время изготовления: {time_hours:.2f} ч")
        lines.append(f"📅 Готовность: {time_ready:.2f} раб. часов")
        lines.append(f"⚖️ Вес тиража: {weight_kg:.2f} кг")

        if materials:
            lines.append("\n📦 Расход материалов:")
            for m in materials:
                title = m.get("title") or m.get("name") or m.get("code") or "Материал"
                qty = m.get("quantity") or m.get("quantity_approx")
                unit = (m.get("unit") or "").strip()
                if unit and unit.lower() == "sheet":
                    unit = ""
                if qty is None:
                    lines.append(f"— {title}")
                else:
                    lines.append(f"— {title}: {qty}" + (f" {unit}" if unit else ""))

        if share_url:
            lines.append("\n🔗 Ссылка для клиента:")
            lines.append(share_url)

        if suspicious:
            lines.append(
                "\n⚠️ ВНИМАНИЕ: калькулятор вернул нулевые значения. Проверьте параметры или уточните расчёт."
            )

        return "\n".join(lines).strip()

    def _execute_search_materials(self, slug: str, query: str, param: str = "material") -> Dict[str, Any]:
        """Вызов POST /api/v1/choices для поиска материалов. param = имя в param_schema: material или lamination."""
        try:
            with httpx.Client(timeout=HTTP_TIMEOUT) as client:
                r = client.post(
                    f"{self.calc_api_url}/api/v1/choices",
                    json={"slug": slug, "param": param, "query": (query or "").strip(), "limit": 15},
                )
                r.raise_for_status()
                data = r.json()
                items = data.get("items") or []
                return {"items": items, "hint": "Подставь выбранный id в material_id (или lamination_id) при вызове калькулятора."}
        except httpx.HTTPStatusError as e:
            detail = (e.response.json() or {}).get("detail", str(e)) if e.response else str(e)
            return {"error": detail, "items": []}
        except (httpx.ConnectError, httpx.TimeoutException) as e:
            logger.warning("Choices API недоступен: %s", e)
            return {"error": "Сервис поиска материалов временно недоступен", "items": []}
        except Exception as e:
            logger.exception("search_materials: %s", e)
            return {"error": str(e), "items": []}

    def execute_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """
        Выполнить инструмент: search_materials → POST /api/v1/choices;
        calc_* → POST /api/v1/calc/{slug}.
        """
        if tool_name == "search_materials":
            slug = (arguments.get("slug") or "").strip()
            query = (arguments.get("query") or "").strip()
            param = (arguments.get("param") or "material").strip() or "material"
            if not slug:
                return {"error": "Укажи slug калькулятора", "items": []}
            logger.info("execute_tool: search_materials slug=%s query=%r param=%s", slug, query, param)
            return self._execute_search_materials(slug, query, param)

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
        Одноступенчатый диалог: LLM видит system prompt + историю + все tools.
        Сама решает, какой калькулятор вызвать (или задать вопрос).
        Цикл tool-calls до calc_* (максимум 5 раундов).
        """
        history = history or []
        if len(history) > MAX_HISTORY_MESSAGES:
            history = history[-MAX_HISTORY_MESSAGES:]

        tools = self.get_tools()
        if not tools:
            return "Сервис расчётов временно недоступен, попробуйте позже."

        messages: List[Dict[str, Any]] = [
            {"role": "system", "content": SYSTEM_PROMPT},
            *history,
            {"role": "user", "content": user_message},
        ]

        try:
            result = self.llm.chat(messages, tools=tools)
        except Exception as e:
            logger.exception("LLM error: %s", e)
            return "Произошла ошибка, попробуйте переформулировать запрос."

        content = result.get("content")
        tool_calls = result.get("tool_calls")

        if not tool_calls:
            return (content or "").strip() or "Нет ответа."

        max_rounds = 5
        while tool_calls and max_rounds > 0:
            max_rounds -= 1

            assistant_msg: Dict[str, Any] = {
                "role": "assistant",
                "content": content or None,
                "tool_calls": [
                    {"id": tc.get("id", f"tc_{i}"), "type": "function", "function": tc["function"]}
                    for i, tc in enumerate(tool_calls)
                ],
            }
            messages.append(assistant_msg)

            calc_tool_name = None
            calc_args: Dict[str, Any] = {}
            calc_result = None

            for tc in tool_calls:
                name = tc["function"]["name"]
                try:
                    args_str = tc["function"].get("arguments") or "{}"
                    args = json.loads(args_str) if isinstance(args_str, str) else args_str
                except json.JSONDecodeError:
                    args = {}

                tool_result = self.execute_tool(name, args)
                tc_id = tc.get("id", f"tc_{tool_calls.index(tc)}")
                messages.append({
                    "role": "tool",
                    "tool_call_id": tc_id,
                    "content": json.dumps(tool_result, ensure_ascii=False),
                })

                if name.startswith("calc_"):
                    calc_tool_name = name
                    calc_args = args
                    calc_result = tool_result

            if calc_tool_name and calc_result is not None:
                return self._format_calc_result(calc_tool_name, calc_args, calc_result)

            try:
                result = self.llm.chat(messages, tools=tools)
            except Exception as e:
                logger.exception("LLM follow-up error: %s", e)
                return "Произошла ошибка при обработке ответа."
            content = result.get("content")
            tool_calls = result.get("tool_calls") or []

        return (content or "").strip() or "Не удалось выполнить расчёт. Попробуйте уточнить параметры."


if __name__ == "__main__":
    agent = InsainAgent()
    print("SYSTEM PROMPT:")
    print(agent.get_system_prompt())
    print(f"\nTools count: {len(agent.get_tools())}")
    for t in agent.get_tools():
        print(f"  - {t['function']['name']}")
