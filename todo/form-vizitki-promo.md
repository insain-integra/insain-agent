# form-vizitki-promo

Статус: черновик
Сложность: низкая
Implementer: Grok 4.7
Reviewer: не нужен
Site ops: Grok 4.7
Почему: вторая форма уже выкатанного slug `print_offset` по skill `ezfc-form-to-api`; калькулятор и копию формы 82 не пересматривать.

## Цель

Копия формы 83 CalcCardPromo на черновике товара считает `POST /api/v1/calc/print_offset`. URL копии пишется GET-именами элементов формы 83. Ссылка с этими GET открывает ту же копию с теми же значениями и той же ценой. Боевая страница https://insain.ru/catalog/vizitki-po-akczii/ остаётся на `insaincalc.calcPrintOffsetPromo`. В пакет `forms-batch-switch` форма 83 не попадает.

## Контекст и ссылки

- `.cursor/skills/ezfc-form-to-api/SKILL.md` и этапы `verify.md` / `copy.md`. Шаги 17–24 не входят.
- `docs/ezfc-api-migration.md` — GET = имя элемента.
- `docs/site/forms.md` — строка формы 83, только читать.
- `wp-plugin/forms/print_offset.js` — JS формы 82 (id 3189, 3208, 3221). `REF_FORM_DEFAULT` формы 82 уже в `test_print_offset.py`.
- `todo/EPIC-forms-to-api.md` — хвост slug.
- Остальное не открывать.

## Scope

- В git (Implementer): JS формы 83 со своими id (шаг 5, боевая 83). `forms/print_offset.js` для формы 82 не сдвигать: её id и `REF_FORM_DEFAULT` остаются. Текст формы 83 — развилкой по набору полей, не по id копии. Если развилка ломает дефолт формы 82 — стоп, `заблокировано: аналитик`.
- Кейс дефолта формы 83 — отдельная константа в `test_print_offset.py` с пометкой `# JS, ДД.ММ.ГГГГ`.
- На проде (Site ops): дубль формы 83 на черновик. JS копии в элементе (`read_file=0`). Плагин не выкладывать. Боевые 83 и 82 не переключать.
- Строка для будущего пакета — в «Результат», не в `todo/forms-batch-switch.md`.

## Файлы

- `wp-plugin/forms/print_offset.js`
- `calc_service/tests/test_calculators/test_print_offset.py`
- WordPress: только новая копия формы 83 и её черновик

## Не-scope

- `todo/forms-batch-switch.md`, `docs/site/forms.md`, `docs/js-runner-cases.md`, `calc_service/calculators/print_offset.py`, JSON цен
- Копия 100 / черновик 2586895, боевые формы 82 и 83, выкладка плагина
- Формы 19 и 29

## Критерии приёмки

- [ ] `python -m pytest calc_service/tests/test_calculators/test_print_offset.py calc_service/tests/test_wp_plugin_forms.py -q` — `passed`. `REF_FORM_DEFAULT` формы 82 на месте. Есть константа дефолта формы 83 с `# JS,`.
- [ ] `Select-String -Path wp-plugin\forms\print_offset.js -Pattern "calcApi\('print_offset'|syncUrl\(|showResult\("` — все три есть. Id формы 82 (3189, 3208, 3221) на месте.
- [ ] Копия не на витрине: статус черновика `draft` или `private`, гость без cookies — не `200`.
- [ ] На копии под админом дефолт даёт `POST /api/v1/calc/print_offset` → 200. Цена на странице = `price` API с округлением `showResult`.
- [ ] URL копии обновляется GET-именами формы 83. Ссылка с этими GET открывает те же значения и ту же цену.
- [ ] Боевая страница визиток по акции в HTML содержит `calcPrintOffsetPromo`, не `calcApi`.

## Проверки

- [ ] `python scripts/dev.py check` — код выхода 0
- [ ] Self-review — чеклист «Перед сдачей» в [AGENTS.md](../AGENTS.md)

## Риски

- Прод: боевые 82 и 83 не меняются. Запись в формы не параллельно с `todo/ezfc-options-source-reset.md`.
- Цены: нет. Эталон формы 82 не сдвигать.
- Формы: id боевой 83 не менять. id формы 82 в JS не подменять.

## Режим

прод

## Журнал передач

19.11.2026 — Analyst, Grok 4.7 — задача заведена, копия формы 82 принята — дальше Implementer

## Найдено вне scope

- 

## Результат

- Ветка, PR или коммит:
- Период: 2026-11-19 —
- Часы человека: оценка 4 ч
- Работа агентов:
- Было / стало:
- Сделано:
- Чем проверено:
- Не сделано и почему:
- Требуется решение: после приёмки копии строка идёт в будущий `forms-batch-2`, не в текущий пакет.
