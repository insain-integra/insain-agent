"""
Telegram-бот Insain: ИИ-ассистент с расчётом стоимости через агента (LLM + function calling).
"""

from __future__ import annotations

import asyncio
import logging
import os
from pathlib import Path
from typing import Any, Dict, List, Set

from aiogram import Bot, Dispatcher, F, BaseMiddleware
from aiogram.enums import ChatAction
from aiogram.filters import Command
from aiogram.types import Message, TelegramObject

# Загрузка .env из корня проекта
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

from agent import InsainAgent

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
)
logger = logging.getLogger(__name__)

# Конфиг из .env
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN", "").strip()
CALC_API_URL = os.getenv("CALC_API_URL", "http://localhost:8001").strip().rstrip("/")
ALLOWED_USERS_RAW = os.getenv("ALLOWED_USERS", "").strip()
ALLOWED_USERS: Set[int] = set()
if ALLOWED_USERS_RAW:
    for part in ALLOWED_USERS_RAW.split(","):
        part = part.strip()
        if part.isdigit():
            ALLOWED_USERS.add(int(part))

# Агент создаётся при старте
agent = InsainAgent(calc_api_url=CALC_API_URL)

# История диалога по user_id (в памяти)
user_histories: Dict[int, List[Dict[str, Any]]] = {}

TELEGRAM_MAX_MESSAGE_LENGTH = 4096


def split_message(text: str, max_len: int = TELEGRAM_MAX_MESSAGE_LENGTH) -> List[str]:
    """Разбить длинное сообщение на части не больше max_len символов."""
    if len(text) <= max_len:
        return [text]
    parts = []
    while text:
        if len(text) <= max_len:
            parts.append(text)
            break
        chunk = text[:max_len]
        last_break = chunk.rfind("\n")
        if last_break > max_len // 2:
            chunk = chunk[: last_break + 1]
            text = text[last_break + 1 :]
        else:
            text = text[max_len:]
        parts.append(chunk)
    return parts


class AllowedUsersMiddleware(BaseMiddleware):
    """Если ALLOWED_USERS задан — пропускать только пользователей из списка, иначе игнорировать."""

    async def __call__(self, handler, event: TelegramObject, data: dict):
        if not ALLOWED_USERS:
            return await handler(event, data)
        user = getattr(event, "from_user", None)
        if user and user.id in ALLOWED_USERS:
            return await handler(event, data)
        if isinstance(event, Message):
            await event.answer("⛔ Доступ запрещён.")
        return


bot = Bot(token=TELEGRAM_TOKEN)
dp = Dispatcher()
dp.message.middleware(AllowedUsersMiddleware())


@dp.message(Command("start"))
async def cmd_start(message: Message):
    text = (
        "Привет! Я ИИ-ассистент компании Инсайн.\n"
        "Могу рассчитать стоимость продукции.\n\n"
        "Просто напишите что нужно, например:\n"
        "«Посчитай лазерную резку акрила 3мм, 50 штук, 40 на 80 мм»"
    )
    await message.answer(text)


@dp.message(Command("help"))
async def cmd_help(message: Message):
    text = (
        "📖 Как пользоваться:\n\n"
        "Напишите запрос своими словами — я подберу калькулятор и параметры.\n\n"
        "Примеры:\n"
        "• Посчитай лазерную резку акрила, 50 штук, 40×80 мм\n"
        "• Нужна плоттерная резка 100 шт, 60 на 60\n"
        "• Печать на листе, 200 шт, 100×150 мм\n\n"
        "Команды:\n"
        "• /clear — очистить историю диалога"
    )
    await message.answer(text)


@dp.message(Command("clear"))
async def cmd_clear(message: Message):
    user_id = message.from_user.id if message.from_user else 0
    user_histories[user_id] = []
    await message.answer("История диалога очищена.")


@dp.message(F.text)
async def handle_text(message: Message):
    text = (message.text or "").strip()
    if not text:
        return

    user_id = message.from_user.id if message.from_user else 0

    await bot.send_chat_action(chat_id=message.chat.id, action=ChatAction.TYPING)

    history = user_histories.get(user_id) or []

    try:
        loop = asyncio.get_event_loop()
        reply = await loop.run_in_executor(None, lambda: agent.chat(text, history=history))
    except Exception as e:
        logger.exception("agent.chat error: %s", e)
        await message.answer("Произошла ошибка, попробуйте ещё раз.")
        return

    if not reply:
        reply = "Произошла ошибка, попробуйте ещё раз."

    # Сохранить историю
    history = history + [
        {"role": "user", "content": text},
        {"role": "assistant", "content": reply},
    ]
    if len(history) > 20:
        history = history[-20:]
    user_histories[user_id] = history

    # Отправить ответ (разбить при необходимости)
    for part in split_message(reply):
        await message.answer(part)


async def main():
    if not TELEGRAM_TOKEN:
        raise SystemExit("Задайте TELEGRAM_TOKEN в .env")
    logger.info("CALC_API_URL=%s ALLOWED_USERS=%s", CALC_API_URL, ALLOWED_USERS or "all")
    await dp.start_polling(bot)


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
