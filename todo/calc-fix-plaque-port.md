# calc-fix-plaque-port

Статус: черновик
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

- [ ] Для `{"quantity":2,"plaque_id":"Plaque2330","material_id":"PVC3","application":"isUVPrint","mode":1}` и того же с `"application":"isGrave"`: `node scripts/run_js_calc.mjs calcPlaque --data current --params '<json>'` и `python -c "import sys,json; sys.path.insert(0,'calc_service'); from calculators.plaque import PlaqueCalculator; print(json.dumps(PlaqueCalculator().execute(json.loads(sys.argv[1]))))" '<json>'` — шесть полей в допуске 0.03. Ориентир JS: УФ 2698.3 / 6205.71 / 1.32 / 35.67 / 1.18, гравировка 9497.1 / 20224.31 / 8.9 / 42.7 / 1.18.
- [ ] `python -c "import pathlib,re; t=pathlib.Path(r'calc_service/tests/test_calculators/test_plaque.py').read_text(encoding='utf-8'); m=re.findall(r'JS, \d{2}\.\d{2}\.\d{4}', t); print(len(m)); assert 5<=len(m)<=10"` — число от 5 до 10, код 0.
- [ ] `python -m pytest calc_service/tests/test_calculators/test_plaque.py calc_service/tests/test_calculators/test_uv_print.py calc_service/tests/test_calculators/test_tablets.py -q` — код 0, `skipped` нет.
- [ ] Тест загрузчика из пункта 5 падает на `main` и проходит на ветке.
- [ ] `git diff main -- calc_service/data js_legacy scripts/run_js_calc.mjs` — пусто.
- [ ] `git diff main --name-only` — только `calc_service/equipment/`, `calc_service/calculators/{uv_print,tablets,plaque}.py`, `calc_service/tests/`, `docs/refactoring-plan.md`, этот файл.

## Проверки

- [ ] `make check` (или `python scripts/dev.py check`) — зелёный вывод
- [ ] Self-review — чеклист «Перед сдачей» в [AGENTS.md](../AGENTS.md)

## Риски

- Прод: нет. На API переведена только форма `puzzle`. Новые цены уйдут в публичный API после деплоя, деплой не в этой задаче.
- Цены: JSON не меняются. Меняются расчётные цены `uv_print`, `uv_badge`, `shild`, `acrylic_prizes`, `badge`, `tablets`, `plaque`: УФ-печать дорожает при resolution > 0 и при белом слое.
- Формы: нет

## Режим

обычный

## Результат

- Ветка, PR или коммит:
- Сделано:
- Чем проверено:
- Не сделано и почему:
- Требуется решение:
