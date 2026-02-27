# CLAUDE.md — Инструкции для ИИ-агента

## Проект

ИИ-агент для рекламно-производственной компании Инсайн.
Консультирует сотрудников по базе знаний (Yandex Wiki),
рассчитывает стоимость продукции через калькуляторы.

Два сервиса: FastAPI калькуляторы и Telegram бот.
На сайте insain.ru — плагин ez Form Calculator,
JS-обёртка заменяет вызовы JS-калькуляторов на fetch к Python API.

Проект мигрирован с JavaScript на Python.
JSON-справочники материалов и оборудования — без изменений.
Исходные JS-файлы лежат в js_legacy/ только для справки и сверки.

## Структура проекта
insain-agent/
│
├── calc_service/ ← СЕРВИС КАЛЬКУЛЯТОРОВ (FastAPI)
│ │
│ ├── main.py — точка входа, роуты API
│ ├── config.py — настройки (SITE_URL и т.д.)
│ ├── Dockerfile
│ ├── requirements.txt
│ │
│ ├── data/ ← ДАННЫЕ (JSON, меняет администратор)
│ │ │
│ │ ├── common.json — наценки, курсы валют, сроки, праздники
│ │ │ (подробности: docs/common-json-reference.md)
│ │ │
│ │ ├── materials/ — справочники материалов (11 файлов)
│ │ │ ├── hardsheet.json — ПВХ, акрил, фанера, поликарбонат
│ │ │ ├── roll.json — баннер, сетка, плёнки, холст
│ │ │ ├── sheet.json — бумага, картон
│ │ │ ├── laminat.json — плёнки для ламинации
│ │ │ ├── profile.json — профили для вывесок
│ │ │ ├── presswall.json — ткани для прессволлов
│ │ │ ├── calendar.json — заготовки календарей
│ │ │ ├── magnet.json — заготовки магнитов
│ │ │ ├── keychain.json — заготовки брелоков
│ │ │ ├── mug.json — заготовки кружек
│ │ │ └── misc.json — прочие расходники
│ │ │
│ │ └── equipment/ — справочники оборудования (11 файлов)
│ │ ├── printer.json — принтеры
│ │ ├── plotter.json — режущие плоттеры
│ │ ├── cutter.json — гильотины, резаки
│ │ ├── laminator.json — ламинаторы
│ │ ├── laser.json — лазеры
│ │ ├── milling.json — фрезеры
│ │ ├── heatpress.json — термопрессы
│ │ ├── cards.json — оборудование для визиток
│ │ ├── metalpins.json — оборудование для значков
│ │ ├── design.json — параметры дизайн-услуг
│ │ └── tools.json — инструменты обработки
│ │
│ ├── common/ ← ОБЩИЕ ФУНКЦИИ (Python)
│ │ ├── init.py
│ │ ├── markups.py — наценки, сроки, get_margin()
│ │ ├── currencies.py — курсы валют, parse_currency()
│ │ ├── holidays.py — праздники, is_working_day()
│ │ ├── helpers.py — find_in_table(), calc_weight()
│ │ └── layout.py — layout_on_sheet(), layout_on_roll()
│ │
│ ├── materials/ ← СПРАВОЧНИКИ МАТЕРИАЛОВ (Python)
│ │ ├── init.py — реестр: ALL_MATERIALS, get_material()
│ │ ├── base.py — MaterialSpec (Pydantic), MaterialCatalog
│ │ └── loader.py — JSON → Python объекты
│ │
│ ├── equipment/ ← СПРАВОЧНИКИ ОБОРУДОВАНИЯ (Python)
│ │ ├── init.py — реестр: ALL_EQUIPMENT
│ │ ├── base.py — EquipmentSpec, LaserSpec, LookupTable
│ │ └── loader.py — JSON → Python объекты
│ │
│ ├── calculators/ ← КАЛЬКУЛЯТОРЫ (мигрированы из JS)
│ │ ├── init.py — реестр: CALCULATORS = {"laser": ..., ...}
│ │ ├── base.py — BaseCalculator, ProductionMode
│ │ ├── _template.py — шаблон для новых калькуляторов
│ │ ├── laser.py — лазерная резка/гравировка
│ │ ├── print_wide.py — широкоформатная печать
│ │ └── ... — остальные (~35 файлов)
│ │
│ └── tests/
│ ├── test_common.py
│ ├── test_materials.py
│ ├── test_equipment.py
│ ├── test_api.py
│ └── test_calculators/
│
├── bot_service/ ← TELEGRAM БОТ
│ ├── bot.py — aiogram 3, команды, хэндлеры
│ ├── agent.py — ядро агента, function calling
│ ├── llm_provider.py — Gemini + YandexGPT fallback
│ ├── knowledge_base.py — Wiki → контекст для LLM
│ ├── wiki_parser.py — парсер Yandex Wiki API
│ ├── privacy.py — анонимизация ПДн
│ ├── models.py — SQLAlchemy модели
│ ├── database.py — подключение к PostgreSQL
│ ├── Dockerfile
│ ├── requirements.txt
│ └── tests/
│
├── wp-plugin/ ← JS-ОБЁРТКА ДЛЯ САЙТА
│ ├── insain-calc-bridge.php — мини-плагин WordPress
│ ├── js/insain-calc-bridge.js — fetch к API + URL параметры
│ └── css/insain-calc-bridge.css
│
├── js_legacy/ ← ИСХОДНЫЙ JS (только для справки!)
│ ├── calc/ — JS-калькуляторы (не запускаются)
│ ├── equipment/ — JSON оборудования (оригиналы)
│ └── material/ — JSON материалов (оригиналы)
│
├── ai_agent/ ← АВТОМАТИЗАЦИЯ
│ ├── task_runner.py
│ └── prompts/
│
├── docs/ ← ПОДРОБНАЯ ДОКУМЕНТАЦИЯ
│ ├── architecture.md — архитектура, контейнеры, потоки
│ ├── data-formats.md — форматы JSON, маппинг JS → Python
│ ├── migration-guide.md — миграция калькуляторов, чек-листы
│ ├── wordpress-integration.md — сайт, ez Form Calculator
│ └── common-json-reference.md — все поля common.json
│
├── infra/ ← ИНФРАСТРУКТУРА
│ ├── docker-compose.yml
│ ├── nginx.conf
│ ├── deploy.sh
│ └── monitoring/healthcheck.py
│
├── scripts/
│ ├── backup_db.sh
│ └── rollback.sh
│
├── wiki_export/ — fallback: ручной экспорт Wiki
├── alembic/ — миграции PostgreSQL
├── .github/workflows/ — CI/CD
├── Makefile
├── .env — секреты (НЕ в git)
└── .gitignore

## Разделение данных и кода

data/*.json = ДАННЫЕ — цены, размеры, наценки, курсы валют
Меняет администратор без знания Python.

common/ = КОД — как загружать данные из JSON
materials/ = КОД — как работать с материалами
equipment/ = КОД — как работать с оборудованием
calculators/ = КОД — как считать стоимость

js_legacy/ = СПРАВКА — оригинальные JS, для сверки при миграции

Калькулятор никогда не хардкодит цены, наценки, курсы валют.
Всё загружается из JSON через loader.
JSON содержат комментарии (`// ...`) — читаются через json5.

## Правила

1. **Данные из JSON, не из кода.**
   Цены, наценки, курсы валют, сроки — всё в `data/common.json`
   и `data/materials/*.json`, `data/equipment/*.json`.

2. **У каждого калькулятора своя наценка.**
   `get_margin("marginLaser")` прибавляется к `MARGIN_OPERATION`.
   Результат не ниже `MARGIN_MIN` (0.25).
   Наценка может быть отрицательной (скидка).
   Полный список: `docs/common-json-reference.md`.

3. **Время — обязательное поле ответа.**
   В JS время считалось, но не возвращалось пользователю.
   В Python `time_hours` и `time_ready` — обязательны.
   `baseTimeReady = [24, 8, 1]` часов (экономичный, стандартный, экспресс).

4. **Курсы валют из common.json.**
   `"USD": 95`, `"EUR": 100`. Не захардкожены в Python.
   `"$11600"` в JSON → `parse_currency()` → рубли.

5. **Default разворачивается при загрузке.**
   MaterialSpec содержит все поля. Нет наследования в рантайме.

6. **Таблицы [порог, значение] → LookupTable.find().**

7. **Формулы из JSON → @property в Python.**

8. **Размеры в мм** на входе. Валидация через Pydantic.

9. **share_url** добавляется автоматически в `execute()`.

10. **API контракт:** `POST /api/v1/calc/{slug}`, `GET /api/v1/options/{slug}`.

11. **Тесты обязательны** для каждого калькулятора, загрузчика, функции.

12. **Формы на сайте — ez Form Calculator** (существующий плагин).
    JS-обёртка заменяет вызовы JS на fetch к API.
    URL обновляется GET-параметрами для share-ссылок.

## Обязательные поля ответа калькулятора

```python
{
    "cost": ...,        # себестоимость тиража, руб.
    "price": ...,       # цена с наценкой, руб.
    "unit_price": ...,  # цена за штуку, руб.
    "time_hours": ...,  # время производства, часов
    "time_ready": ...,  # время готовности, рабочих часов
    "weight_kg": ...,   # вес тиража, кг
    "materials": [...], # расход материалов
    "share_url": "...", # добавляется автоматически
}
```

Команды
```Bash
make test          # все тесты
make test-calc     # калькуляторы и справочники
make test-bot      # бот
make lint          # ruff check
make format        # ruff format
make up            # docker compose up
make restart       # перезапуск контейнеров
make logs          # логи всех контейнеров
make backup        # бэкап PostgreSQL
```

## Что менять при типичных задачах

**Добавить калькулятор:**

```
1. calculators/новый.py         ← копия _template.py
2. tests/test_calculators/      ← тесты
3. calculators/__init__.py      ← добавить в CALCULATORS
Подробности: docs/migration-guide.md
```

**Обновить цены:**

```
data/materials/категория.json → изменить "cost"
make test → make restart
```

**Обновить курс валюты / наценки / сроки:**

```
data/common.json → изменить нужное поле
make test → make restart
```

**Добавить материал:**

```
data/materials/категория.json → новый блок в группу
Если новый файл — добавить в materials/__init__.py
make test
```

**Мигрировать JS-калькулятор:**

```
docs/migration-guide.md — пошаговый процесс и чек-листы
```

## Образцы кода

```
Шаблон калькулятора:      calculators/_template.py
Эталонный калькулятор:    calculators/laser.py
Базовый класс материала:  materials/base.py
Загрузчик материалов:     materials/loader.py
Базовый класс оборуд.:   equipment/base.py
Наценки и сроки:          common/markups.py
Конвертация валют:        common/currencies.py
```

## Подробная документация

```
docs/architecture.md           — архитектура, контейнеры, потоки данных
docs/data-formats.md           — форматы JSON, маппинг JS → Python
docs/migration-guide.md        — миграция калькуляторов, чек-листы
docs/wordpress-integration.md  — сайт, ez Form Calculator, share URL
docs/common-json-reference.md  — все поля common.json с описанием
```