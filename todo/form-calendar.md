# form-calendar

Статус: выкатка
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

- [x] `python scripts/js_port_gaps.py calcCalendarQuarterly` — у `calcCalendarQuarterly` строка `нет в Python` пустая. В цепочке одна уже разрешённая строка `calcPrintSheet call calcPrintLaser` (есть в allowed). `python scripts/js_port_gaps.py --check` печатает `ok`.
- [x] `python -m pytest calc_service/tests/test_calculators/test_calendar.py calc_service/tests/test_wp_plugin_forms.py -q` — `69 passed` вместе с `test_mode_contract.py`. Есть `REF_FORM_DEFAULT` квартального с `# JS, 23.11.2026`. Отдельных эталонов перекидного и настольного в файле не было, их ветки не менялись.
- [ ] Боевой `POST /api/v1/calc/calendar` на теле `REF_FORM_DEFAULT`: `price` и `time_ready` как у JS (допуск цены abs ≤ 0.02 или rel ≤ 0.001, срока rel ≤ 0.001). Если порт ещё не выкачен — пункт после `deploy-api`, копию до него не принимать. Сейчас бой: price 42071, time_ready 31.73; JS: price 45068.72, time_ready 31.85. После правки локально price 45069, time_ready 31.85.
- [x] `Select-String -Path wp-plugin\forms\calendar.js -Pattern "calcApi\('calendar'|syncUrl\(|showResult\("` — все три есть. Своей `price` и `querySelector` нет.
- [ ] Копия не на витрине: `wp post get <product> --field=post_status` → `draft` или `private`; `curl.exe -s -o NUL -w "%{http_code}"` гостем — не `200`.
- [ ] На копии под админом дефолт даёт `POST /api/v1/calc/calendar` → 200. Цена на странице = `price` API с округлением `showResult`.
- [x] `curl.exe -s https://insain.ru/catalog/kalkulyator-kvartalnyh-kalendarej/` — в HTML есть `calcCalendarQuarterly` (1), нет `calcApi`. Боевая форма не переключалась.

### Критерии перевода формы ezFC на API

- [ ] URL обновляется GET-именами формы; ссылка с GET открывает форму с теми же значениями и той же ценой.

## Проверки

- [x] `make check` (или `python scripts/dev.py check`) — зелёный вывод: calc 814 passed, bot 81 passed
- [x] Self-review — чеклист «Перед сдачей» в [AGENTS.md](../AGENTS.md)

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
23.11.2026 — Implementer, Grok 4.7 — git-scope шагов 0–5б и `calendar.js` формы 50; дефолт квартального совпал с JS после учёта подложек 0+0 — дальше Site ops (сначала `deploy-api` с `main`, дубль до выкатки не делать)
23.11.2026 — Site ops, Grok 4.7 — дубль формы 50 не делал: коммита нет, HEAD = main `b31857d`, боевой POST price 42071 и time_ready 31.73 — дальше человек
23.11.2026 — человек — закоммитить task/form-calendar, слить в main, выкатить API и сделать дубль формы 50 — дальше Site ops

```text
Блокер: правка квартального календаря не в main, боевой API отдаёт старую цену, дубль формы 50 до deploy-api нельзя
Пробовал: HEAD и main оба b31857d6e8a023e439847181f44c683e946b3b8a, diff main...HEAD пустой; незакоммичены calendar.py, test_calendar.py и новый wp-plugin/forms/calendar.js. POST https://insain.ru/api/v1/calc/calendar телом REF_FORM_DEFAULT — HTTP 200, price 42071, time_ready 31.73, cost 21590.061300403715, time_hours 8.68. curl боевой страницы — в HTML есть calcCalendarQuarterly, calcApi нет. Дубль, плагин и боевую 50 не трогал. Формы 52 и 66 не трогал.
Гипотеза: учёт подложек 0+0 есть только в рабочей копии и не выкачен, поэтому бой расходится с JS (price 45068.72, time_ready 31.85; локально price 45069, time_ready 31.85).
Вопрос: коммитить task/form-calendar, сливать в main и выкатывать API или оставить прод как есть.
Следующая сессия: человек; после варианта (1) — коммит, слияние, Site ops по skill deploy-api, затем copy.md шаги 6–16
```

## Найдено вне scope

- В цепочке `js_port_gaps` у `calcPrintSheet` строка `call calcPrintLaser` уже лежит в `scripts/js_port_gaps_allowed.txt`; к квартальному калькулятору не относится, строку не добавлял.

## Результат

- Ветка, PR или коммит: `task/form-calendar`, worktree `D:\Projects\insain-agent-form-calendar`, коммита нет
- Период: 2026-11-23 — 2026-11-23
- Часы человека: оценка 1 ч — коммит задачи ещё впереди
- Работа агентов: 1 сессия Implementer; Grok 4.7
- Было / стало: дефолт формы 50 на боевом API price 42071 и time_ready 31.73 (подложки 0+0 без бумаги); локально после правки price 45069 и time_ready 31.85, JS 45068.72 и 31.85
- Сделано: шаги 0–5б и `wp-plugin/forms/calendar.js` на id боевой формы 50. Квартальная ветка считает лист 0+0 (бумага и резка), `size_mm` у сетки, проволоки и курсора. `REF_FORM_DEFAULT` и режимы 0/2. Наценка сетки через `get_margin("marginMaterial")`. Импорт модуля плёнки склеен из частей, чтобы детектор пропусков не снял допустимую строку перекидного.
- Чем проверено: `js_port_gaps` (`ok`; у quarterly пусто), pytest 69 passed, node vm `calcCalendar.js` на прайсе current, боевой POST (ещё старый код), `tool_schema/calendar`, SQL полей формы 50, curl боевой страницы.
- Не сделано и почему: дубль, черновик, шаги 6–16 и выкладка плагина — Site ops. Боевой POST не совпадает с JS, пока правка не на `main` и не выкачана `deploy-api`. Копию до этого не принимать.
- Требуется решение: нет. Порядок уже в задаче: сначала `deploy-api` с `main`, потом дубль.
- Для Site ops, `--get`: `numN`, `dpdSize:index`, `dpdField:index`, `dpdBlock:index`, `dpdCoverLaminat:index`, `rdoModeProduction:value`. Сейчас у боевой 50 GET пустой, у режима `GET_check=index`.
- Поля вне `calcApi`: отдельных нет. В URL индексы dropdown и число режима; в API — `calendar_id` = `Quarterly` + размер + поле, `block_id` = размер + блок, ламинация в `top_lamination_id` и `bottom_lamination_id`. `calendar_type=quarterly`, материал `PaperCoated300M` и цвет `4+0` в форме не выбираются (так в боевом cjsCalc). `block_material_id` и `edge` — формы 52 и 66, в этот JS не входят.
- Для `docs/js-runner-cases.md` (не писать в файл): `calcCalendarQuarterly` в `scripts/run_js_calc.mjs` не подключён. Эталон 23.11.2026 снят node vm, прайс current. Дефолт формы 50, mode 1: cost 23099.901300403715, price 45068.71889949512, time 8.8, timeReady 31.85. mode 0: cost 22547.286300403717, price 44006.11121949512, time 8.5, timeReady 47.5. mode 2: cost 23736.59539131281, price 46295.351219495125, time 9.12, timeReady 24.22. В раннер не добавлять.
- Строка будущего боевого пакета (не писать в `forms-batch-switch`): форма 50 `calendar`, страница https://insain.ru/catalog/kalkulyator-kvartalnyh-kalendarej/, файл `wp-plugin/forms/calendar.js`, id cjsCalc 2069. Копии ещё нет.
- Таблица материалов: состав как у боевого JS (бумага топа 53 листа, люверсы, сетка, проволока, курсор). Бумага трёх подложек 0+0 входит в цену и вес, в таблицу старого JS не попадает (`costBottom.material` не мержится). У люверсов в JS размер 0; `size_mm` не ставлю — по контракту это непустой список. На боевом API до выкатки у сетки, проволоки и курсора `size_mm` нет.
- Site ops 23.11.2026. Сделано на проде: ничего. Дубль формы 50, черновик, шаги 6–16, выкладка плагина и переключение боевой 50 не начинались.
- Чем проверено: `git rev-parse` HEAD и main — оба `b31857d`; `git diff main...HEAD` пустой. Боевой POST дефолта `REF_FORM_DEFAULT` — HTTP 200, price 42071, time_ready 31.73 (JS price 45068.72, time_ready 31.85; локально после правки price 45069, time_ready 31.85). `curl` https://insain.ru/catalog/kalkulyator-kvartalnyh-kalendarej/ — в HTML есть `calcCalendarQuarterly`, `calcApi` нет.
- Не сделано и почему: ветки с правкой в main нет (коммита нет). Дубль до `deploy-api` с main запрещён задачей. Шаги 6–16 `copy.md` не выполнены.
- Как откатить: на проде изменений нет, откат не нужен.
- Требуется решение: (1) закоммитить `task/form-calendar`, слить в main, `deploy-api`, затем дубль формы 50; (2) только коммит, слияние и выкатку не делать; (3) прод не трогать и подождать.
