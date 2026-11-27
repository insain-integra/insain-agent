# form-calendar-flip

Статус: черновик
Сложность: низкая
Implementer: Grok 4.7
Reviewer: Auto
Site ops: Grok 4.7
Почему: вторая форма slug `calendar`. Лид 50 — квартальный календарь; эта форма — перекидной. Лид и копию 115 не пересматривать.

## Цель

Копия формы 52 CalcCalendarFlip на черновике товара считает `POST /api/v1/calc/calendar`. URL копии пишется GET-именами элементов формы 52. Ссылка с этими GET открывает ту же копию с теми же значениями и той же ценой. Боевая страница https://insain.ru/catalog/kalkulyator-perekidnyh-kalendarej/ остаётся на `insaincalc.calcCalendarFlip`. В пакет `forms-batch-switch` форма 52 не попадает.

## Контекст и ссылки

- `.cursor/skills/ezfc-form-to-api/SKILL.md`, этапы `verify.md` и `copy.md`. Шаги 17–24 не входят.
- `docs/ezfc-api-migration.md` — GET = имя элемента. Образец второй формы — `wp-plugin/forms/print_sheet.js`.
- `docs/site/forms.md` — строка формы 52, только читать.
- `wp-plugin/forms/calendar.js` — JS лида 50. `calc_service/tests/test_calculators/test_calendar.py` — эталоны лида не сдвигать.
- Старый JS формы — `calcCalendarFlip`. Эталон — раннер, если функция подключена в `scripts/run_js_calc.mjs`.
- `todo/EPIC-forms-to-api.md` — пачка 6. Форма 66 — отдельная задача после этой.
- Остальное не открывать.

## Scope

- В git (Implementer): JS формы 52 со своими id. Расчёт формы 50 остаётся. Блоки `/* form 50 */` и `/* form 52 */`. Развилка по набору полей, не по id копии. Если развилка не собирается без сдвига цены лида — стоп, `заблокировано: аналитик`.
- Дефолт формы 52 сверить с раннером. Сошёлся с текущим `calendar.py` — калькулятор не менять. Не сошёлся — только ветки этого дефолта через уже существующий порт. Порта нет — стоп, `заблокировано: аналитик`. Новые строки в allowed не добавлять.
- Кейс дефолта — отдельная константа в `test_calendar.py` с `# JS, ДД.ММ.ГГГГ`.
- На проде (Site ops): дубль формы 52 на черновик, `read_file=0`. Плагин не выкладывать. Боевые 52 и 50 не переключать. Копию 115 / 2586911 не править.
- Строка для будущего пакета и дописка раннера — в «Результат».

## Файлы

- `wp-plugin/forms/calendar.js`
- `calc_service/calculators/calendar.py`
- `calc_service/tests/test_calculators/test_calendar.py`
- WordPress: только новая копия формы 52 и её черновик

## Не-scope

- `todo/forms-batch-switch.md`, `docs/site/forms.md`, `docs/js-runner-cases.md`
- Копия 115 / 2586911, боевые формы 50 и 66
- JSON цен, выкладка плагина, шаги 17–24

## Критерии приёмки

- [ ] `python -m pytest calc_service/tests/test_calculators/test_calendar.py calc_service/tests/test_wp_plugin_forms.py -q` — `passed`. Эталоны лида 50 на месте. Есть константа дефолта формы 52 с `# JS,`.
- [ ] В `wp-plugin/forms/calendar.js` есть `calcApi('calendar'`, `syncUrl(`, `showResult(` и блоки `/* form 50 */` и `/* form 52 */`.
- [ ] Копия не на витрине: `draft` или `private`, гость получает не `200`.
- [ ] На копии под админом дефолт даёт `POST /api/v1/calc/calendar` → 200. Цена на странице = `price` API с округлением `showResult`.
- [ ] `curl.exe -s https://insain.ru/catalog/kalkulyator-perekidnyh-kalendarej/` — в HTML есть `calcCalendarFlip`, нет `calcApi`.

### Критерии перевода формы ezFC на API

- [ ] URL обновляется GET-именами формы 52; ссылка с GET открывает форму с теми же значениями и той же ценой.

## Проверки

- [ ] `make check` (или `python scripts/dev.py check`) — зелёный вывод
- [ ] Self-review — чеклист «Перед сдачей» в [AGENTS.md](../AGENTS.md)

## Риски

- Прод: дубль только этой копии. Запись под `lock prod`.
- Цены: нет. Эталоны лида не сдвигать.
- Формы: перекидной календарь может не сходиться с квартальным лидом. id боевой 52 не менять.

## Режим

прод

## Журнал передач

27.11.2026 — человек — завести задачи на оставшиеся формы, реализацию не начинать — дальше Analyst
27.11.2026 — Analyst, Grok 4.7 — черновик второй формы slug `calendar`, форма 52 — дальше человек

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
