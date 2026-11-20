# form-heat-press

Статус: выкатка
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

- [x] `python scripts/js_port_gaps.py calcHeatPress` — у каждой непустой строки `нет в Python` есть пара: docstring и `scripts/js_port_gaps_allowed.txt`. Ветка дефолта формы в `нет в Python` не числится. `python scripts/js_port_gaps.py --check` печатает `ok`.
- [x] `python -m pytest calc_service/tests/test_calculators/test_heat_press.py calc_service/tests/test_wp_plugin_forms.py -q` — `passed`. Есть `REF_FORM_DEFAULT` с `# JS,`. Соседние тесты печати и резки, если их не меняли, зелёные в `make check`.
- [ ] Боевой `POST /api/v1/calc/heat_press` на теле `REF_FORM_DEFAULT`: `price` и `time_ready` как у раннера (допуск цены abs ≤ 0.02 или rel ≤ 0.001, срока rel ≤ 0.001). Если порт ещё не выкачен — пункт после `deploy-api`, копию до него не принимать.
- [x] `Select-String -Path wp-plugin\forms\heat_press.js -Pattern "calcApi\('heat_press'|syncUrl\(|showResult\("` — все три есть. Своей `price` и `querySelector` нет.
- [ ] Копия не на витрине: `draft` или `private`, гость без cookies — не `200`.
- [ ] На копии под админом дефолт даёт `POST /api/v1/calc/heat_press` → 200. Цена на странице = `price` API с округлением `showResult`.
- [ ] URL копии обновляется GET-именами формы 40. Ссылка с этими GET открывает те же значения и ту же цену.
- [ ] Боевая страница в HTML содержит `calcHeatPress`, не `calcApi`.

## Проверки

- [x] `python scripts/dev.py check` — код выхода 0 (`750 passed` в `calc_service/tests`, `81 passed` в `bot_service/tests`)
- [x] Self-review — чеклист «Перед сдачей» в [AGENTS.md](../AGENTS.md)

## Риски

- Прод: боевая форма 40 не меняется. Выкатка API — только если менялся калькулятор, с `main` после ревью. Запись в формы не параллельно с `todo/ezfc-options-source-reset.md`.
- Цены: JSON не менять. Неперенесённые типы трансфера остаются в docstring, пока дефолт их не требует.
- Формы: id боевой 40 не менять.

## Режим

прод

## Журнал передач

19.11.2026 — Analyst, Grok 4.7 — задача заведена, пачка 4, порт неполный — дальше Implementer
21.11.2026 — Implementer, Gemini 4 Hydrogen High — шаги 0–5б, портирована ветка film в heat_press.py, добавлены REF_FORM_DEFAULT + тесты (mode 0/1/2) и wp-plugin/forms/heat_press.js, make check зелёный — дальше Reviewer
21.11.2026 — Reviewer, Grok 4.7 — принято: ветка film и heat_press.js сходятся с раннером по price и time_ready; прод-критерии после слияния и deploy-api — дальше человек
21.11.2026 — человек — принято: слить в main, выкатить API и передать Site ops копию формы 40 — дальше Site ops

## Ревью 1

Вердикт: принято. Статус остаётся `ревью`.

Проверено по diff и командам в worktree:

- `python scripts/js_port_gaps.py calcHeatPress`: у `calcHeatPress` в `нет в Python` только `call calcLayoutOnSheet`, `call calcCutPlotter`, `call calcPrintRoll`, `call calcCutSaber`. Каждая есть в docstring `heat_press.py` и в `scripts/js_port_gaps_allowed.txt`. `call calcSticker` в пропусках нет. `python scripts/js_port_gaps.py --check` → `ok`.
- `python -m pytest calc_service/tests/test_calculators/test_heat_press.py calc_service/tests/test_wp_plugin_forms.py calc_service/tests/test_mode_contract.py -q` → `70 passed`. `REF_FORM_DEFAULT` с пометкой `# JS, 21.11.2026`.
- Раннер `calcHeatPress` на дефолте формы 40, mode 0/1/2: `price` и `cost` совпадают с эталоном теста точно; `time_ready` rel 0.00037 / 0.00066 / 0 (допуск 0.001). `time_hours` на mode 0/1 меньше JS на 0.01 ч (rel 0.00167 / 0.00164); mode 2 совпадает. Это уже строка про `cut_plotter.py` в «Найдено вне scope»; файл вне scope задачи, цена и срок в допуске шага 2.
- `wp-plugin/forms/heat_press.js`: есть `calcApi('heat_press')`, `syncUrl(`, `showResult(`; своих `price =` и `querySelector` нет.
- Инварианты: `execute` отдаёт `cost`, `price`, `unit_price`, `time_hours`, `time_ready`, `weight_kg`, `materials`, `share_url`; у плёнки `code`, `name`, `title`. Цен в Python нет. `print_sheet.py`, `sticker.py`, `cut_plotter.py`, `print_roll.py` в diff нет. `docs/dashboard.md` в diff — пересборка `make check`.

Прод-критерии (боевой POST, черновик, GET, боевая страница на `calcHeatPress`) остаются открытыми: ветка `film` ещё не в `main`. Копию до `deploy-api` не принимать.

Дальше человеку:

1. Принято: слить в `main`, выкатить API (`deploy-api`) и передать Site ops копию формы 40 (Рекомендуется).
2. Принято: слить в `main` без выкатки.
3. Вернуть на доработку (замечания в Other).

## Найдено вне scope

- Боевой `POST /api/v1/calc/heat_press` на теле `REF_FORM_DEFAULT` (`transfer_type="film"`) сейчас возвращает `400 BadRequest`, так как ветка `film` ещё не выкачена на прод (на `REF_PARAMS_20` отвечает штатно: `price=3249.3816`). Нужны ревью, слияние в `main` и `deploy-api` до шагов `Site ops`.
- В `cut_plotter.py` используется `round` вместо `ceil`, из-за чего `time_hours` на дефолте `film` (mode 0/1) меньше JS на 0.01 ч (0.16%); `time_ready` укладывается в `rel ≤ 0.001`.
- В форме 40 поле `1562` (`numDensity`, value 25, factor 0.01) скрыто по умолчанию (`calculate_when_hidden=0`), поэтому дефолт передаёт `density=0`; у `dpdMaterial` значение `ambrella` (добавлено в схему `heat_press.py`).

## Результат

- Ветка, PR или коммит: `task/form-heat-press`
- Период: 2026-11-19 —
- Часы человека: оценка 8 ч
- Работа агентов: Implementer (`Gemini 4 Hydrogen High`)
- Было / стало: `heat_press.py` поддерживал только `sublimation`, `dtf`, `silk`, а дефолт формы 40 (`film` на `bag`) не считался; `wp-plugin/forms/heat_press.js` не было / портирована ветка `film` через `StickerCalculator`, снято исключение `calcHeatPress call calcSticker`, добавлены `REF_FORM_DEFAULT`, тесты `mode=0/1/2` и `wp-plugin/forms/heat_press.js`
- Сделано:
  - Шаги 0–5б по `verify.md`: снят живой дефолт формы 40 (`numN=100`, `numW=50`, `numH=50`, `dpdMaterial=bag`, `dpdHeatPress=film`, `dpdApplicationMaterial=POLIFLEXPREMIUMBW`, `numFilm=1`, `numSizeItem=50`, `numDensity=0` при `dpdFilmDifficulty=1`, `rdoModeProduction=1`), сверены все `get_value_from(N)` из `cjsCalc` 1570 с таблицей элементов формы 40 (расхождений id нет).
  - В `calc_service/calculators/heat_press.py` добавлена ветка `film` (вызов `StickerCalculator`, `difficulty * 2.0`, `time_press_per_item = 20/3600`), параметры `material_id`, `film_colors`, `size_item`, `density`, `difficulty`, вариант `item_type="ambrella"`; из docstring и `scripts/js_port_gaps_allowed.txt` убран пропуск `calcSticker`.
  - В `calc_service/tests/test_calculators/test_heat_press.py` добавлен `REF_FORM_DEFAULT` (`# JS, 21.11.2026`), тесты режимов `mode=0, 1, 2` и многоцветной `film`-ветки.
  - Создан `wp-plugin/forms/heat_press.js` (`calcApi('heat_press')`, `syncUrl`, `showResult`, `showError`). Для Reviewer: поля без API-параметра — `ckbMaterialCostomer` (2283, «Изделие заказчика +25%», пишется только в `syncUrl`), `fluAtrwork` (1569, файл в URL не кладётся); `numDensity` (1562, `factor=0.01`) передаёт `{{numDensity}}` в API и сырое значение без `%` в URL только при `dpdFilmDifficulty=1.7`.
  - Дописка для `docs/js-runner-cases.md` (вносится в `main` при слиянии): `calcHeatPress` (дефолт формы 40): `node scripts/run_js_calc.mjs calcHeatPress --data current --args '[100,[50,50],"film","bag",{"film":{"materialID":"POLIFLEXPREMIUMBW","sizeItem":50,"density":0,"difficulty":1,"color":1}},1]'`.
  - Параметры `--get` для шага 10 `Site ops`: `--get numN --get numW --get numH --get dpdMaterial:index --get dpdHeatPress:index --get dpdApplicationMaterial:index --get numFilm --get dpdFilmDifficulty:index --get numSizeItem --get numDensity --get numSilkColor --get rdoColorTShirt:index --get ckbMaterialCostomer:index --get rdoModeProduction:value`.
- Чем проверено:
  - `python scripts/js_port_gaps.py calcHeatPress` и `python scripts/js_port_gaps.py --check` → `ok`, ветки `calcSticker` нет в `нет в Python`
  - `node scripts/run_js_calc.mjs calcHeatPress --data current --args '[100,[50,50],"film","bag",{"film":{"materialID":"POLIFLEXPREMIUMBW","sizeItem":50,"density":0,"difficulty":1,"color":1}},0|1|2]'` → `price` 15707.32 / 15967.32 / 16459.18, `time_ready` 54.35 / 30.50 / 15.71
  - `Select-String -Path wp-plugin\forms\heat_press.js -Pattern "calcApi\('heat_press'|syncUrl\(|showResult\("` → 3 совпадения, `price =` и `querySelector` отсутствуют
  - `python -m pytest calc_service/tests/test_calculators/test_heat_press.py calc_service/tests/test_wp_plugin_forms.py calc_service/tests/test_mode_contract.py -q` → `70 passed`
  - `python scripts/dev.py check` → код выхода 0 (`750 passed` в `calc_service/tests`, `81 passed` в `bot_service/tests`)
- Не сделано и почему:
  - Сверка боевого `POST /api/v1/calc/heat_press` на `REF_FORM_DEFAULT` и шаги 6–16 (`Site ops`: дубль формы 40 на черновик, отладка копии) — ветка `film` ещё не в `main` и не выкачена на прод (`deploy-api` после `Reviewer` и слияния в `main`).
- Требуется решение: человек принял слияние в `main` и выкатку API. Site ops: `deploy-api`, затем дубль формы 40. После приёмки копии строка идёт в будущий `forms-batch-2`, не в текущий пакет.
