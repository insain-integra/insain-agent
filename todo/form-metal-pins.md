# form-metal-pins

Статус: черновик
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

- [ ] `python scripts/js_port_gaps.py calcMetalPins` — пропуск `isPacking` либо снят, либо назван в docstring и остаётся в allowed. `python scripts/js_port_gaps.py --check` печатает `ok`.
- [ ] `python -m pytest calc_service/tests/test_calculators/test_metal_pins.py calc_service/tests/test_wp_plugin_forms.py -q` — `passed`. Есть `REF_FORM_DEFAULT` с `# JS,`.
- [ ] Боевой `POST /api/v1/calc/metal_pins` на теле `REF_FORM_DEFAULT`: `price` и `time_ready` как у JS (допуск цены abs ≤ 0.02 или rel ≤ 0.001, срока rel ≤ 0.001). Если порт ещё не выкачен — пункт после `deploy-api`, копию до него не принимать.
- [ ] `Select-String -Path wp-plugin\forms\metal_pins.js -Pattern "calcApi\('metal_pins'|syncUrl\(|showResult\("` — все три есть. Своей `price` и `querySelector` нет.
- [ ] Копия не на витрине: `wp post get <product> --field=post_status` → `draft` или `private`; `curl.exe -s -o NUL -w "%{http_code}"` гостем — не `200`.
- [ ] На копии под админом дефолт даёт `POST /api/v1/calc/metal_pins` → 200. Цена на странице = `price` API с округлением `showResult`.
- [ ] `curl.exe -s https://insain.ru/catalog/znachki-metallicheskie-s-emalyami/` — в HTML есть `calcMetalPins`, нет `calcApi`.

### Критерии перевода формы ezFC на API

- [ ] URL обновляется GET-именами формы; ссылка с GET открывает форму с теми же значениями и той же ценой.

## Проверки

- [ ] `make check` (или `python scripts/dev.py check`) — зелёный вывод
- [ ] Self-review — чеклист «Перед сдачей» в [AGENTS.md](../AGENTS.md)

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
