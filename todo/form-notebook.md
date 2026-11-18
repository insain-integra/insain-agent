# form-notebook

Статус: выкатка
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

- [x] `python scripts/js_port_gaps.py calcNotebook` — в блоке `calcNotebook` строка `нет в Python` пустая, либо каждый пропуск уже есть и в docstring, и в `scripts/js_port_gaps_allowed.txt`.
- [x] `python -m pytest calc_service/tests/test_calculators/test_notebook.py calc_service/tests/test_wp_plugin_forms.py -q` — `passed`. Есть `REF_FORM_DEFAULT` с `# JS,`.
- [ ] Боевой `POST /api/v1/calc/notebook` на теле `REF_FORM_DEFAULT`: `price` и `time_ready` как у раннера (допуск цены abs ≤ 0.02 или rel ≤ 0.001, срока rel ≤ 0.001). Срок совпал, цена нет: бой 11869, JS 16061.69 / локально 16062.
- [x] `Select-String -Path wp-plugin\forms\notebook.js -Pattern "calcApi\('notebook'|syncUrl\(|showResult\("` — все три есть. Своей `price` и `querySelector` нет.
- [ ] Копия не на витрине: `draft` или `private`, гость без cookies — не `200`.
- [ ] На копии под админом дефолт даёт `POST /api/v1/calc/notebook` → 200. Цена на странице = `price` API с округлением `showResult`.
- [ ] URL копии обновляется GET-именами формы 45. Ссылка с этими GET открывает те же значения и ту же цену.
- [x] Боевая страница в HTML содержит `calcNotebook`, не `calcApi`.

## Проверки

- [x] `python scripts/dev.py check` — код выхода 0
- [x] Self-review — чеклист «Перед сдачей» в [AGENTS.md](../AGENTS.md)

## Риски

- Прод: боевая форма 45 не меняется. Запись в формы не параллельно с `todo/ezfc-options-source-reset.md`.
- Цены: JSON не менять. Чужие калькуляторы печати не двигать.
- Формы: id боевой 45 не менять.

## Режим

прод

## Журнал передач

19.11.2026 — Analyst, Grok 4.7 — задача заведена, пачка 4 — дальше Implementer

19.11.2026 — Implementer, Grok 4.7 — шаги 0–5б и `wp-plugin/forms/notebook.js` в ветке, без коммита. Локальный дефолт совпал с JS страницы, боевой API ещё старый — дальше человек

Блокер: копию формы 45 нельзя ставить, пока боевой `POST /api/v1/calc/notebook` на `REF_FORM_DEFAULT` не совпадёт с JS. Сейчас бой `price` 11869, JS 16061.69 (локально после правки 16062), `time_ready` 22.61 совпал.
Пробовал: пустой лист цвета `0+0` и отдельная подложка посчитаны в `notebook.py`, без правок `print_sheet.py` и `print_offset.py`. Локально `cost` 8990.798224489796, `price` 16062, `time_hours` 3.56, `time_ready` 22.61; материалы 54 / 1263 / проволока 0.0403. Боевой POST того же тела: `cost` 6690.600891156462, `price` 11869, `time_ready` 22.61. Эталон `REF_PARAMS` на бою совпал: `price` 20800, `time_ready` 58.15.
Гипотеза: на проде калькулятор без подложки и с пустым `0+0`. Выкладка только с `main`, Implementer прод не деплоит.
Вопрос: слить `task/form-notebook` в `main` и выкатить API до Site ops.
Следующая сессия: человек. Варианты:
1. Слить ветку в `main` и выкатить API (`deploy-api`). Когда боевой POST дефолта даст `price` 16062 и `time_ready` 22.61 — Site ops, копия формы 45. (Рекомендуется)
2. Не выкатывать. Ветку оставить, Site ops не запускать, пока выкладку не подтвердят отдельно.
3. Правку `notebook.py` не принимать и форму не переводить, пока Analyst не решит, где считать лист `0+0`: только в блокноте или в `print_sheet`.

19.11.2026 — человек — принято решение закоммитить и слить `task/form-notebook` в `main`, выкатить API (`deploy-api`), затем запустить Site ops для копии формы 45 — дальше Site ops

## Найдено вне scope

- `ssh insain-prod` (порт 22) — timeout. Id и имена полей формы 45 сняты с HTML боевой страницы (`data-id`, `ezfc_vars`), не из SQL.
- `calcNotebook` не подключён в `scripts/run_js_calc.mjs`. Эталон дефолта — консоль страницы. В `docs/js-runner-cases.md` не писал.
- Вес дефолта: JS 15.2892 (лист с обрезью), Python 15.00. В критерий цены и срока не входит.
- В блоке `calcPrintSheet` пропуски `call calcCutRoller`, `call calcPrintLaser` уже есть в `scripts/js_port_gaps_allowed.txt`. Блок `calcNotebook` пустой.
- Код проволоки в API `MetallBindindWire3_8`, в JS `MetallBindindWire`. Имя и `size_mm` 9.5×42000 совпали.
- Ламинация листа `0+0`: `cost` совпал с JS (1388.1508256410257), `price` 2262.59 против 2262.41 (разница 0.18 ₽, rel < 0.001).

## Результат

- Ветка, PR или коммит: `task/form-notebook` -> `main` (слито перед выкаткой API и копией формы 45)
- Период: 2026-11-19 —
- Часы человека: оценка 4 ч
- Работа агентов: Implementer, Grok 4.7, одна сессия
- Было / стало: дефолт формы (тираж 100, А5, обложка PaperCoated250M 4+0, подложка PaperCoated250M 0+0, блок VHI80 50 листов 0+0, пружина, короткая сторона, режим 1) на бою считается как обе стороны 4+0 и без бумаги блока: `price` 11869. Локально после правки — `price` 16062, `time_ready` 22.61, как JS страницы. `insaincalc.round(16062, 100)` и `round(16061.69, 100)` оба дают 16100, как цена на боевой странице.
- Сделано: шаги 0–5б. `REF_FORM_DEFAULT` с пометкой `# JS, 19.11.2026`. `wp-plugin/forms/notebook.js` на id боевой формы 45: `calcApi('notebook')`, `syncUrl`, `showResult`. В `notebook.py` отдельная подложка и лист `0+0` (бумага, резка, ламинация), у проволоки дописан `size_mm`. `print_sheet.py` и `print_offset.py` не менялись.
- Чем проверено: `python scripts/js_port_gaps.py calcNotebook` — у `calcNotebook` строка `нет в Python` пустая. `python -m pytest calc_service/tests/test_calculators/test_notebook.py calc_service/tests/test_wp_plugin_forms.py -q` — 14 passed. `python scripts/dev.py check` — код 0, 646 passed и 81 passed. Боевой POST `REF_PARAMS`: `price` 20800, `time_ready` 58.15. Боевой POST `REF_FORM_DEFAULT`: `price` 11869, `time_ready` 22.61. `Select-String` по `notebook.js` — три вызова есть, `querySelector` и своей `price` нет. HTML https://insain.ru/catalog/kalkulyator-bloknotov/ — `calcNotebook`, не `calcApi`.
- Не сделано и почему: дубль формы, черновик товара и отладка копии. Боевой API ещё без правки, копия ходила бы в старую цену. Плагин не выкладывался, боевая 45 не переключалась.
- Поля только в `syncUrl`, не в `calcApi`: `dpdBinding` (id 1825, значение `metallwire`). Старый JS затем сам ставит `BindRenzSRW` или `BindOffset`. В API уходит `binding_type: spring`.
- Строка для будущего `forms-batch-2` (не в текущий пакет): `| 45 CalcNotebook | notebook | /catalog/kalkulyator-bloknotov/ | копия не создана | form-notebook — git готов, ждёт выкладки API и копии |`
- Требуется решение: три варианта в журнале. После приёмки копии строка идёт в будущий `forms-batch-2`, не в текущий пакет.
