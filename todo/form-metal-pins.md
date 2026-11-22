# form-metal-pins

Статус: закрытие
Сложность: низкая
Implementer: Grok 4.7
Reviewer: не нужен
Site ops: Grok 4.7
Почему: копия формы по skill `ezfc-form-to-api`, калькулятор `metal_pins` уже в API; в allowed один пропуск `isPacking`.

## Цель

Копия формы 34 CalcMetalPins на черновике товара считает `POST /api/v1/calc/metal_pins`. URL копии пишется GET-именами элементов. Ссылка с этими GET открывает ту же копию с теми же значениями и той же ценой. Боевая страница https://insain.ru/catalog/znachki-metallicheskie-s-emalyami/ остаётся на `insaincalc.calcMetalPins`. Боевое переключение отложено решением человека 22.11.2026.

## Контекст и ссылки

- `.cursor/skills/ezfc-form-to-api/SKILL.md`, этапы `verify.md` и `copy.md`. Шаги 17–24 не входят.
- `docs/ezfc-api-migration.md` — GET = имя элемента.
- `docs/site/forms.md` — строка формы 34, только читать.
- `calc_service/calculators/metal_pins.py`, `calc_service/tests/test_calculators/test_metal_pins.py`.
- `js_legacy/calc/calcMetalPins.js` — эталон дефолта формы.
- `scripts/js_port_gaps_allowed.txt` — строка `calcMetalPins option isPacking`.
- `todo/EPIC-forms-to-api.md` — пачка 5.
- Остальное не открывать.

## Scope

- В git (Implementer): шаги 0–5б и `wp-plugin/forms/metal_pins.js`. `REF_FORM_DEFAULT` в `test_metal_pins.py` с пометкой `# JS, ДД.ММ.ГГГГ`. `calcMetalPins.js` в `scripts/run_js_calc.mjs` не подключён — эталон прямым прогоном файла в Node vm, раннер не править.
- Пропуск `isPacking`: если дефолт формы от него не зависит и цена сходится — оставить в docstring и allowed. Если дефолт без этой ветки не сходится — портировать её в `metal_pins.py` в этой задаче и снять строку из allowed. Калькулятор не на боевой форме API, предпосылку не заводить. Новые строки в allowed не добавлять.
- На проде (Site ops): дубль формы 34 на черновик после совпадения дефолта с боевым API. Если порт менял ответ — сначала `deploy-api` с `main`, потом дубль. JS копии в элементе (`read_file=0`). Плагин не выкладывать. Боевую 34 не переключать.
- Строка для будущего боевого пакета и дописка для `docs/js-runner-cases.md` — в «Результат», не в общие файлы.

## Файлы

- `wp-plugin/forms/metal_pins.js`
- `calc_service/calculators/metal_pins.py`
- `calc_service/tests/test_calculators/test_metal_pins.py`
- `scripts/js_port_gaps_allowed.txt` — только снять строку `calcMetalPins`, если ветка портирована
- WordPress: только копия формы 34 и её черновик

## Не-scope

- `todo/forms-batch-switch.md`, `docs/site/forms.md`, `docs/js-runner-cases.md`, `scripts/run_js_calc.mjs`
- Боевая форма 34 и шаги 17–24, выкладка плагина, JSON цен, `calc_service/calculators/__init__.py`
- Новые строки в `scripts/js_port_gaps_allowed.txt`. Чужие калькуляторы.

## Критерии приёмки

Каждый пункт — команда и ожидаемый результат.
Скрипт через `@'…'@ | python -` в PowerShell 5.1 — первой строкой `$OutputEncoding = New-Object System.Text.UTF8Encoding $false`, иначе кириллица в нём станет `?`.

- [x] `python scripts/js_port_gaps.py calcMetalPins` — пропуск `isPacking` либо снят, либо назван в docstring и остаётся в allowed. `python scripts/js_port_gaps.py --check` печатает `ok`.
- [x] `python -m pytest calc_service/tests/test_calculators/test_metal_pins.py calc_service/tests/test_wp_plugin_forms.py -q` — `passed`. Есть `REF_FORM_DEFAULT` с `# JS,`.
- [x] Боевой `POST /api/v1/calc/metal_pins` на теле `REF_FORM_DEFAULT`: `price` и `time_ready` как у JS (допуск цены abs ≤ 0.02 или rel ≤ 0.001, срока rel ≤ 0.001). Если порт ещё не выкачен — пункт после `deploy-api`, копию до него не принимать.
- [x] `Select-String -Path wp-plugin\forms\metal_pins.js -Pattern "calcApi\('metal_pins'|syncUrl\(|showResult\("` — все три есть. Своей `price` и `querySelector` нет.
- [x] Копия не на витрине: `wp post get 2586909 --field=post_status` → `draft`; `curl.exe -s -o NUL -w "%{http_code}"` гостем — `404`.
- [x] На копии под админом дефолт даёт `POST /api/v1/calc/metal_pins` → 200. Цена на странице 27 700 = `insaincalc.round(27615, 100)`.
- [x] `curl.exe -s https://insain.ru/catalog/znachki-metallicheskie-s-emalyami/` — в HTML есть `calcMetalPins`, нет `calcApi`.

### Критерии перевода формы ezFC на API

- [x] URL обновляется GET-именами формы; ссылка с GET открывает форму с теми же значениями и той же ценой. (копия, Site ops)

## Проверки

- [x] `make check` (или `python scripts/dev.py check`) — зелёный вывод
- [x] Self-review — чеклист «Перед сдачей» в [AGENTS.md](../AGENTS.md)

## Риски

- Прод: боевая форма 34 не меняется. Выкатка API — только если менялся калькулятор, с `main`. Запись в формы не параллельно с `todo/ezfc-options-source-reset.md`.
- Цены: JSON не менять.
- Формы: id боевой 34 не менять; копия — новая форма на черновике.

## Режим

прод

## Журнал передач

Строка на сессию: `<дата> — <роль>, <модель> — <итог> — дальше <роль>`. Блокер — по формату
[docs/agents/workflow.md](../docs/agents/workflow.md). Замечания ревью — ниже, в «Ревью N».

22.11.2026 — человек — завести 8 лид-копий, боевые формы не переключать, форма 68 через tablets — дальше Implementer
22.11.2026 — Implementer, Grok 4.7 — сверка дефолта с JS и боевым API, `forms/metal_pins.js`, ответ калькулятора не менялся — дальше Site ops
22.11.2026 — Site ops, Grok 4.7 — копия 113 на черновике 2586909, дефолт API price 27615, на странице 27700, GET-ссылка держит режим и цену — дальше человек
22.11.2026 — человек — принято — закрытие

## Найдено вне scope

- В dropdown формы код алюминия `aluminium`, в прайсе ключ `aluminum`. Код булавки `SafetyPinMetall`, в прайсе `SafetyPin`. Старый JS на этих пунктах падает. Подмена только в `forms/metal_pins.js`; прямой POST с этими кодами калькулятор не алиасит.
- Колонки CostStamp 4 и 5 в JSON обе равны 80: подписи «офсет» и «шелкография» на форме относительно комментария JSON не меняют цену.
- `calcMetalPins` не пишет `result.material`. Боевая таблица материалов пустая. API на дефолте отдаёт «Крепление игла-цанга» и «Полиэтиленовый пакетик», количество 100, `size_mm` нет. Состав страницы и API разный, потому что старый JS карту не заполняет; `size_mm` в JS формы не подставлялся. Строки материалов в калькуляторе не снимались: эталон `PolyBag` уже в тесте.
- Подпись режима на форме начинается с латинской `c` («cтандарт»), поэтому поиск по слову «стандарт» её не находит. Так же на боевой странице.

## Результат

- Ветка, PR или коммит: `task/form-metal-pins`
- Период: 2026-11-22 — 2026-11-22
- Часы человека: 0 ч (коммита нет)
- Работа агентов: 1 сессия Implementer и 1 сессия Site ops; Grok 4.7
- Было / стало: боевая форма 34 по-прежнему на `calcMetalPins`. Копия формы 113 `CalcMetalPins duplicate` на черновике товара 2586909, `ezfc_form_id` 113. Дефолт копии считает `metal_pins`: API price 27615, на странице 27 700.
- Сделано: шаги 0–5б. Пропуск `isPacking` оставлен: в docstring он назван `option_isPacking` (токен без подчёркивания `js_port_gaps.py` считает порт закрытым), строка allowed на месте, `--check` печатает `ok`. Дефолт формы 34 со страницы: 100 шт, вид «простой», 20×20 мм, латунь, процесс 1, серебро, 0 эмалей, толщина 1.2, крепление BC, упаковка PolyBag (в HTML нет `selected`, браузер берёт первый пункт), режим «стандарт» = data-value 1. PolyBag имеет cost 0: price и time_ready те же без пакета (19725 / 360), вес 0.50 против 0.49. Вторые кейсы: двухсторонний (толщина 2-го штампа 0, price JS 37041.2) и двухсоставной (повтор штампа, price JS 43828.4). Режимы 0/1/2: price 20756.4 / 27615 / 34888, time_ready 440 / 360 / 320; price(0) < price(1) < price(2). `REF_FORM_DEFAULT` и кейсы mode/двух штампов в `test_metal_pins.py` с пометкой `# JS, 22.11.2026`. `wp-plugin/forms/metal_pins.js`: `calcApi('metal_pins')`, `syncUrl`, `showResult`; id боевой формы 34. Ответ калькулятора не менялся.
- Чем проверено:
  - `python scripts/js_port_gaps.py calcMetalPins` — `нет в Python: option isPacking`. `python scripts/js_port_gaps.py --check` — `ok`.
  - Node vm, `js_legacy/calc/calcMetalPins.js` + StructDat прайса `calc_service/data` (в `run_js_calc.mjs` функции нет): дефолт cost 19725, price 27615, time 0, timeReady 360, weight 0.5, material size 0. mode 0: 14826 / 20756.4 / 440. mode 2: 24920 / 34888 / 320.
  - Локальный `MetalPinsCalculator.calculate` на тех же телах: cost и time_ready совпали, price mode 0 = 20757 (ceil, rel 2.9e-05), mode 1 = 27615, mode 2 = 34888.
  - Боевой POST `https://insain.ru/api/v1/calc/metal_pins` на `REF_FORM_DEFAULT` и mode 0/2, двухсторонний, двухсоставной: HTTP 200, те же cost/price/time_ready, что локальный Python (допуск шага 2).
  - `python -m pytest calc_service/tests/test_calculators/test_metal_pins.py calc_service/tests/test_wp_plugin_forms.py -q` — `21 passed`.
  - `Select-String` по `wp-plugin/forms/metal_pins.js`: есть `calcApi('metal_pins'`, `syncUrl(`, `showResult(`; `querySelector` и `price =` нет.
  - `python scripts/dev.py check` — `809 passed`, затем `81 passed`, код выхода 0.
  - HTML `https://insain.ru/catalog/znachki-metallicheskie-s-emalyami/`: два вхождения `calcMetalPins`, `calcApi` нет.
  - `GET /api/v1/tool_schema/metal_pins`: обязательны `quantity`, `width_mm`, `height_mm`. Поля формы есть (numN, numW1, numH1).
- Сделано, Site ops, шаги 6–16: форма 113 `CalcMetalPins duplicate` (одна новая строка после 112). Черновик товара 2586909 «Значки металлические с эмалями (Копировать)», `ezfc_form_id` 113, `post_status` draft. Гость: `404`. В элемент `cjsCalc` 4161 записан текст `wp-plugin/forms/metal_pins.js` с id копии, `read_file=0`, `calcApi=1`. GET = имя элемента. `rdoModeProduction` (4174): `GET_check` index → value. Dropdown и checkbox: `index`. В `metal_pins.js` id для URL стоят внутри `get_value_from`, иначе `ezfc_copy.py` оставлял id боевой формы в `optionIndex`/`checkedIndex`. Ответ калькулятора не менялся. `deploy-api` не делался. Плагин не выкладывался. Боевая 34 не переключалась: элемент 1232 по-прежнему `calcMetalPins`, без `calcApi`.
- Чем проверено, Site ops:
  - `wp post get 2586909 --field=post_status` — `draft`. `wp post meta get 2586909 ezfc_form_id` — `113`. Товар 3141 остался `publish`.
  - `curl.exe -s -o NUL -w "%{http_code}" "https://insain.ru/?post_type=product&p=2586909"` — `404`.
  - `ezfc_copy_apply.php` без `apply`, затем с `apply`: `стоп` нет, у `cjsCalc` `calcApi=0 → calcApi=1`, у `rdoModeProduction` `index → value`. Бэкап `/tmp/ezfc-copy-113-20261122-154340.json`.
  - Флаги копии: `sbtPriceTotalDiscount` и `sbtPriceDiscount` hidden=1, calc_hidden=1; менеджерские hidden=0.
  - `wp cache flush` — `Success`. `wp litespeed-purge all` — `Error: Something went wrong! Got 400`. Превью под админом всё равно отдало новый JS.
  - Превью `https://insain.ru/?post_type=product&p=2586909&preview=true`. Дефолт: POST 200, тело `quantity 100, 20×20, brass, process 1, silver, 0 эмалей, толщина 1.2, mode 1, BC, PolyBag`. Ответ API: cost 19725, price 27615, time_ready 360, weight 0.5. На странице 27 700 = `insaincalc.round(27615, 100)`, скидка 25 643, срок «45 дней», вес 0.50 кг. Боевая страница на том же дефолте: тоже «27 700» и «Срок 45 дней». Подсказка срока с датами есть. Цена и «со скидкой» в одной строке. В таблице «Крепление игла-цанга» и «Полиэтиленовый пакетик», количество 100, размер пустой, внутренних `code` нет. Ошибок `insaincalc` и `ezfc` в консоли нет.
  - URL дефолта содержит GET-имена, `rdoModeProduction=1` (value, не индекс). Чекбоксы в URL отсутствуют. Перезагрузка этой ссылки: цена 27 700, режим data-value 1 отмечен.
  - Смена упаковки на индекс 1: цена 31 700, в материалах «Акриловая коробочка 30х30х15мм», в URL `dpdPacking=1`. Включённый `ckbEpoxy1` пишет `ckbEpoxy1=0`. Перезагрузка этой ссылки оставляет чекбокс включённым, упаковку 1, режим 1, цену 32 100.
  - HTML боевой страницы после копии: `calcMetalPins` два раза, `calcApi` нет.
  - `python -m pytest calc_service/tests/test_wp_plugin_forms.py -q` — `8 passed`.
- Не сделано и почему: боевая форма 34 не переключалась (шаги 17–24 вне задачи). Плагин не выкладывался. Коммита нет. `docs/site/forms.md`, `docs/js-runner-cases.md`, `todo/forms-batch-switch.md`, `todo/EPIC-*.md`, `STATUS.md`, `BACKLOG.md` не правились. Блокировку prod не снимал.
- Как откатить: черновик 2586909 и форму 113 удалить в админке. Данные элементов копии до записи JS — `/tmp/ezfc-copy-113-20261122-154340.json`. Боевая форма 34 и товар 3141 не менялись.
- Требуется решение: нет. Дальше человек принимает копию.

### Поля: в URL, в тело API отдельным ключом не входят

`dpdForm` задаёт число штампов. Толщина, эмали, металл, процесс, покрытие, смола и «штамп есть» уходят внутри `stamps`. Файл `fluAtrwork` в URL и в API не кладётся. `width_mm`/`height_mm` — размеры первого штампа; второй штамп только в `stamps`.

### GET копии 113 (проверено на превью)

`cjsCalc` — элемент 4161, `read_file=0`. Выключенный чекбокс в URL отсутствует, включённый пишет `0`.

| Элемент | id копии | GET | GET_check |
| --- | --- | --- | --- |
| numN | 4128 | numN | — |
| numW1, numH1 | 4133, 4134 | имя элемента | — |
| numEnamels1, numT1 | 4142, 4138 | имя элемента | — |
| numW2, numH2 | 4147, 4148 | имя элемента | — |
| numEnamels2, numT2 | 4156, 4152 | имя элемента | — |
| dpdForm | 4129 | dpdForm | index |
| dpdMetall1, dpdProcess1, dpdPlating1 | 4139, 4140, 4141 | имя элемента | index |
| dpdMetall2, dpdProcess2, dpdPlating2 | 4153, 4154, 4155 | имя элемента | index |
| dpdAttachment, dpdPacking | 4158, 4159 | имя элемента | index |
| ckbThinkness1, ckbEpoxy1, ckbMould | 4136, 4143, 4144 | имя элемента | index (вкл → 0, выкл → пусто) |
| ckbThinkness2, ckbEpoxy2 | 4150, 4157 | имя элемента | index (вкл → 0, выкл → пусто) |
| rdoModeProduction | 4174 | rdoModeProduction | value |

### Строка в `docs/js-runner-cases.md` (не вносить в этой задаче)

`calcMetalPins` в `scripts/run_js_calc.mjs` не подключён. Эталон снят Node vm на прайсе `calc_service/data`, 22.11.2026.

| Функция | Slug API | `price` |
| --- | --- | --- |
| `calcMetalPins` form 34 default | `metal_pins` | 27615 |
| `calcMetalPins` form 34 default mode 0 | `metal_pins` | 20756.4 |
| `calcMetalPins` form 34 default mode 2 | `metal_pins` | 34888 |
| `calcMetalPins` form 34 двухсторонний | `metal_pins` | 37041.2 |
| `calcMetalPins` form 34 двухсоставной | `metal_pins` | 43828.4 |

### Строка в «Состав пакета» `todo/forms-batch-switch.md` (после приёмки копии)

| 34 CalcMetalPins | `metal_pins` | `/catalog/znachki-metallicheskie-s-emalyami/` | копия 113, черновик 2586909 | `form-metal-pins` |
