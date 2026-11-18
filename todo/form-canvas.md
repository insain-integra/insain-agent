# form-canvas

Статус: черновик
Сложность: средняя
Implementer: Gemini 4 Hydrogen High
Reviewer: Grok 4.7
Site ops: Grok 4.7
Почему: копия формы по skill, но `calcCanvas call calcBaguette` и модуль `calcBaguette` числятся пропуском, а в docstring `canvas.py` этого списка нет.

## Цель

Копия формы 80 CalcCanvas на черновике товара считает `POST /api/v1/calc/canvas`. URL копии пишется GET-именами элементов. Ссылка с этими GET открывает ту же копию с теми же значениями и той же ценой. Боевая страница https://insain.ru/catalog/canvas/ остаётся на `insaincalc.calcCanvas`. В пакет `forms-batch-switch` форма 80 не попадает.

## Контекст и ссылки

- `.cursor/skills/ezfc-form-to-api/SKILL.md`, этапы `verify.md` и `copy.md`. Шаги 17–24 не входят.
- `docs/ezfc-api-migration.md` — GET = имя элемента.
- `docs/site/forms.md` — строка формы 80, только читать.
- `calc_service/calculators/canvas.py` — печать через `print_roll`, подрамник через профиль и `calc_set_canvas_frame`.
- `scripts/js_port_gaps_allowed.txt` — `calcCanvas call calcBaguette`, `calcBaguette module`.
- `calc_service/tests/test_calculators/test_canvas.py`.
- `todo/EPIC-forms-to-api.md` — пачка 4.
- Остальное не открывать.

## Scope

- В git (Implementer): шаги 0–5б и `wp-plugin/forms/canvas.js`. `REF_FORM_DEFAULT` в `test_canvas.py` с пометкой `# JS, ДД.ММ.ГГГГ`.
- Багет: если дефолт формы считает подрамник уже через профиль и `calc_set_canvas_frame` и цена сходится — дописать в docstring, что `calcBaguette` заменён этими вызовами, строки allowed не дублировать. Если цена дефолта не сходится — портировать недостающий вызов в `canvas.py` в этой задаче. `print_roll.py` не менять. Калькулятор не на боевой форме API, предпосылку не заводить. Новые строки в allowed не добавлять.
- На проде (Site ops): дубль формы 80 на черновик после совпадения дефолта с боевым API. Если порт менял ответ — сначала `deploy-api` с `main`, потом дубль. JS копии в элементе (`read_file=0`). Плагин не выкладывать. Боевую 80 не переключать.
- Строка для будущего пакета — в «Результат», не в `todo/forms-batch-switch.md`.

## Файлы

- `wp-plugin/forms/canvas.js`
- `calc_service/calculators/canvas.py`
- `calc_service/tests/test_calculators/test_canvas.py`
- WordPress: только копия формы 80 и её черновик

## Не-scope

- `todo/forms-batch-switch.md`, `docs/site/forms.md`, `docs/js-runner-cases.md`
- `print_roll.py` и `wp-plugin/forms/print_roll.js`
- Новые строки в `scripts/js_port_gaps_allowed.txt`. Отдельный модуль багета, если дефолт сходится без него.
- Боевая форма 80, выкладка плагина, JSON цен, `calc_service/calculators/__init__.py`

## Критерии приёмки

- [ ] `python scripts/js_port_gaps.py calcCanvas` — `calcBaguette` либо снят, либо назван в docstring и остаётся в allowed. Других непустых `нет в Python` без записи в обоих местах нет. `python scripts/js_port_gaps.py --check` печатает `ok`.
- [ ] `python -m pytest calc_service/tests/test_calculators/test_canvas.py calc_service/tests/test_wp_plugin_forms.py -q` — `passed`. Есть `REF_FORM_DEFAULT` с `# JS,`.
- [ ] Боевой `POST /api/v1/calc/canvas` на теле `REF_FORM_DEFAULT`: `price` и `time_ready` как у раннера (допуск цены abs ≤ 0.02 или rel ≤ 0.001, срока rel ≤ 0.001). Если порт ещё не выкачен — пункт после `deploy-api`, копию до него не принимать.
- [ ] `Select-String -Path wp-plugin\forms\canvas.js -Pattern "calcApi\('canvas'|syncUrl\(|showResult\("` — все три есть. Своей `price` и `querySelector` нет.
- [ ] Копия не на витрине: `draft` или `private`, гость без cookies — не `200`.
- [ ] На копии под админом дефолт даёт `POST /api/v1/calc/canvas` → 200. Цена на странице = `price` API с округлением `showResult`.
- [ ] URL копии обновляется GET-именами формы 80. Ссылка с этими GET открывает те же значения и ту же цену.
- [ ] Боевая страница в HTML содержит `calcCanvas`, не `calcApi`.

## Проверки

- [ ] `python scripts/dev.py check` — код выхода 0
- [ ] Self-review — чеклист «Перед сдачей» в [AGENTS.md](../AGENTS.md)

## Риски

- Прод: боевая форма 80 не меняется. Выкатка API — только если менялся калькулятор, с `main` после ревью. Запись в формы не параллельно с `todo/ezfc-options-source-reset.md`.
- Цены: JSON не менять. `print_roll` не двигать.
- Формы: id боевой 80 не менять.

## Режим

прод

## Журнал передач

19.11.2026 — Analyst, Grok 4.7 — задача заведена, пачка 4, пропуск багета — дальше Implementer

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
