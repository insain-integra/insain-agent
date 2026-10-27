# calc-reconcile-plaque

Статус: черновик
Сложность: высокая
Implementer: Opus 5.5
Reviewer: Grok 4.7
Почему: наценки `js_legacy` и текущего прайса уже расходятся; эталон нельзя списать на устаревшую цену.

## Цель

Есть скрипт на Node, который считает старым JS из `js_legacy/`. Для `calcPlaque` в `test_plaque.py` лежат 5–10 эталонов, совпавших с API на актуальных ценах, с пометкой `JS, ДД.ММ.ГГГГ`. `make check` зелёный. Файлы цен не изменены.

## Контекст и ссылки

- `docs/refactoring-plan.md` — только раздел «Протокол выполнения» и пункт 5.6. План целиком не читать.
- `js_legacy/calc/calcTablets.js` — `calcPlaque` (с объявления функции). Вход: `n`, `plaqueID`, `materialID`, `applicationID`, `options`, `modeProduction`. Выход JS: `cost`, `price`, `time`, `timeReady`, `weight`, `material`. Поля `unit_price` в JS нет.
- В вызове `calcTablets` пятый аргумент — присваивание `modeProduction = 1`. Старый JS считает пластину в режиме 1 при любом `mode`. Ветку `default` у `applicationID` тоже вызывает `calcTablets`. Это не чинить.
- `js_legacy/calc/icdc_ls.js` — `StructDat` и снятие комментариев. `loadData` ходит через `XMLHttpRequest` по пути `icalc/...`; в Node так не грузить.
- `js_legacy/calc/common.js` — `findMaterial`, `mergeMaps`. Плакетка ищется как `findMaterial("misc", plaqueID)`.
- `calc_service/calculators/plaque.py` — те же параметры, что у API (`quantity`, `plaque_id`, `material_id`, `application`, `mode`). `unit_price` = `round(price / max(1, n), 2)`.
- `calc_service/tests/test_calculators/test_plaque.py` — допуск `_cmp` / `rel = 0.03` и эталон `REF_PARAMS` (quantity 2, Plaque2330, PVC3, isUVPrint, mode 1) без пометки источника.
- `docs/site/forms.md` — строка формы 69, страница калькулятора плакеток. Форму не открывать и не менять.
- Наценки уже разные, доску не править. `js_legacy/calc/common.json`: `marginMaterial` 0.6, `marginOperation` 0.55, `marginMin` 0.25, `marginPlaque` 0.5. `calc_service/data/common.json`: 0.66, 0.6, 0.3, 0.45. `Plaque2330.cost` = 315 и там, и в `calc_service/data/materials/plaque.json`.
- Остальное не открывать: весь `js_legacy/`, `docs/archive/`, `CLAUDE.md`, `bot_service/agent.py`.

## Scope

Один новый файл `scripts/run_js_calc.mjs`. Зависимостей npm и `package.json` нет, только встроенный Node. Код `js_legacy/` не править: скрипт читает его с диска.

Интерфейс:

- `node scripts/run_js_calc.mjs <имя> --params '<json>' [--data legacy|current]`
- Имя, которое скрипт считает в этой задаче: `calcPlaque`. Любое другое имя — ненулевой код и текст, что калькулятор не подключён. Чисел расчёта в stdout нет.
- JSON параметров `calcPlaque`: `quantity`, `plaque_id`, `material_id`, `application`, `mode`. В `options` ничего не класть: аргумент в `calcPlaque` не используется.
- `--data` по умолчанию `legacy`: прайс `js_legacy/material`, `js_legacy/equipment`, `js_legacy/calc/common.json`.
- `--data current`: тот же JS, но в памяти подменить числа прайса значениями из `calc_service/data` по тем же кодам (наценки `common` с теми же именами ключей, `cost` и ставки материалов и оборудования, которые читает этот прогон). Файлы не записывать. Кода нет в текущем прайсе — не выдумывать цену и не брать этот кейс в режиме `current`.
- Общего синхронизатора каталогов не писать. Поднимать только те `calc/*.js` и JSON, без которых выбранные кейсы `calcPlaque` не считаются. Список файлов — комментарий в шапке скрипта.
- stdout — один JSON и ничего больше. Ровно поля `cost`, `price`, `unit_price`, `time_hours`, `time_ready`, `weight_kg`. Соответствие: `time_hours` ← `time`, `time_ready` ← `timeReady`, `weight_kg` ← `weight`, `unit_price` как в `plaque.py`. Ошибки — в stderr.

Эталоны в `calc_service/tests/test_calculators/test_plaque.py`:

- Считать совпадением все шесть полей в допуске 0.03 на прогоне `--data current` против `PlaqueCalculator.execute` с теми же параметрами.
- В тест писать числа этого прогона. Пометка на каждом кейсе ровно один раз, буквально `JS, ДД.ММ.ГГГГ` (дата прогона).
- Прогон `--data legacy` в ожидаемые числа не писать.
- Кейсов 5–10. Среди них: два разных `quantity` (один ≥ 2), два `plaque_id`, два `material_id`, два `application` из `isUVPrint`, `isGrave`, `isSublimation`.
- Отдельно прогнать `noApplication`, `mode` 0 и `mode` 2. Совпало — можно включить в 5–10. Не совпало — в «Результат» как расхождение логики, в тест не добавлять и код не менять.
- Существующий `REF_PARAMS`: прогнать `--data current`. Попал в допуск — дописать пометку, числа не переписывать. Не попал — числа не подгонять, кейс в отчёт.
- Меньше пяти совпадений — допуск не ослаблять, калькулятор и JSON не трогать, пункт 5.6 в плане не отмечать, в «Требуется решение» таблица: кейс, поле, legacy, current, API, причина `цена` или `логика`.

Причина `цена`: расходятся именно те ставки и наценки, которые кейс читает (`js_legacy/material`, `js_legacy/equipment`, наценки `common`). Причина `логика`: ставки те же, а поле нет, либо это `mode` ≠ 1 или `noApplication`. Сверка по кодам кейса, не диффом всего каталога в коммит.

После зелёных критериев отметить в `docs/refactoring-plan.md` чекбокс 5.6 и строку «сделано ДД.ММ.ГГГГ, проверено: \<команда\>» по протоколу.

## Не-scope

- Любой калькулятор кроме `calcPlaque` (имя в скрипте есть, расчёта нет).
- Правки `plaque.py`, `calcTablets.js`, прочих `js_legacy/**`, JSON цен и наценок.
- Починка найденного расхождения логики, в том числе принудительного `modeProduction = 1`.
- Форма ezFC 69, WordPress, VDS, деплой.
- Отдельный файл кейсов вне `test_plaque.py`.

## Критерии приёмки

Каждый пункт — команда и ожидаемый результат. Параметры эталона ниже: `{"quantity":2,"plaque_id":"Plaque2330","material_id":"PVC3","application":"isUVPrint","mode":1}`.

- [ ] `node scripts/run_js_calc.mjs calcPlaque --params '{"quantity":2,"plaque_id":"Plaque2330","material_id":"PVC3","application":"isUVPrint","mode":1}'` — код 0; stdout парсится как JSON с полями `cost`, `price`, `unit_price`, `time_hours`, `time_ready`, `weight_kg`, других полей нет
- [ ] `node scripts/run_js_calc.mjs calcPlaque --data current --params '{"quantity":2,"plaque_id":"Plaque2330","material_id":"PVC3","application":"isUVPrint","mode":1}'` — тот же вид JSON; `price` отличается от прогона без `--data current`; файлы в `js_legacy/` и `calc_service/data/` не изменились
- [ ] `node scripts/run_js_calc.mjs notACalc --params "{}"` — код не 0; в stdout нет `cost` и `price`
- [ ] `python -m pytest calc_service/tests/test_calculators/test_plaque.py -q` — код 0, `skipped` нет
- [ ] `python -c "import pathlib,re; t=pathlib.Path(r'calc_service/tests/test_calculators/test_plaque.py').read_text(encoding='utf-8'); m=re.findall(r'JS, \d{2}\.\d{2}\.\d{4}', t); print(len(m)); assert 5<=len(m)<=10"` — печатает число от 5 до 10, код 0
- [ ] `python scripts/dev.py check` — код 0 (`make` в PATH может не быть)
- [ ] `git diff main --name-only` — только `scripts/run_js_calc.mjs`, `calc_service/tests/test_calculators/test_plaque.py`, `todo/calc-reconcile-plaque.md`, `docs/refactoring-plan.md`
- [ ] `git diff main -- calc_service/data js_legacy` — пусто

## Проверки

- [ ] `make check` (или `python scripts/dev.py check`) — зелёный вывод
- [ ] Self-review — чеклист «Перед сдачей» в [AGENTS.md](../AGENTS.md)

## Риски

- Прод: нет. Страница формы 69 не открывается и не меняется.
- Цены: файлы не править. Деньги с `--data legacy` не эталон API. Расхождение ставки и расхождение формулы пишутся в отчёт раздельно.
- Формы: нет

## Режим

обычный

## Результат

Заполняет Implementer при сдаче.

- Ветка, PR или коммит: `task/calc-reconcile-plaque` от `main`
- Сделано:
- Чем проверено:
- Не сделано и почему:
- Требуется решение:
