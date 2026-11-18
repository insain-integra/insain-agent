# form-vizitki

Статус: черновик
Сложность: низкая
Implementer: Grok 4.7
Reviewer: не нужен
Site ops: Grok 4.7
Почему: вторая форма уже выкатанного slug `print_sheet` по skill `ezfc-form-to-api`; калькулятор и первую копию не пересматривать.

## Цель

Копия формы 19 CalcCards на черновике товара считает `POST /api/v1/calc/print_sheet`. URL копии пишется GET-именами элементов формы 19. Ссылка с этими GET открывает ту же копию с теми же значениями и той же ценой. Боевая страница https://insain.ru/catalog/vizitki/ остаётся на `insaincalc.calcPrintSheet`. В пакет `forms-batch-switch` форма 19 не попадает.

## Контекст и ссылки

- `.cursor/skills/ezfc-form-to-api/SKILL.md` и этап `verify.md` / `copy.md` — порядок. Шаги 17–24 (боевая форма) не входят.
- `docs/ezfc-api-migration.md` — шаблон `cjsCalc`, GET = имя элемента.
- `docs/site/forms.md` — строка формы 19, только читать.
- `wp-plugin/forms/print_sheet.js` — JS формы 6, id её элементов. Эталон дефолта формы 6 уже в `test_print_sheet.py` (`REF_FORM_DEFAULT`).
- `todo/EPIC-forms-to-api.md` — хвост slug, не пакет 1.
- Остальное не открывать.

## Scope

- В git (Implementer): JS формы 19 со своими id (шаг 5 skill, боевая 19, не форма 6 и не копия 96). `forms/print_sheet.js` остаётся расчётом формы 6: её id и `REF_FORM_DEFAULT` не менять. Текст JS формы 19 — в том же файле развилкой по набору полей, не по id копии (id копии и боевой 19 различаются). Если развилка не собирается без сдвига цены формы 6 — стоп, `заблокировано: аналитик`, форму не дублировать.
- Кейс дефолта формы 19 — отдельная константа в `test_print_sheet.py` с пометкой `# JS, ДД.ММ.ГГГГ`, не вместо `REF_FORM_DEFAULT`.
- На проде (Site ops): дубль формы 19 на черновик по skill. JS копии в элементе (`read_file=0`), id — копии. Плагин не выкладывать. Боевые формы 19 и 6 не переключать. Копию 96 не править.
- Строка для будущего пакета — в «Результат», не в `todo/forms-batch-switch.md`.

## Файлы

- `wp-plugin/forms/print_sheet.js`
- `calc_service/tests/test_calculators/test_print_sheet.py`
- WordPress: только новая копия формы 19 и её черновик

## Не-scope

- `todo/forms-batch-switch.md`, `docs/site/forms.md`, `docs/js-runner-cases.md`, `calc_service/calculators/print_sheet.py`, JSON цен
- Копия 96 / черновик 2586890 и `todo/print-sheet-copy-result.md`
- Боевые формы 6 и 19, выкладка плагина, `read_file` на них
- Форма 83 и форма 29

## Критерии приёмки

- [ ] `python -m pytest calc_service/tests/test_calculators/test_print_sheet.py calc_service/tests/test_wp_plugin_forms.py -q` — `passed`, `failed` нет. `REF_FORM_DEFAULT` формы 6 на месте. Есть вторая константа дефолта формы 19 с `# JS,`.
- [ ] `Select-String -Path wp-plugin\forms\print_sheet.js -Pattern "calcApi\('print_sheet'|syncUrl\(|showResult\("` — все три есть. Id формы 6 из текущей шапки файла (99, 104 и соседние) на месте.
- [ ] Копия не на витрине: `wp post list` по `ezfc_form_id` копии — `draft` или `private`. `curl.exe` без cookies на permalink черновика — не `200`.
- [ ] На копии под админом дефолт даёт `POST /api/v1/calc/print_sheet` → 200. Цена на странице = `price` API с округлением `showResult`.
- [ ] URL копии обновляется GET-именами формы 19. Ссылка с этими GET открывает те же значения и ту же цену.
- [ ] Боевая страница визиток в HTML содержит `calcPrintSheet`, не `calcApi`. Боевая страница листовок по-прежнему на старом JS.

## Проверки

- [ ] `python scripts/dev.py check` — код выхода 0
- [ ] Self-review — чеклист «Перед сдачей» в [AGENTS.md](../AGENTS.md)

## Риски

- Прод: дубль только копии; боевые 6 и 19 не меняются. Запись в формы не параллельно с `todo/ezfc-options-source-reset.md` (общий `lock prod`).
- Цены: нет. Эталон формы 6 не сдвигать.
- Формы: id боевой 19 не менять. id формы 6 в JS не подменять id формы 19.

## Режим

прод

## Журнал передач

19.11.2026 — Analyst, Grok 4.7 — задача заведена, первая копия slug принята — дальше Implementer

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
- Требуется решение: строку формы 19 в `forms-batch-switch` не переносить. После приёмки копии — в будущий `forms-batch-2`.
