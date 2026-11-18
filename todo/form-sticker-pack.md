# form-sticker-pack

Статус: черновик
Сложность: низкая
Implementer: Grok 4.7
Reviewer: не нужен
Site ops: Grok 4.7
Почему: вторая форма уже выкатанного slug `sticker` по skill `ezfc-form-to-api`; калькулятор и копию формы 22 не пересматривать.

## Цель

Копия формы 29 CalcStickerPack на черновике товара считает `POST /api/v1/calc/sticker`. URL копии пишется GET-именами элементов формы 29. Ссылка с этими GET открывает ту же копию с теми же значениями и той же ценой. Боевая страница https://insain.ru/catalog/stikerpak/ остаётся на `insaincalc.calcSticker`. В пакет `forms-batch-switch` форма 29 не попадает.

## Контекст и ссылки

- `.cursor/skills/ezfc-form-to-api/SKILL.md` и этапы `verify.md` / `copy.md`. Шаги 17–24 не входят.
- `docs/ezfc-api-migration.md` — GET = имя элемента.
- `docs/site/forms.md` — строка формы 29, только читать.
- `wp-plugin/forms/sticker.js` — JS формы 22. `calc_service/tests/test_wp_plugin_forms.py` фиксирует её id (1064, широкие принтеры). `REF_FORM_DEFAULT` формы 22 — в `test_sticker.py`.
- `todo/EPIC-forms-to-api.md` — хвост slug. Это не полимерный стикерпак (форма 70, `form-poly-sticker-pack`).
- Остальное не открывать.

## Scope

- В git (Implementer): JS формы 29 со своими id (шаг 5, боевая 29). Id и ветки формы 22 в `sticker.js` не переписывать: тест `test_sticker_js_posts_wide_print` должен остаться зелёным без правки ожидаемых строк. Форма 29 — развилкой по набору полей, не по id копии. Если развилка требует менять утверждения теста формы 22 — стоп, `заблокировано: аналитик`.
- Кейс дефолта формы 29 — отдельная константа в `test_sticker.py` с пометкой `# JS, ДД.ММ.ГГГГ`. `REF_FORM_DEFAULT` формы 22 не заменять.
- На проде (Site ops): дубль формы 29 на черновик. JS копии в элементе (`read_file=0`). Плагин не выкладывать. Боевые 29 и 22 не переключать.
- Строка для будущего пакета — в «Результат», не в `todo/forms-batch-switch.md`.

## Файлы

- `wp-plugin/forms/sticker.js`
- `calc_service/tests/test_calculators/test_sticker.py`
- WordPress: только новая копия формы 29 и её черновик

## Не-scope

- `todo/forms-batch-switch.md`, `docs/site/forms.md`, `docs/js-runner-cases.md`, `calc_service/calculators/sticker.py`, `cut_plotter.py`, JSON цен
- Копия 97 / черновик 2586891, боевые формы 22 и 29, выкладка плагина
- Форма 70 `poly_sticker_pack`, формы 19 и 83
- Правка ожидаемых строк в `test_sticker_js_posts_wide_print`

## Критерии приёмки

- [ ] `python -m pytest calc_service/tests/test_calculators/test_sticker.py calc_service/tests/test_wp_plugin_forms.py -q` — `passed`. `REF_FORM_DEFAULT` формы 22 на месте. Есть константа дефолта формы 29 с `# JS,`.
- [ ] `Select-String -Path wp-plugin\forms\sticker.js -Pattern "calcApi\('sticker'|syncUrl\(|showResult\("` — все три есть. Строка `get_value_from(1064, true)` на месте.
- [ ] Копия не на витрине: статус черновика `draft` или `private`, гость без cookies — не `200`.
- [ ] На копии под админом дефолт даёт `POST /api/v1/calc/sticker` → 200. Цена на странице = `price` API с округлением `showResult`.
- [ ] URL копии обновляется GET-именами формы 29. Ссылка с этими GET открывает те же значения и ту же цену.
- [ ] Боевая страница стикерпака в HTML содержит `calcSticker`, не `calcApi`.

## Проверки

- [ ] `python scripts/dev.py check` — код выхода 0
- [ ] Self-review — чеклист «Перед сдачей» в [AGENTS.md](../AGENTS.md)

## Риски

- Прод: боевые 22 и 29 не меняются. Запись в формы не параллельно с `todo/ezfc-options-source-reset.md`.
- Цены: нет. Эталон формы 22 не сдвигать.
- Формы: id боевой 29 не менять. id формы 22 в JS и в тесте плагина не подменять.

## Режим

прод

## Журнал передач

19.11.2026 — Analyst, Grok 4.7 — задача заведена, копия формы 22 принята — дальше Implementer

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
