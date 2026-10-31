# EPIC-calc-port-structure

Статус: черновик

## Цель

Python-калькуляторы повторяют граф вызовов и набор опций старого JS: вызов в JS — вызов порта в Python, без копий чужой логики. Полнота порта проверяется скриптом, а не по памяти. `plaque.py` — обёртка над `tablets`, форма 69 переведена на API со всеми нанесениями. Пункт 5.7 в `docs/refactoring-plan.md`.

## Задачи

Файлы задач пишет Analyst по `todo/_template.md`; Implementer — Opus 5.5, Reviewer — Grok 4.7.

- `todo/js-port-gaps.md` — `scripts/js_port_gaps.py`, файл допустимых пропусков, проверка в `make check`, шаг 0 в skills, строки правил в `calc_service/AGENTS.md`.
- `todo/materials-contract.md` — `name` и `title` обязательны, единицы и количество нормализованы, проверка в `BaseCalculator.execute()`, bridge `name || title`, версия плагина, `docs/data-formats.md`.
- `todo/print-inkjet-port.md` — порт `print_inkjet` по `calcPrintInkJet`, эталоны из JS (`scripts/run_js_calc.mjs`).
- `todo/print-sheet-routing.md` — маршрутизация `print_sheet` по принтеру, `size_mm` у бумаги, решение об округлении цены.
- `todo/heat-press-mug-vs-js.md` — `heat_press` и `mug` против JS.
- `todo/tablets-for-plaque.md` — ветки `calcTablets`, нужные плакеткам; явный список «не перенесено».
- `todo/plaque-thin-wrapper.md` — `plaque.py` вызывает `tablets`, дубли и приватный импорт удалены.

## Порядок

1. `todo/js-port-gaps.md` и `todo/materials-contract.md` — независимы, можно параллельно.
2. `todo/print-inkjet-port.md` — после `js-port-gaps`: скрипт сразу показывает пропуски.
3. `todo/print-sheet-routing.md` — после `print-inkjet-port`.
4. `todo/heat-press-mug-vs-js.md` — после `print-sheet-routing`.
5. `todo/tablets-for-plaque.md` — после `heat-press-mug-vs-js`.
6. `todo/plaque-thin-wrapper.md` — после `tablets-for-plaque`. Затем `todo/pilot-plaque-form.md`.

## Входные условия

- Коммит `a992831` с ветки `task/plaque-sublimation` (результаты ворот и копии формы 86, товар 2586879) переносится в `main` до удаления ветки: `git cherry-pick a992831`.
- Ветку `task/plaque-sublimation` не сливать. Коммит `314893f` — источник эталонов сублимации, не код.
- Старый черновик задачи — `git show task/plaque-sublimation:todo/print-inkjet-js.md`.
