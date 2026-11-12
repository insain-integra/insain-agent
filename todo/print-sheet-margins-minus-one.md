# print-sheet-margins-minus-one

Статус: черновик
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

- [ ] Раннер `node scripts/run_js_calc.mjs calcPrintSheet --data current --args '[100,[297,210],\"4+0\",-1,0,\"VHI80\",{},1]'` и локальный `print_sheet` / после деплоя боевой API: `price` abs ≤ 0.02 и rel ≤ 0.001, `time_ready` rel ≤ 0.001 (эталон ~1811.964386666667 / 8.4).
- [ ] В `test_print_sheet.py` кейс с `margins: -1` и пометка `# JS, ДД.ММ.ГГГГ`; assert `cost`, `price`, `time_ready` с `rel=0.001`. Есть кейс с обычными margins (например дефолт `[2,2,2,2]`), числа старых эталонов не менялись.
- [ ] `git stash push -- calc_service/calculators/print_sheet.py` → новые кейсы `failed`, старые `passed` → `git stash pop` → все `passed`.
- [ ] `python -m pytest calc_service/tests/test_calculators/ -q -k "flag or pennant or heat_press or calendar or badge or magnets or notebook or puzzle or print_sheet"` — `failed` нет (соседи вызывают `PrintSheetCalculator`).
- [ ] После `deploy-api`: `POST https://insain.ru/api/v1/calc/print_sheet` телом блокера — `price`/`time_ready` как у раннера.

## Проверки

- [ ] `python scripts/dev.py check` — код выхода 0
- [ ] Self-review — чеклист «Перед сдачей» в [AGENTS.md](../AGENTS.md)

## Риски

- Прод: выкатка API; откат — предыдущий образ по skill `deploy-api`.
- Цены: на проде меняется только вход с `margins: -1` (белые поля). Входы с массивом margins и принятые копии с явными полями не должны сдвинуться.
- Формы: боевую форму 6 не трогать.

## Режим

прод

## Журнал передач

13.11.2026 — Analyst, Grok 4.7 — задача-предпосылка по блокеру form-print-sheet (margins -1) — дальше Implementer (Grok 4.7)

## Найдено вне scope

- —

## Результат

- Ветка, PR или коммит:
- Период:
- Часы человека:
- Работа агентов:
- Было / стало:
- Сделано:
- Чем проверено:
- Не сделано и почему:
- Требуется решение:
