# form-pad-print

Статус: черновик
Сложность: средняя
Implementer: Gemini 4 Hydrogen High
Reviewer: Grok 4.7
Site ops: Grok 4.7
Почему: копия формы по skill, но пропуск `calcPadPrint option Material` есть в `js_port_gaps_allowed.txt`; дефолт может потребовать порт в том же diff.

## Цель

Копия формы 38 CalcPadPrint на черновике товара считает `POST /api/v1/calc/pad_print`. URL копии пишется GET-именами элементов. Ссылка с этими GET открывает ту же копию с теми же значениями и той же ценой. Боевая страница https://insain.ru/catalog/tampopechat/ остаётся на `insaincalc.calcPadPrint`. В пакет `forms-batch-switch` форма 38 не попадает.

## Контекст и ссылки

- `.cursor/skills/ezfc-form-to-api/SKILL.md`, этапы `verify.md` и `copy.md`. Шаги 17–24 не входят.
- `docs/ezfc-api-migration.md` — GET = имя элемента.
- `docs/site/forms.md` — строка формы 38, только читать.
- `calc_service/calculators/pad_print.py`, `calc_service/tests/test_calculators/test_pad_print.py`.
- `scripts/js_port_gaps_allowed.txt` — строка `calcPadPrint option Material`.
- `todo/EPIC-forms-to-api.md` — пачка 4.
- Остальное не открывать.

## Scope

- В git (Implementer): шаги 0–5б и `wp-plugin/forms/pad_print.js`. `REF_FORM_DEFAULT` в `test_pad_print.py` с пометкой `# JS, ДД.ММ.ГГГГ`.
- Пропуск `Material`: если дефолт формы от него не зависит и цена сходится — дописать в «не перенесено» docstring. Если дефолт без этой ветки не сходится — портировать её в `pad_print.py` в этой задаче. Калькулятор не на боевой форме API, предпосылку не заводить. Новые строки в allowed не добавлять.
- На проде (Site ops): дубль формы 38 на черновик после совпадения дефолта с боевым API. Если порт менял ответ — сначала `deploy-api` с `main`, потом дубль. JS копии в элементе (`read_file=0`). Плагин не выкладывать. Боевую 38 не переключать.
- Строка для будущего пакета — в «Результат», не в `todo/forms-batch-switch.md`.

## Файлы

- `wp-plugin/forms/pad_print.js`
- `calc_service/calculators/pad_print.py`
- `calc_service/tests/test_calculators/test_pad_print.py`
- WordPress: только копия формы 38 и её черновик

## Не-scope

- `todo/forms-batch-switch.md`, `docs/site/forms.md`, `docs/js-runner-cases.md`
- Новые строки в `scripts/js_port_gaps_allowed.txt`. Чужие калькуляторы.
- Боевая форма 38, выкладка плагина, JSON цен, `calc_service/calculators/__init__.py`

## Критерии приёмки

- [ ] `python scripts/js_port_gaps.py calcPadPrint` — пропуск `Material` либо снят, либо назван в docstring и остаётся в allowed. Других непустых `нет в Python` без записи в обоих местах нет. `python scripts/js_port_gaps.py --check` печатает `ok`.
- [ ] `python -m pytest calc_service/tests/test_calculators/test_pad_print.py calc_service/tests/test_wp_plugin_forms.py -q` — `passed`. Есть `REF_FORM_DEFAULT` с `# JS,`.
- [ ] Боевой `POST /api/v1/calc/pad_print` на теле `REF_FORM_DEFAULT`: `price` и `time_ready` как у раннера (допуск цены abs ≤ 0.02 или rel ≤ 0.001, срока rel ≤ 0.001). Если порт ещё не выкачен — пункт после `deploy-api`, копию до него не принимать.
- [ ] `Select-String -Path wp-plugin\forms\pad_print.js -Pattern "calcApi\('pad_print'|syncUrl\(|showResult\("` — все три есть. Своей `price` и `querySelector` нет.
- [ ] Копия не на витрине: `draft` или `private`, гость без cookies — не `200`.
- [ ] На копии под админом дефолт даёт `POST /api/v1/calc/pad_print` → 200. Цена на странице = `price` API с округлением `showResult`.
- [ ] URL копии обновляется GET-именами формы 38. Ссылка с этими GET открывает те же значения и ту же цену.
- [ ] Боевая страница в HTML содержит `calcPadPrint`, не `calcApi`.

## Проверки

- [ ] `python scripts/dev.py check` — код выхода 0
- [ ] Self-review — чеклист «Перед сдачей» в [AGENTS.md](../AGENTS.md)

## Риски

- Прод: боевая форма 38 не меняется. Выкатка API — только если менялся калькулятор, с `main` после ревью. Запись в формы не параллельно с `todo/ezfc-options-source-reset.md`.
- Цены: JSON не менять.
- Формы: id боевой 38 не менять.

## Режим

прод

## Журнал передач

19.11.2026 — Analyst, Grok 4.7 — задача заведена, пачка 4, пропуск Material — дальше Implementer

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
