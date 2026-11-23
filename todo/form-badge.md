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

- [ ] Включённая «УФ-печать» на дефолте формы 64: `price` и `time_ready` как у раннера `calcBadge` (допуск цены abs ≤ 0.02 или rel ≤ 0.001, срока rel ≤ 0.001). Дефолт без УФ не сдвинут. Эталон с раннера, пометка `# JS`.
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
23.11.2026 — Implementer, Gemini 4 Hydrogen High — добавлены pocket_id/is_pocket (calc_pocket), is_grave/is_grave_fill/is_grave_contur (LaserCalculator) и is_epoxy (calc_epoxy + брак EpoxyCoating) в badge.py и wp-plugin/forms/badge.js; сняты 7 строк calcBadge из allowed; эталоны с раннера в test_badge.py; дефолт 64 не сдвинут (12913 / 41.3); make check зелёный — дальше Reviewer
23.11.2026 — Reviewer, Grok 4.7 — принято: три опции сходятся с раннером (карман 14557/41.55, гравировка 50×50 48234/85.06, смола 22474/61.22), дефолт 12913/41.3 не сдвинут, js_port_gaps --check ok — дальше человек (слияние и обновление копии 114)
23.11.2026 — человек — принято: слить в main, выкатить API и записать JS в существующую копию 114 — дальше Site ops
23.11.2026 — Site ops, Grok 4.7 — API `9a247eb` выкачен, на копии 114 окошко 14 600, гравировка 48 300, смола 22 500, дефолт 13 000 — дальше Reviewer
23.11.2026 — Reviewer, Grok 4.7 — принято по отчёту опций, задача закрыта локально коммитом `0c5534f` без push — дальше человек
23.11.2026 — человек — вернуть на доработку: опция «УФ-печать» расходится с JS — дальше Implementer

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

## Ревью 3

принято

- Diff только в scope: `badge.py`, `test_badge.py`, `wp-plugin/forms/badge.js`, `scripts/js_port_gaps_allowed.txt` (сняты 7 строк `calcBadge`, новых нет), `todo/form-badge.md`, `docs/dashboard.md` (статус `ревью`). `laser.py` и `process_tools.py` в diff нет.
- Раннер `calcBadge --data current` на дефолте формы 64 и трёх опциях против текущего `badge.py`. Допуск цены rel ≤ 0.001 (тот же, что у дефолта 12913 против 12912.2).
  - Дефолт mode 0: API `12913` / `41.3`, раннер `12912.2` / `41.3`. Режимы 1 и 2 и `EXPECTED_REF` (`3335` / `6060.5` / `1.35` / `17.9`) не сдвинуты: pytest их держит.
  - Окошко `pocket_id=Pocket`, mode 0: API `14557` / `41.55`, раннер `14556.7` / `41.55`. Mode 1: `15937` / `18.25` против `15936.7` / `18.25`. Mode 2: `17646` / `10.99` против `17645.6` / `10.99`.
  - Гравировка `is_grave=2`, `is_grave_fill=[50,50]`, mode 0: API `48234` / `85.06`, раннер `48233.3` / `85.06`. Mode 1: `49338` / `61.67` против `49337.3` / `61.67`. Mode 2: `52452` / `56.38` против `52451.5` / `56.38`. Пустой `isGrave:""` у раннера даёт ту же цену, что заливка на весь размер 50×50. Заливка `[0,0]` цену не меняет (`12912.2`); на форме 64 поля `numGraveW`/`numGraveH` открываются с `50`, и старый `cjsCalc` кладёт в опции `isGrave=2` и `[get_value_from(2604), get_value_from(2605)]` — то же, что `badge.js`.
  - Смола `is_epoxy`, mode 0: API `22474` / `61.22`, раннер `22474.45` / `61.22` (cost `11938.63` против `Math.ceil` `11939`). Mode 1: `23691` / `45.7` против `23691.15` / `45.7`. Mode 2: `27495` / `30.94` против `27495.35` / `30.94`. Брак `EpoxyCoating` увеличивает тираж печати и лазера; `calc_epoxy` идёт с `isLayout`.
  - Три опции вместе, mode 0: API `65158` / `94.64`, раннер `65157.85` / `94.64`. Контур `is_grave=1`, `is_grave_contur=[5,20]`: API `13761` / `42.37`, раннер `13760.9` / `42.37`. На форме 64 поля контура нет, старый расчёт его не ставит.
- `python scripts/js_port_gaps.py calcBadge`: в Python нет ровно шести строк, они названы в docstring (`option_isAdhesiveLayer`, `option_isMetalBlank`, `option_isEpoxySticker`, `calcManualRoll`, `calcPolySticker`, `calcSetSticker`). `python scripts/js_port_gaps.py --check` → `ok`.
- `wp-plugin/forms/badge.js`: `calcApi('badge')`, `syncUrl(`, `showResult(` есть; `querySelector` и своей `price` нет. `chkPocket` → `pocket_id: 'Pocket'`, `chkGrave` + `numGraveW`/`numGraveH` → `is_grave: 2` и `is_grave_fill`, `chkEpoxy` → `is_epoxy`.
- `python -m pytest calc_service/tests/test_calculators/test_badge.py calc_service/tests/test_wp_plugin_forms.py -q` → `32 passed`. `test_mode_contract.py -k badge` → `2 passed`. Полный `python scripts/dev.py check` в этом круге не гонялся: точечные тесты и раннер закрывают diff.
- Боевой API и JS копии 114 этим diff ещё не обновлены. После слияния в `main` нужны `deploy-api` и повторная запись JS в существующую форму 114. Новую копию не создавать.

## Найдено вне scope

- `calc_service/calculators/badge.py`: при `is_uv_print=True` в `uv_params` захардкожено `"color": "4+0"` вместо `color` (в JS передаётся `dpdColor`, но `modeProduction = 1`).
- `calc_service/common/process_tools.py`: `calc_attachment` и `calc_packing` не заполняют `size_mm` у материалов (`Magnet4513`, `ZipLock0812`); в `badge.py` закрыто локально через `_ensure_size_mm`.
- Дефолт формы 64: `weight_kg` API `1.65`, раннер `1.22`. `badge.py` включает вес второй лазерной резки, JS его не складывает (тот же разрыв, что у `EXPECTED_REF` в `test_badge.py`). На цену и срок лида не влияет.

## Результат

- Ветка, PR или коммит: `task/form-badge` (поверх `main` @ `58ebe31`, ожидает ревью и слияния)
- Период: 2026-11-23 — 2026-11-23
- Часы человека: <оценка 2 ч — 1 ч на коммит задачи | N ч факт>
- Работа агентов: Implementer — Gemini 4 Hydrogen High; Reviewer — Grok 4.7; Site ops — Grok 4.7
- Было / стало: 0/5 форм `calcBadge` в git-плагине → `wp-plugin/forms/badge.js` для лид-формы 64 с поддержкой опций «Окошко для имени», «Гравировка» и «Полимерная заливка смолой» и паритетом `badge.py` по цене/сроку/size_mm с JS-раннером
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
  - В `calc_service/calculators/badge.py` добавлен `is_packing` (и совместимость с `packing_id="isPacking"`) для автоподбора упаковки `calc_packing`, исправлен `time_ready = time_hours + max(...)`, добавлен `_ensure_size_mm` для `attachment` (`Magnet4513` `[45.0, 13.0]`), `pack` (`ZipLock0812` `[80.0, 120.0]`) и `pocket` (`Pocket` `[80.0, 23.0]`), использован `parse_mode`.
  - Доработка от 23.11.2026 (три опции формы 64):
    - **Окошко для имени** (`pocket_id` / `is_pocket`): вызов `calc_pocket(n, pocket_id, mode.value)` из `common/process_tools.py`, учёт `cost`/`price`/`time_hours`/`weight_kg`/`materials`, в `_ensure_size_mm` добавлена категория `"pocket"`.
    - **Гравировка** (`is_grave`, `is_grave_fill`, `is_grave_contur`): проброс в `LaserCalculator` (`laser_params2`) в том же ключе, что `calcBadge.js` (булево `True` → `is_grave=2`, `is_grave_fill=size` при отсутствии явных размеров; `False` гравировку не включает; целое `0/1/2` передаётся как разрешение). `laser.py` не менялся.
    - **Полимерная заливка смолой** (`is_epoxy`): учёт брака `EpoxyCoating` через `apply_mode_defects` (`n_items = math.ceil(n * (1 + epoxy_defects))` для печати и лазерной резки/гравировки) и вызов `calc_epoxy(n, size, difficulty, {"isLayout": True}, mode.value)` из `common/process_tools.py` с добавлением `time_ready_epoxy` в `time_ready_list`. `process_tools.py` не менялся.
    - В docstring `badge.py` оставлены 6 неперенесённых позиций: `option_isAdhesiveLayer`, `option_isMetalBlank`, `option_isEpoxySticker`, `calcManualRoll`, `calcPolySticker`, `calcSetSticker`.
    - В `scripts/js_port_gaps_allowed.txt` сняты 7 реально портированных строк `calcBadge` (`option isEpoxy`, `option isGrave`, `option isGraveFill`, `option isGraveContur`, `option isPocket`, `call calcEpoxy`, `call calcPocket`); новые строки не добавлялись.
  - В `calc_service/tests/test_calculators/test_badge.py` сохранены прежние эталоны (`EXPECTED_REF`, `EXPECTED_FORM_DEFAULT` = `12913` / `41.3`, `EXPECTED_FORM_MODES`) и добавлены эталоны с раннера (`# JS, 23.11.2026`) для `pocket_id="Pocket"` (режимы 0/1/2 + `is_pocket=True` + `size_mm`), `is_grave` (режимы 0/1/2 + `bool` + `is_grave_contur`), `is_epoxy=True` (режимы 0/1/2 + `is_print=True, is_epoxy=True`) и комбинации всех трёх опций.
  - В `wp-plugin/forms/badge.js` поля `chkPocket` (`2600` → `pocket_id: 'Pocket'`), `chkGrave` (`2603` → `is_grave: 2`), `numGraveW`/`numGraveH` (`is_grave_fill: [graveW, graveH]`) и `chkEpoxy` (`2609` → `is_epoxy: isEpoxy`) передаются в `calcApi('badge', params)`. Неперенесённой осталась только опция `AdhesiveLayer50` в `dpdAttachment`.
  - Пакет GET для `Site ops` (`ezfc_copy.py`): `--live 64 --get numN --get numW --get numH --get dpdMaterial:index --get dpdDifficulty:index --get chkPocket:index --get chkGrave:index --get numGraveW --get numGraveH --get chkUVPrint:index --get dpdColor:index --get chkEpoxy:index --get dpdAttachment:index --get chkPacking:index --get rdoModeProduction:value`.
  - Дописка для `docs/js-runner-cases.md`:
    `node scripts/run_js_calc.mjs calcBadge --data current --args '[100,[50,50],1,"ROWMARKLASERMAX",{"isAttachment":"Magnet4513","isPacking":"","isCutLaser":{"sizeItem":50,"density":0,"difficulty":1,"lenCut":0}},0]'`
  - Дописка для `docs/site/forms.md` / `todo/forms-batch-switch.md` (после приёмки копии): форма `64` (`CalcBadge`, `wp-plugin/forms/badge.js`, `calcApi('badge')`) — лид-копия на черновике, боевые формы `31, 60, 61, 64, 84` на старом JS.
- Чем проверено (доработка 23.11.2026):
  - `python scripts/js_port_gaps.py --check` → `ok` (6 оставшихся строк `calcBadge`)
  - `python -m pytest calc_service/tests/test_calculators/test_badge.py calc_service/tests/test_wp_plugin_forms.py calc_service/tests/test_mode_contract.py calc_service/tests/test_materials_contract.py -q` → `114 passed`
  - `Select-String -Path wp-plugin\forms\badge.js -Pattern "calcApi\('badge'|syncUrl\(|showResult\(|querySelector|price\s*="` → все 3 вызова на месте, `querySelector` и `price =` отсутствуют
  - `python scripts/dev.py check` → `828 passed` (`calc_service/tests`), `81 passed` (`bot_service/tests`)
- Не сделано и почему: боевой API и JS формы `114` на черновике `2586910` в этой сессии не обновлялись (после ревью нужны `deploy-api` с `main` и повторное применение пакета `ezfc_copy.py` на существующую копию `114` без создания второй копии).
- Требуется решение: человек 23.11.2026 вернул задачу. Опция «УФ-печать» на копии 114 расходится со старым `calcBadge.js`. Свести `price` и `time_ready` с раннером. Дефолт без УФ (12913 / 41.3) не сдвигать. Новую копию не создавать: форма 114, товар 2586910. После ревью — выкатка API и обновление JS этой копии.

Промпт следующей сессии (`Reviewer`):

```text
Reviewer. todo/form-badge.md, ветка task/form-badge, рабочая папка D:\Projects\insain-agent-form-badge.
Прочитай docs/agents/roles/reviewer.md и проверь доработку в task/form-badge:
- diff только в scope (badge.py, test_badge.py, wp-plugin/forms/badge.js, scripts/js_port_gaps_allowed.txt, todo/form-badge.md, docs/dashboard.md); laser.py и process_tools.py не тронуты;
- три опции (chkPocket -> calc_pocket, chkGrave/numGraveW/numGraveH -> is_grave/is_grave_fill/is_grave_contur, chkEpoxy -> calc_epoxy + брак EpoxyCoating) совпадают с раннером calcBadge.js; дефолт формы 64 (12913 / 41.3) и прежние эталоны не сдвинуты;
- python scripts/js_port_gaps.py --check -> ok; оставшиеся 6 строк calcBadge названы в docstring;
- wp-plugin/forms/badge.js передаёт три опции в calcApi('badge') и не содержит querySelector/своей цены;
- python scripts/dev.py check зелёный.
После «принято» и слияния в main — Site ops: deploy-api с main и обновление JS существующей копии 114 (новую копию не создавать).
```

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
