# form-print-sheet

Статус: заблокировано: ждёт todo/print-sheet-port-fix.md
Сложность: средняя
Implementer: Grok 4.7
Reviewer: Auto
Site ops: Grok 4.7
Почему: типовая форма серии по skill `ezfc-form-to-api`, калькулятор уже на API; прод — только копия формы по шагам skill.
Чат: человек открывает новый чат с моделью из поля Implementer.

## Цель

Копия формы 6 CalcPrint на черновике товара считает `POST /api/v1/calc/print_sheet`. URL копии пишется GET-именами элементов. Ссылка с этими GET открывает ту же копию с теми же значениями и той же ценой. Боевая форма 6 на странице https://insain.ru/catalog/listovki-pod-zakaz/ по-прежнему на `insaincalc.calcPrintSheet`.

## Контекст и ссылки

- `.cursor/skills/ezfc-form-to-api/SKILL.md` — порядок. Боевая форма (шаги 17–24 skill) в эту задачу не входит.
- `docs/ezfc-api-migration.md` — шаблон `cjsCalc`, GET = имя элемента, `GET_check`: dropdown с кодом — `index`, radio `1`/`2` — `value`.
- `docs/site/forms.md` — строка формы 6, только читать.
- `todo/EPIC-forms-to-api.md` — пачка 3. Форма 19 CalcCards на том же slug — отдельная задача после принятия этой копии.
- `docs/js-runner-cases.md` — команда раннера для `calcPrintSheet`, если кейс уже есть.
- Остальное не открывать.

## Scope

- В git (Implementer): сверка по skill `verify.md` (порт `calcPrintSheet`, эталон, `REF_FORM_DEFAULT`, раннер, боевой API). `wp-plugin/forms/print_sheet.js`: id элементов боевой формы 6, `insaincalc.syncUrl`, `insaincalc.calcApi('print_sheet'`, `insaincalc.showResult`. Своих формул цены и чтения через DOM нет. Кейс дефолта — в `test_print_sheet.py` с пометкой `# JS, ДД.ММ.ГГГГ`. Команду раннера дописать одной строкой в `docs/js-runner-cases.md`; файл общий для пачки, в «Файлы» его нет. Если строку в файл не вносили — она в «Результат», вносят при слиянии.
- На проде (Site ops): дубль формы и черновик товара — только после «да» человека. На копию — тот же JS с id копии, без `read_file`. GET на копии: имя параметра = имя элемента. Боевую форму не размечать. Прогон копии под админом: эталон, смена полей, ссылка с GET.
- После принятия копии человеком строка для «Состава пакета» пишется в «Результат», не в `todo/forms-batch-switch.md`. В файл пакета её переносят при слиянии, если та задача не в статусе `в работе`.
- Ветка `task/form-print-sheet` от `main`.

## Файлы

- `wp-plugin/forms/print_sheet.js`
- `calc_service/tests/test_calculators/test_print_sheet.py`
- WordPress: только копия формы и черновик товара

## Не-scope

- `read_file` и любое переключение боевой формы 6. Выкладка плагина. `infra/deploy.sh`.
- `docs/site/forms.md`, `site/forms/6.json`, `todo/forms-batch-switch.md`.
- Правка `calc_service/calculators/print_sheet.py`, цен, `calc_service/data/`, `scripts/js_port_gaps_allowed.txt`, `scripts/run_js_calc.mjs`.
- Форма 19 CalcCards и остальные формы эпика.
- Вес: `weight_kg` с JS не сверять. Верный вес — Python (решение 11.11.2026).
- Удаление копии и черновика.

## Критерии приёмки

- [ ] `python scripts/js_port_gaps.py calcPrintSheet` — в блоке `calcPrintSheet` строка `нет в Python:` пустая или каждая позиция уже есть в `scripts/js_port_gaps_allowed.txt`.
- [ ] Раннер и `POST https://insain.ru/api/v1/calc/print_sheet` на эталоне и на дефолте формы 6: `price` abs ≤ 0.02 и rel ≤ 0.001, `time_ready` rel ≤ 0.001. Иначе стоп, форму не дублировать.
- [ ] `python -m pytest calc_service/tests/test_calculators/test_print_sheet.py calc_service/tests/test_wp_plugin_forms.py -q` — `passed`, `failed` нет. В тесте есть `REF_FORM_DEFAULT` с пометкой `# JS, ДД.ММ.ГГГГ`.
- [ ] `Select-String -Path wp-plugin\forms\print_sheet.js -Pattern "calcApi\('print_sheet'|syncUrl\(|showResult\("` — все три вхождения есть.
- [ ] Копия не на витрине: `wp post get PRODUCT --field=post_status` — `draft` или `private`; `curl.exe` без cookies на `/?post_type=product&p=PRODUCT` — `404`.
- [ ] На копии под админом эталон даёт `POST /api/v1/calc/print_sheet` → 200. Цена на странице равна `price` API с округлением `showResult`.
- [ ] URL обновляется GET-именами формы. Ссылка с этими GET открывает копию с теми же значениями и той же ценой.

## Проверки

- [ ] `python scripts/dev.py check` — код выхода 0
- [ ] Self-review — чеклист «Перед сдачей» в [AGENTS.md](../AGENTS.md)

## Риски

- Прод: дубль и GET только с подтверждения человека. Боевая страница клиентам не меняется.
- Цены: JSON не править. Расхождение JS и API (rel > 0.001) — стоп, калькулятор не править, предпосылка по skill `port-fix-prerequisite`.
- Формы: id элементов боевой формы 6 не менять. В админке пишется только копия.

## Режим

прод

## Журнал передач

Строка на сессию: `<дата> — <роль>, <модель> — <итог> — дальше <роль>`. Блокер — по формату [docs/agents/workflow.md](../docs/agents/workflow.md).

12.11.2026 — Implementer, Grok 4.7 — блокер: срок эталона print_sheet не сходится с JS — дальше Analyst

Блокер: эталон REF_PARAMS (100 шт, 210×297, PaperCoated300M, 4+4, mode 1) — `price` совпала, `time_ready` нет. Раннер 10.2, боевой API 10.183636363636364, rel 0.00161 > 0.001. Форму не дублировал, `print_sheet.py` не правил.
Пробовал: `python scripts/js_port_gaps.py calcPrintSheet` — в блоке `calcPrintSheet` только `call calcCutRoller` и `call calcPrintLaser`, обе строки есть в `scripts/js_port_gaps_allowed.txt`. Раннер `calcPrintSheet` `--args '[100,[210,297],"4+4",[0,0,0,0],0,"PaperCoated300M",{},1]'` → cost 3210.479090909091, price 5266.918472727273, time_hours 1.13, time_ready 10.2. `POST https://insain.ru/api/v1/calc/print_sheet` тем же телом → cost и price те же, time_hours 1.12, time_ready 10.183636363636364. Дефолт формы 6 (страница): 100 шт, А4 297×210, 4+0, VHI80, поля [2,2,2,2], интервал 4, без ламинации, mode 1 — раннер price 3214.3125999999997, time_ready 8.6; API price та же, time_ready 8.595, rel 0.000582; материал «Снегурочка 80гр А3», 297×420, qty 105 — совпал. Разложение на странице: `calcPrintLaser(50,[320,450],"4+4","PaperCoated300M","KMBizhubC220",1)` time 1.07, timeReady 9.07; гильотина time 0.05; сумма 1.12; `Math.ceil((1.07+0.05)*100)/100` = 1.13, потому что `(1.07+0.05)*100` = 112.00000000000001; timeReady = 1.13+9.07 = 10.2. Вложенный раннер `calcPrintLaser` на этом входе: time 1.07, timeReady 9.07, cost совпал с `PrintLaserCalculator`; у Python time_hours 1.06 (`round`, не `ceil`), price 4060 против JS 4060.9280727272735. `print_sheet` лазер не вызывает. Гильотина Python: time_hours 0.05, cost 67, price 108 — как на странице. Mode 0 на том же размере: раннер price 4864.332072727273, time_ready 25.02; боевой API cost/price/time как у mode 1 (price 5266.918472727273, time_ready 26.183636363636364), rel price 0.076.
Гипотеза: JS режет время лазерной печати `Math.ceil` до сотых (`js_legacy/calc/calcPrintLaser.js:59`) и ещё раз ceil суммы уже округлённых частей (`calcPrintSheet.js:176`), `timeReady` берёт округлённый `costPrint.timeReady` (`:177`). В `calc_service/calculators/print_sheet.py` `time_print` без округления (`:585`), ceil только у суммы (`:707`), `time_ready` от сырого `time_print` (`:712–714`). Сосед на тех же строках: JS `timePrepare*modeProduction` (`calcPrintLaser.js:19`), Python `* max(1, mode.value)` (`print_sheet.py:584`) — mode 0 совпадает с mode 1. То же `max(1, mode)` в `print_laser.py:239` и `round` вместо `ceil` на `:260`; лист этот модуль не вызывает.
Вопрос: предпосылка на эти две строки (ceil до суммы и `timePrepare * mode`) или расширить scope? Калькулятор в `form-print-sheet` править нельзя.
Следующая сессия: Analyst. Модели Analyst в шапке нет.

12.11.2026 — Analyst, Auto — заведена `todo/print-sheet-port-fix.md` на main (оба расхождения одной предпосылкой); статус ждёт её; копию формы не делал — дальше Implementer `print-sheet-port-fix`

## Найдено вне scope

- Раннер `calcCutGuillotine` на входе 50 листов, 210×297 на листе 320×450, поля [3,3,3,3], interval 0, mode 1 падает: `time_ready` не число (NaN). На странице time 0.05, Python time_hours 0.05, cost 67, price 108. Сверку листа не держит. `scripts/run_js_calc.mjs` не правил.

## Результат

- Ветка, PR или коммит: `task/form-print-sheet`; WIP-коммит статуса после Analyst.
- Сделано: сверка до перевода (шаги 0–3 и разложение срока). Порт по пропускам полный. Цена эталона и дефолта с боевым API совпала. Материалы дефолта совпали. Поля формы 6 прочитаны, id в старом `cjsCalc` (элемент 104) на те же поля. `wp-plugin/forms/print_sheet.js` не писал: стоп до совпадения срока. Analyst: предпосылка `todo/print-sheet-port-fix.md` на main.
- Чем проверено: `python scripts/js_port_gaps.py calcPrintSheet`; раннер `node scripts/run_js_calc.mjs calcPrintSheet --data current --args` на эталоне, дефолте и mode 0; `POST https://insain.ru/api/v1/calc/print_sheet` на тех же трёх телах; разложение `calcPrintLaser` / гильотина в консоли страницы https://insain.ru/catalog/listovki-pod-zakaz/ и раннер `calcPrintLaser`. `python scripts/dev.py check` не запускался: код калькулятора и формы не менялся.
- Не сделано и почему: `REF_FORM_DEFAULT`, строка в `docs/js-runner-cases.md`, `print_sheet.js`, дубль формы. Критерий срока эталона не выполнен (rel 0.00161). Ждём `print-sheet-port-fix`.
- Числа блокера: эталон mode 1 — раннер cost 3210.479090909091, price 5266.918472727273, time_hours 1.13, time_ready 10.2; API price та же, time_ready 10.183636363636364. Mode 0 — раннер price 4864.332072727273, time_ready 25.02; API price 5266.918472727273, time_ready 26.183636363636364. Дефолт формы 6 — раннер price 3214.3125999999997, time_ready 8.6; API price та же, time_ready 8.595.
- Команда раннера эталона: `node scripts/run_js_calc.mjs calcPrintSheet --data current --args '[100,[210,297],\"4+4\",[0,0,0,0],0,\"PaperCoated300M\",{},1]'`
- Команда раннера дефолта формы 6: `node scripts/run_js_calc.mjs calcPrintSheet --data current --args '[100,[297,210],\"4+0\",[2,2,2,2],4,\"VHI80\",{},1]'`
- Поля формы 6 (после починки): qty `numN` 98 = 100; формат `dpdFormat` 99 индекс 1, значение `297,210` (свой размер — значение `0`, тогда `numW` 100 и `numH` 101); цвет `dpdColor` 102 = `4+0`; материал `dpdMaterial` 103 = `VHI80`; «белые поля» `ckbMargin` 419 снят → margins `[2,2,2,2]`, interval 4, включён → margins `-1`, interval 0; ламинация `rdoLaminat` 401 = 0, при 1 код из `dpdRollLaminat` 400, при 2 из `dpdPackLaminat` 402; чекбоксы опций 661/663/666/667/664/668 сняты, `numCrease` 665 = 1, `numHole` 669 = 1; режим `rdoModeProduction` 519 = 1. Файл `fluAtrwork` 614 в API и в URL не входит. Принтера на форме нет, JS берёт `KMBizhubC220`.
- Строка в «Состав пакета» (в `todo/forms-batch-switch.md` не писать, пока та задача `в работе`): нет, копия не делалась.
- После `close` `print-sheet-port-fix`: rebase на `main`, статус `черновик`, продолжить Implementer этой задачи.
