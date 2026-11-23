# form-magnet-acrylic

Статус: выкатка
Сложность: низкая
Implementer: Grok 4.7
Reviewer: не нужен
Site ops: Grok 4.7
Почему: копия формы по skill `ezfc-form-to-api`, калькулятор `magnet_acrylic` уже в API, пропусков порта `calcAcrylicMagnets` в allowed нет.

## Цель

Копия формы 75 CalcАcrylicMagnets на черновике товара считает `POST /api/v1/calc/magnet_acrylic`. URL копии пишется GET-именами элементов. Ссылка с этими GET открывает ту же копию с теми же значениями и той же ценой. Боевая страница https://insain.ru/catalog/akrilovye-magnity/ остаётся на `insaincalc.calcAcrylicMagnets`. Боевое переключение отложено решением человека 22.11.2026.

## Контекст и ссылки

- `.cursor/skills/ezfc-form-to-api/SKILL.md`, этапы `verify.md` и `copy.md`. Шаги 17–24 не входят.
- `docs/ezfc-api-migration.md` — GET = имя элемента.
- `docs/site/forms.md` — строка формы 75, только читать.
- `calc_service/calculators/magnets.py` — только `MagnetAcrylicCalculator` и его функции; `calc_service/tests/test_calculators/test_magnets.py`.
- `js_legacy/calc/calcMagnets.js`, функция `calcAcrylicMagnets` — эталон дефолта формы.
- `todo/EPIC-forms-to-api.md` — пачка 7.
- Остальное не открывать.

## Scope

- В git (Implementer): шаги 0–5б и `wp-plugin/forms/magnet_acrylic.js`. `REF_FORM_DEFAULT` для `magnet_acrylic` в `test_magnets.py` с пометкой `# JS, ДД.ММ.ГГГГ`. `calcMagnets.js` в `scripts/run_js_calc.mjs` не подключён — эталон прямым прогоном файла в Node vm, раннер не править.
- Если дефолт формы не сходится с JS — чинить ветку `magnet_acrylic` в `magnets.py` в этой задаче. Ветку `magnet_laminated` не трогать: её ведёт `todo/form-magnet-laminated.md` после закрытия этой задачи. Калькулятор не на боевой форме API, предпосылку не заводить. Новые строки в allowed не добавлять.
- На проде (Site ops): дубль формы 75 на черновик после совпадения дефолта с боевым API. Если порт менял ответ — сначала `deploy-api` с `main`, потом дубль. JS копии в элементе (`read_file=0`). Плагин не выкладывать. Боевую 75 не переключать.
- Строка для будущего боевого пакета и дописка для `docs/js-runner-cases.md` — в «Результат», не в общие файлы.

## Файлы

- `wp-plugin/forms/magnet_acrylic.js`
- `calc_service/calculators/magnets.py`
- `calc_service/tests/test_calculators/test_magnets.py`
- WordPress: только копия формы 75 и её черновик

## Не-scope

- `todo/forms-batch-switch.md`, `docs/site/forms.md`, `docs/js-runner-cases.md`, `scripts/run_js_calc.mjs`
- Боевая форма 75 и шаги 17–24, выкладка плагина, JSON цен, `calc_service/calculators/__init__.py`
- Ветка `magnet_laminated` в `magnets.py`, строки `calcMagnetLamination` в `scripts/js_port_gaps_allowed.txt`. Чужие калькуляторы, в том числе `keychain.py`.

## Критерии приёмки

Каждый пункт — команда и ожидаемый результат.
Скрипт через `@'…'@ | python -` в PowerShell 5.1 — первой строкой `$OutputEncoding = New-Object System.Text.UTF8Encoding $false`, иначе кириллица в нём станет `?`.

- [x] `python scripts/js_port_gaps.py calcAcrylicMagnets` — у `calcAcrylicMagnets` строка `нет в Python` пустая. В цепочке одна уже допустимая строка `calcPrintSheet call calcPrintLaser` (лазер вшит в `print_sheet.py`, строка есть в allowed). `python scripts/js_port_gaps.py --check` печатает `ok`. Новых строк в allowed нет.
- [x] `python -m pytest calc_service/tests/test_calculators/test_magnets.py calc_service/tests/test_wp_plugin_forms.py -q` — `49 passed`. Есть `REF_FORM_DEFAULT` для `magnet_acrylic` с `# JS, 24.11.2026`; эталоны `magnet_laminated` не сдвинулись.
- [x] Боевой `POST /api/v1/calc/magnet_acrylic` на теле `REF_FORM_DEFAULT`: `price` 5120.5 и `time_ready` 9.35 как у JS (mode 0/1/2 тоже). Цена на проде уже совпадает, выкатка из-за цены не нужна. `size_mm` заготовки и зиплока на боевом API ещё нет — копию до выкатки этой правки не принимать.
- [x] `Select-String -Path wp-plugin\forms\magnet_acrylic.js -Pattern "calcApi\('magnet_acrylic'|syncUrl\(|showResult\("` — все три есть. Своей `price` и `querySelector` нет.
- [ ] Копия не на витрине: `wp post get <product> --field=post_status` → `draft` или `private`; `curl.exe -s -o NUL -w "%{http_code}"` гостем — не `200`.
- [ ] На копии под админом дефолт даёт `POST /api/v1/calc/magnet_acrylic` → 200. Цена на странице = `price` API с округлением `showResult`.
- [x] `curl.exe -s https://insain.ru/catalog/akrilovye-magnity/` — `calcAcrylicMagnets=1`, `calcApi=0`.

### Критерии перевода формы ezFC на API

- [ ] URL обновляется GET-именами формы; ссылка с GET открывает форму с теми же значениями и той же ценой.

## Проверки

- [x] `make check` (или `python scripts/dev.py check`) — зелёный вывод: calc_service 847 passed, bot_service 81 passed
- [x] Self-review — чеклист «Перед сдачей» в [AGENTS.md](../AGENTS.md)

## Риски

- Прод: боевая форма 75 не меняется. Выкатка API — только если менялся калькулятор, с `main`. Запись в формы не параллельно с `todo/ezfc-options-source-reset.md`.
- Цены: JSON не менять.
- Формы: id боевой 75 не менять; копия — новая форма на черновике.
- Общий файл `magnets.py` с `todo/form-magnet-laminated.md`: та задача ждёт закрытия этой.

## Режим

прод

## Журнал передач

Строка на сессию: `<дата> — <роль>, <модель> — <итог> — дальше <роль>`. Блокер — по формату
[docs/agents/workflow.md](../docs/agents/workflow.md). Замечания ревью — ниже, в «Ревью N».

22.11.2026 — человек — завести 8 лид-копий, боевые формы не переключать, форма 68 через tablets — дальше Implementer

24.11.2026 — Implementer, Grok 4.7 — эталон дефолта и `forms/magnet_acrylic.js`; цена и срок уже на боевом API; `size_mm` заготовки и зиплока только в ветке — дальше человек

Блокер: дубль формы 75 нельзя принимать, пока боевой API не отдаёт `size_mm` заготовки и зиплока
Пробовал: `POST https://insain.ru/api/v1/calc/magnet_acrylic` на дефолте — `price` 5120.5 и `time_ready` 9.35 совпали с JS на mode 0/1/2; у `MagnetAcrylic6565` и `ZipLockAcrylic` в `materials` нет `size_mm`. Локально размер добавлен в `calc_acrylic_magnets`, цена не изменилась. Выкатка только с `main`, коммит не делался.
Гипотеза: правка ответа есть только в worktree `task/form-magnet-acrylic`
Вопрос: слить и выкатить API до дубля или дублировать сейчас без размеров
Следующая сессия: человек, затем Site ops, модель Grok 4.7

24.11.2026 — человек — слить в main, выкатить API, затем дубль формы 75 — дальше Site ops

Варианты:
1. Слить `task/form-magnet-acrylic` в `main`, выкатить API (`deploy-api`), затем Site ops делает дубль формы 75 (Рекомендуется). Цена не меняется. В таблице материалов появятся размеры 65×65 и 80×120.
2. Site ops делает дубль сейчас на текущем боевом API. Цена 5120.50 и срок 9.35 совпадут со страницей. Колонка «Размер» у заготовки и зиплока будет пустой, пока API не выкатят.
3. Ничего не выкатывать и не дублировать. Правки остаются в worktree незакоммиченными.

## Найдено вне scope

- Имя бумаги `PaperCoated115M`: JS «Титан DIGITAL мелованная (матовая) SRA3 113г/м», API «…115г/м» (`description` в `sheet.json`). Состав, размер листа 320×450 и количество 4 совпадают. JSON не менялся.
- В цепочке `js_port_gaps` у `calcPrintSheet` строка `call calcPrintLaser`: лазерная печать вшита в `print_sheet.py`, строка уже в `scripts/js_port_gaps_allowed.txt`. Новых строк в allowed нет.
- У формы 75 нет радио «дешевле» (value 0), только «стандарт» 1 и «быстрее» 2. `mode=0` проверен на калькуляторе, на странице его не выбрать.

## Результат

- Ветка, PR или коммит: `task/form-magnet-acrylic`, коммита нет. Файлы: `wp-plugin/forms/magnet_acrylic.js` (новый), `calc_service/calculators/magnets.py` (только `calc_acrylic_magnets`), `calc_service/tests/test_calculators/test_magnets.py`, `calc_service/tests/test_wp_plugin_forms.py` (файл эталона `magnet_acrylic` — `test_magnets.py`).
- Период: 2026-11-24 — 2026-11-24
- Часы человека: оценка 1 ч — 1 ч на коммит задачи | факт сессии не замерялся
- Работа агентов: 1 сессия Implementer; Grok 4.7
- Было / стало: форма 75 на `calcAcrylicMagnets`; в ветке JS `calcApi('magnet_acrylic')` и эталон дефолта (100 шт, `MagnetAcrylic6565`, color 1, mode 1) — JS `price` 5120.504224 / `time_ready` 9.35, боевой API уже 5120.5 / 9.35; `size_mm` заготовки и зиплока в ветке, на проде ещё нет.
- Сделано: шаги 0–5б и текст `wp-plugin/forms/magnet_acrylic.js` (id боевой 75). `REF_FORM_DEFAULT` и режимы 0/2. В `calc_acrylic_magnets` у заготовки `size_mm` из размера магнита, у зиплока — из каталога `pack`. Ветка `magnet_laminated` не менялась. Дефолт: тираж 100, заготовка `MagnetAcrylic6565` (квадрат 65×65), цветность `4+0` → API `color` 1, упаковка всегда (поля нет), mode 1. Поля: `numN` 2988, `dpdBlank` 2989, `dpdColor` 2990, `rdoModeProduction` 3005 (сейчас `GET_check=index`, на копии нужно `value`), `cjsCalc` 2992. В API не уходит и в URL не пишется файл `fluAtrwork` 2991. `get_value_from` смотрит на те же поля, что и старый JS.
- Чем проверено: `python scripts/js_port_gaps.py calcAcrylicMagnets`; `python scripts/js_port_gaps.py --check` → `ok`; Node vm `calcAcrylicMagnets(100,"MagnetAcrylic6565","4+0",Map,mode)` на прайсе `calc_service/data` (раннер не менялся, `calcMagnets.js` в него не входит); `python -m pytest calc_service/tests/test_calculators/test_magnets.py calc_service/tests/test_wp_plugin_forms.py -q` → `49 passed`; `POST` боевого API mode 0/1/2; `Select-String` по `magnet_acrylic.js`; `curl` боевой страницы `calcAcrylicMagnets=1` `calcApi=0`; `python scripts/dev.py check` → 847 passed и 81 passed.
- Не сделано и почему: дубль формы, черновик товара, запись JS в копию и отладка на странице — Site ops, шаги 6–16. Боевая 75 не переключалась. Плагин не выкладывался. Коммит не делался. `docs/dashboard.md` после `check` возвращён, общие файлы не правились.
- Требуется решение: выкатить ли API с `main` до дубля. Цена и срок уже совпадают без выкатки. `size_mm` заготовки и зиплока — нет, копию по шагу 3а до выкатки не принимать.
- Дописка в `docs/js-runner-cases.md` (при слиянии, раннер не подключать): `calcAcrylicMagnets` form 75 default | `magnet_acrylic` | 5120.504224. Тот же вход mode 0 — 4471.917824; mode 2 — 5800.986624. Прогон: Node vm файла `js_legacy/calc/calcMagnets.js` с прайсом `calc_service/data`, не `scripts/run_js_calc.mjs`. Вызов: `calcAcrylicMagnets(100, "MagnetAcrylic6565", "4+0", new Map(), mode)`.
- Строка в `todo/forms-batch-switch.md` после приёмки копии: `| 75 CalcАcrylicMagnets | magnet_acrylic | /catalog/akrilovye-magnity/ | <copy> / <product> (draft) | form-magnet-acrylic |`. Буква «А» в имени формы кириллическая. Боевую 75 в пакет не ставить, пока человек не примет копию.
- Строка в `docs/site/forms.md` после копии: форма 75 остаётся на `insaincalc.calcAcrylicMagnets`; копия `<copy>` на черновике `<product>` считает `magnet_acrylic`.
- Для Site ops, шаг 10: `python scripts/ezfc_copy.py wp-plugin/forms/magnet_acrylic.js --live 75 --copy <copy> --map $env:TEMP\ezfc-map-magnet_acrylic.tsv --get numN --get rdoModeProduction:value --get dpdBlank:index --get dpdColor:index`. На странице после `showResult` итог дефолта — 5200 ₽ (`insaincalc.round(5120.5, 100)`), срок как у боевой на тех же полях. Вес API 2.14 кг (с заготовкой); старый JS вес заготовки не кладёт.

```text
Site ops. todo/form-magnet-acrylic.md, ветка task/form-magnet-acrylic

Предусловие: ветка слита в main и API выкачен skill deploy-api. До этого дубль не делать. В calc_acrylic_magnets появились size_mm заготовки (65×65) и зиплока (80×120); на боевом API 24.11.2026 их нет. Цена и срок дефолта уже совпадают с JS и с текущим API, из-за цены выкатка не нужна. Если человек выбрал дубль без выкатки — копируй сейчас и в отчёте запиши пустой размер заготовки и зиплока.

Дальше шаги 6–16 skill ezfc-form-to-api (copy.md). Шаги 17–24 не делать. Боевую форму 75 не переключать. Плагин не выкладывать. Ветку magnet_laminated не трогать. JSON цен не менять. Коммит не делать, пока человек не попросит.

Форма 75. Поля: numN 2988 = 100; dpdBlank 2989 = MagnetAcrylic6565 (ещё MagnetAcrylic5277); dpdColor 2990 = 4+0 / 4+4; rdoModeProduction 3005 = value 1 и 2, на копии GET_check=value; cjsCalc 2992. Файл fluAtrwork 2991 в URL и в API не писать. Упаковки на форме нет, в calcApi is_packing true.

Дефолт POST /api/v1/calc/magnet_acrylic: quantity 100, magnet_id MagnetAcrylic6565, color 1, is_packing true, mode 1. Ожидание API: price 5120.5, time_ready 9.35. На странице showResult показывает 5200 руб. Режим 0 на форме нет; 1 и 2 есть. Срок копии равен сроку боевой страницы на тех же полях.

Команда записи копии — в «Результате» задачи, ключ --get: numN, rdoModeProduction:value, dpdBlank:index, dpdColor:index. Источник JS — wp-plugin/forms/magnet_acrylic.js, id боевой формы; в копию id подставляет ezfc_copy.py.

В конце обнови статус, журнал и блок text. Общие файлы (docs/site/forms.md, todo/EPIC-*.md, todo/forms-batch-switch.md, docs/js-runner-cases.md, STATUS.md, BACKLOG.md) не правь — дописку оставь в «Результате».
```
