# form-poly-badge

Статус: черновик
Сложность: низкая
Implementer: Grok 4.7
Reviewer: Auto
Site ops: Grok 4.7
Почему: вторая форма уже выкатанного slug `badge` по skill `ezfc-form-to-api`; лид 64 и копию 114 не пересматривать.

## Цель

Копия формы 31 CalcPolyBadge на черновике товара считает `POST /api/v1/calc/badge`. URL копии пишется GET-именами элементов формы 31. Ссылка с этими GET открывает ту же копию с теми же значениями и той же ценой. Боевая страница https://insain.ru/catalog/bejdzhi-s-polimernoj-zalivkoj/ остаётся на `insaincalc.calcBadge`. В пакет `forms-batch-switch` форма 31 не попадает.

## Контекст и ссылки

- `.cursor/skills/ezfc-form-to-api/SKILL.md`, этапы `verify.md` и `copy.md`. Шаги 17–24 не входят.
- `docs/ezfc-api-migration.md` — GET = имя элемента. Образец второй формы — `wp-plugin/forms/print_sheet.js`.
- `docs/site/forms.md` — строка формы 31, только читать.
- `wp-plugin/forms/badge.js` — JS лида 64. `calc_service/tests/test_calculators/test_badge.py` — эталоны лида не сдвигать.
- `js_legacy/calc/calcBadge.js` — эталон, если подключён в `scripts/run_js_calc.mjs`.
- `todo/EPIC-forms-to-api.md` — пачка 5. Формы 60, 61, 84 — отдельные задачи после этой.
- Остальное не открывать.

## Scope

- В git (Implementer): JS формы 31 со своими id. Расчёт формы 64 остаётся: её id и эталоны не менять. Блоки `/* form 64 */` и `/* form 31 */`. Без блоков `scripts/ezfc_copy.py` не примет чужие `get_value_from`. Развилка по набору полей, не по id копии. Если развилка не собирается без сдвига цены лида — стоп, `заблокировано: аналитик`.
- Дефолт формы 31 сверить с раннером. Сошёлся — `badge.py` не менять. Не сошёлся — только ветки этого дефолта через уже существующий порт. Порта нет — стоп, `заблокировано: аналитик`. Новые строки в allowed не добавлять.
- Кейс дефолта — отдельная константа в `test_badge.py` с `# JS, ДД.ММ.ГГГГ`.
- На проде (Site ops): дубль формы 31 на черновик, `read_file=0`. Плагин не выкладывать. Боевые 31 и 64 не переключать. Копию 114 / 2586910 не править.
- Строка для будущего пакета и дописка раннера — в «Результат».

## Файлы

- `wp-plugin/forms/badge.js`
- `calc_service/calculators/badge.py`
- `calc_service/tests/test_calculators/test_badge.py`
- WordPress: только новая копия формы 31 и её черновик

## Не-scope

- `todo/forms-batch-switch.md`, `docs/site/forms.md`, `docs/js-runner-cases.md`
- Копия 114 / 2586910, боевые формы 64, 60, 61, 84
- `uv_badge.py`, JSON цен, выкладка плагина, шаги 17–24

## Критерии приёмки

- [ ] `python -m pytest calc_service/tests/test_calculators/test_badge.py calc_service/tests/test_wp_plugin_forms.py -q` — `passed`. Эталоны лида 64 на месте. Есть константа дефолта формы 31 с `# JS,`.
- [ ] В `wp-plugin/forms/badge.js` есть `calcApi('badge'`, `syncUrl(`, `showResult(` и блоки `/* form 64 */` и `/* form 31 */`. Id формы 64 на месте.
- [ ] Копия не на витрине: `draft` или `private`, гость получает не `200`.
- [ ] На копии под админом дефолт даёт `POST /api/v1/calc/badge` → 200. Цена на странице = `price` API с округлением `showResult`.
- [ ] `curl.exe -s https://insain.ru/catalog/bejdzhi-s-polimernoj-zalivkoj/` — в HTML есть `calcBadge`, нет `calcApi`.

### Критерии перевода формы ezFC на API

- [ ] URL обновляется GET-именами формы 31; ссылка с GET открывает форму с теми же значениями и той же ценой.

## Проверки

- [ ] `make check` (или `python scripts/dev.py check`) — зелёный вывод
- [ ] Self-review — чеклист «Перед сдачей» в [AGENTS.md](../AGENTS.md)

## Риски

- Прод: дубль только этой копии. Запись под `lock prod`.
- Цены: нет. Эталоны лида не сдвигать.
- Формы: id боевой 31 не менять.

## Режим

прод

## Журнал передач

27.11.2026 — человек — завести задачи на оставшиеся формы, реализацию не начинать — дальше Analyst
27.11.2026 — Analyst, Grok 4.7 — черновик второй формы slug `badge`, форма 31 — дальше человек

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
