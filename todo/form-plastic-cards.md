# form-plastic-cards

Статус: закрытие
Сложность: низкая
Implementer: Grok 4.7
Reviewer: не нужен
Site ops: Grok 4.7
Почему: копия формы по skill `ezfc-form-to-api`, калькулятор `cards` уже в API; в allowed один пропуск `isMagneticStripeHiCo`.

## Цель

Копия формы 56 CalcPlasticCards на черновике товара считает `POST /api/v1/calc/cards`. URL копии пишется GET-именами элементов. Ссылка с этими GET открывает ту же копию с теми же значениями и той же ценой. Боевая страница https://insain.ru/catalog/kalkulyator-plastikovyh-kart/ остаётся на `insaincalc.calcPlasticCards`. Боевое переключение отложено решением человека 22.11.2026.

## Контекст и ссылки

- `.cursor/skills/ezfc-form-to-api/SKILL.md`, этапы `verify.md` и `copy.md`. Шаги 17–24 не входят.
- `docs/ezfc-api-migration.md` — GET = имя элемента.
- `docs/site/forms.md` — строка формы 56, только читать.
- `calc_service/calculators/cards.py`, `calc_service/tests/test_calculators/test_cards.py`.
- `js_legacy/calc/calcCards.js`, функция `calcPlasticCards` — эталон дефолта формы.
- `scripts/js_port_gaps_allowed.txt` — строка `calcPlasticCards option isMagneticStripeHiCo`.
- `todo/EPIC-forms-to-api.md` — пачка 7.
- Остальное не открывать.

## Scope

- В git (Implementer): шаги 0–5б и `wp-plugin/forms/cards.js`. `REF_FORM_DEFAULT` в `test_cards.py` с пометкой `# JS, ДД.ММ.ГГГГ`. `calcCards.js` в `scripts/run_js_calc.mjs` не подключён — эталон прямым прогоном файла в Node vm, раннер не править.
- Пропуск `isMagneticStripeHiCo`: если дефолт формы от него не зависит и цена сходится — оставить в docstring и allowed. Если дефолт без этой ветки не сходится — портировать её в `cards.py` в этой задаче и снять строку из allowed. Калькулятор не на боевой форме API, предпосылку не заводить. Новые строки в allowed не добавлять.
- На проде (Site ops): дубль формы 56 на черновик после совпадения дефолта с боевым API. Если порт менял ответ — сначала `deploy-api` с `main`, потом дубль. JS копии в элементе (`read_file=0`). Плагин не выкладывать. Боевую 56 не переключать.
- Строка для будущего боевого пакета и дописка для `docs/js-runner-cases.md` — в «Результат», не в общие файлы.

## Файлы

- `wp-plugin/forms/cards.js`
- `calc_service/calculators/cards.py`
- `calc_service/tests/test_calculators/test_cards.py`
- `scripts/js_port_gaps_allowed.txt` — только снять строку `calcPlasticCards`, если ветка портирована
- WordPress: только копия формы 56 и её черновик

## Не-scope

- `todo/forms-batch-switch.md`, `docs/site/forms.md`, `docs/js-runner-cases.md`, `scripts/run_js_calc.mjs`
- Боевая форма 56 и шаги 17–24, выкладка плагина, JSON цен, `calc_service/calculators/__init__.py`
- Новые строки в `scripts/js_port_gaps_allowed.txt`. Чужие калькуляторы.

## Критерии приёмки

Каждый пункт — команда и ожидаемый результат.
Скрипт через `@'…'@ | python -` в PowerShell 5.1 — первой строкой `$OutputEncoding = New-Object System.Text.UTF8Encoding $false`, иначе кириллица в нём станет `?`.

- [x] `python scripts/js_port_gaps.py calcPlasticCards` — пропуск `isMagneticStripeHiCo` либо снят, либо назван в docstring и остаётся в allowed. `python scripts/js_port_gaps.py --check` печатает `ok`.
- [x] `python -m pytest calc_service/tests/test_calculators/test_cards.py calc_service/tests/test_wp_plugin_forms.py -q` — `passed`. Есть `REF_FORM_DEFAULT` с `# JS,`.
- [x] Боевой `POST /api/v1/calc/cards` на теле `REF_FORM_DEFAULT`: `price` и `time_ready` как у JS (допуск цены abs ≤ 0.02 или rel ≤ 0.001, срока rel ≤ 0.001). Если порт ещё не выкачен — пункт после `deploy-api`, копию до него не принимать.
- [x] `Select-String -Path wp-plugin\forms\cards.js -Pattern "calcApi\('cards'|syncUrl\(|showResult\("` — все три есть. Своей `price` и `querySelector` нет.
- [x] Копия не на витрине: `wp post get 2586913 --field=post_status` → `draft`; `curl.exe -s -o NUL -w "%{http_code}"` гостем на `/?post_type=product&p=2586913` → `404`.
- [x] На копии под админом дефолт даёт `POST /api/v1/calc/cards` → 200, `price` 3155. На странице `3 200 руб.` — это `insaincalc.round(3155, 100)`. Срок свежей загрузки не совпадает с боевой формой: см. блокер.
- [x] `curl.exe -s https://insain.ru/catalog/kalkulyator-plastikovyh-kart/` — в HTML есть `calcPlasticCards`, нет `calcApi`.

### Критерии перевода формы ezFC на API

- [x] URL обновляется GET-именами формы; ссылка с GET открывает форму с теми же значениями и той же ценой.

## Проверки

- [x] `make check` (или `python scripts/dev.py check`) — зелёный вывод
- [x] Self-review — чеклист «Перед сдачей» в [AGENTS.md](../AGENTS.md)

## Риски

- Прод: боевая форма 56 не меняется. Выкатка API — только если менялся калькулятор, с `main`. Запись в формы не параллельно с `todo/ezfc-options-source-reset.md`.
- Цены: JSON не менять.
- Формы: id боевой 56 не менять; копия — новая форма на черновике.

## Режим

прод

## Журнал передач

Строка на сессию: `<дата> — <роль>, <модель> — <итог> — дальше <роль>`. Блокер — по формату
[docs/agents/workflow.md](../docs/agents/workflow.md). Замечания ревью — ниже, в «Ревью N».

22.11.2026 — человек — завести 8 лид-копий, боевые формы не переключать, форма 68 через tablets — дальше Implementer
23.11.2026 — Implementer, Grok 4.7 — дефолт формы 56 сходится с JS и боевым API, forms/cards.js и size_mm, пропуск isMagneticStripeHiCo оставлен — дальше Site ops
23.11.2026 — человек — принято: слить в main, выкатить API, затем копия — дальше Site ops
23.11.2026 — Site ops, Grok 4.7 — API 9439134 выкачен, копия 117 на черновике 2586913; свежая загрузка пишет mode 0 и срок 7 дней вместо 5 на боевой — дальше Implementer

Блокер: свежая копия без GET не выбирает радио «стандарт» и считает mode 0 (срок 7 дней). Боевая форма 56 на том же дефолте держит радио включённым и показывает срок 5 дней.
Пробовал: `bash infra/deploy.sh` → `9439134`, smoke пройден. Боевой POST дефолта (`quantity` 100, `material_id` White, `lamination` gloss, `mode` 1) → 200, `price` 3155, `time_ready` 40, `materials[0].size_mm` [86, 54]. Дубль формы 56 → id 117 «CalcPlasticCards duplicate», одна новая строка. Товар 2586913, `post_status` draft, `ezfc_form_id` 117; гость `curl` → 404. Боевой товар 2586740 остался `publish` и форма 56. `ezfc_copy_apply.php` apply: `calcApi=1`, `read_file` 0, `rdoModeProduction` GET_check `index` → `value`, бэкап `/tmp/ezfc-copy-117-20261123-153135.json`. `wp cache flush` — Success; `wp litespeed-purge all` — 400. Превью `/?post_type=product&p=2586913&preview=true` само уходит на `rdoModeProduction=0`, оба radio `checked=false`, `get_value_from(4292)` = 0, POST `mode` 0, `time_ready` 56, на странице «Срок 7 дней» и `3 200 руб.`. Боевая https://insain.ru/catalog/kalkulyator-plastikovyh-kart/ : radio `ezfc_element-2311-0` checked, data-value 1, «Срок 5 дней», `3 200 руб.`, в HTML есть `calcPlasticCards`, нет `calcApi`. Клик «стандарт» на копии: `get_value_from` = [1], URL `rdoModeProduction=1`, «Срок 5 дней», POST `mode` 1, `time_ready` 40. Повтор этой ссылки сохраняет radio, срок и цену. «быстрее» → [2], URL `=2`, «Срок 4 дня». Смена пластика на индекс 1: URL `dpdMaterial=1`, материал «золотой…», цена `3 800 руб.`, размер 86,54. Цветность и ламинация меняют URL и не меняют эту цену: цвет в `calcApi` не уходит (так в `cards.js`). Консоль: ошибок `insaincalc` и `ezfc` нет; `insainParse/scrtp.js` падает на `querySelector` — вне формы.
Гипотеза: у невыбранного radio `get_value_from` возвращает число 0, не пустую строку. `first(0)` не считается пустым, JS пишет `mode` 0 и `syncUrl` ставит `rdoModeProduction=0`. У опций data-value 1 и 2, GET_check=value значение 0 не находит, оба radio гаснут. Боевая форма GET на элемент 2311 не включает (пусто, check `index`) и оставляет первый radio выбранным, плейсхолдер `{{rdoModeProduction}}` даёт 1.
Вопрос: починить чтение режима в `forms/cards.js` и заново записать JS копии 117.
Следующая сессия: Implementer, модель Grok 4.7
23.11.2026 — Implementer, Grok 4.7 — пустой radio в cards.js даёт mode 1, как calcPlasticCards; тест без правки падал — дальше Site ops, модель Grok 4.7 (шаг 15 skill, не эскалация)
23.11.2026 — Site ops, Grok 4.7 — JS копии 117 перезаписан; свежая загрузка считает mode 1 и срок 5 дней, радио «стандарт» не отмечено — дальше человек
24.11.2026 — человек — отметить «стандарт» в cards.js, когда режим подставлен из пустого radio, затем перезаписать копию 117 — дальше Implementer

Блокер: свежая копия без GET считает как «стандарт» (POST mode 1, срок 5 дней, на странице 3 200 руб.), но радио не выбрано. Боевая форма 56 на том же дефолте держит радио включённым.
Пробовал: `ezfc_copy.py` и `ezfc_copy_apply.php apply` — элемент 4279, JS 3082 → 3609 байт, calcApi=1, read_file 0, GET без изменений, бэкап `/tmp/ezfc-copy-117-20261123-154937.json`. SQL: элемент 2298 формы 56 без modeUnset и без calcApi, с calcPlasticCards; элемент 4279 формы 117 с modeUnset и calcApi. `wp post get 2586913` → draft; гость curl → 404. `wp litespeed-purge all` → 400; `wp cache flush` → Success. Флаги скидки hidden=1, calc_hidden=1; менеджерские hidden=0. Превью без GET: URL дописался до `rdoModeProduction=1`, оба radio checked=false, POST mode 1, material_id White, 200, «Срок 5 дней», «3 200 руб.». HTML копии без checked; боевая `ezfc_element-2311-0` с checked, в HTML есть calcPlasticCards и нет calcApi. «быстрее»: radio data-value 2, URL `=2`, POST mode 2, «Срок 4 дня», «3 200 руб.»; перезагрузка сохраняет радио и срок. Ссылка с `rdoModeProduction=1`: radio data-value 1 выбран, POST mode 1, «Срок 5 дней», «3 200 руб.», «Пластиковые карты белые», размер 86,54. API: mode 1 → price 3155, time_ready 40; mode 2 → price 3155, time_ready 32. Консоль: ошибок insaincalc и ezfc нет.
Гипотеза: у копии включён GET, и ezFC не пишет checked, если параметра нет в запросе. Боевая GET на радио не включает, поэтому сервер ставит checked. JS подставляет mode 1 в POST и в URL, но input не отмечает. Полная загрузка ссылки с `rdoModeProduction=1` радио отмечает. Повторная запись того же JS это не исправит.
Вопрос: (1) Implementer в cards.js отмечает «стандарт», когда режим подставлен из пустого radio, без querySelector и без своего вывода цены; затем Site ops заново пишет копию 117 и повторяет шаги 12–14. Третьей записи того же JS без этой правки не делать. (Рекомендуется) (2) Принять копию: цена, срок и ссылка с GET сошлись, пустая точка только на первом экране без параметра; статус «закрытие». (3) Откатить JS копии строками из `/tmp/ezfc-copy-117-20261123-154937.json`, черновик 2586913 не удалять.
Следующая сессия: человек
24.11.2026 — Implementer, Grok 4.7 — пустой radio отмечает «стандарт» в cards.js, [1] и [2] не сдвинуты; тест без правки падал — дальше Site ops, модель Grok 4.7 (шаг 15 skill, не эскалация)
24.11.2026 — Site ops, Grok 4.7 — JS копии 117 с отметкой «стандарт» записан, 4597 байт; свежая загрузка: radio checked, mode 1, срок 5 дней, 3 200 руб. — дальше человек
24.11.2026 — человек — принято — закрытие

## Найдено вне scope

- Боевой cjsCalc (элемент 2298) пишет ключи `isSignatureStrip ` и `isScratchPanel ` с хвостовым пробелом. На живой форме включённые галки не входят в цену. В `forms/cards.js` ключи без пробела: на 100 шт полоса подписи даёт JS cost 2140 / price 3552.4, скретч — cost 2100 / price 3486. Дефолт обе галки выключены.
- `isEmbossing` в боевом JS закомментирован, поля формы нет. В API параметр необязательный, в запрос не уходит.
- `calcCards.js` не подключён в `scripts/run_js_calc.mjs`. Эталон снят прямым прогоном файла в Node vm. Раннер не менялся.

## Результат

- Ветка, PR или коммит: `task/form-plastic-cards`, коммит git-части перед слиянием в main
- Период: 2026-11-23 — 2026-11-24
- Часы человека: не оценивались
- Работа агентов: 1 сессия; Grok 4.7
- Было / стало: форма 56 на `calcPlasticCards`, эталона дефолта в тесте нет; стало — `forms/cards.js` на `calcApi('cards')`, дефолт JS price 3154 / time_ready 40 ч (API ceil 3155), в materials `size_mm` 86×54. Боевая страница не менялась.
- Сделано: шаги 0–5б и `wp-plugin/forms/cards.js`. `REF_FORM_DEFAULT` с пометкой `# JS, 23.11.2026`. В `cards.py` у материала `size_mm` из прайса. Пропуск `option_isMagneticStripeHiCo` назван в docstring и оставлен в allowed: дефолт полосу не включает, цена сходится, ветка расчёта уже есть как `is_magnetic_stripe`.
- Чем проверено: `python scripts/js_port_gaps.py calcPlasticCards` — `нет в Python: option isMagneticStripeHiCo`; `--check` — `ok`. pytest `test_cards.py` и `test_wp_plugin_forms.py` — 19 passed. Боевой POST дефолта: cost 1900, price 3155, time_ready 40 (mode 0 → 56, mode 2 → 32). JS vm: price 3154.0000000000005, те же сроки; rel цены 0.00032. `Select-String` по `cards.js` — `calcApi('cards'`, `syncUrl(`, `showResult(`, своих `price` и `querySelector` нет. `curl` страницы каталога — в HTML есть `calcPlasticCards`, строки `calcApi` нет. `python scripts/dev.py check` — calc_service 838 passed, bot_service 81 passed, код 0.
- Не сделано и почему: дубль формы, черновик, отладка копии, деплой API и боевая 56 — Site ops. Плагин не выкладывался. Общие файлы не правились; дописки ниже. `docs/dashboard.md` check пересобрал и файл возвращён на HEAD: это общий файл. Повторный `python scripts/dev.py check` в начале снова запишет статус «в работе» и останется зелёным.
- Требуется решение: для копии — нет. Перед будущим боевым переключением: галки подписи и скретча на API начнут входить в цену, на текущем JS из-за пробела в ключе не входят.
- Для Reviewer: id `get_value_from` совпали с полями шага 5. В новом JS id 2315 и 2316 — полоса подписи и скретч, без пробела в ключе API.
- В `calcApi` не уходят (только `syncUrl`): `dpdColor`, `ckbVariables`. Параметр API `is_embossing` на форме поля не имеет, в запрос не пишется.
- Дописка `docs/js-runner-cases.md` (не записана): `calcPlasticCards` form 56 default — slug `cards`, price 3154, timeReady 40; mode 0 — timeReady 56; mode 2 — timeReady 32. Раннер функцию не грузит, число снято Node vm 23.11.2026.
- Строка будущего боевого пакета (не записана): форма 56 CalcPlasticCards, https://insain.ru/catalog/kalkulyator-plastikovyh-kart/, slug `cards`, файл `wp-plugin/forms/cards.js`. Боевую не переключать (решение 22.11.2026). GET: `numN`, `dpdMaterial:index`, `dpdColor:index`, `dpdLaminat:index`, `ckbNumber:index`, `ckbBarcode:index`, `ckbVariables:index`, `ckbEmbossingFoil:index`, `ckbMagneticStripeHiCo:index`, `ckbSignatureStrip:index`, `ckbScratchPanel:index`, `rdoModeProduction:value`.
- Деплой API до копии: да. Ответ калькулятора получил `materials[].size_mm`. Цена и срок на текущем боевом API уже совпадают с JS в допуске; колонка «Размер» на копии будет пустой, пока этот коммит не на `main` и не выкачен.
- Site ops 23.11.2026. Сделано: `bash infra/deploy.sh` на VDS, SHA `943913441b1e04fb6e68193a890f74c1c92d3a78`. Боевой POST дефолта → 200, `price` 3155, `time_ready` 40, `size_mm` [86, 54]. Форма 117 «CalcPlasticCards duplicate», товар-черновик 2586913 «Калькулятор пластиковых карт (Копировать)», `ezfc_form_id` 117. JS в элемент 4279, `read_file=0`, `calcApi=1`. GET: `numN`, dropdown `:index`, `rdoModeProduction:value`. Плагин не выкладывался. Боевая 56 не переключалась.
- Чем проверено: вывод `deploy.sh` «9439134 выкачен, smoke пройден»; `git rev-parse` на VDS тот же SHA. POST `https://insain.ru/api/v1/calc/cards`. `wp post get 2586913` → `draft`; гость `curl` → 404. `wp post get 2586740` → `publish`, meta 56. Превью под админом: POST 200, тело с `material_id` White, не `0`; страница `3 200 руб.` = `round(3155, 100)`; таблица «Пластиковые карты белые», размер 86,54, количество 100, внутреннего `code` нет. Ссылка с `rdoModeProduction=1` снова открывает «стандарт», срок 5 дней и ту же цену. Свежая загрузка без GET — срок 7 дней, radio не выбран. Боевая страница — срок 5 дней, radio выбран.
- Не сделано и почему: приёмка копии. Свежий дефолт копии не равен боевой форме по режиму и сроку. Это ошибка JS при пустом radio (шаг 15), порт и боевой API по `REF_FORM_DEFAULT` сходятся. Правка `cards.js` — Implementer, не эта сессия.
- Как откатить копию: строки из `/tmp/ezfc-copy-117-20261123-153135.json` вернуть в элементы формы 117; товар 2586913 оставить черновиком или удалить только с подтверждением человека. Откат API — повторный `bash infra/deploy.sh` со старого `main` не нужен: smoke прошёл, образ `insain-agent-calc-api:rollback` сохранён скриптом до выкатки.
- Требуется решение: нет, маршрут шага 15 — Implementer. Варианты, если человек остановит маршрут: (1) поправить `cards.js`, пустой radio → `mode` 1, и заново записать копию 117; (2) принять копию: цена дефолта совпала, срок свежей загрузки нет; (3) откатить JS копии из бэкапа и не принимать черновик.
- 23.11.2026, Implementer, чтение режима. Сделано: в `wp-plugin/forms/cards.js` (id боевой формы 2311) скаляр `0` или `"0"` от невыбранного radio — «ничего не выбрано», не режим «дешевле». В `calcApi` и `syncUrl` уходит `mode` 1, как дефолт `calcPlasticCards`. Выбранный массив сохраняется: `[1]` → 1, `[2]` → 2, `[0]` остаётся 0. `first()` для остальных полей не менялся. Калькулятор, JSON, боевая форма 56 и плагин не трогались.
- Чем проверено: до правки `test_cards_js_empty_radio_is_mode_one` падал (`mode` 0, `assert 0 == 1`). После — `python -m pytest calc_service/tests/test_calculators/test_cards.py calc_service/tests/test_wp_plugin_forms.py -q` — 20 passed. `Select-String` по `cards.js`: `calcApi('cards'`, `syncUrl(`, `showResult(`; своих `price` и `querySelector` нет. `python scripts/dev.py check` — calc_service 843 passed, bot_service 81 passed, код 0. `docs/dashboard.md` check пересобрал и файл возвращён на HEAD: это общий файл.
- Не сделано и почему: записать JS на копию 117 и повторить шаги 12–14 — Site ops. Боевую 56 не переключать, плагин не выкладывать. Общие файлы не правились.
- Требуется решение: нет. Site ops заново пишет `forms/cards.js` в форму 117 (товар-черновик 2586913, `read_file=0`) и повторяет шаги 12–14. Свежая загрузка без GET: radio «стандарт» выбран, POST `mode` 1, срок 5 дней, на странице `3 200 руб.`
- 23.11.2026, Site ops, повторная запись JS. Сделано: `forms/cards.js` заново записан в элемент 4279 формы 117, `read_file=0`, `calcApi=1`, JS 3609 байт, в коде `modeUnset` и `get_value_from(4292)`. GET тот же: `numN`, dropdown `:index`, `rdoModeProduction:value`. Бэкап `/tmp/ezfc-copy-117-20261123-154937.json`. Плагин не выкладывался, API не деплоился, боевая 56 не менялась (элемент 2298 без `modeUnset` и без `calcApi`).
- Чем проверено: dry-run и apply `ezfc_copy_apply.php` — `стоп` нет, `4279: записано`. `wp post get 2586913` → `draft`; гость `curl` → 404. `wp cache flush` — Success; `wp litespeed-purge all` — 400. Флаги шага 13а: скидка `hidden=1`, `calc_hidden=1`; менеджерские `hidden=0`. Превью без GET: POST 200, `mode` 1, `material_id` White, страница «Срок 5 дней» и `3 200 руб.`; оба radio `checked=false`. Боевой `curl` страницы: `checked='checked'` у `ezfc_element-2311-0`, есть `calcPlasticCards`, нет `calcApi`. «быстрее»: POST `mode` 2, «Срок 4 дня», radio data-value 2, перезагрузка сохраняет срок. Ссылка `rdoModeProduction=1`: radio выбран, POST `mode` 1, те же 5 дней и `3 200 руб.`, размер 86,54. Прямой POST API: mode 1 — price 3155, time_ready 40; mode 2 — price 3155, time_ready 32. Консоль: ошибок `insaincalc` и `ezfc` нет.
- Не сделано и почему: приёмка копии. Свежий дефолт считает верно, но радио «стандарт» на загрузке без GET не отмечено. Повтор той же записи JS это не чинит. Смену каждого dropdown в этой сессии не повторял. Общие файлы не правились.
- Как откатить эту запись: строки из `/tmp/ezfc-copy-117-20261123-154937.json` вернуть в элементы формы 117. Товар 2586913 оставить черновиком. Боевая форма и API не менялись, откат им не нужен.
- Требуется решение: да, человек. Варианты в журнале. Рекомендуется (1): Implementer отмечает пустой radio как «стандарт» в `cards.js` без querySelector, затем Site ops снова пишет копию. (2) Принять копию и поставить «закрытие». (3) Откатить JS копии из бэкапа.
- 24.11.2026, Implementer, отметка радио. Сделано: в `wp-plugin/forms/cards.js` скаляр `0` / `"0"` по-прежнему даёт `mode` 1. Когда режим подставлен из этого пустого radio (`modeUnset`), пункт «стандарт» получает `checked`: индекс 0, data-value 1. Id элемента — `get_element_id_by_name(__form_id__, 'rdoModeProduction')`, не литерал: `ezfc_copy.py` переписывает только `get_value_from`, на копии 117 радио — 4292. Выбранные `[1]`, `[2]` и `[0]` не отмечаются. `change` не шлётся. Своего вывода цены нет, `querySelector` нет. Калькулятор, JSON, боевая 56 и плагин не трогались.
- Чем проверено: до правки `test_cards_js_empty_radio_checks_standard_option` падал (`checked` нет, `assert None == 'ezfc_element-4292-0'`), соседний тест mode 1 оставался зелёным. После — `python -m pytest calc_service/tests/test_calculators/test_cards.py calc_service/tests/test_wp_plugin_forms.py -q` — 21 passed. `Select-String` по `cards.js`: `calcApi('cards'`, `syncUrl(`, `showResult(`; своих `price` и `querySelector` нет. `python scripts/dev.py check` — calc_service 844 passed, bot_service 81 passed, код 0. `docs/dashboard.md` check пересобрал и файл возвращён на HEAD: это общий файл.
- Не сделано и почему: записать этот JS в элемент 4279 формы 117 и повторить шаги 12–14 — Site ops. Боевую 56 не переключать, плагин не выкладывать, API не деплоить. Третью запись прежнего JS без отметки радио не делать. Общие файлы не правились.
- Требуется решение: нет. Site ops заново пишет `forms/cards.js` в форму 117 (товар-черновик 2586913, элемент 4279, `read_file=0`) и повторяет шаги 12–14. Свежая загрузка без GET: radio «стандарт» checked, POST `mode` 1, срок 5 дней, на странице `3 200 руб.` Ссылка с `rdoModeProduction=1` и «быстрее» (`=2`) остаются как после прошлой записи.
- 24.11.2026, Site ops, запись JS с отметкой радио. Сделано: `wp-plugin/forms/cards.js` этой ветки заново записан в элемент 4279 формы 117 через `ezfc_copy.py` и `ezfc_copy_apply.php apply`. `read_file=0`, `calcApi=1`, JS 3609 → 4597 байт, в коде `modeUnset`, `modeInput.checked = true` и `get_value_from(4292)`. GET без изменений: `numN`, dropdown `:index`, `rdoModeProduction:value`. Бэкап `/tmp/ezfc-copy-117-20261123-161751.json`. Плагин не выкладывался, API не деплоился, боевая 56 не менялась (элемент 2298: 3293 байт, нет `modeUnset` и нет `calcApi`, есть `calcPlasticCards`).
- Чем проверено: dry-run и apply — `стоп` нет, `4279: записано`. SQL: элемент 4279, `read_file` 0, LENGTH 4597, отметка `checked` есть. `wp post get 2586913` → `draft`; meta формы 117. Гость `curl` → 404. Боевой товар 2586740 → `publish`, meta 56. `wp cache flush` — Success; `wp litespeed-purge all` — 400. Флаги шага 13а: скидка `hidden=1`, `calc_hidden=1`; менеджерские `hidden=0`. Боевой HTML каталога: есть `calcPlasticCards`, нет `calcApi`, `ezfc_element-2311-0` с `checked`. Превью без GET `/?post_type=product&p=2586913&preview=true`: URL дописался до `rdoModeProduction=1`, radio `ezfc_element-4292-0` checked (data-value 1, индекс 0), второй radio checked=false. POST `/api/v1/calc/cards` 200, `mode` 1, `quantity` 100, `material_id` White, `lamination` gloss. На странице «Срок 5 дней», «3 200 руб.», «Пластиковые карты белые», размер 86,54, количество 100, вес 0,50 кг. Прямой POST API: mode 1 — price 3155, time_ready 40; mode 2 — price 3155, time_ready 32. Ссылка с `rdoModeProduction=1`: тот же radio, срок 5 дней, «3 200 руб.». «быстрее»: radio `ezfc_element-4292-1` checked, data-value 2, URL `=2`, POST `mode` 2, «Срок 4 дня», «3 200 руб.»; перезагрузка этой ссылки сохраняет radio и срок. Пластик индекс 1: URL `dpdMaterial=1`, «3 800 руб.», в таблице «Пластик золотой, серебряный,прозрачный, перламутровый», размер 86,54. Цветность и ламинация: URL `dpdColor=1`, `dpdLaminat=1`, цена остаётся «3 800 руб.», radio «быстрее» остаётся выбранным. Консоль: ошибок нет.
- Не сделано и почему: боевую форму 56 не переключал, плагин не выкладывал, API не деплоил. Общие файлы не правились. Коммит, push и слияние не делались.
- Как откатить эту запись: строки из `/tmp/ezfc-copy-117-20261123-161751.json` вернуть в элементы формы 117. Товар 2586913 оставить черновиком. Боевая форма и API не менялись, откат им не нужен.
- Требуется решение: да, человек принимает копию. Черновик 2586913, форма 117, превью `https://insain.ru/?post_type=product&p=2586913&preview=true`. Свежая загрузка отмечает «стандарт», POST mode 1, срок 5 дней, на странице 3 200 руб. Ссылка с GET и «быстрее» (срок 4 дня) работают. Боевая страница не менялась.
