# form-sticker-pack

Статус: закрытие
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

- [x] `python -m pytest calc_service/tests/test_calculators/test_sticker.py calc_service/tests/test_wp_plugin_forms.py -q` — `passed`. `REF_FORM_DEFAULT` формы 22 на месте. Есть константа дефолта формы 29 с `# JS,`.
- [x] `Select-String -Path wp-plugin\forms\sticker.js -Pattern "calcApi\('sticker'|syncUrl\(|showResult\("` — все три есть. Строка `get_value_from(1064, true)` на месте.
- [x] Копия не на витрине: статус черновика `draft` или `private`, гость без cookies — не `200`.
- [x] На копии под админом дефолт даёт `POST /api/v1/calc/sticker` → 200. Цена на странице = `price` API с округлением `showResult`.
- [x] URL копии обновляется GET-именами формы 29. Ссылка с этими GET открывает те же значения и ту же цену.
- [x] Боевая страница стикерпака в HTML содержит `calcSticker`, не `calcApi`.

## Проверки

- [x] `python scripts/dev.py check` — код выхода 0
- [x] Self-review — чеклист «Перед сдачей» в [AGENTS.md](../AGENTS.md)

## Риски

- Прод: боевые 22 и 29 не меняются. Запись в формы не параллельно с `todo/ezfc-options-source-reset.md`.
- Цены: нет. Эталон формы 22 не сдвигать.
- Формы: id боевой 29 не менять. id формы 22 в JS и в тесте плагина не подменять.

## Режим

прод

## Журнал передач

19.11.2026 — Analyst, Grok 4.7 — задача заведена, копия формы 22 принята — дальше Implementer
21.11.2026 — Implementer, Grok 4.7 — JS формы 29 и эталон дефолта, check зелёный — дальше Site ops
21.11.2026 — Site ops, Grok 4.7 — копия 108, черновик 2586904, дефолт 1 500 ₽, боевая на calcSticker — дальше человек, приёмка копии и finish-task
21.11.2026 — человек — принято — закрытие

## Найдено вне scope

- Срок дефолта формы 29 на 0.01 ч меньше JS при той же цене: mode 1 JS `time_hours` 0.47 / `time_ready` 16.47, Python и боевой API 0.46 / 16.46; mode 2 — 8.52 против 8.51 (rel 0.00117). `cost` и `price` совпали на mode 0/1/2. `sticker.py` вне scope, не чинился.

## Результат

- Ветка, PR или коммит: `task/form-sticker-pack`
- Период: 2026-11-19 — 2026-11-21
- Часы человека: оценка 4 ч
- Работа агентов: Implementer, Grok 4.7; Site ops, Grok 4.7
- Было / стало: `sticker.js` считал только форму 22. Теперь ветка по полю `dpdFormat` (его нет у формы 22): форма 29 читает id 1062, 1039, 1056. Id формы 22, включая `get_value_from(1064, true)`, на месте. В ветке 22 `{{numSizeItem}}` и `{{numDensity}}` заменены на `get_value_from(651)` и `get_value_from(649)` — так ezFC и подставлял эти имена, а фигурные скобки ломали расчёт копии формы 29. `REF_FORM_DEFAULT` формы 22 на месте, дефолт формы 29 — `REF_FORM_PACK_DEFAULT`.
- Сделано: JS формы 29 в `wp-plugin/forms/sticker.js`; эталон дефолта и mode 0/2 в `test_sticker.py`; `ezfc_copy.py` переписывает только блок `/* form N */` боевой формы, чужие id оставляет (иначе шаг 10 на файле с двумя формами останавливается).
- Чем проверено: `python -m pytest calc_service/tests/test_calculators/test_sticker.py calc_service/tests/test_wp_plugin_forms.py calc_service/tests/test_ezfc_copy.py -q` — 47 passed. Раннер и `POST https://insain.ru/api/v1/calc/sticker` на дефолте формы 29: price mode 0/1/2 = 1356.268 / 1496.268 / 1635.268. `python scripts/dev.py check` — код выхода 0. `js_port_gaps.py calcSticker`: «нет в Python» пусто.
- Не сделано и почему: плагин не выкладывался. Боевые 22 и 29 не переключались. Общие файлы не правились. Шаги 17–24 не делались.
- Требуется решение: человек принимает копию, затем `finish-task`. После приёмки строка идёт в будущий `forms-batch-2`, не в текущий пакет.

Строка для `forms-batch-2`: форма 29 `sticker`, копия 108, черновик 2586904, URL https://insain.ru/?post_type=product&p=2586904&preview=true , боевая https://insain.ru/catalog/stikerpak/ остаётся на `insaincalc.calcSticker`, в `forms-batch-switch` не входит.

### Site ops

- Сделано: дубль формы 29 → форма 108 «CalcStickerPack duplicate». Товар 2195337 скопирован в черновик 2586904 «Стикерпак (Копировать)», `ezfc_form_id` 108. JS копии (`read_file=0`) и GET записаны `ezfc_copy_apply.php`. Блок результата копии приведён к разметке формы 79: скидка в одной строке с ценой, режим внутри срока, материалы. В `sticker.js` убраны `{{numSizeItem}}` и `{{numDensity}}`: ezFC при любом таком имени во всём тексте подменяет расчёт на `return 0`. На форме 22 это те же вызовы `get_value_from(651)` и `get_value_from(649)`.
- Чем проверено: `wp post get 2586904 --field=post_status` → `draft`, meta `ezfc_form_id` → `108`. Гость `curl` `https://insain.ru/?post_type=product&p=2586904` → `404`. Под админом дефолт `POST /api/v1/calc/sticker` 200, тело `quantity 10, width 175, height 250, size_item 50, density 1, difficulty 1, material_id RAFLACOAT, is_find_mark true, mode 1`, `price` 1496.268, на странице `1 500 руб.` / `150 руб./шт`. URL `numN=10&dpdFormat=0&dpdMaterial=0&rdoModeProduction=1` открывает те же значения и `1 500 руб.`, срок `2 дня`. Смена материала и формата меняет цену и таблицу; `rdoModeProduction=0` сохраняется после перезагрузки. Боевая `https://insain.ru/catalog/stikerpak/`: `calcSticker=2`, `calcApi=0`. Товар 2195337 остаётся `publish`, форма 29. `pytest` sticker / wp_plugin_forms / ezfc_copy — 47 passed. `wp litespeed-purge all` дважды вернул 400; `wp cache flush` — Success. Превью после flush перечитано.
- Не сделано и почему: плагин не выкладывался, боевые 29 и 22 не переключались, шаги 17–24 не входят. `wp litespeed-purge all` не прошёл (400); для черновика хватило сброса object cache и повторного открытия превью.
- Как откатить: копия не на витрине. JS и GET — строки бэкапа `/tmp/ezfc-copy-108-20261121-054827.json` (предыдущий снимок `/tmp/ezfc-copy-108-20261121-053656.json`). Удаление формы 108 и черновика 2586904 — только с подтверждением человека. Боевые 29 и 22 не менялись.

Команда раннера для `docs/js-runner-cases.md` (в эту ветку файл не писать):

```text
node scripts/run_js_calc.mjs calcSticker --data current --args '[10,[175,250],50,1,1,"RAFLACOAT",{"isLenCut":0,"isFindMark":true,"isPrint":"KMBizhubC220"},1]'
```

Тот же вызов с последним аргументом `0` и `2`.

Для Site ops: в `calcApi` не уходит `fluAtrwork`. Зашито как в боевом JS, полей нет: `size_item` 50, `density` 1, `difficulty` 1, `is_find_mark` true. Печать не передаётся: боевой `isPrint` — строка `KMBizhubC220`, лазер не стартует; передача принтера изменит цену. GET шага 10: `numN`, `dpdFormat:index`, `dpdMaterial:index`, `rdoModeProduction:value`. Дефолт копии: 10 шт, первое поле 175×250, RAFLACOAT, режим 1, `price` API 1496.268.
