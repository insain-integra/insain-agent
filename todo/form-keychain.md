# form-keychain

Статус: черновик
Сложность: низкая
Implementer: Grok 4.7
Reviewer: не нужен
Site ops: Grok 4.7
Почему: копия формы по skill `ezfc-form-to-api`, калькулятор `keychain` уже в API, пропусков порта в allowed нет.

## Цель

Копия формы 74 CalcАcrylicKeychains на черновике товара считает `POST /api/v1/calc/keychain`. URL копии пишется GET-именами элементов. Ссылка с этими GET открывает ту же копию с теми же значениями и той же ценой. Боевая страница https://insain.ru/catalog/kalkulyator-akrilovyh-brelokov/ остаётся на `insaincalc.calcAcrylicKeychain`. Боевое переключение отложено решением человека 22.11.2026.

## Контекст и ссылки

- `.cursor/skills/ezfc-form-to-api/SKILL.md`, этапы `verify.md` и `copy.md`. Шаги 17–24 не входят.
- `docs/ezfc-api-migration.md` — GET = имя элемента.
- `docs/site/forms.md` — строка формы 74, только читать.
- `calc_service/calculators/keychain.py`, `calc_service/tests/test_calculators/test_keychain.py`.
- `js_legacy/calc/calcKeychain.js`, функция `calcAcrylicKeychain` — эталон дефолта формы.
- `todo/EPIC-forms-to-api.md` — пачка 7.
- Остальное не открывать.

## Scope

- В git (Implementer): шаги 0–5б и `wp-plugin/forms/keychain.js`. `REF_FORM_DEFAULT` в `test_keychain.py` с пометкой `# JS, ДД.ММ.ГГГГ`. `calcKeychain.js` в `scripts/run_js_calc.mjs` не подключён — эталон прямым прогоном файла в Node vm, раннер не править.
- Если дефолт формы не сходится с JS — чинить в `keychain.py` в этой задаче. Калькулятор не на боевой форме API, предпосылку не заводить. Новые строки в allowed не добавлять.
- На проде (Site ops): дубль формы 74 на черновик после совпадения дефолта с боевым API. Если порт менял ответ — сначала `deploy-api` с `main`, потом дубль. JS копии в элементе (`read_file=0`). Плагин не выкладывать. Боевую 74 не переключать.
- Строка для будущего боевого пакета и дописка для `docs/js-runner-cases.md` — в «Результат», не в общие файлы.

## Файлы

- `wp-plugin/forms/keychain.js`
- `calc_service/calculators/keychain.py`
- `calc_service/tests/test_calculators/test_keychain.py`
- WordPress: только копия формы 74 и её черновик

## Не-scope

- `todo/forms-batch-switch.md`, `docs/site/forms.md`, `docs/js-runner-cases.md`, `scripts/run_js_calc.mjs`
- Боевая форма 74 и шаги 17–24, выкладка плагина, JSON цен, `calc_service/calculators/__init__.py`
- `scripts/js_port_gaps_allowed.txt`. Чужие калькуляторы, в том числе `magnets.py` (`magnet_acrylic`).

## Критерии приёмки

Каждый пункт — команда и ожидаемый результат.
Скрипт через `@'…'@ | python -` в PowerShell 5.1 — первой строкой `$OutputEncoding = New-Object System.Text.UTF8Encoding $false`, иначе кириллица в нём станет `?`.

- [ ] `python scripts/js_port_gaps.py calcAcrylicKeychain` — непустых `нет в Python` нет. `python scripts/js_port_gaps.py --check` печатает `ok`.
- [ ] `python -m pytest calc_service/tests/test_calculators/test_keychain.py calc_service/tests/test_wp_plugin_forms.py -q` — `passed`. Есть `REF_FORM_DEFAULT` с `# JS,`.
- [ ] Боевой `POST /api/v1/calc/keychain` на теле `REF_FORM_DEFAULT`: `price` и `time_ready` как у JS (допуск цены abs ≤ 0.02 или rel ≤ 0.001, срока rel ≤ 0.001). Если порт ещё не выкачен — пункт после `deploy-api`, копию до него не принимать.
- [ ] `Select-String -Path wp-plugin\forms\keychain.js -Pattern "calcApi\('keychain'|syncUrl\(|showResult\("` — все три есть. Своей `price` и `querySelector` нет.
- [ ] Копия не на витрине: `wp post get <product> --field=post_status` → `draft` или `private`; `curl.exe -s -o NUL -w "%{http_code}"` гостем — не `200`.
- [ ] На копии под админом дефолт даёт `POST /api/v1/calc/keychain` → 200. Цена на странице = `price` API с округлением `showResult`.
- [ ] `curl.exe -s https://insain.ru/catalog/kalkulyator-akrilovyh-brelokov/` — в HTML есть `calcAcrylicKeychain`, нет `calcApi`.

### Критерии перевода формы ezFC на API

- [ ] URL обновляется GET-именами формы; ссылка с GET открывает форму с теми же значениями и той же ценой.

## Проверки

- [ ] `make check` (или `python scripts/dev.py check`) — зелёный вывод
- [ ] Self-review — чеклист «Перед сдачей» в [AGENTS.md](../AGENTS.md)

## Риски

- Прод: боевая форма 74 не меняется. Выкатка API — только если менялся калькулятор, с `main`. Запись в формы не параллельно с `todo/ezfc-options-source-reset.md`.
- Цены: JSON не менять.
- Формы: id боевой 74 не менять; копия — новая форма на черновике.

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
