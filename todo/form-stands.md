# form-stands

Статус: черновик
Сложность: низкая
Implementer: Grok 4.7
Reviewer: Auto
Site ops: Grok 4.7
Почему: вторая форма уже выкатанного slug `tablets` по skill `ezfc-form-to-api`; лид 36 и копию 120 не пересматривать.

## Цель

Копия формы 48 CalcStands на черновике товара считает `POST /api/v1/calc/tablets`. URL копии пишется GET-именами элементов формы 48. Ссылка с этими GET открывает ту же копию с теми же значениями и той же ценой. Боевая страница https://insain.ru/catalog/kalkulyator-stendov/ остаётся на `insaincalc.calcTablets`. В пакет `forms-batch-switch` форма 48 не попадает.

## Контекст и ссылки

- `.cursor/skills/ezfc-form-to-api/SKILL.md`, этапы `verify.md` и `copy.md`. Шаги 17–24 не входят.
- `docs/ezfc-api-migration.md` — GET = имя элемента. Образец второй формы в одном файле — `wp-plugin/forms/print_sheet.js` (формы 6 и 19).
- `docs/site/forms.md` — строка формы 48, только читать.
- `wp-plugin/forms/tablets.js` — JS лида 36. `calc_service/tests/test_calculators/test_tablets.py` — эталоны лида не сдвигать.
- `js_legacy/calc/calcTablets.js` — эталон; подключён в `scripts/run_js_calc.mjs`.
- `todo/EPIC-forms-to-api.md` — пачка 6. Формы 51, 76, 68 — отдельные задачи после этой.
- Остальное не открывать.

## Scope

- В git (Implementer): JS формы 48 со своими id. `forms/tablets.js` остаётся расчётом формы 36: её id и эталоны лида не менять. Текст формы 48 — в том же файле, блоки `/* form 36 */` и `/* form 48 */`. Без блоков `scripts/ezfc_copy.py` не примет чужие `get_value_from`. Развилка по набору полей формы, не по id копии. Если развилка не собирается без сдвига цены лида — стоп, `заблокировано: аналитик`.
- Дефолт формы 48 сверить с раннером. Сошёлся с текущим `tablets.py` — калькулятор не менять. Не сошёлся — портировать только ветки этого дефолта вызовом уже существующего порта. Порта нет — стоп, `заблокировано: аналитик`. Новые строки в `scripts/js_port_gaps_allowed.txt` не добавлять; снятую строку своего префикса снять, когда ветка сошлась.
- Кейс дефолта формы 48 — отдельная константа в `test_tablets.py` с пометкой `# JS, ДД.ММ.ГГГГ`.
- На проде (Site ops): дубль формы 48 на черновик по skill. JS копии в элементе (`read_file=0`). Плагин не выкладывать. Боевые 48 и 36 не переключать. Копию 120 / 2586916 не править.
- Строка для будущего боевого пакета и дописка для `docs/js-runner-cases.md` — в «Результат».

## Файлы

- `wp-plugin/forms/tablets.js`
- `calc_service/calculators/tablets.py`
- `calc_service/tests/test_calculators/test_tablets.py`
- WordPress: только новая копия формы 48 и её черновик

## Не-scope

- `todo/forms-batch-switch.md`, `docs/site/forms.md`, `docs/js-runner-cases.md`, `scripts/run_js_calc.mjs`
- Копия 120 / 2586916, боевые формы 36, 51, 76, 68
- `shild.py`, `plaque.py`, JSON цен, выкладка плагина, шаги 17–24
- Чужие калькуляторы, кроме вызова уже существующего порта

## Критерии приёмки

Каждый пункт — команда и ожидаемый результат.

- [ ] `python -m pytest calc_service/tests/test_calculators/test_tablets.py calc_service/tests/test_wp_plugin_forms.py -q` — `passed`. Эталоны лида 36 на месте. Есть константа дефолта формы 48 с `# JS,`.
- [ ] `Select-String -Path wp-plugin\forms\tablets.js -Pattern "calcApi\('tablets'|syncUrl\(|showResult\("` — все три есть. Id формы 36 из шапки файла на месте. Есть блоки `/* form 36 */` и `/* form 48 */`.
- [ ] Копия не на витрине: `wp post get <product> --field=post_status` → `draft` или `private`; `curl.exe -s -o NUL -w "%{http_code}"` гостем — не `200`.
- [ ] На копии под админом дефолт даёт `POST /api/v1/calc/tablets` → 200. Цена на странице = `price` API с округлением `showResult`.
- [ ] `curl.exe -s https://insain.ru/catalog/kalkulyator-stendov/` — в HTML есть `calcTablets`, нет `calcApi`.

### Критерии перевода формы ezFC на API

- [ ] URL обновляется GET-именами формы 48; ссылка с GET открывает форму с теми же значениями и той же ценой.

## Проверки

- [ ] `make check` (или `python scripts/dev.py check`) — зелёный вывод
- [ ] Self-review — чеклист «Перед сдачей» в [AGENTS.md](../AGENTS.md)

## Риски

- Прод: дубль только этой копии. Боевые 48 и 36 не меняются. Запись на проде под `lock prod`, не параллельно с другой формой.
- Цены: нет. Эталоны лида не сдвигать.
- Формы: id боевой 48 не менять. id формы 36 в JS не подменять.

## Режим

прод

## Журнал передач

27.11.2026 — человек — завести задачи на оставшиеся формы, реализацию не начинать — дальше Analyst
27.11.2026 — Analyst, Grok 4.7 — черновик второй формы slug `tablets`, форма 48 — дальше человек

## Найдено вне scope

- —

## Результат

- Ветка, PR или коммит:
- Период:
- Часы человека:
- Работа агентов:
- Было / стало:
- Сделано:
- Чем проверено:
- Не сделано и почему:
- Требуется решение:
