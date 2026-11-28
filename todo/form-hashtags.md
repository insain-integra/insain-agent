# form-hashtags

Статус: заблокировано: ждёт todo/form-stands.md
Сложность: низкая
Implementer: Grok 4.7
Reviewer: Auto
Site ops: Grok 4.7
Почему: вторая форма уже выкатанного slug `tablets`; дефолт формы 51 на лиде расходился из-за фрезеровки. Ждёт доработку `form-stands`, те же файлы.

## Цель

Копия формы 51 CalcHashtags на черновике товара считает `POST /api/v1/calc/tablets`. URL копии пишется GET-именами элементов формы 51. Ссылка с этими GET открывает ту же копию с теми же значениями и той же ценой. Боевая страница https://insain.ru/catalog/kalkulyator-heshtegov/ остаётся на `insaincalc.calcTablets`. В пакет `forms-batch-switch` форма 51 не попадает.

## Контекст и ссылки

- `.cursor/skills/ezfc-form-to-api/SKILL.md`, этапы `verify.md` и `copy.md`. Шаги 17–24 не входят.
- `docs/ezfc-api-migration.md` — GET = имя элемента. Образец второй формы — `wp-plugin/forms/print_sheet.js`.
- `docs/site/forms.md` — строка формы 51, только читать.
- `wp-plugin/forms/tablets.js` и `calc_service/tests/test_calculators/test_tablets.py` — блоки и эталоны уже принятых форм не сдвигать.
- `js_legacy/calc/calcTablets.js` — эталон. На сверке лида дефолт формы 51 звал `calcMilling`; раннер без этого вызова падал.
- `todo/EPIC-forms-to-api.md` — пачка 6.
- Остальное не открывать.

## Scope

- В git (Implementer): JS формы 51 со своими id, блок `/* form 51 */` в `forms/tablets.js`. Блоки уже принятых форм и их эталоны не менять. Развилка по набору полей, не по id копии. Если развилка не собирается без сдвига цены принятой формы — стоп, `заблокировано: аналитик`.
- Дефолт формы 51 сверить с раннером. Сошёлся — `tablets.py` не менять. Не сошёлся — портировать только ветки этого дефолта вызовом уже существующего порта (`milling`, если он есть). Порта нет — стоп, `заблокировано: аналитик`. Новые строки в allowed не добавлять.
- Кейс дефолта формы 51 — отдельная константа в `test_tablets.py` с пометкой `# JS, ДД.ММ.ГГГГ`.
- На проде (Site ops): дубль формы 51 на черновик. JS копии в элементе (`read_file=0`). Плагин не выкладывать. Боевую 51 не переключать. Копию 120 и копии предыдущих задач slug не править.
- Строка для будущего боевого пакета и дописка для `docs/js-runner-cases.md` — в «Результат».

## Файлы

- `wp-plugin/forms/tablets.js`
- `calc_service/calculators/tablets.py`
- `calc_service/tests/test_calculators/test_tablets.py`
- WordPress: только новая копия формы 51 и её черновик

## Не-scope

- `todo/forms-batch-switch.md`, `docs/site/forms.md`, `docs/js-runner-cases.md`
- Копия 120 / 2586916, боевые формы 36, 48, 76, 68 и их копии
- `shild.py`, JSON цен, выкладка плагина, шаги 17–24

## Критерии приёмки

- [ ] `python -m pytest calc_service/tests/test_calculators/test_tablets.py calc_service/tests/test_wp_plugin_forms.py -q` — `passed`. Эталоны уже принятых форм на месте. Есть константа дефолта формы 51 с `# JS,`.
- [ ] В `wp-plugin/forms/tablets.js` есть `calcApi('tablets'`, `syncUrl(`, `showResult(` и блок `/* form 51 */`. Id уже принятых форм на месте.
- [ ] Копия не на витрине: статус черновика `draft` или `private`, гость получает не `200`.
- [ ] На копии под админом дефолт даёт `POST /api/v1/calc/tablets` → 200. Цена на странице = `price` API с округлением `showResult`.
- [ ] `curl.exe -s https://insain.ru/catalog/kalkulyator-heshtegov/` — в HTML есть `calcTablets`, нет `calcApi`.

### Критерии перевода формы ezFC на API

- [ ] URL обновляется GET-именами формы 51; ссылка с GET открывает форму с теми же значениями и той же ценой.

## Проверки

- [ ] `make check` (или `python scripts/dev.py check`) — зелёный вывод
- [ ] Self-review — чеклист «Перед сдачей» в [AGENTS.md](../AGENTS.md)

## Риски

- Прод: дубль только этой копии. Запись под `lock prod`.
- Цены: нет. Эталоны принятых форм не сдвигать.
- Формы: дефолт может требовать фрезеровку. id боевой 51 не менять.

## Режим

прод

## Журнал передач

27.11.2026 — человек — завести задачи на оставшиеся формы, реализацию не начинать — дальше Analyst
27.11.2026 — Analyst, Grok 4.7 — задача формы 51, ждёт `form-stands` — дальше человек
29.11.2026 — человек — `form-stands` возвращена на доработку, ожидание снова — дальше человек

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
