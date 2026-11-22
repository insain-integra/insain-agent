# form-milling

Статус: выкатка
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

- [x] `python scripts/js_port_gaps.py calcMilling` — пропуск `isCutMilling` либо снят (ветка есть в Python), либо назван в docstring и остаётся в allowed. Других непустых `нет в Python` без записи в обоих местах нет. `python scripts/js_port_gaps.py --check` печатает `ok`.
- [x] `python -m pytest calc_service/tests/test_calculators/test_milling.py calc_service/tests/test_wp_plugin_forms.py -q` — `passed`. Есть `REF_FORM_DEFAULT` с `# JS,`.
- [ ] Боевой `POST /api/v1/calc/milling` на теле `REF_FORM_DEFAULT`: `price` и `time_ready` как у раннера (допуск цены abs ≤ 0.02 или rel ≤ 0.001, срока rel ≤ 0.001). Если порт ещё не выкачен — этот пункт после `deploy-api`, копию до него не принимать.
- [x] `Select-String -Path wp-plugin\forms\milling.js -Pattern "calcApi\('milling'|syncUrl\(|showResult\("` — все три есть. Своей `price` и `querySelector` нет.
- [ ] Копия не на витрине: `draft` или `private`, гость без cookies — не `200`.
- [ ] На копии под админом дефолт даёт `POST /api/v1/calc/milling` → 200. Цена на странице = `price` API с округлением `showResult`.
- [ ] URL копии обновляется GET-именами формы 35. Ссылка с этими GET открывает те же значения и ту же цену.
- [ ] Боевая страница в HTML содержит `calcMilling`, не `calcApi`.

## Проверки

- [x] `python scripts/dev.py check` — код выхода 0
- [x] Self-review — чеклист «Перед сдачей» в [AGENTS.md](../AGENTS.md)

## Риски

- Прод: боевая форма 35 не меняется. Выкатка API — только если менялся калькулятор, и только с `main` после ревью. Запись в формы не параллельно с `todo/ezfc-options-source-reset.md`.
- Цены: JSON не менять. Порт ветки двигает цену к JS, не от него.
- Формы: id боевой 35 не менять.

## Режим

прод

## Журнал передач

19.11.2026 — Analyst, Grok 4.7 — задача заведена, пачка 4, пропуск isCutMilling — дальше Implementer
22.11.2026 — Implementer, Gemini 4 Hydrogen High — портирован is_cut_milling и исправлен расчёт milling.py по JS (дефолт формы 35 включает isCutMilling; ответ API изменился), написан wp-plugin/forms/milling.js, make check зелёный — дальше Reviewer (затем слияние в main, deploy-api и Site ops)
22.11.2026 — Reviewer, Grok 4.7 — принято: эталоны сходятся с calcMilling.js, прод-критерии после слияния и deploy-api — дальше человек
22.11.2026 — человек — принято: слить в main, выкатить API, затем копия формы 35 — дальше Site ops

## Найдено вне scope

- В форме 35 (`dpdMaterial`, элемент 1298) есть коды `Polycarbonate4` и `AcrylColor5`, которых нет в `calc_service/data/materials/hardsheet.json`.
- `calcMilling` не подключён в `scripts/run_js_calc.mjs` (эталон снят в консоли боевой страницы).
- Для материалов `PET03`–`PET20` из `dpdMaterial` в `calc_service/data/equipment/milling.json` отсутствует группа в `costCut` (ставка резки 0 руб/м, как и в JS).
- 100 шт 50×50 мм PVC3: и JS, и API отдают в материалах 0 листов (доля листа только в себестоимости). На дефолте без материала список пуст. В JS имя материала пустое (в JSON нет `name`), API пишет `description`.

## Результат

- Ветка, PR или коммит: `task/form-milling`
- Период: 2026-11-19 —
- Часы человека: оценка 8 ч
- Работа агентов: Analyst (Grok 4.7), Implementer (Gemini 4 Hydrogen High), Reviewer (Grok 4.7)
- Было / стало: боевой `/api/v1/calc/milling` на дефолте формы 35 (`material_id=""`, `100 шт, 50×50 мм, mode=1`) отдавал `price=719.0` (JS: `1360.0`), не имел `is_cut_milling`, не считал полулист/остаток и не отдавал `size_mm` в `materials`; после правки `milling.py` сходится с JS по всем кейсам и режимам `0/1/2` (dc/dp = 0), создан `wp-plugin/forms/milling.js`.
- Сделано:
  - Шаги 0–5б `ezfc-form-to-api`: проверены элементы формы 35 (`1295 numN`, `1296 numW`, `1297 numH`, `1298 dpdMaterial`, `1299 rdoMaterial`, `1301 dpdDifficulty`, `1303 numSizeItem`, `1304 numDensity`, `1305 numLenCut`, `1328 rdoModeProduction`, `1314 cjsCalc`). Поля формы без параметров API: `1313 fluAtrwork` (файл — не в URL и не в API), `1300 setMaxSize` (служебный hidden), `1302 Image` (картинка). Все `get_value_from(N)` в старом `1314 cjsCalc` указывают на верные id.
  - В `calc_service/calculators/milling.py` портирована опция `is_cut_milling` (`len_cut` в мм, `size_item`, `density`, `difficulty`) с сохранением обратной совместимости плоского `len_cut`, исправлен расчёт остатка/полулиста, порог `MIN_COST` (`cost_cut + cost_material + cost_operator > MIN_COST`), формула наценки (`effective_margin = max(MARGIN_OPERATION + margin_extra, MARGIN_MIN)` вместо `cost_total * (1 + MARGIN_MIN)`), округление `time_hours` через `math.ceil`, добавлен `size_mm` в `materials`, вес считается при любом `material_mode`, `material_id` в `get_tool_schema` необязателен (`default: ""`).
  - Удалена устранённая строка `calcMilling option isCutMilling` из `scripts/js_port_gaps_allowed.txt`.
  - В `calc_service/tests/test_calculators/test_milling.py` добавлены `REF_FORM_DEFAULT` (`# JS, 22.11.2026 (консоль боевой страницы)`) и тесты на `mode=0, 1, 2`, `PVC3`, `difficulty=1.7`, `len_cut=100`, `noCut`, `isMaterialCustomer`, поллиста `0.5` и `size_mm`.
  - Создан `wp-plugin/forms/milling.js` с id боевой формы 35 (`calcApi('milling', ...)`, `syncUrl(...)`, `showResult(...)`, без `price =` и `querySelector`).
- Чем проверено:
  - `python scripts/js_port_gaps.py calcMilling` и `--check` → `нет в Python:` пусто, `ok`.
  - `python -m pytest calc_service/tests/test_calculators/test_milling.py calc_service/tests/test_wp_plugin_forms.py calc_service/tests/test_mode_contract.py calc_service/tests/test_materials_contract.py -q` → `111 passed`.
  - `Select-String -Path wp-plugin\forms\milling.js -Pattern "calcApi\('milling'|syncUrl\(|showResult\(|get_value_from\(\d+"` → все вызовы и только id боевой формы 35; `price =` и `querySelector` не найдены.
  - `python scripts/dev.py check` → `796 passed` + `81 passed`, код выхода 0.
- Не сделано и почему:
  - Прод-шаги (`deploy-api`, шаги 6–16 `Site ops` — дубль формы 35 на черновик, проверка боевого `POST /api/v1/calc/milling` на `REF_FORM_DEFAULT`) не выполнялись, т.к. порт `milling.py` изменил ответ API и требует ревью (`Reviewer: Grok 4.7`), слияния в `main` и выкатки `deploy-api` до дубля формы.
- Требуется решение:
  - После ревью и слияния в `main` — выкатить API (`deploy-api`), затем `Site ops` (шаги 6–16, `--get numN --get numW --get numH --get dpdMaterial:index --get rdoMaterial:index --get dpdDifficulty:index --get numSizeItem --get numDensity --get numLenCut --get rdoModeProduction:value`).
  - После приёмки копии строка идёт в будущий `forms-batch-2`, не в текущий пакет.

## Ревью 1

22.11.2026 — Reviewer, Grok 4.7. Вердикт: принято. Статус остаётся `ревью`. Diff не закоммичен (ветка `task/form-milling` указывает на тот же коммит, что `main`).

Сверено:

- `python scripts/js_port_gaps.py calcMilling` — `нет в Python` пусто, ветка `is_cut_milling` в Python, строка allowed снята. `python scripts/js_port_gaps.py --check` → `ok`.
- `python -m pytest calc_service/tests/test_calculators/test_milling.py calc_service/tests/test_wp_plugin_forms.py -q` → `29 passed`. Есть `REF_FORM_DEFAULT` с `# JS, 22.11.2026`.
- `Select-String` по `wp-plugin/forms/milling.js`: есть `calcApi('milling'`, `syncUrl(`, `showResult(`; своих `price =` и `querySelector` нет.
- Отдельный прогон `js_legacy/calc/calcMilling.js` на `calc_service/data`: `cost`, `price`, `time_hours`, `time_ready` дефолта (`material_id=""`), PVC3, mode 0/1/2, difficulty 1.7, `len_cut=100`, без резки, материал заказчика и поллиста 0.5 совпали с Python.
- Инварианты: обязательные поля ответа; у материала `code`, `name`, `title` и `size_mm`; наценка `get_margin("marginMilling")` поверх `MARGIN_OPERATION`, не ниже `MARGIN_MIN` (0.6 + 0 ≥ 0.3, пол цену не меняет); новых цен в Python нет. Scope: `milling.py`, тест, `forms/milling.js`, снятие строки allowed. `docs/dashboard.md` — пересборка `make check`.
- Прод-критерии (боевой POST, черновик, GET, боевая страница на `calcMilling`) этим кругом не закрываются: порт меняет ответ API, копия только после слияния в `main` и `deploy-api`.

Замечания:

- `желательно` — `size_item=0` и `density=0`: в JS длина реза становится NaN, и цена падает в минимум (PVC3, mode=1: 1360); Python считает внешний периметр (2302.64). Дефолт и эталоны с `size_item=50` сходятся. Не держит сдачу.
- `вне scope` — 0 листов у мелкой раскладки и пустое имя в JS: см. «Найдено вне scope». На дефолте без материала таблица пустая с обеих сторон.
