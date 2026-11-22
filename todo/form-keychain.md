# form-keychain

Статус: выкатка
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

23.11.2026 — Implementer, Grok 4.7 — дефолт формы локально совпал с JS, JS копии в ветке; боевой API ещё старый (5715.6 / 17.61 ч) — дальше человек

Блокер: боевой `POST /api/v1/calc/keychain` на дефолте формы отдаёт старый расчёт (price 5715.6, time_ready 17.61). JS и локальный код после правки: price 5743.30 (Python 5742.6, rel 0.00012), time_ready 17.65. Копию до выкатки принимать нельзя.
Пробовал: Node vm `calcAcrylicKeychain(100, KeychainAcrylic3939, "4+4", {}, mode)` на прайсе `calc_service/data`; локальный `KeychainCalculator`; боевой API тем же телом `REF_FORM_DEFAULT` и mode 0/2.
Гипотеза: правка `keychain.py` и `print_laser.py` есть только в `task/form-keychain`, на прод не выкатана.
Вопрос: сливать ветку в `main` и выкатывать API до дубля формы 74?
Варианты:
1. Слить `task/form-keychain` в `main`, выкатить API (`deploy-api`), затем Site ops делает черновик-копию формы 74 (Рекомендуется).
2. Ветку не сливать и API не выкатывать; копию не создавать.
3. Откатить правки калькуляторов и оставить только `wp-plugin/forms/keychain.js` — копия пойдёт в старый API и не пройдёт допуск цены и срока.
Следующая сессия: человек, затем Site ops (после выкатки)

23.11.2026 — человек — слить task/form-keychain в main, выкатить API, затем черновик-копия формы 74 — дальше Site ops

## Найдено вне scope

- Подпись `PaperCoated115M`: legacy «113г/м», текущий каталог «115г/м». Код, лист 320×450 и количество совпадают.
- Тираж 50, цветность «4+0»: срок Python 16.95 ч против JS 16.97 ч — `cut_plotter` округляет время через `round`, JS через `ceil`. Дефолт формы (100 шт, «4+4») по сроку совпал.
- Вес JS на дефолте 0.12 кг без заготовки; API 1.27 кг с заготовкой.
- `print_laser` по-прежнему отдаёт `price` как `int()`: на дефолте формы 5742.6 против JS 5743.30, rel 0.00012.

## Результат

- Ветка, PR или коммит: `task/form-keychain` сливается в `main` по решению человека 23.11.2026; в коммите порт дефолта и `wp-plugin/forms/keychain.js`. `print_laser.py` входит в тот же коммит: без округления срока вверх дефолт не совпадает с JS.
- Период: 2026-11-23 — 2026-11-23
- Часы человека: оценка 1 ч — 1 ч на коммит задачи | факт: человек не коммитил
- Работа агентов: 1 сессия Implementer; Grok 4.7
- Было / стало: дефолт формы 74 локально price 5715.6 → 5742.6 (JS 5743.30), time_ready 17.61 → 17.65; боевой API ещё 5715.6 / 17.61; дубля формы нет
- Сделано: шаги 0–5б. Порт `calcAcrylicKeychain` без пустых «нет в Python». Дефолт формы 74: тираж 100, `KeychainAcrylic3939`, цветность «4+4» → API `color: 2`, упаковка всегда, mode 1. В `keychain.py` резка вставки с `is_find_mark`, у заготовки и зиплока есть `size_mm`. Срок лазерной печати — `ceil`, как в JS. `REF_FORM_DEFAULT` и mode 0/2 в `test_keychain.py`. `wp-plugin/forms/keychain.js` на id боевой 74: `syncUrl` именами `numN`, `dpdBlank`, `dpdColor`, `rdoModeProduction`; `calcApi('keychain')`; `showResult`. Боевая страница по-прежнему на `calcAcrylicKeychain`, без `calcApi`.
- Поля не в API: `fluAtrwork` (файл) — не в `syncUrl` и не в `calcApi`. `is_packing` поля нет, в запрос уходит `true` (старый JS всегда пакует). Параметр не обязателен.
- Строка будущего боевого пакета: форма 74, slug `keychain`, страница https://insain.ru/catalog/kalkulyator-akrilovyh-brelokov/ — копия ещё не создана, боевая на `insaincalc.calcAcrylicKeychain`.
- Дописка для `docs/js-runner-cases.md`: `calcKeychain.js` в `scripts/run_js_calc.mjs` не подключён. Эталон — тот же раннер после добавления `js_legacy/calc/calcKeychain.js`, `js_legacy/material/keychain.json` и `calc_service/data/materials/keychain.json` (файл раннера не менять): `node scripts/run_js_calc.mjs calcAcrylicKeychain --data current --args '[100,"KeychainAcrylic3939","4+4",{},1]'`. mode 0 и 2 — последний аргумент `0` и `2`. В JS цветность строка «4+4», не число 2.
- Чем проверено: `python scripts/js_port_gaps.py calcAcrylicKeychain` — пустых «нет в Python» нет; `python scripts/js_port_gaps.py --check` — `ok`. `python -m pytest calc_service/tests/test_calculators/test_keychain.py calc_service/tests/test_calculators/test_print_laser.py calc_service/tests/test_wp_plugin_forms.py calc_service/tests/test_mode_contract.py calc_service/tests/test_calculators/test_sticker.py -q` — 114 passed. `python scripts/dev.py check` — exit 0, 813 passed и 81 passed. `Select-String` по `keychain.js` — есть `calcApi('keychain'`, `syncUrl(`, `showResult(`; `querySelector` и `price =` нет. Боевой API дефолта: price 5715.6, time_ready 17.61 (mode 0: 4927.6 / 33.23; mode 2: 6539.6 / 10.01). `curl` страницы брелоков: в HTML есть `calcAcrylicKeychain`, нет `calcApi`.
- Не сделано и почему: дубль формы, черновик товара, запись JS в копию и приёмка URL — Site ops, шаги 6–16. До них нужна выкатка API с `main`: локальный дефолт с JS сошёлся, боевой API ещё старый. Плагин не выкладывался. Боевая форма 74 не переключалась. Коммита нет.
- Требуется решение: см. варианты в журнале. Без выкатки копию не принимать.
