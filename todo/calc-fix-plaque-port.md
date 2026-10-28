# calc-fix-plaque-port

Статус: ревью
Сложность: высокая
Implementer: Opus 5.5
Reviewer: Grok 4.7
Почему: правка чтения УФ-принтера меняет цены шести калькуляторов, эталон — старый JS при одинаковых ставках.

## Цель

`PlaqueCalculator` для `isUVPrint` и `isGrave` (mode 1) совпадает со старым `calcPlaque` во всех шести полях в допуске 0.03 на прогоне `node scripts/run_js_calc.mjs calcPlaque --data current`. В `test_plaque.py` 5–10 эталонов с пометкой `JS, ДД.ММ.ГГГГ`. Чекбокс 5.6 в плане отмечен. Файлы цен не изменены.

## Контекст и ссылки

- Причины расхождений и разложение по слагаемым — `todo/calc-reconcile-plaque.md`, раздел «Разбор расхождений, 28.10.2026». Числа JS по слагаемым там же: эталон для промежуточных проверок.
- `scripts/run_js_calc.mjs` — эталон JS. Ветка `task/calc-reconcile-plaque`: начинать после её merge в `main`, иначе скрипта нет.
- `js_legacy/calc/calcTablets.js` — `calcPlaque` (строки 582–661) и начало `calcTablets` (опции `isCutLaser`, `isUVPrint`, итог). Как плакетка собирает опции для каждого нанесения.
- `js_legacy/calc/calcUVPrint.js` — `volPrint` по раскладке (строки 59–96), `meterPerHour[resolution]`, `costProcess` по цветности (124–129).
- `calc_service/calculators/plaque.py`, `calc_service/calculators/tablets.py` (строки 153–216), `calc_service/calculators/uv_print.py` (`calculate`).
- `calc_service/equipment/loader.py` (строки 186–188 и `cost_process=_to_float(...)`), `calc_service/equipment/base.py` (`EquipmentSpec`). `meter_per_hour_table` и `cost_process` читают ламинация и `process_tools` — их смысл не менять.
- Вызовы `UVPrintCalculator`: `uv_print`, `tablets`, `uv_badge`, `shild`, `acrylic_prizes`, `badge`. Ни одна форма сайта на эти slug не переведена (`docs/site/forms.md`), прод не затрагивается.
- `docs/refactoring-plan.md` — только «Протокол выполнения» и пункт 5.6.
- Остальное не открывать.

## Scope

1. **Чтение записи УФ-принтера.** Плоский массив `meterPerHour` (`[1.2, 0.6, 0.3]`) — скорость по разрешению. Массив `costProcess` (`[1300, 800, 800]`) — расходники по слоям: полноцвет, белый, лак. Сохранить их целиком в новых полях `EquipmentSpec`. Существующие `meter_per_hour`, `meter_per_hour_table`, `cost_process` не менять.
2. **`uv_print.py`** берёт скорость `meterPerHour[resolution]` и расходники по цветности, как в `calcUVPrint.js`. `4+0` и `1+0` — `[0]`, `4+1` — `[0]+[1]`, `4+2` — `[0]+[1]+[2]`. `vol_print` считать по раскладке на столе принтера, как в JS.
3. **Пластина плакетки** собирается как в `calcPlaque`. УФ: лазерная резка с материалом (`sizeItem` = меньшая сторона пластины, `density` 0, `difficulty` 1, `lenCut` 0) и УФ-печать `RimalSuvUV`, resolution 2, `4+1`, `isPlain`. Гравировка: та же резка, плюс `is_grave` 2 и `is_grave_fill` = размер пластины. Как передать — решает Implementer: новые необязательные параметры `TabletsCalculator` или прямые вызовы `LaserCalculator` и `UVPrintCalculator` из `plaque.py`. Ответ slug `tablets` при прежних параметрах не меняется, кроме изменений от пунктов 1–2.
4. **`time_ready` пластины** — как в JS: в `calcTablets` время работ плюс максимум сроков, затем в `calcPlaque` время прибавляется ещё раз.
5. **Тесты.** Загрузчик: у `RimalSuvUV` скорость при resolution 2 равна 0.3, расходники `4+1` — 2100. В `test_plaque.py` 5–10 эталонов прогона `--data current`, пометка `JS, ДД.ММ.ГГГГ` ровно один раз на кейс. Набор: два `quantity` (один ≥ 2), `Plaque2330` и `Plaque1520`, `PVC3` и `AcrylWhite3` (`AcrylWhite3` есть в форме 69), `isUVPrint` и `isGrave`. `REF_PARAMS` перепрогнать: в допуске — дописать пометку, нет — в отчёт.
6. **Ожидаемые числа других тестов** (`test_uv_print`, `test_tablets`, `test_uv_badge`, `test_shild`, `test_acrylic_prizes`, `test_badge`) меняются только из-за пунктов 1–2. Каждое изменение — строка в «Результате»: тест, поле, было, стало.
7. После зелёных критериев — чекбокс 5.6 и строка «сделано ДД.ММ.ГГГГ, проверено: \<команда\>» по протоколу.

## Не-scope

- JSON цен и наценок, `js_legacy/**`, `scripts/run_js_calc.mjs`.
- Сублимация (`NaN` в JS на PVC, расхождение на `AluminiumSU055`), `noApplication` (`time_ready` 0 в JS), mode 0 и 2 (JS принудительно считает пластину в режиме 1).
- Округления в пределах допуска: вес `round` против `Math.ceil`, итог `math.ceil` против цены без округления.
- Ветка не-laser в `tablets.py`: руб./м² умножаются на целые листы. Для плакетки она уходит пунктом 3, для slug `tablets` — отдельная задача.
- Цена гравировки заливкой всей пластины (8.6 ч на две плакетки). Переносится как в JS, бизнес-решение — отдельно.
- Форма 69, WordPress, VDS, деплой.

## Критерии приёмки

Каждый пункт — команда и ожидаемый результат.

- [x] Для `{"quantity":2,"plaque_id":"Plaque2330","material_id":"PVC3","application":"isUVPrint","mode":1}` и того же с `"application":"isGrave"`: `node scripts/run_js_calc.mjs calcPlaque --data current --params '<json>'` и `python -c "import sys,json; sys.path.insert(0,'calc_service'); from calculators.plaque import PlaqueCalculator; print(json.dumps(PlaqueCalculator().execute(json.loads(sys.argv[1]))))" '<json>'` — шесть полей в допуске 0.03. Ориентир JS: УФ 2698.3 / 6205.71 / 1.32 / 35.67 / 1.18, гравировка 9497.1 / 20224.31 / 8.9 / 42.7 / 1.18.
- [x] `python -c "import pathlib,re; t=pathlib.Path(r'calc_service/tests/test_calculators/test_plaque.py').read_text(encoding='utf-8'); m=re.findall(r'JS, \d{2}\.\d{2}\.\d{4}', t); print(len(m)); assert 5<=len(m)<=10"` — число от 5 до 10, код 0.
- [x] `python -m pytest calc_service/tests/test_calculators/test_plaque.py calc_service/tests/test_calculators/test_uv_print.py calc_service/tests/test_calculators/test_tablets.py -q` — код 0, `skipped` нет.
- [x] Тест загрузчика из пункта 5 падает на `main` и проходит на ветке.
- [x] `git diff main -- calc_service/data js_legacy scripts/run_js_calc.mjs` — пусто.
- [x] `git diff main --name-only` — только `calc_service/equipment/`, `calc_service/calculators/{uv_print,tablets,plaque}.py`, `calc_service/tests/`, `docs/refactoring-plan.md`, этот файл.

## Проверки

- [x] `make check` (или `python scripts/dev.py check`) — зелёный вывод
- [x] Self-review — чеклист «Перед сдачей» в [AGENTS.md](../AGENTS.md)

## Риски

- Прод: нет. На API переведена только форма `puzzle`. Новые цены уйдут в публичный API после деплоя, деплой не в этой задаче.
- Цены: JSON не меняются. Меняются расчётные цены `uv_print`, `uv_badge`, `shild`, `acrylic_prizes`, `badge`, `tablets`, `plaque`: УФ-печать дорожает при resolution > 0 и при белом слое.
- Формы: нет

## Режим

обычный

## Результат

- Ветка, PR или коммит: `task/calc-fix-plaque-port`
- Сделано:
  - `EquipmentSpec`: новые поля `meter_per_hour_by_resolution` (плоский `meterPerHour`) и `cost_process_by_layer` (массив `costProcess`), загрузчик заполняет их через `_parse_flat_list`. `meter_per_hour`, `meter_per_hour_table`, `cost_process` не менялись.
  - `uv_print.py`: скорость `meterPerHour[resolution]`, расходники по слоям (`4+1` = `[0]+[1]`), `vol_print` и число загрузок — по раскладке на столе, как `calcLayoutOnSheet` и `calcUVPrint.js` (`_layout_on_printer`, `_vol_print_plain`). Принтеры без массивов считаются по прежней ветке.
  - `plaque.py`: для `isUVPrint` и `isGrave` пластина считается `_calc_plate` — прямые вызовы `LaserCalculator` (резка с материалом, `size_item` = меньшая сторона, гравировка `is_grave` 2 + `is_grave_fill`) и `UVPrintCalculator` (`RimalSuvUV`, resolution 2, `4+1`, plain). Итог как в `calcTablets`: `marginTablets`, время `ceil`, `time_ready` = время + максимум сроков, вес `ceil`; затем `calcPlaque` ещё раз прибавляет время. `tablets.py` не менялся, сублимация идёт прежним путём.
  - Тесты: `test_equipment.py::test_uv_printer_speed_and_cost_by_layer`; в `test_plaque.py` `EXPECTED_REF` заменён числами JS и 7 параметризованных кейсов JS — всего 8 пометок `JS, 29.10.2026` (тиражи 2 и 5, `Plaque2330`/`Plaque1520`, `PVC3`/`AcrylWhite3`, УФ/гравировка). Чекбокс 5.6 в плане отмечен.
  - `REF_PARAMS` перепрогнан: старые числа (2062 / 4906 / 0.37 / 32.74 / 1.17) были не JS и в допуск не попадали; новый расчёт совпал с JS (2698.3 / 6205.71 / 1.32 / 35.67 / 1.18), числа JS вписаны с пометкой.
  - Ожидаемые числа других тестов (было → стало), все из-за пунктов 1–2:
    - `test_uv_print` (resolution 0, `4+0`): cost 2460 → 2430, price 3936 → 3888, time_hours 1.14 → 1.05, time_ready 33.14 → 33.05.
    - `test_tablets`: time_hours 0.65 → 0.6, time_ready 32.65 → 32.6.
    - `test_shild`: cost 2868 → 2843, price 4634 → 4594, time_hours 1.04 → 0.94, time_ready 33.04 → 32.94.
    - `test_uv_badge` (resolution 2): cost 3206 → 4735, price 5929.40 → 8742.30, time_hours 1.64 → 2.98, time_ready 33.64 → 34.98.
    - `test_acrylic_prizes` (resolution 2, `4+1`): cost 1134.45 → 1667.45, price 1816 → 2669, time_hours 1.96 → 2.44, time_ready 34.36 → 35.32.
    - `test_badge`: без изменений.
- Чем проверено:
  - Критерий 1, команды из критерия: УФ JS `2698.3 / 6205.71 / 3102.86 / 1.32 / 35.67 / 1.18`, Python `2698.3 / 6206 / 3103.0 / 1.32 / 35.67 / 1.18`; гравировка JS `9497.1 / 20224.31 / 10112.16 / 8.9 / 42.7 / 1.18`, Python `9497.1 / 20225 / 10112.5 / 8.9 / 42.7 / 1.18`. Дополнительно сетка 16 кейсов (тираж 2 и 5 × две плакетки × два материала × УФ/гравировка) — все 16 в допуске по шести полям, отличие только `math.ceil` цены.
  - Подсчёт пометок: `8`, код 0.
  - `pytest test_plaque.py test_uv_print.py test_tablets.py -q`: `31 passed`, skipped нет.
  - Тест загрузчика: на коде `main` — `FAILED ... AttributeError` (поля нет), на ветке — passed.
  - `git diff main -- calc_service/data js_legacy scripts/run_js_calc.mjs` — пусто; `--name-only` — только разрешённые пути.
  - `python scripts/dev.py check`: `441 passed`, `81 passed`.
- Не сделано и почему: соседние расхождения `uv_print.py` с JS, вне scope: скидка от объёма `discount` (`PrintUV`) не применяется; круговая печать берёт `timePrepare` вместо `timePrepareAround`. `test_equipment.py` при запуске отдельным файлом не находит `common` (нет вставки `calc_service` в `sys.path`), в составе `calc_service/tests` проходит — так и на `main`.
- Требуется решение: бизнес-вопрос из `calc-reconcile-plaque` остаётся — гравировка заливкой всей пластины перенесена как в JS (8.9 ч, 20 225 руб. на две плакетки 2330).
