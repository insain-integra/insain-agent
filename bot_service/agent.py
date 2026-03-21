"""
Ядро бота Insain: агент с function calling.

Два этапа (если включён AGENT_USE_ROUTER):
1) Роутер — intent: knowledge | calculator и calculator_slug; без полного списка calc_* в контексте.
2) Основной вызов — knowledge: только search_knowledge; calculator: search_materials + один calc_* по slug.

Результат расчёта форматируется в Python (_format_calc_result).
"""

from __future__ import annotations

import json
import logging
import math
import os
import re
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional
from urllib.parse import parse_qs, urlparse

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
from knowledge_base import KnowledgeBase
from prompts import (
    build_calculator_index,
    build_recalc_context,
    build_router_system_prompt,
    build_kb_system_prompt,
    build_calc_system_prompt,
    build_calc_system_prompt_full,
)

logger = logging.getLogger(__name__)

CALC_API_URL = os.getenv("CALC_API_URL", "http://localhost:8001").strip().rstrip("/")

AGENT_USE_ROUTER = os.getenv("AGENT_USE_ROUTER", "true").strip().lower() in ("1", "true", "yes", "on")

MAX_HISTORY_MESSAGES = 20
HTTP_TIMEOUT = 15.0
CHOICES_SEARCH_LIMIT = max(10, min(2000, int(os.getenv("CHOICES_SEARCH_LIMIT", "500"))))

SEARCH_KNOWLEDGE_TOOL: Dict[str, Any] = {
    "type": "function",
    "function": {
        "name": "search_knowledge",
        "description": (
            "Поиск в базе знаний компании Инсайн (Wiki). "
            "Используй, когда нужен не расчёт цены, а информация: компания, процессы, сроки, технологии, инструкции."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Поисковый запрос на русском: тема, ключевые слова."},
            },
            "required": ["query"],
        },
    },
}

SEARCH_MATERIALS_TOOL: Dict[str, Any] = {
    "type": "function",
    "function": {
        "name": "search_materials",
        "description": (
            "Поиск позиций каталога для параметра калькулятора. "
            "Возвращает items: {id, title, description}. "
            "Подставь id в вызов calc_*, пользователю показывай только title."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "slug": {"type": "string", "description": "slug калькулятора"},
                "query": {
                    "type": "string",
                    "description": "Строка поиска: меловка 115, плёнка 32 мкм. Пустая строка — полный список.",
                },
                "param": {
                    "type": "string",
                    "description": "Имя параметра: material или lamination",
                    "enum": ["material", "lamination"],
                },
            },
            "required": ["slug", "query"],
        },
    },
}


class InsainAgent:
    """
    Двухэтапный агент: при AGENT_USE_ROUTER — route_request, затем узкий набор tools.
    """

    def __init__(self, calc_api_url: Optional[str] = None):
        self.calc_api_url = (calc_api_url or CALC_API_URL).rstrip("/")
        self.llm = LLMProvider()
        self.kb = KnowledgeBase()
        self._calculators: List[Dict[str, Any]] = []
        self._tools: List[Dict[str, Any]] = []
        self._param_schemas: Dict[str, Dict[str, Any]] = {}
        self._options_by_slug: Dict[str, Dict[str, Any]] = {}
        self.calculator_materials: Dict[str, List[Dict[str, Any]]] = {}
        self._calc_tool_by_slug: Dict[str, Dict[str, Any]] = {}
        self._calc_llm_prompts: Dict[str, str] = {}
        self._calculator_index: str = ""
        self._router_tool: Dict[str, Any] = {}
        # Последний успешный расчёт per user (для пересчёта и восстановления slug)
        self._user_calc_context: Dict[int, Dict[str, Any]] = {}
        self._load_calculators_and_tools()

    @staticmethod
    def _enrich_tool_props_from_param_schema_inline_choices(
        props: Dict[str, Any], param_schema: Dict[str, Any]
    ) -> None:
        """
        Дополняет properties tool_schema: enum + описание из get_param_schema().params[].choices.inline.

        Нужно для заготовок (magnet_id, keychain_id и т.п.): LLM видит допустимые id и title.
        Не трогает поля, у которых в tool_schema уже задан enum (например color для print_sheet).
        """
        params_list = param_schema.get("params")
        if not isinstance(params_list, list):
            return
        for pdef in params_list:
            pname = (pdef.get("name") or "").strip()
            if not pname or pname not in props:
                continue
            choices_def = pdef.get("choices")
            if not isinstance(choices_def, dict):
                continue
            inline = choices_def.get("inline")
            if not inline or not isinstance(inline, list):
                continue
            if (props.get(pname) or {}).get("enum"):
                continue
            enum_values: List[Any] = []
            human_parts: List[str] = []
            for item in inline:
                if not isinstance(item, dict):
                    continue
                item_id = item.get("id")
                if item_id is None:
                    continue
                item_title = item.get("title") or item.get("name")
                if item_title is None:
                    item_title = str(item_id)
                enum_values.append(item_id)
                human_parts.append(f"{item_id} — {item_title}")
            if not enum_values:
                continue
            orig = props.get(pname) or {}
            existing_desc = (orig.get("description") or "").strip()
            choices_desc = "Доступные варианты: " + ", ".join(human_parts) + "."
            desc = f"{existing_desc} {choices_desc}".strip() if existing_desc else choices_desc
            props[pname] = {**orig, "enum": enum_values, "description": desc}

    @staticmethod
    def sanitize_llm_reply_for_display(text: str) -> str:
        """
        Убирает артефакты ответа модели (Gemini/AITunnel: <ctrl46> вместо «:»)
        и утечки внутренних id в скобках (id: PaperCoated115M).
        """
        if not text or not isinstance(text, str):
            return (text or "").strip() if isinstance(text, str) else ""
        s = text
        s = re.sub(r"<ctrl\d+>", ":", s)
        s = re.sub(r"(?im)^\s*title\s*:\s*", "", s)
        # После замены ctrl иногда получается «title::» → одна двоеточие
        s = re.sub(r":{2,}", ":", s)
        s = re.sub(r"\s*\(id:\s*[A-Za-z][A-Za-z0-9_]*\)", "", s)
        return s.strip()

    @staticmethod
    def _parse_numbered_choice_lines(text: str) -> List[str]:
        """Строки вида «1. Вариант» → список вариантов по возрастанию номера."""
        if not text:
            return []
        found: List[tuple[int, str]] = []
        for m in re.finditer(r"(?m)^\s*(\d+)\.\s+(.+?)\s*$", text):
            try:
                n = int(m.group(1))
            except ValueError:
                continue
            title = (m.group(2) or "").strip()
            if title:
                found.append((n, title))
        found.sort(key=lambda x: x[0])
        return [t for _, t in found]

    def _try_force_print_sheet_material_choice(
        self,
        user_message: str,
        history: List[Dict[str, Any]],
        user_id: int,
    ) -> Optional[str]:
        """
        Пользователь ответил номером на список вариантов бумаги — без второго круга LLM.
        Ищем по точному title из последнего сообщения ассистента и вызываем calc_print_sheet.
        """
        um = (user_message or "").strip()
        if not um.isdigit():
            return None
        choice_idx = int(um) - 1
        if choice_idx < 0:
            return None

        last_assistant = ""
        for m in reversed(history or []):
            if m.get("role") == "assistant":
                last_assistant = (m.get("content") or "").strip()
                break
        if not last_assistant:
            return None

        titles = self._parse_numbered_choice_lines(last_assistant)
        # Только явное различение (≥2 пункта), иначе риск ложного срабатывания на чужие списки.
        if len(titles) < 2 or choice_idx >= len(titles):
            return None

        chosen_title = titles[choice_idx]
        r = self._execute_search_materials_single("print_sheet", chosen_title, "material")
        if r.get("error"):
            return None
        items = r.get("items") or []
        if len(items) != 1:
            return None
        mid = (items[0].get("id") or "").strip()
        if not mid:
            return None

        user_blob = "\n".join(
            (m.get("content") or "").strip()
            for m in (history or [])
            if m.get("role") == "user"
        )
        merged = self._merge_params_for_recalc("print_sheet", {}, user_blob, history or [])
        merged["material_id"] = mid
        merged.setdefault("color", "4+0")

        if not self._calc_params_sufficient("print_sheet", merged):
            logger.info(
                "print_sheet: выбор по номеру — не хватает полей для calc: %s",
                list(merged.keys()),
            )
            return None

        tool_name = "calc_print_sheet"
        payload = self._normalize_print_sheet_calc_args(dict(merged))
        logger.info(
            "print_sheet: принудительный расчёт после выбора №%s → material_id=%s",
            um,
            mid,
        )
        result = self.execute_tool(tool_name, payload)
        display_args = self._calc_args_for_display_and_storage(tool_name, payload)
        if isinstance(result, dict) and "error" not in result:
            self._user_calc_context[user_id] = {
                "slug": "print_sheet",
                "tool_name": tool_name,
                "params": dict(display_args),
            }
        return self._format_calc_result(tool_name, display_args, result)

    def _load_calculators_and_tools(self) -> None:
        try:
            with httpx.Client(timeout=HTTP_TIMEOUT) as client:
                r = client.get(f"{self.calc_api_url}/api/v1/calculators")
                r.raise_for_status()
                self._calculators = r.json()
        except (httpx.ConnectError, httpx.TimeoutException) as e:
            logger.warning("Calc API недоступен при инициализации: %s", e)
            self._reset_state()
            return
        except Exception as e:
            logger.exception("Ошибка загрузки калькуляторов: %s", e)
            self._reset_state()
            return

        tools: List[Dict[str, Any]] = []
        with httpx.Client(timeout=HTTP_TIMEOUT) as client:
            for calc in self._calculators:
                slug = calc.get("slug")
                if not slug:
                    continue
                try:
                    ps_r = client.get(f"{self.calc_api_url}/api/v1/param_schema/{slug}")
                    if ps_r.status_code == 200:
                        self._param_schemas[slug] = ps_r.json()

                    opts_r = client.get(f"{self.calc_api_url}/api/v1/options/{slug}")
                    opts: Dict[str, Any] = {}
                    if opts_r.status_code == 200:
                        opts = opts_r.json()
                        self._options_by_slug[slug] = opts
                        self.calculator_materials[slug] = list(opts.get("materials") or [])
                    else:
                        self.calculator_materials[slug] = []

                    schema_r = client.get(f"{self.calc_api_url}/api/v1/tool_schema/{slug}")
                    schema_r.raise_for_status()
                    schema = schema_r.json()

                    prompt_r = client.get(f"{self.calc_api_url}/api/v1/llm_prompt/{slug}")
                    if prompt_r.status_code == 200:
                        self._calc_llm_prompts[slug] = (prompt_r.json().get("prompt") or "").strip()
                except Exception as e:
                    logger.warning("Не удалось загрузить схемы для %s: %s", slug, e)
                    self.calculator_materials[slug] = []
                    continue

                name = schema.get("name") or f"calc_{slug}"
                params = dict(schema.get("parameters") or {"type": "object", "properties": {}})
                props = params.get("properties") or {}

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

                if slug in ("print_sheet", "print_laser") and "color" in props:
                    props["color"] = {
                        **(props.get("color") or {}),
                        "type": "string",
                        "enum": ["1+0", "4+0", "1+1", "4+1", "4+4"],
                        "description": "Цветность печати. 4+0 — односторонняя цветная, 4+4 — двусторонняя цветная. Обязательно передавай при вызове (по умолчанию 4+0).",
                    }

                param_schema = self._param_schemas.get(slug)
                if param_schema:
                    self._enrich_tool_props_from_param_schema_inline_choices(props, param_schema)

                if slug == "metal_pins":
                    attachments = (opts or {}).get("attachments") or []
                    packs = (opts or {}).get("packs") or []

                    if "attachment_id" in props:
                        choices = {a.get("code"): (a.get("name") or a.get("code")) for a in attachments if isinstance(a, dict)}
                        desc = (
                            props.get("attachment_id", {}).get("description")
                            or "Крепление значка (игла-цанга, булавка, магнит и т.п.)."
                        )
                        if choices:
                            human = ", ".join(f"{code} — {name}" for code, name in choices.items())
                            desc = f"{desc} Доступные варианты: {human}."
                        props["attachment_id"] = {
                            **(props.get("attachment_id") or {}),
                            "type": "string",
                            "default": "BC",
                            "enum": sorted(list(choices.keys()) or ["BC", "BC2", "PinMetal", "SafetyPin", "Screw", "TieClip", "Magnet17", "Magnet4513"]),
                            "description": desc,
                        }

                    if "pack_id" in props:
                        pack_choices = {p.get("code"): (p.get("name") or p.get("code")) for p in packs if isinstance(p, dict)}
                        desc_p = (
                            props.get("pack_id", {}).get("description")
                            or "Упаковка значков (пакетик, акриловая коробочка)."
                        )
                        if pack_choices:
                            human_p = ", ".join(f"{code} — {name}" for code, name in pack_choices.items())
                            desc_p = f"{desc_p} Доступные варианты: {human_p}."
                        props["pack_id"] = {
                            **(props.get("pack_id") or {}),
                            "type": "string",
                            "enum": sorted(list(pack_choices.keys()) or ["PolyBag", "AcrylicBox30", "AcrylicBox40", "AcrylicBox50"]),
                            "description": desc_p,
                        }

                tools.append({
                    "type": "function",
                    "function": {
                        "name": name,
                        "description": schema.get("description") or calc.get("description", ""),
                        "parameters": {**params, "properties": props},
                    },
                })

        self._tools = [SEARCH_KNOWLEDGE_TOOL, SEARCH_MATERIALS_TOOL] + tools
        self._calc_tool_by_slug = {}
        for t in tools:
            fn = (t.get("function") or {}).get("name") or ""
            if fn.startswith("calc_"):
                self._calc_tool_by_slug[fn[5:]] = t

        # Роутеру достаточно усечённого индекса (меньше токенов)
        self._calculator_index = build_calculator_index(self._calculators, max_chars=5000)
        self._router_tool = self._build_router_tool()
        loaded_slugs = sorted(self._calc_tool_by_slug.keys())
        logger.info(
            "Загружено калькуляторов: %s, tools: %s, calc_slugs: %s",
            len(self._calculators),
            len(self._tools),
            loaded_slugs,
        )

    def _reset_state(self) -> None:
        self._calculators = []
        self._tools = []
        self._calc_tool_by_slug = {}
        self._calc_llm_prompts = {}
        self._calculator_index = ""
        self._router_tool = {}
        self._param_schemas = {}
        self._options_by_slug = {}
        self.calculator_materials = {}

    def _build_router_tool(self) -> Dict[str, Any]:
        slugs = sorted({str(c.get("slug") or "").strip() for c in self._calculators if c.get("slug")})
        slug_enum: List[str] = [""] + slugs
        return {
            "type": "function",
            "function": {
                "name": "route_request",
                "description": "Классифицируй запрос: база знаний (knowledge) или расчёт (calculator) с указанием slug.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "intent": {
                            "type": "string",
                            "enum": ["knowledge", "calculator"],
                            "description": "knowledge — Wiki; calculator — смета.",
                        },
                        "calculator_slug": {
                            "type": "string",
                            "enum": slug_enum,
                            "description": "При knowledge — пустая строка. При calculator — slug калькулятора или пустая строка, если неясно.",
                        },
                        "reason": {
                            "type": "string",
                            "description": "Краткое обоснование на русском.",
                        },
                    },
                    "required": ["intent", "reason", "calculator_slug"],
                },
            },
        }

    @staticmethod
    def _normalize_choices_param(slug: str, param: str) -> str:
        slug = (slug or "").strip()
        param = (param or "material").strip() or "material"
        if slug == "lamination" and param == "lamination":
            return "material"
        return param

    def get_system_prompt(self) -> str:
        return build_calc_system_prompt_full(self._calculators)

    def get_tools(self) -> List[Dict[str, Any]]:
        return list(self._tools)

    @staticmethod
    def _router_user_content(user_message: str, history: List[Dict[str, Any]]) -> str:
        lines: List[str] = []
        tail = history[-12:] if history else []
        for m in tail:
            role = m.get("role")
            if role not in ("user", "assistant"):
                continue
            c = (m.get("content") or "").strip()
            if not c:
                continue
            if len(c) > 1500:
                c = c[:1500] + "…"
            label = "Пользователь" if role == "user" else "Ассистент"
            lines.append(f"{label}: {c}")
        block = "\n".join(lines) if lines else "(история пуста)"
        return (
            f"Текущее сообщение пользователя:\n{user_message}\n\n"
            f"Контекст диалога (последние реплики):\n{block}"
        )

    @staticmethod
    def _parse_router_result(llm_result: Dict[str, Any]) -> tuple[str, Optional[str]]:
        def _normalize(args: Dict[str, Any]) -> tuple[str, Optional[str]]:
            intent = str(args.get("intent") or "").strip().lower()
            slug = str(args.get("calculator_slug") or "").strip() or None
            if intent == "knowledge":
                return "knowledge", None
            if intent == "calculator":
                return "calculator", slug
            return "calculator", None

        tool_calls = llm_result.get("tool_calls") or []
        for tc in tool_calls:
            fn = (tc.get("function") or {}).get("name")
            if fn != "route_request":
                continue
            raw = (tc.get("function") or {}).get("arguments") or "{}"
            try:
                args = json.loads(raw) if isinstance(raw, str) else raw
            except json.JSONDecodeError:
                continue
            if isinstance(args, dict):
                return _normalize(args)

        text = (llm_result.get("content") or "").strip()
        if text:
            try:
                start = text.find("{")
                end = text.rfind("}")
                if start >= 0 and end > start:
                    obj = json.loads(text[start : end + 1])
                    if isinstance(obj, dict):
                        return _normalize(obj)
            except json.JSONDecodeError:
                pass
        return "calculator", None

    def _heuristic_magnet_slug(self, user_message: str) -> Optional[str]:
        """
        Явные формулировки про магниты — стабильный slug, если API отдал калькуляторы.
        Иначе роутер часто оставляет пустой slug → в tools попадает search_knowledge без calc_*.
        """
        t = (user_message or "").strip().lower()
        if not t:
            return None
        has_magnet = "магнит" in t or "magnet" in t
        if not has_magnet:
            return None
        # Ламинированные / винил (без «акрилового» магнита)
        if "magnet_laminated" in self._calc_tool_by_slug:
            if ("ламинирован" in t and "магнит" in t) or (
                "магнит" in t and "винил" in t and "акрил" not in t and "акрилов" not in t
            ):
                return "magnet_laminated"
        if "magnet_acrylic" in self._calc_tool_by_slug:
            if "акрил" in t or "акрилов" in t:
                return "magnet_acrylic"
        return None

    def _router_classify(
        self, user_message: str, history: List[Dict[str, Any]], user_id: int = 0
    ) -> tuple[str, Optional[str]]:
        if not self._router_tool:
            return "calculator", None
        try:
            router_system = build_router_system_prompt(self._calculator_index)
            messages = [
                {"role": "system", "content": router_system},
                {"role": "user", "content": self._router_user_content(user_message, history)},
            ]
            out = self.llm.chat(messages, tools=[self._router_tool])
            intent, slug = self._parse_router_result(out)
            if intent == "calculator" and (
                not slug or slug not in self._calc_tool_by_slug
            ):
                ctx = self._user_calc_context.get(user_id)
                if ctx and ctx.get("slug"):
                    prev = str(ctx["slug"]).strip()
                    if prev in self._calc_tool_by_slug:
                        slug = prev
                        logger.info("Router: slug восстановлен из контекста: %s", slug)
            # Эвристика магнитов: роутер часто даёт пустой slug или knowledge при явных формулировках
            mh = self._heuristic_magnet_slug(user_message)
            if mh:
                if intent == "knowledge":
                    intent = "calculator"
                    slug = mh
                    logger.info("Router: knowledge→calculator, эвристика магнитов → %s", mh)
                elif intent == "calculator" and (not slug or slug not in self._calc_tool_by_slug):
                    slug = mh
                    logger.info("Router: slug по эвристике магнитов → %s", mh)
            logger.info("Router: intent=%s slug=%s", intent, slug)
            return intent, slug
        except Exception as e:
            logger.warning("Router classify failed: %s — fallback calculator, узкий набор tools", e)
            return "calculator", None

    @staticmethod
    def _user_message_suggests_recalc(user_message: str) -> bool:
        """
        Короткие уточнения пересчёта (тираж, цветность) — для forced calc без LLM.
        Сообщения про смену материала/плотности не помечаем: их обрабатывает LLM + search_materials.
        """
        t = (user_message or "").strip().lower()
        if not t:
            return False
        # Смена материала / плотности — не forced recalc
        if re.search(r"\d+\s*гр", t) or re.search(r"\d+\s*г/м", t):
            return False
        if any(
            word in t
            for word in ("бумаг", "мелов", "глянц", "матов", "материал")
        ):
            return False
        if re.search(r"\d+\s*шт", t):
            return True
        if re.search(r"\b[14]\s*\+\s*[014]\b", t) or re.search(r"\b4\+4\b", t):
            return True
        if re.match(r"^\s*\d+\s*шт\s*$", t):
            return True
        if any(x in t for x in ("посчитай", "пересчитай")) and (
            re.search(r"\d+\s*шт", t) or re.search(r"\b[14]\s*\+\s*[014]\b", t)
        ):
            return True
        return False

    @staticmethod
    def _router_context_continuation_message(user_message: str) -> bool:
        """
        Сообщение похоже на продолжение расчёта (восстановление slug в роутере).
        Шире, чем _user_message_suggests_recalc: «посчитай 130гр» должно оставаться в калькуляторе,
        но не запускать forced calc без LLM.
        """
        if InsainAgent._user_message_suggests_recalc(user_message):
            return True
        t = (user_message or "").strip().lower()
        if not t:
            return False
        if any(x in t for x in ("посчитай", "пересчитай")) and re.search(r"\d", t):
            return True
        if re.search(r"\d+\s*гр", t) or re.search(r"\d+\s*г/м", t):
            return True
        return False

    def _router_apply_context_override(
        self,
        intent: str,
        slug: Optional[str],
        user_message: str,
        user_id: int,
        history: Optional[List[Dict[str, Any]]] = None,
    ) -> tuple[str, Optional[str]]:
        """
        Если роутер вернул knowledge при активной calc-сессии, но реплика похожа на пересчёт —
        принудительно calculator + slug из контекста (см. логи: «посчитай 4+4» → только Wiki).

        Дополнительно: продолжение диалога про акриловые магниты («какие заготовки», размеры)
        без успешного расчёта — принудительно magnet_acrylic, иначе уходит в Wiki без calc_*.
        """
        history = history or []
        intent, slug = self._router_magnet_thread_override(
            intent, slug, user_message, history
        )

        ctx = self._user_calc_context.get(user_id)
        if not ctx or not ctx.get("slug"):
            return intent, slug
        prev = str(ctx["slug"]).strip()
        if prev not in self._calc_tool_by_slug:
            return intent, slug
        # Роутер явно выбрал другой калькулятор — не затираем
        if intent == "calculator" and slug and slug in self._calc_tool_by_slug and slug != prev:
            return intent, slug
        if not self._router_context_continuation_message(user_message):
            return intent, slug
        if intent == "knowledge":
            logger.info("Router: intent исправлен knowledge→calculator по контексту расчёта (%s)", prev)
            return "calculator", prev
        if intent == "calculator" and (not slug or slug not in self._calc_tool_by_slug):
            logger.info("Router: slug восстановлен из контекста (override): %s", prev)
            return "calculator", prev
        return intent, slug

    def _router_magnet_thread_override(
        self,
        intent: str,
        slug: Optional[str],
        user_message: str,
        history: List[Dict[str, Any]],
    ) -> tuple[str, Optional[str]]:
        """Удерживаем magnet_acrylic в треде про акриловые магниты (заготовки, размеры в мм)."""
        if "magnet_acrylic" not in self._calc_tool_by_slug:
            return intent, slug
        t = (user_message or "").strip().lower()
        if not t:
            return intent, slug
        blob_u = " ".join(
            (m.get("content") or "").lower()
            for m in history[-12:]
            if m.get("role") == "user"
        )
        blob_a = " ".join(
            (m.get("content") or "").lower()
            for m in history[-12:]
            if m.get("role") == "assistant"
        )
        blob = f"{blob_u} {blob_a}"
        # Не перехватываем тред про ламинированные магниты
        if "ламинирован" in blob and "магнит" in blob:
            return intent, slug
        if "ламинирован" in t or ("винил" in t and "магнит" in t):
            return intent, slug
        acrylic_thread = ("магнит" in blob and ("акрил" in blob or "акрилов" in blob)) or (
            "магнит" in blob_u and ("акрил" in blob_u or "акрилов" in blob_u)
        )
        if not acrylic_thread:
            return intent, slug
        asks_blanks = "заготовк" in t or (
            "какие есть" in t and ("заготов" in t or "магнит" in t or "вариант" in t)
        )
        asks_dims = bool(re.search(r"\d+\s*[*xх]\s*\d+", t))
        if asks_blanks or asks_dims:
            logger.info(
                "Router: magnet_acrylic — продолжение диалога (заготовки/размеры), было intent=%s slug=%s",
                intent,
                slug,
            )
            return "calculator", "magnet_acrylic"
        return intent, slug

    @staticmethod
    def _params_from_share_url_in_text(text: str) -> Dict[str, Any]:
        """Параметры из share-ссылки калькулятора в ответе ассистента (fallback, если LLM не вызывала tool)."""
        out: Dict[str, Any] = {}
        if not text or "insain.ru" not in text:
            return out
        m = re.search(r"https://[^\s)]+", text)
        if not m:
            return out
        try:
            q = parse_qs(urlparse(m.group(0)).query)
        except Exception:
            return out
        if not q:
            return out
        def first(key: str) -> Optional[str]:
            v = q.get(key)
            return v[0] if v else None
        if first("quantity"):
            try:
                out["quantity"] = int(first("quantity") or 0)
            except (TypeError, ValueError):
                pass
        for dim, key in (("width", "width"), ("height", "height")):
            if first(key):
                try:
                    out[dim] = float(first(key) or 0)
                except (TypeError, ValueError):
                    pass
        mid = first("material_id")
        if mid:
            out["material_id"] = mid
        ct = first("color_type") or first("color")
        if ct:
            c = ct.strip()
            # В query string «+» декодируется как пробел (4+4 → «4 4»)
            m = re.match(r"^([14])\s+([014])$", c)
            if m:
                c = f"{m.group(1)}+{m.group(2)}"
            out["color"] = c
        lam = first("lamination_id")
        if lam:
            out["lamination_id"] = lam
        return out

    @staticmethod
    def _parse_print_sheet_from_assistant_block(text: str) -> Dict[str, Any]:
        """Разбор последнего блока «Печать листовая» от ассистента (тираж/размер/цвет)."""
        out: Dict[str, Any] = {}
        if not text:
            return out
        m = re.search(r"Тираж\t(\d+)", text)
        if m:
            try:
                out["quantity"] = int(m.group(1))
            except (TypeError, ValueError):
                pass
        m = re.search(r"Ширина, мм\t(\d+)", text)
        if m:
            try:
                out["width"] = float(m.group(1))
            except (TypeError, ValueError):
                pass
        m = re.search(r"Высота, мм\t(\d+)", text)
        if m:
            try:
                out["height"] = float(m.group(1))
            except (TypeError, ValueError):
                pass
        m = re.search(r"Цветность печати\t([^\n]+)", text)
        if m:
            c = m.group(1).strip()
            if c and c != "—":
                out["color"] = c
        return out

    def _merge_params_for_recalc(
        self,
        slug: str,
        ctx_params: Dict[str, Any],
        user_message: str,
        history: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """База из контекста + последний показанный расчёт в истории + правки из реплики пользователя."""
        merged: Dict[str, Any] = dict(ctx_params or {})
        # Последний блок расчёта / ссылка в истории (актуальнее застрявшего ctx после «галлюцинаций»)
        for msg in reversed(history or []):
            if msg.get("role") != "assistant":
                continue
            text = msg.get("content") or ""
            if "💰 Цена:" in text or "insain.ru/calculator/" in text:
                merged.update(self._params_from_share_url_in_text(text))
                if slug == "print_sheet":
                    merged.update(self._parse_print_sheet_from_assistant_block(text))
                break

        um = (user_message or "").strip()
        mq = re.search(r"(\d+)\s*шт", um, re.I)
        if mq:
            try:
                merged["quantity"] = int(mq.group(1))
            except (TypeError, ValueError):
                pass
        cm = re.search(r"\b([14]\+[014])\b", um)
        if cm and slug in ("print_sheet", "print_laser"):
            merged["color"] = cm.group(1)
        wh = re.search(r"(\d+)\s*[*xх]\s*(\d+)", um, re.I)
        if wh and slug == "print_sheet":
            try:
                merged["width"] = float(wh.group(1))
                merged["height"] = float(wh.group(2))
            except (TypeError, ValueError):
                pass
        return merged

    def _calc_params_sufficient(self, slug: str, params: Dict[str, Any]) -> bool:
        tool = self._calc_tool_by_slug.get(slug)
        if not tool:
            return False
        schema = (tool.get("function") or {}).get("parameters") or {}
        required = schema.get("required")
        if not isinstance(required, list):
            return True
        for key in required:
            val = params.get(key)
            if val is None:
                return False
            if isinstance(val, str) and not val.strip():
                return False
        return True

    def _try_forced_calc(
        self,
        intent: str,
        slug: Optional[str],
        user_message: str,
        user_id: int,
        history: List[Dict[str, Any]],
    ) -> Optional[str]:
        """
        Если модель вернула текст с «расчётом» без tool_calls — пересчитываем на сервере сами.
        """
        if intent != "calculator" or not slug or slug not in self._calc_tool_by_slug:
            return None
        if not self._user_message_suggests_recalc(user_message):
            return None
        ctx = self._user_calc_context.get(user_id)
        if not ctx or ctx.get("slug") != slug:
            return None
        tool_name = (ctx.get("tool_name") or "").strip() or f"calc_{slug}"
        base = dict(ctx.get("params") or {})
        merged = self._merge_params_for_recalc(slug, base, user_message, history)
        if not self._calc_params_sufficient(slug, merged):
            logger.warning("Forced calc: недостаточно параметров slug=%s keys=%s", slug, list(merged.keys()))
            return None
        logger.info("Forced calc: вызов %s с аргументами %s", tool_name, merged)
        result = self.execute_tool(tool_name, merged)
        display_args = self._calc_args_for_display_and_storage(tool_name, merged)
        if isinstance(result, dict) and "error" not in result:
            cslug = tool_name[5:] if tool_name.startswith("calc_") else tool_name
            self._user_calc_context[user_id] = {
                "slug": cslug,
                "tool_name": tool_name,
                "params": dict(display_args),
            }
        return self._format_calc_result(tool_name, display_args, result)

    def _tools_for_intent(
        self, intent: str, slug: Optional[str], full_tools: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        if intent == "knowledge":
            return [SEARCH_KNOWLEDGE_TOOL]
        if intent == "calculator":
            if slug and slug in self._calc_tool_by_slug:
                return [SEARCH_MATERIALS_TOOL, self._calc_tool_by_slug[slug]]
            logger.warning(
                "Router: неизвестный или пустой slug %r — узкий набор (без всех calc_*)",
                slug,
            )
            return [SEARCH_KNOWLEDGE_TOOL, SEARCH_MATERIALS_TOOL]
        return list(full_tools)

    def _system_prompt_for_intent(
        self, intent: str, slug: Optional[str], user_id: int = 0
    ) -> str:
        if intent == "knowledge":
            return build_kb_system_prompt()
        if intent == "calculator" and slug and slug in self._calc_tool_by_slug:
            meta = self._find_calculator_meta(slug)
            tool_name = (self._calc_tool_by_slug[slug].get("function") or {}).get("name") or f"calc_{slug}"
            calc_prompt = self._calc_llm_prompts.get(slug, "")
            recalc_append = ""
            ctx = self._user_calc_context.get(user_id)
            if ctx and ctx.get("slug") == slug and isinstance(ctx.get("params"), dict):
                recalc_append = build_recalc_context(ctx["params"], slug)
            return build_calc_system_prompt(
                slug=slug,
                tool_name=tool_name,
                calculator_description=meta.get("description", ""),
                calculator_prompt=calc_prompt,
                recalc_append=recalc_append,
            )
        return build_calc_system_prompt_full(self._calculators)

    def _find_calculator_meta(self, slug: str) -> Dict[str, Any]:
        for c in self._calculators:
            if c.get("slug") == slug:
                return c
        return {}

    def _load_calendar_overrides(self) -> Dict[str, set]:
        if hasattr(self, "_calendar_overrides"):
            return self._calendar_overrides  # type: ignore[attr-defined]

        root = Path(__file__).resolve().parent.parent
        common_path = root / "calc_service" / "data" / "common.json"
        working_days: set[str] = set()
        weekend_working: set[str] = set()
        try:
            text_lines: list[str] = []
            with open(common_path, encoding="utf-8") as f:
                for line in f:
                    if "//" in line:
                        line = line.split("//", 1)[0]
                    if line.strip():
                        text_lines.append(line)
            data = json.loads("".join(text_lines))
            calendar = data.get("calendar") or {}
            working_days = set(calendar.get("workingDays") or [])
            weekend_working = set(calendar.get("weekEnd") or [])
        except Exception as e:
            logger.warning("Не удалось загрузить календарь из common.json: %s", e)

        self._calendar_overrides = {
            "workingDays": working_days,
            "weekEnd": weekend_working,
        }
        return self._calendar_overrides  # type: ignore[return-value]

    def _is_business_day(self, dt: datetime) -> bool:
        overrides = self._load_calendar_overrides()
        working_days: set[str] = overrides["workingDays"]
        weekend_working: set[str] = overrides["weekEnd"]
        day_str = f"{dt.day}.{dt.month}"
        weekday = dt.weekday()
        if 0 <= weekday <= 4:
            return day_str not in working_days
        return day_str in weekend_working

    def _add_business_days(self, start: datetime, days: int) -> datetime:
        if days == 0:
            return start
        step = 1 if days > 0 else -1
        remaining = abs(days)
        current = start
        while remaining > 0:
            current += timedelta(days=step)
            if self._is_business_day(current):
                remaining -= 1
        return current

    @staticmethod
    def _ru_plural(n: int, one: str, few: str, many: str) -> str:
        n = abs(int(n))
        titles = (one, few, many)
        cases = (2, 0, 1, 1, 1, 2)
        if 5 <= n % 100 <= 20:
            idx = 2
        else:
            idx = cases[n % 10 if n % 10 < 5 else 5]
        return titles[idx]

    @staticmethod
    def _round_price(price: float, quantity: int, threshold: float = 100.0) -> float:
        try:
            p = float(price)
            q = int(quantity)
        except (TypeError, ValueError):
            return float(price or 0)
        if p <= 0 or q <= 0:
            return p
        threshold_1 = threshold / q
        module = max(10 ** math.ceil(math.log10(threshold_1)), 0.01)
        item_price = p / q
        new_item_price = math.ceil(item_price / module) * module
        if abs(item_price - new_item_price) > threshold_1 and module > 0.01:
            module /= 10
            new_item_price = math.ceil(item_price / module) * module
        new_item_price = round(new_item_price * 100) / 100.0
        return new_item_price * q

    def _format_time_ready_label(self, time_ready_hours: float) -> str:
        try:
            hours = max(0.0, float(time_ready_hours))
        except (TypeError, ValueError):
            return "срок не определён"
        if hours <= 0:
            return "срок не определён"
        if hours < 8:
            h = int(round(hours)) or 1
            label = self._ru_plural(h, "рабочий час", "рабочих часа", "рабочих часов")
            return f"{h} {label}"
        days = int(hours // 8)
        if hours % 8:
            days += 1
        ready_date = self._add_business_days(datetime.now(), days)
        date_str = ready_date.strftime("%d.%m.%Y")
        day_label = self._ru_plural(days, "рабочий день", "рабочих дня", "рабочих дней")
        return f"≈ {days} {day_label} (до {date_str})"

    @staticmethod
    def _mode_label(mode: Any) -> str:
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

        display_price = price
        display_unit_price = unit_price
        if quantity and price > 0:
            rounded = self._round_price(price, quantity)
            if rounded > 0:
                display_price = rounded
                display_unit_price = rounded / max(1, quantity)

        params_lines: List[str] = []
        if quantity is not None:
            params_lines.append(f"Тираж\t{quantity}")
        if w is not None and h is not None:
            params_lines.append(f"Ширина, мм\t{int(w)}")
            params_lines.append(f"Высота, мм\t{int(h)}")

        color = (args.get("color") or "").strip()
        if slug in ("print_sheet", "print_laser"):
            params_lines.append(f"Цветность печати\t{color or '4+0'}")

        if not (slug == "metal_pins" and not materials):
            params_lines.append(f"Материал\t{material_title}")

        if slug == "print_sheet":
            lamination_id = (args.get("lamination_id") or "").strip()
            if lamination_id and len(materials) > 1:
                lam_title = materials[1].get("title") or materials[1].get("name") or "ламинация"
                params_lines.append(f"Ламинация\t{lam_title}")
            elif lamination_id:
                params_lines.append("Ламинация\tда")

        mode = args.get("mode", 1)
        params_lines.append(f"Срочность\t{self._mode_label(mode)}")

        if slug == "metal_pins":
            process = (args.get("process") or "").strip() or "2d"
            num_enamels = args.get("num_enamels")
            plating = (args.get("plating") or "").strip() or "nickel"
            metal = (args.get("metal") or "").strip() or "brass"
            raw_attachment_id = (args.get("attachment_id") or "").strip()
            raw_pack_id = (args.get("pack_id") or "").strip()
            attachment_label = ""
            pack_label = ""
            if materials:
                for m in materials:
                    code = (m.get("code") or "").strip()
                    title = m.get("title") or m.get("name") or code
                    if code and code == raw_attachment_id:
                        attachment_label = f"{title} ({code})"
                    if code and code == raw_pack_id:
                        pack_label = f"{title} ({code})"
            params_lines.append(f"Технология\t{process}")
            if num_enamels is not None:
                params_lines.append(f"Цветов эмали\t{num_enamels}")
            params_lines.append(f"Покрытие\t{plating}")
            params_lines.append(f"Металл\t{metal}")
            if raw_attachment_id and attachment_label:
                params_lines.append(f"Крепление\t{attachment_label}")
            elif raw_attachment_id:
                params_lines.append(f"Крепление\tнеизвестное крепление (код {raw_attachment_id})")
            if raw_pack_id and pack_label:
                params_lines.append(f"Упаковка\t{pack_label}")
            elif raw_pack_id:
                params_lines.append(f"Упаковка\tкод {raw_pack_id}")

        lines: List[str] = []
        lines.append(calc_title)
        lines.append("")
        lines.append("\n".join(params_lines))

        suspicious = (price == 0) or (cost == 0) or (time_hours == 0 and weight_kg == 0)
        lines.append("")
        if display_price:
            lines.append(f"💰 Цена: {display_price:.2f} ₽ ({display_unit_price:.2f} ₽/шт)")
        else:
            lines.append("💰 Цена: 0 ₽")
        lines.append(f"💵 Себестоимость: {cost:.2f} ₽")
        lines.append(f"⏱ Время изготовления: {time_hours:.2f} ч")
        time_ready_label = self._format_time_ready_label(time_ready)
        lines.append(f"📅 Готовность: {time_ready_label}")
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

    def _execute_search_materials_single(
        self, slug: str, query: str, param: str = "material"
    ) -> Dict[str, Any]:
        """Один запрос к /choices без fallback (для внутренних повторов)."""
        param = self._normalize_choices_param(slug, param)
        try:
            with httpx.Client(timeout=HTTP_TIMEOUT) as client:
                r = client.post(
                    f"{self.calc_api_url}/api/v1/choices",
                    json={
                        "slug": slug,
                        "param": param,
                        "query": (query or "").strip(),
                        "limit": CHOICES_SEARCH_LIMIT,
                    },
                )
                r.raise_for_status()
                data = r.json()
                items = data.get("items") or []
                hint = (
                    "Подставь выбранный id в вызов calc_* (material_id / lamination_id). "
                    "Пользователю показывай только title, без id. "
                    "Если пользователь ответил одной цифрой на твой нумерованный список — "
                    "сразу вызови search_materials с query равным полному title этого пункта."
                )
                return {"items": items, "hint": hint}
        except httpx.HTTPStatusError as e:
            detail = (e.response.json() or {}).get("detail", str(e)) if e.response else str(e)
            return {"error": detail, "items": []}
        except (httpx.ConnectError, httpx.TimeoutException) as e:
            logger.warning("Choices API недоступен: %s", e)
            return {"error": "Сервис поиска материалов временно недоступен", "items": []}
        except Exception as e:
            logger.exception("search_materials: %s", e)
            return {"error": str(e), "items": []}

    @staticmethod
    def _fallback_queries_print_sheet_material(query: str) -> List[str]:
        """
        Каталог ищет по «меловка 115», а LLM часто шлёт «Мелованная бумага 115 г/м²» → пустой ответ.
        """
        q = (query or "").strip()
        candidates: List[str] = []
        if q:
            candidates.append(q)
        if q and "мелованн" in q.lower():
            candidates.append(re.sub(r"мелованн[а-я]*", "меловка", q, flags=re.I))
        m = re.search(r"(\d{2,3})", q)
        if m:
            g = m.group(1)
            candidates.extend(
                [
                    f"меловка {g}",
                    f"меловка {g}г",
                    f"меловка {g} г/м",
                    g,
                ]
            )
        candidates.extend(["меловка", "мел"])
        seen: set[str] = set()
        out: List[str] = []
        for c in candidates:
            c = c.strip()
            if c and c not in seen:
                seen.add(c)
                out.append(c)
        return out

    def _execute_search_materials(self, slug: str, query: str, param: str = "material") -> Dict[str, Any]:
        param_norm = self._normalize_choices_param(slug, param)
        queries: List[str] = [(query or "").strip()]
        if slug == "print_sheet" and param_norm == "material":
            queries = self._fallback_queries_print_sheet_material(query)

        last: Dict[str, Any] = {"items": [], "hint": ""}
        for i, q in enumerate(queries):
            last = self._execute_search_materials_single(slug, q, param)
            if last.get("error"):
                return last
            items = last.get("items") or []
            if items:
                if i > 0:
                    logger.info(
                        "search_materials: найдено по fallback-запросу %r (было пусто для %r)",
                        q,
                        (query or "").strip(),
                    )
                return last
        return last

    @staticmethod
    def _material_id_looks_suspicious(material_id: str) -> bool:
        """Эвристика: LLM выдумывает snake_case вроде paper_coated_115 вместо PaperCoated115M."""
        mid = (material_id or "").strip()
        if not mid:
            return True
        if re.match(r"^[A-Z][a-zA-Z0-9]+$", mid) and mid[0].isupper():
            return False
        if "_" in mid and mid == mid.lower():
            return True
        if re.match(r"^[a-z][a-z0-9_]*$", mid) and "_" in mid:
            return True
        if "paper_coated" in mid.lower() or mid.startswith("paper_"):
            return True
        return False

    def _resolve_print_sheet_material_id(self) -> Optional[str]:
        """Подставить material_id из каталога, если LLM передал несуществующий код."""
        for q in ["меловка 115", "115", "меловка", "мел"]:
            r = self._execute_search_materials_single("print_sheet", q, "material")
            if r.get("error"):
                continue
            items = r.get("items") or []
            if items:
                rid = (items[0].get("id") or "").strip()
                if rid:
                    return rid
        return None

    @staticmethod
    def _normalize_metal_pins_calc_args(arguments: Dict[str, Any]) -> Dict[str, Any]:
        """LLM часто шлёт width/height вместо width_mm/height_mm — иначе calc_service даёт HTTP 500."""
        out = dict(arguments)
        if out.get("width_mm") is None and out.get("width") is not None:
            out["width_mm"] = out.pop("width")
        if out.get("height_mm") is None and out.get("height") is not None:
            out["height_mm"] = out.pop("height")
        wm, hm = out.get("width_mm"), out.get("height_mm")
        if wm is not None and hm is None:
            out["height_mm"] = wm
        elif hm is not None and wm is None:
            out["width_mm"] = hm
        return out

    def _normalize_print_sheet_calc_args(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Сайт/LLM иногда шлют color_mode вместо color; material_id — выдуманный snake_case."""
        out = dict(arguments)
        if "color_mode" in out and not (out.get("color") or "").strip():
            cm = str(out.pop("color_mode") or "").strip()
            if cm in ("40", "4+0"):
                out["color"] = "4+0"
            elif cm in ("44", "4+4"):
                out["color"] = "4+4"
            elif cm in ("11", "1+1"):
                out["color"] = "1+1"
            elif "+" in cm:
                out["color"] = cm
        mid = str(out.get("material_id") or "").strip()
        if self._material_id_looks_suspicious(mid):
            resolved = self._resolve_print_sheet_material_id()
            if resolved:
                logger.info("print_sheet: заменён подозрительный material_id %r → %r", mid, resolved)
                out["material_id"] = resolved
        return out

    def _calc_args_for_display_and_storage(
        self, calc_tool_name: str, raw_args: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Те же правки, что перед POST в calc, чтобы контекст и текст ответа не содержали выдуманный id."""
        if not calc_tool_name.startswith("calc_"):
            return dict(raw_args)
        cslug = calc_tool_name[5:]
        if cslug == "print_sheet":
            return self._normalize_print_sheet_calc_args(dict(raw_args))
        if cslug == "metal_pins":
            return self._normalize_metal_pins_calc_args(dict(raw_args))
        return dict(raw_args)

    def execute_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        if tool_name == "search_knowledge":
            query = (arguments.get("query") or "").strip()
            if not query:
                return {"error": "Укажи запрос для поиска в базе знаний.", "results": []}
            logger.info("execute_tool: search_knowledge query=%r", query)
            results = self.kb.search(query, limit=5)
            if not results:
                return {"message": "По запросу ничего не найдено в базе знаний.", "results": []}
            context = self.kb.get_context(query)
            return {"results": results, "context": context}

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
            payload = dict(arguments)
            if slug == "print_sheet":
                payload = self._normalize_print_sheet_calc_args(payload)
            elif slug == "metal_pins":
                payload = self._normalize_metal_pins_calc_args(payload)
            with httpx.Client(timeout=HTTP_TIMEOUT) as client:
                r = client.post(f"{self.calc_api_url}/api/v1/calc/{slug}", json=payload)
                r.raise_for_status()
                result = r.json()
                logger.info("tool result keys: %s", list(result.keys()))
                return result
        except httpx.HTTPStatusError as e:
            if e.response.status_code in (400, 422):
                try:
                    body = e.response.json() or {}
                except Exception:
                    body = {}
                detail = body.get("detail", str(e))
                if isinstance(detail, list):
                    msgs: List[str] = []
                    for item in detail:
                        if isinstance(item, dict):
                            msg = item.get("msg") or str(item)
                            msgs.append(msg)
                        else:
                            msgs.append(str(item))
                    detail = "; ".join(msgs)
                elif isinstance(detail, dict):
                    detail = str(detail)
                return {"error": str(detail)}
            body_preview = (e.response.text or "")[:500]
            logger.warning(
                "Calc API HTTP %s url=%s body[:500]=%r",
                e.response.status_code,
                str(e.request.url),
                body_preview,
            )
            err_out = f"Ошибка расчёта (HTTP {e.response.status_code})"
            if e.response.status_code == 404:
                ct = (e.response.headers.get("content-type") or "").lower()
                if "text/html" in ct:
                    err_out = (
                        "Сервис расчётов вернул 404 (часто неверный CALC_API_URL или прокси). "
                        "Проверьте адрес API и nginx."
                    )
                else:
                    try:
                        detail = (e.response.json() or {}).get("detail")
                        ds = str(detail) if detail is not None else ""
                        if "неизвестный калькулятор" in ds.lower() or "unknown" in ds.lower():
                            err_out = (
                                "Калькулятор на сервере расчётов не найден — "
                                "вероятно, устаревший деплой calc_service. "
                                "Сверьте: python bot_service/check_calc_registry.py"
                            )
                    except Exception:
                        pass
            return {"error": err_out}
        except (httpx.ConnectError, httpx.TimeoutException) as e:
            logger.warning("Calc API недоступен: %s", e)
            return {"error": "Сервис расчётов временно недоступен, попробуйте позже"}
        except Exception as e:
            logger.exception("execute_tool: %s", e)
            return {"error": str(e)}

    def chat(
        self,
        user_message: str,
        history: Optional[List[Dict[str, Any]]] = None,
        user_id: int = 0,
    ) -> str:
        history = history or []
        if len(history) > MAX_HISTORY_MESSAGES:
            history = history[-MAX_HISTORY_MESSAGES:]

        full_tools = self.get_tools()
        if not full_tools:
            return "Сервис расчётов временно недоступен, попробуйте позже."

        intent = "calculator"
        slug: Optional[str] = None
        if AGENT_USE_ROUTER:
            intent, slug = self._router_classify(user_message, history, user_id=user_id)
            intent, slug = self._router_apply_context_override(
                intent, slug, user_message, user_id, history
            )
            tools = self._tools_for_intent(intent, slug, full_tools)
            system_prompt = self._system_prompt_for_intent(intent, slug, user_id=user_id)
        else:
            tools = full_tools
            system_prompt = build_calc_system_prompt_full(self._calculators)

        if AGENT_USE_ROUTER and intent == "calculator" and slug == "print_sheet":
            forced_choice = self._try_force_print_sheet_material_choice(
                user_message, history, user_id
            )
            if forced_choice is not None:
                return self.sanitize_llm_reply_for_display(forced_choice)

        messages: List[Dict[str, Any]] = [
            {"role": "system", "content": system_prompt},
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
            forced = self._try_forced_calc(intent, slug, user_message, user_id, history)
            if forced is not None:
                return self.sanitize_llm_reply_for_display(forced.strip())
            return self.sanitize_llm_reply_for_display(
                (content or "").strip() or "Нет ответа."
            )

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
                display_args = self._calc_args_for_display_and_storage(calc_tool_name, calc_args)
                if "error" not in calc_result:
                    cslug = calc_tool_name[5:] if calc_tool_name.startswith("calc_") else calc_tool_name
                    self._user_calc_context[user_id] = {
                        "slug": cslug,
                        "tool_name": calc_tool_name,
                        "params": dict(display_args),
                    }
                return self.sanitize_llm_reply_for_display(
                    self._format_calc_result(calc_tool_name, display_args, calc_result)
                )

            try:
                result = self.llm.chat(messages, tools=tools)
            except Exception as e:
                logger.exception("LLM follow-up error: %s", e)
                return "Произошла ошибка при обработке ответа."
            content = result.get("content")
            tool_calls = result.get("tool_calls") or []

        return self.sanitize_llm_reply_for_display(
            (content or "").strip()
            or "Не удалось выполнить расчёт. Попробуйте уточнить параметры."
        )


if __name__ == "__main__":
    agent = InsainAgent()
    print("SYSTEM PROMPT (fallback):")
    print(agent.get_system_prompt())
    print(f"\nTools count: {len(agent.get_tools())}")
    for t in agent.get_tools():
        print(f"  - {t['function']['name']}")
