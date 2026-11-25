# form-tablets

Статус: выкатка
Сложность: средняя
Implementer: Gemini 4 Hydrogen High
Reviewer: Grok 4.7
Site ops: Grok 4.7
Почему: лид-копия slug `tablets` на пять боевых форм (с формой 68); 14 пропусков `calcTablets` в allowed, часть — вызовы чужих калькуляторов; порт может понадобиться в том же diff.

## Цель

Копия формы 36 CalcTabs на черновике товара считает `POST /api/v1/calc/tablets`. URL копии пишется GET-именами элементов. Ссылка с этими GET открывает ту же копию с теми же значениями и той же ценой. Боевая страница https://insain.ru/catalog/tablichki-s-uf-pechatyu/ остаётся на `insaincalc.calcTablets`. Боевое переключение отложено решением человека 22.11.2026. Формы 48, 51, 76 и 68 — отдельными задачами после приёмки этой копии. Форма 68 CalcShild вызывает `calcTablets` и переводится через slug `tablets`, не `shild` (решение человека 22.11.2026).

## Контекст и ссылки

- `.cursor/skills/ezfc-form-to-api/SKILL.md`, этапы `verify.md` и `copy.md`. Шаги 17–24 не входят.
- `docs/ezfc-api-migration.md` — GET = имя элемента.
- `docs/site/forms.md` — строки форм 36, 48, 51, 68, 76 (`insaincalc.calcTablets`), только читать.
- `calc_service/calculators/tablets.py`, `calc_service/tests/test_calculators/test_tablets.py`.
- `js_legacy/calc/calcTablets.js`, функция `calcTablets` — эталон; подключён в `scripts/run_js_calc.mjs`.
- `scripts/js_port_gaps_allowed.txt` — строки `calcTablets` (14 штук).
- `todo/EPIC-forms-to-api.md` — пачка 6.
- Остальное не открывать.

## Scope

- В git (Implementer), сверка: раннер против `tablets.py` на дефолтах форм 36, 48, 51, 76 и 68. Итог — таблица «форма → `price` / `time_ready` JS и API, какие пропуски задевает» в «Результат»; для 68 — отдельная строка, что она идёт через `tablets`.
- В git (Implementer), лид: шаги 0–5б для формы 36 и `wp-plugin/forms/tablets.js` с привязкой к id 36. `REF_FORM_DEFAULT` в `test_tablets.py` с пометкой `# JS, ДД.ММ.ГГГГ`. Портировать в `tablets.py` только ветки, без которых дефолт формы 36 не сходится по цене и сроку, и снять их строки из allowed. Вызов в JS — вызов уже существующего порта в Python (`milling`, `print_roll`, `sticker`, `cut_roller`); чужие калькуляторы не менять. Если дефолту формы 36 нужен вызов, у которого порта в Python нет (`calcManualRoll`, `calcPockets`, `calcFrame`), — стоп со статусом `заблокировано: аналитик`. Калькулятор не на боевой форме API, предпосылку не заводить. Новые строки в allowed не добавлять.
- На проде (Site ops): дубль формы 36 на черновик после совпадения дефолта с боевым API. Если порт менял ответ — сначала `deploy-api` с `main`, потом дубль. JS копии в элементе (`read_file=0`). Плагин не выкладывать. Боевую 36 не переключать.
- Строка для будущего боевого пакета и дописка для `docs/js-runner-cases.md` — в «Результат», не в общие файлы.

## Файлы

- `wp-plugin/forms/tablets.js`
- `calc_service/calculators/tablets.py`
- `calc_service/tests/test_calculators/test_tablets.py`
- `scripts/js_port_gaps_allowed.txt` — только снять строки `calcTablets`, если ветка портирована
- WordPress: только копия формы 36 и её черновик

## Не-scope

- `todo/forms-batch-switch.md`, `docs/site/forms.md`, `docs/js-runner-cases.md`, `scripts/run_js_calc.mjs`
- Копии форм 48, 51, 76, 68; ветки, которые дефолт формы 36 не вызывает; модули `calcPockets`, `calcPutTape`, `calcFrame`
- `shild.py` (`calcShild.js`), `plaque.py` (`calcPlaque` из того же `calcTablets.js`), `puzzle.py` и строки `calcPuzzle` / `calcShildSublimaton` в allowed
- Чужие калькуляторы `milling.py`, `print_roll.py`, `sticker.py`, `cut_roller.py` и их тесты
- Боевые формы 36, 48, 51, 68, 76 и шаги 17–24, выкладка плагина, JSON цен, `calc_service/calculators/__init__.py`

## Критерии приёмки

Каждый пункт — команда и ожидаемый результат.
Скрипт через `@'…'@ | python -` в PowerShell 5.1 — первой строкой `$OutputEncoding = New-Object System.Text.UTF8Encoding $false`, иначе кириллица в нём станет `?`.

- [x] В «Результат» есть таблица сверки дефолтов форм 36, 48, 51, 76, 68 (`price` / `time_ready` JS и API, задетые пропуски).
- [x] `python scripts/js_port_gaps.py calcTablets` — каждый пропуск либо снят, либо назван в docstring и остаётся в allowed. `python scripts/js_port_gaps.py --check` печатает `ok`.
- [x] `python -m pytest calc_service/tests/test_calculators/test_tablets.py calc_service/tests/test_calculators/test_plaque.py calc_service/tests/test_wp_plugin_forms.py -q` — `passed`. Есть `REF_FORM_DEFAULT` с `# JS,`; эталоны `plaque` и прежние эталоны `tablets` не сдвинулись или сдвиг объяснён раннером в «Результат».
- [ ] Боевой `POST /api/v1/calc/tablets` на теле `REF_FORM_DEFAULT`: `price` и `time_ready` как у раннера (допуск цены abs ≤ 0.02 или rel ≤ 0.001, срока rel ≤ 0.001). Если порт ещё не выкачен — пункт после `deploy-api`, копию до него не принимать.
- [x] `Select-String -Path wp-plugin\forms\tablets.js -Pattern "calcApi\('tablets'|syncUrl\(|showResult\("` — все три есть. Своей `price` и `querySelector` нет.
- [ ] Копия не на витрине: `wp post get <product> --field=post_status` → `draft` или `private`; `curl.exe -s -o NUL -w "%{http_code}"` гостем — не `200`.
- [ ] На копии под админом дефолт даёт `POST /api/v1/calc/tablets` → 200. Цена на странице = `price` API с округлением `showResult`.
- [x] `curl.exe -s https://insain.ru/catalog/tablichki-s-uf-pechatyu/` — в HTML есть `calcTablets`, нет `calcApi`.

### Критерии перевода формы ezFC на API

- [ ] URL обновляется GET-именами формы; ссылка с GET открывает форму с теми же значениями и той же ценой.

## Проверки

- [x] `make check` (или `python scripts/dev.py check`) — зелёный вывод
- [x] Self-review — чеклист «Перед сдачей» в [AGENTS.md](../AGENTS.md)

## Риски

- Прод: боевые формы `calcTablets` не меняются. Выкатка API — только если менялся калькулятор, с `main` после ревью. Запись в формы не параллельно с `todo/ezfc-options-source-reset.md`.
- Цены: JSON не менять. Порт веток может сдвинуть ответ `tablets` для форм 48, 51, 76, 68 — прежние эталоны теста держат это.
- Формы: id боевой 36 не менять; копия — новая форма на черновике.

## Режим

прод

## Журнал передач

Строка на сессию: `<дата> — <роль>, <модель> — <итог> — дальше <роль>`. Блокер — по формату
[docs/agents/workflow.md](../docs/agents/workflow.md). Замечания ревью — ниже, в «Ревью N».

22.11.2026 — человек — завести 8 лид-копий, боевые формы не переключать, форма 68 через tablets — дальше Implementer
26.11.2026 — Implementer, Gemini 4 Hydrogen High — сверка дефолтов 36/48/51/76/68, порт is_cut_manual и material_mode в tablets.py, REF_FORM_DEFAULT, wp-plugin/forms/tablets.js (id 36), make check зелёный — дальше Reviewer
26.11.2026 — Reviewer, Grok 4.7 — принято по diff, прод-критерии копии после deploy-api — дальше человек
26.11.2026 — человек — принято, слить и выкатить API, затем дубль формы 36 — дальше Site ops

## Ревью 1

принято

Diff `task/form-tablets` относительно `main`: `tablets.py`, `test_tablets.py`, `test_js_port_gaps.py` (`MAX_ALLOWED` 70→68 и проверка цепочки на `calcPockets` — по правилу файла при снятии двух строк allowed), `js_port_gaps_allowed.txt`, `wp-plugin/forms/tablets.js`. Чужие калькуляторы, JSON цен и боевая форма не затронуты.

- Раннер `calcTablets` на дефолте формы 36: `mode=1` → `price` 12754 / `time_ready` 52.82; `mode=0` → 11888 / 60.23; `mode=2` → 13625 / 45.43. `noMaterial` 12264 / 52.82, `isMaterialCustomer` 15262 / 53.84, двойное УФ 13288 / 52.94. Совпадает с `REF_FORM_DEFAULT` и `EXPECTED_FORM_DEFAULT_BY_MODE`.
- `python scripts/js_port_gaps.py calcTablets`: сняты `option isCutManual` и `call calcCutRoller`; остальные 12 пропусков названы в docstring `tablets.py` и остаются в allowed. `python scripts/js_port_gaps.py --check` → `ok`.
- `python -m pytest calc_service/tests/test_calculators/test_tablets.py calc_service/tests/test_calculators/test_plaque.py calc_service/tests/test_wp_plugin_forms.py calc_service/tests/test_js_port_gaps.py -q` → `60 passed`. Прежние эталоны `tablets` и `plaque` в diff не менялись.
- В `wp-plugin/forms/tablets.js` есть `calcApi('tablets'`, `syncUrl(`, `showResult(`; своих `price` и `querySelector` нет. Id полей совпадают с HTML боевой страницы формы 36 (расчёт 1348, материал 1339, режим материала 1340, раскрой 1371, нанесение 1368, режим 2003). Резаки `KeencutEvolutionE2` / `AccusheadPro12` и `PrintUV` — как в старом `cjsCalc`.
- `curl.exe -s` страницы табличек: в HTML есть `calcTablets`, вызова `calcApi` нет.

Прод-пункты (боевой POST на `REF_FORM_DEFAULT`, черновик копии, цена на копии, GET-ссылка) по задаче закрываются после `deploy-api` с `main`. Порт добавляет `is_cut_manual` в ответ `tablets`; на текущем проде этой ветки нет, копию до выкатки не принимать. Это не блокер diff.

Замечаний с меткой `блокер` нет.

## Найдено вне scope

- `scripts/run_js_calc.mjs`: для формы 51 (`CalcHashtags`) падает с `insaincalc.calcMilling is not a function` (не подключён `calcMilling.js`); для формы 68 (`CalcShild`) на дефолте с `materialID=""` падает с `Поле weight_kg не число (NaN)` (в `calcLaser.js` при пустом материале `weight` становится `NaN`).
- `ssh insain-prod` (5.181.252.133:22): в текущей сессии connection timed out — исходники форм 36/48/51/68/76 получены с опубликованных страниц (`curl.exe` + read-only Browser MCP). Для шагов Site ops понадобится рабочий SSH-доступ к VDS.

## Результат

- Ветка, PR или коммит: ветка `task/form-tablets` (worktree `..\insain-agent-form-tablets`, правки в working tree к ревью).
- Период: 2026-11-26 — 2026-11-26
- Часы человека: —
- Работа агентов: 1 сессия; Gemini 4 Hydrogen High
- Было / стало: 0 перенесённых веток ручной роликовой резки в `tablets.py` и 14 пропусков `calcTablets` в allowed / портированы `is_cut_manual` (`CutRollerCalculator`) + `material_mode` + `double_application`, в allowed осталось 12 строк `calcTablets`, добавлен `wp-plugin/forms/tablets.js` (id 36) и `REF_FORM_DEFAULT` (`mode=0,1,2`).
- Сделано:

### Сверка дефолтов форм (JS vs `tablets.py`)

| Форма | Вход дефолта | JS `price` / `time_ready` | API (`tablets.py` после порта) `price` / `time_ready` | Задетые пропуски (`allowed`) |
| --- | --- | --- | --- | --- |
| 36 `CalcTabs` | 100 шт, 50×50, `PVC5`, `isCutManual='KeencutEvolutionE2'`, `isUVPrint` (`PrintUV`, `4+0`, res=1), `isMaterial`, `mode=1` | `12754` / `52.82` (раннер; `mode=0`: `11888`/`60.23`, `mode=2`: `13625`/`45.43`) | `12754.0` / `52.82` (`mode=0`: `11888.0`/`60.23`, `mode=2`: `13625.0`/`45.43`) — **сходится** | До порта: `option isCutManual`, `call calcCutRoller` (оба портированы и сняты) |
| 48 `CalcStands` | 1 шт, 1000×1000, `PVC5`, `isCutManual='KeencutEvolutionE2'`, `isUVPrint` (`PrintUV`, `4+0`, res=0), карманы 0, профиль/подвес/EVA `no`, `mode=1` | `4780` / `48.9` (раннер) | `4780.0` / `48.9` (при наличии опций в форме заденет `isFilm`/`isBackgroundFilm`/`isEVAFoam`/`calcPockets`/`calcFrame`) | На чистом дефолте закрыто портом `is_cut_manual`; опции стендов остаются в allowed |
| 51 `CalcHashtags` | 1 шт, 1000×100, `PVC5`, `#хештег`, `isCutMilling`, `isUVPrint` (`PrintUV`, `4+0`, res=1), `mode=1` | `2388` (страница `2400`) / `56.38` (JS страницы; раннер падает: нет `calcMilling`) | `788.0` / `48.57` (без `is_cut_milling`, только `is_uv_print`) | `option isCutMilling`, `call calcMilling` |
| 76 `CalcTabs9May` | 1 шт, 297×420 (`A3`), `PVC5`, `isCutManual='KeencutEvolutionE2'`, `isPrint` (`Technojet160ECO`), `isShaft` (`PlasticShaft`, 1 м), `mode=1` | `2423.184` / `16.99` (раннер) | `807.0` / `8.36` (только `is_cut_manual`, без `isPrint` и `isShaft`) | `call calcPrintRoll`, `option isShaft` (+ `isPrint` в JS) |
| 68 `CalcShild` | 100 шт, 50×50, `materialID=""` («не задан материал»), `isCutLaser`, `isUVPrint` (`RimalSuvUV`, `4+1`, res=2), `mode=1` | `5792` (страница `5800`) / `36.88`, `weight=NaN` (JS страницы; раннер падает на `NaN`; с `AcrylWhite3`: `7908` / `37.35`) | `ValueError: material_id обязателен` (с первым материалом `AcrylWhite3`: `7908.0` / `37.35`) | Пропусков `calcTablets` не задевает; расхождение только на пустом `material_id=""` |

Форма 68 `CalcShild` вызывает `insaincalc.calcTablets` (не `calcShild`) и переводится отдельной задачей через slug `tablets` (не `shild`).

### Порт в `tablets.py` и `wp-plugin/forms/tablets.js`

- В `calc_service/calculators/tablets.py` перенесены `is_cut_manual` (вызов `CutRollerCalculator`), `material_mode` (`isMaterial` / `isMaterialCustomer` / `noMaterial`), `double_application` и `is_customer_material` для УФ-печати; добавлены в `get_tool_schema` и `get_param_schema`.
- Из `scripts/js_port_gaps_allowed.txt` сняты `calcTablets option isCutManual` и `calcTablets call calcCutRoller` (осталось 12 строк `calcTablets`, все названы в docstring `tablets.py`).
- В `calc_service/tests/test_js_port_gaps.py` уменьшен `MAX_ALLOWED` (`70 → 68`, по правилу файла при снятии строк из allowed) и в `test_report_follows_call_chain` проверка переключена с устранённого `calcCutRoller` на остающийся `calcPockets`.
- В `calc_service/tests/test_calculators/test_tablets.py` добавлены `REF_FORM_DEFAULT` (`# JS, 26.11.2026`), `EXPECTED_FORM_DEFAULT_BY_MODE` (`mode=0, 1, 2`), тесты монотонности режимов и режимов материала / двойного УФ; прежние эталоны `tablets` и `plaque` не сдвинулись.
- Написан `wp-plugin/forms/tablets.js` (привязка к id боевой формы 36 `CalcTabs`, элемент `cjsCalc` 1348).
  - Не-API поля формы 36 (пишутся в `syncUrl`, не уходят в `calcApi`): `dpdTypeCut` (1375), `dpdRollWideLaminat` (1429), `dpdEdge` (1477), `dpdApplicationMaterial` (1484), `numApplicationW` (1419), `numApplicationH` (1420), `numFilm` (1430), `numSizeItem` (1424), `numDensity` (1425), `dpdFilmDifficulty` (1423), `dpdBackgroudMaterial` (1427), `dpdBackroundEdge` (1483), `ckbShaft` (1533), `numLengthShaft` (1534), `chkAdhesiveLayer` (2718).
  - Неперенесённые ветки формы 36 (`isCutMilling`, `isECOPrint`, `isLatexPrint`, `isFilm`, `isShaft`, `chkAdhesiveLayer`) в `calcApi` не отправляются.

### Дописки для общих файлов (перенести при слиянии в `main`)

- Для `docs/js-runner-cases.md`:
  - Строка таблицы: ``| `calcTablets` form 36 default | `tablets` | 12754 |``
  - Команда: `node scripts/run_js_calc.mjs calcTablets --data current --args '[100,[50,50],"PVC5",{"isCutManual":"KeencutEvolutionE2","isUVPrint":{"printerID":"PrintUV","resolution":1,"surface":"isPlain","color":"4+0","isDoubleApplication":false},"Material":"isMaterial"},1]'`
- Для `todo/forms-batch-switch.md` / `todo/EPIC-forms-to-api.md` (будущий боевой пакет, форма 36):
  - `36 CalcTabs` → slug `tablets`, JS `wp-plugin/forms/tablets.js`, ждёт выкатку API (`tablets.py`: `is_cut_manual`, `material_mode`) и дубль копии от Site ops.

- Чем проверено:
  - `python scripts/js_port_gaps.py calcTablets` и `python scripts/js_port_gaps.py --check` → `ok`
  - `python -m pytest calc_service/tests/test_calculators/test_tablets.py calc_service/tests/test_calculators/test_plaque.py calc_service/tests/test_wp_plugin_forms.py -q` → `55 passed`
  - `Select-String -Path wp-plugin\forms\tablets.js -Pattern "calcApi\('tablets'|syncUrl\(|showResult\("` → все 3 совпадения, `price` / `querySelector` нет
  - Node smoke-тест `wp-plugin/forms/tablets.js` → формирует тело `REF_FORM_DEFAULT` и полный `syncUrl`
  - `curl.exe -s https://insain.ru/catalog/tablichki-s-uf-pechatyu/` → в HTML есть `calcTablets`, нет `calcApi`
  - `python scripts/dev.py check` → `calc_service`: `864 passed`, `bot_service`: `81 passed` (`docs/dashboard.md` откачен через `git checkout -- docs/dashboard.md` как общий файл)
- Не сделано и почему:
  - Выкатка `tablets.py` (`deploy-api` с `main`), проверка боевого `POST /api/v1/calc/tablets` на `REF_FORM_DEFAULT` и прод-копия формы 36 (шаги 6–16 `copy.md`) — после `Reviewer` и слияния в `main` (`Site ops` на проде; также требуется доступ к `ssh insain-prod`, сейчас `port 22` таймаутится).
- Требуется решение:
  - Провести ревью (`Reviewer: Grok 4.7`), затем слить в `main` и выкатить API (`deploy-api`) перед снятием копии формы 36.
