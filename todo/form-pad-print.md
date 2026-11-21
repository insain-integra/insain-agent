# form-pad-print

Статус: закрытие
Сложность: средняя
Implementer: Gemini 4 Hydrogen High
Reviewer: Grok 4.7
Site ops: Grok 4.7
Почему: копия формы по skill, но пропуск `calcPadPrint option Material` есть в `js_port_gaps_allowed.txt`; дефолт может потребовать порт в том же diff.

## Цель

Копия формы 38 CalcPadPrint на черновике товара считает `POST /api/v1/calc/pad_print`. URL копии пишется GET-именами элементов. Ссылка с этими GET открывает ту же копию с теми же значениями и той же ценой. Боевая страница https://insain.ru/catalog/tampopechat/ остаётся на `insaincalc.calcPadPrint`. В пакет `forms-batch-switch` форма 38 не попадает.

## Контекст и ссылки

- `.cursor/skills/ezfc-form-to-api/SKILL.md`, этапы `verify.md` и `copy.md`. Шаги 17–24 не входят.
- `docs/ezfc-api-migration.md` — GET = имя элемента.
- `docs/site/forms.md` — строка формы 38, только читать.
- `calc_service/calculators/pad_print.py`, `calc_service/tests/test_calculators/test_pad_print.py`.
- `scripts/js_port_gaps_allowed.txt` — строка `calcPadPrint option Material`.
- `todo/EPIC-forms-to-api.md` — пачка 4.
- Остальное не открывать.

## Scope

- В git (Implementer): шаги 0–5б и `wp-plugin/forms/pad_print.js`. `REF_FORM_DEFAULT` в `test_pad_print.py` с пометкой `# JS, ДД.ММ.ГГГГ`.
- Пропуск `Material`: если дефолт формы от него не зависит и цена сходится — дописать в «не перенесено» docstring. Если дефолт без этой ветки не сходится — портировать её в `pad_print.py` в этой задаче. Калькулятор не на боевой форме API, предпосылку не заводить. Новые строки в allowed не добавлять.
- На проде (Site ops): дубль формы 38 на черновик после совпадения дефолта с боевым API. Если порт менял ответ — сначала `deploy-api` с `main`, потом дубль. JS копии в элементе (`read_file=0`). Плагин не выкладывать. Боевую 38 не переключать.
- Строка для будущего пакета — в «Результат», не в `todo/forms-batch-switch.md`.

## Файлы

- `wp-plugin/forms/pad_print.js`
- `calc_service/calculators/pad_print.py`
- `calc_service/tests/test_calculators/test_pad_print.py`
- WordPress: только копия формы 38 и её черновик

## Не-scope

- `todo/forms-batch-switch.md`, `docs/site/forms.md`, `docs/js-runner-cases.md`
- Новые строки в `scripts/js_port_gaps_allowed.txt`. Чужие калькуляторы.
- Боевая форма 38, выкладка плагина, JSON цен, `calc_service/calculators/__init__.py`

## Критерии приёмки

- [x] `python scripts/js_port_gaps.py calcPadPrint` — пропуск `Material` либо снят, либо назван в docstring и остаётся в allowed. Других непустых `нет в Python` без записи в обоих местах нет. `python scripts/js_port_gaps.py --check` печатает `ok`.
- [x] `python -m pytest calc_service/tests/test_calculators/test_pad_print.py calc_service/tests/test_wp_plugin_forms.py -q` — `passed`. Есть `REF_FORM_DEFAULT` с `# JS,`.
- [x] Боевой `POST /api/v1/calc/pad_print` на теле `REF_FORM_DEFAULT`: `price` и `time_ready` как у раннера (допуск цены abs ≤ 0.02 или rel ≤ 0.001, срока rel ≤ 0.001). Если порт ещё не выкачен — пункт после `deploy-api`, копию до него не принимать.
- [x] `Select-String -Path wp-plugin\forms\pad_print.js -Pattern "calcApi\('pad_print'|syncUrl\(|showResult\("` — все три есть. Своей `price` и `querySelector` нет.
- [x] Копия не на витрине: `draft` или `private`, гость без cookies — не `200`.
- [x] На копии под админом дефолт даёт `POST /api/v1/calc/pad_print` → 200. Цена на странице = `price` API с округлением `showResult`.
- [x] URL копии обновляется GET-именами формы 38. Ссылка с этими GET открывает те же значения и ту же цену.
- [x] Боевая страница в HTML содержит `calcPadPrint`, не `calcApi`.

## Проверки

- [x] `python scripts/dev.py check` — код выхода 0
- [x] Self-review — чеклист «Перед сдачей» в [AGENTS.md](../AGENTS.md)

## Риски

- Прод: боевая форма 38 не меняется. Выкатка API — только если менялся калькулятор, с `main` после ревью. Запись в формы не параллельно с `todo/ezfc-options-source-reset.md`.
- Цены: JSON не менять.
- Формы: id боевой 38 не менять.

## Режим

прод

## Журнал передач

19.11.2026 — Analyst, Grok 4.7 — задача заведена, пачка 4, пропуск Material — дальше Implementer
22.11.2026 — Implementer, Gemini 4 Hydrogen High — шаги 0–5б и wp-plugin/forms/pad_print.js готовы, make check зелёный — дальше Site ops (шаги 6–16)
22.11.2026 — человек — подождать освобождения prod (form-vizitki-promo) — дальше Site ops
22.11.2026 — Site ops, Grok 4.7 — копия формы 110 на черновике 2586906, дефолт API 3436 ₽ / 9.26 ч, страница 3 500 ₽, боевая 38 не переключена — дальше Reviewer
22.11.2026 — Reviewer, Grok 4.7 — принято: `pad_print.js`, `REF_FORM_DEFAULT`, отчёт Site ops по копии 110 — дальше человек (`finish-task`)
22.11.2026 — человек — принято — закрытие

## Найдено вне scope

- `scripts/run_js_calc.mjs`: `calcPadPrint.js` не подключён в раннере (эталон снят прямым прогоном `js_legacy/calc/calcPadPrint.js` в Node vm с `calc_service/data/common.json` и `equipment/tools.json`).
- `js_legacy/calc/calcPadPrint.js` при `n > 100` (`REF_PARAMS`, `n=500`): `nameMaterials` содержит одновременно `costSmallTampon` и `costLargeTampon`, после чего `if (diffPrint == 0)` добавляет выбранный тампон второй раз (`7943 ₽` в JS против `7393 ₽` в `pad_print.py` / `EXPECTED_REF`); на `n <= 100` (`REF_FORM_DEFAULT`, `n=100`) `ceil(n/100) - 1 == 0`, расхождение ~0.04 ₽ и цены сходятся точно (`3001 / 3436 / 3972 ₽`).

## Результат

- Ветка, PR или коммит: `task/form-pad-print`
- Период: 2026-11-19 — 2026-11-22
- Часы человека: оценка 8 ч
- Работа агентов: Implementer (Gemini 4 Hydrogen High), Site ops (Grok 4.7)
- Было / стало: не было `wp-plugin/forms/pad_print.js` и `REF_FORM_DEFAULT`; `calcPadPrint option Material` числился в `js_port_gaps_allowed.txt` / добавлен `wp-plugin/forms/pad_print.js` (id боевой формы 38), в docstring `pad_print.py` зафиксирован перенос `Material` → `material_mode` и убрана строка из `scripts/js_port_gaps_allowed.txt` (логика и ответы `pad_print.py` не менялись, `deploy-api` не требуется), в `test_pad_print.py` добавлены `REF_FORM_DEFAULT`, режимы `0/1/2` и тест опций. Строка для будущего `forms-batch-2` (не в текущий пакет): форма 38 CalcPadPrint → `pad_print`, копия 110, черновик 2586906, превью https://insain.ru/?post_type=product&p=2586906&preview=true . Боевая https://insain.ru/catalog/tampopechat/ остаётся на `insaincalc.calcPadPrint`.
- Сделано:
  - Шаги 0–5б: снят ложный пропуск `Material` (опция уже реализована как `material_mode`); сверены JS vs Python/боевой API на дефолте формы 38 (`100`, `isSmallItems`, `1`, `mode=0/1/2` → `3001 / 3436 / 3972 ₽`, `25.11 / 9.26 / 2.41 ч`) и на кейсе с опциями (`14396 ₽`, `12.04 ч`); `materials` пуст и в JS, и в API.
  - Создан `wp-plugin/forms/pad_print.js` (форма 38, `cjsCalc` 1448): `numN` (1433), `dpdPreset` (1434), `dpdColor` (1435), `dpdSurfaceMaterial` (1442 — не влияет на расчёт, пишется только в `syncUrl`), `ckbPantone` (1444), `ckbMaterialCustomer` (1445), `ckbPacking` (1446), `rdoModeProduction` (1462). `fluAtrwork` (1447) в URL не кладётся.
  - Аргументы `--get` для шага 10 (`Site ops`): `--get numN --get dpdPreset:index --get dpdColor:index --get dpdSurfaceMaterial:index --get ckbPantone:index --get ckbMaterialCustomer:index --get ckbPacking:index --get rdoModeProduction:value`.
  - Дописка для общих файлов при слиянии: `docs/js-runner-cases.md` — `calcPadPrint` в `run_js_calc.mjs` не подключён; дефолт формы 38 (`100`, `isSmallItems`, `1`, `mode=0/1/2`) → `price` `3001 / 3436 / 3972`, `time_ready` `25.11 / 9.26 / 2.41` (22.11.2026); в будущий `forms-batch-2` — форма 38 `CalcPadPrint` → `pad_print`.
- Чем проверено: `python scripts/js_port_gaps.py calcPadPrint` (`нет в Python:` пусто); `python scripts/js_port_gaps.py --check` (`ok`); `python -m pytest calc_service/tests/test_calculators/test_pad_print.py calc_service/tests/test_wp_plugin_forms.py calc_service/tests/test_js_port_gaps.py -q` (`25 passed`); `Invoke-RestMethod` к `https://insain.ru/api/v1/calc/pad_print` (`mode=0/1/2` → `3001 / 3436 / 3972 ₽`, `25.11 / 9.26 / 2.41 ч`); `Select-String` по `wp-plugin\forms\pad_print.js`; `python scripts/dev.py check` (exit 0).
- Сделано (Site ops, шаги 6–16):
  - Дубль формы 38 → форма **110** `CalcPadPrint duplicate` (одна новая строка). Черновик товара **2586906** «Тампопечать (Копировать)», `post_status=draft`, `ezfc_form_id=110`. Боевой товар 2253730 остался `publish` / форма 38.
  - JS копии из `wp-plugin/forms/pad_print.js` (`read_file=0`, `calcApi=1`), GET: `numN`, dropdown `:index`, чекбоксы `:index`, `rdoModeProduction:value`. Повторная запись GET после сохранения блока результата (радио снова `value`). Бэкап `/tmp/ezfc-copy-110-20261121-204735.json`.
  - Блок результата на копии как у формы 79: `grpPrice` (менеджер «цена» + скрытые `sbtPriceTotalDiscount` / `sbtPriceDiscount`, `calculate_when_hidden=1`), `htmCost` со скидкой, режим внутри `grpTime`, `htmTime` без класса на обёртке, `grpMaterial` / `htmMaterial`. Удалены на копии заголовок «Цена» и группа клиентских `sbtPrice` / `sbtPriceTotal`.
  - Плагин не выкладывался. Калькулятор не деплоился. Шаги 17–24 не делались. Боевая форма 38 не переключалась.
- Чем проверено (Site ops):
  - Гость: `curl.exe -s -o NUL -w "%{http_code}" "https://insain.ru/?post_type=product&p=2586906"` → `404`. `wp post get 2586906 --field=post_status` → `draft`.
  - Флаги шага 13а: менеджерские `hidden=0`; скидка `hidden=1`, `calc_hidden=1`.
  - Под админом `https://insain.ru/?post_type=product&p=2586906&preview=true`: `POST /api/v1/calc/pad_print` 200, тело `quantity=100, size_item=isSmallItems, color=1, mode=1` → `price=3436`, `time_ready=9.26`. На странице `3 500 руб.` (`insaincalc.round(3436, 100)=3500`), «со скидкой» `2 442 руб.` (не 0), срок «1 день» (`timeToWords(9.26)`), подсказка дат на `<a>`.
  - Смена `dpdPreset` / `dpdColor` и чекбоксов меняет тело POST и цену; `dpdSurfaceMaterial` пишется в URL и в расчёт не входит (как в `pad_print.js`). `materials` пустой и в API. Режим 0 по ссылке: радио `0`, страница `3 100 руб.` (`round(3001, 100)`), срок «3 дня» (`timeToWords(25.11)`).
  - URL копии — GET-имена формы 38. Перезагрузка `…&dpdPreset=1&dpdColor=1&rdoModeProduction=2&ckbPantone=0&ckbMaterialCustomer=0&ckbPacking=0` оставляет те же значения; POST `mode=2`, `price=15737` → на странице `15 800 руб.`.
  - Боевая страница: `curl` `https://insain.ru/catalog/tampopechat/` — в HTML `insaincalc.calcPadPrint` и `get_value_from(1433)` / `1462`, вызова `calcApi` нет. `wp litespeed-purge all` вернул `Got 400`; `wp cache flush` — `Success`. Проверка копии шла под админом.
- Не сделано и почему: шаги 17–24 (боевая форма, снимок, реестр) вне этой сессии. Плагин не выкладывался.
- Как откатить: форма 110 и черновик 2586906 нигде не опубликованы; удаление — только с подтверждением человека. JS/GET копии — бэкап `/tmp/ezfc-copy-110-20261121-204735.json`. Боевую 38 откатывать не нужно.
- Требуется решение: после приёмки копии строка идёт в будущий `forms-batch-2`, не в текущий пакет. Дописка для общих файлов при слиянии уже в «Сделано» Implementer.

## Ревью 1

**Итог:** принято.

**Критерии (diff + команды этой сессии; копию и боевую форму не открывал, пункты 5–8 — отчёт Site ops):**

| Критерий | Статус |
| --- | --- |
| `js_port_gaps.py calcPadPrint`: пропуск `Material` снят, других `нет в Python` нет; `--check` → `ok` | ok — `options: isPantone, isPacking, Material`, `нет в Python:` пусто, `--check` → `ok`. Строка `calcPadPrint option Material` снята из allowed. В `pad_print.py` уже есть `material_mode == "isMaterialCustomer"` → `defects += 0.25`, как в JS; в diff калькулятора только docstring |
| pytest `test_pad_print.py` + `test_wp_plugin_forms.py` — `passed`, есть `REF_FORM_DEFAULT` с `# JS,` | ok — `20 passed`. Эталон `# JS, 22.11.2026`; режимы 0/1/2: `3001 / 3436 / 3972`, `25.11 / 9.26 / 2.41` |
| Боевой `POST /api/v1/calc/pad_print` на теле `REF_FORM_DEFAULT` | ok — ответ калькулятора не менялся, `deploy-api` не нужен. Дефолт `3436` / `9.26` совпадает с отчётами Implementer и Site ops |
| `pad_print.js`: `calcApi('pad_print'`, `syncUrl(`, `showResult(`; своей `price` и `querySelector` нет | ok — `Select-String`: три вызова, совпадений `price` и `querySelector` нет |
| Копия не на витрине: `draft`, гость не `200` | ok — Site ops: товар 2586906 `draft`, curl гостя `404` |
| Дефолт копии: `POST` 200, цена на странице = `price` с округлением `showResult` | ok — Site ops: тело `quantity=100, size_item=isSmallItems, color=1, mode=1` → `3436` / `9.26`, на странице `3 500 руб.`. `insaincalc.round(3436, 100)` = 3500; режим 0: `3001` → `3 100 руб.` |
| URL копии — GET-имена формы 38; ссылка открывает те же значения и ту же цену | ok — Site ops: перезагрузка `dpdPreset=1&dpdColor=1&rdoModeProduction=2&ckbPantone=0&ckbMaterialCustomer=0&ckbPacking=0` → POST `mode=2`, `price=15737`, страница `15 800 руб.` (`round(15737, 100)`) |
| Боевая страница: в HTML `calcPadPrint`, нет `calcApi` | ok — Site ops: `curl` https://insain.ru/catalog/tampopechat/ содержит `insaincalc.calcPadPrint`, вызова `calcApi` нет |

**Инварианты:** в diff нет цен, наценок и курсов в Python и JSON. Ответ `calculate()` не менялся: `cost`, `price`, `unit_price`, `time_hours`, `time_ready`, `weight_kg`, `materials`. Внутренние `code` на страницу не пишутся (`materials` пустой). Scope: docstring `pad_print.py`, `test_pad_print.py`, `wp-plugin/forms/pad_print.js`, снятие строки allowed. `docs/dashboard.md` в diff при правке `todo/` — не замечание. Общие файлы не правились.

**Замечания:**

- `желательно` — правки ещё не закоммичены; `task/form-pad-print` на 2 коммита позади `main` (закрытие `form-vizitki-promo`, файлы задачи не пересекаются). При закрытии: коммит в worktree, затем fast-forward. Если ff не проходит — rebase; конфликт только в `docs/dashboard.md` пересобрать.
- `желательно` — при закрытии перенести дописку из «Результат»: строка `calcPadPrint` в `docs/js-runner-cases.md`; форма 38 `CalcPadPrint` → `pad_print` в будущий `forms-batch-2`, не в текущий `todo/forms-batch-switch.md`.

**Вне scope:** двойной тампон в JS при `n > 100` и отсутствие `calcPadPrint` в `run_js_calc.mjs` уже в «Найдено вне scope». На дефолте формы (`n = 100`) цена сходится. Блокеров нет.
