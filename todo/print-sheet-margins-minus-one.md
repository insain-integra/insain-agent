# print-sheet-margins-minus-one

Статус: выкатка
Сложность: низкая
Implementer: Grok 4.7
Reviewer: Auto
Site ops: Grok 4.7
Почему: быстрая предпосылка порта по образцу print-sheet-port-fix; на проде только deploy-api и smoke на входе блокера form-print-sheet.
Чат: человек открывает новый чат с моделью из поля Implementer.

## Цель

`POST /api/v1/calc/print_sheet` с `margins: -1` (галка «белые поля» формы 6) даёт `price` и `time_ready` как раннер `calcPrintSheet` на том же входе. Поля принтера при `-1` не прибавляются.

## Контекст и ссылки

- Образец: закрытый `print-sheet-port-fix` (`docs/history/log.md` 2026-11-13) — тот же класс: порт `print_sheet` под JS, skill `port-fix-prerequisite` быстрый путь.
- JS: `js_legacy/calc/calcPrintSheet.js:48-49` — `if (margins != -1) { sum_margins = margins.map(… + printer.margins) }`.
- Python: `calc_service/calculators/print_sheet.py:459-463` на `-1` ставит `[0,0,0,0]`; `:503-507` `if … and sum_margins` считает список нулей истинным и прибавляет поля принтера.
- Блокер `form-print-sheet` 13.11.2026: дефолт А4 297×210, VHI80, 4+0, mode 1, `margins -1`, interval 0 — раннер price 1811.964386666667, time_ready 8.4; боевой API 3214.3125999999997, time_ready 8.6.
- Skill: `.cursor/skills/port-fix-prerequisite/SKILL.md`.
- Остальное не открывать.

## Scope

- В git (Implementer): в `print_sheet.py` при `margins == -1` не прибавлять поля принтера (как JS:48-49). Эталон раннера на входе блокера + ветка с обычными margins (соседи не сдвинулись). Тест падает без правки. Строка раннера в `docs/js-runner-cases.md`.
- На проде (Site ops): после слияния и зелёного CI — только skill `deploy-api`; smoke `POST` на входе блокера `form-print-sheet` (тело как у раннера «белых полей»).

Ветка `task/print-sheet-margins-minus-one` от `main`.

## Файлы

- `calc_service/calculators/print_sheet.py`
- `calc_service/tests/test_calculators/test_print_sheet.py`
- `docs/js-runner-cases.md`

## Не-scope

- `todo/form-print-sheet.md`, `wp-plugin/forms/print_sheet.js`, дубль формы 6.
- Цены и `calc_service/data/`.
- Тот же шаблон `margins == -1` в других калькуляторах (не сверялись с JS).
- Правка соседей (`flag`, `pennant`, …), если их эталоны с явным массивом margins; упал эталон соседа — стоп, Analyst.

## Критерии приёмки

- [x] Раннер `node scripts/run_js_calc.mjs calcPrintSheet --data current --args '[100,[297,210],\"4+0\",-1,0,\"VHI80\",{},1]'` и локальный `print_sheet` / после деплоя боевой API: `price` abs ≤ 0.02 и rel ≤ 0.001, `time_ready` rel ≤ 0.001 (эталон ~1811.964386666667 / 8.4).
- [x] В `test_print_sheet.py` кейс с `margins: -1` и пометка `# JS, ДД.ММ.ГГГГ`; assert `cost`, `price`, `time_ready` с `rel=0.001`. Есть кейс с обычными margins (например дефолт `[2,2,2,2]`), числа старых эталонов не менялись.
- [x] `git stash push -- calc_service/calculators/print_sheet.py` → новые кейсы `failed`, старые `passed` → `git stash pop` → все `passed`.
- [x] `python -m pytest calc_service/tests/test_calculators/ -q -k "flag or pennant or heat_press or calendar or badge or magnets or notebook or puzzle or print_sheet"` — `failed` нет (соседи вызывают `PrintSheetCalculator`).
- [ ] После `deploy-api`: `POST https://insain.ru/api/v1/calc/print_sheet` телом блокера — `price`/`time_ready` как у раннера.

## Проверки

- [x] `python scripts/dev.py check` — код выхода 0
- [x] Self-review — чеклист «Перед сдачей» в [AGENTS.md](../AGENTS.md)

## Риски

- Прод: выкатка API; откат — предыдущий образ по skill `deploy-api`.
- Цены: на проде меняется только вход с `margins: -1` (белые поля). Входы с массивом margins и принятые копии с явными полями не должны сдвинуться.
- Формы: боевую форму 6 не трогать.

## Режим

прод

## Журнал передач

13.11.2026 — Analyst, Grok 4.7 — задача-предпосылка по блокеру form-print-sheet (margins -1) — дальше Implementer (Grok 4.7)
13.11.2026 — Implementer, Grok 4.7 — сдал, make check зелёный — дальше Reviewer (Auto)
13.11.2026 — Reviewer, Auto — принято — дальше человек: слияние
13.11.2026 — человек — принято — выкатка

## Ревью 1

принято

Сверка критериев (код, без выкатки):
- Diff `print_sheet.py`: `skip_printer_margins = margins_param == -1`; при `-1` поля принтера не прибавляются — как JS `calcPrintSheet.js:48-49`.
- Эталоны: `-1` → price 1811.964386666667 / time_ready 8.4; `[2,2,2,2]` → 3214.3125999999997 / 8.6. Старые `EXPECTED_REF` / `EXPECTED_REF_MODE0` (5266… / 4864…) в diff не менялись — только добавления.
- Пометка `# JS, 13.11.2026`; assert `cost`/`price`/`time_ready` с `rel=0.001`.
- Stash только `print_sheet.py`: 1 failed (`margins_minus_one`, cost 1951.1725 vs 1102.82…), 8 passed; после `stash pop` соседи+print_sheet — 115 passed.
- `docs/js-runner-cases.md` — две строки команд. `docs/dashboard.md` — пересборка от `make check`, не замечание.
- Выкатка / smoke боевого API — не-scope этого diff; критерий после `deploy-api` остаётся Site ops.

## Найдено вне scope

- —

## Результат

- Ветка, PR или коммит: `task/print-sheet-margins-minus-one`, worktree `D:\Projects\insain-agent-print-sheet-margins-minus-one`, от `479f42e`. Коммита нет.
- Период: 2026-11-13
- Часы человека: —
- Работа агентов: Implementer — Grok 4.7
- Было / стало: при `margins: -1` список `[0,0,0,0]` считался истинным и к нему прибавлялись поля принтера — `price` 3214.3125999999997, `time_ready` 8.6. Стало: поля принтера не прибавляются, как `calcPrintSheet.js:48-49` — `price` 1811.964386666667, `time_ready` 8.4. Вход `[2,2,2,2]` остался 3214.3125999999997 / 8.6.
- Сделано: флаг `skip_printer_margins` в `print_sheet.py`; эталоны раннера `-1` и `[2,2,2,2]` в `test_print_sheet.py`; строки команд в `docs/js-runner-cases.md`.
- Чем проверено: раннер `-1` — cost 1102.8211666666666, price 1811.964386666667, time_ready 8.4; раннер `[2,2,2,2]` — cost 1951.1725, price 3214.3125999999997, time_ready 8.6. `pytest test_print_sheet.py -k "margins_minus_one or margins_default or expected_values_print_sheet"` — 9 passed. Stash только `print_sheet.py`: 1 failed (`margins_minus_one`, cost 1951.1725 вместо 1102.8211666666666), 22 passed (старые эталоны и `[2,2,2,2]`); после `stash pop` соседи и `print_sheet` — 115 passed. `python scripts/dev.py check` — код 0 (548 + 81 passed).
- Не сделано и почему: коммит не делал — не просили. Выкатка и smoke боевого API — Site ops после ревью и слияния.
- Требуется решение: нет.
