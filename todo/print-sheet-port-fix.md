# print-sheet-port-fix

Статус: выкатка
Сложность: средняя
Implementer: Opus 5.5
Reviewer: Grok 4.7
Site ops: Grok 4.7
Почему: срок и цена `print_sheet` на проде расходятся с JS (ceil времени печати и `timePrepare * mode`); предпосылка `form-print-sheet`, нужен деплой API.
Чат: человек открывает новый чат с моделью из поля Implementer.

## Цель

`PrintSheetCalculator` считает `time_hours` / `time_ready` и экономичный режим (`mode` 0) как JS `calcPrintSheet` / встроенная лазерная ветка `calcPrintLaser`. На проде эталон формы 6 (100 шт, 210×297, PaperCoated300M, 4+4, mode 1) даёт `time_ready` 10.2, а тот же вход с mode 0 — `price` 4864.332072727273 и `time_ready` 25.02 (как раннер).

## Контекст и ссылки

- Блокер `todo/form-print-sheet.md` (worktree `task/form-print-sheet`): эталон mode 1 — раннер `price` 5266.918472727273, `time_ready` 10.2; боевой API `price` та же, `time_ready` 10.183636363636364 (rel 0.00161). Mode 0 — раннер `price` 4864.332072727273, `time_ready` 25.02; API как mode 1 (`price` 5266.918472727273, `time_ready` 26.183636363636364).
- `js_legacy/calc/calcPrintLaser.js:19` — `timePrepare * modeProduction`; `:59` — `Math.ceil(timePrint * 100) / 100` до `timeReady`.
- `js_legacy/calc/calcPrintSheet.js:176–177` — второй `Math.ceil` суммы уже округлённых частей; `timeReady` от `costPrint.timeReady`.
- `calc_service/calculators/print_sheet.py:584` — `time_prepare * max(1, mode.value)`; `:585` — `time_print` без округления; `:707` — ceil только суммы; `:712–714` — `time_ready` от сырого `time_print`.
- Образец без `max(1, …)`: закрытый `uv-print-prepare` / `docs/history/log.md` 2026-11-08; в коде — `print_inkjet.py` (`time_prepare * mode`).
- Текущий `EXPECTED_REF` в `test_print_sheet.py` зафиксировал Python-числа (`time_ready` 10.1836…, комментарий «ceil снят») — переснять `time_hours` / `time_ready` с раннера; `price` эталона mode 1 не менять.
- `docs/js-runner-cases.md` — формат команды раннера.
- Остальное не открывать.

## Scope

- В git (Implementer):
  - `print_sheet.py`, лазерная ветка: `time_prepare = (printer.time_prepare or …) * mode.value` (без `max(1, …)`); время печати для `time_hours` / вклада в `print_time_ready` — `math.ceil(time_print * 100) / 100`, как JS; себестоимость от сырого `time_print`, как JS.
  - `test_print_sheet.py`, эталоны с раннера, пометка `# JS, ДД.ММ.ГГГГ`, команда рядом, assert `cost` / `price` / `time_ready` с `rel=0.001`:
    1) вход блокера mode 1 — `price` 5266.918472727273, `time_ready` 10.2 (обновить `EXPECTED_REF.time_hours` / `time_ready`; `price`/`cost`/`weight_kg` не трогать без расхождения с раннером);
    2) тот же вход mode 0 — `price` 4864.332072727273, `time_ready` 25.02.
    Оба кейса падают на текущем `print_sheet.py` (mode 1 — по `time_ready`; mode 0 — по `price` и `time_ready`).
  - Соседи, которые вызывают `PrintSheetCalculator`: прогон их тестов без пересъёмки эталонов. Упал эталон — стоп, `заблокировано: аналитик`.
  - `docs/js-runner-cases.md`: строки раннера для обоих кейсов.
- На проде (Site ops): после merge в `main` и зелёного CI — skill `deploy-api` (`bash infra/deploy.sh`), smoke на двух входах блокера `form-print-sheet`.

## Файлы

- `calc_service/calculators/print_sheet.py`
- `calc_service/tests/test_calculators/test_print_sheet.py` — пересекается с `form-print-sheet`, она ждёт эту задачу
- `docs/js-runner-cases.md`

## Не-scope

- `print_laser.py` (`:239` тот же `max(1, mode)`, `:260` `round` вместо `ceil`): лист этот модуль не вызывает; с JS в этой задаче не сверялся — не трогать.
- `calc_service/data/`, `wp-plugin/`, формы ezFC, копия формы 6, правка `form-print-sheet`.
- Такой же `max(1, mode)` / округление времени в других калькуляторах — не сверялись, не трогать.
- `weight_kg`: верный вес — Python (решение 11.11.2026); в новых кейсах вес не сверять с JS.
- Струйная ветка `print_sheet` и эталоны Epson/DTF — не часть блокера; падение — стоп Analyst.

## Критерии приёмки

Скрипт через `@'…'@ | python -` в PowerShell 5.1 — первой строкой `$OutputEncoding = New-Object System.Text.UTF8Encoding $false`.

- [x] Раннер `calcPrintSheet` на обоих кейсах. Mode 1: `price` 5266.918472727273, `timeReady` 10.2. Mode 0: `price` 4864.332072727273, `timeReady` 25.02.

```powershell
node scripts/run_js_calc.mjs calcPrintSheet --data current --args '[100,[210,297],"4+4",[0,0,0,0],0,"PaperCoated300M",{},1]'
node scripts/run_js_calc.mjs calcPrintSheet --data current --args '[100,[210,297],"4+4",[0,0,0,0],0,"PaperCoated300M",{},0]'
```

- [x] Тесты `print_sheet`. Stdout: `passed`, `failed` нет. На `git stash push -- calc_service/calculators/print_sheet.py` новые/обновлённые кейсы падают числами старого кода; после `git stash pop` — снова `passed`.

```powershell
python -m pytest calc_service/tests/test_calculators/test_print_sheet.py -q
```

- [x] Вызывающие не сдвинулись. Stdout: `passed`, `failed` нет. Упал эталон — стоп Analyst, эталоны соседей в этой задаче не переснимать.

```powershell
python -m pytest calc_service/tests/test_calculators/test_flag.py calc_service/tests/test_calculators/test_pennant.py calc_service/tests/test_calculators/test_calendar.py calc_service/tests/test_calculators/test_heat_press.py calc_service/tests/test_calculators/test_magnets.py calc_service/tests/test_calculators/test_badge.py calc_service/tests/test_calculators/test_notebook.py calc_service/tests/test_calculators/test_puzzle.py -q
```

- [ ] После деплоя (Site ops): боевой API на двух телах блокера. Mode 1: `price` 5266.918472727273 (abs ≤ 0.02), `time_ready` 10.2 (`rel ≤ 0.001`). Mode 0: `price` 4864.332072727273, `time_ready` 25.02 (`rel ≤ 0.001`). До правки mode 1 `time_ready` 10.1836…, mode 0 как mode 1.

```powershell
$api = Invoke-RestMethod -Method Post -Uri https://insain.ru/api/v1/calc/print_sheet -ContentType 'application/json' -Body '{"quantity":100,"width":210,"height":297,"material_id":"PaperCoated300M","color":"4+4","margins":[0,0,0,0],"interval":0,"mode":1}'
$api | Select-Object price, time_ready
```

## Проверки

- [x] `python scripts/dev.py check` — код выхода 0
- [x] Self-review — чеклист «Перед сдачей» в [AGENTS.md](../AGENTS.md)
- [ ] Деплой: skill `deploy-api`, smoke зелёный; откат — автооткат скрипта или образ `insain-agent-calc-api:rollback`.

## Риски

- Прод: деплой API с `main`.
- Цены: JSON не меняется. Mode 0 у `print_sheet` подешевеет до уровня JS у всех вызывающих (`flag`, `pennant`, `calendar`, `heat_press`, `magnets`, `badge`, `notebook`, `puzzle` и прямой `/calc/print_sheet`). Mode 1: `price` эталона не должен сдвинуться; `time_ready` чуть вырастет (10.1836… → 10.2). Затронуты принятые копии 73 (`pennant`) и 55 (`flag`) — после деплоя ближе к боевым JS-формам.
- Режим 0: как в JS, подготовка 0; срок и цена экономичного заказа короче/ниже стандартного — поведение JS, менять отдельной задачей.
- Формы: нет. Боевая форма 6 на витрине по-прежнему JS.

## Режим

прод

## Журнал передач

Строка на сессию: `<дата> — <роль>, <модель> — <итог> — дальше <роль>`. Блокер — по формату
[docs/agents/workflow.md](../docs/agents/workflow.md). Замечания ревью — ниже, в «Ревью N».

- 12.11.2026 — Analyst, Auto — предпосылка `form-print-sheet`: ceil времени печати до суммы и `timePrepare * mode` в `print_sheet.py`; `print_laser.py` в не-scope — дальше Implementer
- 12.11.2026 — Implementer, Auto — лазерная ветка: `time_prepare * mode`, ceil `time_print`, `print_time_ready` от `baseTimeReady` принтера; эталоны mode 1/0 с раннера; check зелёный — дальше Reviewer (Grok 4.7)
- 12.11.2026 — Reviewer, Grok 4.7 — принято — дальше человек (слияние)
- 13.11.2026 — человек — принято, слияние — дальше Site ops

## Ревью 1

принято. Блокеров нет. Деплой не этот круг: боевой API — Site ops после слияния в `main`.

- Раннер `calcPrintSheet --data current`. Mode 1: `cost` 3210.479090909091, `price` 5266.918472727273, `time_hours` 1.13, `time_ready` 10.2. Mode 0: `cost` 2959.689090909091, `price` 4864.332072727273, `time_hours` 1.02, `time_ready` 25.02. `weight_kg` раннера 2.16 в эталон не вписан.
- `pytest test_print_sheet.py -q`: 21 passed. На `git stash push -- print_sheet.py` оба кейса упали числами старого кода (mode 1 `time_hours` 1.12; mode 0 `cost` 3210.479090909091). После `stash pop` — снова 21 passed.
- Вызывающие flag…puzzle: 85 passed.
- `python scripts/dev.py check`: код 0, calc 546 passed, bot 81 passed.
- Diff: лазерная ветка `print_sheet.py` (`time_prepare * mode` без `max(1, …)`, себестоимость от сырого `time_print`, ceil времени печати, `print_time_ready` от `baseTimeReady` принтера). Эталон mode 1: сдвинуты только `time_hours` / `time_ready`. Mode 0 — новый кейс. Строки в `docs/js-runner-cases.md`. `print_laser.py`, JSON и `wp-plugin/` не тронуты. Струйная ветка не менялась.

## Найдено вне scope

- `print_laser.py:239` / `:260` — тот же `max(1, mode)` и `round` вместо `ceil`; вызывается из `sticker` и `/calc/print_laser`, не из листа. Вынести отдельной задачей после сверки со `calcPrintLaser`.
- Раннер `calcCutGuillotine` на входе гильотины листа даёт `time_ready` NaN (из блокера `form-print-sheet`); сверку листа не держит.

## Результат

- Ветка, PR или коммит: `task/print-sheet-port-fix`
- Период: 12.11.2026
- Часы человека:
- Работа агентов: Implementer
- Было / стало: mode 0 готовил как mode 1 (`max(1, …)`), `time_ready` без ceil печати и с `baseTimeReady` листа → mode 1 `time_ready` 10.1836… / mode 0 цена как mode 1. Стало: как JS — mode 1 `time_ready` 10.2, mode 0 `price` 4864.33… / `time_ready` 25.02
- Сделано: правка лазерной ветки `print_sheet.py`; эталоны mode 1/0; строки в `docs/js-runner-cases.md`
- Чем проверено: раннер обоих кейсов; `pytest test_print_sheet.py` 21 passed; stash calc → 2 failed (time_hours 1.12; mode0 cost 3210…), pop → 21 passed; соседи 85 passed; `python scripts/dev.py check` 546+81 passed, код 0
- Не сделано и почему: деплой и smoke боевого API — Site ops после merge
- Требуется решение: пуш `main`, затем деплой API (Site ops)
