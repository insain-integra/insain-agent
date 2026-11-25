# form-magnet-laminated

Статус: закрытие
Сложность: низкая
Implementer: Grok 4.7
Reviewer: не нужен
Site ops: Grok 4.7
Почему: лид-копия slug `magnet_laminated` по skill `ezfc-form-to-api`; общий `magnets.py` с `form-magnet-acrylic`, в allowed три пропуска `calcMagnetLamination`.

## Цель

Копия формы 54 CalcMagnetLamination на черновике товара считает `POST /api/v1/calc/magnet_laminated`. URL копии пишется GET-именами элементов. Ссылка с этими GET открывает ту же копию с теми же значениями и той же ценой. Боевая страница https://insain.ru/catalog/kulkulyator-magnitov-vinilovyh/ остаётся на `insaincalc.calcMagnetLamination`. Боевое переключение отложено решением человека 22.11.2026. Вторая форма slug — 57 CalcMagnetPoly — отдельной задачей после приёмки этой копии.

## Контекст и ссылки

- `.cursor/skills/ezfc-form-to-api/SKILL.md`, этапы `verify.md` и `copy.md`. Шаги 17–24 не входят.
- `docs/ezfc-api-migration.md` — GET = имя элемента.
- `docs/site/forms.md` — строка формы 54, только читать.
- `calc_service/calculators/magnets.py` — только `MagnetLaminatedCalculator` и его функции; `calc_service/tests/test_calculators/test_magnets.py`.
- `js_legacy/calc/calcMagnets.js`, функция `calcMagnetLamination` — эталон дефолта формы.
- `scripts/js_port_gaps_allowed.txt` — строки `calcMagnetLamination option isLamination`, `isBarcode`, `isVariables`.
- `todo/EPIC-forms-to-api.md` — пачка 7.
- Остальное не открывать.

## Scope

- В git (Implementer): шаги 0–5б и `wp-plugin/forms/magnet_laminated.js`. `REF_FORM_DEFAULT` для `magnet_laminated` в `test_magnets.py` с пометкой `# JS, ДД.ММ.ГГГГ`. `calcMagnets.js` в `scripts/run_js_calc.mjs` не подключён — эталон прямым прогоном файла в Node vm, раннер не править.
- Пропуск `isLamination` оставить в docstring и в allowed. `isBarcode` и `isVariables` снять из allowed, когда ветка портирована. `isNumber` тоже портировать: детектор считает его перенесённым из-за слова `number`, в расчёте его нет. Новые строки в allowed не добавлять. Калькулятор не на боевой форме API, предпосылку не заводить.
- Доработка 26.11.2026 (важнее абзаца выше про «только дефолт»): нумерация, штрихкод и переменные данные на копии меняют цену и срок как `calcMagnetLamination`. Снятые галочки не двигают `REF_FORM_DEFAULT_LAMINATED`. Суммы не выдумывать и в новый JSON не заводить: те же величины, что уже стоят в `print_sheet.py` и в JS (на тираж `n_items`, затем та же наценка, что у остальной цены). `wp-plugin/forms/magnet_laminated.js` передаёт три флага в `calcApi`; `syncUrl` остаётся.
- Ветку `magnet_acrylic` и её эталоны не менять.
- На проде (Site ops): дубль формы 54 на черновик после совпадения дефолта с боевым API. Если порт менял ответ — сначала `deploy-api` с `main`, потом дубль. JS копии в элементе (`read_file=0`). Плагин не выкладывать. Боевую 54 не переключать.
- Строка для будущего боевого пакета и дописка для `docs/js-runner-cases.md` — в «Результат», не в общие файлы. Что не сходится на дефолте формы 57 — одна строка в «Результат».

## Файлы

- `wp-plugin/forms/magnet_laminated.js`
- `calc_service/calculators/magnets.py`
- `calc_service/tests/test_calculators/test_magnets.py`
- `scripts/js_port_gaps_allowed.txt` — только снять строки `calcMagnetLamination`, если ветка портирована
- WordPress: только копия формы 54 и её черновик

## Не-scope

- `todo/forms-batch-switch.md`, `docs/site/forms.md`, `docs/js-runner-cases.md`, `scripts/run_js_calc.mjs`
- Копия формы 57 и боевые формы 54 и 57, шаги 17–24, выкладка плагина, JSON цен, `calc_service/calculators/__init__.py`
- Ветка `magnet_acrylic` в `magnets.py`. Новые строки в allowed. Чужие калькуляторы.

## Критерии приёмки

Каждый пункт — команда и ожидаемый результат.
Скрипт через `@'…'@ | python -` в PowerShell 5.1 — первой строкой `$OutputEncoding = New-Object System.Text.UTF8Encoding $false`, иначе кириллица в нём станет `?`.

- [x] `python scripts/js_port_gaps.py calcMagnetLamination` — `isBarcode` и `isVariables` сняты из allowed, `isNumber` есть в расчёте, а не только в docstring. `isLamination` остаётся в allowed. `python scripts/js_port_gaps.py --check` печатает `ok`.
- [x] `python -m pytest calc_service/tests/test_calculators/test_magnets.py calc_service/tests/test_wp_plugin_forms.py -q` — `passed`. Дефолт без трёх галочек не сдвинулся. Отдельные эталоны `# JS,` на нумерацию, штрихкод, переменные данные и на все три вместе. Эталоны `magnet_acrylic` не сдвинулись.
- [ ] Боевой `POST /api/v1/calc/magnet_laminated` на теле `REF_FORM_DEFAULT`: `price` и `time_ready` как у JS (допуск цены abs ≤ 0.02 или rel ≤ 0.001, срока rel ≤ 0.001). То же для каждой опции и для трёх вместе. Если порт ещё не выкачен — пункт после `deploy-api`, копию до него не принимать.
- [x] `Select-String -Path wp-plugin\forms\magnet_laminated.js -Pattern "calcApi\('magnet_laminated'|syncUrl\(|showResult\("` — все три есть. Три флага уходят в объект `calcApi`, не только в `syncUrl`. Своей `price` и `querySelector` нет.
- [x] Копия не на витрине: `wp post get <product> --field=post_status` → `draft` или `private`; `curl.exe -s -o NUL -w "%{http_code}"` гостем — не `200`.
- [ ] На копии под админом включённая нумерация, штрихкод и переменные данные дают цену страницы = `price` API с округлением `showResult`. Дефолт со снятыми галочками остаётся 2 900 руб. Дефолт проверен 26.11.2026 (2 900 руб., «Срок 1 день», POST 200, `price` 2827.85, три флага `false`). Цены включённых галочек — после `deploy-api`: боевой API этих опций ещё не знает.
- [x] `curl.exe -s https://insain.ru/catalog/kulkulyator-magnitov-vinilovyh/` — в HTML есть `calcMagnetLamination`, нет `calcApi`.

### Критерии перевода формы ezFC на API

- [x] URL обновляется GET-именами формы; ссылка с GET открывает форму с теми же значениями и той же ценой.

## Проверки

- [x] `make check` (или `python scripts/dev.py check`) — зелёный вывод
- [x] Self-review — чеклист «Перед сдачей» в [AGENTS.md](../AGENTS.md)

## Риски

- Прод: боевые формы 54 и 57 не меняются. Выкатка API — только если менялся калькулятор, с `main`. Запись в формы не параллельно с `todo/ezfc-options-source-reset.md`.
- Цены: JSON не менять.
- Формы: id боевой 54 не менять; копия — новая форма на черновике.
- Общий файл `magnets.py` с `form-magnet-acrylic` (закрыто 2026-11-24, `docs/history/log.md`): начинать только после её закрытия и слияния в `main`.

## Режим

прод

## Журнал передач

Строка на сессию: `<дата> — <роль>, <модель> — <итог> — дальше <роль>`. Блокер — по формату
[docs/agents/workflow.md](../docs/agents/workflow.md). Замечания ревью — ниже, в «Ревью N».

22.11.2026 — человек — завести 8 лид-копий, боевые формы не переключать, форма 68 через tablets — дальше ожидание закрытия `form-magnet-acrylic` (закрыто 2026-11-24, `docs/history/log.md`), затем Implementer

25.11.2026 — Implementer, Grok 4.7 — дефолт формы 54 сходится с JS, `forms/magnet_laminated.js` и эталон в тесте, `make check` зелёный — дальше Site ops
25.11.2026 — человек — продолжить несмотря на два незакоммиченных файла на main (были до задачи) — дальше Site ops
25.11.2026 — Site ops, Grok 4.7 — дубль не создан: админка ezFC открыла `wp-login.php` — дальше человек
25.11.2026 — человек — войти в wp-admin в Chrome Browser MCP и продолжить дубль формы 54 с шага 6, боевую не трогать — дальше Site ops
25.11.2026 — Site ops, Grok 4.7 — дубль принят: форма 119 на черновике 2586915, дефолт на странице 2 900 руб. при API 2827.85, боевая 54 на старом JS — дальше человек, приёмка
25.11.2026 — человек — принято: слить в main, закрыть задачу и запушить; боевую 54 не переключать, плагин не выкладывать — дальше finish-task
25.11.2026 — человек — включить в коммит lamination.py, print_sheet.py и строку slug — дальше finish-task
26.11.2026 — человек — доработка: на копии не работают нумерация, штрихкод и переменные данные — дальше Implementer
26.11.2026 — Implementer, Grok 4.7 — нумерация, штрихкод и переменные данные в калькуляторе и в calcApi, дефолт без галочек прежний, `make check` зелёный — дальше Site ops
26.11.2026 — Site ops, Grok 4.7 — новый JS с `is_number`, `is_barcode`, `is_variables` записан в элемент 4333 копии 119 (`read_file=0`), дефолт на странице «2 900 руб.» и «Срок 1 день», POST 200 `price` 2827.85, боевая 54 не менялась — дальше человек, приёмка
26.11.2026 — человек — принято: слить в main, закрыть, запушить и выкатить API; боевую 54 и плагин не трогать — дальше finish-task

## Ревью 1

26.11.2026 — человек

- блокер: галочки нумерации (`ckbNumber`), штрихкода (`ckbBarcode`) и переменных данных (`ckbVariables`) на копии формы 119 не меняют цену. В `magnet_laminated.js` они пишутся только в `syncUrl` и в `calcApi` не уходят. В `MagnetLaminatedCalculator` этих опций нет.
- Эталон — `calcMagnetLamination` в `js_legacy/calc/calcMagnets.js`, блок «дополнительные опции». Надбавки до общей наценки, на `n_items` (без эпоксидки это тираж): нумерация cost 0.75 / price 1 / time 0.05; штрихкод 1 / 2 / 0.1; переменные данные 3 / 5 / 0.1. Каждая галочка отдельно и все три вместе сходятся с JS (допуск цены и срока из критериев задачи). Все три сняты — прежний дефолт.
- Числа не выдумывать. Отдельный JSON не заводить: те же константы уже в `print_sheet.py`. Ветку `magnet_acrylic`, `isLamination` и чужие калькуляторы не менять.
- После сдачи кода Site ops записывает новый JS в элемент копии 119 (`read_file=0`). Плагин не выкладывать. Боевую 54 не переключать. Пока ветки нет в `main`, выкатку API не делать: копия бьёт в боевой API, новые цены опций на странице принимать только после `deploy-api`.

Варианты для человека:
1. Принять копию и закрыть задачу через finish-task: коммит ветки `task/form-magnet-laminated`, слияние в `main`, push. Боевую форму 54 не переключать, плагин не выкладывать. Lock prod снимет finish-task. (Рекомендуется)
2. Копию не закрывать: черновик 2586915 и форма 119 остаются, в чат — что поправить. Lock prod остаётся у `form-magnet-laminated`.
3. Удалить дубль (форма 119 и черновик 2586915) и вернуть статус `заблокировано: человек`. Боевую 54 и товар 2586724 не трогать. Удаление только после этого выбора.

Эти три варианта закрыты доработкой 26.11.2026. Актуальная приёмка — в «Результат», «Требуется решение».

## Найдено вне scope

- Сложность на форме 54 и 57: 1 / 1.5 / 2, в enum схемы 1 / 1.3 / 1.7. `calculate()` число формы принимает. Прямоугольный дефолт сложность не использует.
- Консоль превью копии: `insainParse/scrtp.js` — `TypeError` на `options` и `querySelector`; `admin-ajax.php?action=woocommerce_load_status_widget` — 504. Ошибок `insaincalc` и `ezfc` нет. Форму не трогал.
- Скругление при форме не `rectangular` JS добавляет к вырубке, API умеет его только как `rectangular_rounded` (сабельный рез). В JS копии так только для прямоугольника.

## Результат

- Ветка, PR или коммит: `task/form-magnet-laminated`, коммита нет
- Период: 2026-11-25 — 2026-11-26
- Часы человека: оценка 2 ч — 1 ч на коммит задачи | факт 3 сессии
- Работа агентов: 2 сессии Implementer; 3 сессии Site ops; Grok 4.7
- Было / стало: на копии 119 галочки нумерации, штрихкода и переменных данных цену не меняли; опции есть в калькуляторе и в JS элемента 4333. Боевая форма 54 на старом JS.
- Сделано: шаги 0–5б. Пропуск `isLamination` оставлен в docstring и allowed. `isBarcode` и `isVariables` сняты из allowed 26.11.2026: нумерация (`is_number`), штрихкод (`is_barcode`) и переменные данные (`is_variables`) считаются в `calc_laminated_magnets` на `n_items` до общей наценки. Величины — константы `_OPTION_*` из `print_sheet.py`, не новый JSON. Ветка `magnet_acrylic` не менялась. Срок дефолта на mode 0 и 2 совпал с JS за счёт сырого времени ламинации в сумме печати (`js_time_sum` только из `calc_laminated_magnets`). `wp-plugin/forms/magnet_laminated.js` передаёт три флага в объект `calcApi` и оставляет их в `syncUrl`. `REF_FORM_DEFAULT_LAMINATED` в `test_magnets.py` не сдвинут. Эталоны `# JS, 26.11.2026` на каждую галочку и на все три вместе.
- Пустой код `dpdLaminat` («нет») в запрос не кладётся; пустой `lamination_id` API по-прежнему заменяет на Laminat32G.
- Id `get_value_from` старого JS совпали с элементами 54. Чужих id нет.
- Чем проверено 26.11.2026:
  - Node vm, прайс `calc_service/data`, `calcMagnetLamination(100,[50,50],"rectangular",1,"MagnetVinil04", Map isLamination=Laminat32G + галочка, mode 1)`: дефолт `price` 2827.85 / `time_ready` 9.16; нумерация 2942.85 / 9.21; штрихкод 3057.85 / 9.26; переменные данные 3402.85 / 9.26; все три 3747.85 / 9.41. Себестоимость: 1525 / 1600 / 1625 / 1825 / 2000.
  - `python scripts/js_port_gaps.py calcMagnetLamination` — у `calcMagnetLamination` в «нет в Python» только `option isLamination`. `isNumber` есть в расчёте (`is_number`), не только в docstring.
  - `python scripts/js_port_gaps.py --check` — `ok`.
  - `python -m pytest calc_service/tests/test_calculators/test_magnets.py calc_service/tests/test_wp_plugin_forms.py -q` — `58 passed`. Эталоны `magnet_acrylic` не сдвинулись. Дефолт без галочек: `price` 2827.85, `time_ready` 9.16.
  - `python scripts/dev.py check` — `856 passed`, затем `81 passed`, код выхода 0. `docs/dashboard.md` скрипт пересобрал и сдвинул чужую строку; файл возвращён к версии ветки, в diff задачи его нет.
  - `Select-String` по `wp-plugin/forms/magnet_laminated.js` — есть `calcApi('magnet_laminated'`, `syncUrl(`, `showResult(`, `is_number: isNumber`, `is_barcode: isBarcode`, `is_variables: isVariables`. `querySelector` нет.
- Чем проверено 25.11.2026:
  - `python scripts/js_port_gaps.py calcMagnetLamination` — у `calcMagnetLamination` в «нет в Python» только `option isLamination`, `option isBarcode`, `option isVariables`.
  - `python scripts/js_port_gaps.py --check` — `ok`.
  - `python -m pytest calc_service/tests/test_calculators/test_magnets.py calc_service/tests/test_wp_plugin_forms.py calc_service/tests/test_calculators/test_print_sheet.py calc_service/tests/test_calculators/test_lamination.py -q` — `97 passed`. Эталоны `magnet_acrylic` не сдвинулись.
  - `python scripts/dev.py check` — `850 passed`, затем `81 passed`, код выхода 0.
  - Боевой POST `REF_FORM_DEFAULT_LAMINATED`: mode 1 `price` 2827.85, `time_ready` 9.16 (как JS). mode 0 `time_ready` 24.55 при JS 24.54 (rel < 0.001). mode 2 `time_ready` 2.78 при JS 2.8 — в ветке уже 2.8, на проде до выкатки старое значение. Материалы mode 1: винил 0.44 / 620×0, RAFLACOAT 5 / 320×450, Laminat32G 3.384 / 330×0 — как Node vm.
  - `curl.exe -s https://insain.ru/catalog/kulkulyator-magnitov-vinilovyh/` — в HTML есть `calcMagnetLamination`, нет `calcApi`.
  - `Select-String` по `wp-plugin/forms/magnet_laminated.js` — есть `calcApi('magnet_laminated'`, `syncUrl(`, `showResult(`; нет `querySelector` и присваивания `price`.
- Сделано на проде (шаги 6–16): один Duplicate формы 54 → форма 119. Черновик товара 2586915 «Калькулятор магнитов виниловых (Копировать)», `ezfc_form_id` 119. JS копии записан `ezfc_copy_apply.php` (`read_file=0`, `calcApi=1`), GET на полях `syncUrl`. У `rdoModeProduction` копии `GET_check=value`, `preselect` с 0 на 1: при `GET_check=value` ноль не выбирает опцию «стандарт» (её value 1), чистая страница считала mode 0. После правки дефолт — mode 1. Бэкап JS: `/tmp/ezfc-copy-119-20261124-201809.json`.
- Не сделано и почему: выкатка API не делалась — ветки нет в `main`, копия бьёт в боевой API. Включённые галочки цену страницы не меняют, пока порт не выкачен; это не провал записи, галочки не крутил и не откатывал. Шаги 17–24 и выкладка плагина не входят. Коммит, push, merge, close не делались. Lock prod не снимался. Боевой POST опций не сверялся: порт ещё не на проде. Mode 2 на боевом API по-прежнему может быть `time_ready` 2.78 при JS 2.8 — выкатка не делалась.
- Сделано на проде 26.11.2026: админка открылась (не `wp-login.php`). `ezfc_copy.py` + `ezfc_copy_apply.php` перезаписали JS элемента 4333 (`cjsCalc` копии 119). Показ без записи: менялся только `custom_calculation` (3851 → 3678 байт, `calcApi=1`), `read_file` `'0' = '0'`, GET без изменений. Запись: `бэкап: /tmp/ezfc-copy-119-20261125-181220.json`, `записано` у элементов копии. Боевая 54 и товар 2586724 не менялись.
- Форма 57, дефолт (эпоксид всегда, без ламинации, 100 шт, 50×50, прямоугольник, MagnetVinil04, mode 1): JS `price` 12628.15 и `time_ready` 45.14, текущий API 12214.15 и 44.84 (цена rel ≈ 0.033). Не чинил — вторая форма, отдельная задача.
- Строка для будущего боевого пакета: форма 54 `magnet_laminated`, файл `wp-plugin/forms/magnet_laminated.js`, id боевого `cjsCalc` 2234; переключение боевой только пакетом, копия отдельно.
- Дописка для `docs/js-runner-cases.md`: кейс `calcMagnetLamination` в `run_js_calc.mjs` не подключён (25.11.2026), `calcMagnets.js` в раннер не входит. Дефолт формы 54 снят Node vm на прайсе `calc_service/data`: `calcMagnetLamination(100,[50,50],"rectangular",1,"MagnetVinil04", Map isLamination=Laminat32G, mode)` → mode 1 price 2827.85 / time_ready 9.16; mode 0 — 1791.7 / 24.54; mode 2 — 3984.75 / 2.8. Опции mode 1 (26.11.2026): нумерация 2942.85 / 9.21; штрихкод 3057.85 / 9.26; переменные данные 3402.85 / 9.26; все три 3747.85 / 9.41.
- Требуется решение человека. Варианты:
  1. Принять и закрыть через finish-task: коммит ветки `task/form-magnet-laminated`, слияние в `main`, push, затем выкатка API (`deploy-api`), чтобы галочки нумерации, штрихкода и переменных данных на копии начали менять цену. Боевую форму 54 не переключать, плагин не выкладывать. (Рекомендуется)
  2. Принять без выкатки: finish-task сливает в `main` и пушит, API не выкатывать. Галочки на копии цену не изменят. Боевую 54 не переключать, плагин не выкладывать.
  3. Доработка: не сливать. Форма 119 и черновик 2586915 остаются, lock prod остаётся у `form-magnet-laminated`. В чат — что поправить.
- Откат этой записи JS: строки из `/tmp/ezfc-copy-119-20261125-181220.json` (JS копии до 26.11.2026). Более ранний бэкап первого перевода — `/tmp/ezfc-copy-119-20261124-201809.json`. `preselect` элемента 4346 не менялся (остаётся 1, `GET_check=value`). Удаление формы 119 и черновика 2586915 — только по выбору человека. Боевая форма 54 и товар 2586724 не менялись.
- Site ops 26.11.2026, чем проверено:
  - `python scripts/dev.py lock status` — `prod` занят `form-magnet-laminated` (с 2026-11-25T18:10:02Z). `acquire` и `release` не вызывались.
  - Админка `https://insain.ru/wp-admin/` — «Консоль», не `wp-login.php`.
  - SQL карты 54 → 119: `cjsCalc` 2234/4333, `ckbNumber` 2228/4329, `ckbBarcode` 2229/4330, `ckbVariables` 2230/4331, `rdoModeProduction` 2247/4346. Пустых `id_copy` нет.
  - После записи SQL элемента 4333: `read_file=0`; `is_number: isNumber` на позиции 2682, `is_barcode: isBarcode` 2707, `is_variables: isVariables` 2734, `insaincalc.calcApi(` 3213 (флаги внутри `var params`, до вызова). `calcMagnetLamination` в элементе копии нет. Элемент 2234 боевой: `read_file=0`, трёх флагов и `calcApi` нет, `calcMagnetLamination` есть.
  - Товары: 2586915 `draft`, мета `119`; 2586724 `publish`, мета `54`. Гость `curl.exe -s -o NUL -w "%{http_code}" "https://insain.ru/?post_type=product&p=2586915"` — `404`.
  - `wp cache flush` — `Success`. `wp litespeed-purge all` — `Got 400` (дважды). Превью под админом всё равно выполнило новый JS.
  - Превью `/?post_type=product&p=2586915&preview=true`: URL дописал `numN=100&numW=50&numH=50&dpdShape=0&dpdDifficulty=0&dpdMaterial=0&dpdLaminat=1&rdoModeProduction=1`, параметров галочек нет. `POST /api/v1/calc/magnet_laminated` 200, тело с `is_number:false`, `is_barcode:false`, `is_variables:false`, `mode:1`, `Laminat32G`. Ответ `price` 2827.85, `time_ready` 9.16. На странице «2 900 руб.», «Срок 1 день». Галочки не включал.
  - `curl.exe -s -D -` боевой страницы — HTTP 200, 334747 байт. В файле `calcMagnetLamination` 1 раз, `calcApi` 0. В совпадении — `insaincalc.calcMagnetLamination(ezfc_functions.get_value_from(2222),...)`.
- Site ops 25.11.2026, чем проверено:
  - `python scripts/dev.py lock status` — `prod` занят `form-magnet-laminated` (с 2026-11-24T20:03:46Z). Повторный `acquire` не вызывался.
  - SQL до Duplicate: старшая форма 118. После одного Duplicate: `119 CalcMagnetLamination duplicate`, затем 118, 117.
  - `wp post meta update 2586915 ezfc_form_id 119` — `Success`. `post_status` копии `draft`, мета `119`. Товар 2586724 `publish`, мета `54`.
  - `curl.exe -s -o NUL -w "%{http_code}" "https://insain.ru/?post_type=product&p=2586915"` — `404`.
  - `ezfc_copy_apply.php` без `apply`, затем с `apply`: `calcApi=0 → calcApi=1`, `read_file` `'0' = '0'`, `rdoModeProduction` `GET_check` `index → value`. `бэкап: /tmp/ezfc-copy-119-20261124-201809.json`, по строке `записано`.
  - Флаги скидки формы 119: `sbtPriceTotalDiscount` и `sbtPriceDiscount` `hidden=1`, `calc_hidden=1`; менеджерские `hidden=0`.
  - Боевой POST тела `REF_FORM_DEFAULT_LAMINATED`: `price` 2827.85, `time_ready` 9.16, `weight_kg` 0.47. Тело запроса со страницы копии при «стандарт»: quantity 100, MagnetVinil04, 50×50, rectangular, difficulty 1, mode 1, Laminat32G. POST 200. На странице «2 900 руб.», «29 руб./шт», «со скидкой 1 983 руб.» / «19.83 руб./шт», «Срок 1 день», вес 0.47 кг. В таблице имена материалов, размер и количество; внутренних `code` нет. Консоль `insaincalc`/`ezfc` без ошибок.
  - Боевая страница в том же Chrome: «2 900 руб.», «Срок 1 день», радио «стандарт» `checked`, в HTML `calcMagnetLamination` есть, `calcApi` нет. Штучная скидка старого JS на боевой — 19.82; у `showResult` 19.83.
  - Чистый заход на `/?post_type=product&p=2586915&preview=true` после `preselect=1`: радио «стандарт» выбрано, `get_value_from` → `[1]`, цена «2 900 руб.», срок «Срок 1 день», URL дописывает `numN=100&numW=50&numH=50&dpdShape=0&dpdDifficulty=0&dpdMaterial=0&dpdLaminat=1&rdoModeProduction=1`. Повторная загрузка этой ссылки оставляет те же цену, режим и срок.
  - Смена dropdown: материал 0.7 мм — 3 000 руб. и винил 0.7 мм, `dpdMaterial=1`; форма «не стандартная» — 7 000 руб. и винил 0.88, `dpdShape=2`; сложность «с вогнутостями» — 7 000 руб., `dpdDifficulty=1`; ламинация 75 мкм — 3 100 руб. и плёнка 75 mic, `dpdLaminat=3`. «нет» у ламинации цену не меняет: пустой код в запрос не кладётся, API подставляет Laminat32G.
  - SQL после сохранения админки: элемент 4333 `has_api=1`, `read_file=0`; элемент 4346 `preselect=1`, `GET_check=value`. Боевые 2234 `has_api=0`, 2247 `preselect=0`, `GET_check=index`.
  - `curl` боевой страницы: `calcMagnetLamination` 1 раз, `calcApi` 0.
  - `Select-String` по `wp-plugin/forms/magnet_laminated.js` — строки `syncUrl(`, `calcApi('magnet_laminated'`, `showResult(`; `querySelector` и присваивания `price` нет.
  - `make check` в этой сессии не перезапускался: код калькулятора и JS в git не менялись, прошлый прогон `850 passed` / `81 passed`, код выхода 0.

### Промпт следующей сессии

```text
Человек, приёмка. todo/form-magnet-laminated.md, ветка task/form-magnet-laminated, статус закрытие. Reviewer не нужен. Коммита нет, ветки нет в main.

JS копии записан в элемент 4333 формы 119 (read_file=0): is_number, is_barcode, is_variables внутри params calcApi. Дефолт со снятыми галочками: «2 900 руб.», «Срок 1 день», POST 200, price 2827.85. Боевая форма 54 и товар 2586724 не менялись, страница на calcMagnetLamination. Плагин не выкладывался. API не выкатывался: включённые галочки цену не изменят, пока нет deploy-api.

Варианты: 1) слить в main и выкатить API, чтобы галочки начали менять цену (рекомендуется); 2) слить без выкатки API; 3) доработка, не сливать. Lock prod держит form-magnet-laminated. Рабочая папка: D:\Projects\insain-agent-form-magnet-laminated.
```
