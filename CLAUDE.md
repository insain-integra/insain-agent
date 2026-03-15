# CLAUDE.md — Инструкции для ИИ-агента

## Проект

ИИ-агент для рекламно-производственной компании Инсайн.
Консультирует сотрудников по базе знаний (Yandex Wiki),
рассчитывает стоимость продукции через калькуляторы.

Два сервиса: FastAPI калькуляторы и Telegram бот.
На сайте insain.ru — плагин ez Form Calculator,
JS-обёртка заменяет вызовы JS-калькуляторов на fetch к Python API.

Агент **одноступенчатый**: LLM видит все tools (search_materials + calc_*),
сама выбирает нужный калькулятор. Ранее был двухступенчатый (классификация + расчёт) — отменено.

Проект мигрирован с JavaScript на Python.
JSON-справочники материалов и оборудования — регулярно обновляются, структура материалов расширена (см. ниже).
Исходные JS-файлы лежат в js_legacy/ только для справки и сверки.

## Структура проекта
insain-agent/
│
├── calc_service/ ← СЕРВИС КАЛЬКУЛЯТОРОВ (FastAPI)
│ │
│ ├── main.py — точка входа, роуты API
│ ├── config.py — настройки (SITE_URL и т.д.)
│ ├── requirements.txt — зависимости (fastapi, pydantic, json5 и др.)
│ ├── Dockerfile          ← TODO
│ │
│ ├── data/ ← ДАННЫЕ (JSON, меняет администратор)
│ │ │
│ │ ├── common.json — наценки, курсы валют, сроки, праздники
│ │ │ (подробности: docs/common-json-reference.md)
│ │ │
│ │ ├── materials/ — справочники материалов (см. раздел «Структура data/materials» ниже)
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
│ │ ├── __init__.py
│ │ ├── base.py
│ │ ├── _template.py
│ │ ├── laser.py
│ │ ├── cut_plotter.py
│ │ ├── cut_guillotine.py  (is_public=False)
│ │ ├── cut_roller.py
│ │ ├── milling.py
│ │ ├── lamination.py
│ │ ├── print_sheet.py
│ │ ├── print_laser.py     (is_public=False)
│ │ └── ...                ← ~32 JS-калькулятора ещё не мигрированы
│ │
│ └── tests/
│ ├── test_common.py
│ ├── test_materials.py
│ ├── test_equipment.py
│ ├── test_api.py
│ └── test_calculators/
│
├── bot_service/ ← TELEGRAM БОТ
│ ├── bot.py              — aiogram 3, /start, /help, /clear
│ ├── agent.py            — одноступенчатый агент, function calling
│ ├── llm_provider.py     — Gemini / AITunnel / YandexGPT
│ ├── token_analyzer.py   — анализ расхода токенов
│ ├── analyze_tokens.py   — CLI-утилита для анализа логов
│ ├── check.py            — проверка LLM-подключения
│ ├── requirements.txt
│ ├── knowledge_base.py   ← TODO: Wiki → контекст
│ ├── wiki_parser.py      ← TODO: парсер Yandex Wiki API
│ ├── privacy.py          ← TODO: анонимизация ПДн
│ ├── models.py           ← TODO: SQLAlchemy модели
│ ├── database.py         ← TODO: подключение к PostgreSQL
│ ├── Dockerfile          ← TODO
│ └── tests/              ← TODO
│
├── wp-plugin/              ← TODO: JS-ОБЁРТКА ДЛЯ САЙТА
│ ├── insain-calc-bridge.php
│ ├── js/insain-calc-bridge.js
│ └── css/insain-calc-bridge.css
│
├── js_legacy/ ← ИСХОДНЫЙ JS (только для справки!)
│ ├── calc/ — JS-калькуляторы (не запускаются)
│ ├── equipment/ — JSON оборудования (оригиналы)
│ └── material/ — JSON материалов (оригиналы)
│
├── ai_agent/               ← TODO: АВТОМАТИЗАЦИЯ
│ ├── task_runner.py
│ └── prompts/
│
├── docs/ ← ПОДРОБНАЯ ДОКУМЕНТАЦИЯ
│ ├── architecture.md — архитектура, контейнеры, потоки
│ ├── data-formats.md — форматы JSON, маппинг JS → Python
│ ├── migration-guide.md — миграция калькуляторов, чек-листы
│ ├── wordpress-integration.md — сайт, ez Form Calculator
│ ├── common-json-reference.md — все поля common.json
│ ├── gemini-prompt-caching.md — кэширование контекста Gemini
│ └── project_summary.md — общий обзор проекта
│
├── infra/                  ← TODO: ИНФРАСТРУКТУРА
│ ├── docker-compose.yml
│ ├── nginx.conf
│ ├── deploy.sh
│ └── monitoring/healthcheck.py
│
├── scripts/                ← TODO (сейчас есть calc_service/scripts/)
│ ├── backup_db.sh
│ └── rollback.sh
│
├── wiki_export/ — fallback: ручной экспорт Wiki
├── alembic/                ← TODO: миграции PostgreSQL
├── .github/workflows/      ← TODO: CI/CD
├── Makefile                ← TODO
├── .env — секреты (НЕ в git)
└── .gitignore

## Структура data/materials/

**ВСЕ материалы в одной папке `data/materials/`:**

### Основные материалы:
- `hardsheet.json` — жёсткие листовые (ПВХ, акрил, фанера, поликарбонат)
- `sheet.json` — бумага и картон (листовая печать)
- `offset_promo.json` — готовые цены сборных офсетных тиражей (листовки А4/А5/А6, евро, визитки 1000 шт); только для будущего калькулятора calcPrintOffsetPromo (calcPrintOffset.js), пока нигде не используется
- `roll.json` — рулонные материалы (баннер, сетка, плёнки)
- `laminat.json` — плёнки для ламинации
- `calendar.json` — заготовки календарей
- `profile.json` — профили для рамок
- `magnet.json` — заготовки магнитов
- `keychain.json` — заготовки брелоков
- `mug.json` — заготовки кружек
- `presswall.json` — ткани для прессволлов
- `epoxy.json` — смолы и отвердители
- `attachment.json` — крепёж, фурнитура, скрепки, переплётные материалы
- `pack.json` — упаковка (зип-локи)
- `pocket.json` — карманы для стендов
- `flag.json` — древки для флагов и знамён
- `pins.json` — заготовки значков (металлические, закатные)
- `tape.json` — скотчи, клеевые ленты
- `plaque.json` — плакетки
- `puzzle.json` — пазлы
- `pennant.json` — вымпела, шнуры
- `misc.json` — прочее (остатки, новые категории)

Правила:
- **Новые материалы** добавлять в соответствующий файл.
- Если материал **не подходит ни под одну категорию** → временно в `misc.json`.
- При создании **новой категории** → создать новый файл в `data/materials/` и задокументировать его здесь.

### Структура одного материала

Каждый материал после миграции описывается в JSON так:

```json5
"PVC3": {
  "title": "ПВХ белый 3мм",                      // краткое название для UI (≤ 50 символов)
  "description": "ПВХ Unext Strong 3 мм",        // полное описание
  "cost": 750,
  "cost_date": "2025-03-24",                     // дата актуальности прайса (YYYY-MM-DD)
  "cost_source": "ТрастФМ",                      // источник прайса (Зенон, ТрастФМ и т.п.)
  "thickness": 3
}
```

Правила:
- Старое поле `name` больше не используется, при миграции оно перенесено в `description`.
- Поле `title` — краткое человеко-понятное название без лишних брендов и технических подробностей (ономастика для UI).  
  Примеры:
  - `"Акрил молочный Plexiglas XT 3мм"` → `"Акрил молочный 3мм"`,
  - `"Заготовка металлического значка на цанге круг 25мм"` → `"Значок металл круг 25мм"`.
- `title` ограничен ~50 символами, чтобы хорошо помещаться в выпадающие списки.
- `cost_date` и `cost_source` извлекаются из комментариев к `cost` при помощи миграционного скрипта
  `calc_service/scripts/migrate_materials_metadata.py` и хранятся явно.

В Python это соответствует `MaterialSpec` в `materials/base.py`:

- `title: str` — краткое название для UI,
- `description: str` — полное описание,
- `cost_date: str | None`,
- `cost_source: str | None`.

Для фронтенда `MaterialCatalog.list_for_frontend()` возвращает:

```python
{
  "code": m.code,
  "group": m.group,
  "name": m.title or m.description,   # краткое
  "title": m.title or m.description,  # дублирует name для совместимости
  "description": m.description,
  "thickness": m.thickness,
}
```

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

9. **Комментарии и ошибки — на русском.**
   Все комментарии в коде и сообщения об ошибках (`ValueError`, `KeyError` и т.п.)
   формулируются по-русски.

10. **share_url** добавляется автоматически в `execute()`.

11. **API контракт:**  
    - `POST /api/v1/calc/{slug}` — расчёт калькулятора,  
    - `GET /api/v1/options/{slug}` — опции для форм (материалы, режимы и т.п.),  
    - `GET /api/v1/calculators` — список калькуляторов (slug, name, description),  
    - `GET /api/v1/param_schema/{slug}` — детальная схема параметров калькулятора для агента/фронтенда,  
    - `GET /api/v1/tool_schema/{slug}` — компактная JSON‑схема для function calling (LLM),  
    - `POST /api/v1/choices` — поиск вариантов для параметров с choices (материалы, режимы и т.п.).

12. **Тесты обязательны** для каждого калькулятора, загрузчика, функции.

13. **Формы на сайте — ez Form Calculator** (существующий плагин).
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
    "materials": [...], # расход материалов (подробности ниже)
    "share_url": "...", # добавляется автоматически
}
```

### Формат поля materials

Все калькуляторы возвращают расход материалов в едином формате:

```python
"materials": [
    {
        "code": material.code,          # внутренний код (например, PVC3)
        "name": material.description,   # полное название (для логов, проверки)
        "title": material.title,        # краткое название для UI
        # дополнительные поля зависят от калькулятора:
        # - "quantity": ...,
        # - "unit": "sheet" | "m" | "m2" | "шт",
        # - "size_mm": [w, h], ...
    },
    ...
]
```

Правила:
- В ответах калькуляторов **всегда** должны быть поля `code`, `name`, `title`.
- UI и агент показывают пользователю только `title` и/или `description`, внутренний `code`
  используется для вызова калькуляторов и не должен попадать в ответы Telegram‑бота.

## Команды

> Makefile ещё не создан. Временные команды:

```Bash
pytest calc_service/tests/ -v          # тесты калькуляторов
cd bot_service && python bot.py        # запуск бота
```

### Команды (после создания Makefile) — TODO

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
docs/gemini-prompt-caching.md  — кэширование контекста Gemini
docs/project_summary.md        — общий обзор проекта (выжимка)
```