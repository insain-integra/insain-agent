"""
Ядро бота Insain: одноступенчатый агент с function calling.

LLM видит все калькуляторы (tools) + search_materials, сама выбирает нужный.
Результат расчёта форматируется в Python (_format_calc_result).
"""

from __future__ import annotations

import json
import logging
import math
import os
from datetime import datetime, timedelta
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
from knowledge_base import KnowledgeBase

logger = logging.getLogger(__name__)

CALC_API_URL = os.getenv("CALC_API_URL", "http://localhost:8001").strip().rstrip("/")

MAX_HISTORY_MESSAGES = 20
HTTP_TIMEOUT = 15.0

SYSTEM_PROMPT = (
    "Ты — ассистент компании Инсайн. Рассчитываешь стоимость через калькуляторы (tools).\n"
    "ВАЖНО: единственный источник правды о параметрах — tool_schema (properties, enum, required). "
    "Игнорируй свои предыдущие ответы о том, какие параметры доступны или недоступны. "
    "Если параметр есть в tool_schema — он доступен, даже если ранее ты говорил обратное.\n"
    "Для подбора material_id/lamination_id вызови search_materials(slug, query), из результата подставь id.\n"
    "Коды менеджеру не показывай. mode: 0=эконом, 1=стандарт, 2=экспресс (по умолчанию 1).\n"
    "При пересчёте (смена параметра) вызывай калькулятор заново. Результат покажу я — не придумывай цены и ссылки.\n"
    "Если вопрос не про расчёт, а про компанию/процессы/услуги — вызови search_knowledge(query) для поиска в базе знаний.\n"
    "Ответы: plain text, без Markdown. Отвечай на русском."
)

SEARCH_KNOWLEDGE_TOOL: Dict[str, Any] = {
    "type": "function",
    "function": {
        "name": "search_knowledge",
        "description": (
            "Поиск в базе знаний компании Инсайн (Wiki). "
            "Используй для вопросов о компании, услугах, процессах, инструкциях — всего, что не касается расчёта стоимости."
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
        self.kb = KnowledgeBase()
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

                # Металлические значки: крепления и упаковка.
                # По умолчанию учитываем крепление игла-цанга (BC) и явно подсвечиваем LLM,
                # какие коды чему соответствуют, чтобы не галлюцинировать.
                if slug == "metal_pins":
                    attachments = (opts or {}).get("attachments") or []
                    packs = (opts or {}).get("packs") or []

                    if "attachment_id" in props:
                        # Базовое описание + варианты из /options.
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

    def _load_calendar_overrides(self) -> Dict[str, set]:
        """
        Загрузить рабочие/праздничные дни из calc_service/data/common.json.
        workingDays — праздничные дни (будни, которые стали выходными),
        weekEnd — выходные, которые стали рабочими.
        """
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
                    # Убираем комментарии // ...
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
        """
        Рабочий день с учётом календаря:
        - будни, которых нет в workingDays;
        - выходные из weekEnd считаются рабочими.
        Формат дат в common.json: "д.М" (например, "3.1").
        """
        overrides = self._load_calendar_overrides()
        working_days: set[str] = overrides["workingDays"]
        weekend_working: set[str] = overrides["weekEnd"]

        day_str = f"{dt.day}.{dt.month}"
        weekday = dt.weekday()  # 0=понедельник, 6=воскресенье

        if 0 <= weekday <= 4:
            # Будние: если день не в списке праздничных workingDays — рабочий.
            return day_str not in working_days
        # Выходные: если день отмечен как рабочий в weekEnd — рабочий.
        return day_str in weekend_working

    def _add_business_days(self, start: datetime, days: int) -> datetime:
        """Добавить N рабочих дней с учётом праздников/рабочих выходных из common.json."""
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
        """Русские окончания по схеме из timeToWords."""
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
        """
        Округление цены по правилу insaincalc.round из js_legacy/common.js.
        Себестоимость не меняем, только финальную цену.
        """
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
        """
        Человекочитаемый срок готовности:
        - < 8 часов → N рабочих часов (со склонениями)
        - ≥ 8 часов → N рабочих дней + дата готовности от сегодняшнего дня.
        """
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

        # Переводим рабочие часы в дни, округляя вверх
        days = int(hours // 8)
        if hours % 8:
            days += 1

        ready_date = self._add_business_days(datetime.now(), days)
        date_str = ready_date.strftime("%d.%m.%Y")
        day_label = self._ru_plural(days, "рабочий день", "рабочих дня", "рабочих дней")
        return f"≈ {days} {day_label} (до {date_str})"

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

        # Округляем финальную цену по бизнес-правилам (round из common.js), себестоимость не трогаем.
        display_price = price
        display_unit_price = unit_price
        if quantity and price > 0:
            rounded = self._round_price(price, quantity)
            if rounded > 0:
                display_price = rounded
                display_unit_price = rounded / max(1, quantity)

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

        # Материал: для большинства калькуляторов берём из первого материала,
        # для металлических значков выводим отдельные поля ниже.
        if not (slug == "metal_pins" and not materials):
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

        # Доп. параметры для металлических значков — всегда явно показываем, что рассчитано.
        if slug == "metal_pins":
            process = (args.get("process") or "").strip() or "2d"
            num_enamels = args.get("num_enamels")
            plating = (args.get("plating") or "").strip() or "nickel"
            metal = (args.get("metal") or "").strip() or "brass"
            raw_attachment_id = (args.get("attachment_id") or "").strip()
            raw_pack_id = (args.get("pack_id") or "").strip()

            # Попробуем получить человекочитаемые названия крепления/упаковки из материалов расчёта.
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
                # Если код не распознан, лучше явно показать, что это неизвестное крепление, а не придумывать название.
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
        Выполнить инструмент: search_knowledge → KB,
        search_materials → POST /api/v1/choices, calc_* → POST /api/v1/calc/{slug}.
        """
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
