# form-pins

Статус: заблокировано: ждёт todo/form-poly-pin.md
Сложность: низкая
Implementer: Grok 4.7
Reviewer: Auto
Site ops: Grok 4.7
Почему: форма 61 CalcPins одна на трёх товарах. Одна копия формы, не три. Ждёт `form-poly-pin`.

## Цель

Копия формы 61 CalcPins на черновике товара считает `POST /api/v1/calc/badge`. URL копии пишется GET-именами элементов формы 61. Ссылка с этими GET открывает ту же копию с теми же значениями и той же ценой. Боевые страницы остаются на `insaincalc.calcBadge`: https://insain.ru/catalog/znachki-plastikovye-s-gravirovkoj/ , https://insain.ru/catalog/znachki-plastikovye-s-uf-pechatyu/ , https://insain.ru/catalog/znachki-derevyannye/ . В пакет `forms-batch-switch` форма 61 не попадает.

## Контекст и ссылки

- `.cursor/skills/ezfc-form-to-api/SKILL.md`, этапы `verify.md` и `copy.md`. Шаги 17–24 не входят.
- `docs/ezfc-api-migration.md` — GET = имя элемента. Образец второй формы — `wp-plugin/forms/print_sheet.js`.
- `docs/site/forms.md` — три строки формы 61, только читать.
- `wp-plugin/forms/badge.js` и `test_badge.py` — блоки и эталоны уже принятых форм не сдвигать.
- `js_legacy/calc/calcBadge.js` — эталон.
- `todo/EPIC-forms-to-api.md` — пачка 5.
- Остальное не открывать.

## Scope

- В git (Implementer): JS формы 61 со своими id, блок `/* form 61 */` в `forms/badge.js`. Блоки и эталоны уже принятых форм не менять. Одна форма — один блок, не по товару.
- Дефолт формы 61 сверить с раннером. Сошёлся — `badge.py` не менять. Не сошёлся — только ветки этого дефолта через уже существующий порт. Порта нет — стоп, `заблокировано: аналитик`. Новые строки в allowed не добавлять.
- Кейс дефолта — отдельная константа в `test_badge.py` с `# JS, ДД.ММ.ГГГГ`.
- На проде (Site ops): один дубль формы 61 на один черновик, `read_file=0`. Плагин не выкладывать. Три боевых товара не переключать. Чужие копии slug не править.
- Строка для будущего пакета — одна на форму 61, с пометкой трёх товаров. Дописка раннера — в «Результат».

## Файлы

- `wp-plugin/forms/badge.js`
- `calc_service/calculators/badge.py`
- `calc_service/tests/test_calculators/test_badge.py`
- WordPress: только новая копия формы 61 и её черновик

## Не-scope

- `todo/forms-batch-switch.md`, `docs/site/forms.md`, `docs/js-runner-cases.md`
- Копия 114 / 2586910, боевые 64, 31, 60, 84 и их копии
- `uv_badge.py`, JSON цен, выкладка плагина, шаги 17–24
- Отдельные копии на каждый из трёх товаров

## Критерии приёмки

- [ ] `python -m pytest calc_service/tests/test_calculators/test_badge.py calc_service/tests/test_wp_plugin_forms.py -q` — `passed`. Эталоны уже принятых форм на месте. Есть константа дефолта формы 61 с `# JS,`.
- [ ] В `wp-plugin/forms/badge.js` есть `calcApi('badge'`, `syncUrl(`, `showResult(` и блок `/* form 61 */`.
- [ ] Копия не на витрине: `draft` или `private`, гость получает не `200`.
- [ ] На копии под админом дефолт даёт `POST /api/v1/calc/badge` → 200. Цена на странице = `price` API с округлением `showResult`.
- [ ] `curl.exe -s` трёх боевых страниц — в HTML есть `calcBadge`, нет `calcApi`.

### Критерии перевода формы ezFC на API

- [ ] URL обновляется GET-именами формы 61; ссылка с GET открывает форму с теми же значениями и той же ценой.

## Проверки

- [ ] `make check` (или `python scripts/dev.py check`) — зелёный вывод
- [ ] Self-review — чеклист «Перед сдачей» в [AGENTS.md](../AGENTS.md)

## Риски

- Прод: один дубль на одну форму. Три товара переключатся вместе, когда дойдёт боевой пакет. Запись под `lock prod`.
- Цены: нет.
- Формы: id боевой 61 не менять.

## Режим

прод

## Журнал передач

27.11.2026 — человек — завести задачи на оставшиеся формы, реализацию не начинать — дальше Analyst
27.11.2026 — Analyst, Grok 4.7 — задача формы 61 на трёх товарах, ждёт `form-poly-pin` — дальше человек

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
