# form-flag

Статус: закрытие
Сложность: средняя
Implementer: Grok 4.7
Reviewer: Auto
Site ops: Grok 4.7
Почему: типовая форма серии по skill `ezfc-form-to-api`, калькулятор уже на API; прод — только копия формы по шагам skill.
Чат: человек открывает новый чат с моделью из поля Implementer.

## Цель

Копия формы 55 CalcFlagPaper на черновике товара считает `POST /api/v1/calc/flag`. URL копии пишется GET-именами элементов. Ссылка с этими GET открывает ту же копию с теми же значениями и той же ценой. Боевая форма 55 на странице https://insain.ru/catalog/kalkulyator-flazhkov-bumazhnyh/ по-прежнему на `insaincalc.calcFlagPaper`.

## Контекст и ссылки

- `.cursor/skills/ezfc-form-to-api/SKILL.md` — порядок. Боевая форма (шаги 17–24 skill) в эту задачу не входит.
- `docs/ezfc-api-migration.md` — шаблон `cjsCalc`, GET = имя элемента, `GET_check`: dropdown с кодом — `index`, radio `1`/`2` — `value`.
- `docs/site/forms.md` — строка формы 55, только читать.
- `todo/forms-batch-switch.md` — в конце одна строка в «Состав пакета».
- `todo/EPIC-forms-to-api.md` — очередь, после `form-pennant` (закрыто 2026-11-11, `docs/history/log.md`).
- `todo/flag-materials-size-mm.md` — предпосылка: `size_mm` в ответе `flag` (шаг 3а skill). До close — `flag.js` и копию не начинать.
- `docs/js-runner-cases.md` — команда раннера и `price` для `calcFlagPaper`.
- Эталон: `REF_PARAMS` в `calc_service/tests/test_calculators/test_flag.py` — 100 шт., 100×150, `PaperCoated115M`, `4+0`, mode 1. Порог `price` — прогон JS против API, не число из файла. JS: `js_legacy/calc/calcFlag.js`, сигнатура `calcFlagPaper(n, size, color, materialID, options, modeProduction)`.
- Остальное не открывать.

## Scope

- Раннер готов (`js-runner-forms` закрыта 05.11.2026). Кейс и команда раннера — из `docs/js-runner-cases.md`. `calc_service/data/` и калькулятор не менять.
- JS и API сошлись — переснять эталон в `test_flag.py` с пометкой `JS, ДД.ММ.ГГГГ`, как в `test_tablets.py`. Допуск assert — `rel=0.001`. Не сошлись — файл не трогать. Кейс `REF_FORM_DEFAULT` (дефолт формы 55) и команда раннера в `docs/js-runner-cases.md` — после close `flag-materials-size-mm`, вместе с `flag.js` (skill `verify.md` п.1а).
- `wp-plugin/forms/flag.js`: id элементов боевой формы 55, `insaincalc.syncUrl`, `insaincalc.calcApi('flag'`, `insaincalc.showResult`. Своих формул цены и чтения через DOM нет.
- Дубль формы и черновик товара — только после «да» человека. На копию — тот же JS с id копии, без `read_file`.
- GET на копии: имя параметра = имя элемента. Боевую форму не размечать.
- Прогон копии под админом: эталон, смена полей, ссылка с GET.
- После принятия копии человеком — одна строка в таблицу «Состав пакета» `todo/forms-batch-switch.md`. Ветка `task/form-flag` от `main`.

Распределение: сверку эталона, `test_flag.py`, `wp-plugin/forms/flag.js` и строку в `todo/forms-batch-switch.md` делает Implementer. Дубль и черновик товара, JS и GET на копии, прогон под админом — Site ops; расхождение на копии возвращается Implementer.

## Файлы

- `wp-plugin/forms/flag.js`
- `calc_service/tests/test_calculators/test_flag.py`
- `todo/forms-batch-switch.md` — общий для задач эпика: одна строка в «Состав пакета»
- WordPress: только копия формы и черновик товара

## Не-scope

- `read_file` и любое переключение боевой формы 55. Выкладка плагина. `infra/deploy.sh`.
- `docs/site/forms.md`, `site/forms/55.json`.
- Правка `calc_service/calculators/flag.py`, цен, `calc_service/data/`, `scripts/js_port_gaps_allowed.txt`, `scripts/run_js_calc.mjs`.
- Удаление копии и черновика.
- Остальные формы эпика — свои задачи.

## Критерии приёмки

Каждый пункт — команда и ожидаемый результат. `COPY` и `PRODUCT` — id копии и черновика из отчёта. В PowerShell 5.1 кавычки JSON внутри аргумента экранируются `\"`, как в skill.

- [x] Порт. В блоке `calcFlagPaper` строка `нет в Python:` пустая или каждая позиция уже есть в `scripts/js_port_gaps_allowed.txt`.

```powershell
python scripts/js_port_gaps.py calcFlagPaper
```

- [x] Раннер на входе эталона печатает `price`. Команда — из `docs/js-runner-cases.md` для `calcFlagPaper`. 404 API или расхождение — стоп, форму не дублировать. Калькулятор и `calc_service/data/` не править.

```powershell
node scripts/run_js_calc.mjs calcFlagPaper --data current --args '<args из docs/js-runner-cases.md>'
Invoke-RestMethod -Method Post -Uri https://insain.ru/api/v1/calc/flag -ContentType 'application/json' -Body '{"quantity":100,"width_mm":100,"height_mm":150,"material_id":"PaperCoated115M","color":"4+0","mode":1}' | Select-Object price
```

- [x] `price` раннера и API: абсолютная разница ≤ 0.02 и относительная ≤ 0.001. Подставить оба числа. Stdout начинается с `ok`. JS = API = 3934.4107840000006, abs 0, rel 0.

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

- [x] Эталон в `test_flag.py` переснят с этого прогона: комментарий `# JS, ДД.ММ.ГГГГ` и вызов раннера рядом с эталоном, в docstring та же пометка, `price` в `EXPECTED_*` равен цене раннера, допуск assert — `rel=0.001`. Stdout: `passed`, `failed` нет. Расхождение JS и Python — стоп, файл не менять.

```powershell
python -m pytest calc_service/tests/test_calculators/test_flag.py -q
```

- [x] Файл формы. В выводе есть `insaincalc.calcApi('flag'`, `insaincalc.syncUrl(` и `insaincalc.showResult(`.

```powershell
Select-String -Path wp-plugin\forms\flag.js -Pattern "calcApi\('flag'|syncUrl\(|showResult\("
```

- [x] Контракт всех `forms/*.js`. Stdout: `passed`.

```powershell
python -m pytest calc_service/tests/test_wp_plugin_forms.py -q
```

- [x] Копия не на витрине. Одна строка со статусом `draft` или `private`. HTTP без cookies — `404`. Товар 2586888: `draft`, `curl` без cookies — `404`.

```powershell
ssh insain-prod "sudo -u www-data wp post get PRODUCT --field=post_status --path=/var/www/insain.ru"
curl.exe -s -o NUL -w "%{http_code}" "https://insain.ru/?post_type=product&p=PRODUCT"
```

### Критерии перевода формы ezFC на API

- [x] На копии под админом (`https://insain.ru/?post_type=product&p=PRODUCT&preview=true`) эталон даёт `POST /api/v1/calc/flag` → 200, в теле коды материалов, не `0`. Цена на странице равна `price` API с округлением `showResult`. В «Результат» — код ответа и обе цены. Копия 95, товар 2586888: 200, `price` 4052.2966080000006, на странице 4 100 руб.
- [x] Смена каждого dropdown меняет цену и таблицу материалов. В таблице нет внутренних `code`. Есть вес и срок с подсказкой дат. Перезагрузка не меняет режим и срок. Цветность меняет цену; строки таблицы те же, что отдаёт API.
- [x] URL обновляется GET-именами формы (имя параметра = имя элемента). Ссылка с этими GET открывает копию с теми же значениями и той же ценой. У dropdown с кодом в `data-value` — `GET_check=index`. У radio со значениями `1`/`2` — `GET_check=value`.

## Проверки

- [x] `python scripts/dev.py check` — код выхода 0. calc_service: 545 passed. bot_service: 81 passed.
- [x] Self-review — чеклист «Перед сдачей» в [AGENTS.md](../AGENTS.md)

## Риски

- Прод: дубль и GET только с подтверждения человека. Боевая страница клиентам не меняется.
- Цены: JSON не править. Чужой `price` на проде не выравнивать. Расхождение JS и Python (локальный расчёт и боевой API, rel > 0.001) — стоп и эскалация, калькулятор не править.
- Формы: id элементов боевой формы 55 не менять. В админке пишется только копия.

## Режим

прод

## Журнал передач

Строка на сессию: `<дата> — <роль>, <модель> — <итог> — дальше <роль>`. Блокер — по формату [docs/agents/workflow.md](../docs/agents/workflow.md).

2026-11-11 — Implementer, Grok 4.7 — цена и срок JS и API сошлись, на дефолте нет `size_mm`, `flag.js` не писался — дальше Analyst

Блокер: шаг 3а skill `ezfc-form-to-api`. Дефолт боевой формы 55 на странице показывает размеры материалов, `POST /api/v1/calc/flag` их не отдаёт. `flag.js` не создан, копия формы не делалась.
Пробовал: раннер и боевой API на эталоне 100×150 и на дефолте 200×99 — `price` совпал, `time_ready` в допуске rel ≤ 0.001. Локально `PrintSheetCalculator` отдаёт бумаге `size_mm` [320, 450], `calc_set_staples` и `calc_set_shaft` — `None`. Ответ `flag` после сборки в `flag.py` (строки 205–229) без `size_mm`. На странице: бумага 320×450 × 18, скобы 6×0 × 100, трубочка 5×380 × 100.
Гипотеза: `flag.py` копирует материалы печати без `size_mm`. Скобы и палочка не пишут размер каталога: JS `calcProcessTools.js` строки 235 и 1386 кладут `staples.size` и `shaft.size`, Python `calc_set_staples` / `calc_set_shaft` — нет (у шнура в `calc_set_rope` размер уже есть).
Вопрос: предпосылка на `size_mm` (калькулятор и `process_tools`, не эта задача) или расширить scope `form-flag`?
Следующая сессия: Analyst. Модель Analyst в шапке не задана.

2026-11-11 — Analyst, Grok 4.7 — предпосылка `flag-materials-size-mm`, scope формы не расширять — дальше Implementer flag-materials-size-mm
2026-11-12 — человек — предпосылка `flag-materials-size-mm` закрыта, боевой API отдаёт `size_mm` на дефолте формы 55 — дальше Implementer
2026-11-12 — Implementer, Grok 4.7 — сверка сошлась, `flag.js` и эталон дефолта готовы, дубль ждёт «да» — дальше человек
2026-11-12 — человек — «да» на дубль формы 55 и черновик товара — дальше Site ops
2026-11-12 — человек — «да» на дубль формы 55 и черновик товара — дальше Site ops

Блокер: шаг 6 skill `ezfc-form-to-api`. Дубль формы 55 и черновик товара — только после «да» человека. Боевая форма не менялась, на прод ничего не писалось.
Пробовал: шаги 0–5б локально и чтением прода. Порт `calcFlagPaper` пустой. Эталон 100×150 и дефолт 200×99: `price` JS = API, `time_ready` rel ≤ 0.001, `size_mm` бумаги, скоб и трубочки совпал со страницей. `wp-plugin/forms/flag.js` написан на id боевой формы 55.
Гипотеза: это штатные ворота skill перед дублем, не расхождение порта.
Вопрос: дублировать форму 55 CalcFlagPaper на черновик товара? Боевая страница https://insain.ru/catalog/kalkulyator-flazhkov-bumazhnyh/ не меняется.
Следующая сессия: человек. После «да» — Site ops, модель Grok 4.7.
2026-11-12 — Site ops, Grok 4.7 — копия формы 95 на черновике 2586888 считает flag, боевая форма 55 не менялась — дальше человек
2026-11-12 — человек — копия 95 на черновике 2586888 принята — дальше Reviewer
2026-11-12 — Reviewer, Auto — принято — дальше человек
2026-11-12 — человек — принято — закрытие

## Найдено вне scope

- Подпись опции `dpdSize` «200х90мм», `data-value` «200,99»: страница считает 200×99. Править форму в этой задаче нельзя.
- Имя `PaperCoated115M`: JS `js_legacy/material/sheet.json` «113г/м», Python `calc_service/data/materials/sheet.json` «115г/м». Код, тираж 18 и цена совпали.
- Эталон задачи 100×150 нет в `dpdSize` (148×105, 200×99, 210×148). На странице его не ввести.
- Вес на копии 0.24 кг (API `weight_kg` 0.2377), на боевой форме 55 при тех же полях «Вес тиража 0.29 кг». Цена 4 100 и срок «Срок 1 день» с той же подсказкой дат совпали. Калькулятор в этой задаче не менялся.

## Результат

- Ветка, PR или коммит: `task/form-flag` → `main` (fast-forward 2026-11-12)
- Период: 2026-11-12
- Часы человека: не учтено
- Работа агентов: Implementer, Grok 4.7; Site ops, Grok 4.7
- Было / стало: боевая форма 55 по-прежнему на `insaincalc.calcFlagPaper`. Появились копия формы 95 `CalcFlagPaper duplicate` и черновик товара 2586888 «Калькулятор флажков бумажных (Копировать)» с `ezfc_form_id` 95. На копии `cjsCalc` 3568 вызывает `insaincalc.calcApi('flag'`, GET-имена прописаны.
- Сделано: шаги 6–16 skill. Дубль формы 55 одним кликом — id 95, второй новой формы нет. Черновик товара 2586888, гость получает 404. JS копии собран из `wp-plugin/forms/flag.js` с id копии, без `read_file`. GET: `numN`; `dpdSize`, `dpdColor`, `dpdMaterial`, `dpdCoverLaminat` — `index`; `rdoModeProduction` — `value` (на копии было `index`). Боевая форма 55 и товар 2586729 не менялись. Блок результата на копии уже как у формы 79: цена и «со скидкой» в одной строке, режим внутри группы срока, вес, таблица с размером.
- Чем проверено:
  - `python scripts/js_port_gaps.py calcFlagPaper` — у `calcFlagPaper` строка `нет в Python:` пустая. Пропуски `calcPrintSheet` (`call calcCutRoller`, `call calcPrintLaser`) уже в `scripts/js_port_gaps_allowed.txt`.
  - Раннер эталона — `price` 3934.4107840000006, `time_ready` 9.41. Боевой API — `price` тот же, `time_ready` 9.406 (rel 0.000425). Скрипт допуска: `ok 3934.4107840000006 3934.4107840000006 0.0 0.0`.
  - Раннер дефолта `[100,[200,99],"4+0","PaperCoated115M",{},1]` — `cost` 2508.1588, `price` 4052.2966080000006, `time_hours` 1.03, `time_ready` 9.45. API — `price` тот же, `time_ready` 9.442 (rel 0.000847). Скрипт: `ok price default` и `ok time_ready default`.
  - Страница формы 55, дефолт: бумага 320×450 × 18, скобы 6×0 × 100, трубочка 5×380 × 100. API `materials` — те же размеры и количества. Имя бумаги на странице «113г/м», в API «115г/м» — уже в «Найдено вне scope».
  - `python -m pytest calc_service/tests/test_calculators/test_flag.py -q` — `9 passed`.
  - `Select-String` по `wp-plugin/forms/flag.js` — есть `syncUrl(`, `calcApi('flag'` и `showResult(`.
  - `python -m pytest calc_service/tests/test_wp_plugin_forms.py -q` — `3 passed`.
  - `python scripts/dev.py check` — код выхода 0. calc_service: 545 passed. bot_service: 81 passed.
  - Формы после дубля: `SELECT id, name … ORDER BY id DESC LIMIT 3` — `95 CalcFlagPaper duplicate`, дальше 94 и 93. Второй новой формы нет.
  - `wp post meta update 2586888 ezfc_form_id 95` — `Success: Updated custom field 'ezfc_form_id'.` Повторное чтение — `95`.
  - Статус товара: тот же `wp post get 2586888 --field=post_status` на сервере — `draft`. Прямой однострочный `ssh` с этой командой из PowerShell дважды завершился локально с кодом 1073741845 и пустым выводом; вывод получен тем же wp-cli через `bash` на сервере.
  - `curl.exe -s -o NUL -w "%{http_code}" "https://insain.ru/?post_type=product&p=2586888"` — `404`.
  - Показ пакета без `apply`: `calcApi=0 → calcApi=1`, GET пустые → имена, `rdoModeProduction` `index → value`, у dropdown `index = index`, `стоп` нет. С `apply`: `бэкап: /tmp/ezfc-copy-95-20261111-180608.json`, `записано` у 3568, 3563, 3581, 3564, 3565, 3566, 3567.
  - `wp litespeed-purge all` — `Error: Something went wrong! Got 400`. `wp cache flush` — `Success: The cache was flushed.` Страница копии после этого отдала новый JS.
  - Копия под админом, эталон: `POST /api/v1/calc/flag` 200, тело `{"quantity":100,"width_mm":200,"height_mm":99,"material_id":"PaperCoated115M","color":"4+0","mode":1}`. Ответ `price` 4052.2966080000006. На странице 4 100 руб. и 41 руб./шт (`insaincalc.round`). Консоли `insaincalc` и `ezfc` нет.
  - Размер index 2: 4 400 руб., бумага × 27. Цветность index 1: 5 100 руб., строки таблицы те же (API для 210×148, `4+0` и `4+4`: бумага × 27, скобы × 100, трубочка × 100, цены 4327.37 и 5025.87). Бумага index 1: 5 400 руб., в таблице «170г/м». Ламинация index 1: 7 300 руб., в таблице плёнка. Внутренних `code` в таблице нет. Вес 0.24 кг. Срок «Срок 1 день», подсказка дат на `<a>`.
  - Режим «быстрее» (`data-value` 2): URL `rdoModeProduction=2`, подсказка «Готовность заказа: 12.11.26, 15:00…», цена 8 800 руб. Перезагрузка оставила режим, срок, подсказку и цену.
  - Ссылка `?post_type=product&p=2586888&preview=true&numN=100&dpdSize=1&dpdColor=0&dpdMaterial=0&dpdCoverLaminat=0&rdoModeProduction=1` открыла те же поля и 4 100 руб. Режим `data-value` 1 отмечен.
  - Боевая страница https://insain.ru/catalog/kalkulyator-flazhkov-bumazhnyh/ : те же 4 100 руб., «Срок 1 день» и та же подсказка «13.11.26, 15:00 / 12.11.26, 11:00». Элемент 2265: `calcApi` не найден, `calcFlagPaper` на месте. Элемент 3568: `calcApi` есть.
- Не сделано и почему: выкладка плагина и переключение боевой формы 55 — не эта задача. Удаление копии и черновика не делалось.
- Как откатить: боевую форму 55 и товар 2586729 не трогали, откатывать нечего. JS и GET копии 95 — строки бэкапа `/tmp/ezfc-copy-95-20261111-180608.json`. Черновик 2586888 гостю отдаёт 404; удаление копии и черновика — только с «да» человека.
- Поля, которые есть в форме и не уходят в `calcApi`: нет. Пустой `dpdCoverLaminat` (значение «») не шлёт `lamination_id`. Обязательные параметры API (`quantity`, `width_mm`, `height_mm`, `material_id`) закрыты полями `numN`, `dpdSize`, `dpdMaterial`.
- Для Reviewer: id копии 95, товар 2586888, `post_status` draft. Id копии: `numN` 3563, `dpdSize` 3564, `dpdColor` 3565, `dpdMaterial` 3566, `dpdCoverLaminat` 3567, `cjsCalc` 3568, `rdoModeProduction` 3581 (`GET_check=value`, data-value `1` и `2`). Боевые id — в прежнем абзаце, GET-имена боевой пустые, `GET_check` режима на боевой по-прежнему `index`.
- Строка в «Состав пакета»: `| 55 CalcFlagPaper | flag | /catalog/kalkulyator-flazhkov-bumazhnyh/ | 95 / 2586888 (draft) | копия принята 12.11.2026, form-flag |`

## Ревью 1

**Вердикт:** принято.

| Критерий | Результат |
| --- | --- |
| Порт `calcFlagPaper` | `python scripts/js_port_gaps.py calcFlagPaper` — `нет в Python:` пусто |
| `test_flag.py` | `9 passed` (локально с незакоммиченным `test_form_default_flag` — `12 passed` вместе с `test_wp_plugin_forms.py`) |
| `flag.js` | `calcApi('flag'`, `syncUrl(`, `showResult(`; режим без `\|\| 1` |
| `docs/js-runner-cases.md` | Кейс дефолта 4052.296608 и команда раннера `[200,99]` |
| Копия не на витрине | SQL: товар 2586888 `draft`; `curl` без cookies — `404` |
| Боевой API дефолт | `POST /calc/flag` → `price` 4052.2966080000006 |
| Копия 95 на проде | SQL `forms_elements`: GET-имена у полей; dropdown `GET_check=index`; `rdoModeProduction` `value`; `cjsCalc` 3568 — `calcApi flag` |
| Боевая 55 | `cjsCalc` 2265 — `calcFlagPaper`; GET-имена пустые (не размечена, по scope ок) |

**Желательно:** перед слиянием закоммитить на ветке не только `9c5ee35`, но и рабочее дерево: `wp-plugin/forms/flag.js` (untracked), доработки `test_flag.py`, `docs/js-runner-cases.md`, актуальный `todo/form-flag.md`. Строку в `todo/forms-batch-switch.md` — по scope при закрытии, не блокер ревью копии.

## Промпт следующей сессии

```text
человек. todo/form-flag.md, ветка task/form-flag, папка d:\Projects\insain-agent.
Ревью принято (Reviewer, Auto, 2026-11-12). Закоммитить оставшиеся файлы scope на ветке, затем «принято, сливай» / skill finish-task: merge в main, close. Боевую форму 55 не переключать. Выкладка плагина с flag.js — отдельно (deploy-wp-plugin), когда решите выкатывать bridge; копия уже считает через JS в БД.
```
