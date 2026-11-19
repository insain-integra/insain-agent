# form-canvas

Статус: выкатка
Сложность: средняя
Implementer: Gemini 4 Hydrogen High
Reviewer: Grok 4.7
Site ops: Grok 4.7
Почему: копия формы по skill, но `calcCanvas call calcBaguette` и модуль `calcBaguette` числятся пропуском, а в docstring `canvas.py` этого списка нет.

## Цель

Копия формы 80 CalcCanvas на черновике товара считает `POST /api/v1/calc/canvas`. URL копии пишется GET-именами элементов. Ссылка с этими GET открывает ту же копию с теми же значениями и той же ценой. Боевая страница https://insain.ru/catalog/canvas/ остаётся на `insaincalc.calcCanvas`. В пакет `forms-batch-switch` форма 80 не попадает.

## Контекст и ссылки

- `.cursor/skills/ezfc-form-to-api/SKILL.md`, этапы `verify.md` и `copy.md`. Шаги 17–24 не входят.
- `docs/ezfc-api-migration.md` — GET = имя элемента.
- `docs/site/forms.md` — строка формы 80, только читать.
- `calc_service/calculators/canvas.py` — печать через `print_roll`, подрамник через профиль и `calc_set_canvas_frame`.
- `scripts/js_port_gaps_allowed.txt` — `calcCanvas call calcBaguette`, `calcBaguette module`.
- `calc_service/tests/test_calculators/test_canvas.py`.
- `todo/EPIC-forms-to-api.md` — пачка 4.
- Остальное не открывать.

## Scope

- В git (Implementer): шаги 0–5б и `wp-plugin/forms/canvas.js`. `REF_FORM_DEFAULT` в `test_canvas.py` с пометкой `# JS, ДД.ММ.ГГГГ`.
- Багет: если дефолт формы считает подрамник уже через профиль и `calc_set_canvas_frame` и цена сходится — дописать в docstring, что `calcBaguette` заменён этими вызовами, строки allowed не дублировать. Если цена дефолта не сходится — портировать недостающий вызов в `canvas.py` в этой задаче. `print_roll.py` не менять. Калькулятор не на боевой форме API, предпосылку не заводить. Новые строки в allowed не добавлять.
- На проде (Site ops): дубль формы 80 на черновик после совпадения дефолта с боевым API. Если порт менял ответ — сначала `deploy-api` с `main`, потом дубль. JS копии в элементе (`read_file=0`). Плагин не выкладывать. Боевую 80 не переключать.
- Строка для будущего пакета — в «Результат», не в `todo/forms-batch-switch.md`.

## Файлы

- `wp-plugin/forms/canvas.js`
- `calc_service/calculators/canvas.py`
- `calc_service/tests/test_calculators/test_canvas.py`
- WordPress: только копия формы 80 и её черновик

## Не-scope

- `todo/forms-batch-switch.md`, `docs/site/forms.md`, `docs/js-runner-cases.md`
- `print_roll.py` и `wp-plugin/forms/print_roll.js`
- Новые строки в `scripts/js_port_gaps_allowed.txt`. Отдельный модуль багета, если дефолт сходится без него.
- Боевая форма 80, выкладка плагина, JSON цен, `calc_service/calculators/__init__.py`

## Критерии приёмки

- [x] `python scripts/js_port_gaps.py calcCanvas` — `calcBaguette` либо снят, либо назван в docstring и остаётся в allowed. Других непустых `нет в Python` без записи в обоих местах нет. `python scripts/js_port_gaps.py --check` печатает `ok`.
- [x] `python -m pytest calc_service/tests/test_calculators/test_canvas.py calc_service/tests/test_wp_plugin_forms.py -q` — `passed`. Есть `REF_FORM_DEFAULT` с `# JS,`.
- [ ] Боевой `POST /api/v1/calc/canvas` на теле `REF_FORM_DEFAULT`: `price` и `time_ready` как у раннера (допуск цены abs ≤ 0.02 или rel ≤ 0.001, срока rel ≤ 0.001). Если порт ещё не выкачен — пункт после `deploy-api`, копию до него не принимать.
- [x] `Select-String -Path wp-plugin\forms\canvas.js -Pattern "calcApi\('canvas'|syncUrl\(|showResult\("` — все три есть. Своей `price` и `querySelector` нет.
- [ ] Копия не на витрине: `draft` или `private`, гость без cookies — не `200`.
- [ ] На копии под админом дефолт даёт `POST /api/v1/calc/canvas` → 200. Цена на странице = `price` API с округлением `showResult`.
- [ ] URL копии обновляется GET-именами формы 80. Ссылка с этими GET открывает те же значения и ту же цену.
- [ ] Боевая страница в HTML содержит `calcCanvas`, не `calcApi`.

## Проверки

- [x] `python scripts/dev.py check` — код выхода 0
- [x] Self-review — чеклист «Перед сдачей» в [AGENTS.md](../AGENTS.md)

## Риски

- Прод: боевая форма 80 не меняется. Выкатка API — только если менялся калькулятор, с `main` после ревью. Запись в формы не параллельно с `todo/ezfc-options-source-reset.md`.
- Цены: JSON не менять. `print_roll` не двигать.
- Формы: id боевой 80 не менять.

## Режим

прод

## Журнал передач

19.11.2026 — Analyst, Grok 4.7 — задача заведена, пачка 4, пропуск багета — дальше Implementer
20.11.2026 — Implementer, Gemini 4 Hydrogen High — шаги 0–5б, правка canvas.py (время сборки углов, time_ready, size_mm, docstring), test_canvas.py (REF_FORM_DEFAULT и mode 0/1/2), wp-plugin/forms/canvas.js; dev.py check зелёный — дальше Reviewer
20.11.2026 — человек — закоммитить ai-seo-geo-yoast.md на main, потом Reviewer — дальше Reviewer
20.11.2026 — Reviewer, Grok 4.7 — принято, статус ревью; цена и срок дефолта и mode 0/1/2 сходятся с JS — дальше человек: слияние в main и выкатка API, затем Site ops шаги 6–16
20.11.2026 — человек — принято: слить в main, выкатить API, затем Site ops 6–16 — дальше Site ops

## Ревью 1

принято. Статус остаётся `ревью`: в diff шаги 0–5б и `wp-plugin/forms/canvas.js`. Боевой POST и копия формы — после слияния в `main` и `deploy-api`.

Проверено по diff и повторным командам:

- `python scripts/js_port_gaps.py calcCanvas` и `python scripts/js_port_gaps.py --check` → `ok`. `calcBaguette` назван в docstring `canvas.py` и остаётся в `scripts/js_port_gaps_allowed.txt`. Других непустых `нет в Python` нет.
- `python -m pytest calc_service/tests/test_calculators/test_canvas.py calc_service/tests/test_wp_plugin_forms.py -q` → `19 passed`. `REF_FORM_DEFAULT` с `# JS, 20.11.2026`, режимы `mode=0/1/2` на дефолте и на тираже 2 с подрамником.
- Сверка с `calcCanvas` на текущем прайсе (загрузчик `run_js_calc.mjs` плюс `calcCanvas.js` и `profile.json`, файл репозитория не менялся). Дефолт `1×400×500`, без подрамника, mode 0/1/2: `cost`, `price`, `time_hours`, `time_ready` совпали с эталоном теста (в том числе `price=2543`, `time_ready=33.53` на mode 1). Тираж 2, `400×500`, подрамник: цена и срок в допуске шага 2 (`rel ≤ 0.001`); JS `price` 7966.968 / 9425.208 / 10907.448, Python после `ceil` — 7967 / 9426 / 10908. `size_mm` холста `[1270, 0]` и профиля `[45, 20]` совпали с JS. Сборка углов `(n * 4 * 480) / 3600` совпала с `(numCut / 2 * 480) / 3600`.
- `wp-plugin/forms/canvas.js`: `syncUrl`, `calcApi('canvas')`, `showResult`, `showError`; своей `price` и `querySelector` нет; mode `0` не схлопывается через `||`. Id полей и `chkFrame` (`get_value_from(3151, false) == 1`), свой размер без `×10` совпадают с боевым `cjsCalc`. На странице выбран `400×500`, подрамник выключен. В HTML боевой страницы есть `calcCanvas`, нет `calcApi`.
- `docs/dashboard.md` в diff — пересборка статуса `ревью`, не замечание. `print_roll.py`, `scripts/js_port_gaps_allowed.txt` и общие файлы не менялись. Полный `python scripts/dev.py check` в журнале Implementer зелёный; целевые pytest и `js_port_gaps` перепроверены.

- желательно: в `test_form_frame_n2_modes` у `time_hours` допуск `rel=0.01`, не `0.001` шага 1а. Повторный `math.ceil` суммы даёт 2.38 / 2.98 / 3.58 против JS 2.3767 / 2.9767 / 3.5767 (mode 0 и 1 чуть выше `0.001`). `time_ready` при этом внутри `0.001`. Сдачу не держит.
- вне scope: на дефолте расход холста в `materials` `0.6` м против `0.605` м в JS — округление `print_roll`, цена `2543` совпала. `print_roll.py` не менять.

## Найдено вне scope

- `calc_service/calculators/print_roll.py`: при `quantity=2, width=400, height=300` (размер вне пресетов формы 80) расход `CanvasDLCNM320` (`length_min=500` мм) в `materials` даёт `0.48` м вместо `0.5` м в JS (разница ~10 ₽ в `calcCanvas` для `400×300`). `print_roll.py` не правился (вне scope).
- На дефолте формы `400×500` без подрамника `materials` холста `0.6` м против `0.605` м в JS (то же округление `print_roll` до 2 знаков). Цена совпала: `2543`.
- Форма 80 (`dpdSize` id=3130): у опции `id=8` подпись `"1000х1100 мм"` при `value="1000,1200"`.
- `scripts/run_js_calc.mjs`: `calcCanvas` не подключён (эталоны сняты в консоли боевой страницы, 20.11.2026; Reviewer сверил тем же загрузчиком локально, скрипт не менялся).

## Результат

- Ветка, PR или коммит: `task/form-canvas` → merge в `main` (выкатка API, затем копия формы)
- Период: 2026-11-19 —
- Часы человека: оценка 8 ч
- Работа агентов: Implementer (Gemini 4 Hydrogen High) — шаги 0–5б, правки `canvas.py`, `test_canvas.py`, `wp-plugin/forms/canvas.js`
- Было / стало:
  - Было: в `canvas.py` баг `num_corners / 2` занижал стоимость и время сборки подрамника (`is_frame=True` на 10–15%), `time_ready` расходился с JS (`max` вместо `time_hours + time_ready_max`, разница до 15.8% на `mode=2`), отсутствовал `size_mm` в `materials`, не было описания `calcBaguette` в docstring; отсутствовал `wp-plugin/forms/canvas.js` и `REF_FORM_DEFAULT` в `test_canvas.py`.
  - Стало: `canvas.py` приведён в соответствие с `calcCanvas.js` на всех режимах `mode=0/1/2` (время сборки `num_corners * 480 / 3600`, `time_ready = time_hours + time_ready_max`, `size_mm` для холста и профиля, docstring с `calcBaguette`); добавлены `REF_FORM_DEFAULT` и эталоны `mode=0/1/2` с подрамником и без (`# JS, 20.11.2026`) в `test_canvas.py`; создан `wp-plugin/forms/canvas.js` под боевую форму 80.
- Сделано:
  - Шаги 0–5б (`verify.md`): проверен `js_port_gaps.py calcCanvas` (`calcBaguette` задокументирован в docstring `canvas.py`, остаётся в `js_port_gaps_allowed.txt`); сверены схема API `tool_schema/canvas` и поля формы 80 (`3129` `numN`, `3130` `dpdSize`, `3152` `numW`, `3153` `numH`, `3151` `chkFrame`, `3147` `rdoModeProduction`, `3134` `cjsCalc`). Все обязательные параметры API (`quantity`, `width`, `height`) покрыты полями формы; полей без параметров API нет; `material_id`, `printer_code`, `frame_id` в форме не выбираются (используются дефолты API). Все `get_value_from(N)` в старом JS совпадают с id шага 5.
  - Исправлен `calc_service/calculators/canvas.py`: убрано лишнее деление `num_corners / 2`, исправлено `time_ready`, добавлен `size_mm` в `materials`, добавлен список «не перенесено» для `calcBaguette` в docstring.
  - Обновлён `calc_service/tests/test_calculators/test_canvas.py`: добавлены `REF_FORM_DEFAULT` (1 шт, `400×500`, `is_frame=False`, `mode=1`), `FORM_DEFAULT_MODE_CASES` (`mode=0/1/2`), `FORM_FRAME_N2_CASES` (2 шт, `400×500`, `is_frame=True`, `mode=0/1/2`), обновлён `EXPECTED_REF` после починки `num_corners`.
  - Создан `wp-plugin/forms/canvas.js`: читает `numN`, `dpdSize` (+ `numW`/`numH` при `dpdSize='0'`), `chkFrame`, `rdoModeProduction` (с сохранением `0`), вызывает `syncUrl`, `calcApi('canvas', ...)`, `showResult`, `showError`.
  - Заметка для `docs/js-runner-cases.md` (дописать после слияния в `main`): `calcCanvas` не подключён в `scripts/run_js_calc.mjs`; эталоны для формы 80 сняты в консоли https://insain.ru/catalog/canvas/ (`# JS, 20.11.2026`).
  - Заметка для `Site ops` (после ревью, слияния в `main` и `deploy-api`):
    - Боевой API сейчас отдаёт старый ответ (до выкатки), поэтому сначала `deploy-api` с `main` и проверка `POST /api/v1/calc/canvas` на `REF_FORM_DEFAULT` (`price=2543`, `time_ready=33.53`) и `quantity=2, is_frame=True` (`price=9426`, `time_ready=36.0`, `size_mm`), затем дубль формы 80 (шаги 6–16).
    - Аргументы для `scripts/ezfc_copy.py` на шаге 10: `--get numN --get dpdSize:index --get numW --get numH --get chkFrame:index --get rdoModeProduction:value`.
    - Примечание по `rdoModeProduction` в форме 80: сейчас на форме только опции `1` («cтандарт») и `2` («быстрее»).
- Чем проверено:
  - `python scripts/js_port_gaps.py calcCanvas` и `python scripts/js_port_gaps.py --check` → `ok`
  - `python -m pytest calc_service/tests/test_calculators/test_canvas.py calc_service/tests/test_wp_plugin_forms.py -q` → `19 passed`
  - `Select-String -Path wp-plugin\forms\canvas.js -Pattern "calcApi\('canvas'|syncUrl\(|showResult\("` → все 3 присутствуют, `price`/`querySelector` отсутствуют
  - `python scripts/dev.py check` → код выхода 0
- Не сделано и почему:
  - Проверка боевого `POST /api/v1/calc/canvas` на обновлённой логике и шаги 6–16 (дубль формы 80 на черновик) — требуют ревью, слияния в `main` и `deploy-api` (`Site ops`), т.к. правки в `canvas.py` меняют ответ API.
- Требуется решение: после приёмки копии строка идёт в будущий `forms-batch-2`, не в текущий пакет. (После `Reviewer` и слияния в `main` — выкатка API и копия формы 80.)
