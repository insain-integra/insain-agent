"""
Промпты для LLM-агента Insain.

Архитектура двухэтапная:
1) Роутер — классификация запроса (knowledge / calculator + product_slug).
2) Исполнитель — узкий system prompt + только нужные tools.

Product-first: роутер выбирает product_slug (обёртка над калькулятором),
исполнитель получает base_calc tool + product-specific defaults и промт.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional


# ---------------------------------------------------------------------------
#  Product index (для роутера)
# ---------------------------------------------------------------------------

def build_product_index(
    products: List[Dict[str, Any]],
    max_chars: int = 8000,
) -> str:
    """Справочник продуктов для роутера: product_slug — title. disambiguation [keywords]."""
    lines: List[str] = []
    for p in products:
        slug = (p.get("product_slug") or "").strip()
        if not slug:
            continue
        if not p.get("available", True):
            continue
        title = (p.get("title") or slug).strip()
        dis = (p.get("disambiguation") or "").strip()
        kws = p.get("keywords") or []
        kw_str = ", ".join(str(x) for x in kws[:6]) if kws else ""
        block = f"- {slug} — {title}"
        if dis:
            block += f". {dis}"
        if kw_str:
            block += f" [{kw_str}]"
        lines.append(block)
    text = "\n".join(lines).strip()
    if len(text) > max_chars:
        return text[: max_chars - 80] + "\n\n[… справочник обрезан …]"
    return text


def build_product_categories(
    products: List[Dict[str, Any]],
) -> str:
    """Категории продуктов для fallback-промта (без calc tools)."""
    cats: Dict[str, List[str]] = {}
    cat_labels = {
        "print": "Печатная продукция",
        "outdoor": "Наружная реклама и навигация",
        "badges": "Бейджи и значки",
        "souvenir": "Сувенирная продукция",
        "calendar": "Календари",
        "sticker": "Наклейки",
        "production": "Промышленная обработка",
    }
    for p in products:
        if not p.get("available", True):
            continue
        cat = p.get("category") or "other"
        title = p.get("title") or p.get("product_slug", "")
        cats.setdefault(cat, []).append(title)
    lines: List[str] = []
    for key, label in cat_labels.items():
        items = cats.get(key)
        if not items:
            continue
        lines.append(f"• {label}: {', '.join(items)}")
    other = cats.get("other")
    if other:
        lines.append(f"• Другое: {', '.join(other)}")
    return "\n".join(lines) or "(продукты не загружены)"


# ---------------------------------------------------------------------------
#  Backward-compat: старые функции (используются, если продукты не загружены)
# ---------------------------------------------------------------------------

def build_calculator_index(
    calculators: List[Dict[str, Any]],
    max_chars: int = 12000,
    only_slug: Optional[str] = None,
) -> str:
    """DEPRECATED: используй build_product_index. Краткий справочник калькуляторов."""
    lines: List[str] = []
    for c in calculators:
        slug = (c.get("slug") or "").strip()
        if not slug:
            continue
        if only_slug and slug != only_slug:
            continue
        name = (c.get("name") or slug).strip()
        desc = (c.get("description") or "").strip().replace("\n", " ")
        kws = c.get("keywords") or []
        kw_str = ", ".join(str(x) for x in kws if x) if isinstance(kws, (list, tuple)) else str(kws or "")
        block = f"- {slug} — {name}"
        if desc:
            block += f". {desc}"
        if kw_str:
            block += f" Ключевые слова: {kw_str}."
        lines.append(block)
    text = "\n".join(lines).strip()
    if len(text) > max_chars:
        return text[: max_chars - 80] + "\n\n[… справочник обрезан …]"
    return text


def build_calculator_categories_short(
    calculators: List[Dict[str, Any]],
    max_items: int = 40,
) -> str:
    """DEPRECATED: используй build_product_categories."""
    lines: List[str] = []
    for c in calculators[:max_items]:
        slug = (c.get("slug") or "").strip()
        if not slug:
            continue
        name = (c.get("name") or slug).strip()
        lines.append(f"- {name} ({slug})")
    return "\n".join(lines).strip() or "(калькуляторы не загружены)"


# ---------------------------------------------------------------------------
#  Recalc context
# ---------------------------------------------------------------------------

def build_recalc_context(prev_params: Dict[str, Any], slug: str) -> str:
    """Блок для system prompt: параметры предыдущего успешного расчёта."""
    lines = [f"=== ПРЕДЫДУЩИЙ РАСЧЁТ ({slug}) ==="]
    lines.append("Используй эти параметры как базу, меняй только то, что просит пользователь:")
    for k, v in sorted(prev_params.items()):
        lines.append(f"  {k}: {v}")
    lines.append("Вызови калькулятор с полным набором аргументов при любом изменении параметров.")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
#  Router system prompt (product-first)
# ---------------------------------------------------------------------------

def build_router_system_prompt(
    calculator_index: str,
    kb_description: str = "внутренняя Wiki: компания, процессы, сроки, технологии, инструкции",
) -> str:
    """
    System prompt для роутера: intent + product_slug.

    calculator_index может быть как product_index, так и старым calc_index.
    """
    idx = (calculator_index or "").strip()
    return (
        "Ты — классификатор запросов менеджера рекламно-производственной компании Инсайн.\n"
        "Проанализируй текущее сообщение пользователя с учётом контекста диалога.\n"
        "Обязательно вызови функцию route_request.\n\n"

        "=== ПРАВИЛА КЛАССИФИКАЦИИ ===\n"
        "intent — строго одно из двух:\n"
        "- knowledge — справочный вопрос без числового расчёта "
        f"({kb_description}).\n"
        "- calculator — любой запрос со сметой, стоимостью, тиражом, расчётом, "
        "пересчётом, выбором материала под заказ.\n"
        "- calculator — также вопросы о возможностях расчёта: «что ты можешь посчитать», "
        "«какие калькуляторы есть», «список продуктов» → intent=calculator, product_slug пустая строка.\n\n"

        "product_slug:\n"
        "- При intent=knowledge — пустая строка.\n"
        "- При intent=calculator — slug ОДНОГО наиболее подходящего продукта из списка ниже.\n"
        "- Если однозначно определить нельзя — пустая строка (агент уточнит у пользователя).\n\n"

        "=== РАЗЛИЧЕНИЕ ПОХОЖИХ ПРОДУКТОВ ===\n"
        "«значки» без уточнения → pins_metal_enamel (металлические по умолчанию).\n"
        "«значки деревянные/из фанеры» → pins_wood.\n"
        "«значки пластиковые с гравировкой» → pins_plastic_engraving.\n"
        "«значки пластиковые/акриловые с печатью/УФ» → pins_plastic_uv.\n"
        "«значки полимерные/эпоксидные» → pins_polymer.\n"
        "«бейджи с гравировкой» → badge_laser_engraving.\n"
        "«бейджи с УФ» → badge_uv_print.\n"
        "«бейджи с заливкой» → badge_poly_fill.\n"
        "«магниты акриловые» → (ищи magnet_acrylic если есть, иначе knowledge).\n"
        "«магниты ламинированные/виниловые» → magnet_vinyl.\n"
        "«магниты полимерные/эпоксидные/с заливкой» → magnet_polymer.\n"
        "«таблички» → tablets; «стенды» → stand; «хештеги» → hashtag; «шильды» → shild.\n"
        "«листовки/визитки/флаеры» → print_sheet.\n"
        "«широкоформат/баннер/постер» → print_wide.\n\n"

        "=== КОНТЕКСТ ДИАЛОГА ===\n"
        "Если в истории обсуждался расчёт и пользователь меняет параметр или просит пересчёт — "
        "intent=calculator, product_slug тот же, что был.\n"
        "Короткие реплики («да», «ок», «1», число) в контексте расчёта → intent=calculator.\n"
        "Короткие реплики без контекста → intent=knowledge (безопаснее).\n\n"

        f"=== ДОСТУПНЫЕ ПРОДУКТЫ ===\n{idx}\n\n"
        f"=== БАЗА ЗНАНИЙ ===\n{kb_description}"
    )


# ---------------------------------------------------------------------------
#  KB system prompt (без изменений)
# ---------------------------------------------------------------------------

def build_kb_system_prompt() -> str:
    """System prompt только для Wiki."""
    return (
        "Ты — ассистент рекламно-производственной компании Инсайн. "
        "Отвечаешь по внутренней базе знаний (Wiki) через инструмент search_knowledge.\n\n"
        "Правила:\n"
        "- Сформулируй запрос на русском и вызови search_knowledge.\n"
        "- Не выдумывай факты — только то, что вернул поиск.\n"
        "- Если вопрос про стоимость или расчёт заказа — ответь, что для сметы нужен "
        "отдельный запрос к калькулятору; ты отвечаешь только по базе знаний.\n"
        "- Формат ответа: plain text, без Markdown. Язык: русский."
    )


# ---------------------------------------------------------------------------
#  Calc system prompt (пошаговый алгоритм + product context)
# ---------------------------------------------------------------------------

def build_calc_system_prompt(
    slug: str,
    tool_name: str,
    calculator_description: str = "",
    calculator_prompt: str = "",
    recalc_append: str = "",
    product_title: str = "",
    product_defaults: Optional[Dict[str, Any]] = None,
    product_disambiguation: str = "",
) -> str:
    """
    System prompt для расчёта одним калькулятором.

    Пошаговый алгоритм вместо стены правил.
    Product context (title, defaults, disambiguation) подставляется из ProductSpec.
    """
    parts: List[str] = [
        "Ты — ассистент рекламно-производственной компании Инсайн.",
    ]

    if product_title:
        parts.append(f"Продукт: «{product_title}».")
        if product_disambiguation:
            parts.append(product_disambiguation)
    elif calculator_description:
        parts.append(f"Калькулятор: {calculator_description}")
    parts.append("")

    # Product defaults
    if product_defaults:
        defaults_lines = []
        for k, v in sorted(product_defaults.items()):
            defaults_lines.append(f"  {k} = {v}")
        parts.append(
            "=== DEFAULTS (подставляй если пользователь не указал; это внутренние коды — НЕ показывай пользователю) ===\n"
            + "\n".join(defaults_lines)
        )
        parts.append("")

    # Пошаговый алгоритм (текст адаптируется к наличию DEFAULTS)
    has_defaults = bool(product_defaults)
    step1_source = "из сообщения пользователя и DEFAULTS выше" if has_defaults else "из сообщения пользователя"
    step3_qualifier = " и нет в DEFAULTS" if has_defaults else ""
    parts.append(
        "=== ПОШАГОВЫЙ АЛГОРИТМ ===\n"
        f"ШАГ 1. Извлеки параметры {step1_source}.\n"
        f"ШАГ 2. Пользователь упомянул материал, бумагу, плотность, «гр», плёнку?\n"
        f"  - ДА → НЕМЕДЛЕННО вызови search_materials(slug=\"{slug}\", query=\"то что назвал пользователь\").\n"
        f"    Не отвечай текстом со списком материалов! Только tool call.\n"
        f"    search_materials вернул 1 вариант → подставь id и переходи к ШАГ 3.\n"
        f"    search_materials вернул несколько → выведи НУМЕРОВАННЫЙ СПИСОК (1. Title\\n2. Title), попроси выбрать номер.\n"
        f"  - НЕТ → переходи к ШАГ 3.\n"
        f"ШАГ 3. Проверь, все ли required-поля заполнены (из tool_schema {tool_name}).\n"
        f"  - Если ДА → НЕМЕДЛЕННО вызывай {tool_name}. НЕ спрашивай опциональные.\n"
        f"  - Если НЕТ → задай ОДИН уточняющий вопрос на человеко-понятном языке "
        f"(«укажите размер», «какая плотность бумаги»). НЕ показывай имена полей и коды.\n"
        f"ШАГ 4. Пересчёт: возьми ВСЕ параметры из предыдущего расчёта, замени "
        f"только то, что изменил пользователь, вызови {tool_name}.\n"
        f"  - Если пользователь меняет материал словами (плотность, название) → "
        f"ОБЯЗАТЕЛЬНО вызови search_materials(slug=\"{slug}\", query=\"...\"). "
        f"НИКОГДА не угадывай material_id.\n"
    )
    parts.append("")

    parts.append(
        "=== ЗАПРЕТЫ ===\n"
        "- Не придумывай цены, сроки, вес, названия материалов — только из калькулятора или search_materials.\n"
        "- НИКОГДА не показывай пользователю внутренние коды, имена полей и id "
        "(material_id, slug, enum-коды, PaperCoated250M, VHI80 и т.п.). "
        "Пользователь видит только человеко-понятные названия.\n"
        "- Не предлагай материалы «по памяти» — ВСЕГДА вызывай search_materials tool call.\n"
        "- ЗАПРЕЩЕНО отвечать текстом со списком материалов — только tool call search_materials.\n"
        "- Не спрашивай опциональные параметры, если пользователь их не упомянул.\n"
        "- Не задавай больше одного вопроса за раз.\n"
        "- Блоки с ценами в истории — старые ответы; для нового расчёта вызови tool.\n"
        "- mode: 0=эконом, 1=стандарт, 2=экспресс; по умолчанию 1."
    )
    parts.append("")

    if recalc_append.strip():
        parts.append(recalc_append.strip())
        parts.append("")

    parts.append("Формат ответа: plain text, без Markdown. Язык: русский.")

    if calculator_prompt:
        parts.append("")
        parts.append(f"=== АЛГОРИТМ РАСЧЁТА ({slug}) ===\n{calculator_prompt}")

    return "\n".join(parts)


# ---------------------------------------------------------------------------
#  Fallback (product не определён)
# ---------------------------------------------------------------------------

def build_calc_system_prompt_full(
    calculators: List[Dict[str, Any]],
    products: Optional[List[Dict[str, Any]]] = None,
) -> str:
    """
    Fallback: продукт не определён — категории для уточнения (~500 токенов).

    Если products переданы — используются категории продуктов.
    Иначе — старый формат из калькуляторов.
    """
    if products:
        cats = build_product_categories(products)
    else:
        cats = build_calculator_categories_short(calculators)

    return (
        "Ты — ассистент рекламно-производственной компании Инсайн. "
        "Помогаешь менеджеру рассчитать стоимость.\n\n"
        "=== СИТУАЦИЯ ===\n"
        "Тип продукции ещё не определён.\n"
        "Если пользователь спрашивает, что ты можешь посчитать / какие калькуляторы есть — "
        "перечисли категории из списка ниже с примерами продуктов.\n"
        "Если пользователь называет продукт — уточни детали кратким вопросом.\n\n"
        f"=== КАТЕГОРИИ ПРОДУКЦИИ ===\n{cats}\n\n"
        "=== ЗАПРЕТЫ ===\n"
        "- Не придумывай цены, себестоимость, сроки.\n"
        "- Не показывай внутренние коды.\n"
        "- Не вызывай калькулятор, пока не ясен тип продукта.\n\n"
        "Формат ответа: plain text, без Markdown. Язык: русский."
    )
