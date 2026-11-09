# form-pennant

Статус: заблокировано: ждёт todo/print-sheet-weight-port-fix.md
Сложность: средняя
Implementer: Grok 4.7
Reviewer: Auto
Site ops: Grok 4.7
Почему: типовая форма серии по skill `ezfc-form-to-api`, калькулятор уже на API; прод — только копия формы по шагам skill.
Чат: после закрытия `print-sheet-weight-port-fix` человек ставит `черновик` и открывает Implementer (Grok 4.7).

## Цель

Копия формы 73 CalcPennantPaper на черновике товара считает `POST /api/v1/calc/pennant`. URL копии пишется GET-именами элементов. Ссылка с этими GET открывает ту же копию с теми же значениями и той же ценой. Боевая форма 73 на странице https://insain.ru/catalog/kalkulyator-vympelov-bumazhnyh/ по-прежнему на `insaincalc.calcPennantPaper`.

## Контекст и ссылки

- `.cursor/skills/ezfc-form-to-api/SKILL.md` — порядок. Боевая форма (шаги 17–24 skill) в эту задачу не входит.
- `docs/ezfc-api-migration.md` — шаблон `cjsCalc`, GET = имя элемента, `GET_check`: dropdown с кодом — `index`, radio `1`/`2` — `value`.
- `docs/site/forms.md` — строка формы 73, только читать.
- `todo/forms-batch-switch.md` — в конце одна строка в «Состав пакета».
- `todo/EPIC-forms-to-api.md` — очередь, после `form-presswall` (закрыто 2026-11-09, `docs/history/log.md`).
- `docs/js-runner-cases.md` — команда раннера и `price` для `calcPennantPaper`.
- Эталон: `REF_PARAMS` в `calc_service/tests/test_calculators/test_pennant.py` — 50 шт., 80×120, `PaperCoated115M`, `4+0`, mode 1. Порог `price` — прогон JS против API, не число из файла. JS: `js_legacy/calc/calcPennant.js`, сигнатура `calcPennantPaper(n, size, color, materialID, options, modeProduction)`.
- Предпосылка: `todo/print-sheet-weight-port-fix.md` — вес `print_sheet` с JS; без неё `pennant.js` и дубль не делать. После `close` этой предпосылки — снова сверка эталона (в т.ч. `weight_kg`) и дефолт формы.
- Остальное не открывать.

## Scope

- Раннер готов (`js-runner-forms` закрыта 05.11.2026). Кейс и команда раннера — из `docs/js-runner-cases.md`. `calc_service/data/` и калькулятор не менять.
- JS и API сошлись — переснять эталон в `test_pennant.py` с пометкой `JS, ДД.ММ.ГГГГ`, как в `test_tablets.py`. Допуск assert — `rel=0.001`. Не сошлись — файл не трогать. Новый кейс не добавлять.
- `wp-plugin/forms/pennant.js`: id элементов боевой формы 73, `insaincalc.syncUrl`, `insaincalc.calcApi('pennant'`, `insaincalc.showResult`. Своих формул цены и чтения через DOM нет.
- Дубль формы и черновик товара — только после «да» человека. На копию — тот же JS с id копии, без `read_file`.
- GET на копии: имя параметра = имя элемента. Боевую форму не размечать.
- Прогон копии под админом: эталон, смена полей, ссылка с GET.
- После принятия копии человеком — одна строка в таблицу «Состав пакета» `todo/forms-batch-switch.md`. Ветка `task/form-pennant` от `main`.

Распределение: сверку эталона, `test_pennant.py`, `wp-plugin/forms/pennant.js` и строку в `todo/forms-batch-switch.md` делает Implementer. Дубль и черновик товара, JS и GET на копии, прогон под админом — Site ops; расхождение на копии возвращается Implementer.

## Файлы

- `wp-plugin/forms/pennant.js`
- `calc_service/tests/test_calculators/test_pennant.py`
- `todo/forms-batch-switch.md` — общий для задач эпика: одна строка в «Состав пакета»
- WordPress: только копия формы и черновик товара

## Не-scope

- `read_file` и любое переключение боевой формы 73. Выкладка плагина. `infra/deploy.sh`.
- `docs/site/forms.md`, `site/forms/73.json`.
- Правка `calc_service/calculators/pennant.py`, цен, `calc_service/data/`, `scripts/js_port_gaps_allowed.txt`, `scripts/run_js_calc.mjs`.
- Удаление копии и черновика.
- Остальные формы эпика — свои задачи.

## Критерии приёмки

Каждый пункт — команда и ожидаемый результат. `COPY` и `PRODUCT` — id копии и черновика из отчёта. В PowerShell 5.1 кавычки JSON внутри аргумента экранируются `\"`, как в skill.

- [x] Порт. В блоке `calcPennantPaper` строка `нет в Python:` пустая или каждая позиция уже есть в `scripts/js_port_gaps_allowed.txt`.

```powershell
python scripts/js_port_gaps.py calcPennantPaper
```

- [x] Раннер на входе эталона печатает `price`. Команда — из `docs/js-runner-cases.md` для `calcPennantPaper`. 404 API или расхождение — стоп, форму не дублировать. Калькулятор и `calc_service/data/` не править.

```powershell
node scripts/run_js_calc.mjs calcPennantPaper --data current --args '<args из docs/js-runner-cases.md>'
Invoke-RestMethod -Method Post -Uri https://insain.ru/api/v1/calc/pennant -ContentType 'application/json' -Body '{"quantity":50,"width_mm":80,"height_mm":120,"material_id":"PaperCoated115M","color":"4+0","mode":1}' | Select-Object price
```

- [x] `price` раннера и API: абсолютная разница ≤ 0.02 и относительная ≤ 0.001. Подставить оба числа. Stdout начинается с `ok`. JS = API = 2181.133696, abs 0, rel 0.

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

- [x] Эталон в `test_pennant.py` переснят с этого прогона: комментарий `# JS, ДД.ММ.ГГГГ` и вызов раннера рядом с эталоном, в docstring та же пометка, `price` в `EXPECTED_*` равен цене раннера, допуск assert — `rel=0.001`. Stdout: `passed`, `failed` нет. Расхождение JS и Python — стоп, файл не менять. 10.11.2026, `7 passed`.

```powershell
python -m pytest calc_service/tests/test_calculators/test_pennant.py -q
```

- [ ] Файл формы. В выводе есть `insaincalc.calcApi('pennant'`, `insaincalc.syncUrl(` и `insaincalc.showResult(`.

```powershell
Select-String -Path wp-plugin\forms\pennant.js -Pattern "calcApi\('pennant'|syncUrl\(|showResult\("
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

- [ ] На копии под админом (`https://insain.ru/?post_type=product&p=PRODUCT&preview=true`) эталон даёт `POST /api/v1/calc/pennant` → 200, в теле коды материалов, не `0`. Цена на странице равна `price` API с округлением `showResult`. В «Результат» — код ответа и обе цены.
- [ ] Смена каждого dropdown меняет цену и таблицу материалов. В таблице нет внутренних `code`. Есть вес и срок с подсказкой дат. Перезагрузка не меняет режим и срок.
- [ ] URL обновляется GET-именами формы (имя параметра = имя элемента). Ссылка с этими GET открывает копию с теми же значениями и той же ценой. У dropdown с кодом в `data-value` — `GET_check=index`. У radio со значениями `1`/`2` — `GET_check=value`.

## Проверки

- [x] `python scripts/dev.py check` — код выхода 0. calc_service 539 passed, bot_service 81 passed.
- [x] Self-review — чеклист «Перед сдачей» в [AGENTS.md](../AGENTS.md). Diff: эталон `test_pennant.py`, шапка и журнал задачи, пересборка `docs/dashboard.md`.

## Риски

- Прод: дубль и GET только с подтверждения человека. Боевая страница клиентам не меняется.
- Цены: JSON не править. Чужой `price` на проде не выравнивать. Расхождение JS и Python (локальный расчёт и боевой API, rel > 0.001) — стоп и эскалация, калькулятор не править.
- Формы: id элементов боевой формы 73 не менять. В админке пишется только копия.

## Режим

прод

## Журнал передач

Строка на сессию: `<дата> — <роль>, <модель> — <итог> — дальше <роль>`. Блокер — по формату [docs/agents/workflow.md](../docs/agents/workflow.md).

2026-11-10 — Implementer, Grok 4.7 — эталон 50 шт. 80×120 без ламинации сошёлся (price 2181.133696); дефолт формы с ламинацией раннер не считает, abs цены 0.179 > 0.02 — дальше Analyst

Блокер: дефолт боевой формы 73 нельзя сверить раннером и он не проходит допуск цены 0.02
Пробовал: `node scripts/run_js_calc.mjs calcPennantPaper --data current` и `--data legacy` с args `[100,[148,210],"4+0","PaperCoated170M",{"isLamination":"Laminat32G"},1]` — оба `Cannot read properties of undefined (reading 'Laminat')`. Боевой JS на странице формы: cost 3684.0074923076927, price 5976.162177692308, time_ready 10.63, weight 1.0144. Локальный Python и POST /api/v1/calc/pennant: cost тот же, price 5976.340906666667, time_ready 10.623333333333333, weight 0.8818. abs цены 0.1787 > 0.02, rel 2.99e-5. `insaincalc.round` обоих даёт 6000.
Гипотеза: раннер не грузит `js_legacy/material/laminat.json` и `js_legacy/calc/calcLamination.js`; правка `scripts/run_js_calc.mjs` вне scope. Цена расходится при одинаковом cost, вес JS выше и на эталоне без ламинации (0.1328 против 0.1052). Размер 80×120 и `PaperCoated115M` в dropdown формы нет (А6/А5/А4, бумага 170/200/250/300) — эталон задачи на странице не ввести.
Вопрос: стоп по abs 0.18 при одинаковом round 6000 и предпосылка на раннер (skill port-fix-prerequisite), или разрешить `pennant.js` и `REF_FORM_DEFAULT` при rel < 0.001.
Следующая сессия: Analyst

2026-11-10 — Analyst, Grok 4.7 — вес важнее допуска цены: не разрешать `pennant.js`; предпосылка `todo/print-sheet-weight-port-fix.md` (порт веса `print_sheet` с JS). Раннер/laminat — harness вне scope. Abs цены 0.18 при round 6000 — после фикса веса. — дальше Implementer предпосылки, Opus 5.5

## Найдено вне scope

- Раннер не грузит `laminat.json` / `calcLamination.js` — дефолт формы 73 с ламинацией раннером не считается; правка `scripts/run_js_calc.mjs` не в этой задаче.
- Abs `price` дефолта с ламинацией ≈ 0.18 при одинаковом `cost` и `round` 6000 — вернуться после закрытия `print-sheet-weight-port-fix`.

## Результат

- Ветка, PR или коммит: `task/form-pennant`, коммита нет
- Период: 2026-11-10
- Часы человека: не учтено
- Работа агентов: Implementer, Grok 4.7
- Было / стало: эталон в `test_pennant.py` — пометка `JS, 04.11.2026`, допуск `rel=0.03` → `JS, 10.11.2026`, команда раннера рядом с эталоном, docstring с той же пометкой, `rel=0.001`. Числа `EXPECTED_REF` те же: price раннера 2181.133696.
- Сделано: порт `calcPennantPaper` пустой; цепочка `calcPrintSheet` — пропуски уже в `scripts/js_port_gaps_allowed.txt`. Эталон без ламинации совпал с боевым API. Допуск эталона переснят.
- Чем проверено: `python scripts/js_port_gaps.py calcPennantPaper` (у `calcPennantPaper` строка `нет в Python:` пустая). Раннер `{"price":2181.133696,"time_ready":9.17,"weight_kg":0.1328}`. API `price 2181.133696`, `time_ready 9.164`, `weight_kg 0.1052`. Скрипт сверки: `ok 2181.133696 2181.133696 0.0 0.0`. `python -m pytest calc_service/tests/test_calculators/test_pennant.py -q` — `7 passed`.
- Не сделано и почему: `wp-plugin/forms/pennant.js`, `REF_FORM_DEFAULT`, строка в `todo/forms-batch-switch.md`, дубль и черновик — ждёт `print-sheet-weight-port-fix` (вес). Форму не дублировать.
- Требуется решение: нет (решено Analyst 2026-11-10).
- Строка в «Состав пакета» `todo/forms-batch-switch.md` (id копии и товар — после принятия копии): не добавлена, копия не принималась.

| 73 CalcPennantPaper | `pennant` | /catalog/kalkulyator-vympelov-bumazhnyh/ | COPY / PRODUCT (draft) | todo/form-pennant.md |
