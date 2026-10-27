# calc-reconcile-plaque

Статус: ревью
Сложность: высокая
Implementer: Opus 5.5
Reviewer: Grok 4.7
Почему: наценки `js_legacy` и текущего прайса уже расходятся; эталон нельзя списать на устаревшую цену.

## Цель

Есть скрипт на Node, который считает старым JS из `js_legacy/`. Для `calcPlaque` в `test_plaque.py` лежат 5–10 эталонов, совпавших с API на актуальных ценах, с пометкой `JS, ДД.ММ.ГГГГ`. `make check` зелёный. Файлы цен не изменены.

## Контекст и ссылки

- `docs/refactoring-plan.md` — только раздел «Протокол выполнения» и пункт 5.6. План целиком не читать.
- `js_legacy/calc/calcTablets.js` — `calcPlaque` (с объявления функции). Вход: `n`, `plaqueID`, `materialID`, `applicationID`, `options`, `modeProduction`. Выход JS: `cost`, `price`, `time`, `timeReady`, `weight`, `material`. Поля `unit_price` в JS нет.
- В вызове `calcTablets` пятый аргумент — присваивание `modeProduction = 1`. Старый JS считает пластину в режиме 1 при любом `mode`. Ветку `default` у `applicationID` тоже вызывает `calcTablets`. Это не чинить.
- `js_legacy/calc/icdc_ls.js` — `StructDat` и снятие комментариев. `loadData` ходит через `XMLHttpRequest` по пути `icalc/...`; в Node так не грузить.
- `js_legacy/calc/common.js` — `findMaterial`, `mergeMaps`. Плакетка ищется как `findMaterial("misc", plaqueID)`.
- `calc_service/calculators/plaque.py` — те же параметры, что у API (`quantity`, `plaque_id`, `material_id`, `application`, `mode`). `unit_price` = `round(price / max(1, n), 2)`.
- `calc_service/tests/test_calculators/test_plaque.py` — допуск `_cmp` / `rel = 0.03` и эталон `REF_PARAMS` (quantity 2, Plaque2330, PVC3, isUVPrint, mode 1) без пометки источника.
- `docs/site/forms.md` — строка формы 69, страница калькулятора плакеток. Форму не открывать и не менять.
- Наценки уже разные, доску не править. `js_legacy/calc/common.json`: `marginMaterial` 0.6, `marginOperation` 0.55, `marginMin` 0.25, `marginPlaque` 0.5. `calc_service/data/common.json`: 0.66, 0.6, 0.3, 0.45. `Plaque2330.cost` = 315 и там, и в `calc_service/data/materials/plaque.json`.
- Остальное не открывать: весь `js_legacy/`, `docs/archive/`, `CLAUDE.md`, `bot_service/agent.py`.

## Scope

Один новый файл `scripts/run_js_calc.mjs`. Зависимостей npm и `package.json` нет, только встроенный Node. Код `js_legacy/` не править: скрипт читает его с диска.

Интерфейс:

- `node scripts/run_js_calc.mjs <имя> --params '<json>' [--data legacy|current]`
- Имя, которое скрипт считает в этой задаче: `calcPlaque`. Любое другое имя — ненулевой код и текст, что калькулятор не подключён. Чисел расчёта в stdout нет.
- JSON параметров `calcPlaque`: `quantity`, `plaque_id`, `material_id`, `application`, `mode`. В `options` ничего не класть: аргумент в `calcPlaque` не используется.
- `--data` по умолчанию `legacy`: прайс `js_legacy/material`, `js_legacy/equipment`, `js_legacy/calc/common.json`.
- `--data current`: тот же JS, но в памяти подменить числа прайса значениями из `calc_service/data` по тем же кодам (наценки `common` с теми же именами ключей, `cost` и ставки материалов и оборудования, которые читает этот прогон). Файлы не записывать. Кода нет в текущем прайсе — не выдумывать цену и не брать этот кейс в режиме `current`.
- Общего синхронизатора каталогов не писать. Поднимать только те `calc/*.js` и JSON, без которых выбранные кейсы `calcPlaque` не считаются. Список файлов — комментарий в шапке скрипта.
- stdout — один JSON и ничего больше. Ровно поля `cost`, `price`, `unit_price`, `time_hours`, `time_ready`, `weight_kg`. Соответствие: `time_hours` ← `time`, `time_ready` ← `timeReady`, `weight_kg` ← `weight`, `unit_price` как в `plaque.py`. Ошибки — в stderr.

Эталоны в `calc_service/tests/test_calculators/test_plaque.py`:

- Считать совпадением все шесть полей в допуске 0.03 на прогоне `--data current` против `PlaqueCalculator.execute` с теми же параметрами.
- В тест писать числа этого прогона. Пометка на каждом кейсе ровно один раз, буквально `JS, ДД.ММ.ГГГГ` (дата прогона).
- Прогон `--data legacy` в ожидаемые числа не писать.
- Кейсов 5–10. Среди них: два разных `quantity` (один ≥ 2), два `plaque_id`, два `material_id`, два `application` из `isUVPrint`, `isGrave`, `isSublimation`.
- Отдельно прогнать `noApplication`, `mode` 0 и `mode` 2. Совпало — можно включить в 5–10. Не совпало — в «Результат» как расхождение логики, в тест не добавлять и код не менять.
- Существующий `REF_PARAMS`: прогнать `--data current`. Попал в допуск — дописать пометку, числа не переписывать. Не попал — числа не подгонять, кейс в отчёт.
- Меньше пяти совпадений — допуск не ослаблять, калькулятор и JSON не трогать, пункт 5.6 в плане не отмечать, в «Требуется решение» таблица: кейс, поле, legacy, current, API, причина `цена` или `логика`.

Причина `цена`: расходятся именно те ставки и наценки, которые кейс читает (`js_legacy/material`, `js_legacy/equipment`, наценки `common`). Причина `логика`: ставки те же, а поле нет, либо это `mode` ≠ 1 или `noApplication`. Сверка по кодам кейса, не диффом всего каталога в коммит.

После зелёных критериев отметить в `docs/refactoring-plan.md` чекбокс 5.6 и строку «сделано ДД.ММ.ГГГГ, проверено: \<команда\>» по протоколу.

## Не-scope

- Любой калькулятор кроме `calcPlaque` (имя в скрипте есть, расчёта нет).
- Правки `plaque.py`, `calcTablets.js`, прочих `js_legacy/**`, JSON цен и наценок.
- Починка найденного расхождения логики, в том числе принудительного `modeProduction = 1`.
- Форма ezFC 69, WordPress, VDS, деплой.
- Отдельный файл кейсов вне `test_plaque.py`.

## Критерии приёмки

Каждый пункт — команда и ожидаемый результат. Параметры эталона ниже: `{"quantity":2,"plaque_id":"Plaque2330","material_id":"PVC3","application":"isUVPrint","mode":1}`.

- [x] `node scripts/run_js_calc.mjs calcPlaque --params '{"quantity":2,"plaque_id":"Plaque2330","material_id":"PVC3","application":"isUVPrint","mode":1}'` — код 0; stdout парсится как JSON с полями `cost`, `price`, `unit_price`, `time_hours`, `time_ready`, `weight_kg`, других полей нет
- [ ] `node scripts/run_js_calc.mjs calcPlaque --data current --params '{"quantity":2,"plaque_id":"Plaque2330","material_id":"PVC3","application":"isUVPrint","mode":1}'` — тот же вид JSON; `price` отличается от прогона без `--data current`; файлы в `js_legacy/` и `calc_service/data/` не изменились. Форма JSON и неизменность файлов есть, `price` совпадает (см. «Результат»).
- [x] `node scripts/run_js_calc.mjs notACalc --params "{}"` — код не 0; в stdout нет `cost` и `price`
- [x] `python -m pytest calc_service/tests/test_calculators/test_plaque.py -q` — код 0, `skipped` нет
- [ ] `python -c "import pathlib,re; t=pathlib.Path(r'calc_service/tests/test_calculators/test_plaque.py').read_text(encoding='utf-8'); m=re.findall(r'JS, \d{2}\.\d{2}\.\d{4}', t); print(len(m)); assert 5<=len(m)<=10"` — печатает число от 5 до 10, код 0. Печатает `0`, код 1: совпавших кейсов нет.
- [x] `python scripts/dev.py check` — код 0 (`make` в PATH может не быть)
- [ ] `git diff main --name-only` — только `scripts/run_js_calc.mjs`, `calc_service/tests/test_calculators/test_plaque.py`, `todo/calc-reconcile-plaque.md`, `docs/refactoring-plan.md`. В diff нет теста и плана: эталоны не добавлены, чекбокс 5.6 не отмечен.
- [x] `git diff main -- calc_service/data js_legacy` — пусто

## Проверки

- [x] `make check` (или `python scripts/dev.py check`) — зелёный вывод
- [x] Self-review — чеклист «Перед сдачей» в [AGENTS.md](../AGENTS.md)

## Риски

- Прод: нет. Страница формы 69 не открывается и не меняется.
- Цены: файлы не править. Деньги с `--data legacy` не эталон API. Расхождение ставки и расхождение формулы пишутся в отчёт раздельно.
- Формы: нет

## Режим

обычный

## Результат

Заполняет Implementer при сдаче.

- Ветка, PR или коммит: `task/calc-reconcile-plaque` от `main`
- Сделано: `scripts/run_js_calc.mjs` считает `calcPlaque` (legacy и `--data current` в памяти). Сетка кейсов (тиражи 1/2/10, три плакетки, PVC3/PVC5, четыре нанесения, mode 1; отдельно mode 0 и 2 на эталоне; сублимация ещё на AluminiumSU055) — ни один кейс не попал в допуск 0.03 по всем шести полям. `legacy == current` на каждом посчитанном поле: ставки, которые читает прогон, уже совпадают (в том числе наценки `common` после `8a64d09`). Калькулятор, JSON цен и чекбокс 5.6 не менялись. `REF_PARAMS` не переписывался и пометку `JS` не получил.
- Чем проверено:
  - `python scripts/dev.py check` — код 0: calc_service 433 passed, bot_service 81 passed.
  - `python -m pytest calc_service/tests/test_calculators/test_plaque.py -q` — `11 passed`, skipped нет.
  - Прогон эталона без `--data` и с `--data current`: оба `{"cost":2698.3,"price":6205.71,"unit_price":3102.86,"time_hours":1.32,"time_ready":35.67,"weight_kg":1.18}`, других полей нет. `price` не отличается.
  - `notACalc` — код 1, stdout пустой, stderr `Калькулятор не подключён: notACalc`.
  - Подсчёт пометок `JS, ДД.ММ.ГГГГ` — печатает `0`, код 1.
  - `git diff main -- calc_service/data js_legacy` — пусто.
- Не сделано и почему: в тест не добавлены эталоны (меньше пяти совпадений, допуск не ослаблялся). Пункт 5.6 в `docs/refactoring-plan.md` не отмечен. Критерий «`price` с `--data current` отличается от legacy» не выполнен: подмена ставок есть, но числа те же.
- Требуется решение: как закрывать 5.6, если формулы не сходятся при одинаковых ставках, и нужен ли критерий «price отличается», когда прайсы уже выровнены. Таблица расхождений — ниже. Причина везде `логика`: legacy и current совпадают. `цена` не встретилась.

| Кейс | Поле | legacy | current | API | Причина |
| --- | --- | --- | --- | --- | --- |
| qty 2, Plaque2330, PVC3, isUVPrint, mode 1 (REF) | cost | 2698.3 | 2698.3 | 2093 | логика |
| тот же | price | 6205.71 | 6205.71 | 4977 | логика |
| тот же | unit_price | 3102.86 | 3102.86 | 2488.5 | логика |
| тот же | time_hours | 1.32 | 1.32 | 0.37 | логика |
| тот же | time_ready | 35.67 | 35.67 | 32.74 | логика |
| тот же, mode 0 | cost | 2698.3 | 2698.3 | 2093 | логика |
| тот же, mode 0 | price | 6205.71 | 6205.71 | 4977 | логика |
| тот же, mode 0 | unit_price | 3102.86 | 3102.86 | 2488.5 | логика |
| тот же, mode 0 | time_hours | 1.32 | 1.32 | 0.37 | логика |
| тот же, mode 0 | time_ready | 35.67 | 35.67 | 56.74 | логика |
| тот же, mode 2 | cost | 2698.3 | 2698.3 | 2469 | логика |
| тот же, mode 2 | price | 6205.71 | 6205.71 | 5850 | логика |
| тот же, mode 2 | unit_price | 3102.86 | 3102.86 | 2925 | логика |
| тот же, mode 2 | time_hours | 1.32 | 1.32 | 0.58 | логика |
| тот же, mode 2 | time_ready | 35.67 | 35.67 | 17.16 | логика |
| qty 2, Plaque2330, PVC3, isGrave, mode 1 | cost | 9497.1 | 9497.1 | 1184 | логика |
| тот же | price | 20224.31 | 20224.31 | 2691 | логика |
| тот же | unit_price | 10112.16 | 10112.16 | 1345.5 | логика |
| тот же | time_hours | 8.9 | 8.9 | 0.29 | логика |
| тот же | time_ready | 42.7 | 42.7 | 16.58 | логика |
| qty 2, Plaque2330, PVC3, noApplication, mode 1 | time_ready | 0 | 0 | 8 | логика |
| qty 2, Plaque2330, PVC3, isSublimation, mode 1 | cost | NaN | NaN | 1380 | логика |
| qty 2, Plaque2330, AluminiumSU055, isSublimation, mode 1 | cost | 1696.08 | 1696.08 | 993 | логика |
| тот же | price | 4018.24 | 4018.24 | 2391 | логика |
| тот же | unit_price | 2009.12 | 2009.12 | 1195.5 | логика |
| тот же | time_hours | 0.58 | 0.58 | 0 | логика |
| тот же | time_ready | 18.55 | 18.55 | 8 | логика |
| тот же | weight_kg | 1.19 | 1.19 | 1.15 | логика |
| qty 2, Plaque1520, PVC3, isUVPrint, mode 1 (ближайший по цене) | time_hours | 0.83 | 0.83 | 0.3 | логика |
| тот же | time_ready | 34.21 | 34.21 | 32.6 | логика |

### Разбор расхождений, 28.10.2026

Прод и браузер открывались по прямому указанию человека, только чтение.

- Форма 69, элемент `cjsCalc` (id 2783): `insaincalc.calcPlaque({{numN}}, plaqueID, materialID, applicationID, new Map(), {{rdoModeProduction}})`. Порядок аргументов тот же, что в `run_js_calc.mjs`, скрипт не менялся. На экран форма выводит `insaincalc.round(price, n)`. В списке материалов формы нет `PVC3`: там `AcrylWhite3`, `AcrylColor3`, `Plywood3`, `AluminiumSU055`, `ZENOMARKLASER`, `SHENGWEI`, `ROWMARKLASERMAX`, `ROWMARKLASERMAX3`. Режимы только 1 и 2.
- `/var/www/insain.ru/icalc/`: `calcTablets.js`, `calcLaser.js`, `calcUVPrint.js`, `calc/common.json`, `hardsheet.json`, `laser.json` по md5 совпадают с `js_legacy`. На проде отличаются только записи, которые кейсы не читают: `Plaque3038` в `misc.json`, `DTFTransfer` в `printer.json`, ветка dtf в `calcHeatPress.js`, точки с запятой в `icdc_ls.js`.
- Третий эталон: `insaincalc.calcPlaque` на странице https://insain.ru/catalog/kalkulyator-nagradnyh-plaketok/ (qty 2, Plaque2330, mode 1). На PVC3 УФ дал 2698.3 / 6205.71 / 1.32 / 35.67 / 1.18, гравировка — 9497.1 / 20224.31 / 8.9 / 42.7 / 1.18, это совпадает со скриптом. Через UI формы на AcrylWhite3 УФ — 6 620 руб., 1.37 кг. Это `round(6618.96)`, скрипт даёт 6618.96. Гравировка — 20 640 руб., это `round(20637.56)`, скрипт даёт 20637.56. Прод-API (`POST /api/v1/calc/plaque`) равен локальному `PlaqueCalculator`.

Слагаемые пластины (qty 2, Plaque2330, PVC3, mode 1; пластина 195×265; основа 630 / 1045.8 у обоих):

| Кейс | Слагаемое | JS | Python | Причина |
| --- | --- | --- | --- | --- |
| УФ | материал и резка | `calcLaser` с `isCutLaser`: материал по площади 0.02 листа = 93.79, рез 920 мм 0.09 ч, подготовка 0.2 ч → 553.3 / 810 / 0.29 ч | `tablets.py`, ветка не-laser: 1 целый лист × `cost` 750 (это руб./м²) = 750 / 1245, лазерной резки нет, 0 ч | перенос: `tablets.py` при `uv` не вызывает лазерную резку и умножает руб./м² на целые листы |
| УФ | параметры печати | `RimalSuvUV`, resolution 2, `4+1` | resolution 0, `4+0`: `tablets.py` их не передаёт | перенос: `tablets.py` / `plaque.py` |
| УФ | скорость печати | `meterPerHour[2]` 0.3 / 2 = 0.15 м²/ч | `meter_per_hour` 0, таблицы нет → запасное 1.0 м²/ч при любом resolution | перенос: загрузчик принтера не читает массив `meterPerHour` |
| УФ | расходники | `costProcess[0] + [1]` = 1300 + 800 = 2100 руб./м² | один `cost_process` 1300 на все цвета (при `4+1` было бы 2600) | перенос: из `costProcess` берётся только первый элемент |
| УФ | объём печати | по раскладке на столе 0.1061 м² | площадь × n 0.1034 м² | перенос, упрощение (около 3 %) |
| УФ | печать итого | 1515 / 2424, 1.03 ч | 713 / 1141, 0.37 ч; с параметрами JS — 970 / 1552, 0.48 ч | сумма трёх строк выше |
| гравировка | гравировка | `isGrave` 2 + `isGraveFill` на всю пластину: 0.0517 м² × 2 / 0.012 м²/ч = 8.61 ч, гравировка 1098.31, оператор 6857 → 8867.1 / 12902 / 8.9 ч | только резка: 553.3 / 810 / 0.29 ч | перенос: `tablets.py` при `laser` не передаёт `is_grave` / `is_grave_fill`. `LaserCalculator` с этими параметрами даёт ровно JS 8867.1 / 12902 / 8.9 / 24.9 |
| оба | `time_ready` пластины | `calcTablets`: time + max(timeReady), затем `calcPlaque` ещё раз + time (время считается дважды) | `tablets.py`: max(time_ready), `plaque.py`: + time (один раз) | перенос, без пометки о намеренности. УФ 34.35 против 32.37 |
| оба | вес пластины | `Math.ceil` → 0.18 | `round` → 0.17 | перенос, в допуске |
| оба | итоговая цена | без округления 6205.71 | `math.ceil` 4977 | перенос, в допуске |

Вывод: ошибок скрипта нет, его вход и выход совпали с формой на сайте. Все расхождения — ошибки переноса в Python, свидетельств намеренного изменения в коде нет. Гравировка и резка — ошибки в `tablets.py`: не передаются параметры, а `LaserCalculator` перенесён верно. В УФ ошибки в `tablets.py` (материал, резка, параметры печати) и в чтении записи принтера `uv_print.py` (`meterPerHour`, `costProcess`). Совпавших кейсов нет, `test_plaque.py` не менялся. Чинить — отдельная задача: код калькулятора и цены в scope не входят.

Требуется решение (бизнес): JS считает гравировку заливкой всей пластины в максимальном разрешении. Это 8.6 ч на две плакетки, на сайте 20 240–20 640 руб. Если такая цена неверна, то при починке `tablets.py` эталоном гравировки JS брать нельзя.

У REF и mode 0/2 вес в допуске (1.18 против 1.17). У noApplication в допуске все поля, кроме `time_ready`. У Plaque1520×2 УФ в допуске cost/price/unit_price/weight. Сублимация на PVC не отдаёт число: `material.size` — список листов, `size[0] * size[1]` даёт NaN.
