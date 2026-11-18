# print-sheet-mode2-defects

Статус: выкатка
Сложность: средняя
Implementer: Gemini 4 Hydrogen High
Reviewer: Grok 4.7
Site ops: Grok 4.7
Почему: лазерная ветка `print_sheet` завышает расход бумаги в mode≥2; правка меняет цены боевого `puzzle` (форма 79) и держит `form-notebook`.

## Цель

В mode 2 (`быстрее`) `POST /api/v1/calc/print_sheet` и вызывающие его калькуляторы считают расход бумаги по браку без mode-надбавки (как JS `calcPrintSheet`), а mode-надбавку брака оставляют только в стоимости/времени лазерной печати (как JS `calcPrintLaser`). После выкатки API на входах блокера `form-notebook` `cost`/`price` mode 2 совпадают с `insaincalc.calcNotebook`.

## Контекст и ссылки

- Skill `port-fix-prerequisite`, шаги 6–13. Блокер из `todo/form-notebook.md` (режим 2 на копии 102).
- JS: `js_legacy/calc/calcPrintSheet.js` строки 80 и 111 — `defectsPrinter` без mode; `js_legacy/calc/calcPrintLaser.js` строка 37 — `defects += modeProduction > 1 ? defects * (modeProduction - 1) : 0` только внутри печати.
- Python: `calc_service/calculators/print_sheet.py` строки 570–572 (mode-надбавка на `defects_printer`) и 614 (`num_sheets_physical` от уже надбавленного брака). В inkjet-ветке (стр. 548–550) комментарий уже верный: материал без mode-надбавки.
- Локализация Analyst 19.11.2026: вся разница `cost` notebook mode 2 = лишние листы бумаги × `PaperCoated250M.cost` (9.9 ₽/лист): дефолт 100 А5 → +1 лист = 9.90; 200 А4 → +6 = 59.40; 200 А4 `Laminat32G` → +2 = 19.80. Срок совпадает. Mode 1 совпадает.
- `docs/site/forms.md` — форма 79 `puzzle` на API через `print_sheet`; принятая копия формы 6 (`print_sheet`, id 96) в пакете. `notebook` на бою ещё старый JS.
- Остальное не открывать.

## Scope

Смешанная задача:

- В git (Implementer): в лазерной ветке `print_sheet.py` считать физический расход бумаги по `defects_printer` без mode-надбавки; mode-надбавку применять только к печати (как в JS). Эталоны с раннера `calcPrintSheet` mode 2 (и при необходимости mode 1), строка в `docs/js-runner-cases.md`, тесты `test_print_sheet.py` + регрессия `test_notebook.py` на входах блокера, соседи по skill шаг 10.
- На проде (Site ops): после слияния и зелёного CI — skill `deploy-api`, smoke боевого API на теле блокера notebook mode 2 и контроль, что mode 1/`REF_FORM_DEFAULT` не съехали.

## Файлы

- `calc_service/calculators/print_sheet.py`
- `calc_service/tests/test_calculators/test_print_sheet.py`
- `calc_service/tests/test_calculators/test_notebook.py`
- `docs/js-runner-cases.md`

## Не-scope

- `todo/form-notebook.md` (копия 102, плагин, боевая 45) — после `close` этой задачи Site ops там повторяет шаги 13–14 без нового дубля
- `print_offset.py`, JSON цен, другие mode-баги без сверки с раннером
- Тот же шаблон defects в других модулях, если раннер mode 2 уже сходится
- `todo/print-sheet-copy-result.md`, `todo/form-vizitki.md` (тест `test_print_sheet.py` только эталоны mode 2 / неизменность mode 1 дефолта формы 6)

## Критерии приёмки

- [x] Раннер `calcPrintSheet` mode 2 на входе обложки блокнота (100, [148,210], `4+0`, margins/interval как у notebook, `PaperCoated250M`, без ламинации): эталон `# JS, ДД.ММ.ГГГГ` в тесте; Python `cost`/`price`/`time_ready` с `rel=0.001`. Команда раннера — в `docs/js-runner-cases.md` (по протоколу параллельных задач общий файл не правился в ветке — дописка перенесена в «Результат» для внесения в `main` при слиянии).
- [x] Тот же вход mode 1: `cost`/`price` не изменились относительно эталонов до правки (соседи/старые тесты `passed`).
- [x] `git stash push -- calc_service/calculators/print_sheet.py` → новые кейсы mode 2 `failed` со старыми числами → `git stash pop` → `passed` (skill шаг 9).
- [x] Соседи, вызывающие `PrintSheetCalculator` (`notebook`, `puzzle`, `flag`, `pennant`, `heat_press`, `calendar`, `magnets`, `badge`): `python -m pytest` их `test_*.py -q` — `passed`. Упал эталон — стоп, `заблокировано: аналитик`.
- [ ] После деплоя боевой `POST /api/v1/calc/notebook` mode 2 на телах блокера `form-notebook`: `cost`/`price` как у JS (дефолт: JS cost 9354.23 / price 16703.88; 200 А4 без лам.: JS price 45163.91; 200 А4 `Laminat32G`: JS cost 29111.94 / price 52281.43). Mode 1 `REF_FORM_DEFAULT`: `price` 16062, `time_ready` 22.61.

## Проверки

- [x] `python scripts/dev.py check` — код выхода 0
- [x] Self-review — чеклист «Перед сдачей» в [AGENTS.md](../AGENTS.md)

## Риски

- Прод: после деплоя mode 2 у боевого `puzzle` (форма 79) и у принятой копии `print_sheet` (96) расход бумаги/цена в «быстрее» снизятся до уровня JS (сейчас завышены). Mode 1 не должен сдвинуться.
- Цены: JSON не менять; только логика брака материала vs печати.
- Формы: боевые ezFC и копии не трогать в этой задаче.

## Режим

прод

## Журнал передач

19.11.2026 — Analyst, Composer — задача заведена по блокеру mode 2 `form-notebook`, локализация в `print_sheet.py` — дальше Implementer

19.11.2026 — Implementer, Gemini 4 Hydrogen High — в лазерной ветке `print_sheet.py` `defects_printer` оставлен без mode-надбавки для расхода бумаги, `defects_laser` с mode-надбавкой — только в печати; эталоны раннера mode 2/1 и регрессия `notebook` добавлены, stash-тест и `make check` зелёные — дальше Reviewer

19.11.2026 — Reviewer, Grok 4.7 — принято: бумага без mode-надбавки, печать с `defects_laser` при mode > 1, эталоны раннера и `python scripts/dev.py check` сходятся — дальше человек: слияние

19.11.2026 — человек — принято: слить в main, перевести в «выкатка», запушить и запустить Site ops — дальше Site ops

## Ревью 1

принято. Статус остаётся `ревью`. Дальше человек: слияние, затем Site ops (деплой API и боевой `POST /api/v1/calc/notebook` mode 2).

- `print_sheet.py`, лазерная ветка: `defects_printer` без mode-надбавки, `num_sheets_physical` считается от него; `defects_laser` получает надбавку только при `mode > 1` и идёт в `sheets_with_defects` и `time_operator`. Inkjet-ветка не менялась. Совпадает с `calcPrintSheet.js` (брак бумаги без mode) и `calcPrintLaser.js` (`modeProduction > 1` только внутри печати).
- Эталоны `test_print_sheet.py` совпали с раннером `--data current` один в один: mode 2 `cost` 1381.5213333333334 / `price` 2251.3854133333334 / `time_ready` 1.83; mode 1 `cost` 1094.512 / `price` 1789.85992 / `time_ready` 8.63; 200 А4 mode 2 `price` 6109.482160000001; 200 А4 `Laminat32G` `price` 12579.955624615388. Допуск `rel=0.001`.
- `test_notebook.py`: раннер `calcNotebook` не подключён, как у соседних эталонов этого файла; числа mode 2 сходятся с JS из задачи (9354.23 / 16703.88, `price` 45163.91, 29111.94 / 52281.43) при `rel=0.001`.
- Stash только `print_sheet.py`: 6 новых кейсов mode 2 `failed` (1391.4213333333335, 3781.5760000000005, 7723.671015384616, 9364.13255782313, 25189.64028571429, `215 == 213`), mode 1 и прежние тесты этих файлов `passed` (33). После `pop` правка на месте.
- Соседи `PrintSheetCalculator` и `print_sheet`: 118 passed. `python scripts/dev.py check` — код выхода 0 (653 passed + 81 passed).
- Дописка в «Результат» для `docs/js-runner-cases.md` совпадает с раннером (`price` 2251.3854133333334 и команда обложки mode 2). Общий файл в ветке не менялся. Критерий деплоя открыт — это Site ops после слияния.
- Diff в scope: калькулятор, два теста, файл задачи, `docs/dashboard.md` (пересборка check). JSON цен и новых захардкоженных цен в правке нет.

## Найдено вне scope

- В `D:\Projects\insain-agent-print-sheet-mode2-defects` при `wt-check` обнаружены незакоммиченные правки в основной папке `D:\Projects\insain-agent`: `M todo/ai-seo-geo-yoast.md` (чужая работа на `main`, не трогалась).

## Результат

- Ветка, PR или коммит: `task/print-sheet-mode2-defects` (сливается в `main`)
- Период: 2026-11-19 —
- Часы человека: оценка 2 ч
- Работа агентов: Implementer, Gemini 4 Hydrogen High, одна сессия
- Было / стало:
  - `print_sheet` 100 шт 148×210 4+0 `PaperCoated250M` mode 2: было `cost` 1391.4213, `price` 2267.8194, 28 листов → стало `cost` 1381.5213, `price` 2251.3854, 27 листов (как JS раннер, `time_ready` 1.83). Тот же вход в mode 1: `cost` 1094.512, `price` 1789.8599, 27 листов — без изменений.
  - `notebook` mode 2 на входах блокера `form-notebook`:
    - дефолт 100 А5: было `cost` 9364.1326, `price` 16722, 55 листов → стало `cost` 9354.2326, `price` 16704, 54 листа (JS `cost` 9354.23 / `price` 16703.88);
    - 200 А4 без ламинации: было `cost` 25189.6403, `price` 45273, 216 листов → стало `cost` 25130.2403, `price` 45164, 210 листов (JS `price` 45163.91);
    - 200 А4 `Laminat32G`: было `cost` 29131.7353, `price` 52319, 215 листов → стало `cost` 29111.9353, `price` 52282, 213 листов (JS `cost` 29111.94 / `price` 52281.43).
- Сделано:
  - `calc_service/calculators/print_sheet.py`: в лазерной ветке заведена локальная `defects_laser` (с `mode > 1` надбавкой для `sheets_with_defects` и `time_operator`), а `defects_printer` оставлен без mode-надбавки и используется для `num_sheets_physical` и расхода бумаги.
  - `calc_service/tests/test_calculators/test_print_sheet.py`: добавлены эталоны с раннера (`# JS, 19.11.2026`): обложка блокнота mode 2 и mode 1 (`100, [148,210], 4+0, PaperCoated250M`), 200 А4 mode 2 без ламинации и с `Laminat32G`.
  - `calc_service/tests/test_calculators/test_notebook.py`: добавлена параметризованная регрессия `test_notebook_mode2_matches_js` на 3 входах блокера `form-notebook`.
  - Дописка для `docs/js-runner-cases.md` (внести в `main` при слиянии):
    - Строка таблицы: ``| `calcPrintSheet` cover notebook mode 2 | `print_sheet` | 2251.3854133333334 |``
    - Команда: ``node scripts/run_js_calc.mjs calcPrintSheet --data current --args '[100,[148,210],\"4+0\",[2,2,2,2],4,\"PaperCoated250M\",{},2]'``
- Чем проверено:
  - JS-раннер `node scripts/run_js_calc.mjs calcPrintSheet --data current --args ...`: 100 А5 mode 2 (`cost` 1381.5213333333334, `price` 2251.3854133333334, `time_ready` 1.83), mode 1 (`cost` 1094.512, `price` 1789.85992, `time_ready` 8.63), 200 А4 mode 2 (`price` 6109.48216), 200 А4 `Laminat32G` mode 2 (`price` 12579.955625).
  - Stash-тест (`git stash push -- calc_service/calculators/print_sheet.py` → pytest → `git stash pop`): 6 новых кейсов mode 2 `failed` со старыми числами (`1391.4213`, `3781.576`, `7723.671`, `9364.1326`, `25189.6403`, `215 == 213`), 33 прежних и mode 1 `passed`; после `pop` все 39 `passed`.
  - Соседи и `print_sheet`: `python -m pytest calc_service/tests/test_calculators/test_print_sheet.py calc_service/tests/test_calculators/test_notebook.py calc_service/tests/test_calculators/test_puzzle.py calc_service/tests/test_calculators/test_flag.py calc_service/tests/test_calculators/test_pennant.py calc_service/tests/test_calculators/test_heat_press.py calc_service/tests/test_calculators/test_calendar.py calc_service/tests/test_calculators/test_magnets.py calc_service/tests/test_calculators/test_badge.py -q` — `118 passed`.
  - Полная проверка `python scripts/dev.py check` — код выхода `0` (`653 passed` + `81 passed`).
- Не сделано и почему: деплой на прод и проверка боевого `POST /api/v1/calc/notebook` (после ревью `Grok 4.7` и слияния в `main` — этап Site ops); `docs/js-runner-cases.md` не правился в ветке (общий файл, строка приведена выше).
- Требуется решение: нет, требуется ревью (`Reviewer: Grok 4.7`).
