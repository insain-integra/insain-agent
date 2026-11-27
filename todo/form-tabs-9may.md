# form-tabs-9may

Статус: заблокировано: ждёт todo/form-hashtags.md
Сложность: низкая
Implementer: Grok 4.7
Reviewer: Auto
Site ops: Grok 4.7
Почему: вторая форма slug `tablets`, транспарант 9 мая. Ждёт `form-hashtags`, те же файлы.

## Цель

Копия формы 76 CalcTabs9May на черновике товара считает `POST /api/v1/calc/tablets`. URL копии пишется GET-именами элементов формы 76. Ссылка с этими GET открывает ту же копию с теми же значениями и той же ценой. Боевая страница https://insain.ru/catalog/transparanty-bessmertnyj-polk/ остаётся на `insaincalc.calcTablets`. В пакет `forms-batch-switch` форма 76 не попадает.

## Контекст и ссылки

- `.cursor/skills/ezfc-form-to-api/SKILL.md`, этапы `verify.md` и `copy.md`. Шаги 17–24 не входят.
- `docs/ezfc-api-migration.md` — GET = имя элемента. Образец второй формы — `wp-plugin/forms/print_sheet.js`.
- `docs/site/forms.md` — строка формы 76, только читать.
- `wp-plugin/forms/tablets.js` и `test_tablets.py` — блоки и эталоны уже принятых форм не сдвигать.
- `js_legacy/calc/calcTablets.js` — эталон. На сверке лида дефолт формы 76 включал экосольвент и древко.
- `todo/EPIC-forms-to-api.md` — пачка 6.
- Остальное не открывать.

## Scope

- В git (Implementer): JS формы 76 со своими id, блок `/* form 76 */` в `forms/tablets.js`. Блоки и эталоны уже принятых форм не менять. Развилка по набору полей, не по id копии.
- Дефолт формы 76 сверить с раннером. Сошёлся — `tablets.py` не менять. Не сошёлся — портировать только ветки этого дефолта вызовом уже существующего порта. Порта нет (в том числе древко, если его нет в Python) — стоп, `заблокировано: аналитик`. Новые строки в allowed не добавлять.
- Кейс дефолта — отдельная константа в `test_tablets.py` с `# JS, ДД.ММ.ГГГГ`.
- На проде (Site ops): дубль формы 76 на черновик, `read_file=0`. Плагин не выкладывать. Боевую 76 не переключать. Чужие копии slug не править.
- Строка для будущего пакета и дописка раннера — в «Результат».

## Файлы

- `wp-plugin/forms/tablets.js`
- `calc_service/calculators/tablets.py`
- `calc_service/tests/test_calculators/test_tablets.py`
- WordPress: только новая копия формы 76 и её черновик

## Не-scope

- `todo/forms-batch-switch.md`, `docs/site/forms.md`, `docs/js-runner-cases.md`
- Копия 120 / 2586916, боевые 36, 48, 51, 68 и их копии
- `shild.py`, JSON цен, выкладка плагина, шаги 17–24

## Критерии приёмки

- [ ] `python -m pytest calc_service/tests/test_calculators/test_tablets.py calc_service/tests/test_wp_plugin_forms.py -q` — `passed`. Эталоны уже принятых форм на месте. Есть константа дефолта формы 76 с `# JS,`.
- [ ] В `wp-plugin/forms/tablets.js` есть `calcApi('tablets'`, `syncUrl(`, `showResult(` и блок `/* form 76 */`.
- [ ] Копия не на витрине: `draft` или `private`, гость получает не `200`.
- [ ] На копии под админом дефолт даёт `POST /api/v1/calc/tablets` → 200. Цена на странице = `price` API с округлением `showResult`.
- [ ] `curl.exe -s https://insain.ru/catalog/transparanty-bessmertnyj-polk/` — в HTML есть `calcTablets`, нет `calcApi`.

### Критерии перевода формы ezFC на API

- [ ] URL обновляется GET-именами формы 76; ссылка с GET открывает форму с теми же значениями и той же ценой.

## Проверки

- [ ] `make check` (или `python scripts/dev.py check`) — зелёный вывод
- [ ] Self-review — чеклист «Перед сдачей» в [AGENTS.md](../AGENTS.md)

## Риски

- Прод: дубль только этой копии. Запись под `lock prod`.
- Цены: нет.
- Формы: дефолт может требовать древко. id боевой 76 не менять.

## Режим

прод

## Журнал передач

27.11.2026 — человек — завести задачи на оставшиеся формы, реализацию не начинать — дальше Analyst
27.11.2026 — Analyst, Grok 4.7 — задача формы 76, ждёт `form-hashtags` — дальше человек

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
