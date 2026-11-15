# print-offset-promo

Статус: выкатка
Сложность: средняя
Implementer: Opus 5.5
Reviewer: Grok 4.7
Site ops: Grok 4.7
Почему: порт ветки promo в существующий `print_offset` меняет ответ API и правит раннер; на бой — только skill `deploy-api` и smoke.
Чат: новый чат Orchestrator. Implementer — модель из поля Implementer.

## Цель

`POST /api/v1/calc/print_offset` с кодом из каталога `offset_promo` считает как `calcPrintOffsetPromo`. Дефолт формы 82: тираж 1000, `OffsetPromoА51000` (кириллическая А), mode 0 — cost 2250, price 4244.4, time_hours 0, time_ready 56, weight_kg 3.5742. Обычный офсет `PaperCoated115M` остаётся на текущем эталоне. Форма 82 на этот порт не переключается.

## Контекст и ссылки

- `.cursor/skills/port-fix-prerequisite/SKILL.md` — шаги 8–13. Держит `todo/form-print-offset.md`: человек выбрал вариант 1 (эталон mode 0, как value радио «стандарт» на форме 82).
- JS `js_legacy/calc/calcPrintOffset.js`, строки 89–106: `findMaterial('sheet', offsetpromoID)`, набор `ceil(numSheet / numSheet)`, вес, доставка `calcShipment(..., 'Luch')`, наценка `marginOffsetPromo`, срок `baseTimeReadyPrintOffsetPromo[ceil(mode)]`, `time = 0`.
- Python `calc_service/calculators/print_offset.py`, строки 100–104: код ищется только в каталоге sheet, неизвестный код уходит в `_empty`. Боевой POST с `OffsetPromoА51000` сейчас: price 0, time_ready 8 (срок из `baseTimeReady` принтера, не из промо).
- Каталог уже загружается: `calc_service/materials/__init__.py` (`offset_promo`). В `calc_service/data/materials/offset_promo.json` у `OffsetPromoА51000` поле `size` `[148, 210]`; цветность `4+4` и плотность 115 приходят из `Default`. В JSON нет поля `sizeSheet` — это имя в старом JS.
- Срок и наценка уже в `calc_service/common/markups.py`: `BASE_TIME_READY_PRINT_OFFSET_PROMO` / `get_time_ready("baseTimeReadyPrintOffsetPromo")` = `[56, 48, 40]`, `get_margin("marginOffsetPromo")`. В Python эти числа не хардкодить.
- Цена от режима не зависит. `time_ready` при тираже 1000: mode 0 → 56, mode 1 → 48, mode 2 → 40. `cost` 2250, `price` 4244.4, `time_hours` 0, `weight_kg` 3.5742 на всех трёх режимах.
- Тираж 2000, mode 1, тот же код: cost 4050, price 7592.4, time_ready 48, weight_kg 7.1484. Тираж 2000, mode 0 раннером ещё не снимали.
- `calc_service/calculators/notebook.py` вызывает `PrintOffsetCalculator.calculate` для обычной бумаги. Его эталоны не переснимать.
- В `PORTS` (`scripts/js_port_gaps.py`) есть `calcPrintOffset`, `calcWeight`, `calcShipment`. Записи `calcPrintOffsetPromo` нет. Строка `calcPrintOffsetPromo module` уже лежит в `scripts/js_port_gaps_allowed.txt`.
- Штатный раннер не грузит `js_legacy/calc/calcPrintOffset.js`. Числа выше сняты `--data current` с временной подгрузкой этого файла. `offset_promo.json` в `CURRENT_FILES` не входит; legacy `sheet.json` для этого кода имеет тот же `cost` 1800.
- Остальное не открывать.

## Scope

- В git (Implementer): в `PrintOffsetCalculator.calculate` отдельная ветка для кода из `offset_promo`. Такой код не попадает в `_empty` и не идёт в раскладку SRA2 обычного офсета. Размер и цветность берутся из каталога. Запрос только с `num_sheet`, `material_id` и `mode` для промо-кода считается. Для кода из sheet `width`, `height` и `color` остаются обязательными.
- Зарегистрировать `calcPrintOffsetPromo` в `PORTS`. `calcWeight` и `calcShipment` подключить импортом их портов. Новую строку в `scripts/js_port_gaps_allowed.txt` — только если проверка ругается на вызов, которого в Python нет под другим именем (`findMaterial`: поиск по каталогу). Строкой allowed не закрывать саму цену и срок.
- В `scripts/run_js_calc.mjs` добавить `js_legacy/calc/calcPrintOffset.js` в `JS_FILES` и в список файлов в шапке. `CURRENT_FILES` не расширять.
- Эталоны — только с раннера, пометка `# JS, 16.11.2026`, `rel=0.001` на `cost`, `price`, `time_ready`. Рядом в тесте — команда раннера.
- `docs/js-runner-cases.md` в ветке не править (общий файл). Строка для слияния — в «Результат» с первого коммита кода.
- На проде (Site ops): после ревью, слияния в `main` и зелёного CI — skill `deploy-api`, затем smoke боевого API на дефолте ниже. Форму 82 не трогать.

## Файлы

- `calc_service/calculators/print_offset.py`
- `calc_service/tests/test_calculators/test_print_offset.py`
- `scripts/run_js_calc.mjs`
- `scripts/js_port_gaps.py`

## Не-scope

- `wp-plugin/`, копия и боевая форма 82, `docs/site/forms.md`, `todo/form-print-offset.md` (статус формы уже в её worktree).
- Правка `calc_service/data/`, цен, наценок, курсов, сроков. Ветка обычного офсета, включая `max(1, mode.value)` на строке расчёта времени обычного тиража. Эталон `PaperCoated115M` не сдвигать.
- `calc_service/calculators/notebook.py` и пересъём его эталонов. Упал эталон блокнота — стоп, `заблокировано: аналитик`.
- `docs/js-runner-cases.md` в ветке. Форма 83 CalcCardPromo. Slug `print_wide`.
- Добавление `offset_promo.json` в `CURRENT_FILES`.

## Критерии приёмки

Команды из корня репозитория. В `--args` кириллическая А. PowerShell 5.1: кавычки JSON внутри `--args` экранируются `\"`.

- [x] `node scripts/run_js_calc.mjs calcPrintOffsetPromo --data current --args '[1000,"OffsetPromoА51000",0]'` — завершается без «Калькулятор не подключён»; cost 2250, price 4244.4, time_hours 0, time_ready 56, weight_kg 3.5742.
- [x] Та же команда с mode `1` и mode `2`: price 4244.4, time_ready 48 и 40. С `--args '[2000,"OffsetPromoА51000",1]'`: cost 4050, price 7592.4, time_ready 48, weight_kg 7.1484.
- [x] `node scripts/run_js_calc.mjs calcPrintOffsetPromo --data current --args '[2000,"OffsetPromoА51000",0]'` — снять cost, price, time_hours, time_ready, weight_kg и этими числами закрыть второй кейс в тесте.
- [x] `python -m pytest calc_service/tests/test_calculators/test_print_offset.py -q` — `passed`, `failed` нет. В тесте есть кейсы mode 0/1/2 на тираже 1000 и оба кейса тиража 2000, пометка `# JS, 16.11.2026`, assert `cost`, `price`, `time_ready` с `rel=0.001`. Вызов промо без `width`, `height`, `color` даёт тот же price и time_ready, что вызов с `width` 148, `height` 210, `color` `4+4`.
- [x] Эталон обычного офсета в том же файле не сдвинут: `PaperCoated115M`, 1000 шт, 210×297, `4+0`, mode 1 — cost 6848.6, price 14108.116, time_hours 0, time_ready 56, weight_kg 7.173.
- [x] Откат только калькулятора роняет новые кейсы и оставляет старый эталон зелёным. После возврата файла снова всё зелёное. Числа — в «Результат».

```powershell
git stash push -- calc_service/calculators/print_offset.py
python -m pytest calc_service/tests/test_calculators/test_print_offset.py -q
git stash pop
```

- [x] `python -m pytest calc_service/tests/test_calculators/test_notebook.py -q` — `passed`. Упал эталон блокнота — стоп, эталон в этой задаче не менять.
- [x] `python scripts/js_port_gaps.py calcPrintOffsetPromo` — в блоке нет `нет порта`. Строка `нет в Python:` пустая или каждый пропуск уже есть в `scripts/js_port_gaps_allowed.txt`. `python scripts/js_port_gaps.py` — код выхода 0.
- [x] В «Результат» лежит строка для слияния в `docs/js-runner-cases.md`: `node scripts/run_js_calc.mjs calcPrintOffsetPromo --data current --args '[1000,"OffsetPromoА51000",0]'` → price 4244.4, time_ready 56.
- [ ] После `deploy-api`: `POST https://insain.ru/api/v1/calc/print_offset` с телом `{"num_sheet":1000,"material_id":"OffsetPromoА51000","mode":0}` → 200, price 4244.4 (abs ≤ 0.02 и rel ≤ 0.001), time_ready 56.

## Проверки

- [x] `python scripts/dev.py check` — код выхода 0
- [x] Self-review — чеклист «Перед сдачей» в [AGENTS.md](../AGENTS.md)

## Риски

- Прод: slug `print_offset` ни на одной боевой форме API не стоит (`docs/site/forms.md`). После выкатки промо-код перестаёт отдавать price 0 и time_ready 8. Обычный код бумаги цену на бою менять не должен. Форму 82 не переключать.
- Цены: JSON не менять. Расхождение с раннером больше rel 0.001 — стоп, эталон под ответ API не подгонять.
- Формы: нет правок ezFC. После `close` этой задачи worktree `form-print-offset` делает `git rebase main`, ставит `черновик` и возвращает тест в свои «Файлы» ради `REF_FORM_DEFAULT`.

## Режим

прод

## Журнал передач

16.11.2026 — Analyst, Grok 4.7 — задача заведена по варианту 1 из `form-print-offset`: порт promo в `print_offset`, эталон mode 0 — дальше Implementer, Opus 5.5
16.11.2026 — Implementer, Opus 5.5 — ветка promo в `print_offset`, раннер грузит `calcPrintOffset.js`, `calcPrintOffsetPromo` в `PORTS`, 5 эталонов с раннера; `make check` зелёный. Строка `calcPrintOffsetPromo module` удалена из `scripts/js_port_gaps_allowed.txt` (иначе `--check` падает «пропуск устранён») — дальше Reviewer, Grok 4.7
16.11.2026 — Reviewer, Grok 4.7 — принято по diff, блокеров нет. Статус остаётся `ревью`. Дальше человек: слияние и выкатка; затем Site ops, Grok 4.7
16.11.2026 — человек — принято — выкатка

## Найдено вне scope

- Радио «стандарт» на форме 82: value 0 и data-value 1. Боевой JS читает value. В калькулятор и в форму не переносить.
- Штатный раннер до этой задачи не загружает `calcPrintOffset.js`.
- Живой price обычного офсета `PaperCoated115M`, 1000 шт, 210×297, `4+0`, mode 1 — 14450.546 и до этой правки, и после. Константа теста 14108.116 не менялась; тест держится на `rel=0.03`. В этой задаче не чинить.

## Результат

- Ветка, PR или коммит: `task/print-offset-promo`, правки не закоммичены (коммит — по решению человека/Orchestrator).
- Период: 16.11.2026
- Часы человека: оценка 1 ч — постановка
- Работа агентов: Analyst Grok 4.7 — постановка; Implementer Opus 5.5 — код и тесты.
- Было / стало: боевой `print_offset` на `OffsetPromoА51000` отдаёт price 0 и time_ready 8. Должно стать price 4244.4 и time_ready 56 при mode 0. Локально (TestClient, `POST /api/v1/calc/print_offset` с `{"num_sheet":1000,"material_id":"OffsetPromoА51000","mode":0}`): 200, cost 2250.0, price 4244.4, time_hours 0.0, time_ready 56.0, weight_kg 3.5742.
- Сделано:
  - `calc_service/calculators/print_offset.py`: код из каталога `offset_promo` уходит в `_calculate_promo` до раскладки SRA2 и `_empty`. Размер (`size`), плотность и тираж набора (`numSheet` через `_get_raw_material("offset_promo", …)`) — из JSON; `width`/`height`/`color` для промо не читаются. Доставка `calc_shipment(1, …, "Luch")`, наценка `get_margin("marginOffsetPromo")`, срок `get_time_ready("baseTimeReadyPrintOffsetPromo")[mode]`, `time_hours` 0. В `materials` — код набора, name/title из каталога, `quantity` = листов в наборах, `unit` «шт», `size_mm`. Ветка обычного офсета не тронута (переставлено только чтение `material_id`/`mode` выше).
  - `calc_service/tests/test_calculators/test_print_offset.py`: 5 кейсов с раннера (`# JS, 16.11.2026`, команда раннера рядом, `rel=0.001` на cost/price/time_ready, плюс weight_kg и time_hours) и тест «без width/height/color = с 148×210, 4+4».
  - `scripts/run_js_calc.mjs`: `js_legacy/calc/calcPrintOffset.js` в `JS_FILES` и в шапке. `CURRENT_FILES` не менялся.
  - `scripts/js_port_gaps.py`: `calcPrintOffsetPromo` → `calculators.print_offset`.
  - `scripts/js_port_gaps_allowed.txt` (вне «Файлов»): удалена строка `calcPrintOffsetPromo module` — без этого `js_port_gaps.py --check` падает «пропуск устранён, удалите строку». Новых строк allowed нет.
- Чем проверено:
  - Раннер `--data current`: `[1000,…,0]` → cost 2250, price 4244.4, time_hours 0, time_ready 56, weight_kg 3.5742; mode 1 → time_ready 48, mode 2 → 40 (price 4244.4); `[2000,…,1]` → cost 4050, price 7592.4, time_ready 48, weight_kg 7.1484; `[2000,…,0]` (снят впервые) → cost 4050, price 7592.4, time_hours 0, time_ready 56, weight_kg 7.1484.
  - `pytest test_print_offset.py -q` → 13 passed. Эталон `PaperCoated115M` в тесте не менялся и зелёный.
  - Откат только калькулятора (`git stash push -- calc_service/calculators/print_offset.py`): 5 failed (все `test_promo_matches_js`), 8 passed (старый эталон зелёный; тест равенства «без размеров = с размерами» на старом коде проходит тривиально — оба 0). После `git stash pop` — 13 passed.
  - `pytest test_notebook.py -q` → 6 passed.
  - `python scripts/js_port_gaps.py calcPrintOffsetPromo` → `нет в Python:` пусто у `calcPrintOffsetPromo`, `calcWeight`, `calcShipment`; `python scripts/js_port_gaps.py` → exit 0; `--check` → ok, exit 0.
  - `python scripts/dev.py check` → exit 0 (calc_service 630 passed, bot_service 81 passed).
- Не сделано и почему: деплой API и smoke боевого `print_offset` — шаг Site ops после ревью, слияния в `main` и зелёного CI. Коммит — не просили.
- Требуется решение: нет.
- Строка в `docs/js-runner-cases.md` (в ветке файл не править, внести при слиянии): `node scripts/run_js_calc.mjs calcPrintOffsetPromo --data current --args '[1000,"OffsetPromoА51000",0]'` → price 4244.4, time_ready 56.

## Ревью 1

Принято по diff. Статус остаётся `ревью`. Блокеров нет. Деплой и smoke боевого API в этот круг не входят.

Дальше человек: слияние смешанной цепочки (`finish-task`, «Принято, слить и выкатить») — коммит в `task/print-offset-promo`, fast-forward в `main`, строка раннера из «Результат» в `docs/js-runner-cases.md`, статус `выкатка`, push и зелёный CI. После этого — промпт Site ops ниже.

Сверено с diff и командами в worktree `D:\Projects\insain-agent-print-offset-promo`:

- Раннер `node scripts/run_js_calc.mjs calcPrintOffsetPromo --data current --args` (JSON-массив в argv: PowerShell 5.1 снимает кавычки внутри `--args`). Калькулятор подключён. `[1000, OffsetPromoА51000, 0]` → cost 2250, price 4244.4, time_hours 0, time_ready 56, weight_kg 3.5742. Mode 1 → time_ready 48, mode 2 → 40, price 4244.4. `[2000, …, 1]` и `[2000, …, 0]` → cost 4050, price 7592.4, time_hours 0, weight_kg 7.1484, time_ready 48 и 56. Числа совпали с пятью эталонами теста.
- `python -m pytest calc_service/tests/test_calculators/test_print_offset.py -q` → 13 passed. В тесте кейсы mode 0/1/2 на тираже 1000 и оба кейса тиража 2000, пометка `# JS, 16.11.2026`, команда раннера рядом, `rel=0.001` на cost, price, time_ready. Вызов без width/height/color даёт тот же price и time_ready, что 148×210, `4+4`.
- Константы эталона `PaperCoated115M` в файле теста не менялись: cost 6848.6, price 14108.116, time_hours 0, time_ready 56, weight_kg 7.173. Живой расчёт обычной ветки до stash и после одинаковый: cost 6848.6, price 14450.546, time_hours 0, time_ready 56, weight_kg 7.173. В diff обычной ветки только перенос чтения `material_id` и `mode`; `max(1, mode.value)` на месте.
- Откат только калькулятора: `git stash push` → 5 failed (`test_promo_matches_js`), 8 passed; `git stash pop` → 13 passed. Stash снят.
- `python -m pytest calc_service/tests/test_calculators/test_notebook.py -q` → 6 passed.
- `python scripts/js_port_gaps.py calcPrintOffsetPromo`: `нет порта` нет, `нет в Python:` пусто у `calcPrintOffsetPromo`, `calcWeight`, `calcShipment`. `python scripts/js_port_gaps.py` → exit 0. `--check` → ok, exit 0. Удаление `calcPrintOffsetPromo module` из `scripts/js_port_gaps_allowed.txt` (вне «Файлов») оставляет проверку зелёной; новой строки allowed нет, цена и срок ею не закрыты.
- Строка для `docs/js-runner-cases.md` лежит в «Результат». В ветке файл не менялся. `docs/dashboard.md` — пересборка статуса `ревью`, не замечание.
- `python scripts/dev.py check` → exit 0 (calc_service 630 passed, bot_service 81 passed).
- В `_calculate_promo` нет числовых цен, наценок и сроков: наценка `get_margin("marginOffsetPromo")` (в `common.json` 0.20), срок `get_time_ready("baseTimeReadyPrintOffsetPromo")` (`[56, 48, 40]`), `MARGIN_MATERIAL` из `common/markups.py`. Ноль в `time_hours` и thickness, `"Luch"`, `"гм2"` и `/80/10` — формула JS. `POST /api/v1/calc/{slug}` схему `required` не проверяет и считает тело только с `num_sheet`, `material_id`, `mode`.
- `materials[0]`: code `OffsetPromoА51000`, name и title «Листовки А5, 4+4, сборный тираж на офсет, 1000шт». Code в name и title нет. `execute` добавляет `share_url`.

```text
Site ops. todo/print-offset-promo.md, модель Grok 4.7.
Рабочая папка: D:\Projects\insain-agent на main. Worktree D:\Projects\insain-agent-print-offset-promo не трогать.
Старт только после слияния task/print-offset-promo в main, статуса «выкатка» и зелёного CI на этом коммите.
Прочитай docs/agents/roles/site-ops.md и .cursor/skills/deploy-api/SKILL.md и иди по skill. Форму 82 не трогать. Общие файлы (docs/site/forms.md, todo/EPIC-*.md, todo/forms-batch-switch.md, docs/js-runner-cases.md, STATUS.md, BACKLOG.md) не править.
Сделай skill deploy-api, затем smoke: POST https://insain.ru/api/v1/calc/print_offset с телом {"num_sheet":1000,"material_id":"OffsetPromoА51000","mode":0} → 200, price 4244.4 (abs ≤ 0.02 и rel ≤ 0.001), time_ready 56.
Отчёт в «Результат», строка в «Журнал передач». Подтверждений у человека не спрашивай; шаг с подтверждением или развилкой — блокер «заблокировано: человек» с 2–4 готовыми вариантами. Без git commit и git push, кроме шагов самого skill deploy-api.
```
