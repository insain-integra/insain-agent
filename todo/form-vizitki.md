# form-vizitki

Статус: в работе
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

- [x] `python -m pytest calc_service/tests/test_calculators/test_print_sheet.py calc_service/tests/test_wp_plugin_forms.py -q` — `passed`, `failed` нет. `REF_FORM_DEFAULT` формы 6 на месте. Есть вторая константа дефолта формы 19 с `# JS,`.
- [x] `Select-String -Path wp-plugin\forms\print_sheet.js -Pattern "calcApi\('print_sheet'|syncUrl\(|showResult\("` — все три есть. Id формы 6 из текущей шапки файла (99, 104 и соседние) на месте.
- [x] Копия не на витрине: `wp post list` по `ezfc_form_id` копии — `draft` или `private`. `curl.exe` без cookies на permalink черновика — не `200`.
- [x] На копии под админом дефолт даёт `POST /api/v1/calc/print_sheet` → 200. Цена на странице = `price` API с округлением `showResult`.
- [x] URL копии обновляется GET-именами формы 19. Ссылка с этими GET открывает те же значения и ту же цену.
- [x] Боевая страница визиток в HTML содержит `calcPrintSheet`, не `calcApi`. Боевая страница листовок по-прежнему на старом JS.

## Проверки

- [x] `python scripts/dev.py check` — код выхода 0
- [x] Self-review — чеклист «Перед сдачей» в [AGENTS.md](../AGENTS.md)

## Риски

- Прод: дубль только копии; боевые 6 и 19 не меняются. Запись в формы не параллельно с `todo/ezfc-options-source-reset.md` (общий `lock prod`).
- Цены: нет. Эталон формы 6 не сдвигать.
- Формы: id боевой 19 не менять. id формы 6 в JS не подменять id формы 19.

## Режим

прод

## Журнал передач

19.11.2026 — Analyst, Grok 4.7 — задача заведена, первая копия slug принята — дальше Implementer
21.11.2026 — Implementer, Grok 4.7 — JS формы 19 и эталон дефолта в тесте, make check зелёный — дальше Site ops (дубль на черновик)
21.11.2026 — Site ops, Grok 4.7 — шаги 6–9 сделаны, шаг 10 остановлен скриптом — дальше Analyst
Блокер: scripts/ezfc_copy.py не записывает JS копии формы 19: в print_sheet.js есть get_value_from формы 6, их нет в карте формы 19
Пробовал: один раз `python scripts/ezfc_copy.py wp-plugin/forms/print_sheet.js --live 19 --copy 107 --map $env:TEMP\ezfc-map-print_sheet.tsv --get numN --get dpdFormat:index --get dpdColor:index --get dpdMaterial:index --get dpdLaminat:index --get ckbNumber:index --get ckbBarcode:index --get ckbVariables:index --get ckbRounding:index --get ckbHole:index --get numHole --get rdoModeProduction:value --out $env:TEMP\ezfc-copy-print_sheet.json` → код выхода 1, `стоп: get_value_from с id не из боевой формы: [99, 100, 101, 102, 103, 400, 401, 402, 419, 519, 661, 663, 664, 665, 666, 667, 668]`, файл пакета не создан. Повтор и запись JS в админке не делались.
Гипотеза: build_copy_js требует, чтобы каждый get_value_from файла был в карте этой формы. Файл общий для форм 6 и 19, id формы 6 в карту 19 не входят. Дубль в порядке: форма 107 «CalcCards duplicate», черновик товара 2586903, у всех 31 строк карты id_copy заполнен и отличается от id_live.
Вопрос: 1) научить ezfc_copy.py оставлять get_value_from, которых нет в карте этой формы (id формы 6 остаются, id формы 19 подменяются), затем снова шаг 10. 2) оставить черновик как есть и не писать JS, пока скрипт не поправлен. 3) считать дубль лишним и спросить человека, удалять ли черновик.
Следующая сессия: Analyst, модель Grok 4.7
21.11.2026 — человек — править ezfc_copy.py: id вне карты формы оставлять, id формы 19 подменять, затем шаг 10 на копии 107 — дальше Implementer
21.11.2026 — Implementer, Grok 4.7 — правка скрипта и тест, make check зелёный — дальше Site ops (шаг 10 на уже существующей копии 107, черновик 2586903, дубль не повторять)
21.11.2026 — Site ops, Grok 4.7 — шаг 10 записан на копию 107, дефолт ушёл в ветку формы 6, price 0 — дальше Implementer
Блокер: копия 107 считает веткой формы 6. POST /api/v1/calc/print_sheet → 200, тело `width` 0, `height` 0, `crease_lines_per_item` 0, `price` 0. На странице число цены пустое, не 1100. URL с именами формы 6 (`numW`, `numH`, `rdoLaminat`, `numCrease`), не формы 19.
Пробовал: `python scripts/ezfc_copy.py` с картой и `--get` из шапки шага 10 — код выхода 0. В `get_value_from` id формы 19 подменены (3952, 3953, 3954, 3955, 3957, 3958, 3959, 3960, 3961, 3976), id формы 6 остались. `ezfc_copy_apply.php` без `apply`, затем с `apply`: форма 107, `бэкап: /tmp/ezfc-copy-107-20261121-051829.json`, `записано` у 3963, 3951–3955, 3957–3962, 3976. `read_file` у 3963 остался 0, `calcApi=1`. Превью под админом: поля на экране — 100 шт, 90×50, 4+0, мелованная 300, ламинация «нет», опции сняты, но POST из ветки `else`. `get_element_id_by_name(null, 'dpdLaminat')` → false; `get_element_id_by_name(107, 'dpdLaminat')` → 3955. Повтор записи и правка JS не делались.
Гипотеза: `isCards` ложный, потому что первый аргумент `null`. В DOM у обёртки `data-elementname` равен `dpdlaminat` (нижний регистр), селектор с `dpdLaminat` элемент не находит и без id формы не доходит до `element_vars`. С id формы имя сравнивается в нижнем регистре и находится. У `form.ezfc-form` есть `data-id` 107. Ветка формы 19 не выполняется.
Вопрос: нет. Ошибка JS копии, не порт и не развилка для человека. Дубль не удалять.
Следующая сессия: Implementer, модель Grok 4.7
21.11.2026 — Implementer, Gemini 4 Hydrogen High — починка ветки визиток, make check зелёный — дальше Site ops (заново шаг 10 на копии 107 и шаги 11–16; дубль не повторять; превью открывать без старых GET формы 6 numW, numH, rdoLaminat, numCrease, потому что syncUrl их сам не удаляет)
21.11.2026 — человек — записать исправленный JS на копию 107 и проверить цену — дальше Site ops
21.11.2026 — Site ops, Grok 4.7 — повтор шага 10 на копии 107 записан, шаги 11–16 зелёные: POST price 1011.4034181818182, на странице 1 100 руб., URL именами формы 19 — дальше человек (приёмка копии)
21.11.2026 — человек — принято — закрытие
21.11.2026 — finish-task — слияние с main не fast-forward: конфликт scripts/ezfc_copy.py с блоками /* form N */ — дальше Implementer
21.11.2026 — человек — оставить скрипт с main, разметить print_sheet.js блоками форм 6 и 19, затем слить и запушить — дальше Implementer
21.11.2026 — Implementer, Gemini 4 Hydrogen High — блоки form 6 и form 19 в print_sheet.js, скрипт main оставлен, make check зелёный — дальше слияние

## Найдено вне scope

- Пропуски порта `calcPrintSheet call calcCutRoller` и `call calcPrintLaser` уже в `scripts/js_port_gaps_allowed.txt`. Лазер вшит в `print_sheet.py`, роликовый рез — TODO. Дефолт визиток (90×50, PaperCoated300M) в эту ветку не попадает: 6 листов 320×450.
- На копии смена материала на «350гр, матовая» вместе с форматом «Евро» и цветом 4+4 дала `material_id` ColotechPlus350M, ширина 85, высота 55 и `price` 0 при HTTP 200. Дефолт 90×50 при этом снова считается в 1 100. Подпись «Евро (86х54 мм)» в запрос уходит как 85×55.

## Результат

- Ветка, PR или коммит: `task/form-vizitki`
- Период: 2026-11-19 — 2026-11-21
- Часы человека: оценка 4 ч
- Работа агентов: Implementer, сверка 0–5б и текст JS шага 10; Site ops, шаги 6–9, один запуск шага 10 до правки скрипта; Implementer, `build_copy_js` оставляет id вне карты; Site ops, шаг 10 на копии 107 и приёмка 11–16 (цена 0, ветка формы 6); Implementer (Gemini 4 Hydrogen High), починка развилки `isCards` в `print_sheet.js` и тест в `test_wp_plugin_forms.py`; Site ops, повтор шага 10 и приёмка 11–16 на копии 107 (цена 1 100)
- Было / стало: `print_sheet.js` считал только форму 6 → развилка: форма 19 по имени `dpdLaminat`, форма 6 прежними id. `REF_FORM_DEFAULT` на месте, добавлен `REF_FORM19_DEFAULT`. `build_copy_js` бросал ValueError на id вне карты → такой id остаётся как в файле, id из карты подменяется на id копии. `isCards = ezfc_functions.get_element_id_by_name(null, 'dpdLaminat')` (с `null` в DOM ищется регистрозависимо и возвращает `false`) → `ezfc_functions.get_element_id_by_name(__form_id__, 'dpdLaminat')` (находит элемент формы 19 и копии 107, на форме 6 возвращает `false`).
- Сделано: JS формы 19 (id 432, 435, 436, 439, 574, 725, 726, 727, 728, 731) и эталон дефолта. Полей вне API нет: все элементы ввода уходят в `calcApi` и `syncUrl`. `margins`/`interval` не поля, в запрос константами `[2,2,2,2]` и `4`, как боевой cjsCalc. Шаг 5б: `get_value_from` боевого JS совпали с полями, цена из-за чужого id не едет. Починена развилка `isCards`: первый аргумент `__form_id__` вместо `null`; добавлен тест `test_print_sheet_js_branches_by_dpd_laminat_with_form_id` в `calc_service/tests/test_wp_plugin_forms.py` (падал до правки, зелёный после). Site ops: дубль формы 19 → форма 107 «CalcCards duplicate» (одна новая строка после 106). Черновик товара 2586903 «Визитки (Копировать)», `ezfc_form_id` 107, `post_status` draft. Карта id: 31 строка, пустых `id_copy` нет, `id_copy` ≠ `id_live`. Ключи: cjsCalc 441→3963, numN 431→3951, dpdFormat 432→3952, dpdColor 435→3953, dpdMaterial 436→3954, dpdLaminat 439→3955, ckbNumber 725→3957, ckbBarcode 726→3958, ckbVariables 727→3959, ckbRounding 728→3960, ckbHole 731→3961, numHole 732→3962, rdoModeProduction 574→3976. Боевой товар 5594 остался `ezfc_form_id` 19, `publish`. Черновик 2586890 по-прежнему форма 96. Плагин не выкладывался, `read_file` на формах 6 и 19 не включался. Скрипт: `scripts/ezfc_copy.py` `build_copy_js` — id из карты → id копии, id вне карты остаётся (пробелы исходной записи тоже). Тест `test_unknown_live_id_stays`: 3094→3484, 3999 остаётся. `test_acrylic_prizes_js_gets_copy_ids` зелёный. `REF_FORM_DEFAULT`, id формы 6, `print_sheet.py`, JSON цен и `scripts/ezfc_copy.py` не менялись. Повтор шага 10: пакет из `wp-plugin/forms/print_sheet.js` записан на копию 107. В JS копии есть `get_element_id_by_name(__form_id__, 'dpdLaminat')`, вызова с `null` нет. Id формы 19 из карты подменены (3952, 3953, 3954, 3955, 3957, 3958, 3959, 3960, 3961, 3976), id формы 6 в `get_value_from` остались. `ezfc_copy_apply.php` без `apply`, затем с `apply`: форма 107, `бэкап: /tmp/ezfc-copy-107-20261121-060454.json`, `записано` у 3963, 3951–3955, 3957–3962, 3976. `read_file` у 3963 остался 0, `calcApi=1`. Плагин не выкладывался. `read_file` на формах 6 и 19 не включался. Копия 96 и черновик 2586890 не менялись.
- Чем проверено: раннер и боевой API на mode 0/1/2 совпали (price 602.817 / 1011.403 / 1460.495). Материал JS и API: PaperCoated300M, 320×450, 6 шт. До правки `print_sheet.js`: `python -m pytest calc_service/tests/test_wp_plugin_forms.py -q` → код выхода 1 (`test_print_sheet_js_branches_by_dpd_laminat_with_form_id` failed). После правки: `python -m pytest calc_service/tests/test_calculators/test_print_sheet.py calc_service/tests/test_wp_plugin_forms.py calc_service/tests/test_ezfc_copy.py -q` → код выхода 0 (`44 passed`); `Select-String -Path wp-plugin\forms\print_sheet.js -Pattern "calcApi\('print_sheet'|syncUrl\(|showResult\("` → все три найдены (4 строки); `python scripts/dev.py check` → код выхода 0 (`calc_service`: 766 passed, `bot_service`: 81 passed). Site ops (предыдущая сессия): `wp post list --meta_value=107` → `2586903 draft`; `curl.exe` без cookies → `404`; боевые формы 6 и 19 и черновик 2586890 не тронуты. Эта сессия: `python scripts/ezfc_copy.py … --live 19 --copy 107` → код выхода 0. `wp eval-file` без `apply`, затем с `apply` → `записано`, бэкап `/tmp/ezfc-copy-107-20261121-060454.json`. SQL элемента 3963: `read_file` 0, подстрока `get_element_id_by_name(__form_id__` найдена, `get_element_id_by_name(null` нет. Флаги цены копии 107: `sbtPriceTotalDiscount` и `sbtPriceDiscount` hidden 1 / calc_hidden 1, менеджерские hidden 0. `wp post list --post_type=product --meta_value=107` → `2586903 draft` «Визитки (Копировать)». `curl.exe` без cookies на `https://insain.ru/?post_type=product&p=2586903` → 404. Товар 5594 `publish`, `ezfc_form_id` 19. Черновик 2586890 `draft`, `ezfc_form_id` 96. `wp cache flush` → Success. `wp litespeed-purge all` дважды → `Error: Something went wrong! Got 400`. Превью под админом без GET формы 6: `POST /api/v1/calc/print_sheet` 200, тело `quantity` 100, `width` 90, `height` 50, `color` 4+0, `material_id` PaperCoated300M, `mode` 1, опции false, `price` 1011.4034181818182. На странице `1 100 руб.` и `11 руб./шт`, вес `0.14 кг.`, срок `Срок 1 день`, материалы «Титан DIGITAL мелованная (матовая) SRA3 300г/м», размер 320,450, количество 6, внутреннего `code` нет. Режим «стандарт»: у выбранной радио `data-value` 1, `get_value_from(3976, true)` → `[1]`. Галочки сняты. URL: `numN=100&dpdFormat=0&dpdColor=0&dpdMaterial=0&dpdLaminat=0&numHole=0&rdoModeProduction=1`, имён `numW` / `numH` / `rdoLaminat` / `numCrease` нет. Повторное открытие этой ссылки даёт тот же POST и ту же цену. Смена формата: цена 1 000, `dpdFormat=1`. Смена цветности на 4+4: цена 1 200, `dpdColor=1`. Смена ламинации на «глянцевая, 32 мкм»: цена 1 700, `dpdLaminat=1`, в таблице бумага и плёнка. Возврат на дефолт снова 1 100. Боевая https://insain.ru/catalog/vizitki/ в браузере: срок `Срок 1 день`, цена `1 100 руб.`, в HTML есть `calcPrintSheet`, `calcApi` нет. `curl.exe` страниц визиток и листовок: HTTP 200, вызов `insaincalc.calcPrintSheet`, `calcApi` нет. Консоль превью: ошибок `insaincalc` и `ezfc` нет. Скидка на копии 814 руб., на боевой странице 813 руб.: `showResult` округляет `cost * (1 + marginMin)` вверх.
- Не сделано и почему: шаги 17–24 не входят, боевая форма 19 не переключалась. Дубль не удалялся. `docs/js-runner-cases.md`, `docs/site/forms.md`, `todo/forms-batch-switch.md`, `todo/EPIC-*.md`, `STATUS.md`, `BACKLOG.md` не писались. Коммита и push нет. `lock prod` задачи form-vizitki не снимался. `scripts/ezfc_copy.py` и `wp-plugin/forms/print_sheet.js` в этой сессии не менялись.
- Как откатить: боевые формы 6 и 19 и товары 5594 / 2586890 не менялись. Запись JS копии 107 откатывается строками бэкапа `/tmp/ezfc-copy-107-20261121-060454.json` (это JS до этой записи, с `null`). Предыдущий бэкап `/tmp/ezfc-copy-107-20261121-051829.json` тоже на сервере. Форму 107 и черновик 2586903 не удалять без «да» человека. Правки `wp-plugin/forms/print_sheet.js`, `calc_service/tests/test_wp_plugin_forms.py`, `calc_service/tests/test_calculators/test_print_sheet.py`, `scripts/ezfc_copy.py`, `calc_service/tests/test_ezfc_copy.py` не закоммичены.
- Строка для будущего пакета (не в `forms-batch-switch`, не пакет 1; после приёмки копии — `forms-batch-2`): `| 19 CalcCards | print_sheet | /catalog/vizitki/ | копия 107, черновик 2586903, дефолт POST 1011.4034181818182, на странице 1 100, ждёт приёмку человека | form-vizitki |`
- Требуется решение: приёмка копии человеком. Боевую форму 19 не переключать.
- Промпт следующей сессии: Человек, приёмка копии. Задача `todo/form-vizitki.md`, ветка `task/form-vizitki`, статус `закрытие`. Копия формы 107 «CalcCards duplicate», черновик товара 2586903, гостю `404`. Дефолт под админом: 100 шт, 90×50, 4+0, PaperCoated300M, ламинация «нет», опции сняты, режим «стандарт» (`data-value` 1). `POST /api/v1/calc/print_sheet` → 200, `price` 1011.4034181818182, на странице `1 100 руб.`. URL копии: `numN`, `dpdFormat`, `dpdColor`, `dpdMaterial`, `dpdLaminat`, `numHole`, `rdoModeProduction`. Ссылка с этими GET открывает ту же цену. Боевые https://insain.ru/catalog/vizitki/ и https://insain.ru/catalog/listovki-pod-zakaz/ остаются на `insaincalc.calcPrintSheet`. Плагин не выкладывался, коммита нет. Принять копию и закрыть задачу через `finish-task` или вернуть на доработку. Боевую форму не переключать.
