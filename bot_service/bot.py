"""
Минимальный Telegram-бот для прототипа калькуляторов Insain.

Команды: /start, /calc, /help.
Текстовые сообщения парсятся простым парсером (без LLM): тип калькулятора,
тираж, размер, материал → запрос к API калькуляторов.
"""

from __future__ import annotations

import logging
import os
import re
from typing import Any, Dict, List, Optional, Set, Tuple

import httpx
from aiogram import Bot, Dispatcher, F, BaseMiddleware
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import Command
from aiogram.types import Message, TelegramObject
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
)
logger = logging.getLogger(__name__)

# --- Конфиг из .env ---
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN", "").strip()
CALC_API_URL = os.getenv("CALC_API_URL", "http://localhost:8001").rstrip("/")
ALLOWED_USERS_RAW = os.getenv("ALLOWED_USERS", "").strip()
ALLOWED_USERS: Set[int] = set()
if ALLOWED_USERS_RAW:
    for part in ALLOWED_USERS_RAW.split(","):
        part = part.strip()
        if part.isdigit():
            ALLOWED_USERS.add(int(part))

# Ключевые слова → slug калькулятора (первое совпадение в тексте)
SLUG_KEYWORDS: List[Tuple[List[str], str]] = [
    (["лазер", "лазерная резка", "лазерная гравировка"], "laser"),
    (["плоттер", "плоттерная резка", "резка плоттер"], "cut_plotter"),
    (["гильотина", "гильотинная резка"], "cut_guillotine"),
    (["рулонная резка", "роликовый резак"], "cut_roller"),
    (["фрезер", "фрезеровка"], "milling"),
    (["ламинация", "ламинация"], "lamination"),
    (["печать лист", "печать на листе", "печать листовая"], "print_sheet"),
    (["печать лазер", "лазерная печать"], "print_laser"),
]
# Короткие алиасы для быстрого ввода
SLUG_ALIASES: Dict[str, str] = {
    "лазер": "laser",
    "резка": "cut_plotter",
    "печать": "print_sheet",
    "ламин": "lamination",
    "фрезер": "milling",
    "гильотина": "cut_guillotine",
    "рулон": "cut_roller",
}


def detect_slug(text: str) -> Optional[str]:
    """Определить slug калькулятора по ключевым словам в тексте."""
    t = text.lower().strip()
    for keywords, slug in SLUG_KEYWORDS:
        for kw in keywords:
            if kw in t:
                return slug
    for alias, slug in SLUG_ALIASES.items():
        if alias in t:
            return slug
    return None


def parse_quantity(text: str) -> Optional[int]:
    """Извлечь тираж — первое целое число от 1 до 100000."""
    for m in re.finditer(r"\b(1\d{0,4}|[2-9]\d{0,4}|[1-9])\b", text):
        n = int(m.group(1))
        if 1 <= n <= 100_000:
            return n
    return None


def parse_size(text: str) -> Optional[Tuple[float, float]]:
    """Извлечь размер в мм: 40x80, 40×80, 40*80, 100 150."""
    # Разделитель x, ×, *
    m = re.search(r"(\d+(?:[.,]\d+)?)\s*[x×*]\s*(\d+(?:[.,]\d+)?)", text, re.IGNORECASE)
    if m:
        return (float(m.group(1).replace(",", ".")), float(m.group(2).replace(",", ".")))
    # Два числа подряд
    nums = re.findall(r"\d+(?:[.,]\d+)?", text)
    if len(nums) >= 2:
        return (float(nums[0].replace(",", ".")), float(nums[1].replace(",", ".")))
    return None


def find_material_id(materials: List[Dict[str, Any]], query: str) -> Optional[str]:
    """Найти code материала по подстроке в названии (name)."""
    if not materials or not query or not query.strip():
        return None
    q = query.strip().lower()
    for m in materials:
        name = (m.get("name") or "").lower()
        code = m.get("code")
        if code and q in name:
            return str(code)
    return None


async def fetch_calculators() -> List[Dict[str, str]]:
    """Список калькуляторов с API."""
    async with httpx.AsyncClient(timeout=10.0) as client:
        r = await client.get(f"{CALC_API_URL}/api/v1/calculators")
        r.raise_for_status()
        return r.json()


async def fetch_options(slug: str) -> Dict[str, Any]:
    """Опции калькулятора (материалы и т.д.)."""
    async with httpx.AsyncClient(timeout=10.0) as client:
        r = await client.get(f"{CALC_API_URL}/api/v1/options/{slug}")
        r.raise_for_status()
        return r.json()


async def call_calc(slug: str, body: Dict[str, Any]) -> Dict[str, Any]:
    """POST /api/v1/calc/{slug}."""
    async with httpx.AsyncClient(timeout=15.0) as client:
        r = await client.post(f"{CALC_API_URL}/api/v1/calc/{slug}", json=body)
        r.raise_for_status()
        return r.json()


def parse_message(text: str) -> Optional[Dict[str, Any]]:
    """
    Простой парсер: slug, quantity, size, material.
    Возвращает None если не удалось распарсить минимум (slug + quantity + size).
    """
    slug = detect_slug(text)
    if not slug:
        return None
    quantity = parse_quantity(text)
    size = parse_size(text)
    if quantity is None or size is None:
        return None
    width, height = size
    if width <= 0 or height <= 0:
        return None
    return {
        "slug": slug,
        "quantity": quantity,
        "width": round(width, 2),
        "height": round(height, 2),
        "text": text,
    }


def build_calc_body(parsed: Dict[str, Any], material_id: Optional[str], calc_name: str) -> Dict[str, Any]:
    """Собрать body для POST /calc/{slug} по умолчаниям калькулятора."""
    slug = parsed["slug"]
    body: Dict[str, Any] = {
        "quantity": parsed["quantity"],
        "width": parsed["width"],
        "height": parsed["height"],
        "mode": 1,
    }
    if material_id:
        body["material_id"] = material_id
    if slug == "laser":
        body.setdefault("material_id", material_id or "AcrylColor3")
        body.setdefault("is_cut_laser", {})
        body.setdefault("is_grave", 1)
        body.setdefault("is_grave_fill", [parsed["width"], parsed["height"]])
    elif slug == "cut_guillotine":
        body["num_sheet"] = max(1, (parsed["quantity"] + 99) // 100)
        body["sheet_width"] = 450
        body["sheet_height"] = 320
        if material_id:
            body["material_id"] = material_id
    elif slug == "print_laser":
        body["num_sheet"] = parsed["quantity"]
        body["color"] = "4+0"
        if material_id:
            body["material_id"] = material_id
    return body


def format_result(slug: str, calc_name: str, parsed: Dict[str, Any], result: Dict[str, Any]) -> str:
    """Форматирование ответа расчёта."""
    price = result.get("price") or 0
    unit = result.get("unit_price") or 0
    time_h = result.get("time_hours") or 0
    time_ready = result.get("time_ready") or 0
    weight = result.get("weight_kg") or 0
    share_url = result.get("share_url") or ""

    material_label = "—"
    if parsed.get("material_name"):
        material_label = parsed["material_name"]

    lines = [
        f"📋 {calc_name}",
        "",
        f"📦 Тираж: {parsed['quantity']} шт",
        f"📐 Размер: {parsed['width']}×{parsed['height']} мм",
        f"🧱 Материал: {material_label}",
        "",
        f"💰 Цена: {price:,.0f} ₽ ({unit:,.2f} ₽/шт)".replace(",", " "),
        f"⏱ Время: {time_h} ч",
        f"📅 Готовность: {time_ready} раб. часов",
        f"⚖️ Вес: {weight} кг",
    ]
    if share_url:
        lines.append("")
        lines.append("🔗 Ссылка для клиента:")
        lines.append(share_url)
    return "\n".join(lines)


def format_calculator_list(calcs: List[Dict[str, str]]) -> str:
    """Список калькуляторов для сообщения."""
    lines = ["📌 Доступные калькуляторы:", ""]
    for c in calcs:
        lines.append(f"• {c.get('name', c.get('slug', ''))}")
    lines.append("")
    lines.append("Напишите, например: лазер 50 акрил 40x80")
    return "\n".join(lines)


# --- Middleware авторизации ---
class AllowedUsersMiddleware(BaseMiddleware):
    """Проверка user_id по ALLOWED_USERS (пустой = все разрешены)."""

    async def __call__(self, handler, event: TelegramObject, data: dict):
        if not ALLOWED_USERS:
            return await handler(event, data)
        user = getattr(event, "from_user", None)
        if user and user.id in ALLOWED_USERS:
            return await handler(event, data)
        if isinstance(event, Message):
            await event.answer("⛔ Доступ запрещён.")
        return


# --- Бот ---
bot = Bot(token=TELEGRAM_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher()
dp.message.middleware(AllowedUsersMiddleware())


@dp.message(Command("start"))
async def cmd_start(message: Message):
    try:
        calcs = await fetch_calculators()
        text = "👋 Привет! Я бот расчёта стоимости продукции Insain.\n\n"
        text += "Команды:\n• /calc — список калькуляторов\n• /help — справка по формату запроса\n\n"
        text += format_calculator_list(calcs)
    except Exception as e:
        logger.exception("fetch calculators: %s", e)
        text = "Сервис расчётов временно недоступен."
    await message.answer(text)


@dp.message(Command("calc"))
async def cmd_calc(message: Message):
    try:
        calcs = await fetch_calculators()
        text = format_calculator_list(calcs)
    except Exception as e:
        logger.exception("fetch calculators: %s", e)
        text = "Сервис расчётов временно недоступен."
    await message.answer(text)


@dp.message(Command("help"))
async def cmd_help(message: Message):
    text = (
        "📖 Формат запроса (без LLM, простой парсер):\n\n"
        "Напишите одной строкой, например:\n"
        "• <b>лазер 50 акрил 40x80</b> — лазерная резка, 50 шт, акрил, 40×80 мм\n"
        "• <b>резка 100 60x60</b> — плоттерная резка, 100 шт, 60×60 мм\n"
        "• <b>печать 200 100 150</b> — печать на листе, 200 шт, 100×150 мм\n\n"
        "Бот ищет: тип калькулятора (лазер, резка, печать…), тираж, размер (NxM или два числа), материал по названию из опций.\n"
        "Если не удалось распарсить — попробуйте явно указать размер через x или ×."
    )
    await message.answer(text)


@dp.message(F.text)
async def handle_text(message: Message):
    text = (message.text or "").strip()
    if not text:
        return

    parsed = parse_message(text)
    if not parsed:
        await message.answer(
            "Не удалось разобрать запрос. Укажите тип (лазер, резка, печать…), тираж и размер, например:\n"
            "лазер 50 акрил 40x80"
        )
        return

    slug = parsed["slug"]
    try:
        calcs = await fetch_calculators()
        calc_info = next((c for c in calcs if c.get("slug") == slug), {})
        calc_name = calc_info.get("name", slug)
    except Exception as e:
        logger.exception("fetch calculators: %s", e)
        await message.answer("Сервис расчётов временно недоступен.")
        return

    options: Dict[str, Any] = {}
    try:
        options = await fetch_options(slug)
    except Exception as e:
        logger.warning("fetch options %s: %s", slug, e)

    materials = options.get("materials") or []
    material_id = find_material_id(materials, text)
    material_name = None
    if material_id and materials:
        for m in materials:
            if str(m.get("code")) == str(material_id):
                material_name = m.get("name")
                break
    parsed["material_name"] = material_name or (material_id or "—")

    body = build_calc_body(parsed, material_id, calc_name)

    try:
        result = await call_calc(slug, body)
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 400:
            detail = (e.response.json() or {}).get("detail", str(e))
            await message.answer(f"Ошибка расчёта: {detail}")
        else:
            await message.answer("Сервис расчётов вернул ошибку. Попробуйте позже.")
        return
    except (httpx.ConnectError, httpx.TimeoutException) as e:
        logger.warning("API unreachable: %s", e)
        await message.answer("Сервис расчётов временно недоступен.")
        return
    except Exception as e:
        logger.exception("call_calc: %s", e)
        await message.answer("Произошла ошибка. Попробуйте позже.")
        return

    reply = format_result(slug, calc_name, parsed, result)
    await message.answer(reply)


async def main():
    if not TELEGRAM_TOKEN:
        raise SystemExit("Задайте TELEGRAM_TOKEN в .env")
    logger.info("CALC_API_URL=%s ALLOWED_USERS=%s", CALC_API_URL, ALLOWED_USERS or "all")
    await dp.start_polling(bot)


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
