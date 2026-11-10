# print-sheet-weight-port-fix

Статус: закрытие
Сложность: высокая
Implementer: Opus 5.5
Reviewer: Grok 4.7
Site ops: Grok 4.7
Почему: человек 11.11.2026 оставил вес Python (изделие). JS считает лист с обрезью; формулу к JS не переводим. Деплой API не нужен.
Чат: человек открывает новый чат с моделью из поля Implementer.

## Цель

Вес лазерной листовой печати остаётся расчётом Python: тираж × размер изделия. JS (`calcPrintSheet` → `calcPrintLaser`) считает лист (`numSheet` × `sizeSheet`) и тяжелее, потому что в вес входит обрезь. Это расхождение принято, к JS вес не выравниваем. На входе `form-pennant` (50 шт., 80×120, `PaperCoated115M`, `4+0`, mode 1, без ламинации) Python даёт `weight_kg` 0.1052, раннер — 0.1328. Цена и срок не меняются.

## Контекст и ссылки

- `.cursor/skills/port-fix-prerequisite/SKILL.md` — порядок предпосылки.
- Держит `todo/form-pennant.md` (форма 73). Блокер 2026-11-10: без ламинации раннер `weight_kg` 0.1328, Python и боевой API 0.1052; с ламинацией (дефолт формы) JS страницы 1.0144 против API 0.8818.
- Гипотеза: `calc_service/calculators/print_sheet.py` (~716–728) на не-inkjet считает `calc_weight(quantity, …, size=изделие)`; JS `calcPrintLaser` / `calcPrintInkJet` — `calcWeight(numSheet, …, sizeSheet)`.
- `js_legacy/calc/calcPrintSheet.js` (~178), `js_legacy/calc/calcPrintLaser.js` (~61–63).
- Эталоны и команда раннера — `docs/js-runner-cases.md`; кейс pennant без ламинации уже есть.
- Остальное не открывать.

## Scope

- В git (Implementer): локализовать расхождение раннером (`calcPrintSheet` и/или `calcPennantPaper` без ламинации); выровнять вес в `print_sheet` с JS; эталоны только с раннера; тест падает без правки; соседи, вызывающие `PrintSheetCalculator`, зелёные или осознанно пересняты только если их вес не был сверен с JS; строка раннера в `docs/js-runner-cases.md` при новом кейсе.
- На проде (Site ops): после ревью, слияния в `main` и зелёного CI — `bash infra/deploy.sh` (skill `deploy-api`); smoke веса на входе блокера `form-pennant`.

## Файлы

- `calc_service/calculators/print_sheet.py`
- `calc_service/tests/test_calculators/test_print_sheet.py`
- `calc_service/tests/test_calculators/test_pennant.py` — только `weight_kg` (и связанные assert) эталона блокера, если сдвинулся после правки
- `docs/js-runner-cases.md` — при новом или уточнённом кейсе веса

## Не-scope

- `wp-plugin/forms/pennant.js`, дубль формы 73, `todo/form-pennant.md` кроме снятия «ждёт» через `close`.
- Правка цен, наценок, `calc_service/data/`.
- `scripts/run_js_calc.mjs` (загрузка `laminat.json` / `calcLamination.js`) — harness; сверка веса — на кейсе без ламинации.
- Тот же шаблон веса в других калькуляторах, если они не вызывают `PrintSheetCalculator` и не сверены с JS.
- Формы эпика, кроме возврата к `form-pennant` после закрытия.

## Критерии приёмки

Решение человека 11.11.2026: сверка веса с раннером снята. Верный `weight_kg` — Python по размеру изделия. Формула возвращена. Деплой не нужен: на проде вес уже такой.

- [x] Локализация записана. Вымпел без ламинации: раннер `weight_kg` 0.1328, Python 0.1052. JS — `calcPrintLaser.js` строки 61–63, `calcWeight(numSheet, sizeSheet)`. Python — `print_sheet.py`, `calc_weight` по тиражу и размеру изделия.
- [x] Формула лазерного веса — тираж и размер изделия. Причина расхождения и верность Python отмечены в `print_sheet.py`, в эталоне `test_pennant` и в `docs/js-runner-cases.md`.
- [x] Эталоны веса соседей не пересняты под JS: `pennant` 0.1052, `flag` 0.1825, `badge` 1.18, `calendar` 29.33, `notebook` 8.23.
- [x] `python -m pytest calc_service/tests/test_calculators/ -q --tb=no` — зелёный.

Сняты решением: эталон веса с раннера, падение теста без правки под лист, боевой API «вес равен раннеру».

## Проверки

- [x] `python scripts/dev.py check` — код выхода 0.
- [x] Self-review — чеклист «Перед сдачей» в [AGENTS.md](../AGENTS.md).

## Риски

- Прод: деплой API меняет `weight_kg` у всех расчётов через `print_sheet` (вымпелы, флаги, календари, магниты и др.). Откат — предыдущий образ по skill `deploy-api`.
- Цены: JSON не трогать. Если при выравнивании веса сдвинется `price`/`time_ready` — стоп и эскалация Analyst.
- Формы: боевые формы не переключать. `form-pennant` ждёт закрытия этой задачи.

## Режим

прод

## Журнал передач

2026-11-10 — Analyst, Grok 4.7 — заведена предпосылка по весу print_sheet; `form-pennant` ждёт — дальше Implementer, Opus 5.5
2026-11-10 — Implementer, Grok 4.7 — лазерный вес переведён на лист, как JS
2026-11-11 — человек — верный вес по размеру изделия (Python); лист из JS, с обрезью, не переносим
2026-11-11 — Implementer, Grok 4.7 — формула возвращена, причина записана; статус `ревью` — дальше Reviewer, Grok 4.7
2026-11-11 — Reviewer, Grok 4.7 — Ревью 1: принято — дальше человек: слияние
2026-11-11 — человек — принято — закрытие

## Ревью 1

принято

- Diff против `main` (коммита нет): только комментарии/пометки решения 11.11.2026 в `print_sheet.py`, `test_pennant.py`, `test_print_sheet.py`, `docs/js-runner-cases.md` (+ файл задачи и автосборка `docs/dashboard.md`). Код `calc_weight(quantity=…, size=изделие)` не менялся.
- Эталоны веса не пересняты: `pennant` 0.1052; `flag`/`badge`/`calendar`/`notebook` без diff; числа `weight_kg` в `test_print_sheet` без изменений.
- Соседи: `python -m pytest …/test_{pennant,print_sheet,flag,badge,calendar,notebook}.py -q --tb=line` — 52 passed.

## Найдено вне scope

- Раннер не грузит `laminat.json` / `calcLamination.js` — дефолт формы 73 с ламинацией раннером не считается.
- Струйный вес `print_sheet` по-прежнему берётся из `calcPrintInkJet` (тоже по листу). Решение 11.11.2026 записано для лазерной ветки.

## Результат

- Ветка, PR или коммит: `task/print-sheet-weight-port-fix` от `main`, worktree `D:\Projects\insain-agent-print-sheet-weight-port-fix`. Коммита нет.
- Период: 2026-11-10 — 2026-11-11
- Часы человека:
- Работа агентов: Implementer, Grok 4.7
- Было / стало: попытка считать лазерный вес по листу, как JS, возвращена. Снова тираж × размер изделия. Вымпел 50×80×120 `PaperCoated115M`: Python `weight_kg` 0.1052, JS 0.1328.
- Сделано: формула в `print_sheet.py` как до правки; комментарий с причиной; та же пометка в `test_pennant.py`, `test_print_sheet.py` и `docs/js-runner-cases.md`. Эталоны веса соседей снова прежние.
- Чем проверено: `python -m pytest calc_service/tests/test_calculators/ -q --tb=line` — 388 passed; `python scripts/dev.py check` — код 0 (539 + 81).
- Не сделано и почему: деплой не нужен — поведение веса совпадает с продом. `form-pennant` больше не должен ждать выравнивания веса с JS; снять «ждёт» — Analyst на `main`.
- Требуется решение: нет
