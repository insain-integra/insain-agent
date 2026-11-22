# form-tablets

Статус: черновик
Сложность: средняя
Implementer: Gemini 4 Hydrogen High
Reviewer: Grok 4.7
Site ops: Grok 4.7
Почему: лид-копия slug `tablets` на пять боевых форм (с формой 68); 14 пропусков `calcTablets` в allowed, часть — вызовы чужих калькуляторов; порт может понадобиться в том же diff.

## Цель

Копия формы 36 CalcTabs на черновике товара считает `POST /api/v1/calc/tablets`. URL копии пишется GET-именами элементов. Ссылка с этими GET открывает ту же копию с теми же значениями и той же ценой. Боевая страница https://insain.ru/catalog/tablichki-s-uf-pechatyu/ остаётся на `insaincalc.calcTablets`. Боевое переключение отложено решением человека 22.11.2026. Формы 48, 51, 76 и 68 — отдельными задачами после приёмки этой копии. Форма 68 CalcShild вызывает `calcTablets` и переводится через slug `tablets`, не `shild` (решение человека 22.11.2026).

## Контекст и ссылки

- `.cursor/skills/ezfc-form-to-api/SKILL.md`, этапы `verify.md` и `copy.md`. Шаги 17–24 не входят.
- `docs/ezfc-api-migration.md` — GET = имя элемента.
- `docs/site/forms.md` — строки форм 36, 48, 51, 68, 76 (`insaincalc.calcTablets`), только читать.
- `calc_service/calculators/tablets.py`, `calc_service/tests/test_calculators/test_tablets.py`.
- `js_legacy/calc/calcTablets.js`, функция `calcTablets` — эталон; подключён в `scripts/run_js_calc.mjs`.
- `scripts/js_port_gaps_allowed.txt` — строки `calcTablets` (14 штук).
- `todo/EPIC-forms-to-api.md` — пачка 6.
- Остальное не открывать.

## Scope

- В git (Implementer), сверка: раннер против `tablets.py` на дефолтах форм 36, 48, 51, 76 и 68. Итог — таблица «форма → `price` / `time_ready` JS и API, какие пропуски задевает» в «Результат»; для 68 — отдельная строка, что она идёт через `tablets`.
- В git (Implementer), лид: шаги 0–5б для формы 36 и `wp-plugin/forms/tablets.js` с привязкой к id 36. `REF_FORM_DEFAULT` в `test_tablets.py` с пометкой `# JS, ДД.ММ.ГГГГ`. Портировать в `tablets.py` только ветки, без которых дефолт формы 36 не сходится по цене и сроку, и снять их строки из allowed. Вызов в JS — вызов уже существующего порта в Python (`milling`, `print_roll`, `sticker`, `cut_roller`); чужие калькуляторы не менять. Если дефолту формы 36 нужен вызов, у которого порта в Python нет (`calcManualRoll`, `calcPockets`, `calcFrame`), — стоп со статусом `заблокировано: аналитик`. Калькулятор не на боевой форме API, предпосылку не заводить. Новые строки в allowed не добавлять.
- На проде (Site ops): дубль формы 36 на черновик после совпадения дефолта с боевым API. Если порт менял ответ — сначала `deploy-api` с `main`, потом дубль. JS копии в элементе (`read_file=0`). Плагин не выкладывать. Боевую 36 не переключать.
- Строка для будущего боевого пакета и дописка для `docs/js-runner-cases.md` — в «Результат», не в общие файлы.

## Файлы

- `wp-plugin/forms/tablets.js`
- `calc_service/calculators/tablets.py`
- `calc_service/tests/test_calculators/test_tablets.py`
- `scripts/js_port_gaps_allowed.txt` — только снять строки `calcTablets`, если ветка портирована
- WordPress: только копия формы 36 и её черновик

## Не-scope

- `todo/forms-batch-switch.md`, `docs/site/forms.md`, `docs/js-runner-cases.md`, `scripts/run_js_calc.mjs`
- Копии форм 48, 51, 76, 68; ветки, которые дефолт формы 36 не вызывает; модули `calcPockets`, `calcPutTape`, `calcFrame`
- `shild.py` (`calcShild.js`), `plaque.py` (`calcPlaque` из того же `calcTablets.js`), `puzzle.py` и строки `calcPuzzle` / `calcShildSublimaton` в allowed
- Чужие калькуляторы `milling.py`, `print_roll.py`, `sticker.py`, `cut_roller.py` и их тесты
- Боевые формы 36, 48, 51, 68, 76 и шаги 17–24, выкладка плагина, JSON цен, `calc_service/calculators/__init__.py`

## Критерии приёмки

Каждый пункт — команда и ожидаемый результат.
Скрипт через `@'…'@ | python -` в PowerShell 5.1 — первой строкой `$OutputEncoding = New-Object System.Text.UTF8Encoding $false`, иначе кириллица в нём станет `?`.

- [ ] В «Результат» есть таблица сверки дефолтов форм 36, 48, 51, 76, 68 (`price` / `time_ready` JS и API, задетые пропуски).
- [ ] `python scripts/js_port_gaps.py calcTablets` — каждый пропуск либо снят, либо назван в docstring и остаётся в allowed. `python scripts/js_port_gaps.py --check` печатает `ok`.
- [ ] `python -m pytest calc_service/tests/test_calculators/test_tablets.py calc_service/tests/test_calculators/test_plaque.py calc_service/tests/test_wp_plugin_forms.py -q` — `passed`. Есть `REF_FORM_DEFAULT` с `# JS,`; эталоны `plaque` и прежние эталоны `tablets` не сдвинулись или сдвиг объяснён раннером в «Результат».
- [ ] Боевой `POST /api/v1/calc/tablets` на теле `REF_FORM_DEFAULT`: `price` и `time_ready` как у раннера (допуск цены abs ≤ 0.02 или rel ≤ 0.001, срока rel ≤ 0.001). Если порт ещё не выкачен — пункт после `deploy-api`, копию до него не принимать.
- [ ] `Select-String -Path wp-plugin\forms\tablets.js -Pattern "calcApi\('tablets'|syncUrl\(|showResult\("` — все три есть. Своей `price` и `querySelector` нет.
- [ ] Копия не на витрине: `wp post get <product> --field=post_status` → `draft` или `private`; `curl.exe -s -o NUL -w "%{http_code}"` гостем — не `200`.
- [ ] На копии под админом дефолт даёт `POST /api/v1/calc/tablets` → 200. Цена на странице = `price` API с округлением `showResult`.
- [ ] `curl.exe -s https://insain.ru/catalog/tablichki-s-uf-pechatyu/` — в HTML есть `calcTablets`, нет `calcApi`.

### Критерии перевода формы ezFC на API

- [ ] URL обновляется GET-именами формы; ссылка с GET открывает форму с теми же значениями и той же ценой.

## Проверки

- [ ] `make check` (или `python scripts/dev.py check`) — зелёный вывод
- [ ] Self-review — чеклист «Перед сдачей» в [AGENTS.md](../AGENTS.md)

## Риски

- Прод: боевые формы `calcTablets` не меняются. Выкатка API — только если менялся калькулятор, с `main` после ревью. Запись в формы не параллельно с `todo/ezfc-options-source-reset.md`.
- Цены: JSON не менять. Порт веток может сдвинуть ответ `tablets` для форм 48, 51, 76, 68 — прежние эталоны теста держат это.
- Формы: id боевой 36 не менять; копия — новая форма на черновике.

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
