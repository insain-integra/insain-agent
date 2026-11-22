# form-calendar

Статус: черновик
Сложность: низкая
Implementer: Grok 4.7
Reviewer: не нужен
Site ops: Grok 4.7
Почему: лид-копия slug `calendar` по skill `ezfc-form-to-api`; у квартального календаря (`calcCalendarQuarterly`) пропусков в allowed нет.

## Цель

Копия формы 50 CalcCalendarQuarterly на черновике товара считает `POST /api/v1/calc/calendar` в режиме квартального календаря. URL копии пишется GET-именами элементов. Ссылка с этими GET открывает ту же копию с теми же значениями и той же ценой. Боевая страница https://insain.ru/catalog/kalkulyator-kvartalnyh-kalendarej/ остаётся на `insaincalc.calcCalendarQuarterly`. Боевое переключение отложено решением человека 22.11.2026. Формы 52 (перекидной) и 66 (настольный перекидной) — отдельными задачами после приёмки этой копии.

## Контекст и ссылки

- `.cursor/skills/ezfc-form-to-api/SKILL.md`, этапы `verify.md` и `copy.md`. Шаги 17–24 не входят.
- `docs/ezfc-api-migration.md` — GET = имя элемента.
- `docs/site/forms.md` — строка формы 50, только читать.
- `calc_service/calculators/calendar.py` — ветка квартальных; `calc_service/tests/test_calculators/test_calendar.py`.
- `js_legacy/calc/calcCalendar.js`, функция `calcCalendarQuarterly` — эталон дефолта формы.
- `todo/EPIC-forms-to-api.md` — пачка 6.
- Остальное не открывать.

## Scope

- В git (Implementer): шаги 0–5б и `wp-plugin/forms/calendar.js` для формы 50. `REF_FORM_DEFAULT` квартального в `test_calendar.py` с пометкой `# JS, ДД.ММ.ГГГГ`. `calcCalendar.js` в `scripts/run_js_calc.mjs` не подключён — эталон прямым прогоном файла в Node vm, раннер не править.
- Если дефолт формы 50 не сходится с JS — чинить ветку квартальных в `calendar.py` в этой задаче. Ветки перекидного и настольного не трогать. Калькулятор не на боевой форме API, предпосылку не заводить. Новые строки в allowed не добавлять.
- `calendar.js` пишется с привязкой к id формы 50; поддержку форм 52 и 66 не добавлять заранее.
- На проде (Site ops): дубль формы 50 на черновик после совпадения дефолта с боевым API. Если порт менял ответ — сначала `deploy-api` с `main`, потом дубль. JS копии в элементе (`read_file=0`). Плагин не выкладывать. Боевую 50 не переключать.
- Строка для будущего боевого пакета и дописка для `docs/js-runner-cases.md` — в «Результат», не в общие файлы.

## Файлы

- `wp-plugin/forms/calendar.js`
- `calc_service/calculators/calendar.py`
- `calc_service/tests/test_calculators/test_calendar.py`
- WordPress: только копия формы 50 и её черновик

## Не-scope

- `todo/forms-batch-switch.md`, `docs/site/forms.md`, `docs/js-runner-cases.md`, `scripts/run_js_calc.mjs`
- Копии и боевые формы 52 и 66; ветки `calcCalendarFlip` и `calcCalendarTableFlip`; строка `calcCalendarFlip option isLamination` в allowed
- Боевая форма 50 и шаги 17–24, выкладка плагина, JSON цен (в том числе подписи `materials/calendar.json` из `BACKLOG.md`), `calc_service/calculators/__init__.py`. Чужие калькуляторы.

## Критерии приёмки

Каждый пункт — команда и ожидаемый результат.
Скрипт через `@'…'@ | python -` в PowerShell 5.1 — первой строкой `$OutputEncoding = New-Object System.Text.UTF8Encoding $false`, иначе кириллица в нём станет `?`.

- [ ] `python scripts/js_port_gaps.py calcCalendarQuarterly` — непустых `нет в Python` нет. `python scripts/js_port_gaps.py --check` печатает `ok`.
- [ ] `python -m pytest calc_service/tests/test_calculators/test_calendar.py calc_service/tests/test_wp_plugin_forms.py -q` — `passed`. Есть `REF_FORM_DEFAULT` квартального с `# JS,`; эталоны перекидного и настольного не сдвинулись.
- [ ] Боевой `POST /api/v1/calc/calendar` на теле `REF_FORM_DEFAULT`: `price` и `time_ready` как у JS (допуск цены abs ≤ 0.02 или rel ≤ 0.001, срока rel ≤ 0.001). Если порт ещё не выкачен — пункт после `deploy-api`, копию до него не принимать.
- [ ] `Select-String -Path wp-plugin\forms\calendar.js -Pattern "calcApi\('calendar'|syncUrl\(|showResult\("` — все три есть. Своей `price` и `querySelector` нет.
- [ ] Копия не на витрине: `wp post get <product> --field=post_status` → `draft` или `private`; `curl.exe -s -o NUL -w "%{http_code}"` гостем — не `200`.
- [ ] На копии под админом дефолт даёт `POST /api/v1/calc/calendar` → 200. Цена на странице = `price` API с округлением `showResult`.
- [ ] `curl.exe -s https://insain.ru/catalog/kalkulyator-kvartalnyh-kalendarej/` — в HTML есть `calcCalendarQuarterly`, нет `calcApi`.

### Критерии перевода формы ezFC на API

- [ ] URL обновляется GET-именами формы; ссылка с GET открывает форму с теми же значениями и той же ценой.

## Проверки

- [ ] `make check` (или `python scripts/dev.py check`) — зелёный вывод
- [ ] Self-review — чеклист «Перед сдачей» в [AGENTS.md](../AGENTS.md)

## Риски

- Прод: боевые формы 50, 52, 66 не меняются. Выкатка API — только если менялся калькулятор, с `main`. Запись в формы не параллельно с `todo/ezfc-options-source-reset.md`.
- Цены: JSON не менять.
- Формы: id боевой 50 не менять; копия — новая форма на черновике.

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
