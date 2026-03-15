# Insain Agent — обзор проекта

## 1. Назначение проекта

- ИИ-ассистент для рекламно‑производственной компании «Инсайн».
- Основные задачи:
  - Консультировать менеджеров по базе знаний (Yandex Wiki).
  - Считать стоимость продукции через калькуляторы (Python, FastAPI).
  - Интеграция с сайтом через WordPress + ez Form Calculator.
  - Telegram‑бот для оперативных расчётов и консультаций.

## 2. Структура репозитория (верхний уровень)

- `calc_service/` — сервис калькуляторов (FastAPI).
- `bot_service/` — Telegram‑бот и LLM‑агент.
- `docs/` — документация (архитектура, форматы данных, миграции).
- `wp-plugin/` — интеграция с WordPress (JS‑обёртка).
- `js_legacy/` — исходные JS‑калькуляторы и JSON (только как референс).
- `infra/` — docker‑compose, nginx, healthcheck.
- `ai_agent/` — автоматизация/таск‑раннер.
- `wiki_export/` — ручной экспорт Wiki.
- `alembic/` — миграции БД.
- `.env` — конфиг (секреты, URLы, режим LLM и т.д.).

## 3. calc_service/ — сервис калькуляторов

### 3.1. Основные файлы

- `main.py` — FastAPI‑приложение, определяет все HTTP‑эндпоинты:
  - `POST /api/v1/calc/{slug}` — расчёт калькулятора.
  - `GET /api/v1/options/{slug}` — опции для форм (материалы, режимы).
  - `GET /api/v1/calculators` — список калькуляторов (slug, name, description).
  - `GET /api/v1/param_schema/{slug}` — детальная схема параметров калькулятора.
  - `GET /api/v1/tool_schema/{slug}` — компактная схема для function calling (LLM).
  - `POST /api/v1/choices` — поиск вариантов для параметров с choices (материалы и др.).
- `requirements.txt` — зависимости кальк‑сервиса.

### 3.2. Данные (`calc_service/data/`)

- `common.json` — глобальные настройки:
  - наценки (`margin*`), базовые наценки (`marginMaterial`, `marginOperation`, `marginMin`),
  - базовые сроки готовности (`baseTimeReady`, `baseTimeReadyPrintSheet`, ...),
  - курсы валют `USD`, `EUR`,
  - календарь праздников/выходных.
- `materials/` — **все материалы в одной папке**:
  - `hardsheet.json`, `sheet.json`, `roll.json`, `laminat.json`,
  - `calendar.json`, `profile.json`, `magnet.json`, `keychain.json`, `mug.json`, `presswall.json`,
  - `epoxy.json`, `attachment.json`, `pack.json`, `pocket.json`, `flag.json`,
  - `pins.json`, `tape.json`, `plaque.json`, `puzzle.json`, `pennant.json`, `misc.json`.
- `equipment/` — справочники оборудования:
  - `printer.json`, `plotter.json`, `cutter.json`, `laminator.json`, `laser.json`, `milling.json`,
  - `heatpress.json`, `cards.json`, `metalpins.json`, `design.json`, `tools.json`.

### 3.3. Общие модули (`calc_service/common/`)

- `markups.py`:
  - константы: `MARGIN_MATERIAL`, `MARGIN_OPERATION`, `MARGIN_MIN`, `BASE_TIME_READY`,
  - функции: `get_margin(name)`, `get_time_ready(key)`.
- `currencies.py`:
  - `USD_RATE`, `EUR_RATE`,
  - `parse_currency("$11600") → рубли`.
- `holidays.py`:
  - `is_working_day(date)`, `add_working_hours(start, hours)`.
- `helpers.py`:
  - `find_in_table()`, `calc_weight()` (учёт плотности, толщины, единиц измерения).
- `layout.py`:
  - `layout_on_sheet(size_item, size_sheet, margins, interval)`,
  - `layout_on_roll(quantity, size, roll_size, interval)`.

### 3.4. Материалы (`calc_service/materials/`)

- `base.py`:
  - `MaterialSpec` (Pydantic) — единый формат материала:
    - ключевые поля:
      - `code: str`, `group: str`, `category: str`,
      - `title: str` — краткое имя для UI (≤ 50 символов),
      - `description: str` — полное описание,
      - `cost: float | None`, `cost_tiers: list[tuple[float, float]] | None`,
      - `cost_date: str | None` (ISO `YYYY-MM-DD`),
      - `cost_source: str | None` (источник прайса),
      - `sizes`, `min_size`, `is_roll`, `thickness`, `density`, `density_unit`, `length_min`, `weight_per_unit`, `available`.
    - свойство `name` для обратной совместимости возвращает `description`.
  - `MaterialCatalog`:
    - хранит все `MaterialSpec` одной категории,
    - методы: `add`, `get`, `get_group`, `list_all`, `list_for_frontend()`, `filter_by_thickness()`.
    - `list_for_frontend()` отдаёт:
      - `code`, `group`, `name` (краткое), `title`, `description`, `thickness` — используется в UI и агенте.
- `loader.py` — загрузка файлов `data/materials/*.json`:
  - читает JSON5 (поддержка `//`‑комментариев),
  - для каждой группы: применяет `Default` к вариантам,
  - мигрирует старый формат (`name`) в новый (`description` + `title`),
  - при необходимости извлекает `cost_date` и `cost_source` (поддержка миграционного скрипта).
- `__init__.py`:
  - загружает все каталоги в `ALL_MATERIALS: dict[str, MaterialCatalog]`,
  - функции:
    - `get_material(category: str, code: str) -> MaterialSpec`,
    - `get_all_options() -> dict[str, list[dict]]` (списки материалов для фронта).

### 3.5. Оборудование (`calc_service/equipment/`)

- `base.py` — описания оборудования (принтеры, плоттеры, лазеры и т.д.) с:
  - справочными таблицами скоростей, брака, стоимости,
  - методами `get_sheets_per_hour`, `get_defect_rate`, `get_meter_per_hour`, `get_time_ready` и др.
- `loader.py`, `__init__.py` — загрузка всех JSON‑файлов и реестр `ALL_EQUIPMENT`.

### 3.6. Калькуляторы (`calc_service/calculators/`)

- `base.py`:
  - `ProductionMode` — режимы (ECONOMY/0, STANDARD/1, EXPRESS/2).
  - `BaseCalculator`:
    - атрибуты `slug`, `name`, `description`.
    - методы:
      - `get_options()` — опции для форм (материалы, режимы и т.п.).
      - `get_tool_schema()` — компактная schema для LLM tools.
      - `get_param_schema()` — **новая** детальная схема параметров (по умолчанию пустая, реализуется по мере надобности в конкретных калькуляторах).
      - `get_required_params()`, `get_default_values()` — вспомогательные методы для работы с `param_schema`.
      - `calculate(params)` — чистый расчёт.
      - `execute(params)` — обёртка над `calculate` + добавление `share_url`.
- Реализованные калькуляторы (примеры):
  - Лазер:
    - `laser.py` (`LaserCalculator`, slug `"laser"`):
      - `get_param_schema()` реализован: параметры `quantity`, `width_mm`, `height_mm`, `material` (`enum_cascading` из `materials:hardsheet`), `cut_length_m`, `grave_area_m2`, `mode`.
      - `materials` в результате содержат `code`, `name`, `title`, `size_mm`, `quantity`, `unit`.
  - Листовая печать:
    - `print_sheet.py` (`PrintSheetCalculator`, slug `"print_sheet"`):
      - учитывает раскладку на листе, дефекты печати, опциональную ламинацию и гильотинную резку,
      - вес `weight_kg` считается по количеству готовых изделий + вес ламинации,
      - `time_hours` и `time_ready` приведены к логике JS‑калькулятора (`Math.ceil` и учёт `baseTimeReadyPrintSheet`).
      - `get_param_schema()` описывает параметры `quantity`, `width_mm`, `height_mm`, `material` (`materials:sheet`), `color`, `lamination` (`materials:laminat`), `lamination_double_side`, `mode`.
  - Лазерная печать по листам:
    - `print_laser.py` (`PrintLaserCalculator`, slug `"print_laser"`).
  - Ламинация:
    - `lamination.py` (`LaminationCalculator`, slug `"lamination"`).
  - Резка:
    - `cut_plotter.py` (`CutPlotterCalculator`, slug `"cut_plotter"`, материалы `materials:roll`).
    - `cut_guillotine.py` (`CutGuillotineCalculator`, slug `"cut_guillotine"`, материалы `materials:sheet` + размеры листа/изделия).
    - `cut_roller.py` (`CutRollerCalculator`, slug `"cut_roller"`, материалы `materials:sheet`).
  - Много других калькуляторов (см. `docs/data-formats.md` и комментарии в `calculators/_template.py`).

### 3.7. Обязательные поля ответа калькулятора

Все калькуляторы возвращают структуру:

```python
{
  "cost": ...,        # себестоимость тиража, руб.
  "price": ...,       # цена с наценкой, руб.
  "unit_price": ...,  # цена за штуку, руб.
  "time_hours": ...,  # время производства, часов
  "time_ready": ...,  # время готовности, рабочих часов
  "weight_kg": ...,   # вес тиража, кг
  "materials": [...], # расход материалов (единый формат)
  "share_url": "...", # добавляется автоматически в execute()
}
```

`materials` всегда содержит объекты:

```python
{
  "code": material.code,          # внутренний код (например, "PVC3")
  "name": material.description,   # полное название из каталога
  "title": material.title,        # краткое название для UI
  # + дополнительные поля: quantity, unit, size_mm, ...
}
```

## 4. bot_service/ — Telegram‑бот и агент

### 4.1. Telegram‑бот (`bot.py`)

- Использует aiogram 3.
- Команды:
  - `/start`, `/help`, `/clear`.
- Для каждого текстового сообщения:
  - показывает статус `typing`,
  - вызывает `await agent.process_message(user_id, text)`,
  - отправляет ответ (с разбиением длинных сообщений по 4096 символов).

### 4.2. Агент (`agent.py`, класс `InsainAgent`)

- При инициализации:
  - грузит конфиг `.env` (в т.ч. `CALC_API_URL`, `LLM_MODE` и ключи LLM),
  - создаёт `LLMProvider`,
  - загружает список калькуляторов и их схемы через `_load_calculators_and_tools()`:
    - `GET /api/v1/calculators`,
    - для каждого `slug`:
      - `GET /api/v1/param_schema/{slug}` → `_param_schemas[slug]`,
      - `GET /api/v1/options/{slug}` → `_options_by_slug[slug]`, `calculator_materials[slug]`,
      - `GET /api/v1/tool_schema/{slug}` → `_tools_by_slug[slug]`.
  - строит `self._tools` — список tools для LLM (OpenAI function calling), с `enum` для `material_id`.
  - строит системный промпт `_system_prompt` через `_build_system_prompt()`:
    - включает список калькуляторов, краткие описания, списки материалов (код + человеко‑понятное название + толщина),
    - содержит правила выбора материалов и запрета на показ внутренних кодов менеджеру.

- Важные методы:
  - `get_system_prompt()` — возвращает текущий системный промпт.
  - `get_tools()` — список tools для LLM.
  - `execute_tool(name, arguments)` — обёртка над `POST /api/v1/calc/{slug}`.
  - `chat(user_message, history)` — старый «сырый» режим с function calling (не используется ботом после внедрения `process_message`).
  - `async _search_choices(slug, param, query)` — запрос к `/api/v1/choices` для поиска материалов/choices (максимум 5 вариантов, логирование).
  - `async process_message(user_id, text)` — новый двухэтапный режим диалога:
    1. **Классификация**:
       - вызывает `_classify_intent(text)` (LLM без tools) для определения:
         - intent: `"calculation"` или что‑то иное,
         - slug калькулятора (например, `"laser"`).
       - если intent ≠ `"calculation"` — уходит в `_simple_chat(text)` (обычный чат).
    2. **Сбор параметров**:
       - достаёт `param_schema = _param_schemas[slug]`,
       - использует `_extract_params(slug, text, param_schema)` для грубого извлечения значений из текста,
       - вычисляет список обязательных параметров (`required` из `param_schema["params"]`),
       - если есть пропуски — вызывает `_ask_missing_params(slug, missing, param_schema)` и возвращает вопрос менеджеру.
    3. **Выбор материалов/choices**:
       - проходит по параметрам с `type in ("enum", "enum_cascading")` (например, `material`),
       - если пользователь ввёл текст (типа `"акрил 3мм"`, `"молочный"`) вместо кода:
         - вызывает `_search_choices(slug, param_name, param_value)`,
         - если вариантов > 1 — возвращает текст с нумерованным списком вариантов для уточнения,
         - если вариант один — автоматически подставляет его `id` в `params`.
    4. **Вызов калькулятора**:
       - выбирает `tool_name` из `_tools_by_slug[slug]["name"]` или `calc_{slug}`,
       - вызывает `execute_tool(tool_name, params)`,
       - возвращает результат как JSON (форматирование текста может быть усложнено в будущем, используя LLM).

> Методы `_classify_intent`, `_simple_chat`, `_extract_params`, `_ask_missing_params` реализуются на стороне агента
> с использованием `LLMProvider` и знаний о `param_schema` — их точная реализация может эволюционировать.

### 4.3. Провайдер LLM (`llm_provider.py`)

- Использует `openai` SDK с кастомным `base_url` для Gemini.
- `LLM_MODE` в `.env`:
  - `mixed` — Gemini + fallback на YandexGPT при любой ошибке.
  - `gemini` — только Gemini.
  - `yandex` — только YandexGPT (нативный API).
- Встроен `TokenAnalyzer`:
  - `log_request()` — разбивает запрос по компонентам:
    - system, history, user, tools (включая размер JSON‑схем),
  - `log_response()` — считает токены на ответ и tool‑calls,
  - `save_to_file()` — пишет JSONL в `logs/token_usage.jsonl`.

## 5. Интеграция с сайтом и WordPress (`wp-plugin/`, `docs/wordpress-integration.md`)

- На сайте установлен ez Form Calculator.
- JavaScript‑обёртка (`insain-calc-bridge.js`):
  - перехватывает вызовы JS‑калькуляторов,
  - отправляет запросы на `calc_service` (`POST /api/v1/calc/{slug}`),
  - синхронизирует GET‑параметры URL и поля форм (`share_url`).
- Мини‑плагин `insain-calc-bridge.php` подключает JS на нужных страницах.

## 6. Документация (`docs/`)

- `CLAUDE.md` — основной «гайд для ИИ» по проекту:
  - структура репозитория,
  - правила работы с данными и калькуляторами,
  - инварианты ответов (обязательные поля),
  - перечень файлов `data/materials` и правила их расширения,
  - описание формата материалов (`title`, `description`, `cost_date`, `cost_source`),
  - текущий API‑контракт (`calc`, `options`, `calculators`, `param_schema`, `tool_schema`, `choices`).
- `architecture.md` — архитектура контейнеров, потоков данных, режимов LLM, список API‑эндпоинтов.
- `data-formats.md` — форматы JSON (материалы, оборудование, cost в рублях/валюте, расчётные поля).
- `common-json-reference.md` — полное описание и актуальные значения в `data/common.json`.
- `migration-guide.md` — пошаговая миграция JS→Python для калькуляторов и отдельный раздел по миграции метаданных материалов.
- `wordpress-integration.md` — интеграция с WordPress/ez Form Calculator.

Этот файл даёт внешней LLM цельную картину проекта: структуру кода и данных, важные инварианты, реализованные калькуляторы, API‑контракт, устройство бота и LLM‑провайдера. Он предназначен как точка входа для анализа и обсуждения изменений без необходимости читать весь репозиторий. 

## 7. Примеры данных

### 7.1. Пример материала (hardsheet.json)

```json5
"PVCUnextStrong": {
  "Default": {
    "size": [[3050, 2050], [2050, 1525]],
    "minSize": [200, 200],
    "density": 0.55,
    "unitDensity": "гсм3"
  },
  "PVC3": {
    "title": "ПВХ белый 3мм",
    "description": "ПВХ Unext Strong 3 мм",
    "cost": 750,
    "cost_date": "2025-03-24",   // дата прайса
    "cost_source": "ТрастФМ",    // источник прайса
    "thickness": 3
  },
  "PVC5": {
    "title": "ПВХ белый 5мм",
    "description": "ПВХ Unext Strong 5 мм",
    "cost": 1182,
    "thickness": 5
  }
}
```

После загрузки через `loader.py` варианты `PVC3`, `PVC5` превращаются в `MaterialSpec` с полным набором полей:
размеры из `Default`, плотность и т.д. `Default` как отдельный материал не создаётся.

### 7.2. Пример записи оборудования (laser.json, фрагмент)

```json5
"Laser01": {
  "name": "Лазерный гравер 60Вт",
  "cutPerHour": [[0.5, 200], [1.0, 120], [2.0, 60]],
  "defects": [[10, 0.1], [100, 0.05], [500, 0.02]],
  "depreciationPerHour": 150,
  "operatorCostPerHour": 700,
  "timePrepare": 0.25
}
```

В Python это превращается в объект оборудования с методами `get_cut_per_hour()`, `get_defect_rate()`, `get_time_ready()` и т.п.

### 7.3. Пример common.json (фрагмент)

```json5
{
  "costOperator": 1400,
  "marginMaterial": 0.6,
  "marginOperation": 0.55,
  "marginMin": 0.25,
  "marginBadge": 0.15,
  "baseTimeReady": [24, 8, 1],
  "USD": 95,
  "EUR": 100
}
```

Использование:

```python
from common.markups import MARGIN_MATERIAL, MARGIN_OPERATION, MARGIN_MIN, get_margin, BASE_TIME_READY
```

## 8. Примеры калькуляторов

### 8.1. LaserCalculator (упрощённо)

```python
class LaserCalculator(BaseCalculator):
    slug = "laser"
    name = "Лазерная резка и гравировка"
    description = "Расчёт стоимости лазерной резки/гравировки по жёстким материалам."

    def get_param_schema(self) -> dict:
        return {
            "slug": self.slug,
            "title": self.name,
            "params": [
                {
                    "name": "quantity",
                    "type": "integer",
                    "required": True,
                    "title": "Тираж",
                    "description": "Количество изделий",
                    "validation": {"min": 1, "max": 100000},
                },
                {
                    "name": "width_mm",
                    "type": "number",
                    "required": True,
                    "title": "Ширина (мм)",
                    "validation": {"min": 10, "max": 1300},
                    "unit": "мм",
                },
                {
                    "name": "height_mm",
                    "type": "number",
                    "required": True,
                    "title": "Высота (мм)",
                    "validation": {"min": 10, "max": 900},
                    "unit": "мм",
                },
                {
                    "name": "material",
                    "type": "enum_cascading",
                    "required": True,
                    "title": "Материал",
                    "description": "Листовой жёсткий материал (ПВХ, акрил и др.)",
                    "choices": {
                        "source": "materials:hardsheet",
                        "cascade_levels": ["type", "variant", "thickness"],
                    },
                },
                # ...
            ],
            "param_groups": {
                "main": ["quantity", "width_mm", "height_mm"],
                "material": ["material"],
                "processing": ["cut_length_m", "grave_area_m2"],
                "mode": ["mode"],
            },
        }
```

Реальный код дополнительно использует `layout_on_sheet`, методы оборудования и наценки из `common.markups`.

### 8.2. PrintSheetCalculator (основные моменты)

- Использует:
  - материалы `sheet` (бумага/картон),
  - оборудование `printer` (цифровая печать),
  - опционально калькулятор `lamination` и `cut_guillotine`.
- Важные особенности:
  - раскладка изделий на листе (учёт полей и интервалов),
  - порядок учёта брака: **сначала ламинация, потом печать** (как в исходном JS),
  - вес `weight_kg` считается по количеству конечных изделий, а не по листам с браком,
  - `time_hours` и `time_ready` приведены к JS‑логике (`Math.ceil` на сумму времён, `baseTimeReadyPrintSheet`).

## 9. Примеры тестов

### 9.1. Тест лазерного калькулятора (`calc_service/tests/test_calculators/test_laser.py`)

Основная идея:

- сравнить реальные расчёты по «номерам на двери» с эталонными значениями (стоимость, цена, время, вес, расход материалов),
- убедиться, что `materials` содержит `name` и `title`.

Фрагмент:

```python
def test_laser_real_nomerki(nomerki_result):
    if nomerki_result is None:
        pytest.skip("расчёт не выполнен (гравировка/данные)")
    r = nomerki_result
    e = EXPECTED

    assert _cmp(r["cost"], e["cost"], 0.01)
    assert _cmp(r["price"], e["price"], 0.01)
    assert _cmp(r["time_hours"], e["time_hours"], 0.01)
    assert _cmp(r["time_ready"], e["time_ready"], 0.01)
    assert _cmp(r["weight_kg"], e["weight_kg"], 0.01)

    mats = r.get("materials") or []
    got = next((m for m in mats if m.get("code") == "AcrylColor3"), None)
    assert got is not None
    assert "name" in got
    assert "title" in got
```

### 9.2. Тест API param_schema (`calc_service/tests/test_api.py`)

```python
from fastapi.testclient import TestClient
import sys
from pathlib import Path

_calc_service = Path(__file__).resolve().parent.parent
if _calc_service.name == "calc_service" and str(_calc_service) not in sys.path:
    sys.path.insert(0, str(_calc_service))

from main import app

client = TestClient(app)


def test_param_schema_endpoint() -> None:
    response = client.get("/api/v1/calculators")
    calculators = response.json()

    for calc in calculators:
        slug = calc["slug"]
        resp = client.get(f"/api/v1/param_schema/{slug}")
        assert resp.status_code == 200

        schema = resp.json()
        assert schema["slug"] == slug
        assert "params" in schema
        assert len(schema["params"]) > 0
```

## 10. Примеры работы агента и choices API

### 10.1. Запрос вариантов материалов (HTTP)

Пример запроса для подбора акрила 3мм в калькуляторе `laser`:

```bash
curl -s -X POST "http://localhost:8001/api/v1/choices" \
  -H "Content-Type: application/json" \
  -d '{"slug":"laser","param":"material","query":"акрил 3"}'
```

Ответ (пример):

```json
{
  "items": [
    {
      "id": "AcrylWhite3",
      "title": "Акрил молочный 3мм",
      "description": "Акрил молочный Plexiglas XT 3мм",
      "hint": "3.0 мм"
    },
    {
      "id": "AcrylTrans3",
      "title": "Акрил прозрачный 3мм",
      "description": "Акрил прозрачный Plexiglas XT 3мм",
      "hint": "3.0 мм"
    },
    {
      "id": "AcrylColor3",
      "title": "Акрил цветной 3мм",
      "description": "Акрил цветной Plexiglas XT 3мм",
      "hint": "3.0 мм"
    }
  ]
}
```

### 10.2. Диалог с агентом (концептуально)

1. Менеджер: «Посчитай резку акрила 3мм, 50×50мм, 10 штук».
2. Агент:
   - классифицирует запрос как `"calculation"`, выбирает калькулятор `laser`,
   - из текста извлекает: `quantity=10`, `width_mm=50`, `height_mm=50`, `material="акрил 3мм"`,
   - по `param_schema` видит, что `material` — `enum_cascading` с `choices.source="materials:hardsheet"`,
   - вызывает `/choices` с `query="акрил 3мм"`, получает несколько вариантов акрила 3мм,
   - возвращает менеджеру список:
     - 1. Акрил молочный 3мм
     - 2. Акрил прозрачный 3мм
     - 3. Акрил цветной 3мм
3. Менеджер: «Молочный».
4. Агент:
   - по ответу менеджера снова вызывает `/choices` (query="молочный") или фильтрует предыдущие варианты,
   - остаётся один вариант `AcrylWhite3`, подставляет его `id` в параметры,
   - вызывает калькулятор `laser` через `POST /api/v1/calc/laser`,
   - форматирует ответ (стоимость, сроки, вес, расход материалов) и отправляет в Telegram.

---

Этот расширенный файл `project_summary.md` даёт внешней LLM не только обзор структуры проекта, но и реальные примеры данных, калькуляторов, тестов и API‑взаимодействий, необходимых для качественной консультации и доработок без прямого доступа ко всему коду. 

