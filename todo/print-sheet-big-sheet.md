# print-sheet-big-sheet

Статус: черновик
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

- [ ] `node scripts/run_js_calc.mjs calcPrintSheet --data current --args '[100,[90,50],"4+0",[2,2,2,2],4,"MAJESTIC",{},1]'` — снять `price`, `cost`, число и размер листов материала. Эти числа лежат в тесте с `# JS,`.
- [ ] `python -m pytest calc_service/tests/test_calculators/test_print_sheet.py -q` — `passed`, `failed` нет. Кейс `MAJESTIC` совпадает с раннером и падает, если вернуть расчёт «6 листов 1020×720 / price 4522.503». Дефолт мелованной 300 г по-прежнему `price` 1011.403 и 6 листов 320×450.
- [ ] После выкатки `POST https://insain.ru/api/v1/calc/print_sheet` с телом этого кейса (`quantity` 100, `width` 90, `height` 50, `color` `4+0`, `margins` `[2,2,2,2]`, `interval` 4, `material_id` `MAJESTIC`, `mode` 1) → 200 и тот же `price`, что в тесте. Дефолт `PaperCoated300M` на том же размере → `price` 1011.403.
- [ ] HTML https://insain.ru/catalog/vizitki/ по-прежнему содержит `calcPrintSheet`, вызова `calcApi` нет.

## Проверки

- [ ] `python scripts/dev.py check` — код выхода 0
- [ ] Self-review — чеклист «Перед сдачей» в [AGENTS.md](../AGENTS.md)

## Риски

- Прод: выкатка API меняет цену копий, которые уже зовут `print_sheet` (форма 107 и копия 96). Боевые страницы на старом JS цену не меняют.
- Цены: JSON не менять. Меняется только формула ветки «лист больше принтера».
- Формы: записи в ezFC нет.

## Режим

прод

## Журнал передач

21.11.2026 — Analyst, Grok 4.7 — задача заведена: на копии 107 Маджестик считает 6 листов 1020×720 — дальше Implementer

## Найдено вне scope

-

## Результат

- Ветка, PR или коммит:
- Период: 2026-11-21 —
- Часы человека: оценка 4 ч
- Работа агентов:
- Было / стало: `MAJESTIC` 100 шт 90×50 сейчас `price` 4522.503 и 6 листов 1020×720. Стало — числа раннера `calcPrintSheet`.
- Сделано:
- Чем проверено:
- Не сделано и почему:
- Требуется решение: боевые формы 6 и 19 не переключать. После приёмки цены на API копия 107 подхватит её без новой записи JS.
