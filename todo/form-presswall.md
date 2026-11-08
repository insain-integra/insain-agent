# form-presswall

Статус: закрытие
Сложность: высокая
Implementer: Opus 5.5
Reviewer: Grok 4.7
Site ops: Opus 5.5
Почему: режим прод и два контура — `wp-plugin/forms/presswall.js` в git и WordPress (дубль, GET на копии, прогон под админом).
Чат: человек открывает новый чат с моделью из поля Implementer.

## Цель

Копия формы 46 CalcPresswall на черновике товара считает `POST /api/v1/calc/presswall`. URL копии пишется GET-именами элементов. Ссылка с этими GET открывает ту же копию с теми же значениями и той же ценой. Боевая форма 46 на странице https://insain.ru/catalog/kalkulyator-pressvolov/ по-прежнему на `insaincalc.calcPresswall`.

## Контекст и ссылки

- `.cursor/skills/ezfc-form-to-api/SKILL.md` — порядок. Боевая форма (шаги 17–24 skill) в эту задачу не входит.
- `docs/ezfc-api-migration.md` — шаблон `cjsCalc`, GET = имя элемента, `GET_check`: dropdown с кодом — `index`, radio `1`/`2` — `value`.
- `docs/site/forms.md` — строка формы 46, только читать.
- `todo/forms-batch-switch.md` — в конце одна строка в «Состав пакета».
- `todo/EPIC-forms-to-api.md` — очередь, после `todo/form-rollup.md`.
- `docs/js-runner-cases.md` — команда раннера и `price` для `calcPresswall`.
- Эталон: кейсы с креплением в `calc_service/tests/test_calculators/test_presswall.py` от `presswall-banner-options` (закрыто 2026-11-09, `docs/history/log.md`) — тираж 1, `Joker30_20_eyelet`, `BannerFronlitCoat400`, каркас да, аренда 0; люверсы `is_eyelet [300,300,300,300]` (mode 1 и 2), карман `is_pocket [1,0,1,0]` + `is_cutting [0,1,0,1]`, люверсы с чехлом `bag160`. `REF_PARAMS` без крепления на форме недостижим (dpdAttachment всегда даёт одну из опций) — для сверки формы не годится. Порог `price` — прогон JS против API, не число из файла. Тираж ≥ 2 не добавлять. JS: `js_legacy/calc/calcPresswall.js`, сигнатура `calcPresswall(n, presswallID, materialID, options, modeProduction)`.
- Форма 46, cjsCalc 1862: dpdAttachment = люверсы — `options.isEyelet = [300,300,300,300]`; карман — `isPocket = [1,0,1,0]` и `isCutting = [0,1,0,1]`.
- Остальное не открывать.

## Scope

- Раннер готов (`js-runner-forms` закрыта 05.11.2026). Кейс и команда раннера — из `docs/js-runner-cases.md`. `calc_service/data/` и калькулятор не менять.
- Сверка JS и API — на кейсе дефолта формы 46 (значения полей при открытии страницы, крепление из dpdAttachment). Совпал с кейсом `presswall-banner-options` — `test_presswall.py` не трогать. Не совпал — один кейс дефолта с пометкой `JS, ДД.ММ.ГГГГ`, как в `test_tablets.py`. Допуск assert: `cost`, `price`, `time_ready` — `rel=0.001`, `weight_kg` — `abs=0.02` (`print_roll` отдаёт вес баннера, округлённый до 0.01: раннер 9.79, API 9.78). Не сошлись — файл не трогать.
- `wp-plugin/forms/presswall.js`: id элементов боевой формы 46, `insaincalc.syncUrl`, `insaincalc.calcApi('presswall'`, `insaincalc.showResult`. Крепление в `calcApi`: dpdAttachment люверсы — `is_eyelet: [300,300,300,300]`; карман — `is_pocket: [1,0,1,0]` и `is_cutting: [0,1,0,1]`, как cjsCalc 1862. Чехол dpdBag — `is_bag`. Своих формул цены и чтения через DOM нет.
- Дубль формы и черновик товара — только после «да» человека. На копию — тот же JS с id копии, без `read_file`.
- GET на копии: имя параметра = имя элемента. Боевую форму не размечать.
- Прогон копии под админом: эталон тиража 1, смена полей, ссылка с GET.
- После принятия копии человеком — одна строка в таблицу «Состав пакета» `todo/forms-batch-switch.md`. Ветка `task/form-presswall` от `main`.

Распределение: сверку эталона, `test_presswall.py`, `wp-plugin/forms/presswall.js` и строку в `todo/forms-batch-switch.md` делает Implementer. Дубль и черновик товара, JS и GET на копии, прогон под админом — Site ops; расхождение на копии возвращается Implementer.

## Файлы

- `wp-plugin/forms/presswall.js`
- `calc_service/tests/test_calculators/test_presswall.py`
- `todo/forms-batch-switch.md` — общий для задач эпика: одна строка в «Состав пакета»
- WordPress: только копия формы и черновик товара

## Не-scope

- `read_file` и любое переключение боевой формы 46. Выкладка плагина. `infra/deploy.sh`.
- `docs/site/forms.md`, `site/forms/46.json`.
- Правка `calc_service/calculators/presswall.py`, цен, `calc_service/data/`, `scripts/js_port_gaps_allowed.txt`, `scripts/run_js_calc.mjs`.
- Новый эталон с тиражом ≥ 2.
- Удаление копии и черновика.
- Остальные формы эпика — свои задачи.

## Критерии приёмки

Каждый пункт — команда и ожидаемый результат. `COPY` и `PRODUCT` — id копии и черновика из отчёта. В PowerShell 5.1 кавычки JSON внутри аргумента экранируются `\"`, как в skill.

- [x] Порт. В блоке `calcPresswall` строка `нет в Python:` пустая или каждая позиция уже есть в `scripts/js_port_gaps_allowed.txt`.

```powershell
python scripts/js_port_gaps.py calcPresswall
```

- [x] Раннер на кейсе дефолта формы 46 (тираж 1, с креплением) печатает `price`. Ниже — образец на люверсах, mode 1 (08.11.2026: 13914.624); поля подставить из дефолта формы, команды других кейсов — `docs/js-runner-cases.md`. 404 API, API без `is_eyelet` в `tool_schema` или расхождение — стоп, форму не дублировать. Калькулятор и `calc_service/data/` не править.

```powershell
node scripts/run_js_calc.mjs calcPresswall --data current --args '[1,\"Joker30_20_eyelet\",\"BannerFronlitCoat400\",{\"isPresswall\":true,\"isRent\":0,\"isEyelet\":[300,300,300,300]},1]'
Invoke-RestMethod -Method Post -Uri https://insain.ru/api/v1/calc/presswall -ContentType 'application/json' -Body '{"quantity":1,"presswall_id":"Joker30_20_eyelet","material_id":"BannerFronlitCoat400","is_presswall":true,"is_rent":0,"is_eyelet":[300,300,300,300],"mode":1}' | Select-Object price, time_ready
```

- [x] `price` раннера и API: абсолютная разница ≤ 0.02 и относительная ≤ 0.001. Подставить оба числа. Stdout начинается с `ok`.

```powershell
$OutputEncoding = New-Object System.Text.UTF8Encoding $false
@'
js = JS_PRICE
api = API_PRICE
abs_d = abs(js - api)
rel = abs_d / max(abs(api), 1e-9)
assert abs_d <= 0.02 and rel <= 0.001, (js, api, abs_d, rel)
print("ok", js, api, abs_d, rel)
'@ | python -
```

- [x] Эталон дефолта формы в `test_presswall.py` — кейс с креплением: уже есть от `presswall-banner-options` или добавлен с этого прогона (комментарий `# JS, ДД.ММ.ГГГГ` и вызов раннера рядом, `price` равен цене раннера). Допуск assert: `cost`, `price`, `time_ready` — `rel=0.001`, `weight_kg` — `abs=0.02`. Stdout: `passed`, `failed` нет. Расхождение JS и Python — стоп, файл не менять.

```powershell
python -m pytest calc_service/tests/test_calculators/test_presswall.py -q
```

- [x] Файл формы. В выводе есть `insaincalc.calcApi('presswall'`, `insaincalc.syncUrl(` и `insaincalc.showResult(`, а также `is_eyelet`, `is_pocket`, `is_cutting` и `is_bag` — крепление и чехол уходят в `calcApi`.

```powershell
Select-String -Path wp-plugin\forms\presswall.js -Pattern "calcApi\('presswall'|syncUrl\(|showResult\(|is_eyelet|is_pocket|is_cutting|is_bag"
```

- [x] Контракт всех `forms/*.js`. Stdout: `passed`.

```powershell
python -m pytest calc_service/tests/test_wp_plugin_forms.py -q
```

- [x] Копия не на витрине. Одна строка со статусом `draft` или `private`. HTTP без cookies — `404`.

```powershell
ssh insain-prod "sudo -u www-data wp post get PRODUCT --field=post_status --path=/var/www/insain.ru"
curl.exe -s -o NUL -w "%{http_code}" "https://insain.ru/?post_type=product&p=PRODUCT"
```

### Критерии перевода формы ezFC на API

- [x] На копии под админом (`https://insain.ru/?post_type=product&p=PRODUCT&preview=true`) эталон даёт `POST /api/v1/calc/presswall` → 200, в теле коды материалов, не `0`. Цена на странице равна `price` API с округлением `showResult`. В «Результат» — код ответа и обе цены.
- [x] Люверсы и карман в dpdAttachment дают разные `price`, каждая равна раннеру на том же входе (rel ≤ 0.001).
- [x] Смена каждого dropdown меняет цену и таблицу материалов. В таблице нет внутренних `code`. Есть вес и срок с подсказкой дат. Перезагрузка не меняет режим и срок.
- [x] URL обновляется GET-именами формы (имя параметра = имя элемента). Ссылка с этими GET открывает копию с теми же значениями и той же ценой. У dropdown с кодом в `data-value` — `GET_check=index`. У radio со значениями `1`/`2` — `GET_check=value`.

## Проверки

- [x] `python scripts/dev.py check` — код выхода 0
- [x] Self-review — чеклист «Перед сдачей» в [AGENTS.md](../AGENTS.md)

## Риски

- Прод: дубль и GET только с подтверждения человека. Боевая страница клиентам не меняется.
- Цены: JSON не править. Чужой `price` на проде не выравнивать. Расхождение JS и Python (локальный расчёт и боевой API, rel > 0.001) — стоп и эскалация, калькулятор не править.
- Формы: id элементов боевой формы 46 не менять. В админке пишется только копия.

## Режим

прод

## Журнал передач

Строка на сессию: `<дата> — <роль>, <модель> — <итог> — дальше <роль>`. Блокер — по формату [docs/agents/workflow.md](../docs/agents/workflow.md).

08.11.2026 — Implementer, Opus 5.5 — стоп на сверке (skill verify, шаги 5а–5б): крепление баннера из формы 46 в API не уходит, файлы не менялись — дальше Analyst

```
Блокер: поле dpdAttachment (1845, «люверсы» / «карман») боевой формы 46 влияет на цену, а у POST /api/v1/calc/presswall параметра для него нет — форму на API не перевести без недооценки.
Пробовал: js_port_gaps calcPresswall — блок calcPresswall пуст (calcPrintRoll call calcLaminationWide есть в allowed); эталон REF_PARAMS: раннер price 11453.624, боевой API 11453.624, проверка abs/rel — ok. cjsCalc 1862 (SELECT): при dpdAttachment=isEyelet ставит options isEyelet [300,300,300,300], при isPocket — isPocket [1,0,1,0] и isCutting [0,1,0,1]; у dropdown только эти две опции, т.е. одна из них всегда в options. calcPresswall передаёт options в calcPrintRoll баннера. Раннер, тираж 1, Joker30_20_eyelet, BannerFronlitCoat400, каркас: с люверсами price 13914.624 / time_ready 19.94; с карманом 12659.624 / 19.12; без крепления 11453.624 / 18.3. API на том же входе (лишний is_eyelet игнорируется) — 11453.624. tool_schema presswall: quantity, presswall_id, material_id, is_presswall, is_rent, is_bag, mode — крепления нет; presswall.py вызывает PrintRollCalculator без опций. Без баннера (material_id "") JS и API сходятся: 7006.624.
Гипотеза: порт calcPresswall потерял проброс options в calcPrintRoll; js_port_gaps его не видит, потому что смотрит только options.has() самой функции. REF_PARAMS (баннер без крепления) на форме недостижим.
Вопрос: завести задачу-предпосылку по skill port-fix-prerequisite — параметр крепления (люверсы / карман) в presswall API с пробросом в print_roll, эталоны раннера на обоих вариантах; эту задачу — `заблокировано: ждёт todo/<предпосылка>.md`, эталон в test_presswall.py переснять на кейсе с креплением.
Следующая сессия: Analyst, модель Opus 5.5
```

08.11.2026 — Analyst, Opus 5.5 — задача-предпосылка `presswall-banner-options` (закрыто 2026-11-09, `docs/history/log.md`) (крепление, плюс найденные раннером люверсы `calc_eyelet`, режим баннера, чехол); эталон — кейс с креплением, `forms/presswall.js` передаёт крепление и чехол, допуск веса `abs=0.02` — дальше человек: после закрытия предпосылки `черновик`, Implementer — `git rebase main`

09.11.2026 — Implementer, Opus 5.5 — git-часть готова: дефолт формы 46 (без баннера) раннер = боевой API 7006.624, кейс `REF_FORM_DEFAULT` в `test_presswall.py`, `wp-plugin/forms/presswall.js`; `make check` зелёный — дальше человек («да» на дубль), затем Site ops

```
Блокер: следующий шаг — дубль формы 46 и черновик товара на проде (skill ezfc-form-to-api, copy.md, шаги 6–16) — только после «да» человека.
Пробовал: шаги 0–5б пройдены, критерии Implementer — в «Результат».
Гипотеза: —
Вопрос: дублировать форму 46 CalcPresswall на черновик товара для копии на API?
Следующая сессия: Site ops, модель Opus 5.5
```

09.11.2026 — человек — «да» на дубль формы 46 CalcPresswall и черновик товара (в чате Orchestrator) — дальше Site ops

09.11.2026 — Site ops, Opus 5.5 — копия 92 на черновике 2586885 (draft, гость 404), JS и GET из `forms/presswall.js` через `ezfc_copy_apply.php`, прогон под админом: дефолт 7006.624, люверсы 13914.624, карман 12659.624, аренда, чехол, режим, перезагрузка и ссылка с GET сходятся с раннером и боевым API; форма 46 не тронута — дальше человек принимает копию, затем Reviewer

09.11.2026 — человек — «принято» на копию 92 на черновике 2586885 (в чате Orchestrator) — дальше Implementer

09.11.2026 — Implementer, Opus 5.5 — строка формы 46 в «Состав пакета» `todo/forms-batch-switch.md` (92 / 2586885 (draft), копия принята 09.11.2026); `make check` зелёный, коммитов нет — дальше Reviewer

09.11.2026 — Reviewer, Grok 4.7 — принято — дальше человек: finish-task

09.11.2026 — человек — принято — закрытие

## Ревью 1

Вердикт: `принято`. Замечаний нет.

- Diff `task/form-presswall` (HEAD `f0d1f4b`, коммитов нет): `test_presswall.py` — только `REF_FORM_DEFAULT` (`# JS, 09.11.2026`, вызов раннера рядом, `price` 7006.624); допуск прежний (`rel=0.001`, вес `abs=0.02`). `wp-plugin/forms/presswall.js` — id боевой формы 46, `calcApi('presswall'`, `syncUrl`, `showResult`, `is_eyelet` / `is_pocket` / `is_cutting` / `is_bag`. `todo/forms-batch-switch.md` — одна строка 46 / 92 / 2586885 (draft). Калькулятор, `calc_service/data/`, `docs/site/forms.md` не менялись. `docs/dashboard.md` — пересборка `make check`.
- Раннер дефолта формы: `price` 7006.624, `cost` 4270, `time_ready` 17.72 — как в эталоне. `pytest test_presswall.py test_wp_plugin_forms.py -q` — `14 passed`.
- Прод, чтение: cjsCalc 3497 (форма 92) совпадает с `forms/presswall.js` после подстановки id копии (3491, 3492, 3494, 3495, 3496, 3510); `read_file` = `0`. GET: 3490 `numN`, 3493 `numDays` (без `GET_check`); 3491 `dpdPresswall`, 3492 `rdoPresswal`, 3494 `dpdBanner`, 3495 `dpdAttachment`, 3496 `dpdBag` — `index`; 3510 `rdoModeProduction` — `value`. Форма 46: 26 элементов, пустой GET, нет `calcApi`, `read_file` ≠ 1; cjsCalc 1862 — `calcPresswall`, `read_file` = `0`. Товар 2586885 — `draft`, `ezfc_form_id` 92, гость 404. Товар 2586683 — `publish`, форма 46, страница каталога 200.

## Найдено вне scope

- `weight_kg` presswall на эталоне: раннер 9.79, Python и боевой API 9.78 (rel 0.00102) — presswall.py суммирует вес баннера, уже округлённый print_roll до 0.01. Учтено: допуск `abs=0.02` в assert веса.
- skill `ezfc-form-to-api` (verify.md, шаг 1а) требует строку раннера дефолта в `docs/js-runner-cases.md`; файла нет в «Файлы» задачи — команда только в комментарии `REF_FORM_DEFAULT`.
- Раннер `calcPresswall` с баннером `BannerFronlitLamin440` (ламинированный 440) падает «Поле weight_kg не число (NaN)» — старый JS не считает вес этого баннера; API отдаёт цену (каркас 2,5×2,5 + карман: 12790.624). Сверку JS и API на ламинированном баннере сделать нечем.
## Результат

- Ветка, PR или коммит: `task/form-presswall` от `main` f0d1f4b; коммит — после шага 5 finish-task.
- Период: 08.11.2026 – 09.11.2026
- Часы человека: не учтено
- Работа агентов:
- Было / стало: у формы 46 нет JS на API → `forms/presswall.js` с креплением и чехлом в `calcApi`, эталон дефолта формы в тесте
- Сделано:
  - Дефолт боевой формы 46 (HTML страницы, `selected`/`checked`): numN 1, dpdPresswall `Joker30_20_eyelet`, dpdBanner «без баннера» (`""`), dpdAttachment люверсы, dpdBag «не нужна», rdoPresswal «изготовить», режим 1. Дефолт без баннера, поэтому кейсы `presswall-banner-options` (все с баннером) с ним не совпали — добавлен `REF_FORM_DEFAULT` (`# JS, 09.11.2026`, вызов раннера рядом).
  - `wp-plugin/forms/presswall.js`: id боевой формы 46 (numN 1843, dpdPresswall 1844, dpdAttachment 1845, dpdBanner 1879, dpdBag 1880, numDays 1882, rdoPresswal 1883, rdoModeProduction 1875; cjsCalc 1862). rdoPresswal: isPresswall → `is_presswall: true, is_rent: 0`; isRent → `is_presswall: false, is_rent: numDays`; noPresswall → `false, 0` (как `options` в cjsCalc 1862). Крепление и чехол — как cjsCalc 1862.
- Чем проверено:
  - `python scripts/js_port_gaps.py calcPresswall` — блок `calcPresswall`: `нет в Python:` пусто; в цепочке `calcPrintRoll call calcLaminationWide` и `calcLaminationWide module` — оба в `js_port_gaps_allowed.txt`.
  - Дефолт формы: раннер `[1,"Joker30_20_eyelet","",{"isPresswall":true,"isEyelet":[300,300,300,300]},1]` → cost 4270, price 7006.624, time_ready 17.72, weight 7.38; боевой API на том же входе → 4270 / 7006.624 / 17.72 / 7.38. Проверка abs/rel: `ok 7006.624 7006.624 0.0 0.0`.
  - Люверсы с баннером, mode 1: раннер 13914.624 / 19.94, боевой API 13914.624 / 19.94; `ok 13914.624 13914.624 0.0 0.0`.
  - Дополнительно: аренда 2 дня + карман + bag210, mode 2 — раннер 9116.8925 / 27.39, боевой API 9116.8925 / 27.39 (`is_presswall: false, is_rent: 2`).
  - `tool_schema/presswall` на проде: есть `is_eyelet`, `is_pocket`, `is_cutting`, `is_bag`, `is_rent`, `is_presswall`, `mode`.
  - Implementer, 09.11.2026, после принятия копии: `python scripts/dev.py check` — `538 passed`, `81 passed`, код выхода 0; `js_port_gaps.py calcPresswall` — `нет в Python:` пусто; `pytest test_presswall.py test_wp_plugin_forms.py -q` — `14 passed`. Раннер и боевой API не перезапускались (на прод не ходить) — числа выше от 09.11.2026.
  - `pytest test_presswall.py -q` — `11 passed`; `pytest test_wp_plugin_forms.py -q` — `3 passed`; `Select-String` по `presswall.js` — есть `calcApi('presswall'`, `syncUrl(`, `showResult(`, `is_eyelet`, `is_pocket`, `is_cutting`, `is_bag`.
- Site ops, 09.11.2026 (копия, skill `ezfc-form-to-api`, шаги 6–16):
  - Копия формы `COPY` = **92** («CalcPresswall duplicate», одна новая строка в `wp_insain_ezfc_forms`). Черновик товара `PRODUCT` = **2586885** («Калькулятор прессволов (Копировать)», WooCommerce «Дублировать» от 2586683). Превью: https://insain.ru/?post_type=product&p=2586885&preview=true
  - `wp post meta update 2586885 ezfc_form_id 92` → `Success: Updated custom field 'ezfc_form_id'.`; `post_status` → `draft`; гость `curl` → `404`.
  - Карта id (шаг 9): все 26 элементов с `id_copy` ≠ `id_live`; поля копии: numN 3490, dpdPresswall 3491, rdoPresswal 3492, numDays 3493, dpdBanner 3494, dpdAttachment 3495, dpdBag 3496, cjsCalc 3497, rdoModeProduction 3510.
  - `ezfc_copy.py … --get numN --get numDays --get rdoModeProduction:value --get dpdPresswall:index --get dpdAttachment:index --get dpdBanner:index --get dpdBag:index --get rdoPresswal:index`; `ezfc_copy_apply.php` показ — без `стоп`, cjsCalc `calcApi=0 → calcApi=1`, `read_file` `'0' = '0'`, rdoModeProduction `GET_check 'index' → 'value'`; `apply` — `бэкап: /tmp/ezfc-copy-92-20261108-163736.json`, `записано` у 9 элементов. Затем `wp litespeed-purge all` и `wp cache flush`.
  - Блок результата копии сверен с формой 79 по `data` элементов (группы, колонки, стили, HTML `htmTime`/`htmCost`/`htmMaterial`, порядок): отличий нет, кроме `sbtWeightTotal.show_in_email_cond` (на вид не влияет). Правка в админке не понадобилась.
  - Прогон под админом (Browser MCP, перехват `fetch` к `/calc/`), все запросы `POST https://insain.ru/api/v1/calc/presswall` → 200, коды в теле, не `0`:

    | Вход на копии | `price` API | Раннер JS | На странице |
    | --- | --- | --- | --- |
    | Дефолт (без баннера, люверсы) | 7006.624 | 7006.624 | 7 100 руб. |
    | Литой 400 + люверсы, режим 1 | 13914.624 | 13914.624 | 14 000 |
    | Литой 400 + карман, режим 1 | 12659.624 | 12659.624 | 12 700 |
    | Каркас 2,5×2,5, литой, карман | 13015.624 | 13015.624 | 13 100 |
    | То же, ламинированный 440 | 12790.624 | падает (вес NaN, «Найдено вне scope») | 12 800 |
    | + чехол bag210 | 14926.5165 | — | 15 000 |
    | Аренда 3 дня, литой, карман, bag210, режим 2 | 10136.8925 | 10136.8925 | 10 200 |
    | Литой + люверсы, режим 2 (ссылка с GET) | — | 14040.704 | 14 100 |
    | Свой прессвол, литой, люверсы, bag160 (ссылка с GET) | 8925.6175 | 8925.6175 | 9 000 |

    Цена на странице — `insaincalc.round` вверх до 100 руб. (проверено в консоли: 7006.624 → 7100, 13914.624 → 14000, 12659.624 → 12700). Таблица материалов — только названия (люверсы пропадают при кармане, каркас — при аренде и «своём»), вес и «Срок N дней» с подсказкой дат (`data-bs-original-title`: «Готовность заказа: …»).
  - Аренда: копия шлёт `is_presswall: false, is_rent: N`. Старый JS смотрит наличие ключа (`options.has('isPresswall')`), а cjsCalc 1862 при аренде ключ не ставит, поэтому раннер — без `isPresswall`; с `"isPresswall": false` раннер ошибочно добавляет каркас (16249.60 против 9116.89). Для Reviewer: на копии всё верно.
  - Перезагрузка с `rdoPresswal=1&numDays=3&rdoModeProduction=2`: режим «быстрее», аренда, 3 дня, все dropdown и цена 10 200 те же. Ссылка в новой вкладке — те же значения и цена.
  - Консоль: ошибки только из стороннего `insainParse/…/scrtp.js` (есть и в админке); ошибок `insaincalc`/`ezfc` нет.
  - Боевая форма 46 не тронута (SQL): cjsCalc 1862 — `calcPresswall` есть, `calcApi` нет; GET у полей 1843–1883 пустые. Товар 2586683 — `ezfc_form_id` 46, https://insain.ru/catalog/kalkulyator-pressvolov/ → 200. `curl /api/v1/calculators` — отвечает.
  - Откат копии JS/GET: строки из `/tmp/ezfc-copy-92-20261108-163736.json` на VDS. Копия 92 и черновик 2586885 не удалялись (не-scope).
- Принятие: человек 09.11.2026 принял копию 92 на черновике 2586885; строка формы 46 добавлена в «Состав пакета» `todo/forms-batch-switch.md`.
- Не сделано и почему: боевая форма 46 — не-scope (переключение в `forms-batch-switch`).
- Для Site ops: GET на копии — `numN`, `dpdPresswall`, `dpdAttachment`, `dpdBanner`, `dpdBag` (dropdown с кодом, `GET_check=index`), `rdoPresswal` (radio с кодами isPresswall/isRent/noPresswall, не `1`/`2` — `GET_check=index`, в `syncUrl` уходит индекс), `numDays`, `rdoModeProduction` (`GET_check=value`). Дефолт копии — без баннера: для проверки крепления на копии выбрать баннер, иначе люверсы и карман дают одну цену 7006.624.
- Требуется решение: нет.
- Строка в «Состав пакета» `todo/forms-batch-switch.md` (формат по соседним строкам):

| 46 CalcPresswall | `presswall` | `/catalog/kalkulyator-pressvolov/` | 92 / 2586885 (draft) | копия принята 09.11.2026, `form-presswall` |
