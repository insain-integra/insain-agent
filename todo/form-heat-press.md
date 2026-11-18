# form-heat-press

Статус: черновик
Сложность: средняя
Implementer: Gemini 4 Hydrogen High
Reviewer: Grok 4.7
Site ops: Grok 4.7
Почему: копия формы по skill, но в docstring `heat_press.py` не перенесены плёнка, экосольвент, лазерная бумага и резка; дефолт формы может попасть в эти ветки.

## Цель

Копия формы 40 CalcHeatPress на черновике товара считает `POST /api/v1/calc/heat_press`. URL копии пишется GET-именами элементов. Ссылка с этими GET открывает ту же копию с теми же значениями и той же ценой. Боевая страница https://insain.ru/catalog/kalkulyator-naneseniya-na-odezhdu/ остаётся на `insaincalc.calcHeatPress`. В пакет `forms-batch-switch` форма 40 не попадает.

## Контекст и ссылки

- `.cursor/skills/ezfc-form-to-api/SKILL.md`, этапы `verify.md` и `copy.md`. Шаги 17–24 не входят.
- `docs/ezfc-api-migration.md` — GET = имя элемента.
- `docs/site/forms.md` — строка формы 40, только читать.
- `calc_service/calculators/heat_press.py` — список «не перенесено» в шапке модуля.
- `scripts/js_port_gaps_allowed.txt` — вызовы `calcSticker`, `calcLayoutOnSheet`, `calcCutPlotter`, `calcPrintRoll`, `calcCutSaber`.
- `calc_service/tests/test_calculators/test_heat_press.py`.
- `todo/EPIC-forms-to-api.md` — пачка 4.
- Остальное не открывать.

## Scope

- В git (Implementer): шаги 0–5б и `wp-plugin/forms/heat_press.js`. `REF_FORM_DEFAULT` в `test_heat_press.py` с пометкой `# JS, ДД.ММ.ГГГГ`.
- Портировать в `heat_press.py` только ту ветку, без которой дефолт формы не сходится с раннером. Остальные пункты «не перенесено» не разгребать. Чужие калькуляторы (`print_sheet.py`, `sticker.py`, `cut_plotter.py`, `print_roll.py`) не менять: вызывать уже существующие. Калькулятор не на боевой форме API, предпосылку не заводить. Новые строки в allowed не добавлять; снятую строку убрать, если вызов появился.
- На проде (Site ops): дубль формы 40 на черновик после совпадения дефолта с боевым API. Если порт менял ответ — сначала `deploy-api` с `main`, потом дубль. JS копии в элементе (`read_file=0`). Плагин не выкладывать. Боевую 40 не переключать.
- Строка для будущего пакета — в «Результат», не в `todo/forms-batch-switch.md`.

## Файлы

- `wp-plugin/forms/heat_press.js`
- `calc_service/calculators/heat_press.py`
- `calc_service/tests/test_calculators/test_heat_press.py`
- `scripts/js_port_gaps_allowed.txt` — только снять строку, если её вызов появился в `heat_press.py`
- WordPress: только копия формы 40 и её черновик

## Не-scope

- `todo/forms-batch-switch.md`, `docs/site/forms.md`, `docs/js-runner-cases.md`
- `print_sheet.py`, `sticker.py`, `cut_plotter.py`, `print_roll.py` и их тесты
- Ветки трансфера, которые дефолт формы не вызывает
- Боевая форма 40, выкладка плагина, JSON цен, `calc_service/calculators/__init__.py`

## Критерии приёмки

- [ ] `python scripts/js_port_gaps.py calcHeatPress` — у каждой непустой строки `нет в Python` есть пара: docstring и `scripts/js_port_gaps_allowed.txt`. Ветка дефолта формы в `нет в Python` не числится. `python scripts/js_port_gaps.py --check` печатает `ok`.
- [ ] `python -m pytest calc_service/tests/test_calculators/test_heat_press.py calc_service/tests/test_wp_plugin_forms.py -q` — `passed`. Есть `REF_FORM_DEFAULT` с `# JS,`. Соседние тесты печати и резки, если их не меняли, зелёные в `make check`.
- [ ] Боевой `POST /api/v1/calc/heat_press` на теле `REF_FORM_DEFAULT`: `price` и `time_ready` как у раннера (допуск цены abs ≤ 0.02 или rel ≤ 0.001, срока rel ≤ 0.001). Если порт ещё не выкачен — пункт после `deploy-api`, копию до него не принимать.
- [ ] `Select-String -Path wp-plugin\forms\heat_press.js -Pattern "calcApi\('heat_press'|syncUrl\(|showResult\("` — все три есть. Своей `price` и `querySelector` нет.
- [ ] Копия не на витрине: `draft` или `private`, гость без cookies — не `200`.
- [ ] На копии под админом дефолт даёт `POST /api/v1/calc/heat_press` → 200. Цена на странице = `price` API с округлением `showResult`.
- [ ] URL копии обновляется GET-именами формы 40. Ссылка с этими GET открывает те же значения и ту же цену.
- [ ] Боевая страница в HTML содержит `calcHeatPress`, не `calcApi`.

## Проверки

- [ ] `python scripts/dev.py check` — код выхода 0
- [ ] Self-review — чеклист «Перед сдачей» в [AGENTS.md](../AGENTS.md)

## Риски

- Прод: боевая форма 40 не меняется. Выкатка API — только если менялся калькулятор, с `main` после ревью. Запись в формы не параллельно с `todo/ezfc-options-source-reset.md`.
- Цены: JSON не менять. Неперенесённые типы трансфера остаются в docstring, пока дефолт их не требует.
- Формы: id боевой 40 не менять.

## Режим

прод

## Журнал передач

19.11.2026 — Analyst, Grok 4.7 — задача заведена, пачка 4, порт неполный — дальше Implementer

## Найдено вне scope

- 

## Результат

- Ветка, PR или коммит:
- Период: 2026-11-19 —
- Часы человека: оценка 8 ч
- Работа агентов:
- Было / стало:
- Сделано:
- Чем проверено:
- Не сделано и почему:
- Требуется решение: после приёмки копии строка идёт в будущий `forms-batch-2`, не в текущий пакет.
