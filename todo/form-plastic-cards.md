# form-plastic-cards

Статус: черновик
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

- [ ] `python scripts/js_port_gaps.py calcPlasticCards` — пропуск `isMagneticStripeHiCo` либо снят, либо назван в docstring и остаётся в allowed. `python scripts/js_port_gaps.py --check` печатает `ok`.
- [ ] `python -m pytest calc_service/tests/test_calculators/test_cards.py calc_service/tests/test_wp_plugin_forms.py -q` — `passed`. Есть `REF_FORM_DEFAULT` с `# JS,`.
- [ ] Боевой `POST /api/v1/calc/cards` на теле `REF_FORM_DEFAULT`: `price` и `time_ready` как у JS (допуск цены abs ≤ 0.02 или rel ≤ 0.001, срока rel ≤ 0.001). Если порт ещё не выкачен — пункт после `deploy-api`, копию до него не принимать.
- [ ] `Select-String -Path wp-plugin\forms\cards.js -Pattern "calcApi\('cards'|syncUrl\(|showResult\("` — все три есть. Своей `price` и `querySelector` нет.
- [ ] Копия не на витрине: `wp post get <product> --field=post_status` → `draft` или `private`; `curl.exe -s -o NUL -w "%{http_code}"` гостем — не `200`.
- [ ] На копии под админом дефолт даёт `POST /api/v1/calc/cards` → 200. Цена на странице = `price` API с округлением `showResult`.
- [ ] `curl.exe -s https://insain.ru/catalog/kalkulyator-plastikovyh-kart/` — в HTML есть `calcPlasticCards`, нет `calcApi`.

### Критерии перевода формы ezFC на API

- [ ] URL обновляется GET-именами формы; ссылка с GET открывает форму с теми же значениями и той же ценой.

## Проверки

- [ ] `make check` (или `python scripts/dev.py check`) — зелёный вывод
- [ ] Self-review — чеклист «Перед сдачей» в [AGENTS.md](../AGENTS.md)

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

## Найдено вне scope

- —

## Результат

- Ветка, PR или коммит:
- Период: <ГГГГ-ММ-ДД — ГГГГ-ММ-ДД>
- Часы человека: <оценка N ч — 1 ч на коммит задачи | N ч факт>
- Работа агентов: <N сессий; модели>
- Было / стало: <одна строка с числами — для docs/history/log.md>
- Сделано:
- Чем проверено:
- Не сделано и почему:
- Требуется решение:
