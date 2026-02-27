# Справочник common.json

Файл `data/common.json` содержит все общие настройки расчётов.
Читается через json5 (поддерживает комментарии).

Загружается тремя модулями:
- `common/markups.py` — наценки и сроки
- `common/currencies.py` — курсы валют
- `common/holidays.py` — праздничные дни

## Полное содержимое файла

```json
{
    "costOperator": 1400,
    "marginMaterial": 0.6,
    "marginOperation": 0.55,
    "marginMin": 0.25,
    "marginPrintLaser": 0.0,
    "marginPrintWide": 0.0,
    "marginLamination": 0.0,
    "marginLaminationWide": 0.0,
    "marginCutGuillotine": 0.0,
    "marginCutRoller": 0.0,
    "marginPlotter": 0.0,
    "marginLaser": 0.0,
    "marginMilling": 0.0,
    "marginSticker": 0.0,
    "marginBadge": 0.20,
    "marginStickerPoly": 0.20,
    "marginMetalPins": 0.4,
    "marginButtonPins": -0.1,
    "marginPrintSheet": 0.0,
    "marginPrintRoll": 0.0,
    "marginTablets": 0.0,
    "marginPlaque": 0.5,
    "marginUVPrint": 0.0,
    "marginPadPrint": 0.25,
    "marginProcessManual": 0.0,
    "marginHeatPress": 0.0,
    "marginMug": 0.0,
    "marginNotebook": 0.1,
    "marginCalendar": 0.2,
    "marginPrintOffset": 0.4,
    "marginOffsetPromo": 0.1,
    "marginPresswall": 0.0,
    "marginRollup": 0.0,
    "marginFlag": 0.0,
    "marginPennantPaper": 0.0,
    "marginPuzzle": 0.0,
    "marginAcrylicKeychain": 0.0,
    "marginAcrilycPrizes": 0.0,
    "marginCanvas": 0.0,
    "marginEmbossing": 0.0,
    "baseTimeReady": [24, 8, 1],
    "baseTimeReadyPrintSheet": [24, 8, 1],
    "baseTimeReadyPrintOffsetPromo": [56, 48, 40],
    "USD": 95,
    "EUR": 100,
    "calendar": {
        "workingDays": ["3.1","4.1","5.1","6.1","7.1","23.2",
                        "7.3","8.3","2.5","3.5","9.5","10.5",
                        "13.6","4.11"],
        "weekEnd": ["5.3"]
    }
}
```

## Основные параметры

| Поле | Значение | Описание | Python |
|------|----------|----------|--------|
| costOperator | 1400 | Себестоимость часа оператора, ₽ | `COST_OPERATOR` |
| marginMaterial | 0.6 | Наценка на материал (60%) | `MARGIN_MATERIAL` |
| marginOperation | 0.55 | Базовая наценка на операции (55%) | `MARGIN_OPERATION` |
| marginMin | 0.25 | Минимальная допустимая наценка (25%) | `MARGIN_MIN` |

## Специфичные наценки

Прибавляются к `marginOperation`. Могут быть отрицательными (скидка).
Получать через `get_margin("marginИмя")`.

| Поле | Значение | Итоговая наценка | Калькулятор |
|------|----------|------------------|-------------|
| marginPrintLaser | 0.0 | 0.55 | Лазерная печать |
| marginPrintWide | 0.0 | 0.55 | Широкоформатная печать |
| marginLamination | 0.0 | 0.55 | Ламинация |
| marginLaminationWide | 0.0 | 0.55 | Широкоформатная ламинация |
| marginCutGuillotine | 0.0 | 0.55 | Гильотинная резка |
| marginCutRoller | 0.0 | 0.55 | Роликовый резак |
| marginPlotter | 0.0 | 0.55 | Плоттерная резка |
| marginLaser | 0.0 | 0.55 | Лазерная резка |
| marginMilling | 0.0 | 0.55 | Фрезерная резка |
| marginSticker | 0.0 | 0.55 | Наклейки |
| marginBadge | 0.20 | **0.75** | Бейджи |
| marginStickerPoly | 0.20 | **0.75** | Полимерные наклейки |
| marginMetalPins | 0.4 | **0.95** | Металлические значки |
| marginButtonPins | -0.1 | **0.45** | Закатные значки *(скидка)* |
| marginPrintSheet | 0.0 | 0.55 | Листовая печать |
| marginPrintRoll | 0.0 | 0.55 | Рулонная печать |
| marginTablets | 0.0 | 0.55 | Таблички |
| marginPlaque | 0.5 | **1.05** | Плакетки |
| marginUVPrint | 0.0 | 0.55 | УФ-печать |
| marginPadPrint | 0.25 | **0.80** | Тампопечать |
| marginProcessManual | 0.0 | 0.55 | Ручные операции |
| marginHeatPress | 0.0 | 0.55 | Термоперенос |
| marginMug | 0.0 | 0.55 | Кружки |
| marginNotebook | 0.1 | **0.65** | Блокноты |
| marginCalendar | 0.2 | **0.75** | Календари |
| marginPrintOffset | 0.4 | **0.95** | Офсетная печать |
| marginOffsetPromo | 0.1 | **0.65** | Сборная офсетная |
| marginPresswall | 0.0 | 0.55 | Прессволы |
| marginRollup | 0.0 | 0.55 | Ролл-апы |
| marginFlag | 0.0 | 0.55 | Флажки |
| marginPennantPaper | 0.0 | 0.55 | Бумажные вымпелы |
| marginPuzzle | 0.0 | 0.55 | Пазлы |
| marginAcrylicKeychain | 0.0 | 0.55 | Акриловые брелоки |
| marginAcrilycPrizes | 0.0 | 0.55 | Акриловые призы |
| marginCanvas | 0.0 | 0.55 | Холст |
| marginEmbossing | 0.0 | 0.55 | Тиснение |

*Итоговая наценка = max(marginOperation + marginХХХ, marginMin)*

## Сроки готовности

Массив из трёх значений: [экономичный, стандартный, экспресс].
Единица измерения — рабочие часы.

| Поле | Значение | Для чего |
|------|----------|----------|
| baseTimeReady | [24, 8, 1] | По умолчанию (большинство калькуляторов) |
| baseTimeReadyPrintSheet | [24, 8, 1] | Листовая печать |
| baseTimeReadyPrintOffsetPromo | [56, 48, 40] | Сборная офсетная печать |

Расшифровка индексов:
```
[0] = экономичный режим (mode=0)  — 24 часа ≈ 3 рабочих дня
[1] = стандартный режим (mode=1)  —  8 часов ≈ 1 рабочий день
[2] = экспресс режим (mode=2)    —  1 час   ≈ в тот же день
```

Формула:
```
time_ready = time_hours + baseTimeReady[mode]
```

Получать через:
```python
from common.markups import BASE_TIME_READY, get_time_ready

# По умолчанию
BASE_TIME_READY[mode.value]

# Для калькуляторов с особыми сроками
get_time_ready("baseTimeReadyPrintSheet")[mode.value]
get_time_ready("baseTimeReadyPrintOffsetPromo")[mode.value]
```

## Курсы валют

| Поле | Значение | Описание |
|------|----------|----------|
| USD | 95 | Курс доллара к рублю |
| EUR | 100 | Курс евро к рублю |

Используются в `common/currencies.py` для конвертации цен
оборудования из валюты в рубли (`"$11600"` → рубли).

Получать через:
```python
from common.currencies import USD_RATE, EUR_RATE, parse_currency

parse_currency("$11600")  # → 1 102 000.0
parse_currency("€500")    # → 50 000.0
parse_currency(750)        # → 750.0
```

## Календарь

```json
"calendar": {
    "workingDays": ["3.1", "4.1", ...],  // праздничные нерабочие дни
    "weekEnd": ["5.3"]                    // выходные ставшие рабочими
}
```

Формат даты: `"день.месяц"` (без года — повторяется каждый год).

Используется в `common/holidays.py`:
```python
from common.holidays import is_working_day, add_working_hours

is_working_day(date(2024, 1, 3))    # → False (праздник)
is_working_day(date(2024, 3, 5))    # → True  (выходной стал рабочим)
add_working_hours(today, 24)         # → дата готовности
```

## Как обновлять

```
Изменить data/common.json → make test → make restart

Примеры:
  Курс доллара:     "USD": 95 → "USD": 100
  Наценка на бейджи: "marginBadge": 0.20 → "marginBadge": 0.30
  Сроки:            "baseTimeReady": [24, 8, 1] → [32, 16, 4]
  Стоимость часа:   "costOperator": 1400 → "costOperator": 1600
```