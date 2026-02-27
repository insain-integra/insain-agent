# Архитектура проекта

## Общая схема
Менеджер → Telegram Bot → Agent → LLM (Gemini / YandexGPT)
↓
Calc API (FastAPI)
↓
JSON справочники (data/)

Клиент → WordPress (ez Form Calculator)
↓
JS-обёртка (insain-calc-bridge.js)
↓
Calc API (FastAPI)

Программист → Cursor → git push → GitHub Actions → VPS

## Контейнеры на VPS
VPS (Ubuntu 22.04, 2GB RAM)
│
├── insain-calc-api (порт 8001)
│ FastAPI + загрузчики JSON + калькуляторы
│ Volume: ./calc_service/data:/app/data
│
├── insain-tg-bot
│ aiogram 3 + агент + Aider
│ depends_on: postgres, calc-api
│
├── insain-postgres (порт 5432)
│ PostgreSQL 16, БД: insain_agent_db
│ Volume: insain_postgres_data
│ healthcheck: pg_isready
│
├── insain-nginx (порты 80, 443)
│ SSL + reverse proxy
│ depends_on: calc-api
│
└── Cron:
├── Бэкап PostgreSQL — ежедневно в 3:00
└── Healthcheck — каждые 5 минут

## Потоки данных

### ЭТАП 1 (сейчас)
База знаний:
Yandex Wiki → парсер (каждые 6ч) → PostgreSQL (кэш статей)
Менеджер → Bot → [вся база целиком + вопрос] → Gemini → ответ

Расчёты:
Менеджер → Bot → Agent → HTTP POST calc-api → результат + share_url
Клиент → WordPress → JS-обёртка → HTTP POST calc-api → результат

Данные:
Запрос → FastAPI → loader.py → JSON из data/ → калькулятор → ответ

Логирование:
Все запросы → PostgreSQL (логи, история диалогов, аналитика)


### ЭТАП 2 (когда статей 200+)
Wiki → парсер → PostgreSQL (pgvector + эмбеддинги)
Менеджер → Bot → pgvector (5 релевантных кусков) → Gemini → ответ
Остальное не меняется.

## LLM
Основной: Google Gemini 2.5 Flash
Бесплатно, 500 req/day
Через openai SDK с совместимым base_url

Fallback: YandexGPT 4
Платный (~1500 ₽/мес)
Автопереключение после 3 ошибок Gemini
Cooldown 5 минут

Кодинг: Cursor ($20/мес) — редактор с ИИ
Aider (бесплатно + Gemini) — автогенерация калькуляторов

## PostgreSQL (insain_agent_db)
Таблицы:
conversations — история диалогов (user_id, role, content, timestamp)
calc_logs — логи расчётов (calculator, params, result, timestamp)
wiki_cache — кэш статей Wiki (slug, title, content, updated_at)

ЭТАП 2:
wiki_embeddings — pgvector для поиска по базе знаний
## API эндпоинты
POST /api/v1/calc/{slug} — расчёт калькулятора
GET /api/v1/options/{slug} — опции для форм на сайте
GET /api/v1/calculators — список всех калькуляторов
GET /api/v1/materials — справочник материалов
GET /api/v1/materials/{cat} — материалы по категории
GET /api/v1/equipment — справочник оборудования

## Ежемесячные расходы
VPS (2GB RAM) — 700 ₽
Google AI Studio — 0 ₽
PostgreSQL (self-hosted) — 0 ₽
GitHub — 0 ₽
Cursor — 1 800 ₽

ИТОГО (Gemini работает) — 2 500 ₽/мес
ИТОГО (fallback YandexGPT) — 4 000 ₽/мес