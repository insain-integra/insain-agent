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

#### Влияние режима производства

```Python
# Подготовка зависит от режима (в некоторых калькуляторах)
time_prepare = equipment.time_prepare * mode.value

# Брак увеличивается в экспрессе
if mode.value > 1:
    defect_rate += defect_rate * (mode.value - 1)
```

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
- Режимы: EXPRESS < STANDARD < ECONOMY
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
☐ make test проходит
```

