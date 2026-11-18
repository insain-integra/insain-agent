# form-milling

Статус: черновик
Сложность: средняя
Implementer: Gemini 4 Hydrogen High
Reviewer: Grok 4.7
Site ops: Grok 4.7
Почему: копия формы по skill, но пропуск `calcMilling option isCutMilling` есть в `js_port_gaps_allowed.txt` и не назван в docstring; дефолт может потребовать порт в том же diff.

## Цель

Копия формы 35 CalcMilling на черновике товара считает `POST /api/v1/calc/milling`. URL копии пишется GET-именами элементов. Ссылка с этими GET открывает ту же копию с теми же значениями и той же ценой. Боевая страница https://insain.ru/catalog/frezerovka-listovyh-materialov/ остаётся на `insaincalc.calcMilling`. В пакет `forms-batch-switch` форма 35 не попадает.

## Контекст и ссылки

- `.cursor/skills/ezfc-form-to-api/SKILL.md`, этапы `verify.md` и `copy.md`. Шаги 17–24 не входят.
- `docs/ezfc-api-migration.md` — GET = имя элемента.
- `docs/site/forms.md` — строка формы 35, только читать.
- `calc_service/calculators/milling.py`, `calc_service/tests/test_calculators/test_milling.py`.
- `scripts/js_port_gaps_allowed.txt` — строка `calcMilling option isCutMilling`.
- `todo/EPIC-forms-to-api.md` — пачка 4.
- Остальное не открывать.

## Scope

- В git (Implementer): шаги 0–5б и `wp-plugin/forms/milling.js`. `REF_FORM_DEFAULT` в `test_milling.py` с пометкой `# JS, ДД.ММ.ГГГГ`.
- Пропуск `isCutMilling`: если дефолт формы его не включает и цена сходится — дописать опцию в «не перенесено» docstring, строку в allowed не дублировать. Если дефолт её включает и цена не сходится — портировать ветку в `milling.py` в этой задаче. Калькулятор не на боевой форме API, предпосылку не заводить. Новые строки в allowed не добавлять.
- На проде (Site ops): дубль формы 35 на черновик после совпадения дефолта с боевым API. Если порт менял ответ API — сначала выкатка по skill `deploy-api` с `main`, потом дубль. JS копии в элементе (`read_file=0`). Плагин не выкладывать. Боевую 35 не переключать.
- Строка для будущего пакета — в «Результат», не в `todo/forms-batch-switch.md`.

## Файлы

- `wp-plugin/forms/milling.js`
- `calc_service/calculators/milling.py`
- `calc_service/tests/test_calculators/test_milling.py`
- WordPress: только копия формы 35 и её черновик

## Не-scope

- `todo/forms-batch-switch.md`, `docs/site/forms.md`, `docs/js-runner-cases.md`
- Новые строки в `scripts/js_port_gaps_allowed.txt`. Чужие калькуляторы.
- Боевая форма 35, выкладка плагина, JSON цен, `calc_service/calculators/__init__.py`

## Критерии приёмки

- [ ] `python scripts/js_port_gaps.py calcMilling` — пропуск `isCutMilling` либо снят (ветка есть в Python), либо назван в docstring и остаётся в allowed. Других непустых `нет в Python` без записи в обоих местах нет. `python scripts/js_port_gaps.py --check` печатает `ok`.
- [ ] `python -m pytest calc_service/tests/test_calculators/test_milling.py calc_service/tests/test_wp_plugin_forms.py -q` — `passed`. Есть `REF_FORM_DEFAULT` с `# JS,`.
- [ ] Боевой `POST /api/v1/calc/milling` на теле `REF_FORM_DEFAULT`: `price` и `time_ready` как у раннера (допуск цены abs ≤ 0.02 или rel ≤ 0.001, срока rel ≤ 0.001). Если порт ещё не выкачен — этот пункт после `deploy-api`, копию до него не принимать.
- [ ] `Select-String -Path wp-plugin\forms\milling.js -Pattern "calcApi\('milling'|syncUrl\(|showResult\("` — все три есть. Своей `price` и `querySelector` нет.
- [ ] Копия не на витрине: `draft` или `private`, гость без cookies — не `200`.
- [ ] На копии под админом дефолт даёт `POST /api/v1/calc/milling` → 200. Цена на странице = `price` API с округлением `showResult`.
- [ ] URL копии обновляется GET-именами формы 35. Ссылка с этими GET открывает те же значения и ту же цену.
- [ ] Боевая страница в HTML содержит `calcMilling`, не `calcApi`.

## Проверки

- [ ] `python scripts/dev.py check` — код выхода 0
- [ ] Self-review — чеклист «Перед сдачей» в [AGENTS.md](../AGENTS.md)

## Риски

- Прод: боевая форма 35 не меняется. Выкатка API — только если менялся калькулятор, и только с `main` после ревью. Запись в формы не параллельно с `todo/ezfc-options-source-reset.md`.
- Цены: JSON не менять. Порт ветки двигает цену к JS, не от него.
- Формы: id боевой 35 не менять.

## Режим

прод

## Журнал передач

19.11.2026 — Analyst, Grok 4.7 — задача заведена, пачка 4, пропуск isCutMilling — дальше Implementer

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
