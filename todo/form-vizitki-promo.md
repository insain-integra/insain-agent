# form-vizitki-promo

Статус: закрытие
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

- [x] `python -m pytest calc_service/tests/test_calculators/test_print_offset.py calc_service/tests/test_wp_plugin_forms.py -q` — `passed`. `REF_FORM_DEFAULT` формы 82 на месте. Есть константа дефолта формы 83 с `# JS,`.
- [x] `Select-String -Path wp-plugin\forms\print_offset.js -Pattern "calcApi\('print_offset'|syncUrl\(|showResult\("` — все три есть. Id формы 82 (3189, 3208, 3221) на месте.
- [x] Копия не на витрине: статус черновика `draft` или `private`, гость без cookies — не `200`.
- [x] На копии под админом дефолт даёт `POST /api/v1/calc/print_offset` → 200. Цена на странице = `price` API с округлением `showResult`.
- [x] URL копии обновляется GET-именами формы 83. Ссылка с этими GET открывает те же значения и ту же цену.
- [x] Боевая страница визиток по акции в HTML содержит `calcPrintOffsetPromo`, не `calcApi`.

## Проверки

- [x] `python scripts/dev.py check` — код выхода 0
- [x] Self-review — чеклист «Перед сдачей» в [AGENTS.md](../AGENTS.md)

## Риски

- Прод: боевые 82 и 83 не меняются. Запись в формы не параллельно с `todo/ezfc-options-source-reset.md`.
- Цены: нет. Эталон формы 82 не сдвигать.
- Формы: id боевой 83 не менять. id формы 82 в JS не подменять.

## Режим

прод

## Журнал передач

19.11.2026 — Analyst, Grok 4.7 — задача заведена, копия формы 82 принята — дальше Implementer
22.11.2026 — Implementer, Grok 4.7 — JS формы 83 и эталон дефолта в git, локальные проверки зелёные — дальше Site ops, шаги 6–16
22.11.2026 — Site ops, Grok 4.7 — копия 109 на черновике 2586905, дефолт API 2284.8 и на странице 2300 — дальше человек, приёмка копии
22.11.2026 — человек — принято — закрытие

## Найдено вне scope

- Подпись радио «стандарт» на боевой форме 83 в HTML начинается с латинской «c» (`cтандарт`). На расчёт не влияет. На копии 109 подпись та же, не менялась.
- Боевая страница в браузере показывает 2 500 руб.: `calcPrintOffsetPromo(1000,"OffsetPromoViz1000",1)` на загруженных `/icalc/` даёт price 2470.8, `round` → 2500. API и раннер — 2284.8 → на копии 2 300. Срок обоих «6 дней», вес 1.35 кг. Боевая форма не переключалась.

## Результат

- Ветка, PR или коммит: `task/form-vizitki-promo`
- Период: 2026-11-19 — 2026-11-22
- Часы человека: оценка 4 ч
- Работа агентов: Implementer, Grok 4.7, одна сессия 22.11.2026. Site ops, Grok 4.7, одна сессия 22.11.2026.
- Было / стало: `print_offset.js` считал только форму 82. Стало: развилка по полю `dpdFormat` (есть у 82, нет у 83). Форма 83 шлёт `num_sheet`, зашитый `OffsetPromoViz1000` и `mode` из data-value радио 3242. `REF_FORM_DEFAULT` формы 82 не сдвинут. Добавлен `REF_FORM83_DEFAULT`.
- Сделано: шаг 5 — поля боевой 83 (SQL, только чтение). Вход: `numN` 3227 = 1000, `rdoModeProduction` 3242 (checked «стандарт»: HTML value 0, data-value 1), `cjsCalc` 3229. Сборник в боевом JS зашит: `OffsetPromoViz1000`. В `calcApi` не уходят `width`, `height`, `color`: полей нет, размер и цветность у промо-кода, как на форме 82. В URL копии: `numN` и `rdoModeProduction` (`GET_check=value`). Порт `calcPrintOffsetPromo` полный (`нет в Python` пусто).
- Чем проверено: раннер 22.11.2026 mode 0/1/2 → price 2284.8, time_ready 56/48/40. Локальный `PrintOffsetCalculator` и `POST https://insain.ru/api/v1/calc/print_offset` — те же числа. `pytest` двух файлов — 28 passed, код 0. `ezfc_copy.py --live 83` подменяет только 3242, id 3189 и 3221 оставляет; `--live 82` — наоборот. `python scripts/dev.py check` — код 0 (calc_service 781 passed, bot_service 81 passed).
- Не сделано и почему: шаги 17–24 не входили (боевые 82 и 83 не переключались, плагин не выкладывался). `docs/js-runner-cases.md` не правился: строка для main — `node scripts/run_js_calc.mjs calcPrintOffsetPromo --data current --args '[1000,"OffsetPromoViz1000",1]'` (mode 0 → time_ready 56, mode 2 → 40, price 2284.8). `wp litespeed-purge all` дважды вернул `Error: Something went wrong! Got 400`, код выхода 1; `wp cache flush` — `Success`, код 0. Черновик новый, в кэше страницы его не было: копия отдала новый JS.
- Строка для будущего `forms-batch-2`, не в текущий пакет: форма 83 CalcCardPromo, slug `print_offset`, страница https://insain.ru/catalog/vizitki-po-akczii/, копия 109, черновик 2586905.
- Site ops, шаги 6–16. Копия формы `<copy>` 109 «CalcCardPromo duplicate». Черновик `<product>` 2586905 «Визитки по акции (Копировать)», `post_status` draft, `ezfc_form_id` 109. Боевой товар 5630 остался `publish`, форма 83. Гость без cookies: `curl` код 404. URL: https://insain.ru/?post_type=product&p=2586905&preview=true&numN=1000&rdoModeProduction=1
- Дефолт копии: `POST /api/v1/calc/print_offset` тело `{"num_sheet":1000,"material_id":"OffsetPromoViz1000","mode":1}` → 200, price 2284.8, time_ready 48. На странице после `showResult`: 2 300 руб. (2.30 руб./шт), срок «6 дней» (`timeToWords(48)`), вес 1.35 кг. Тираж 1000. Радио «стандарт»: HTML value 0, data-value 1, после открытия ссылки с GET отмечено; «быстрее» data-value 2 не отмечено. В URL `rdoModeProduction=1` (`GET_check=value`). Повторное открытие этой ссылки: те же тираж, радио и цена, тот же POST. Флаги скидки копии: `sbtPriceDiscount` и `sbtPriceTotalDiscount` hidden 1, calculate_when_hidden 1; менеджерские hidden 0. В таблице материалов имя без внутреннего code, размер 90×50, количество 1000.
- JS копии записан в элемент 4011 (`cjsCalc`), `read_file=0`, `calcApi=1`. `get_value_from` копии: 3242 → 4024; 3189 и 3221 в блоке формы 82 оставлены. GET: numN на 4010, rdoModeProduction на 4024. Бэкап: `/tmp/ezfc-copy-109-20261121-200653.json`.
- Боевая страница до и после: `calcPrintOffsetPromo` есть (1), `calcApi` нет (0). Элементы не менялись: 3208 форма 82 и 3229 форма 83 — `calcApi` нет, `calcPrintOffsetPromo` есть; 4011 форма 109 — наоборот.
- Чем проверено Site ops: дубль в админке ezFC один раз; SQL `ORDER BY id DESC LIMIT 3` — одна новая строка 109. Копия товара — «Копировать в новый черновик», один раз. `wp post meta update 2586905 ezfc_form_id 109` — `Success`, код 0; `wp post get` — `draft`. `curl` гостя — 404, код 0. `ezfc_copy.py` — код 0, без `стоп`. `wp eval-file` показ и `apply` — код 0, `записано` у 4011, 4010, 4024. `POST` API — код 0, HTTP 200. Browser MCP: POST 200, тело дефолта, цена 2 300, GET-ссылка восстанавливает значения. `wp litespeed-purge all` — код 1.
- Как откатить: только копия 109 и черновик 2586905. JS копии — строки из `/tmp/ezfc-copy-109-20261121-200653.json`. Боевые формы 82 и 83 и товар 5630 не откатывать. Удаление формы и черновика — только с подтверждением человека.
- Требуется решение: нет. Приёмка 22.11.2026 — слить, закрыть и запушить. Строка формы 83 идёт в будущий `forms-batch-2`, не в текущий пакет. На боевой странице старый расчёт по-прежнему показывает 2 500 руб.; копия показывает цену API 2 300.
