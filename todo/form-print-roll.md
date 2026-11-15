# form-print-roll

Статус: выкатка
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
- Цены, `calc_service/data/`, `scripts/run_js_calc.mjs`. Ламинация в `calc_service/calculators/print_roll.py` — в scope с 16.11.2026: человек не принял копию, калькулятор не на боевых формах, отдельный `todo/<fix>.md` не заводить. Из `scripts/js_port_gaps_allowed.txt` снимается только строка `calcPrintRoll call calcLaminationWide` (пропуск закрыт), `MAX_ALLOWED` 71 → 70.
- Калькулятор и slug `print_wide`. Остальные формы эпика.
- Удаление копии и черновика.

## Критерии приёмки

- [x] `python scripts/js_port_gaps.py calcPrintRoll` — в блоке `calcPrintRoll` строка `нет в Python:` пустая или каждая позиция уже есть в `scripts/js_port_gaps_allowed.txt`.
- [x] Раннер и `POST https://insain.ru/api/v1/calc/print_roll` на эталоне и на дефолте формы 23: `price` abs ≤ 0.02 и rel ≤ 0.001, `time_ready` rel ≤ 0.001. Иначе стоп, форму не дублировать.
- [x] `python -m pytest calc_service/tests/test_calculators/test_print_roll.py calc_service/tests/test_wp_plugin_forms.py -q` — `passed`, `failed` нет. В тесте есть `REF_FORM_DEFAULT` с пометкой `# JS, ДД.ММ.ГГГГ`.
- [x] `Select-String -Path wp-plugin\forms\print_roll.js -Pattern "calcApi\('print_roll'|syncUrl\(|showResult\("` — все три вхождения есть.
- [x] Ламинация, дефолт А0: раннер и локальный расчёт `cost` 1443, `price` 2335, `time_ready` 16.55 (rel 0.001). Эталон 14291 и дефолт без ламинации 1544 не сдвинулись.
- [x] `test_form_default_lamination_print_roll` без правки `print_roll.py` — failed (старый cost 955, price 1544, time_ready 16.52); остальные тесты файла passed. После возврата правки — passed.
- [x] Соседи, которые вызывают `PrintRollCalculator` (`canvas`, `rollup`, `presswall`) — passed.
- [x] Копия не на витрине: `wp post get PRODUCT --field=post_status` — `draft` или `private`; `curl.exe` без cookies на `/?post_type=product&p=PRODUCT` — `404`.
- [x] На копии под админом эталон даёт `POST /api/v1/calc/print_roll` → 200. Цена на странице равна `price` API с округлением `showResult`.
- [x] URL обновляется GET-именами формы. Ссылка с этими GET открывает копию с теми же значениями и той же ценой. Дефолт восстанавливается (1 600). Ссылка с люверсами: `numStepEyelets=30`, радио «одинаковая» (`rdoProcessEdge=0`), на странице 12 650.

## Проверки

- [x] `python scripts/dev.py check` — код выхода 0
- [x] Self-review — чеклист «Перед сдачей» в [AGENTS.md](../AGENTS.md)

## Риски

- Прод: дубль и GET только с подтверждения человека. Боевая страница клиентам не меняется.
- Цены: JSON не править. Ламинация 16.11 чинится в `print_roll.py` без смены JSON: калькулятор не на боевых формах. Другое расхождение JS и API (rel > 0.001) — стоп.
- Формы: id элементов боевой формы 23 не менять. В админке пишется только копия.

## Режим

прод

## Журнал передач

Строка на сессию: `<дата> — <роль>, <модель> — <итог> — дальше <роль>`. Блокер — по формату [docs/agents/workflow.md](../docs/agents/workflow.md).

15.11.2026 — Implementer, Grok 4.7 — эталон и дефолт формы 23 сходятся с боевым API, JS и REF_FORM_DEFAULT в git — дальше Reviewer

15.11.2026 — Reviewer, Auto — git-часть по коду ок, блокер: нет коммита и print_roll.js вне индекса — дальше Implementer

15.11.2026 — человек — блокер «нет коммита» снят: коммит при закрытии; sameEdges не трогать; дубль формы 23 на черновике разрешён, боевую форму не трогать — дальше Site ops

15.11.2026 — Site ops, Grok 4.7 — копия 99 на черновике 2586893 считает print_roll, цена на странице равна округлению API; ссылка GET с люверсами не восстанавливает шаг и радио 0 — дальше человек

15.11.2026 — человек — URL шага люверсов писать в сантиметрах поля, разобрать радио value 0, sameEdges не менять; затем снова Site ops — дальше Implementer

16.11.2026 — Implementer, Grok 4.7 — в URL шаг люверсов в сантиметрах поля, радио value 0 отмечается и считается как «одинаковая»; sameEdges не менялся — дальше Site ops

16.11.2026 — Site ops, Grok 4.7 — JS копии 99 перезаписан из git, ссылка с шагом 30 см и радио 0 снова открывает 12 650 — дальше человек

16.11.2026 — человек — копию не принимать: ламинация не считается, при выборе результат тот же — дальше Implementer

16.11.2026 — человек — копию не принимать: ламинация не считается, при выборе результат тот же — дальше Implementer

16.11.2026 — Implementer, Grok 4.7 — ламинация дефолта А0 совпала с раннером: price 2335, time_ready 16.55; эталоны 1544 и 14291 на месте — дальше Reviewer

16.11.2026 — человек — незакоммиченный docs/dashboard.md на main убрать, Reviewer продолжить — дальше Reviewer

16.11.2026 — Reviewer, Auto — ревью 2: ламинация и gaps принято; ветка за main на 1 коммит, `print_roll.js` untracked — дальше человек

16.11.2026 — человек — принято: слить, push, выкатить API, Site ops проверяет ламинацию на копии 99, затем закрыть — дальше выкатка

```text
Блокер: ссылка с GET люверсов не открывает ту же цену
Пробовал: форма 99, товар 2586893 draft, гость curl 404. Под админом дефолт POST print_roll 200, на странице 1 600 = round(1544, 1). Люверсы 300 мм: POST is_eyelet [300,300,300,300], API price 12631, на странице 12 650. Та же ссылка заново: шаг зажат до 50, радио value 0 не выбрано, цена 7 000. Дефолтная ссылка снова даёт 1 600.
Гипотеза: в URL шаг пишется уже с factor 10 (мм), поле в см и max 50; ezFC не отмечает радио со value 0. sameEdges не менялся. Одним списком форма шлёт либо резку, либо люверсы, не оба сразу (эталон API 14291).
Вопрос: принять копию с этой оговоркой, вернуть правку URL шага Implementer, или оставить черновик без закрытия
Следующая сессия: человек, затем Site ops или Implementer по выбору
```

## Ревью 1

**Итог:** не принято (один **блокер**); статус **доработка**.

**Сверка критериев (git, локально):**

| Критерий | Статус |
| --- | --- |
| `js_port_gaps.py calcPrintRoll` | ок: единственный пропуск `call calcLaminationWide` в allowlist |
| Раннер / боевой API эталон и дефолт | перепроверка Implementer принята; rel в норме |
| `pytest test_print_roll.py` + `test_wp_plugin_forms.py` | 22 passed (повтор ревью) |
| Паттерны в `print_roll.js` | `syncUrl`, `calcApi('print_roll'`, `showResult`, `showError` — есть |
| `make check` / `dev.py check` | 622 + 81 passed |
| Не-scope (print_roll.py, data, боевая 23) | в diff нет |
| Копия на проде (критерии 54–56) | вне круга Reviewer — Site ops после git |

**Инварианты diff:** своих `price=` и `querySelector` нет; `width`/`height` в мм согласованы с API; режим через `modeRaw`, не `|| 1`; `REF_FORM_DEFAULT` с `# JS, 15.11.2026` и тестом `test_form_default_print_roll`. Ламинация и `size_mm` — без замечаний (уже в «Найдено вне scope»).

**Замечания:**

1. **блокер:** Ветка без коммита: `git diff main` не содержит `wp-plugin/forms/print_roll.js` (untracked). Для слияния и CI нужен коммит с `print_roll.js`, `test_print_roll.py`, `todo/form-print-roll.md` (изменения `docs/dashboard.md` — от `make check`, в коммит по правилам репо).
2. **желательно:** `sameEdges = processNum === 1` при описании в «Результат»: индекс/value **0** — «одинаковая», **1** — «разная». Если в боевом cjsCalc иначе — сослаться в комментарии; иначе ожидается `processNum === 0`. На копии проверить сценарий эталона (резка + люверсы 300, одинаковая обработка).
3. **желательно:** Строки раннера из «Результат» в `docs/js-runner-cases.md` — при слиянии (уже зафиксировано в задаче).

**Дописка в «Результат» (общие файлы не правились):** при слиянии в `docs/js-runner-cases.md` — две команды раннера из блока «Результат» (эталон 14291, дефолт 1544).

## Ревью 2

**Итог:** **принято**; статус **`ревью`**, дальше человек (слияние, деплой API, приёмка копии с ламинацией).

**Круг:** diff после ревью 1 (коммит при закрытии — по решению 15.11) и блокеров Site ops по URL; починка `is_lamination` в `print_roll.py`, снятие `calcPrintRoll call calcLaminationWide`, `test_form_default_lamination_print_roll` с `# JS, 16.11.2026`.

**Сверка критериев (git, локально):**

| Критерий | Статус |
| --- | --- |
| `js_port_gaps.py calcPrintRoll` | ок: `нет в Python:` пусто |
| Ламинация дефолт А0 | локальный расчёт `cost` 1443, `price` 2335, `time_ready` 16.55 (rel 0.001); эталон Implementer по раннеру принят |
| Эталоны без ламинации 1544 / 14291 | `test_form_default_print_roll` и эталонные тесты в `test_print_roll.py` — в 24 passed |
| `pytest test_print_roll.py` + `test_wp_plugin_forms.py` | 24 passed |
| `LaminationWideCalculator` в `print_roll.py` | вложенный расчёт по размеру изделия и `mode`; `time_ready` ламинации не суммируется; JSON `calc_service/data/` в diff нет |
| `js_port_gaps_allowed.txt` / `MAX_ALLOWED` | строка `calcPrintRoll call calcLaminationWide` снята, `MAX_ALLOWED` 70 |
| Соседи `canvas` / `rollup` / `presswall` | 24 passed |
| Паттерны `print_roll.js` | `syncUrl`, `calcApi('print_roll'`, `showResult`; `is_lamination` при `laminat > 0`; шаг `/ 10`, радио `value 0` — тест `test_print_roll_js_writes_eyelet_step_cm_and_reads_radio_zero` |
| `python scripts/dev.py check` | 624 + 81 passed |
| Копия на проде | вне круга; Site ops 16.11 закрыл люверсы; ламинация на копии — после деплоя API |

**Инварианты:** наценки/цены не в Python; `sameEdges = processNum === 1` без изменений; своих формул `price=` и `querySelector` нет; обязательные поля ответа — по существующим тестам калькулятора.

**Замечания (не блокируют сдачу git):**

1. **желательно:** при `finish-task` в коммит включить `wp-plugin/forms/print_roll.js` (сейчас **untracked**; в `git diff main` не виден).
2. **желательно:** `HEAD` ветки на `0a4aca2`, `main` на `1f10b7c` — перед слиянием подтянуть `main` (site-page-seo / guardrails), иначе откатятся файлы из коммита `1f10b7c`.
3. **желательно:** третья команда раннера ламинации из «Результат» — в `docs/js-runner-cases.md` при слиянии (как в задаче).

**Для человека после слияния и деплоя API:** на копии 99 проверить включение ламинации — цена должна уйти с 1 600 (1544) на округление ~2 335; без деплоя копия по-прежнему на старом API (отчёт Implementer 16.11).

## Найдено вне scope

- Ламинация. На дефолте А0 с `isLamination: 1` раннер даёт price 2335, time_ready 16.55; до правки `POST` с `is_lamination: true` оставался 1544 / 16.52. Пропуск `calcPrintRoll call calcLaminationWide` был в `scripts/js_port_gaps_allowed.txt`. 16.11.2026 человек вернул починку в эту задачу: правка в `print_roll.py`, строка пропуска снята, см. «Результат». `size_mm` по-прежнему вне scope.
- `size_mm`. Боевая форма не вызывает `showMaterials`, таблицы материалов на странице нет. В ответе API на дефолте и эталоне ключа нет (плёнка 1.2 м; на эталоне ещё люверсы 80 шт). В `print_roll.js` размер не подставляется. Для колонки «Размер» на копии нужен `size_mm` в калькуляторе, образец `pennant-materials-size-mm` / `flag-materials-size-mm`.
- «Поля 5 см» и «поля 10 см» (`isField50`, `idField100`) старый `calcPrintRoll` не считает. В API не уходят — так же, как боевой JS.

## Результат

- Ветка, PR или коммит: `task/form-print-roll`, коммита нет.
- Сделано: сверка шагов 0–5б. `wp-plugin/forms/print_roll.js` на id боевой формы 23: `syncUrl`, `calcApi('print_roll')`, `showResult`. `REF_FORM_DEFAULT` в тесте, пометка `# JS, 15.11.2026`.
- Чем проверено:
  - `python scripts/js_port_gaps.py calcPrintRoll` — в блоке `calcPrintRoll` только `call calcLaminationWide`, строка есть в `scripts/js_port_gaps_allowed.txt`.
  - Эталон `REF_PARAMS_2` (5 шт, 1500×1000, резка и люверсы 300): раннер и `POST` оба `price` 14291, `time_ready` 20.43, `cost` 8897, `time_hours` 3.47.
  - Дефолт формы 23 (1 шт, А0 1189×841, ORAJET3640, Technojet160ECO, режим 1): раннер и `POST` тела из `REF_FORM_DEFAULT` оба `price` 1544, `time_ready` 16.52, `cost` 955, `time_hours` 0.26, `weight_kg` 0.22. На боевой странице себестоимость 955, вес 0.22 кг, цена на экране 1 600 ₽ — это `insaincalc.round(1544, 1)`.
  - `python -m pytest calc_service/tests/test_calculators/test_print_roll.py calc_service/tests/test_wp_plugin_forms.py -q` — 22 passed.
  - `Select-String` — `syncUrl(`, `calcApi('print_roll'`, `showResult(` есть.
  - `python scripts/dev.py check` — код 0: calc_service 622 passed, bot_service 81 passed.
- Не сделано и почему: дубль формы, черновик товара и прогон копии — Site ops, шаги 6–16. Боевая форма 23 не переключалась. Строка раннера в `docs/js-runner-cases.md` не вносилась (файл общий): при слиянии добавить две команды ниже. Выкладка плагина не делалась.
- Поля формы, которые пишутся в `syncUrl` и не уходят в `calcApi`: файл `fluAtrwork`; «поля 5 см» / «поля 10 см»; тип ламинации (глянец/мат) — в API только `is_lamination`; `rdoProcessEdge` выбирает набор краёв; `numW`/`numH` в URL в сантиметрах, в API `width`/`height` в миллиметрах.
- Для Site ops, `GET_check`: dropdown с кодом — `index` (`dpdFormat`, `dpdMaterial`, `dpdPrinter`, `dpdRollLaminat`, `dpdProcessEdge` и четыре края). `rdoModeProduction` — `value`. `rdoProcessEdge` — `value`: у опций value 0/1, data-value 1/2; в URL индекс 0 («одинаковая») или 1 («разная»), не 1/2. `ckbJoing` — `index`, выключенный чекбокс из URL убирается.
- Для Reviewer: старый `cjsCalc` передавал материал и принтер без `[0]`; в новом JS берётся `[0]`, код тот же. Id из `get_value_from` совпали с именами элементов, чужих полей нет.
- Требуется решение: нет для git-части на 15.11. Дальше человек не принял копию из-за ламинации: с 16.11 починка в этой задаче, см. блок «Implementer, 16.11.2026 — ламинация». `size_mm` по-прежнему вне scope.
- Строка в «Состав пакета» (в `todo/forms-batch-switch.md` не писать, пока та задача `в работе`): после приёмки копии человеком. Черновик строки, в файл пакета не переносить, пока человек не примет копию:

| Форма | Slug API | Страница | Копия (форма / товар) | Задача |
| --- | --- | --- | --- | --- |
| 23 CalcPrintWide | `print_roll` | `/catalog/shirokoformatnaya-pechat-na-zakaz/` | 99 / 2586893 (draft) | `form-print-roll`, копия считает `print_roll`, ссылка люверсов восстанавливает 12 650; ждёт приёмки человеком |

- Команды раннера при слиянии в `docs/js-runner-cases.md` (`price` на `--data current`, 15.11.2026):

```powershell
node scripts/run_js_calc.mjs calcPrintRoll --data current --args '[5,[1500,1000],"BannerFronlitCoat400","Technojet160ECO",{"isCutting":[1,1,1,1],"isEyelet":[300,300,300,300]},1]'

node scripts/run_js_calc.mjs calcPrintRoll --data current --args '[1,[1189,841],"ORAJET3640","Technojet160ECO",{},1]'
```

Эталон: `price` 14291. Дефолт формы 23: `price` 1544.

### Site ops, 15.11.2026

- Сделано: форма 99 «CalcPrintWide duplicate», товар 2586893 «Широкоформатная печать на заказ (Копировать)», `post_status` draft, `ezfc_form_id` 99. Боевой товар 7801 остался `publish`, форма 23. На копию записан JS с id копии и GET (`scripts/ezfc_copy_apply.php`, `calcApi=1`). Блок цены копии: `sbtPriceTotalDiscount` / `sbtPriceDiscount` скрыты и `calculate_when_hidden=1`, менеджерские поля видимы, `htmCost` со шорткодом `read_maxdiscount`, режим внутри `grpTime`. `sameEdges` не менялся. Боевая форма не переключалась. Плагин и `infra/deploy.sh` не выкатывались. Коммита нет.
- Чем проверено:
  - `wp post get 2586893 --field=post_status` — `draft`. `wp post meta get 2586893 ezfc_form_id` — `99`. Живой 7801 — `publish`, форма `23`.
  - `curl.exe` без cookies `/?post_type=product&p=2586893` — `404`. Живая страница — `200`.
  - Элемент 776 боевой формы — по-прежнему `calcPrintRoll`. Элемент 3735 копии — `calcApi`.
  - Под админом `https://insain.ru/?post_type=product&p=2586893&preview=true`. Дефолт: `POST /api/v1/calc/print_roll` 200, тело `quantity 1, 1189×841, ORAJET3640, Technojet160ECO, mode 1`. На странице 1 600 ₽ и 1 600 ₽/шт, вес 0,22 кг, «со скидкой» 1 242 ₽. Это `round(1544, 1)` и `ceil(955×1,3)`.
  - Люверсы, одинаковая обработка, шаг поля 30 см: POST `is_eyelet [300,300,300,300]`, API `price` 12631, на странице 12 650 ₽ = `round(12631, 5)`. Смена края на «резка в край» даёт POST `is_cutting [1,1,1,1]` и 8 650 ₽.
  - Эталон API 14291 (резка и люверсы вместе) форма одним списком не шлёт: у края одна операция. Так же устроен боевой `calcPrintRoll`. `sameEdges` не трогался.
  - Дефолтная ссылка с GET-именами снова открывает копию: тираж 1, формат 0, материал 0, режим 1, цена 1 600.
  - `wp cache flush` — Success. `wp litespeed-purge all` — `Error: Something went wrong! Got 400`.
- Не сделано и почему: ссылка с люверсами (`numStepEyelets=300`, `rdoProcessEdge=0`, `dpdProcessEdge=5`) заново даёт шаг 50 (max поля, factor 10), радио value 0 не отмечено, цена 7 000, не 12 650. Критерий «ссылка с этими GET» не закрыт. Группы материалов на копии нет: в форме 23 не было `grpMaterial` / `htmMaterial`, новый элемент не добавлялся. Колонка «Размер» по-прежнему упирается в отсутствие `size_mm` (вне scope).
- Как откатить: JS копии — бэкап `/tmp/ezfc-copy-99-20261115-153707.json` на VDS. Товар 2586893 и форму 99 не удалять (не-scope), они и так не на витрине. Боевая форма 23 и товар 7801 не менялись.
- Требуется решение человека (варианты в журнале).

### Implementer, 16.11.2026

- Сделано: в `wp-plugin/forms/print_roll.js` шаг люверсов в `syncUrl` пишется в сантиметрах поля (`step / 10`: factor 10, значение для API остаётся в миллиметрах). Так для `numStepEyelets` и четырёх полей краёв. Радио `rdoProcessEdge=0`: если пункт не отмечен, JS отмечает индекс 0 (`ezfc_element-…-0`, id через `get_element_id_by_name`) и на этом проходе не пишет URL и не шлёт POST; следующий пересчёт читает data-value 1. `sameEdges = processNum === 1` не менялся. Калькулятор, цены, `data/` и прод не трогались.
- Чем проверено: `python -m pytest calc_service/tests/test_wp_plugin_forms.py calc_service/tests/test_calculators/test_print_roll.py -q` — 23 passed. `python scripts/dev.py check` — код 0: calc_service 623 passed, bot_service 81 passed.
- Не сделано и почему: копия 99 на проде всё ещё со старым JS. Плагин не выкладывался. Боевая форма 23 и товар 2586893 не менялись. Критерий ссылки с люверсами закроет Site ops. Старая ссылка с `numStepEyelets=300` по-прежнему зажмёт поле до 50: после правки в URL должно быть `30`.
- Для Site ops: заново записать JS копии из git (id копии, `read_file` не включать). GET не менять. Проверка под админом: люверсы, одинаковая обработка, шаг 30 см → URL `numStepEyelets=30` и `rdoProcessEdge=0`; открыть эту ссылку заново → радио «одинаковая» отмечено, шаг 30, POST `is_eyelet [300,300,300,300]`, на странице 12 650. Эталон 14291 одним списком не чинить.

### Site ops, 16.11.2026

- Сделано: на копию 99 заново записан JS из `wp-plugin/forms/print_roll.js` (`scripts/ezfc_copy.py` + `ezfc_copy_apply.php apply`). Id — элементы копии, `custom_calculation_function_read_file=0`. GET-имена и `GET_check` не менялись (в показе все `=`). `sameEdges` не менялся. Боевая форма 23 и товар 2586893 не менялись. Плагин не выкладывался. Коммита нет. Эталон 14291 одним списком не чинился.
- Чем проверено:
  - `wp post get 2586893 --field=post_status` — `draft`. `ezfc_form_id` — `99`. Товар 7801 — `publish`, форма `23`. Элемент 776: в data есть `calcPrintRoll`, нет `insaincalc.calcApi`. Элемент 3735: есть `insaincalc.calcApi`.
  - `curl.exe` без cookies `/?post_type=product&p=2586893` — `404`.
  - Под админом превью черновика. Люверсы, одинаковая обработка, шаг 30 см, тираж 5, свой размер 150×100 см, баннер Fronlit 400: URL `numStepEyelets=30` и `rdoProcessEdge=0` (не 300). POST `{"quantity":5,"width":1500,"height":1000,"material_id":"BannerFronlitCoat400","printer_code":"Technojet160ECO","mode":1,"is_eyelet":[300,300,300,300]}` — 200, API `price` 12631. На странице 12 650 руб. и 2 530 руб./шт.
  - Та же ссылка заново: радио «Одинаковая по всем краям» отмечено, шаг 30, край «люверсовка», тот же POST `is_eyelet [300,300,300,300]`, на странице снова 12 650.
  - Дефолтная ссылка заново: тираж 1, А0, край «поля 5 см», POST без `is_eyelet` (`quantity 1, 1189×841, ORAJET3640, Technojet160ECO, mode 1`), на странице 1 600 руб. и 1 600 руб./шт.
  - `POST https://insain.ru/api/v1/calc/print_roll` тем же телом люверсов — `price` 12631. Консоль: ошибок `insaincalc` и `ezfc` нет.
  - `wp cache flush` — Success. `wp litespeed-purge all` — `Error: Something went wrong! Got 400`.
- Не сделано и почему: боевая форма 23 не переключалась, плагин не выкладывался, коммита нет — так и задано. Группы материалов и колонка «Размер» (`size_mm`) по-прежнему вне scope. В карте id копии нет `sbtCost`, `sbtCostTotal`, `grpPriceCustomer` (блок цены копии уже другой); в JS их нет, в пакет не входили. Старую ссылку с `numStepEyelets=300` эталоном не использовал.
- Как откатить: JS копии — бэкап `/tmp/ezfc-copy-99-20261115-164235.json` на VDS (снимок до этой записи). Форму 99 и товар 2586893 не удалять. Боевая форма 23 и товар 7801 не менялись.
- Требуется решение: приёмка копии человеком. Строка пакета выше — в `todo/forms-batch-switch.md` не переносить, пока человек не примет копию и та задача не свободна.

### Implementer, 16.11.2026 — ламинация

- Ветка, PR или коммит: `task/form-print-roll`, коммита нет (коммит при закрытии, как решил человек 15.11).
- Сделано: в `calc_service/calculators/print_roll.py` при `is_lamination` вызывается `LaminationWideCalculator` на размере изделия и режиме, как `calcLaminationWide(n, size, mode)` в JS. В себестоимость, цену, время и вес входят `cost`, `price`, `time_hours` и `weight_kg` вложенного расчёта. `time_ready` ламинации не прибавляется: в JS у `calcLaminationWide` он остаётся 0, срок печати — `time + max(timeReady опций, timeReady печати)`. Плёнка и цены берутся из уже сверенного `lamination_wide`, JSON не менялся. `sameEdges` в `wp-plugin/forms/print_roll.js` не менялся. Формы 23 и 99, товар 2586893, плагин и `infra/deploy.sh` не трогались.
- Числа. Раннер, дефолт А0, `isLamination: 1`: `cost` 1443, `price` 2335, `time_hours` 0.29, `time_ready` 16.55, `weight_kg` 0.32. До правки локальный расчёт с `is_lamination: true` (и боевой разрыв): `cost` 955, `price` 1544, `time_hours` 0.26, `time_ready` 16.52, `weight_kg` 0.22. После правки локальный расчёт совпал с раннером: `cost` 1443, `price` 2335, `unit_price` 2335, `time_hours` 0.29, `time_ready` 16.55, `weight_kg` 0.32. Боевой API не перепроверялся: деплой в эту сдачу не входит.
- Чем проверено падение теста без правки: `git stash push -- calc_service/calculators/print_roll.py`, затем `python -m pytest calc_service/tests/test_calculators/test_print_roll.py -q --tb=line` — 1 failed, 17 passed. Упал только `test_form_default_lamination_print_roll`: `assert 955.0 == 1443 ± 1.443`. Старый расчёт на этом входе: cost 955, price 1544, time_ready 16.52. `git stash pop`, тот же pytest — 18 passed. Эталоны без ламинации (дефолт 1544, эталон 14291) в этих 17/18 passed.
- Соседи: `python -m pytest calc_service/tests/test_calculators/test_canvas.py calc_service/tests/test_calculators/test_rollup.py calc_service/tests/test_calculators/test_presswall.py -q` — 24 passed. Они не передают `is_lamination`.
- `python scripts/dev.py check` — код 0: calc_service 624 passed, bot_service 81 passed.
- Пропуск порта: строка `calcPrintRoll call calcLaminationWide` удалена из `scripts/js_port_gaps_allowed.txt`. `MAX_ALLOWED` в `calc_service/tests/test_js_port_gaps.py` уменьшен с 71 до 70: проверка репозитория не принимает закрытый пропуск в списке.
- Не сделано и почему: коммит не делался. Строка раннера ламинации в `docs/js-runner-cases.md` не вносилась (файл общий) — команда ниже, в файл при слиянии. Копия 99 по-прежнему на старом API без этой правки: плагин и `infra/deploy.sh` не запускались. `size_mm` не добавлялся.
- Требуется решение: нет для git-части. Дальше Reviewer. Повторный прогон копии — после ревью, слияния и деплоя API, не в этой сдаче.
- Команда раннера ламинации (в `docs/js-runner-cases.md` при слиянии, `price` 2335 на `--data current`, 16.11.2026):

```powershell
node scripts/run_js_calc.mjs calcPrintRoll --data current --args '[1,[1189,841],"ORAJET3640","Technojet160ECO",{"isLamination":1},1]'
```
