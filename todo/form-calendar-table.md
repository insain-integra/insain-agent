# form-calendar-table

Статус: заблокировано: ждёт todo/form-calendar-flip.md
Сложность: низкая
Implementer: Grok 4.7
Reviewer: Auto
Site ops: Grok 4.7
Почему: вторая форма slug `calendar`, настольный перекидной календарь. Ждёт `form-calendar-flip`.

## Цель

Копия формы 66 CalcCalendarTable на черновике товара считает `POST /api/v1/calc/calendar`. URL копии пишется GET-именами элементов формы 66. Ссылка с этими GET открывает ту же копию с теми же значениями и той же ценой. Боевая страница https://insain.ru/catalog/kalkulyator-nastolnyh-perekidnyh-kalendarej/ остаётся на `insaincalc.calcCalendarTableFlip`. В пакет `forms-batch-switch` форма 66 не попадает.

## Контекст и ссылки

- `.cursor/skills/ezfc-form-to-api/SKILL.md`, этапы `verify.md` и `copy.md`. Шаги 17–24 не входят.
- `docs/ezfc-api-migration.md` — GET = имя элемента. Образец второй формы — `wp-plugin/forms/print_sheet.js`.
- `docs/site/forms.md` — строка формы 66, только читать.
- `wp-plugin/forms/calendar.js` и `test_calendar.py` — блоки и эталоны уже принятых форм не сдвигать.
- Старый JS формы — `calcCalendarTableFlip`.
- `todo/EPIC-forms-to-api.md` — пачка 6.
- Остальное не открывать.

## Scope

- В git (Implementer): JS формы 66 со своими id, блок `/* form 66 */` в `forms/calendar.js`. Блоки и эталоны уже принятых форм не менять.
- Дефолт формы 66 сверить с раннером. Сошёлся — `calendar.py` не менять. Не сошёлся — только ветки этого дефолта через уже существующий порт. Порта нет — стоп, `заблокировано: аналитик`. Новые строки в allowed не добавлять.
- Кейс дефолта — отдельная константа в `test_calendar.py` с `# JS, ДД.ММ.ГГГГ`.
- На проде (Site ops): дубль формы 66 на черновик, `read_file=0`. Плагин не выкладывать. Боевую 66 не переключать. Чужие копии slug не править.
- Строка для будущего пакета и дописка раннера — в «Результат».

## Файлы

- `wp-plugin/forms/calendar.js`
- `calc_service/calculators/calendar.py`
- `calc_service/tests/test_calculators/test_calendar.py`
- WordPress: только новая копия формы 66 и её черновик

## Не-scope

- `todo/forms-batch-switch.md`, `docs/site/forms.md`, `docs/js-runner-cases.md`
- Копия 115 / 2586911, боевые 50 и 52 и копия формы 52
- JSON цен, выкладка плагина, шаги 17–24

## Критерии приёмки

- [ ] `python -m pytest calc_service/tests/test_calculators/test_calendar.py calc_service/tests/test_wp_plugin_forms.py -q` — `passed`. Эталоны уже принятых форм на месте. Есть константа дефолта формы 66 с `# JS,`.
- [ ] В `wp-plugin/forms/calendar.js` есть `calcApi('calendar'`, `syncUrl(`, `showResult(` и блок `/* form 66 */`.
- [ ] Копия не на витрине: `draft` или `private`, гость получает не `200`.
- [ ] На копии под админом дефолт даёт `POST /api/v1/calc/calendar` → 200. Цена на странице = `price` API с округлением `showResult`.
- [ ] `curl.exe -s https://insain.ru/catalog/kalkulyator-nastolnyh-perekidnyh-kalendarej/` — в HTML есть `calcCalendarTableFlip`, нет `calcApi`.

### Критерии перевода формы ezFC на API

- [ ] URL обновляется GET-именами формы 66; ссылка с GET открывает форму с теми же значениями и той же ценой.

## Проверки

- [ ] `make check` (или `python scripts/dev.py check`) — зелёный вывод
- [ ] Self-review — чеклист «Перед сдачей» в [AGENTS.md](../AGENTS.md)

## Риски

- Прод: дубль только этой копии. Запись под `lock prod`.
- Цены: нет.
- Формы: настольный перекидной может не сходиться с квартальным лидом. id боевой 66 не менять.

## Режим

прод

## Журнал передач

27.11.2026 — человек — завести задачи на оставшиеся формы, реализацию не начинать — дальше Analyst
27.11.2026 — Analyst, Grok 4.7 — задача формы 66, ждёт `form-calendar-flip` — дальше человек

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
