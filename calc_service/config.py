import os
from pathlib import Path

from dotenv import load_dotenv


# Корень проекта: два уровня выше текущего файла
PROJECT_ROOT = Path(__file__).resolve().parents[2]
ENV_PATH = PROJECT_ROOT / ".env"

# Загружаем переменные окружения из файла .env (если он существует)
load_dotenv(dotenv_path=ENV_PATH)

# Базовый URL сайта. По умолчанию — https://insain.ru
SITE_URL: str = os.getenv("SITE_URL", "https://insain.ru")

