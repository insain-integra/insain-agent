# form-pennant

Статус: ревью
Сложность: средняя
Implementer: Grok 4.7
Reviewer: Auto
Site ops: Grok 4.7
Почему: типовая форма серии по skill `ezfc-form-to-api`, калькулятор уже на API; прод — только копия формы по шагам skill.
Чат: копия 94 (черновик 2586887) принята, строка в «Состав пакета» добавлена; дальше Reviewer, Auto.

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
- Предпосылка `print-sheet-weight-port-fix`: решение 11.11.2026 — верный вес Python (изделие), к JS лист с обрезью не выравниваем. Файл `todo/print-sheet-weight-port-fix.md` ещё может лежать как leftover.
- Предпосылка `todo/pennant-materials-size-mm.md` — `size_mm` в ответе `pennant` (бумага, плёнка, шнур); без неё колонка «Размер» на копии пустая. После её закрытия и деплоя API — Site ops перепроверяет столбец на копии 94, `pennant.js` не переписывать.
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

- [x] Эталон в `test_pennant.py` переснят с этого прогона: комментарий `# JS, ДД.ММ.ГГГГ` и вызов раннера рядом с эталоном, в docstring та же пометка, `price` в `EXPECTED_*` равен цене раннера, допуск assert — `rel=0.001`. Stdout: `passed`, `failed` нет. Расхождение JS и Python — стоп, файл не менять. 11.11.2026, повтор сверки: price совпал, `weight_kg` оставлен Python.

```powershell
python -m pytest calc_service/tests/test_calculators/test_pennant.py -q
```

- [x] Файл формы. В выводе есть `insaincalc.calcApi('pennant'`, `insaincalc.syncUrl(` и `insaincalc.showResult(`. 11.11.2026: строки 21 `syncUrl(`, 42 `calcApi('pennant'`, 43 `showResult(`.

```powershell
Select-String -Path wp-plugin\forms\pennant.js -Pattern "calcApi\('pennant'|syncUrl\(|showResult\("
```

- [x] Контракт всех `forms/*.js`. Stdout: `passed`. 11.11.2026: вместе с `test_pennant.py` — `11 passed`.

```powershell
python -m pytest calc_service/tests/test_wp_plugin_forms.py -q
```

- [x] Копия не на витрине. 11.11.2026: товар 2586887 — `draft`, без cookies `404`. Форма копии 94.

```powershell
ssh insain-prod "sudo -u www-data wp post get PRODUCT --field=post_status --path=/var/www/insain.ru"
curl.exe -s -o NUL -w "%{http_code}" "https://insain.ru/?post_type=product&p=PRODUCT"
```

### Критерии перевода формы ezFC на API

- [x] На копии под админом (`https://insain.ru/?post_type=product&p=2586887&preview=true`) дефолт формы даёт `POST /api/v1/calc/pennant` → 200. Тело: PaperCoated170M, 4+0, Laminat32G, mode 1, не `0`. `price` API 5976.340906666667, на странице `showResult` 6 000 руб.
- [x] Смена каждого dropdown меняет цену и таблицу материалов. В таблице нет внутренних `code`. Вес 0.88 кг, срок «Срок 1 день», подсказка дат есть. Перезагрузка оставляет режим data-value 1 и тот же срок.
- [x] URL обновляется GET-именами формы. Ссылка с дефолтными GET открывает копию 94: А5, 4+0, 170гр, глянцевая 32 мкм, режим 1, цена 6 000 руб. У dropdown `GET_check=index`. У radio (data-value 1 и 2) `GET_check=value`: «быстрее» пишет `rdoModeProduction=2`.
- [x] После закрытия и деплоя `pennant-materials-size-mm`: на копии 94 / товаре 2586887 под админом в таблице материалов колонка «Размер» — плёнка `330,0`, бумага `320,450`, шнур `4,350` (как на боевой 73). `pennant.js` и bridge не менять. Цена дефолта по-прежнему 6 000 руб. 11.11.2026: свежая загрузка превью — бумага `320,450` / 29, плёнка `330,0` / 24.68, шнур `4,350` / 100, на странице 6 000 руб. Боевая 73 после перезагрузки — те же размеры и количества (порядок строк: плёнка, бумага, шнур), цена 6 000 руб. Внутренних `code` в таблице нет.

## Проверки

- [x] `python scripts/dev.py check` — код выхода 0. 11.11.2026: calc_service 541 passed, bot_service 81 passed.
- [x] Self-review — чеклист «Перед сдачей» в [AGENTS.md](../AGENTS.md). Diff этой сессии: одна строка в `todo/forms-batch-switch.md`, шапка, журнал и «Результат» `todo/form-pennant.md`, пересборка `docs/dashboard.md`. Калькулятор, JSON цен и `pennant.js` не менялись.

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
2026-11-11 — человек — предпосылка `print-sheet-weight-port-fix` закрыта (вес Python оставлен); статус `черновик` — дальше Implementer, Grok 4.7
2026-11-11 — Implementer, Grok 4.7 — эталон без ламинации снова сошёлся (price 2181.133696, срок rel 0.00065); дефолт с ламинацией: price abs 0.1787 > 0.02 при одинаковом cost и round 6000 — дальше Analyst

Блокер: дефолт боевой формы 73 (100 шт., А5 148×210, 4+0, PaperCoated170M, Laminat32G, mode 1) не проходит допуск цены abs ≤ 0.02
Пробовал: раннер эталона `node scripts/run_js_calc.mjs calcPennantPaper --data current --args '[50,[80,120],"4+0","PaperCoated115M",{},1]'` → price 2181.133696, time_ready 9.17, weight_kg 0.1328. Боевой API и локальный Python: price 2181.133696, time_ready 9.164, weight_kg 0.1052. Сверка price: abs 0, rel 0; срок rel 0.000655. Вес JS 0.1328 против Python 0.1052 — оставлен Python (решение 11.11.2026). Дефолт, боевой JS страницы: cost 3684.0074923076927, price 5976.162177692308, time 1.44, time_ready 10.63, weight 1.0144, round 6000. API и Python: cost тот же, price 5976.340906666667, time_ready 10.623333333333333, weight_kg 0.8818, round 6000. abs цены 0.1787 > 0.02, rel 2.99e-5; срок rel 0.000628. Порт `calcPennantPaper`: строка `нет в Python:` пустая. Поля формы 73: numN=100, dpdSize «148, 210», dpdColor «4+0», dpdMaterial PaperCoated170M, dpdCoverLaminat Laminat32G, rdoModeProduction «1». get_value_from 2938/2939/2940/2941 совпадают с этими элементами.
Гипотеза: разница цены целиком в `calcPrintSheet` с ламинацией (JS price 4058.562177692308, Python 4058.740906666667) при одинаковом cost 2499.0074923076927 и том же расходе (бумага 29 листов, плёнка 24.675 м). Без ламинации price листа совпадает, шнур совпадает. `marginPrintSheet` и `marginPennantPaper` равны 0. Раннер ламинацию не считает (harness, вне scope). Вес к JS не выравниваем.
Вопрос: разрешить `pennant.js` и `REF_FORM_DEFAULT` при rel цены < 0.001 и одном round 6000 (числа дефолта — с боевого JS, вес — Python), или предпосылка на price ламинации в `print_sheet` (abs 0.18 при одинаковом cost)?
Следующая сессия: Analyst

2026-11-11 — человек — допуск цены принят: дефолт формы 73 сверяется по rel ≤ 0.001 при одинаковом round (abs 0.18 при 6000 допустим); `pennant.js` и `REF_FORM_DEFAULT` писать (числа дефолта — с боевого JS, вес — Python) — дальше Implementer, Grok 4.7
2026-11-11 — Implementer, Grok 4.7 — `pennant.js` и `REF_FORM_DEFAULT`: дефолт формы 73, price rel 2.99e-5, round обоих 6000, вес Python 0.8818 — дальше человек

Блокер: дубль формы 73 и черновик товара — шаг с подтверждением человека
Пробовал: git-часть готова. `wp-plugin/forms/pennant.js` — id боевой формы 73 (dpdSize 2938, dpdColor 2939, dpdMaterial 2940, dpdCoverLaminat 2941, rdoModeProduction 2955, cjsCalc 2942). `REF_FORM_DEFAULT`: 100 шт., 148×210, PaperCoated170M, 4+0, Laminat32G, mode 1. Локальный Python и `POST /api/v1/calc/pennant`: cost 3684.0074923076927, price 5976.340906666667, time_hours 1.44, time_ready 10.623333333333333, weight_kg 0.8818. Боевой JS страницы: price 5976.162177692308, time_ready 10.63. rel цены 2.99e-5, rel срока 0.000628, round обоих 6000. `pytest` `test_pennant.py` и `test_wp_plugin_forms.py`: `11 passed`.
Гипотеза: без «да» Site ops копию не создаёт; боевая форма клиентам не меняется.
Вопрос: дублировать форму 73 CalcPennantPaper на черновик товара?
Следующая сессия: человек; после «да» — Site ops, модель Grok 4.7

2026-11-11 — Site ops, Grok 4.7 — человек сказал «да» (2026-11-11) на дубль формы 73 и черновик; копия 94, черновик 2586887, POST 200, price 5976.340906666667, на странице 6000, срок как у формы 73 — дальше человек (приёмка копии), затем Reviewer, Auto
2026-11-11 — Implementer, Grok 4.7 — замечание человека «На форму материалов не передаются размеры»: колонка «Размер» пустая, ответ `pennant` без `size_mm`; `pennant.js` и bridge не виноваты — дальше Analyst, Grok 4.7

Блокер: колонка «Размер» таблицы материалов на копии пустая; чтобы её заполнить, нужна правка калькулятора — это вне scope
Пробовал: боевая страница, `insaincalc.calcPennantPaper(100,[148,210],"4+0","PaperCoated170M", isLamination Laminat32G, 1)` и `showMaterials` — плёнка `330,0` / 24.68, бумага `320,450` / 29, шнур `4,350` / 100. `POST https://insain.ru/api/v1/calc/pennant` с тем же дефолтом: те же три строки и те же количества (29 / 24.675 / 100), ключа `size_mm` нет ни у одной. Локальный `PrintSheetCalculator` на этих параметрах отдаёт у бумаги `size_mm` `[320, 450]`, у плёнки размера нет. `pennant.py` при сборке `materials_out` копирует `code`/`name`/`title`/`quantity`/`unit` и `size_mm` бумаги выбрасывает. `lamination.py` и `calc_set_rope` (`process_tools.py`) `size_mm` не ставят: в каталоге у плёнки дефолт `[330, 0]`, у шнура `[4, 350]`. `pennant.js` передаёт размер изделия `width_mm` 148 и `height_mm` 210; Site ops уже видел это тело и цену 6 000. `showResult` берёт размер только из `materials[].size_mm` (`materialSize` в `insain-calc-bridge.js`). Превью копии без входа админа — 404. SSH не вызывался. Код не менялся.
Гипотеза: пустая ячейка на копии — не маппинг полей формы. Bridge уже кладёт `size_mm` во второй столбец; API его не присылает. Подставить размеры в `pennant.js` значило бы захардкодить каталог.
Вопрос: расширить scope этой задачи на `size_mm` в ответе `pennant` (бумага уже есть в `print_sheet`, плёнка и шнур — в `lamination` и `calc_set_rope`) или завести предпосылку и вернуть форму к Implementer после неё?
Следующая сессия: Analyst, модель Grok 4.7

2026-11-11 — человек — scope не расширять: завести задачу-предпосылку на `size_mm` в ответе `pennant` (бумага, плёнка, шнур); form-pennant ждёт её закрытия, затем Site ops перепроверяет столбец «Размер» на копии 94 — дальше Analyst (написать предпосылку)
2026-11-11 — Analyst, Grok 4.7 — заведена `todo/pennant-materials-size-mm.md` (прокидка `size_mm` в `pennant` + общие `lamination` / `calc_set_rope`, деплой API); статус `заблокировано: ждёт todo/pennant-materials-size-mm.md`. После закрытия предпосылки — Site ops перепроверяет столбец «Размер» на копии 94 (`pennant.js` не переписывать), затем приёмка человеком и Reviewer, Auto — дальше Implementer предпосылки, Grok 4.7
2026-11-11 — человек — предпосылка `pennant-materials-size-mm` закрыта (API `6a9e14b` на проде, `size_mm` бумаги, плёнки и шнура в ответе); ветка перенесена на `main`; статус `черновик` — дальше Site ops, Grok 4.7: перепроверить столбец «Размер» на копии 94
2026-11-11 — Site ops, Grok 4.7 — на копии 94 колонка «Размер» заполнена и совпадает с формой 73 (плёнка 330,0; бумага 320,450; шнур 4,350), цена дефолта 6 000 руб.; `pennant.js` не менялся — дальше человек (приёмка копии), затем Reviewer, Auto
2026-11-11 — человек — копия 94 (черновик 2586887) принята — дальше Implementer, Grok 4.7: строка в «Состав пакета» `todo/forms-batch-switch.md`, затем Reviewer, Auto
2026-11-11 — Implementer, Grok 4.7 — строка в «Состав пакета»: 73 CalcPennantPaper, копия 94 / черновик 2586887; предпосылки print-sheet-weight-port-fix и pennant-materials-size-mm закрыты — дальше Reviewer, Auto

## Найдено вне scope

- Раннер не грузит `laminat.json` / `calcLamination.js` — дефолт формы 73 с ламинацией раннером не считается; правка `scripts/run_js_calc.mjs` не в этой задаче.
- Колонка «Размер» таблицы материалов закрывается предпосылкой `pennant-materials-size-mm`, не расширением scope этой задачи.
- Порядок строк на копии (бумага, плёнка, шнур) отличается от боевой 73 (плёнка, бумага, шнур). Размеры и количества те же: `showResult` выводит `materials` в порядке ответа API. Боевую форму и JS не менял.
- `todo/print-sheet-weight-port-fix.md` всё ещё в репозитории со статусом `черновик` при решении «вес Python» — leftover для человека (`close` или удаление).

## Результат

- Ветка, PR или коммит: `task/form-pennant`, коммиты `a95ece5`, `c14d415`. Эта сессия: строка в `todo/forms-batch-switch.md`, шапка, журнал и «Результат» `todo/form-pennant.md`; `docs/dashboard.md` пересобирает `make check`. Прод и `pennant.js` не менялись. В git не закоммичено.
- Период: 2026-11-10 — 2026-11-11
- Часы человека: не учтено
- Работа агентов: Implementer, Grok 4.7; Site ops, Grok 4.7 (дубль 11.11 и перепроверка «Размер» 11.11). Предпосылки закрыты: `print-sheet-weight-port-fix` (журнал 2026-11-11, вес Python оставлен), `pennant-materials-size-mm` (журнал 2026-11-11, API `6a9e14b`).
- Было / стало: файла `wp-plugin/forms/pennant.js` не было → custom JS боевой формы 73 (`calcApi('pennant')`, `syncUrl`, `showResult`). На проде форма 73 без копии → копия 94 `CalcPennantPaper duplicate` на черновике товара 2586887, JS копии через `calcApi`, GET проставлен. Боевая форма 73 по-прежнему на `calcPennantPaper`. На свежей загрузке копии колонка «Размер» заполнена: плёнка `330,0`, бумага `320,450`, шнур `4,350`. Строки пакета для формы 73 не было → строка копии 94 / черновика 2586887 в «Состав пакета».
- Сделано: человек сказал «да» (2026-11-11) на дубль формы 73 и черновик; 2026-11-11 копию 94 (черновик 2586887) принял. Копия 94 (одна новая строка после 93). Черновик 2586887 «Калькулятор вымпелов бумажных (Копировать)», `ezfc_form_id` 94, `post_status` draft. Гость: HTTP 404. JS и GET записаны в копию (бэкап `/tmp/ezfc-copy-94-20261110-175751.json`). Боевая форма не размечалась и не переключалась: у элементов 73 имя GET пустое, у режима `GET_check` по-прежнему `index`, в расчёте есть `calcPennantPaper` и нет `calcApi`. Плагин не выкладывался. 11.11.2026 перепроверка после API `6a9e14b`: на копии 94 столбец «Размер» заполнен и совпадает с боевой 73, цена дефолта 6 000 руб. `pennant.js` не переписывался. Строка в «Состав пакета» `todo/forms-batch-switch.md` добавлена.
- Чем проверено: `wp post get 2586887 --field=post_status` → `draft`. `curl` без cookies на `?post_type=product&p=2586887` → `404`. Превью под админом: `POST /api/v1/calc/pennant` 200, тело `quantity 100, 148×210, PaperCoated170M, 4+0, Laminat32G, mode 1`. `price` API 5976.340906666667, на странице 6 000 руб. и 60 руб./шт. Срок «Срок 1 день», подсказка «Готовность заказа: 12.11.26, 15:00 При запуске заказа в работу до: 11.11.26, 11:00» — тот же текст, что на боевой странице. Вес на копии 0.88 кг (Python); на боевой странице старый JS показывает 1.01 кг — так и решено 11.11.2026. Строка «со скидкой» на копии 4 790 руб., на боевой 4 789 руб.; менеджерская цена обоих 6 000. В таблице материалов имена, без `PaperCoated170M` / `Laminat32G` / `RopeForPack`. Смена размера, цветности, бумаги и ламинации меняет цену (6 000 → 4 800 → 5 200 → 5 300 → 4 200) и строки таблицы; «быстрее» даёт 4 900 руб., «Срок 4 часа» и `rdoModeProduction=2`. Ссылка с дефолтными GET возвращает А5, 4+0, 170гр, глянцевую 32 мкм, режим 1 и 6 000 руб. Повторная загрузка режим и срок не меняет. `wp cache flush` — Success. `wp litespeed-purge all` — `Error: Something went wrong! Got 400`; превью всё равно отдало новый JS.
- Чем проверено (11.11.2026, столбец «Размер»): свежая загрузка превью копии 94 под админом — таблица «бумага 320,450 / 29; плёнка 330,0 / 24.68; шнур 4,350 / 100», на странице 6 000 руб., внутренних `code` нет. `POST /api/v1/calc/pennant` дефолта: `price` 5976.340906666667, `size_mm` бумага `[320, 450]`, плёнка `[330, 0]`, шнур `[4, 350]`. Боевая 73 после перезагрузки публичной страницы: те же размеры и количества, цена 6 000 руб., в HTML есть `calcPennantPaper` и нет `calcApi`. Смена на копии: А6 — те же размеры, кол-во 15 / 12.84 / 100, цена 4 800; бумага 300гр — имя 300г, размеры те же, цена 5 000, тело `PaperCoated300M`; ламинация «нет» — строки плёнки нет, бумага 320,450 / 14, шнур 4,350, цена 3 900; матовая 32 мкм — плёнка MATT `330,0`, цена 5 600, в таблице нет `Laminat32M`; А4 — те же размеры, кол-во 56 / 49.35 / 100, цена 11 600. Числа размера у этих пунктов каталога одни (лист 320×450, рулон 330×0, шнур 4×350); обновляются имя, количество и наличие строки плёнки, ячейка «Размер» каждый раз берётся из `size_mm`. Уже открытая вкладка со старым расчётом (ламинация «нет», 4 200) до перезагрузки показывала пустой «Размер»; после загрузки URL приёмки столбец заполнился. SSH не вызывался. Сброс кэша не нужен: новый расчёт ходит в API. Консоль: только JQMIGRATE, ошибок `insaincalc` / `ezfc` нет.
- Не сделано и почему: выкладка плагина и переключение боевой формы 73 — не эта задача. Удаление копии и черновика — не-scope. Кейс дефолта в `docs/js-runner-cases.md` не добавлялся: раннер ламинацию не считает. `pennant.js` не менялся: размер пришёл из API. Файл `todo/print-sheet-weight-port-fix.md` со статусом `черновик` оставлен: предпосылка закрыта в журнале, удаление leftover — человеку.
- Как откатить: эта сессия прод не меняла, откат не нужен. Элементы копии — из бэкапа `/tmp/ezfc-copy-94-20261110-175751.json` тем же `ezfc_copy_apply.php`. Черновик 2586887 гостям не виден. Удалять форму 94 и товар только с отдельным «да». Боевую форму откатывать не нужно: она не менялась.
- Требуется решение: нет. Копия 94 (черновик 2586887) принята человеком 2026-11-11. Дальше Reviewer, Auto.
- Строка в «Состав пакета» `todo/forms-batch-switch.md` записана после приёмки:

| 73 CalcPennantPaper | `pennant` | `/catalog/kalkulyator-vympelov-bumazhnyh/` | 94 / 2586887 (draft) | todo/form-pennant.md |

- Превью: https://insain.ru/?post_type=product&p=2586887&preview=true&numN=100&dpdSize=1&dpdColor=0&dpdMaterial=0&dpdCoverLaminat=1&rdoModeProduction=1
