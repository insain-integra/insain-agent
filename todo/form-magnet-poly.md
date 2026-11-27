# form-magnet-poly

Статус: черновик
Сложность: низкая
Implementer: Grok 4.7
Reviewer: Auto
Site ops: Grok 4.7
Почему: вторая форма slug `magnet_laminated`. Лид 54 и копию 119 не пересматривать.

## Цель

Копия формы 57 CalcMagnetPoly на черновике товара считает `POST /api/v1/calc/magnet_laminated`. URL копии пишется GET-именами элементов формы 57. Ссылка с этими GET открывает ту же копию с теми же значениями и той же ценой. Боевая страница https://insain.ru/catalog/magnity-polimernye/ остаётся на `insaincalc.calcMagnetLamination`. В пакет `forms-batch-switch` форма 57 не попадает.

## Контекст и ссылки

- `.cursor/skills/ezfc-form-to-api/SKILL.md`, этапы `verify.md` и `copy.md`. Шаги 17–24 не входят.
- `docs/ezfc-api-migration.md` — GET = имя элемента. Образец второй формы — `wp-plugin/forms/print_sheet.js`.
- `docs/site/forms.md` — строка формы 57, только читать.
- `wp-plugin/forms/magnet_laminated.js` — JS лида 54. `calc_service/tests/test_calculators/test_magnets.py` — эталоны лида не сдвигать.
- Старый JS формы — `calcMagnetLamination`, тот же вызов, что у формы 54.
- `todo/EPIC-forms-to-api.md` — пачка 7.
- Остальное не открывать.

## Scope

- В git (Implementer): JS формы 57 со своими id. Расчёт формы 54 остаётся. Блоки `/* form 54 */` и `/* form 57 */`. Развилка по набору полей, не по id копии. Если развилка не собирается без сдвига цены лида — стоп, `заблокировано: аналитик`.
- Дефолт формы 57 сверить с раннером. Сошёлся — `MagnetLaminatedCalculator` не менять. Не сошёлся — только ветки этого дефолта через уже существующий порт. Порта нет — стоп, `заблокировано: аналитик`. Новые строки в allowed не добавлять.
- Кейс дефолта — отдельная константа в `test_magnets.py` с `# JS, ДД.ММ.ГГГГ`. Эталоны акрилового магнита не сдвигать.
- На проде (Site ops): дубль формы 57 на черновик, `read_file=0`. Плагин не выкладывать. Боевые 57 и 54 не переключать. Копию 119 / 2586915 не править.
- Строка для будущего пакета и дописка раннера — в «Результат».

## Файлы

- `wp-plugin/forms/magnet_laminated.js`
- `calc_service/calculators/magnets.py`
- `calc_service/tests/test_calculators/test_magnets.py`
- WordPress: только новая копия формы 57 и её черновик

## Не-scope

- `todo/forms-batch-switch.md`, `docs/site/forms.md`, `docs/js-runner-cases.md`
- Копия 119 / 2586915, боевая форма 54, форма 75 и `magnet_acrylic`
- JSON цен, выкладка плагина, шаги 17–24

## Критерии приёмки

- [ ] `python -m pytest calc_service/tests/test_calculators/test_magnets.py calc_service/tests/test_wp_plugin_forms.py -q` — `passed`. Эталоны лида 54 и акрилового магнита на месте. Есть константа дефолта формы 57 с `# JS,`.
- [ ] В `wp-plugin/forms/magnet_laminated.js` есть `calcApi('magnet_laminated'`, `syncUrl(`, `showResult(` и блоки `/* form 54 */` и `/* form 57 */`.
- [ ] Копия не на витрине: `draft` или `private`, гость получает не `200`.
- [ ] На копии под админом дефолт даёт `POST /api/v1/calc/magnet_laminated` → 200. Цена на странице = `price` API с округлением `showResult`.
- [ ] `curl.exe -s https://insain.ru/catalog/magnity-polimernye/` — в HTML есть `calcMagnetLamination`, нет `calcApi`.

### Критерии перевода формы ezFC на API

- [ ] URL обновляется GET-именами формы 57; ссылка с GET открывает форму с теми же значениями и той же ценой.

## Проверки

- [ ] `make check` (или `python scripts/dev.py check`) — зелёный вывод
- [ ] Self-review — чеклист «Перед сдачей» в [AGENTS.md](../AGENTS.md)

## Риски

- Прод: дубль только этой копии. Запись под `lock prod`.
- Цены: нет. Эталоны лида и акрила не сдвигать.
- Формы: `magnets.py` общий с акриловым магнитом. id боевой 57 не менять.

## Режим

прод

## Журнал передач

27.11.2026 — человек — завести задачи на оставшиеся формы, реализацию не начинать — дальше Analyst
27.11.2026 — Analyst, Grok 4.7 — черновик второй формы slug `magnet_laminated`, форма 57 — дальше человек

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
