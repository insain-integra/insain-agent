# Миграция калькулятора JS → Python

## Пошаговый процесс

### 1. Подготовка

Открыть рядом:
- JS-файл из `js_legacy/calc/`
- Шаблон `calculators/_template.py`
- Эталон `calculators/laser.py` (если уже создан)

### 2. Определить зависимости

В JS какие справочники используются:
insaincalc.hardsheet → from ..materials import hardsheet
insaincalc.roll → from ..materials import roll
insaincalc.laser → from ..equipment import laser_catalog
insaincalc.printer → from ..equipment import printer_catalog

### 3. Определить наценку

Каждый калькулятор имеет свою наценку в `common.json`.

Как найти:
- В JS искать `insaincalc.common.margin*`
- Или по имени калькулятора: laser → `marginLaser`, badge → `marginBadge`

Как использовать:
```python
from ..common.markups import (
    MARGIN_MATERIAL, MARGIN_OPERATION, MARGIN_MIN, get_margin,
)

margin_extra = get_margin("marginLaser")  # 0.0, 0.20, -0.1 и т.д.
effective_margin = max(MARGIN_OPERATION + margin_extra, MARGIN_MIN)

price_material = cost_material * (1 + MARGIN_MATERIAL)
price_operation = cost_operation * (1 + effective_margin)
price = price_material + price_operation
````

Примеры:
```
Лазер:     0.0   → effective = max(0.55 + 0.0, 0.25)  = 0.55
Бейджи:    0.20  → effective = max(0.55 + 0.20, 0.25) = 0.75
Значки:   -0.1   → effective = max(0.55 - 0.1, 0.25)  = 0.45
Плакетки:  0.5   → effective = max(0.55 + 0.5, 0.25)  = 1.05
```
### 4. Перенести расчёт времени
**Ключевое отличие от JS.** В JS время считается но НЕ отображается.  
В Python `time_hours` и `time_ready` — обязательные поля.

#### Как найти в JS

Искать: `time`, `Time`, `hour`, `Hour`, `Ready`, `Prepare`

```
JS                    Python
─────────────────────────────────────
timePrepare         → time_prepare
timeCut             → time_cut
timeGrave           → time_grave
timePrint           → time_print
timeLoad            → time_load
timeOperator        → time_operator
timeLamination      → time_lamination
result.time         → time_hours
result.timeReady    → time_ready
baseTimeReady       → из оборудования или common.json
```

#### Формула

```Python
# Чистое время работы
time_hours = time_prepare + time_work + time_load + ...

# Время готовности = работа + очередь
# Вариант 1: из оборудования
time_ready = time_hours + equipment.get_time_ready(mode.value)

# Вариант 2: из common.json (по умолчанию)
from ..common.markups import BASE_TIME_READY
time_ready = time_hours + BASE_TIME_READY[mode.value]  # [24, 8, 1]

# Вариант 3: особые сроки
from ..common.markups import get_time_ready
time_ready = time_hours + get_time_ready("baseTimeReadyPrintSheet")[mode.value]
```

#### Влияние режима производства (`ProductionMode`)

Режим производства во всём ядре и API — **0-based** (`ProductionMode`):
- `0` (`ECONOMY`) — экономичный: `time_prepare = base_prepare * 0` (`0`), брак базовый (`defect_rate`), самый длинный срок `baseTimeReady[0]`;
- `1` (`STANDARD`) — стандартный (по умолчанию): `time_prepare = base_prepare * 1`, брак базовый, `baseTimeReady[1]`;
- `2` (`EXPRESS`) — экспресс: `time_prepare = base_prepare * 2`, брак удваивается (`defect_rate += defect_rate * (mode - 1)`), самый короткий срок `baseTimeReady[2]`.

Использовать единые хелперы из `calculators/base.py` и `EquipmentSpec.get_time_ready(mode)` (0-based, без `mode + 1`):

```Python
from calculators.base import (
    ProductionMode,
    apply_mode_defects,
    calc_time_prepare,
    parse_mode,
    pick_time_ready,
)

# Чтение режима: НЕ писать `params.get("mode") or 1` (съедает mode=0!)
mode = parse_mode(params.get("mode"))

# Подготовка: НЕ писать `max(1, mode.value)` — в экономе подготовка = 0 (как в js_legacy)
time_prepare = calc_time_prepare(equipment.time_prepare, mode)

# Брак: в экспрессе (mode > 1) растёт на defect_rate * (mode - 1)
defect_rate = apply_mode_defects(equipment.get_defect_rate(quantity), mode)

# Базовый срок готовности (0-based индекс, зажим в границах массива)
time_ready = time_hours + equipment.get_time_ready(mode)
# Или для произвольного массива сроков:
time_ready = time_hours + pick_time_ready(custom_times, mode, BASE_TIME_READY)
```

Контракт (автоматически проверяется в `calc_service/tests/test_mode_contract.py`):
- для всех калькуляторов: `time_hours(0) <= time_hours(1) <= time_hours(2)`, `price(0) <= price(1) <= price(2)`, `time_ready(2) <= time_ready(1) <= time_ready(0)`;
- для собственного производства: строго `price(0) < price(1) < price(2)`;
- запрещены `max(1, mode...)` в расчёте `time_prepare` и `mode or 1` при чтении режима.

#### Реестр исключений `mode`

| Категория | Калькуляторы / ветки | Особенность `mode` |
| --- | --- | --- |
| **Подрядчики** | `cards`, `print_offset` (сборники `offset_promo`), `button_pins` при `n > 2000` (Амалит), `metal_pins` | Цена либо фиксирована (`cards`, `offset_promo`, Амалит; у `cards` и `offset_promo` `mode` меняет только `time_ready`, у Амалита срок тоже фиксирован), либо зависит от тарифа логистики (`metal_pins`: Китай→РФ по индексу `mode` и `timePrepare * mode`). |
| **Логистика** | `metal_pins`, `milling` | `metal_pins`: ступенчатый тариф доставки Китай→РФ `[5.2, 10, 17]` по `mode`. `milling`: коэффициент доставки `0.5` при `mode=0` и `max(1, mode.value)` при `mode >= 1` (`time_prepare` при этом считается честно через `mode.value`). |
| **Составные слои / подрасчёты** | `acrylic_prizes`, `print_sheet`, `tablets`, `plaque` | `acrylic_prizes`: как в JS, `timeReady` операции берётся один раз на первом слое при `mode > 0`, поэтому при `mode=0` `time_ready == time_hours`. `print_sheet`: mode-надбавку к браку применяет только печать, а не расход бумаги. `tablets`: режим пробрасывается в подрасчёты (`laser`, `uv_print`, ручные операции). `plaque`: как в JS (`calcPlaque`, стр. 640), пластина всегда считается в `mode=1`, цена и срок фиксированы. |
| **Нулевая подготовка в JSON** | `print_offset` (`OffsetPrint`), `cut_guillotine`, `cut_roller`, `lamination_wide` | В JSON `timePrepare = 0`: цена плоская (у `lamination_wide` `price(0) == price(1) < price(2)` за счёт брака в экспрессе), `mode` меняет `time_ready`. |

### 5. Перенести остальную логику

```
JS                                     Python
──────────────────────────────────────────────────────────────
options.has('key')                    → "key" in params
options.get('key')                    → params["key"]
insaincalc.findMaterial('x', id)     → x_catalog.get(id)
insaincalc.calcLayoutOnSheet(...)    → layout_on_sheet(...)
insaincalc.calcLayoutOnRoll(...)     → layout_on_roll(...)
insaincalc.common.marginMaterial     → MARGIN_MATERIAL
insaincalc.common.marginLaser        → get_margin("marginLaser")
insaincalc.common.costOperator       → COST_OPERATOR
insaincalc.laser["code"]             → laser_catalog.get("code")
throw new ICalcError(...)            → raise ValueError(...)
Math.ceil / round / max / min / floor→ math.ceil / round / max / min / int
Map                                  → dict
result.material.set(k, v)            → materials.append({...})
```

### 6. Вернуть обязательные поля

```Python
return {
    "cost": cost,
    "price": price,
    "unit_price": price / qty,
    "time_hours": time_hours,
    "time_ready": time_ready,
    "weight_kg": weight,
    "materials": materials,
}
```

`share_url` добавляется автоматически в `execute()`.

### 7. Зарегистрировать

В `calculators/__init__.py`:

```Python
from .новый import НовыйCalculator
CALCULATORS = { ..., "новый": НовыйCalculator() }
```

### 8. Написать тесты

- Базовый расчёт: price > 0
- Время: time_hours > 0, time_ready > time_hours
- Режимы `mode ∈ {0, 1, 2}`: `time_ready(2) <= time_ready(1) <= time_ready(0)`, `time_hours(0) <= time_hours(1) <= time_hours(2)`, `price(0) < price(1) < price(2)` (для собственного производства) и сверка `mode=0, 1, 2` с JS/ТЗ; добавление кейса в `calc_service/tests/test_mode_contract.py`
- Тираж: больше → больше time_hours
- Все материалы группы
- Граничные случаи
- Невалидные данные → ошибка

### 9. Сверить с JS

На одинаковых входных: цена ≈, time ≈, weight ≈.

## Чек-лист

### Время

```
☐ time_hours > 0
☐ time_ready > time_hours
☐ EXPRESS < STANDARD < ECONOMY
☐ Больше тираж → больше time_hours
☐ Все этапы включены
☐ Совпадает с JS
```

### Наценки


```
☐ get_margin("marginИмя")
☐ Прибавляется к MARGIN_OPERATION
☐ Не ниже MARGIN_MIN
☐ MARGIN_MATERIAL для материалов
☐ price > cost
```

### Общее

```
☐ Все обязательные поля
☐ Несколько материалов
☐ Тесты написаны и проходят
☐ Добавлен в CALCULATORS
☐ pytest calc_service/tests/ -v проходит
```

## Миграция метаданных материалов (title, description, cost_date, cost_source)

После первичной миграции калькуляторов структура файлов `data/materials/*.json`
была расширена:

- `name` → `description` (старое поле больше не используется),
- добавлен `title` — короткое название для UI (≤ 50 символов),
- добавлены `cost_date` и `cost_source` — метаданные о стоимости.

Для автоматической миграции используется скрипт:

```bash
python -m calc_service.scripts.migrate_materials_metadata
```

Он:

- читает JSON5‑файлы материалов как текст,
- переносит `name` → `description`, если `description` отсутствует,
- генерирует `title` по правилам (убирает бренды и лишние технические детали),
- извлекает `cost_date` и `cost_source` из комментариев к `cost`
  (например, `// 24.03.2025 ТрастФМ`),
- сохраняет обновлённую структуру обратно в `data/materials/*.json`.

После запуска скрипта обязательно:

```bash
pytest calc_service/tests/ -v
```

чтобы убедиться, что все калькуляторы и загрузчики продолжают корректно работать с новой структурой.

