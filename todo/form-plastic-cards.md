# form-plastic-cards

Статус: выкатка
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
- [ ] Копия не на витрине: `wp post get <product> --field=post_status` → `draft` или `private`; `curl.exe -s -o NUL -w "%{http_code}"` гостем — не `200`.
- [ ] На копии под админом дефолт даёт `POST /api/v1/calc/cards` → 200. Цена на странице = `price` API с округлением `showResult`.
- [x] `curl.exe -s https://insain.ru/catalog/kalkulyator-plastikovyh-kart/` — в HTML есть `calcPlasticCards`, нет `calcApi`.

### Критерии перевода формы ezFC на API

- [ ] URL обновляется GET-именами формы; ссылка с GET открывает форму с теми же значениями и той же ценой.

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

## Найдено вне scope

- Боевой cjsCalc (элемент 2298) пишет ключи `isSignatureStrip ` и `isScratchPanel ` с хвостовым пробелом. На живой форме включённые галки не входят в цену. В `forms/cards.js` ключи без пробела: на 100 шт полоса подписи даёт JS cost 2140 / price 3552.4, скретч — cost 2100 / price 3486. Дефолт обе галки выключены.
- `isEmbossing` в боевом JS закомментирован, поля формы нет. В API параметр необязательный, в запрос не уходит.
- `calcCards.js` не подключён в `scripts/run_js_calc.mjs`. Эталон снят прямым прогоном файла в Node vm. Раннер не менялся.

## Результат

- Ветка, PR или коммит: `task/form-plastic-cards`, коммит git-части перед слиянием в main
- Период: 2026-11-23 — 2026-11-23
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
