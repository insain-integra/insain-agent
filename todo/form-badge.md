# form-badge

Статус: черновик
Сложность: средняя
Implementer: Gemini 4 Hydrogen High
Reviewer: Grok 4.7
Site ops: Grok 4.7
Почему: лид-копия slug `badge` на пять боевых форм; 13 пропусков `calcBadge` в allowed и известное расхождение срока и веса (`BACKLOG.md`, из `form-laser`) — порт может понадобиться в том же diff.

## Цель

Выбрана лид-форма slug `badge` по сверке порта, и её копия на черновике товара считает `POST /api/v1/calc/badge`. Кандидат — форма 64 CalcBadge; другая форма из 31, 60, 61, 84 берётся лидом, только если сверка показала у неё меньше расхождений. URL копии пишется GET-именами элементов. Ссылка с этими GET открывает ту же копию с теми же значениями и той же ценой. Все боевые формы `calcBadge` остаются на старом JS. Боевое переключение отложено решением человека 22.11.2026. Остальные четыре формы slug — отдельными задачами после приёмки этой копии.

## Контекст и ссылки

- `.cursor/skills/ezfc-form-to-api/SKILL.md`, этапы `verify.md` и `copy.md`. Шаги 17–24 не входят.
- `docs/ezfc-api-migration.md` — GET = имя элемента.
- `docs/site/forms.md` — строки форм 31, 60, 61, 64, 84 (`insaincalc.calcBadge`), только читать.
- `calc_service/calculators/badge.py`, `calc_service/tests/test_calculators/test_badge.py`.
- `js_legacy/calc/calcBadge.js` — эталон; подключён в `scripts/run_js_calc.mjs`.
- `scripts/js_port_gaps_allowed.txt` — строки `calcBadge` (13 штук).
- `BACKLOG.md` — строка «Из `form-laser`: `badge.py`: `time_ready` … вес …», только читать.
- `todo/EPIC-forms-to-api.md` — пачка 5.
- Остальное не открывать.

## Scope

- В git (Implementer), сверка: раннер против `badge.py` на дефолтах всех пяти форм (31, 60, 61, 64, 84). Итог — таблица «форма → `price` / `time_ready` JS и API, какие пропуски задевает» в «Результат». Лид — форма 64, если её дефолт сходится или упирается в меньше пропусков, чем у других; иначе форма с наименьшим числом пропусков. Выбор и причина — строка в журнале.
- В git (Implementer), лид: шаги 0–5б для лид-формы и `wp-plugin/forms/badge.js` с привязкой к её id. `REF_FORM_DEFAULT` в `test_badge.py` с пометкой `# JS, ДД.ММ.ГГГГ`. Портировать в `badge.py` только ветки, без которых дефолт лида не сходится по цене и сроку, и снять их строки из allowed. Вызов в JS — вызов уже существующего порта в Python (`poly_sticker`, `cut_*`, `lamination`), чужие калькуляторы не менять. Если дефолту лида нужен вызов, у которого порта в Python нет (`calcManualRoll`, `calcEpoxy`, `calcSetSticker`, `calcPocket`), — стоп со статусом `заблокировано: аналитик`. Калькулятор не на боевой форме API, предпосылку не заводить. Новые строки в allowed не добавлять.
- На проде (Site ops): дубль лид-формы на черновик после совпадения дефолта с боевым API. Если порт менял ответ — сначала `deploy-api` с `main`, потом дубль. JS копии в элементе (`read_file=0`). Плагин не выкладывать. Боевые формы не переключать.
- Строка для будущего боевого пакета и дописка для `docs/js-runner-cases.md` — в «Результат», не в общие файлы.

## Файлы

- `wp-plugin/forms/badge.js`
- `calc_service/calculators/badge.py`
- `calc_service/tests/test_calculators/test_badge.py`
- `scripts/js_port_gaps_allowed.txt` — только снять строки `calcBadge`, если ветка портирована
- WordPress: только копия лид-формы и её черновик

## Не-scope

- `todo/forms-batch-switch.md`, `docs/site/forms.md`, `docs/js-runner-cases.md`, `scripts/run_js_calc.mjs`, `BACKLOG.md`
- Копии остальных четырёх форм `calcBadge`; ветки, которые дефолт лида не вызывает
- `uv_badge.py` (`calcUVBadge`) и прочие чужие калькуляторы и их тесты
- Боевые формы 31, 60, 61, 64, 84 и шаги 17–24, выкладка плагина, JSON цен, `calc_service/calculators/__init__.py`

## Критерии приёмки

Каждый пункт — команда и ожидаемый результат.
Скрипт через `@'…'@ | python -` в PowerShell 5.1 — первой строкой `$OutputEncoding = New-Object System.Text.UTF8Encoding $false`, иначе кириллица в нём станет `?`.

- [ ] В «Результат» есть таблица сверки дефолтов пяти форм (`price` / `time_ready` JS и API, задетые пропуски), в журнале — строка с выбранной лид-формой и причиной.
- [ ] `python scripts/js_port_gaps.py calcBadge` — каждый пропуск либо снят, либо назван в docstring и остаётся в allowed. `python scripts/js_port_gaps.py --check` печатает `ok`.
- [ ] `python -m pytest calc_service/tests/test_calculators/test_badge.py calc_service/tests/test_wp_plugin_forms.py -q` — `passed`. Есть `REF_FORM_DEFAULT` с `# JS,`; прежние эталоны `test_badge.py` не сдвинулись или сдвиг объяснён раннером в «Результат».
- [ ] Боевой `POST /api/v1/calc/badge` на теле `REF_FORM_DEFAULT`: `price` и `time_ready` как у раннера (допуск цены abs ≤ 0.02 или rel ≤ 0.001, срока rel ≤ 0.001). Если порт ещё не выкачен — пункт после `deploy-api`, копию до него не принимать.
- [ ] `Select-String -Path wp-plugin\forms\badge.js -Pattern "calcApi\('badge'|syncUrl\(|showResult\("` — все три есть. Своей `price` и `querySelector` нет.
- [ ] Копия не на витрине: `wp post get <product> --field=post_status` → `draft` или `private`; `curl.exe -s -o NUL -w "%{http_code}"` гостем — не `200`.
- [ ] На копии под админом дефолт даёт `POST /api/v1/calc/badge` → 200. Цена на странице = `price` API с округлением `showResult`.
- [ ] `curl.exe -s` по каждой боевой странице лид-формы из `docs/site/forms.md` (для 64 — https://insain.ru/catalog/bejdzhi-s-uf-pechatyu/ и https://insain.ru/catalog/bejdzhi-s-lazernoj-gravirovkoj/) — в HTML есть `calcBadge`, нет `calcApi`.

### Критерии перевода формы ezFC на API

- [ ] URL обновляется GET-именами формы; ссылка с GET открывает форму с теми же значениями и той же ценой.

## Проверки

- [ ] `make check` (или `python scripts/dev.py check`) — зелёный вывод
- [ ] Self-review — чеклист «Перед сдачей» в [AGENTS.md](../AGENTS.md)

## Риски

- Прод: боевые формы `calcBadge` не меняются. Выкатка API — только если менялся калькулятор, с `main` после ревью. Запись в формы не параллельно с `todo/ezfc-options-source-reset.md`.
- Цены: JSON не менять. Порт веток может сдвинуть ответ `badge` для других форм — прежние эталоны теста держат это.
- Формы: id боевых форм не менять; копия — новая форма на черновике.

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
