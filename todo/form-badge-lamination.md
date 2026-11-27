# form-badge-lamination

Статус: заблокировано: ждёт todo/form-pins.md
Сложность: низкая
Implementer: Grok 4.7
Reviewer: Auto
Site ops: Grok 4.7
Почему: вторая форма slug `badge`, ламинированные бейджи. Ждёт `form-pins`.

## Цель

Копия формы 84 CalcBadgeLamination на черновике товара считает `POST /api/v1/calc/badge`. URL копии пишется GET-именами элементов формы 84. Ссылка с этими GET открывает ту же копию с теми же значениями и той же ценой. Боевая страница https://insain.ru/catalog/bejdzhi-laminirovannye/ остаётся на `insaincalc.calcBadge`. В пакет `forms-batch-switch` форма 84 не попадает.

## Контекст и ссылки

- `.cursor/skills/ezfc-form-to-api/SKILL.md`, этапы `verify.md` и `copy.md`. Шаги 17–24 не входят.
- `docs/ezfc-api-migration.md` — GET = имя элемента. Образец второй формы — `wp-plugin/forms/print_sheet.js`.
- `docs/site/forms.md` — строка формы 84, только читать.
- `wp-plugin/forms/badge.js` и `test_badge.py` — блоки и эталоны уже принятых форм не сдвигать.
- `js_legacy/calc/calcBadge.js` — эталон.
- `todo/EPIC-forms-to-api.md` — пачка 5.
- Остальное не открывать.

## Scope

- В git (Implementer): JS формы 84 со своими id, блок `/* form 84 */` в `forms/badge.js`. Блоки и эталоны уже принятых форм не менять.
- Дефолт формы 84 сверить с раннером. Сошёлся — `badge.py` не менять. Не сошёлся — только ветки этого дефолта через уже существующий порт. Порта нет — стоп, `заблокировано: аналитик`. Новые строки в allowed не добавлять.
- Кейс дефолта — отдельная константа в `test_badge.py` с `# JS, ДД.ММ.ГГГГ`.
- На проде (Site ops): дубль формы 84 на черновик, `read_file=0`. Плагин не выкладывать. Боевую 84 не переключать. Чужие копии slug не править.
- Строка для будущего пакета и дописка раннера — в «Результат».

## Файлы

- `wp-plugin/forms/badge.js`
- `calc_service/calculators/badge.py`
- `calc_service/tests/test_calculators/test_badge.py`
- WordPress: только новая копия формы 84 и её черновик

## Не-scope

- `todo/forms-batch-switch.md`, `docs/site/forms.md`, `docs/js-runner-cases.md`
- Копия 114 / 2586910, боевые 64, 31, 60, 61 и их копии
- `uv_badge.py`, JSON цен, выкладка плагина, шаги 17–24

## Критерии приёмки

- [ ] `python -m pytest calc_service/tests/test_calculators/test_badge.py calc_service/tests/test_wp_plugin_forms.py -q` — `passed`. Эталоны уже принятых форм на месте. Есть константа дефолта формы 84 с `# JS,`.
- [ ] В `wp-plugin/forms/badge.js` есть `calcApi('badge'`, `syncUrl(`, `showResult(` и блок `/* form 84 */`.
- [ ] Копия не на витрине: `draft` или `private`, гость получает не `200`.
- [ ] На копии под админом дефолт даёт `POST /api/v1/calc/badge` → 200. Цена на странице = `price` API с округлением `showResult`.
- [ ] `curl.exe -s https://insain.ru/catalog/bejdzhi-laminirovannye/` — в HTML есть `calcBadge`, нет `calcApi`.

### Критерии перевода формы ezFC на API

- [ ] URL обновляется GET-именами формы 84; ссылка с GET открывает форму с теми же значениями и той же ценой.

## Проверки

- [ ] `make check` (или `python scripts/dev.py check`) — зелёный вывод
- [ ] Self-review — чеклист «Перед сдачей» в [AGENTS.md](../AGENTS.md)

## Риски

- Прод: дубль только этой копии. Запись под `lock prod`.
- Цены: нет.
- Формы: id боевой 84 не менять.

## Режим

прод

## Журнал передач

27.11.2026 — человек — завести задачи на оставшиеся формы, реализацию не начинать — дальше Analyst
27.11.2026 — Analyst, Grok 4.7 — задача формы 84, ждёт `form-pins` — дальше человек

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
