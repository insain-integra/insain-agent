# print-sheet-big-sheet

Статус: выкатка
Сложность: высокая
Implementer: Gemini 4 Hydrogen High
Reviewer: Grok 4.7
Site ops: Grok 4.7
Почему: лист больше принтера в `print_sheet` считается как целый лист материала; эталон — старый `calcPrintSheet`, цены копий на API после выкатки меняются.

## Цель

Для визитки 100 шт, 90×50, 4+0, поля `[2,2,2,2]`, интервал 4, режим 1, материал `MAJESTIC` ответ `POST /api/v1/calc/print_sheet` совпадает со старым `calcPrintSheet`: число листов материала — сколько печатных листов 320×450 помещается на лист 1020×720, плюс предварительная резка большого листа. Сейчас API отдаёт `price` 4522.503 и 6 листов 1020×720. Дефолт мелованной 300 г (`price` 1011.403, 6 листов 320×450) не сдвигается. Боевые формы 6 и 19 остаются на старом JS.

## Контекст и ссылки

- `js_legacy/calc/calcPrintSheet.js` — ветка `layoutOnPrinter.num == 0` (строки около 54–68) и `costMaterial` (около 111). Это эталон.
- `calc_service/calculators/print_sheet.py` — сейчас при том же условии `layout_on_material` считается листом принтера по самому себе, `cost_cut` предварительной резки остаётся 0.
- `calc_service/calculators/cut_roller.py` и гильотина — вызывать готовые, не переписывать.
- `scripts/js_port_gaps_allowed.txt` — строка `calcPrintSheet call calcCutRoller`.
- Копия, на которой это видно: форма 107, черновик 2586903. Боевая страница визиток на старом JS.
- Остальное не открывать.

## Scope

- В git (Implementer): когда лист материала не входит в `maxSize` принтера `KMBizhubC220`, печатный лист — этот `maxSize`. Число листов материала — как в JS: печатные листы раскладываются на полном `material.size`, себестоимость материала — `cost * ceil(n * (1 + defects)) / layout.num`, не `cost * ceil(n / layout)`.
- Предварительная резка большого листа — та же развилка, что в JS: лист входит в гильотину → уже существующий расчёт гильотины; не входит → `CutRollerCalculator` с резаком `KWTrio3026`. Рез визиток из печатного листа, который уже есть в Python, не подменять этой резкой.
- Эталон одного входа снять раннером и записать в тест с пометкой `# JS, ДД.ММ.ГГГГ`. Тест падает на текущем ответе `price` 4522.503 и 6 листах 1020×720.
- Если вызов роликового реза появился в `print_sheet.py`, строку `calcPrintSheet call calcCutRoller` убрать из `scripts/js_port_gaps_allowed.txt`. Соседние строки файла не трогать.
- На проде (Site ops, после слияния и зелёного CI): skill `deploy-api`. Плагин не выкладывать. Формы ezFC не менять.

## Файлы

- `calc_service/calculators/print_sheet.py`
- `calc_service/tests/test_calculators/test_print_sheet.py`
- `scripts/js_port_gaps_allowed.txt`

## Не-scope

- `wp-plugin/forms/print_sheet.js`, копии 96 и 107, боевые формы 6 и 19, JSON цен
- `calc_service/calculators/cut_roller.py` и калькулятор гильотины — только вызов
- Строка `calcPrintSheet call calcPrintLaser` в allowed
- `SUPERWAIS` отдельным кейсом не заводить: тот же размер 1020×720, та же ветка
- Нулевая цена «350гр» + «Евро» + 4+4 — другая ветка (изделие не входит в лист), уже в `BACKLOG.md`
- `todo/print-sheet-copy-result.md`, `todo/forms-batch-switch.md`

## Критерии приёмки

- [x] `node scripts/run_js_calc.mjs calcPrintSheet --data current --args '[100,[90,50],"4+0",[2,2,2,2],4,"MAJESTIC",{},1]'` — снять `price`, `cost`, число и размер листов материала. Эти числа лежат в тесте с `# JS,`.
- [x] `python -m pytest calc_service/tests/test_calculators/test_print_sheet.py -q` — `passed`, `failed` нет. Кейс `MAJESTIC` совпадает с раннером и падает, если вернуть расчёт «6 листов 1020×720 / price 4522.503». Дефолт мелованной 300 г по-прежнему `price` 1011.403 и 6 листов 320×450.
- [ ] После выкатки `POST https://insain.ru/api/v1/calc/print_sheet` с телом этого кейса (`quantity` 100, `width` 90, `height` 50, `color` `4+0`, `margins` `[2,2,2,2]`, `interval` 4, `material_id` `MAJESTIC`, `mode` 1) → 200 и тот же `price`, что в тесте. Дефолт `PaperCoated300M` на том же размере → `price` 1011.403.
- [ ] HTML https://insain.ru/catalog/vizitki/ по-прежнему содержит `calcPrintSheet`, вызова `calcApi` нет.

## Проверки

- [x] `python scripts/dev.py check` — код выхода 0
- [x] Self-review — чеклист «Перед сдачей» в [AGENTS.md](../AGENTS.md)

## Риски

- Прод: выкатка API меняет цену копий, которые уже зовут `print_sheet` (форма 107 и копия 96). Боевые страницы на старом JS цену не меняют.
- Цены: JSON не менять. Меняется только формула ветки «лист больше принтера».
- Формы: записи в ezFC нет.

## Режим

прод

## Журнал передач

21.11.2026 — Analyst, Grok 4.7 — задача заведена: на копии 107 Маджестик считает 6 листов 1020×720 — дальше Implementer
21.11.2026 — Implementer, Gemini 4 Hydrogen High — исправлена ветка большого листа в print_sheet.py, добавлены тесты MAJESTIC (JS, 21.11.2026) и предреза, снят пропуск calcCutRoller, check зелёный — дальше Reviewer
21.11.2026 — Reviewer, Grok 4.7 — принято: MAJESTIC совпал с раннером (price 1962.9526181818183, 2 листа 1020×720), pytest 32 passed, пропуск calcCutRoller снят — дальше человек
21.11.2026 — человек — принято: слить в main и выкатить API, формы 6 и 19 не переключать — дальше Site ops

## Найдено вне scope

- Гильотинное плечо буквального JS: `calcCutGuillotine(num, maxSize принтера, material.size, id, mode)` кладёт mode в аргумент margins, и предварительный рез выходит с нулевой ценой. Python вызывает тот же калькулятор с margins 0 и mode отдельно. Для EPSONWF7610 и PaperCoated300M, 100 шт 90×50, это +27 к cost, +44 к price и +0.02 ч. На дефолтном KMBizhubC220 ни один размер из `sheet.json` в эту ветку не попадает: 320×450 входит в принтер, 1000×700 и 1020×720 идут на роликовый. Эталон задачи — роликовый MAJESTIC, он с раннером совпал.

## Ревью 1

принято. Статус остаётся `ревью`: POST на боевой API и HTML визиток — после слияния и выкатки, это Site ops.

- Раннер `calcPrintSheet` для `[100,[90,50],"4+0",[2,2,2,2],4,"MAJESTIC",{},1]`, `--data current`: cost 1202.0618181818181, price 1962.9526181818183, time_hours 0.34, time_ready 8.5, материал MAJESTIC — 2 листа 1020×720. Те же числа в тесте с пометкой `# JS, 21.11.2026`. Вес в тесте 0.1305 (изделия), в JS 0.2088 (лист) — как в комментарии теста.
- Старый ответ price 4522.503 и 6 листов 1020×720 эти утверждения не проходят: тест ждёт price ~1962.95 и quantity 2.
- Дефолт мелованной 300 г не сдвинут: `test_form19_default_print_sheet` по-прежнему ждёт price 1011.4034181818182 и 6 листов 320×450.
- `python -m pytest calc_service/tests/test_calculators/test_print_sheet.py -q` — 32 passed.
- Строка `calcPrintSheet call calcCutRoller` снята, сосед `calcPrintSheet call calcPrintLaser` на месте. `python scripts/js_port_gaps.py --check` — ok.
- Себестоимость материала — `cost * ceil(n * (1 + defects)) / layout.num`. Предрез роликовым KWTrio3026 не подменяет рез изделий с печатного листа.
- Прод-критерии этого круга не закрывают сдачу кода: деплоя ещё нет.
- Инварианты: цен в Python нет, обязательные поля ответа на месте, diff внутри файлов задачи. `docs/dashboard.md` пересобран вместе со статусом.

## Результат

- Ветка, PR или коммит: `task/print-sheet-big-sheet`
- Период: 2026-11-21 —
- Часы человека: оценка 4 ч
- Работа агентов: Implementer (Gemini 4 Hydrogen High)
- Было / стало: `MAJESTIC` 100 шт 90×50 было `price` 4522.503 и 6 листов 1020×720; стало `price` 1962.9526181818183 (`cost` 1202.0618181818181, `time_hours` 0.34, `time_ready` 8.5, `weight_kg` 0.1305) и 2 листа 1020×720 (совпадает с раннером `calcPrintSheet`, кроме веса по изделиям).
- Сделано: в `calc_service/calculators/print_sheet.py` при `layout_on_printer["num"] == 0` печатные листы `max_printer` раскладываются на полном `material_size`, себестоимость материала считается как `cost * ceil(n * (1 + defects)) / layout.num`, добавлена предварительная резка (`CutGuillotineCalculator` при входе в гильотину `KWTrio3971`, иначе `CutRollerCalculator` с `KWTrio3026`) с учётом `price_cut` в `price`; в `calc_service/tests/test_calculators/test_print_sheet.py` добавлены тесты `test_print_sheet_big_sheet_majestic` и `test_print_sheet_big_sheet_guillotine_precut`; из `scripts/js_port_gaps_allowed.txt` убрана строка `calcPrintSheet call calcCutRoller`.
- Чем проверено: `node scripts/run_js_calc.mjs calcPrintSheet --data current --args '[100,[90,50],"4+0",[2,2,2,2],4,"MAJESTIC",{},1]'` (`cost` 1202.0618, `price` 1962.9526); `python -m pytest calc_service/tests/test_calculators/test_print_sheet.py -q` (32 passed); `python scripts/dev.py check` (код 0: `calc_service` 778 passed, `bot_service` 81 passed).
- Не сделано и почему: деплой API и проверка на проде выполняются после ревью и слияния в `main` (роль Site ops).
- Требуется решение: боевые формы 6 и 19 не переключать. После приёмки цены на API копия 107 подхватит её без новой записи JS.
