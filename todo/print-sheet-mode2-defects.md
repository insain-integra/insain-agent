# print-sheet-mode2-defects

Статус: черновик
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

- [ ] Раннер `calcPrintSheet` mode 2 на входе обложки блокнота (100, [148,210], `4+0`, margins/interval как у notebook, `PaperCoated250M`, без ламинации): эталон `# JS, ДД.ММ.ГГГГ` в тесте; Python `cost`/`price`/`time_ready` с `rel=0.001`. Команда раннера — в `docs/js-runner-cases.md`.
- [ ] Тот же вход mode 1: `cost`/`price` не изменились относительно эталонов до правки (соседи/старые тесты `passed`).
- [ ] `git stash push -- calc_service/calculators/print_sheet.py` → новые кейсы mode 2 `failed` со старыми числами → `git stash pop` → `passed` (skill шаг 9).
- [ ] Соседи, вызывающие `PrintSheetCalculator` (`notebook`, `puzzle`, `flag`, `pennant`, `heat_press`, `calendar`, `magnets`, `badge`): `python -m pytest` их `test_*.py -q` — `passed`. Упал эталон — стоп, `заблокировано: аналитик`.
- [ ] После деплоя боевой `POST /api/v1/calc/notebook` mode 2 на телах блокера `form-notebook`: `cost`/`price` как у JS (дефолт: JS cost 9354.23 / price 16703.88; 200 А4 без лам.: JS price 45163.91; 200 А4 `Laminat32G`: JS cost 29111.94 / price 52281.43). Mode 1 `REF_FORM_DEFAULT`: `price` 16062, `time_ready` 22.61.

## Проверки

- [ ] `python scripts/dev.py check` — код выхода 0
- [ ] Self-review — чеклист «Перед сдачей» в [AGENTS.md](../AGENTS.md)

## Риски

- Прод: после деплоя mode 2 у боевого `puzzle` (форма 79) и у принятой копии `print_sheet` (96) расход бумаги/цена в «быстрее» снизятся до уровня JS (сейчас завышены). Mode 1 не должен сдвинуться.
- Цены: JSON не менять; только логика брака материала vs печати.
- Формы: боевые ezFC и копии не трогать в этой задаче.

## Режим

прод

## Журнал передач

19.11.2026 — Analyst, Composer — задача заведена по блокеру mode 2 `form-notebook`, локализация в `print_sheet.py` — дальше Implementer

## Найдено вне scope

- 

## Результат

- Ветка, PR или коммит:
- Период: 2026-11-19 —
- Часы человека: оценка 2 ч
- Работа агентов:
- Было / стало:
- Сделано:
- Чем проверено:
- Не сделано и почему:
- Требуется решение:
