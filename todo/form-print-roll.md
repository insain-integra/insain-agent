# form-print-roll

Статус: черновик
Сложность: средняя
Implementer: Grok 4.7
Reviewer: Auto
Site ops: Grok 4.7
Почему: типовая форма серии по skill `ezfc-form-to-api`, калькулятор уже на API; прод — только копия формы по шагам skill.
Чат: человек открывает новый чат с моделью из поля Implementer.

## Цель

Копия формы 23 CalcPrintWide на черновике товара считает `POST /api/v1/calc/print_roll`. URL копии пишется GET-именами элементов. Ссылка с этими GET открывает ту же копию с теми же значениями и той же ценой. Боевая форма 23 на странице https://insain.ru/catalog/shirokoformatnaya-pechat-na-zakaz/ по-прежнему на `insaincalc.calcPrintRoll`.

## Контекст и ссылки

- `.cursor/skills/ezfc-form-to-api/SKILL.md` — порядок. Боевая форма (шаги 17–24 skill) в эту задачу не входит.
- `docs/ezfc-api-migration.md` — шаблон `cjsCalc`, GET = имя элемента, `GET_check`: dropdown с кодом — `index`, radio `1`/`2` — `value`.
- `docs/site/forms.md` — строка формы 23, только читать.
- `todo/EPIC-forms-to-api.md` — пачка 3. Имя формы CalcPrintWide, вызов в JS — `calcPrintRoll`, slug API — `print_roll`.
- `docs/js-runner-cases.md` — команда раннера для `calcPrintRoll`, если кейс уже есть.
- Остальное не открывать.

## Scope

- В git (Implementer): сверка по skill `verify.md` (порт `calcPrintRoll`, эталон, `REF_FORM_DEFAULT`, раннер, боевой API). `wp-plugin/forms/print_roll.js`: id элементов боевой формы 23, `insaincalc.syncUrl`, `insaincalc.calcApi('print_roll'`, `insaincalc.showResult`. Своих формул цены и чтения через DOM нет. Кейс дефолта — в `test_print_roll.py` с пометкой `# JS, ДД.ММ.ГГГГ`. Команду раннера дописать одной строкой в `docs/js-runner-cases.md`; файл общий для пачки, в «Файлы» его нет. Если строку в файл не вносили — она в «Результат», вносят при слиянии.
- На проде (Site ops): дубль формы и черновик товара — только после «да» человека. На копию — тот же JS с id копии, без `read_file`. GET на копии: имя параметра = имя элемента. Боевую форму не размечать. Прогон копии под админом: эталон, смена полей, ссылка с GET.
- После принятия копии человеком строка для «Состава пакета» пишется в «Результат», не в `todo/forms-batch-switch.md`. В файл пакета её переносят при слиянии, если та задача не в статусе `в работе`.
- Ветка `task/form-print-roll` от `main`.

## Файлы

- `wp-plugin/forms/print_roll.js`
- `calc_service/tests/test_calculators/test_print_roll.py`
- WordPress: только копия формы и черновик товара

## Не-scope

- `read_file` и любое переключение боевой формы 23. Выкладка плагина. `infra/deploy.sh`.
- `docs/site/forms.md`, `site/forms/23.json`, `todo/forms-batch-switch.md`.
- Правка `calc_service/calculators/print_roll.py`, цен, `calc_service/data/`, `scripts/js_port_gaps_allowed.txt`, `scripts/run_js_calc.mjs`.
- Калькулятор и slug `print_wide`. Остальные формы эпика.
- Удаление копии и черновика.

## Критерии приёмки

- [ ] `python scripts/js_port_gaps.py calcPrintRoll` — в блоке `calcPrintRoll` строка `нет в Python:` пустая или каждая позиция уже есть в `scripts/js_port_gaps_allowed.txt`.
- [ ] Раннер и `POST https://insain.ru/api/v1/calc/print_roll` на эталоне и на дефолте формы 23: `price` abs ≤ 0.02 и rel ≤ 0.001, `time_ready` rel ≤ 0.001. Иначе стоп, форму не дублировать.
- [ ] `python -m pytest calc_service/tests/test_calculators/test_print_roll.py calc_service/tests/test_wp_plugin_forms.py -q` — `passed`, `failed` нет. В тесте есть `REF_FORM_DEFAULT` с пометкой `# JS, ДД.ММ.ГГГГ`.
- [ ] `Select-String -Path wp-plugin\forms\print_roll.js -Pattern "calcApi\('print_roll'|syncUrl\(|showResult\("` — все три вхождения есть.
- [ ] Копия не на витрине: `wp post get PRODUCT --field=post_status` — `draft` или `private`; `curl.exe` без cookies на `/?post_type=product&p=PRODUCT` — `404`.
- [ ] На копии под админом эталон даёт `POST /api/v1/calc/print_roll` → 200. Цена на странице равна `price` API с округлением `showResult`.
- [ ] URL обновляется GET-именами формы. Ссылка с этими GET открывает копию с теми же значениями и той же ценой.

## Проверки

- [ ] `python scripts/dev.py check` — код выхода 0
- [ ] Self-review — чеклист «Перед сдачей» в [AGENTS.md](../AGENTS.md)

## Риски

- Прод: дубль и GET только с подтверждения человека. Боевая страница клиентам не меняется.
- Цены: JSON не править. Расхождение JS и API (rel > 0.001) — стоп, калькулятор не править, предпосылка по skill `port-fix-prerequisite`.
- Формы: id элементов боевой формы 23 не менять. В админке пишется только копия.

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
