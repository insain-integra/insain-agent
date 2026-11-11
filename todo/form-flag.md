# form-flag

Статус: черновик
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

- [ ] Файл формы. В выводе есть `insaincalc.calcApi('flag'`, `insaincalc.syncUrl(` и `insaincalc.showResult(`.

```powershell
Select-String -Path wp-plugin\forms\flag.js -Pattern "calcApi\('flag'|syncUrl\(|showResult\("
```

- [ ] Контракт всех `forms/*.js`. Stdout: `passed`.

```powershell
python -m pytest calc_service/tests/test_wp_plugin_forms.py -q
```

- [ ] Копия не на витрине. Одна строка со статусом `draft` или `private`. HTTP без cookies — `404`.

```powershell
ssh insain-prod "sudo -u www-data wp post get PRODUCT --field=post_status --path=/var/www/insain.ru"
curl.exe -s -o NUL -w "%{http_code}" "https://insain.ru/?post_type=product&p=PRODUCT"
```

### Критерии перевода формы ezFC на API

- [ ] На копии под админом (`https://insain.ru/?post_type=product&p=PRODUCT&preview=true`) эталон даёт `POST /api/v1/calc/flag` → 200, в теле коды материалов, не `0`. Цена на странице равна `price` API с округлением `showResult`. В «Результат» — код ответа и обе цены.
- [ ] Смена каждого dropdown меняет цену и таблицу материалов. В таблице нет внутренних `code`. Есть вес и срок с подсказкой дат. Перезагрузка не меняет режим и срок.
- [ ] URL обновляется GET-именами формы (имя параметра = имя элемента). Ссылка с этими GET открывает копию с теми же значениями и той же ценой. У dropdown с кодом в `data-value` — `GET_check=index`. У radio со значениями `1`/`2` — `GET_check=value`.

## Проверки

- [x] `python scripts/dev.py check` — код выхода 0. calc_service: 541 passed. bot_service: 81 passed.
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

## Найдено вне scope

- Подпись опции `dpdSize` «200х90мм», `data-value` «200,99»: страница считает 200×99. Править форму в этой задаче нельзя.
- Имя `PaperCoated115M`: JS `js_legacy/material/sheet.json` «113г/м», Python `calc_service/data/materials/sheet.json` «115г/м». Код, тираж 18 и цена совпали.
- Эталон задачи 100×150 нет в `dpdSize` (148×105, 200×99, 210×148). На странице его не ввести.

## Результат

- Ветка, PR или коммит: ветка `task/form-flag` от `main` (`6f7d6da`). Коммита нет. Незакоммичено: `calc_service/tests/test_calculators/test_flag.py`, `todo/form-flag.md`, `docs/dashboard.md` (статус задачи в дашборде).
- Период: 2026-11-11
- Часы человека: не учтено
- Работа агентов: Implementer, Grok 4.7, одна сессия
- Было / стало: эталон `test_flag.py` с пометкой JS 04.11.2026 и допуском `rel=0.03` → пометка JS 11.11.2026, `price` 3934.410784, допуск `rel=0.001`. `wp-plugin/forms/flag.js` нет.
- Сделано: порт `calcFlagPaper` пустой; пропуски `calcPrintSheet` (`call calcCutRoller`, `call calcPrintLaser`) уже в `scripts/js_port_gaps_allowed.txt`. Цена и срок эталона и дефолта формы сошлись с боевым API. Поля формы 55 сверены с `cjsCalc`: id верные. Эталон в тесте переснят.
- Чем проверено:
  - `python scripts/js_port_gaps.py calcFlagPaper` — у `calcFlagPaper` строка `нет в Python:` пустая.
  - `node scripts/run_js_calc.mjs calcFlagPaper --data current --args '[100,[100,150],"4+0","PaperCoated115M",{},1]'` — `price` 3934.4107840000006, `time_ready` 9.41.
  - `POST https://insain.ru/api/v1/calc/flag` тело эталона — `price` 3934.4107840000006, `time_ready` 9.406 (rel 0.000425). Скрипт допуска: `ok 3934.4107840000006 3934.4107840000006 0.0 0.0`.
  - Дефолт страницы (100, 200×99, `PaperCoated115M`, `4+0`, без ламинации, mode 1): раннер `price` 4052.2966080000006, `time_ready` 9.45; API `price` тот же, `time_ready` 9.442 (rel 0.000847). Количества: бумага 18, скобы 100, трубочка 100.
  - `python -m pytest calc_service/tests/test_calculators/test_flag.py -q` — `7 passed`.
  - `python scripts/dev.py check` — код 0. calc_service: 541 passed. bot_service: 81 passed.
- Не сделано и почему: `wp-plugin/forms/flag.js`, строка в `todo/forms-batch-switch.md`, дубль и черновик. Стоп шага 3а: без `size_mm` копия не покажет размеры. Калькулятор — в `flag-materials-size-mm`. `REF_FORM_DEFAULT` — после предпосылки, вместе с `flag.js`.
- Поля копии, когда перевод продолжится: `numN` 2256, `dpdSize` 2258 (`GET_check=index`), `dpdColor` 2282 (index), `dpdMaterial` 2263 (index), `dpdCoverLaminat` 2264 (index, пустое значение — не слать `lamination_id`), `rdoModeProduction` 2278 (на копии `GET_check=value`; сейчас на боевой index, значения data-value `1` и `2`), `cjsCalc` 2265. Дефолт: 100 шт., размер index 1 (`200,99`), цвет `4+0`, бумага `PaperCoated115M`, ламинации нет, режим data-value `1`.
- Строка в «Состав пакета» `todo/forms-batch-switch.md` (id копии и товар — после принятия копии): не добавлена, копии нет.

| 55 CalcFlagPaper | `flag` | /catalog/kalkulyator-flazhkov-bumazhnyh/ | COPY / PRODUCT (draft) | todo/form-flag.md |
