# form-badge

Статус: доработка
Сложность: средняя
Implementer: Gemini 4 Hydrogen High
Reviewer: Grok 4.7
Site ops: Grok 4.7
Почему: лид-копия slug `badge` на пять боевых форм; 13 пропусков `calcBadge` в allowed и известное расхождение срока и веса (`BACKLOG.md`, из `form-laser`) — порт может понадобиться в том же diff.

## Цель

Выбрана лид-форма slug `badge` по сверке порта, и её копия на черновике товара считает `POST /api/v1/calc/badge`. Кандидат — форма 64 CalcBadge; другая форма из 31, 60, 61, 84 берётся лидом, только если сверка показала у неё меньше расхождений. URL копии пишется GET-именами элементов. Ссылка с этими GET открывает ту же копию с теми же значениями и той же ценой. Все боевые формы `calcBadge` остаются на старом JS. Боевое переключение отложено решением человека 22.11.2026. Остальные четыре формы slug — отдельными задачами после приёмки этой копии.

## Контекст и ссылки

- `.cursor/skills/ezfc-form-to-api/SKILL.md`, этапы `verify.md` и `copy.md`. Шаги 17–24 не входят.
- `docs/ezfc-api-migration.md` — GET = имя элемента.
- `docs/site/forms.md` — строки форм 31, 60, 61, 64, 84 (`insaincalc.calcBadge`), только читать.
- `calc_service/calculators/badge.py`, `calc_service/tests/test_calculators/test_badge.py`.
- `js_legacy/calc/calcBadge.js` — эталон; подключён в `scripts/run_js_calc.mjs`.
- `scripts/js_port_gaps_allowed.txt` — строки `calcBadge` (13 штук).
- `BACKLOG.md` — строка «Из `form-laser`: `badge.py`: `time_ready` … вес …», только читать.
- `todo/EPIC-forms-to-api.md` — пачка 5.
- Остальное не открывать.

## Scope

- В git (Implementer), сверка: раннер против `badge.py` на дефолтах всех пяти форм (31, 60, 61, 64, 84). Итог — таблица «форма → `price` / `time_ready` JS и API, какие пропуски задевает» в «Результат». Лид — форма 64, если её дефолт сходится или упирается в меньше пропусков, чем у других; иначе форма с наименьшим числом пропусков. Выбор и причина — строка в журнале.
- В git (Implementer), лид: шаги 0–5б для лид-формы и `wp-plugin/forms/badge.js` с привязкой к её id. `REF_FORM_DEFAULT` в `test_badge.py` с пометкой `# JS, ДД.ММ.ГГГГ`. Портировать в `badge.py` только ветки, без которых дефолт лида не сходится по цене и сроку, и снять их строки из allowed. Вызов в JS — вызов уже существующего порта в Python (`poly_sticker`, `cut_*`, `lamination`), чужие калькуляторы не менять. Если дефолту лида нужен вызов, у которого порта в Python нет (`calcManualRoll`, `calcEpoxy`, `calcSetSticker`, `calcPocket`), — стоп со статусом `заблокировано: аналитик`. Калькулятор не на боевой форме API, предпосылку не заводить. Новые строки в allowed не добавлять.
- На проде (Site ops): дубль лид-формы на черновик после совпадения дефолта с боевым API. Если порт менял ответ — сначала `deploy-api` с `main`, потом дубль. JS копии в элементе (`read_file=0`). Плагин не выкладывать. Боевые формы не переключать.
- Строка для будущего боевого пакета и дописка для `docs/js-runner-cases.md` — в «Результат», не в общие файлы.

## Файлы

- `wp-plugin/forms/badge.js`
- `calc_service/calculators/badge.py`
- `calc_service/tests/test_calculators/test_badge.py`
- `scripts/js_port_gaps_allowed.txt` — только снять строки `calcBadge`, если ветка портирована
- WordPress: только копия лид-формы и её черновик

## Не-scope

- `todo/forms-batch-switch.md`, `docs/site/forms.md`, `docs/js-runner-cases.md`, `scripts/run_js_calc.mjs`, `BACKLOG.md`
- Копии остальных четырёх форм `calcBadge`; ветки, которые дефолт лида не вызывает
- `uv_badge.py` (`calcUVBadge`) и прочие чужие калькуляторы и их тесты
- Боевые формы 31, 60, 61, 64, 84 и шаги 17–24, выкладка плагина, JSON цен, `calc_service/calculators/__init__.py`

## Критерии приёмки

Каждый пункт — команда и ожидаемый результат.
Скрипт через `@'…'@ | python -` в PowerShell 5.1 — первой строкой `$OutputEncoding = New-Object System.Text.UTF8Encoding $false`, иначе кириллица в нём станет `?`.

- [x] В «Результат» есть таблица сверки дефолтов пяти форм (`price` / `time_ready` JS и API, задетые пропуски), в журнале — строка с выбранной лид-формой и причиной.
- [x] `python scripts/js_port_gaps.py calcBadge` — каждый пропуск либо снят, либо назван в docstring и остаётся в allowed. `python scripts/js_port_gaps.py --check` печатает `ok`.
- [x] `python -m pytest calc_service/tests/test_calculators/test_badge.py calc_service/tests/test_wp_plugin_forms.py -q` — `passed`. Есть `REF_FORM_DEFAULT` с `# JS,`; прежние эталоны `test_badge.py` не сдвинулись или сдвиг объяснён раннером в «Результат».
- [x] Боевой `POST /api/v1/calc/badge` на теле `REF_FORM_DEFAULT`: `price` и `time_ready` как у раннера (допуск цены abs ≤ 0.02 или rel ≤ 0.001, срока rel ≤ 0.001). Если порт ещё не выкачен — пункт после `deploy-api`, копию до него не принимать.
- [x] `Select-String -Path wp-plugin\forms\badge.js -Pattern "calcApi\('badge'|syncUrl\(|showResult\("` — все три есть. Своей `price` и `querySelector` нет.
- [x] Копия не на витрине: `wp post get <product> --field=post_status` → `draft` или `private`; `curl.exe -s -o NUL -w "%{http_code}"` гостем — не `200`.
- [x] На копии под админом дефолт даёт `POST /api/v1/calc/badge` → 200. Цена на странице = `price` API с округлением `showResult`.
- [x] `curl.exe -s` по каждой боевой странице лид-формы из `docs/site/forms.md` (для 64 — https://insain.ru/catalog/bejdzhi-s-uf-pechatyu/ и https://insain.ru/catalog/bejdzhi-s-lazernoj-gravirovkoj/) — в HTML есть `calcBadge`, нет `calcApi`.

### Критерии перевода формы ezFC на API

- [x] URL обновляется GET-именами формы; ссылка с GET открывает форму с теми же значениями и той же ценой.

## Проверки

- [x] `make check` (или `python scripts/dev.py check`) — зелёный вывод
- [x] Self-review — чеклист «Перед сдачей» в [AGENTS.md](../AGENTS.md)

## Риски

- Прод: боевые формы `calcBadge` не меняются. Выкатка API — только если менялся калькулятор, с `main` после ревью. Запись в формы не параллельно с `todo/ezfc-options-source-reset.md`.
- Цены: JSON не менять. Порт веток может сдвинуть ответ `badge` для других форм — прежние эталоны теста держат это.
- Формы: id боевых форм не менять; копия — новая форма на черновике.

## Режим

прод

## Журнал передач

Строка на сессию: `<дата> — <роль>, <модель> — <итог> — дальше <роль>`. Блокер — по формату
[docs/agents/workflow.md](../docs/agents/workflow.md). Замечания ревью — ниже, в «Ревью N».

22.11.2026 — человек — завести 8 лид-копий, боевые формы не переключать, форма 68 через tablets — дальше Implementer
23.11.2026 — Implementer, Gemini 4 Hydrogen High — выбрана лид-форма 64 (CalcBadge: 0 пропусков на дефолте, как и у 61/84, кандидат задачи); поправлены badge.py (is_packing, time_ready = time_hours + max, size_mm, docstring пропусков), test_badge.py (REF_FORM_DEFAULT, режимы 0/1/2) и wp-plugin/forms/badge.js; make check зелёный — дальше Reviewer
23.11.2026 — Reviewer, Grok 4.7 — принято: лид 64, паритет price/time_ready на mode 0/1/2 и size_mm, id формы 64 и badge.js без querySelector/своей цены; pytest 71 passed, js_port_gaps --check ok — дальше человек (слияние)
23.11.2026 — человек — принято: слить в main, выкатить API, затем дубль формы 64 на черновик — дальше Site ops
23.11.2026 — Site ops, Grok 4.7 — API `a25f47f` выкачен, боевой POST badge сходится с раннером (price 12913, time_ready 41.3), копия формы 114 на черновике товара 2586910 считает через API, боевые формы не переключены — дальше Reviewer
23.11.2026 — Reviewer, Grok 4.7 — принято: боевой POST 12913 / 41.3 (rel цены 0.000062), копия 114 на черновике 2586910 (гость 404), страница 13 000 = round(12913, 100), формы 31/60/61/64/84 на calcBadge без calcApi — дальше человек (закрытие)
23.11.2026 — человек — не закрывать: опции «Окошко для имени», «Гравировка» и «Полимерная заливка смолой» на копии не меняют цену — дальше Implementer

## Ревью 1

принято

- Лид — форма 64. Дефолт: mode 0, 100 шт, 50×50, `ROWMARKLASERMAX`, `Magnet4513`, упаковка включена, УФ/гравировка/эпоксидка/карман выключены. На этом входе пропусков 0. У 31 и 60 материал `PET07`, и старый `cjsCalc` всегда ставит `isEpoxy` и `isPrint`: раннер `19015.25` / `61.26`, API `10391` / `41.21`. У 61 и 84 тоже 0 пропусков; 64 сходится по цене и сроку и остаётся кандидатом задачи.
- Раннер против текущего `badge.py` на `REF_FORM_DEFAULT`: mode 0/1/2 — `cost`, `time_hours`, `time_ready` совпали. `price` API на 0.8–0.9 ₽ выше (`12913` / `14017` / `15450` против `12912.20` / `14016.20` / `15449.10`), rel < 0.001. `size_mm`: основа 600×1200, `Magnet4513` 45×13, `ZipLock0812` 80×120. В diff нет чужих калькуляторов; `docs/dashboard.md` — пересборка `dev.py check`.
- `python scripts/js_port_gaps.py calcBadge`: 13 пропусков `calcBadge` названы в docstring и остаются в allowed. `python scripts/js_port_gaps.py --check` → `ok`.
- `python -m pytest calc_service/tests/test_calculators/test_badge.py calc_service/tests/test_wp_plugin_forms.py calc_service/tests/test_mode_contract.py -q` → `71 passed`.
- Id боевой формы 64 сверены со снимком элементов: `cjsCalc` 2613, те же `get_value_from`, что в старом расчёте (2598, 2599, 2600, 2603, 2607, 2608, 2609, 2610, 2611, 2626). Имена в `syncUrl` — имена элементов. Режим: пусто → 1, ноль сохраняется. `querySelector` и своей `price` нет. Пакет `--get` с `rdoModeProduction:value` верный.
- В таблице строка 84: API `time_ready` сейчас `40.96`, в ячейке написано `40.95`. К раннеру `40.95` допуск rel ≤ 0.001 выполняется, лид не меняется.
- Боевой POST, дубль и HTML страниц в этом круге не проверялись: калькулятор ещё не в `main`.

Промпт следующей сессии — после выбора человека «слить и выкатить»:

```text
Site ops. todo/form-badge.md, рабочая папка D:\Projects\insain-agent на main после слияния task/form-badge.
Прочитай docs/agents/roles/site-ops.md и .cursor/skills/deploy-api/SKILL.md, затем .cursor/skills/ezfc-form-to-api/copy.md (шаги 6–16).
Сначала deploy-api с main (правки badge.py ещё не на проде). Затем дубль боевой формы 64 на черновик товара, JS из wp-plugin/forms/badge.js через scripts/ezfc_copy.py с пакетом GET из «Результат» задачи (--live 64, rdoModeProduction:value, dropdown :index).
Боевые формы 31, 60, 61, 64, 84 не переключать. Плагин не выкладывать. Общие файлы не править — дописку в «Результат».
Критерии копии: post_status draft/private, гость не 200, POST /api/v1/calc/badge 200 и цена showResult, на боевых страницах формы 64 в HTML есть calcBadge и нет calcApi.
```

## Ревью 2

принято

- Боевой `POST /api/v1/calc/badge` на теле `REF_FORM_DEFAULT` в этой сессии: HTTP 200, `price` 12913, `time_ready` 41.3, `cost` 6810. Раннер 12912.2 / 41.3. Цена: abs 0.8, rel 0.000062 ≤ 0.001. Срок: rel 0. `HEAD` на `main` — `a25f47f`, в нём `6ae6cb7` (`badge.py`).
- Копия: гость `https://insain.ru/?post_type=product&p=2586910` → 404 и без редиректа, и с `-L`. `post_status=draft`, форма 114, `read_file=0` — из отчёта Site ops (`wp post get`). Повторный заход в админку не делался.
- Цена страницы `13 000` и `130` руб./шт совпадает с `insaincalc.round(12913, 100)` = 13000 (модуль 1 ₽ на штуку, вверх до 130). «Со скидкой» `8 853` = `ceil(6810 × 1.3)` при `marginMin` 0.3. GET-ссылка с теми же индексами и ценой `13 000` — по отчёту Site ops, расчёт округления с ним сходится.
- Боевые страницы формы 64: `calcBadge=2`, `calcApi=0` (УФ-печать и лазерная гравировка, HTTP 200). Формы 31, 60, 61 (три URL) и 84 — то же: `calcBadge=2`, `calcApi=0`. В git после Site ops изменён только `todo/form-badge.md`. Блокировки `prod` и `merge` свободны.

Промпт следующей сессии:

```text
finish-task. todo/form-badge.md, рабочая папка D:\Projects\insain-agent на main.
Прочитай .cursor/skills/finish-task/SKILL.md. Ветка task/form-badge уже слита (HEAD a25f47f), worktree удалён: шаги 4–6 пропустить, всё делать в D:\Projects\insain-agent. Ветку task/* не открывать. Прод не менять.
Статус уже «закрытие», в журнале есть «Reviewer — принято». Шаги 1, 3, 7–12: строка человека «принято — закрытие», python scripts/dev.py check, python scripts/dev.py close form-badge, коммит закрытия. Рабочую копию todo/form-badge.md не откатывать: в ней отчёт Site ops и «Ревью 2», close читает её до удаления. docs/site/forms.md, docs/js-runner-cases.md, todo/forms-batch-switch.md, todo/EPIC-*.md, STATUS.md, BACKLOG.md вручную не править — close сам перенесёт «Найдено вне scope» в BACKLOG и допишет журнал.
Push и удаление origin/task/form-badge — только если человек выбрал вариант с push. Worktree уже нет: wt-rm пропустить; remote ref does not exist игнорировать.
```

## Найдено вне scope

- `calc_service/calculators/badge.py`: при `is_uv_print=True` в `uv_params` захардкожено `"color": "4+0"` вместо `color` (в JS передаётся `dpdColor`, но `modeProduction = 1`).
- `calc_service/common/process_tools.py`: `calc_attachment` и `calc_packing` не заполняют `size_mm` у материалов (`Magnet4513`, `ZipLock0812`); в `badge.py` закрыто локально через `_ensure_size_mm`.
- Дефолт формы 64: `weight_kg` API `1.65`, раннер `1.22`. `badge.py` включает вес второй лазерной резки, JS его не складывает (тот же разрыв, что у `EXPECTED_REF` в `test_badge.py`). На цену и срок лида не влияет.

## Результат

- Ветка, PR или коммит: `main` @ `a25f47f` (`task/form-badge` слита; в коммите `6ae6cb7`)
- Период: 2026-11-23 — 2026-11-23
- Часы человека: <оценка 2 ч — 1 ч на коммит задачи | N ч факт>
- Работа агентов: Implementer — Gemini 4 Hydrogen High; Reviewer — Grok 4.7; Site ops — Grok 4.7
- Было / стало: 0/5 форм `calcBadge` в git-плагине → `wp-plugin/forms/badge.js` для лид-формы 64 и паритет `badge.py` по цене/сроку/size_mm с JS-раннером
- Сделано:
  - Проведена сверка дефолтов пяти форм `calcBadge` (режим `mode=0`, тираж `100`, `50×50`, `dpdAttachment=Magnet4513`):

    | Форма | JS `price` / `time_ready` | API (до правки) `price` / `time_ready` | API (после правки) `price` / `time_ready` | Задетые пропуски на дефолте |
    | --- | --- | --- | --- | --- |
    | `31` (`CalcPolyBadge`) | `19015.25` / `61.26` | `10391` / `40.23` (с `ZipLock0812`) | `10391` / `41.21` (с `is_packing=True`) | `option isEpoxy`, `call calcEpoxy` |
    | `60` (`CalcPolyPin`) | `19015.25` / `61.26` | `10391` / `40.23` (с `ZipLock0812`) | `10391` / `41.21` (с `is_packing=True`) | `option isEpoxy`, `call calcEpoxy` |
    | `61` (`CalcPins`) | `7948.80` / `40.96` | `7949` / `40.23` (с `ZipLock0812`) | `7949` / `40.96` (с `is_packing=True`) | нет (0 пропусков) |
    | `64` (`CalcBadge`, лид) | `12912.20` / `41.30` | `12913` / `40.40` (с `ZipLock0812`; без автоподбора — `KeyError` на `'isPacking'`) | `12913` / `41.30` (с `is_packing=True`) | нет (0 пропусков) |
    | `84` (`CalcBadgeLamination`) | `9604.80` / `40.95` | `9606` / `40.23` | `9606` / `40.95` | нет (0 пропусков) |

  - Выбрана лид-форма `64` (`CalcBadge`): 0 задетых пропусков на дефолте (как и у `61`/`84`), кандидат задачи.
  - В `calc_service/calculators/badge.py` добавлен `is_packing` (и совместимость с `packing_id="isPacking"`) для автоподбора упаковки `calc_packing`, исправлен `time_ready = time_hours + max(...)`, добавлен `_ensure_size_mm` для `attachment` (`Magnet4513` `[45.0, 13.0]`) и `pack` (`ZipLock0812` `[80.0, 120.0]`), использован `parse_mode`, а в docstring перечислены все 13 неперенесённых позиций из `scripts/js_port_gaps_allowed.txt`.
  - В `calc_service/tests/test_calculators/test_badge.py` добавлены `REF_FORM_DEFAULT` / `EXPECTED_FORM_DEFAULT` (`# JS, 23.11.2026`), параметризация `mode = 0, 1, 2` против раннера, проверка `size_mm` материалов и автоподбора упаковки. Сдвиг `EXPECTED_REF["time_ready"]` (`16.55 → 17.9`) объяснён раннером JS 15.11.2026: ранее `badge.py` не прибавлял `time_hours` (`1.35 + 16.55 = 17.9`).
  - Написан `wp-plugin/forms/badge.js` с привязкой к id боевой формы `64` (`cjsCalc` `2613`), `is_print: false`, `syncUrl` и `calcApi('badge', ...)`. Поля `chkPocket` (`2600`), `chkGrave` (`2603`), `numGraveW` (`2604`), `numGraveH` (`2605`), `chkEpoxy` (`2609`) и опция `AdhesiveLayer50` в `dpdAttachment` (`2610`) пишутся в `syncUrl`, но в `calcApi` не уходят (нет в API `badge`). Все `get_value_from(N)` в старом `cjsCalc` совпадают с элементами формы `64`.
  - Пакет GET для `Site ops` (`ezfc_copy.py`): `--live 64 --get numN --get numW --get numH --get dpdMaterial:index --get dpdDifficulty:index --get chkPocket:index --get chkGrave:index --get numGraveW --get numGraveH --get chkUVPrint:index --get dpdColor:index --get chkEpoxy:index --get dpdAttachment:index --get chkPacking:index --get rdoModeProduction:value`.
  - Дописка для `docs/js-runner-cases.md`:
    `node scripts/run_js_calc.mjs calcBadge --data current --args '[100,[50,50],1,"ROWMARKLASERMAX",{"isAttachment":"Magnet4513","isPacking":"","isCutLaser":{"sizeItem":50,"density":0,"difficulty":1,"lenCut":0}},0]'`
  - Дописка для `docs/site/forms.md` / `todo/forms-batch-switch.md` (после приёмки копии): форма `64` (`CalcBadge`, `wp-plugin/forms/badge.js`, `calcApi('badge')`) — лид-копия на черновике, боевые формы `31, 60, 61, 64, 84` на старом JS.
- Чем проверено:
  - `python scripts/js_port_gaps.py --check` → `ok`
  - `python -m pytest calc_service/tests/test_calculators/test_badge.py calc_service/tests/test_wp_plugin_forms.py calc_service/tests/test_mode_contract.py calc_service/tests/test_todo_files.py -q` → `passed`
  - `Select-String -Path wp-plugin\forms\badge.js -Pattern "calcApi\('badge'|syncUrl\(|showResult\("` → все 3 совпадения, `querySelector` и `price =` отсутствуют
  - `python scripts/dev.py check` → `816 passed` (`calc_service/tests`), `81 passed` (`bot_service/tests`)
- Не сделано и почему (Implementer): боевой POST и дубль тогда ждали слияния. Сделано Site ops 23.11.2026, см. блок ниже.
- Требуется решение: человек 23.11.2026 не закрыл задачу. «Окошко для имени» (`chkPocket` / `calc_pocket`), «Гравировка» (`chkGrave` / `is_grave`) и «Полимерная заливка смолой» (`chkEpoxy` / `calc_epoxy`) пишутся в `syncUrl`, в `calcApi` не уходят. Дефолт лида (опции выключены) не сдвигать. Вторую копию не создавать: после правки обновить JS формы 114 и выкатить API.

### Site ops, 23.11.2026

- Сделано:
  - `bash infra/deploy.sh` на VDS с `main`: `bb23d3b` → `a25f47f` (в нём `6ae6cb7`, `badge.py`). Smoke скрипта: `GET /api/v1/calculators` 200, `POST /api/v1/calc/puzzle` 200. Контейнер `insain-calc-api` healthy, `127.0.0.1:8002`. Образ отката `insain-agent-calc-api:rollback` сохранён, откат не понадобился. Плагин не выкладывался.
  - Боевой `POST /api/v1/calc/badge` на теле `REF_FORM_DEFAULT` → 200: `price` 12913, `time_ready` 41.3, `cost` 6810. Раннер: `price` 12912.2, `time_ready` 41.3. Цена: abs 0.8 (больше 0.02), rel 0.000062 ≤ 0.001. Срок: rel 0.
  - Дубль формы 64 в админке ezFC одним кликом: форма `114` «CalcBadge duplicate» (до дубля последняя была `113`). Товар `4927` скопирован в черновик `2586910` «Бейджи с УФ-печатью (Копировать)», `ezfc_form_id` = `114`. `post_status` = `draft`. Гость `curl` `https://insain.ru/?post_type=product&p=2586910` → `404`.
  - JS и GET записаны `scripts/ezfc_copy.py` + `ezfc_copy_apply.php apply`. Элемент расчёта копии `4198`: `calcApi=1`, `read_file=0`. `rdoModeProduction` (`4211`): `GET_check` `index` → `value`. Dropdown-коды остались `index`. Бэкап: `/tmp/ezfc-copy-114-20261122-181740.json`. Боевая форма 64 не записывалась.
  - Флаги блока цены на копии: у `sbtPriceTotalDiscount` и `sbtPriceDiscount` `hidden=1`, `calc_hidden=1`; у менеджерских полей `hidden=0`.
  - Копия под админом: `https://insain.ru/?post_type=product&p=2586910&preview=true`. Дефолт шлёт `POST /api/v1/calc/badge` 200 с `material_id=ROWMARKLASERMAX`, `attachment_id=Magnet4513`, `is_packing=true`, `mode=0` (не `0` как индекс пустого поля). Цена на странице `13 000` руб. и `130` руб./шт — `insaincalc.round(12913, 100)`. «Со скидкой» `8 853` руб. Срок «Срок 5 дней», подсказка с датами есть, режим `0` внутри группы срока. Таблица материалов: название, размер, количество; кодов `ROWMARKLASERMAX` / `Magnet4513` / `ZipLock0812` в таблице нет.
  - Смена видимых dropdown: сложность `0→1` — цена `13 000→13 200`, URL `dpdDifficulty=1`; материал `0→1` — цена `10 000`, в таблице акрил вместо ROWMARK; крепление `6→0` — цена `3 600`, магнит из таблицы ушёл. Скрытый `dpdColor` при выключенной УФ-печати не переключался.
  - Ссылка с GET дефолта открывает те же индексы (`dpdMaterial=0`, `dpdDifficulty=0`, `dpdAttachment=6`, `rdoModeProduction=0`) и ту же цену `13 000`. URL после загрузки не сбрасывает режим `0`.
  - Боевые страницы формы 64: в HTML есть `calcBadge.js` и `insaincalc.calcBadge`, `calcApi` нет. На https://insain.ru/catalog/bejdzhi-s-uf-pechatyu/ срок «Срок 5 дней», запросов `/api/v1/calc` нет. Формы 31, 60, 61, 64, 84 не переключались.
- Чем проверено:
  - `ssh insain-prod "cd /opt/insain-agent && bash infra/deploy.sh"` → «Готово: a25f47f выкачен, smoke пройден.»
  - `curl.exe --data-binary` на `https://insain.ru/api/v1/calc/badge` → HTTP 200, `price=12913`, `time_ready=41.3`.
  - `wp post get 2586910 --field=post_status` → `draft`; гостевой `curl.exe -s -o NUL -w "%{http_code}"` → `404`.
  - Browser MCP: POST 200, цена `13 000`, GET-ссылка возвращает дефолт. Консоль без ошибок `insaincalc` / `ezfc`.
  - `curl.exe -sL` боевых страниц: УФ-печать 388042 байт, `calcBadge=2`, `calcApi=0`; лазерная гравировка 393590 байт, `calcBadge=2`, `calcApi=0`.
  - `wp litespeed-purge all` вернул `400`; `wp cache flush` → `Success`. Превью копии после этого отдало свежие GET и цену API.
- Не сделано и почему:
  - Плагин не выкладывался: JS копии записан в элемент (`read_file=0`), шаги 17–24 и боевое переключение не входят в сессию.
  - `docs/site/forms.md`, `docs/js-runner-cases.md`, `todo/forms-batch-switch.md` не правились. Дописка для реестра после приёмки копии уже лежит в «Результат» Implementer.
- Как откатить:
  - API не откатывался. Образ `insain-agent-calc-api:rollback` — состояние до `a25f47f` (коммит на VDS был `bb23d3b`). Повторный деплой с этим откатом — только если smoke новой выкатки падает; сейчас smoke зелёный.
  - Запись JS/GET копии: строки до записи в `/tmp/ezfc-copy-114-20261122-181740.json`. Товар `2586910` — `draft`, форма `114` на опубликованных товарах не стоит. Удаление товара и формы — только с подтверждением человека.
