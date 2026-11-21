# form-poly-sticker

Статус: закрытие
Сложность: низкая
Implementer: Grok 4.7
Reviewer: не нужен
Site ops: Grok 4.7
Почему: калькулятор `poly_sticker` уже в API, пропусков `calcPolySticker` в `js_port_gaps_allowed.txt` нет; копия формы по skill `ezfc-form-to-api`.

## Цель

Копия формы 30 CalcPolySticker на черновике товара считает `POST /api/v1/calc/poly_sticker`. URL копии пишется GET-именами элементов. Ссылка с этими GET открывает ту же копию с теми же значениями и той же ценой. Боевая страница https://insain.ru/catalog/naklejki-s-polimernoj-zalivkoj/ остаётся на `insaincalc.calcPolySticker`. В пакет `forms-batch-switch` форма 30 не попадает.

## Контекст и ссылки

- `.cursor/skills/ezfc-form-to-api/SKILL.md`, этапы `verify.md` и `copy.md`. Шаги 17–24 не входят.
- `docs/ezfc-api-migration.md` — шаблон `cjsCalc`, GET = имя элемента.
- `docs/site/forms.md` — строка формы 30, только читать.
- `calc_service/calculators/poly_sticker.py`, `calc_service/tests/test_calculators/test_poly_sticker.py`.
- `docs/js-runner-cases.md` — кейс `calcPolySticker` 80×80, price 4107.8, если он ещё подходит дефолту формы. Новый кейс в этот файл из ветки не писать: строка — в «Результат».
- `todo/EPIC-forms-to-api.md` — пачка 4.
- Остальное не открывать.

## Scope

- В git (Implementer): шаги 0–5б и текст `wp-plugin/forms/poly_sticker.js` (`calcApi`, `syncUrl`, `showResult`, без своей цены). `REF_FORM_DEFAULT` в `test_poly_sticker.py` с пометкой `# JS, ДД.ММ.ГГГГ`.
- Калькулятор не на боевой форме API. Если дефолт формы не сходится с раннером — чинить в этой ветке, эталоны соседей не сдвигать. Отдельную предпосылку не заводить.
- На проде (Site ops): дубль формы 30 на черновик после того, как дефолт совпал с боевым API. JS копии в элементе (`read_file=0`). Плагин не выкладывать. Боевую форму 30 не переключать.
- Строка для будущего пакета — в «Результат», не в `todo/forms-batch-switch.md`.

## Файлы

- `wp-plugin/forms/poly_sticker.js`
- `calc_service/calculators/poly_sticker.py`
- `calc_service/tests/test_calculators/test_poly_sticker.py`
- WordPress: только копия формы 30 и её черновик

## Не-scope

- `todo/forms-batch-switch.md`, `docs/site/forms.md`, `docs/js-runner-cases.md`, `scripts/js_port_gaps_allowed.txt` (новые строки не добавлять)
- `sticker.py`, форма 70, боевая форма 30, выкладка плагина, JSON цен
- `calc_service/calculators/__init__.py` — slug уже зарегистрирован

## Критерии приёмки

- [x] `python scripts/js_port_gaps.py calcPolySticker` — в блоке `calcPolySticker` строка `нет в Python` пустая, либо каждый пропуск уже есть и в docstring модуля, и в `scripts/js_port_gaps_allowed.txt`.
- [x] `python -m pytest calc_service/tests/test_calculators/test_poly_sticker.py calc_service/tests/test_wp_plugin_forms.py -q` — `passed`. В тесте есть `REF_FORM_DEFAULT` с `# JS,`.
- [x] Боевой `POST /api/v1/calc/poly_sticker` на теле `REF_FORM_DEFAULT`: `price` и `time_ready` как у раннера, допуск цены abs ≤ 0.02 или rel ≤ 0.001, срока rel ≤ 0.001.
- [x] `Select-String -Path wp-plugin\forms\poly_sticker.js -Pattern "calcApi\('poly_sticker'|syncUrl\(|showResult\("` — все три есть. Своей `price` и `querySelector` нет.
- [x] Копия не на витрине: `draft` или `private`, гость без cookies — не `200`.
- [x] На копии под админом дефолт даёт `POST /api/v1/calc/poly_sticker` → 200. Цена на странице = `price` API с округлением `showResult`.
- [x] URL копии обновляется GET-именами формы 30. Ссылка с этими GET открывает те же значения и ту же цену.
- [x] Боевая страница в HTML содержит `calcPolySticker`, не `calcApi`.

## Проверки

- [x] `python scripts/dev.py check` — код выхода 0
- [x] Self-review — чеклист «Перед сдачей» в [AGENTS.md](../AGENTS.md)

## Риски

- Прод: боевая форма 30 не меняется. Запись в формы не параллельно с `todo/ezfc-options-source-reset.md`.
- Цены: JSON не менять. Если дефолт не сходится — правка калькулятора в этой ветке, не новый прайс.
- Формы: id боевой 30 не менять.

## Режим

прод

## Журнал передач

19.11.2026 — Analyst, Grok 4.7 — задача заведена, пачка 4 — дальше Implementer
21.11.2026 — Implementer, Grok 4.7 — шаги 0–5б, эталон дефолта и `wp-plugin/forms/poly_sticker.js`; дефолт совпал с боевым API — дальше Site ops
21.11.2026 — Site ops, Grok 4.7 — шаги 6–16: копия формы 106, черновик товара 2586902, JS и GET записаны; боевая форма 30 не переключалась — дальше человек, приёмка копии
21.11.2026 — человек — принято — закрытие

## Найдено вне scope

- Боевой `cjsCalc` формы 30 кладёт в `isPrint` строку принтера, `calcSticker` читает `.printerID` и `.color`. Печать в цену не входит. JS копии это повторяет: `color` и `printer_code` не отправляются. Починка меняет цену (100 шт 50×50 RaflatacMW, KM + метки + Laminat32G: раннер со строкой 10812.3, с объектом `{printerID, color:4+0}` 11447.1). Широкая печать на листовой Raflatac в Python бросает «только на рулонном материале».
- Рулонная ламинация в `lamination.py` ниже раннера. `calcLamination` 4 листа 320×450, mode 1: Laminat32G JS price 401.00 / Python 376; LaminatDLCLAM JS 831.35 / Python 720. На форме это KM 10812.3 против API 10783.55 и экосольвент 11306.8 против 11179.15. Срок в допуске rel ≤ 0.001. Ламинация не на боевой форме API, эталон `test_lamination.py` не двигался. На дефолте ламинации нет.
- mode=2 дефолта: weight раннер 0.65, Python и боевой API 0.64 — round веса эпоксидки. `price` и `time_ready` совпали.
- Кейс 80×80 PaperCoated115M из `docs/js-runner-cases.md` (price 4107.8) — не дефолт формы 30.
- В HTML боевой и копии у «Способ печати» выбран index 1 «Цифровая лазерная печать» (`data-initvalue=1`), не «Без печати». Эталон без печати — выбор «Без печати» или GET `dpdPrint=0`. Открытие копии без GET даёт тот же лазер, что боевая: 10 800 руб. и 108 руб./шт, API price 10783.55.
- Скидка на копии (showResult, cost 5486) — 7 132 руб. и 71.32 руб./шт. Боевой старый JS на тех же полях без печати — 7 121 руб. и 71.21 руб./шт. Менеджерская цена и срок совпали. Формулу скидки до шагов 17–24 не менять.

## Результат

- Ветка, PR или коммит: `task/form-poly-sticker`
- Период: 2026-11-19 — 2026-11-21
- Часы человека: оценка 4 ч
- Работа агентов: Implementer, сверка и JS; Site ops, шаги 6–16
- Было / стало: форма 30 на `insaincalc.calcPolySticker`. В git есть `wp-plugin/forms/poly_sticker.js` (`calcApi`, `syncUrl`, `showResult`) и `REF_FORM_DEFAULT`. Боевая форма и плагин не менялись. На проде копия формы 106 «CalcPolySticker duplicate» на черновике товара 2586902, `ezfc_form_id` 106. URL копии: https://insain.ru/?post_type=product&p=2586902&preview=true&numN=100&numW=50&numH=50&dpdMaterial=0&dpdDifficulty=0&dpdPrint=0&rdoModeProduction=1
- Сделано: шаги 0–5б. Порт `calcPolySticker` без пропусков. Дефолт формы 30 (поля из SQL, id не выдуманы): numN 1067 = 100, numW 1068 = 50, numH 1069 = 50, dpdDifficulty 1072 = 1 «простая», dpdMaterial 1076 = RaflatacMW (первая опция), dpdPrint 1077 = No, rdoModeProduction 2415 = 1 «стандарт» (вторая опция — 2 «быстрее», mode 0 в форме нет). `cjsCalc` 1081. Кейс 80×80 дефолту не подходит. Раннер и боевой API на mode 0/1/2 совпали по price и time_ready; своё производство: 9952.1 < 10224.65 < 11855.35 и срок 58.19 > 42.27 > 26.69. Материалы дефолта: RaflatacMW 4 листа 320×450 и EpoxyPoly 0.48 кг. У плёнки на боевой размер есть, в API `size_mm` есть. У эпоксидки JS пишет размер 0, в API `size_mm` нет — пустая ячейка, не стоп. `get_value_from(1076)` и `get_value_from(1077)` указывают на материал и печать. В боевом JS у материала нет `[0]`; в новом JS есть, код тот же. В `calcApi` не уходят: файл `fluAtrwork`, картинка Image, код принтера. В URL копии: `numN`, `numW`, `numH`, `dpdMaterial:index`, `dpdDifficulty:index`, `dpdPrint:index`, `rdoModeProduction:value`. Принтер не No включает `is_find_mark`; KMBizhubC220 → `lamination_id` Laminat32G, Technojet160ECO → LaminatDLCLAM, HPLatex335 без плёнки. Цена страницы на эталоне без печати после `showResult`: 10 300 руб. и 103 руб./шт (API price 10224.65, time_ready 42.27, weight 0.56). Строка для будущего `forms-batch-2`, не в текущий пакет: форма 30 `poly_sticker`, `wp-plugin/forms/poly_sticker.js`, боевая https://insain.ru/catalog/naklejki-s-polimernoj-zalivkoj/ остаётся на `insaincalc.calcPolySticker`. Кейс раннера в `docs/js-runner-cases.md` из ветки не писался: `node scripts/run_js_calc.mjs calcPolySticker --data current --args '[100,[50,50],1,"RaflatacMW",{},1]'` → price 10224.65, time_ready 42.27. `docs/dashboard.md` пересобран `make check` (статус «в работе»). Шаги 6–16: форма 106 (одна новая строка после 105), товар 2586902 `draft`, гость `404`. Таблица id: cjsCalc 1081→3932, numN 1067→3924, numW 1068→3925, numH 1069→3926, dpdDifficulty 1072→3928, dpdMaterial 1076→3929, dpdPrint 1077→3930, rdoModeProduction 2415→3945. `ezfc_copy.py` + `ezfc_copy_apply.php apply`: `calcApi=1`, `read_file=0`, GET как в JS, у `rdoModeProduction` `GET_check` index→value. Бэкап `/tmp/ezfc-copy-106-20261121-043527.json`. Флаги скидки: hidden=1, calc_hidden=1; менеджерские hidden=0. На эталоне POST `{"quantity":100,"width":50,"height":50,"difficulty":1,"material_id":"RaflatacMW","mode":1}` → 200, без `color` и `printer_code`. Страница: 10 300 руб., 103 руб./шт, срок «5 дней», подсказка «Готовность заказа: 28.11.26, 15:00» / «до: 23.11.26, 11:00» — как боевая на тех же полях. Материалы: RaflatacMW 320,450 × 4 и эпоксидка без размера × 0.48, внутренних `code` нет. Смена dropdown: сложность 10 300→13 600 (difficulty 1.3), материал ORAJET3640 → 12 300 и другая строка материалов, печать KM → 10 800 и Laminat32G. Режим «быстрее»: URL `rdoModeProduction=2`, «Срок 3 дня», 11 900 руб. (API mode 2 price 11855.35). Перезагрузка режим и срок не сбрасывает. Повтор GET-ссылки возвращает 100×50×50, печать «Без печати», mode 1, 10 300 руб. Блок результата: цена и «со скидкой» в одной строке, режим внутри срока, `htmTime` на внутреннем div, даты в `data-bs-original-title`.
- Чем проверено: `python scripts/js_port_gaps.py calcPolySticker` — у `calcPolySticker` строка `нет в Python` пустая. Раннер mode 0/1/2 — price 9952.1 / 10224.65 / 11855.35, time_ready 58.19 / 42.27 / 26.69. Боевой POST тем же телом — те же price и time_ready. `python -m pytest calc_service/tests/test_calculators/test_poly_sticker.py calc_service/tests/test_wp_plugin_forms.py -q` — `17 passed`. `Select-String` — есть `calcApi('poly_sticker'`, `syncUrl(`, `showResult(`; `querySelector` и `price =` нет. `curl.exe` страницы каталога — в HTML есть `calcPolySticker`, строки `calcApi` нет. `python scripts/dev.py check` — код 0, calc 767 passed, bot 81 passed. Site ops: SQL `ORDER BY id DESC LIMIT 3` — одна новая форма `106 CalcPolySticker duplicate`. `wp post meta update 2586902 ezfc_form_id 106` — `Success`, `post_status` `draft`. `curl.exe` гостя `https://insain.ru/?post_type=product&p=2586902` — `404`. `wp post meta get 2195343 ezfc_form_id` — `30`. SQL элемента 1081: `calcApi=0`, `calcPolySticker=1`; элемент 3932: `calcApi=1`. Показ `ezfc_copy_apply.php` без `apply` — `стоп` нет, затем `apply` — `записано` у 3932, 3924, 3925, 3926, 3929, 3928, 3930, 3945. `wp cache flush` — `Success`. `wp litespeed-purge all` — `Error: Something went wrong! Got 400` (повтор тот же); страница копии всё равно отдала новый JS. Боевой POST эталона — price 10224.65, time_ready 42.27, weight_kg 0.56. Браузер под админом: POST 200, страница 10 300 / 103, срок как на боевой. Консоль: ошибки `insainParse/scrtp.js`, не `insaincalc` и не `ezfc`.
- Не сделано и почему: шаги 17–24 не входят (боевая форма 30 не переключалась, снимок и реестр не писались). Плагин не выкладывался. Коммита и push нет. Блокировка prod не снималась. Общие файлы (`docs/site/forms.md`, `todo/forms-batch-switch.md`, `docs/js-runner-cases.md`, `STATUS.md`) не менялись: строка для будущего `forms-batch-2` остаётся здесь.
- Как откатить: боевая форма 30 и товар 2195343 не менялись. JS и GET копии — строки из `/tmp/ezfc-copy-106-20261121-043527.json`. Черновик 2586902 и форма 106 гостю не видны; удалять их только с отдельным «да».
- Требуется решение: приёмка копии человеком. Варианты: слить `task/form-poly-sticker` в `main` и закрыть; оставить только локально (копия на проде черновиком, ветку не сливать); доработка. После приёмки строка идёт в будущий `forms-batch-2`, не в текущий пакет. Печать строкой и цена ламинации — в «Найдено вне scope»; чинить печать до переключения боевой формы не нужно, это смена цены для клиентов.
