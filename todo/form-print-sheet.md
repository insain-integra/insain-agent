# form-print-sheet

Статус: черновик
Сложность: средняя
Implementer: Grok 4.7
Reviewer: Auto
Site ops: Grok 4.7
Почему: типовая форма серии по skill `ezfc-form-to-api`, калькулятор уже на API; прод — только копия формы по шагам skill.
Чат: человек открывает новый чат с моделью из поля Implementer.

## Цель

Копия формы 6 CalcPrint на черновике товара считает `POST /api/v1/calc/print_sheet`. URL копии пишется GET-именами элементов. Ссылка с этими GET открывает ту же копию с теми же значениями и той же ценой. Боевая форма 6 на странице https://insain.ru/catalog/listovki-pod-zakaz/ по-прежнему на `insaincalc.calcPrintSheet`.

## Контекст и ссылки

- `.cursor/skills/ezfc-form-to-api/SKILL.md` — порядок. Боевая форма (шаги 17–24 skill) в эту задачу не входит.
- `docs/ezfc-api-migration.md` — шаблон `cjsCalc`, GET = имя элемента, `GET_check`: dropdown с кодом — `index`, radio `1`/`2` — `value`.
- `docs/site/forms.md` — строка формы 6, только читать.
- `todo/EPIC-forms-to-api.md` — пачка 3. Форма 19 CalcCards на том же slug — отдельная задача после принятия этой копии.
- `docs/js-runner-cases.md` — команда раннера для `calcPrintSheet`, если кейс уже есть.
- Остальное не открывать.

## Scope

- В git (Implementer): сверка по skill `verify.md` (порт `calcPrintSheet`, эталон, `REF_FORM_DEFAULT`, раннер, боевой API). `wp-plugin/forms/print_sheet.js`: id элементов боевой формы 6, `insaincalc.syncUrl`, `insaincalc.calcApi('print_sheet'`, `insaincalc.showResult`. Своих формул цены и чтения через DOM нет. Кейс дефолта — в `test_print_sheet.py` с пометкой `# JS, ДД.ММ.ГГГГ`. Команду раннера дописать одной строкой в `docs/js-runner-cases.md`; файл общий для пачки, в «Файлы» его нет. Если строку в файл не вносили — она в «Результат», вносят при слиянии.
- На проде (Site ops): дубль формы и черновик товара — только после «да» человека. На копию — тот же JS с id копии, без `read_file`. GET на копии: имя параметра = имя элемента. Боевую форму не размечать. Прогон копии под админом: эталон, смена полей, ссылка с GET.
- После принятия копии человеком строка для «Состава пакета» пишется в «Результат», не в `todo/forms-batch-switch.md`. В файл пакета её переносят при слиянии, если та задача не в статусе `в работе`.
- Ветка `task/form-print-sheet` от `main`.

## Файлы

- `wp-plugin/forms/print_sheet.js`
- `calc_service/tests/test_calculators/test_print_sheet.py`
- WordPress: только копия формы и черновик товара

## Не-scope

- `read_file` и любое переключение боевой формы 6. Выкладка плагина. `infra/deploy.sh`.
- `docs/site/forms.md`, `site/forms/6.json`, `todo/forms-batch-switch.md`.
- Правка `calc_service/calculators/print_sheet.py`, цен, `calc_service/data/`, `scripts/js_port_gaps_allowed.txt`, `scripts/run_js_calc.mjs`.
- Форма 19 CalcCards и остальные формы эпика.
- Вес: `weight_kg` с JS не сверять. Верный вес — Python (решение 11.11.2026).
- Удаление копии и черновика.

## Критерии приёмки

- [ ] `python scripts/js_port_gaps.py calcPrintSheet` — в блоке `calcPrintSheet` строка `нет в Python:` пустая или каждая позиция уже есть в `scripts/js_port_gaps_allowed.txt`.
- [ ] Раннер и `POST https://insain.ru/api/v1/calc/print_sheet` на эталоне и на дефолте формы 6: `price` abs ≤ 0.02 и rel ≤ 0.001, `time_ready` rel ≤ 0.001. Иначе стоп, форму не дублировать.
- [ ] `python -m pytest calc_service/tests/test_calculators/test_print_sheet.py calc_service/tests/test_wp_plugin_forms.py -q` — `passed`, `failed` нет. В тесте есть `REF_FORM_DEFAULT` с пометкой `# JS, ДД.ММ.ГГГГ`.
- [ ] `Select-String -Path wp-plugin\forms\print_sheet.js -Pattern "calcApi\('print_sheet'|syncUrl\(|showResult\("` — все три вхождения есть.
- [ ] Копия не на витрине: `wp post get PRODUCT --field=post_status` — `draft` или `private`; `curl.exe` без cookies на `/?post_type=product&p=PRODUCT` — `404`.
- [ ] На копии под админом эталон даёт `POST /api/v1/calc/print_sheet` → 200. Цена на странице равна `price` API с округлением `showResult`.
- [ ] URL обновляется GET-именами формы. Ссылка с этими GET открывает копию с теми же значениями и той же ценой.

## Проверки

- [ ] `python scripts/dev.py check` — код выхода 0
- [ ] Self-review — чеклист «Перед сдачей» в [AGENTS.md](../AGENTS.md)

## Риски

- Прод: дубль и GET только с подтверждения человека. Боевая страница клиентам не меняется.
- Цены: JSON не править. Расхождение JS и API (rel > 0.001) — стоп, калькулятор не править, предпосылка по skill `port-fix-prerequisite`.
- Формы: id элементов боевой формы 6 не менять. В админке пишется только копия.

## Режим

прод

## Журнал передач

Строка на сессию: `<дата> — <роль>, <модель> — <итог> — дальше <роль>`. Блокер — по формату [docs/agents/workflow.md](../docs/agents/workflow.md).

## Найдено вне scope

- —

## Результат

- Ветка, PR или коммит:
- Сделано:
- Чем проверено:
- Не сделано и почему:
- Требуется решение:
- Строка в «Состав пакета» (в `todo/forms-batch-switch.md` не писать, пока та задача `в работе`):
