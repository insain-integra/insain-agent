# form-shields

Статус: заблокировано: ждёт todo/form-tabs-9may.md
Сложность: низкая
Implementer: Grok 4.7
Reviewer: Auto
Site ops: Grok 4.7
Почему: форма 68 CalcShild вызывает `calcTablets` и идёт через slug `tablets`, не `shild`. Ждёт `form-tabs-9may`.

## Цель

Копия формы 68 CalcShild на черновике товара считает `POST /api/v1/calc/tablets`. URL копии пишется GET-именами элементов формы 68. Ссылка с этими GET открывает ту же копию с теми же значениями и той же ценой. Боевая страница https://insain.ru/catalog/kalkulyator-shildov/ остаётся на `insaincalc.calcTablets`. В пакет `forms-batch-switch` форма 68 не попадает.

## Контекст и ссылки

- `.cursor/skills/ezfc-form-to-api/SKILL.md`, этапы `verify.md` и `copy.md`. Шаги 17–24 не входят.
- `docs/ezfc-api-migration.md` — GET = имя элемента. Образец второй формы — `wp-plugin/forms/print_sheet.js`.
- `docs/site/forms.md` — строка формы 68, только читать.
- `wp-plugin/forms/tablets.js` и `test_tablets.py` — блоки и эталоны уже принятых форм не сдвигать.
- `js_legacy/calc/calcTablets.js` — эталон. Форма вызывает `calcTablets`, не `calcShild`. Решение человека 22.11.2026: slug `tablets`.
- `todo/EPIC-forms-to-api.md` — пачка 6.
- Остальное не открывать.

## Scope

- В git (Implementer): JS формы 68 со своими id, блок `/* form 68 */` в `forms/tablets.js`. Блоки и эталоны уже принятых форм не менять. `shild.py` не трогать. Развилка по набору полей, не по id копии.
- Дефолт формы 68 сверить с раннером. Пустой материал, на котором раннер падает, не подменять молча: если боевой дефолт без материала не считается, стоп, `заблокировано: аналитик`, с вариантами. Сошёлся — `tablets.py` не менять. Не сошёлся — только ветки этого дефолта через уже существующий порт. Порта нет — стоп, `заблокировано: аналитик`.
- Кейс дефолта — отдельная константа в `test_tablets.py` с `# JS, ДД.ММ.ГГГГ`.
- На проде (Site ops): дубль формы 68 на черновик, `read_file=0`. Плагин не выкладывать. Боевую 68 не переключать. Чужие копии slug не править.
- Строка для будущего пакета и дописка раннера — в «Результат».

## Файлы

- `wp-plugin/forms/tablets.js`
- `calc_service/calculators/tablets.py`
- `calc_service/tests/test_calculators/test_tablets.py`
- WordPress: только новая копия формы 68 и её черновик

## Не-scope

- `todo/forms-batch-switch.md`, `docs/site/forms.md`, `docs/js-runner-cases.md`
- `calc_service/calculators/shild.py` и строки `calcShild` в allowed
- Копия 120 / 2586916, боевые 36, 48, 51, 76 и их копии
- JSON цен, выкладка плагина, шаги 17–24

## Критерии приёмки

- [ ] `python -m pytest calc_service/tests/test_calculators/test_tablets.py calc_service/tests/test_wp_plugin_forms.py -q` — `passed`. Эталоны уже принятых форм на месте. Есть константа дефолта формы 68 с `# JS,`.
- [ ] В `wp-plugin/forms/tablets.js` есть `calcApi('tablets'`, `syncUrl(`, `showResult(` и блок `/* form 68 */`. Вызова `calcShild` нет.
- [ ] Копия не на витрине: `draft` или `private`, гость получает не `200`.
- [ ] На копии под админом дефолт даёт `POST /api/v1/calc/tablets` → 200. Цена на странице = `price` API с округлением `showResult`.
- [ ] `curl.exe -s https://insain.ru/catalog/kalkulyator-shildov/` — в HTML есть `calcTablets`, нет `calcApi`.

### Критерии перевода формы ezFC на API

- [ ] URL обновляется GET-именами формы 68; ссылка с GET открывает форму с теми же значениями и той же ценой.

## Проверки

- [ ] `make check` (или `python scripts/dev.py check`) — зелёный вывод
- [ ] Self-review — чеклист «Перед сдачей» в [AGENTS.md](../AGENTS.md)

## Риски

- Прод: дубль только этой копии. Запись под `lock prod`.
- Цены: нет.
- Формы: пустой материал дефолта. id боевой 68 не менять. Калькулятор `shild` не использовать.

## Режим

прод

## Журнал передач

27.11.2026 — человек — завести задачи на оставшиеся формы, реализацию не начинать — дальше Analyst
27.11.2026 — Analyst, Grok 4.7 — задача формы 68 через slug `tablets`, ждёт `form-tabs-9may` — дальше человек

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
