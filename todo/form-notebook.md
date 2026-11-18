# form-notebook

Статус: черновик
Сложность: низкая
Implementer: Grok 4.7
Reviewer: не нужен
Site ops: Grok 4.7
Почему: калькулятор `notebook` уже в API, пропусков `calcNotebook` в `js_port_gaps_allowed.txt` нет; копия формы по skill `ezfc-form-to-api`.

## Цель

Копия формы 45 CalcNotebook на черновике товара считает `POST /api/v1/calc/notebook`. URL копии пишется GET-именами элементов. Ссылка с этими GET открывает ту же копию с теми же значениями и той же ценой. Боевая страница https://insain.ru/catalog/kalkulyator-bloknotov/ остаётся на `insaincalc.calcNotebook`. В пакет `forms-batch-switch` форма 45 не попадает.

## Контекст и ссылки

- `.cursor/skills/ezfc-form-to-api/SKILL.md`, этапы `verify.md` и `copy.md`. Шаги 17–24 не входят.
- `docs/ezfc-api-migration.md` — GET = имя элемента.
- `docs/site/forms.md` — строка формы 45, только читать.
- `calc_service/calculators/notebook.py`, `calc_service/tests/test_calculators/test_notebook.py`.
- `todo/EPIC-forms-to-api.md` — пачка 4.
- Остальное не открывать.

## Scope

- В git (Implementer): шаги 0–5б и `wp-plugin/forms/notebook.js`. `REF_FORM_DEFAULT` в `test_notebook.py` с пометкой `# JS, ДД.ММ.ГГГГ`.
- Калькулятор не на боевой форме API. Расхождение дефолта чинить в `notebook.py`, не в `print_sheet.py` и не в `print_offset.py`. Если без их правки дефолт не сходится — стоп, `заблокировано: аналитик`.
- На проде (Site ops): дубль формы 45 на черновик после совпадения дефолта с боевым API. JS копии в элементе (`read_file=0`). Плагин не выкладывать. Боевую 45 не переключать.
- Строка для будущего пакета — в «Результат», не в `todo/forms-batch-switch.md`.

## Файлы

- `wp-plugin/forms/notebook.js`
- `calc_service/calculators/notebook.py`
- `calc_service/tests/test_calculators/test_notebook.py`
- WordPress: только копия формы 45 и её черновик

## Не-scope

- `todo/forms-batch-switch.md`, `docs/site/forms.md`, `docs/js-runner-cases.md`, новые строки в `scripts/js_port_gaps_allowed.txt`
- `print_sheet.py`, `print_offset.py`, их тесты и `wp-plugin/forms/print_sheet.js`, `print_offset.js`
- Боевая форма 45, выкладка плагина, JSON цен, `calc_service/calculators/__init__.py`

## Критерии приёмки

- [ ] `python scripts/js_port_gaps.py calcNotebook` — в блоке `calcNotebook` строка `нет в Python` пустая, либо каждый пропуск уже есть и в docstring, и в `scripts/js_port_gaps_allowed.txt`.
- [ ] `python -m pytest calc_service/tests/test_calculators/test_notebook.py calc_service/tests/test_wp_plugin_forms.py -q` — `passed`. Есть `REF_FORM_DEFAULT` с `# JS,`.
- [ ] Боевой `POST /api/v1/calc/notebook` на теле `REF_FORM_DEFAULT`: `price` и `time_ready` как у раннера (допуск цены abs ≤ 0.02 или rel ≤ 0.001, срока rel ≤ 0.001).
- [ ] `Select-String -Path wp-plugin\forms\notebook.js -Pattern "calcApi\('notebook'|syncUrl\(|showResult\("` — все три есть. Своей `price` и `querySelector` нет.
- [ ] Копия не на витрине: `draft` или `private`, гость без cookies — не `200`.
- [ ] На копии под админом дефолт даёт `POST /api/v1/calc/notebook` → 200. Цена на странице = `price` API с округлением `showResult`.
- [ ] URL копии обновляется GET-именами формы 45. Ссылка с этими GET открывает те же значения и ту же цену.
- [ ] Боевая страница в HTML содержит `calcNotebook`, не `calcApi`.

## Проверки

- [ ] `python scripts/dev.py check` — код выхода 0
- [ ] Self-review — чеклист «Перед сдачей» в [AGENTS.md](../AGENTS.md)

## Риски

- Прод: боевая форма 45 не меняется. Запись в формы не параллельно с `todo/ezfc-options-source-reset.md`.
- Цены: JSON не менять. Чужие калькуляторы печати не двигать.
- Формы: id боевой 45 не менять.

## Режим

прод

## Журнал передач

19.11.2026 — Analyst, Grok 4.7 — задача заведена, пачка 4 — дальше Implementer

## Найдено вне scope

- 

## Результат

- Ветка, PR или коммит:
- Период: 2026-11-19 —
- Часы человека: оценка 4 ч
- Работа агентов:
- Было / стало:
- Сделано:
- Чем проверено:
- Не сделано и почему:
- Требуется решение: после приёмки копии строка идёт в будущий `forms-batch-2`, не в текущий пакет.
