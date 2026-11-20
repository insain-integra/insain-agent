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
- 21.11.2026, человек на приёмке копии: пока не считаются «Изделие заказчика» (элемент 2283) и ветки `filmSublimation`, `filmEcosolvent`, `paperLaser`, копию не принимать. Эти три ветки и наценку изделия заказчика перенести, эталон — раннер. Чужие калькуляторы не менять. Остальное из «не перенесено» (в частности `calcCutSaber` в `dtf`) не разгребать, если эти ветки его не вызывают.

## Файлы

- `wp-plugin/forms/heat_press.js`
- `calc_service/calculators/heat_press.py`
- `calc_service/tests/test_calculators/test_heat_press.py`
- `scripts/js_port_gaps_allowed.txt` — только снять строку, если её вызов появился в `heat_press.py`
- WordPress: только копия формы 40 и её черновик

## Не-scope

- `todo/forms-batch-switch.md`, `docs/site/forms.md`, `docs/js-runner-cases.md`
- `print_sheet.py`, `sticker.py`, `cut_plotter.py`, `print_roll.py` и их тесты
- Ветки трансфера, которые дефолт формы не вызывает, кроме `filmSublimation`, `filmEcosolvent`, `paperLaser` и наценки «Изделие заказчика» (решение человека 21.11.2026)
- Боевая форма 40, выкладка плагина, JSON цен, `calc_service/calculators/__init__.py`

## Критерии приёмки

- [x] `python scripts/js_port_gaps.py calcHeatPress` — у каждой непустой строки `нет в Python` есть пара: docstring и `scripts/js_port_gaps_allowed.txt`. Ветка дефолта формы в `нет в Python` не числится. `python scripts/js_port_gaps.py --check` печатает `ok`.
- [x] `python -m pytest calc_service/tests/test_calculators/test_heat_press.py calc_service/tests/test_wp_plugin_forms.py -q` — `passed`. Есть `REF_FORM_DEFAULT` с `# JS,`. Соседние тесты печати и резки, если их не меняли, зелёные в `make check`.
- [ ] Боевой `POST /api/v1/calc/heat_press` на теле `REF_FORM_DEFAULT` (а также `is_customer_material`, `filmSublimation`, `filmEcosolvent`, `paperLaser` после выкатки): `price` и `time_ready` как у раннера (допуск цены abs ≤ 0.02 или rel ≤ 0.001, срока rel ≤ 0.001). Если порт ещё не выкачен — пункт после `deploy-api`, копию до него не принимать.
- [x] `Select-String -Path wp-plugin\forms\heat_press.js -Pattern "calcApi\('heat_press'|syncUrl\(|showResult\("` — все три есть. Своей `price` и `querySelector` нет.
- [x] Копия не на витрине: `draft` или `private`, гость без cookies — не `200`.
- [ ] На копии под админом дефолт, «Изделие заказчика +25%» и способы печати (`filmSublimation`, `filmEcosolvent`, `paperLaser`) дают `POST /api/v1/calc/heat_press` → 200. Цена на странице = `price` API с округлением `showResult`.
- [x] URL копии обновляется GET-именами формы 40. Ссылка с этими GET открывает те же значения и ту же цену.
- [x] Боевая страница в HTML содержит `calcHeatPress`, не `calcApi`.

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
21.11.2026 — Site ops, Grok 4.7 — API `17b84f8` выкачен, дефолт сошёлся с раннером, копия формы 105 на черновике 2586901; боевая 40 не переключена — дальше Reviewer
21.11.2026 — Reviewer, Grok 4.7 — принято: API `17b84f8`, POST дефолта в допуске, копия 105 на черновике 2586901 считает heat_press, боевая 40 на calcHeatPress — дальше человек
21.11.2026 — человек — копия не принята: не работает «Изделие заказчика» и способы печати (плёнка с полноцветной сублимацией, плёнка с полноцветным экосольвентом, полноцветная термобумага) — дальше Implementer
21.11.2026 — Implementer, Gemini 4 Hydrogen High — доработка: в heat_press.py добавлены is_customer_material (+25% к цене, как cjsCalc 1570), filmSublimation, filmEcosolvent и paperLaser; обновлены heat_press.js, js_port_gaps_allowed.txt и эталоны раннера в test_heat_press.py; make check зелёный — дальше Reviewer
21.11.2026 — Reviewer, Grok 4.7 — принято: is_customer_material ×1.25 как cjsCalc 1570, ветки filmSublimation, filmEcosolvent и paperLaser сходятся с раннером по price и time_ready; чужие калькуляторы не менялись — дальше человек
21.11.2026 — человек — принято: закоммитить доработку, слить в main, выкатить API и обновить JS копии 105 — дальше Site ops

## Ревью 1

Вердикт: принято. Статус остаётся `ревью`.

Проверено по diff и командам в worktree:

- `python scripts/js_port_gaps.py calcHeatPress`: у `calcHeatPress` в `нет в Python` только `call calcLayoutOnSheet`, `call calcCutPlotter`, `call calcPrintRoll`, `call calcCutSaber`. Каждая есть в docstring `heat_press.py` и в `scripts/js_port_gaps_allowed.txt`. `call calcSticker` в пропусках нет. `python scripts/js_port_gaps.py --check` → `ok`.
- `python -m pytest calc_service/tests/test_calculators/test_heat_press.py calc_service/tests/test_wp_plugin_forms.py calc_service/tests/test_mode_contract.py -q` → `70 passed`. `REF_FORM_DEFAULT` с пометкой `# JS, 21.11.2026`.
- Раннер `calcHeatPress` на дефолте формы 40, mode 0/1/2: `price` и `cost` совпадают с эталоном теста точно; `time_ready` rel 0.00037 / 0.00066 / 0 (допуск 0.001). `time_hours` на mode 0/1 меньше JS на 0.01 ч (rel 0.00167 / 0.00164); mode 2 совпадает. Это уже строка про `cut_plotter.py` в «Найдено вне scope»; файл вне scope задачи, цена и срок в допуске шага 2.
- `wp-plugin/forms/heat_press.js`: есть `calcApi('heat_press')`, `syncUrl(`, `showResult(`; своих `price =` и `querySelector` нет.
- Инварианты: `execute` отдаёт `cost`, `price`, `unit_price`, `time_hours`, `time_ready`, `weight_kg`, `materials`, `share_url`; у плёнки `code`, `name`, `title`. Цен в Python нет. `print_sheet.py`, `sticker.py`, `cut_plotter.py`, `print_roll.py` в diff нет. `docs/dashboard.md` в diff — пересборка `make check`.

Прод-критерии на момент ревью 1 были открыты: ветка `film` ещё не была в `main`. Site ops закрыл их после выкатки `17b84f8` — см. «Результат».

Дальше человеку:

1. Принято: слить в `main`, выкатить API (`deploy-api`) и передать Site ops копию формы 40 (Рекомендуется).
2. Принято: слить в `main` без выкатки.
3. Вернуть на доработку (замечания в Other).

## Найдено вне scope

- До выкатки боевой `POST /api/v1/calc/heat_press` на `REF_FORM_DEFAULT` (`transfer_type="film"`) возвращал `400`. После `deploy-api` `17b84f8` тот же POST → 200, `price` совпадает с раннером. Пункт закрыт.
- В `cut_plotter.py` используется `round` вместо `ceil`, из-за чего `time_hours` на дефолте `film` (mode 0/1) меньше JS на 0.01 ч (0.16%); `time_ready` укладывается в `rel ≤ 0.001`. На боевом API после выкатки то же: `time_hours` 6.071 против раннера 6.081, `time_ready` rel 0.00066. На доработке то же у `filmSublimation` и `filmEcosolvent`: оба времени меньше раннера на 0.01 ч; на 100×50×50 mode 1 `time_ready` rel 0.00029 и 0.00033. `paperLaser` резку не вызывает, `time_hours` и `time_ready` совпали точно.
- В форме 40 поле `1562` (`numDensity`, value 25, factor 0.01) скрыто по умолчанию (`calculate_when_hidden=0`), поэтому дефолт передаёт `density=0`; у `dpdMaterial` значение `ambrella` (добавлено в схему `heat_press.py`).
- На тех же дефолтах строка «со скидкой»: копия `12 939` (`showResult` от `cost` API), боевая старая форма `12 926`. Менеджерская цена `16 000` и срок «4 дня» совпали. Формула скидки старого JS не чинилась.
- В `filmEcosolvent` возвращаемый `PrintRollCalculator` элемент `materials` (`POLIFLEX4030`) не содержит `size_mm` (в отличие от `film` и `paperLaser`); `print_roll.py` вне scope задачи.
- В `paperLaser` `weight_kg` считается по изделию в `print_sheet.py` (`0.0341`), тогда как JS считает по целому листу с обрезью (`0.0505`) — принятое правило для цепочек `calcPrintSheet` (11.11.2026).

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
- Не сделано и почему (Implementer): сверка боевого POST и копия — тогда ещё не было выкатки. Сделано Site ops ниже.
- Доработка 21.11.2026 (Implementer):
  - Сделано:
    - В `calc_service/calculators/heat_press.py` добавлена поддержка:
      1) `is_customer_material` (элемент 2283 `ckbMaterialCostomer='isMaterialCustomer'`): как в `cjsCalc` (1570) боевой формы 40, коэффициент `1.25` умножает итоговую цену `price_total` (и `unit_price`), а `cost_total` не меняется;
      2) `filmSublimation` — раскладка на `PaperSublimation128` через `layout_on_sheet` (отступы плоттера `[top, right, bottom, left]`, интервал 2), рекурсивный `self.calculate` (`sublimation`, `tshirt`), плоттерная резка `CutPlotterCalculator` на `POLIFLEX4675` (`is_find_mark=True`, `density=1.0`, `difficulty=1.7`, `size_item=max(size)`), `time_press_per_item=45/3600`;
      3) `filmEcosolvent` — печать `PrintRollCalculator` (`POLIFLEX4030`, `Technojet160ECO`) и плоттерная резка `CutPlotterCalculator` (`POLIFLEX4030`, `is_find_mark=True`, `density=1.0`, `difficulty=1.7`, `size_item=max(size)`), `time_press_per_item=15/3600`;
      4) `paperLaser` — печать `PrintSheetCalculator` (`PaperFOREVERLASERTRANSPARENT`, `KMBizhubC220`, `4+0`, `margins=[2,2,2,2]`, `interval=2`), `time_press_per_item=45/3600`.
    - Из `scripts/js_port_gaps_allowed.txt` и docstring `heat_press.py` сняты `calcHeatPress call calcLayoutOnSheet`, `calcHeatPress call calcCutPlotter`, `calcHeatPress call calcPrintRoll` (оставлен только `calcCutSaber`).
    - В `wp-plugin/forms/heat_press.js` поле `ckbMaterialCostomer` (2283) теперь передаётся в `calcApi('heat_press', params)` как `is_customer_material` (и по-прежнему пишется в `syncUrl`).
    - В `calc_service/tests/test_calculators/test_heat_press.py` добавлены тесты с эталонами раннера (`test_customer_material_markup`, `test_film_sublimation_modes`, `test_film_ecosolvent_modes`, `test_paper_laser_modes`, `test_new_transfer_types_mode_order`).
    - Дописка для `docs/js-runner-cases.md` (вносится в `main` при слиянии):
      - `calcHeatPress` (`filmSublimation`): `node scripts/run_js_calc.mjs calcHeatPress --data current --args '[100,[50,50],"filmSublimation","bag",{},1]'`
      - `calcHeatPress` (`filmEcosolvent`): `node scripts/run_js_calc.mjs calcHeatPress --data current --args '[100,[50,50],"filmEcosolvent","bag",{},1]'`
      - `calcHeatPress` (`paperLaser`): `node scripts/run_js_calc.mjs calcHeatPress --data current --args '[100,[50,50],"paperLaser","bag",{},1]'`
  - Чем проверено:
    - `python scripts/js_port_gaps.py calcHeatPress` и `python scripts/js_port_gaps.py --check` → `ok`, в `нет в Python` только `call calcCutSaber`
    - `node scripts/run_js_calc.mjs calcHeatPress --data current --args '[100,[50,50],"filmSublimation"|"filmEcosolvent"|"paperLaser","bag",{},0|1|2]'` → эталоны совпали с `test_heat_press.py`
    - `Select-String -Path wp-plugin\forms\heat_press.js -Pattern "calcApi\('heat_press'|syncUrl\(|showResult\("` → 3 совпадения, `price =` и `querySelector` отсутствуют
    - `python -m pytest calc_service/tests/test_calculators/test_heat_press.py calc_service/tests/test_wp_plugin_forms.py calc_service/tests/test_mode_contract.py -q` → `83 passed`
    - `python scripts/dev.py check` → код выхода 0 (`763 passed` в `calc_service/tests`, `81 passed` в `bot_service/tests`)
  - Не сделано и почему: выкатка API (`deploy-api`) и обновление JS элемента 3905 копии 105 (`Site ops`) — после ревью и слияния в `main`.
  - Требуется решение: ревью доработки (`Reviewer`), затем слияние в `main`, `deploy-api` и обновление копии 105 (`Site ops`).
- Site ops, 21.11.2026:
  - Сделано: `bash infra/deploy.sh` на VDS, `41ff806` → `17b84f8`. Дубль формы 40 → форма **105** «CalcHeatPress duplicate». Товар **2586901** «Калькулятор нанесения на одежду (Копировать)», `post_status=draft`, `ezfc_form_id` был 40, стал 105. Боевой товар 2586662 остался `publish` и `ezfc_form_id=40`. JS копии записан в элемент 3905 (`read_file=0`, `calcApi=1`), GET проставлены. Плагин не выкладывался. Боевая форма 40 и страница каталога не переключались. Шаги 17–24 не делались.
  - Чем проверено:
    - Smoke деплоя: `GET /api/v1/calculators` → 200, `POST /api/v1/calc/puzzle` → 200, контейнер `insain-calc-api` healthy. В списке калькуляторов есть `heat_press`.
    - Раннер `calcHeatPress` на дефолте mode 1: `price` 15967.324482222226, `time_ready` 30.501111111111115.
    - Боевой `POST /api/v1/calc/heat_press` на `REF_FORM_DEFAULT` → 200: `price` 15967.324482222226 (abs 0), `time_ready` 30.48111111111111 (rel 0.00066 ≤ 0.001).
    - Гость: `curl` `https://insain.ru/?post_type=product&p=2586901` → **404**.
    - Копия под админом, дефолт: `POST /api/v1/calc/heat_press` → 200, тело `transfer_type=film`, `item_type=bag`, `material_id=POLIFLEXPREMIUMBW`, `mode=1`. На странице **16 000 руб.** и **160 руб./шт** — это `insaincalc.round(15967.32, 100)`. Срок «4 дня», подсказка с датами есть. Материалы: название, размер `500,0`, кол-во `0.74`, кода `POLIFLEXPREMIUMBW` в таблице нет.
    - Смена плёнки → `material_id=POLIFLEXPREMIUMCOLOR`, цена 15 800, в таблице цветная плёнка, URL `dpdApplicationMaterial=1`. Смена изделия → `item_type=tshirt`, цена 8 400. Смена сложности → URL `dpdFilmDifficulty=2` и `numDensity=25`, цена 9 500. DTF → `transfer_type=dtf`, цена 10 000, материал «Пленка для DTF трансферов».
    - GET-ссылка дефолта снова открывает сумку, плёнку, белую/чёрную, простую форму, 16 000 руб., «4 дня». Перезагрузка режим и срок не меняет. «быстрее» пишет `rdoModeProduction=2` (value, не index), цена 16 500, срок «2 дня»; перезагрузка это сохраняет.
    - Боевая страница на тех же дефолтах: «16 000 руб.», «Срок 4 дня». HTML содержит `calcHeatPress`, вызова `calcApi` нет.
    - Консоль копии: ошибки только `insainParse` (`options` / `querySelector`), сообщений `insaincalc` и `ezfc` нет.
    - `wp litespeed-purge all` вернул `Error: Something went wrong! Got 400`. `wp cache flush` — `Success`. Превью копии после этого отдало новый JS.
  - Не сделано и почему: шаги 17–24 (боевая форма, снимок, реестр) вне scope. Плагин не выкладывался: JS копии лежит в элементе. Строка пакета не записана в `todo/forms-batch-switch.md` — форма 40 в текущий пакет не входит.
  - Как откатить: JS и GET копии — пакет `/tmp/ezfc-copy-105-20261120-210659.json` (бэкап `ezfc_copy_apply.php`). Черновик 2586901 снять с витрины не нужно: он уже `draft`, гость получает 404. API — образ `insain-agent-calc-api:rollback` снят с коммита `41ff806` до этой выкатки; повторный деплой тег перезапишет.
  - Строка для будущего пакета (`forms-batch-2`, не текущий `forms-batch-switch`): `| 40 CalcHeatPress | heat_press | /catalog/kalkulyator-naneseniya-na-odezhdu/ | 105 / 2586901 (draft) | form-heat-press, копия 21.11.2026 |`
  - URL копии: `https://insain.ru/?post_type=product&p=2586901&preview=true`
  - GET дефолта: `https://insain.ru/?post_type=product&p=2586901&preview=true&numN=100&numW=50&numH=50&dpdMaterial=4&dpdHeatPress=0&dpdApplicationMaterial=0&numFilm=1&dpdFilmDifficulty=0&numSizeItem=50&rdoModeProduction=1`

## Ревью 2

Вердикт: принято. Статус: `закрытие`.

Приёмка отчёта Site ops. Повторный разбор diff до слияния не делался. Сверено с main командами:

- VDS `/opt/insain-agent`: HEAD `17b84f8f9a3da00e92a2f9d0bd6164e6b417d3a7`, дерево чистое. Коммит включает `d2dc227` (ветка `film`).
- Боевой `POST /api/v1/calc/heat_press` на теле `REF_FORM_DEFAULT` → 200. `price` 15967.324482222226, abs 0 к эталону раннера. `time_ready` 30.48111111111111 против 30.501111111111115, rel 0.00066 (допуск 0.001).
- Товар 2586901: `draft`, `ezfc_form_id=105`, единственный товар с формой 105. Гость без cookies: `?p=2586901` и `preview=true` → 404.
- Элемент 3905 (`cjsCalc`, `read_file=0`): `insaincalc.calcApi('heat_press'`, `syncUrl`, `showResult`. В этом JS нет `calcHeatPress`, `querySelector` и `price =`. GET у полей дефолта записаны; у `rdoModeProduction` стоит `value`, у dropdown с кодом — `index`.
- Боевой товар 2586662: `publish`, `ezfc_form_id=40`. Элемент 1570: в JS есть `calcHeatPress`, вызова `calcApi` нет. Страница каталога: `calcHeatPress` — 2 вхождения, `calcApi` — 0.
- Шаги 17–24 не делались. Общие файлы не менялись: в рабочей копии грязный только `todo/form-heat-press.md`.

Загрузчик копии (элемент 3885) по-прежнему содержит строку `calcHeatPress`. Расчёт идёт из `cjsCalc` через `calcApi`. Это не блокер.

Дальше человеку — вид копии, затем закрытие. Открыть `https://insain.ru/?post_type=product&p=2586901&preview=true` и GET дефолта из «Результата». Ожидается POST `heat_press`, **16 000 руб.**, **160 руб./шт**, срок «4 дня». Каталог https://insain.ru/catalog/kalkulyator-naneseniya-na-odezhdu/ остаётся на старом калькуляторе.

1. Принять копию и закрыть задачу (Рекомендуется).
2. Копия не сошлась по виду — вернуть Site ops с тем, что на экране.
3. Вернуть с другим блокером (через Other).

## Ревью 3

Вердикт: принято. Статус остаётся `ревью`. Блокеров нет.

Доработка не закоммичена: ветка `task/form-heat-press` указывает на тот же коммит, что и `main` (`62f1805`), правки только в рабочей копии. В diff относительно `main`: `heat_press.py`, `test_heat_press.py`, `wp-plugin/forms/heat_press.js`, `scripts/js_port_gaps_allowed.txt`, `todo/form-heat-press.md`, `docs/dashboard.md` (пересборка `make check`, статус задачи `ревью`). `print_sheet.py`, `sticker.py`, `cut_plotter.py`, `print_roll.py` в diff нет.

Проверено:

- `is_customer_material`: в cjsCalc боевой формы 40 (элемент 1570, страница каталога) `get_value_from(2283, true)[0] == 'isMaterialCustomer'` ставит `coeff = 1.25`; `PriceTotalManager = round(calcCost.price * coeff, тираж)`, `PriceTotalDiscount = calcCost.cost * (1+marginMin)`, срок и себестоимость без коэффициента. Чекбокс 2283: `data-value` и `data-factor` равны `isMaterialCustomer`, подпись «Изделие заказчика +25%». В `heat_press.py` тот же множитель только на `price` и `unit_price`. На дефолте формы и на `filmSublimation` mode 1 цена Python = цена раннера × 1.25 (abs 0), `cost` и `time_ready` не меняются. `heat_press.js` читает 2283 так же и передаёт boolean в `calcApi`; `syncUrl` по-прежнему пишет индекс `0`.
- Раннер `calcHeatPress` против `HeatPressCalculator.execute` на `filmSublimation`, `filmEcosolvent`, `paperLaser` (100 шт, 50×50, bag, mode 0/1/2): `price` и `cost` abs 0. `time_ready` у веток с плоттером rel 0.00029–0.00033 (допуск 0.001); у `paperLaser` abs 0. Дополнительно 10×180×40 `filmSublimation`, 10×200×280 `paperLaser`, 5×90×120 `filmEcosolvent` mode 2: `price` abs 0, `time_ready` rel ≤ 0.00095. Раскладка `filmSublimation` переставляет отступы плоттера `[left, top, right, bottom]` в `[top, right, bottom, left]`, как `cut_plotter.py` и `calcLayoutOnSheet`.
- В `materials` есть `code`, `name`, `title`. У `filmSublimation` в списке только бумага сублимации: JS сливает `costTransfer.material` и не добавляет плёнку резки. Цен в Python нет, `1.25` — коэффициент формы, не цена из JSON.
- `python scripts/js_port_gaps.py calcHeatPress`: в `нет в Python` только `call calcCutSaber` (ветка `dtf`, эти три ветки её не вызывают). Строка есть в docstring и в `js_port_gaps_allowed.txt`. `python scripts/js_port_gaps.py --check` → `ok`.
- `python -m pytest calc_service/tests/test_calculators/test_heat_press.py calc_service/tests/test_wp_plugin_forms.py -q` → `32 passed`. Новые тесты: `test_customer_material_markup`, `test_film_sublimation_modes`, `test_film_ecosolvent_modes`, `test_paper_laser_modes`, `test_new_transfer_types_mode_order`.
- `heat_press.js`: есть `calcApi('heat_press')`, `syncUrl(`, `showResult(`; своих `price =` и `querySelector` нет.

Прод-критерии остаются открытыми: боевой POST новых веток и копия 105 — после коммита, слияния и `deploy-api`. Боевая форма 40 не переключается.

Дальше человеку:

1. Принято: закоммитить доработку, слить в `main`, выкатить API (`deploy-api`) и обновить JS копии 105 (Site ops) (Рекомендуется).
2. Принято: закоммитить и слить в `main` без выкатки.
3. Вернуть на доработку (замечания в Other).

## Промпт следующей сессии

Ревью 3 принято. Следующий шаг — выбор человека (слияние, `deploy-api`, обновление копии 105). Промпт Site ops пишется после этого выбора. Доработку сначала закоммитить: она лежит в рабочей копии `task/form-heat-press`, указатель ветки всё ещё `62f1805`.
