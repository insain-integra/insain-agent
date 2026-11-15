# print-offset-promo

Статус: черновик
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

- [ ] `node scripts/run_js_calc.mjs calcPrintOffsetPromo --data current --args '[1000,"OffsetPromoА51000",0]'` — завершается без «Калькулятор не подключён»; cost 2250, price 4244.4, time_hours 0, time_ready 56, weight_kg 3.5742.
- [ ] Та же команда с mode `1` и mode `2`: price 4244.4, time_ready 48 и 40. С `--args '[2000,"OffsetPromoА51000",1]'`: cost 4050, price 7592.4, time_ready 48, weight_kg 7.1484.
- [ ] `node scripts/run_js_calc.mjs calcPrintOffsetPromo --data current --args '[2000,"OffsetPromoА51000",0]'` — снять cost, price, time_hours, time_ready, weight_kg и этими числами закрыть второй кейс в тесте.
- [ ] `python -m pytest calc_service/tests/test_calculators/test_print_offset.py -q` — `passed`, `failed` нет. В тесте есть кейсы mode 0/1/2 на тираже 1000 и оба кейса тиража 2000, пометка `# JS, 16.11.2026`, assert `cost`, `price`, `time_ready` с `rel=0.001`. Вызов промо без `width`, `height`, `color` даёт тот же price и time_ready, что вызов с `width` 148, `height` 210, `color` `4+4`.
- [ ] Эталон обычного офсета в том же файле не сдвинут: `PaperCoated115M`, 1000 шт, 210×297, `4+0`, mode 1 — cost 6848.6, price 14108.116, time_hours 0, time_ready 56, weight_kg 7.173.
- [ ] Откат только калькулятора роняет новые кейсы и оставляет старый эталон зелёным. После возврата файла снова всё зелёное. Числа — в «Результат».

```powershell
git stash push -- calc_service/calculators/print_offset.py
python -m pytest calc_service/tests/test_calculators/test_print_offset.py -q
git stash pop
```

- [ ] `python -m pytest calc_service/tests/test_calculators/test_notebook.py -q` — `passed`. Упал эталон блокнота — стоп, эталон в этой задаче не менять.
- [ ] `python scripts/js_port_gaps.py calcPrintOffsetPromo` — в блоке нет `нет порта`. Строка `нет в Python:` пустая или каждый пропуск уже есть в `scripts/js_port_gaps_allowed.txt`. `python scripts/js_port_gaps.py` — код выхода 0.
- [ ] В «Результат» лежит строка для слияния в `docs/js-runner-cases.md`: `node scripts/run_js_calc.mjs calcPrintOffsetPromo --data current --args '[1000,"OffsetPromoА51000",0]'` → price 4244.4, time_ready 56.
- [ ] После `deploy-api`: `POST https://insain.ru/api/v1/calc/print_offset` с телом `{"num_sheet":1000,"material_id":"OffsetPromoА51000","mode":0}` → 200, price 4244.4 (abs ≤ 0.02 и rel ≤ 0.001), time_ready 56.

## Проверки

- [ ] `python scripts/dev.py check` — код выхода 0
- [ ] Self-review — чеклист «Перед сдачей» в [AGENTS.md](../AGENTS.md)

## Риски

- Прод: slug `print_offset` ни на одной боевой форме API не стоит (`docs/site/forms.md`). После выкатки промо-код перестаёт отдавать price 0 и time_ready 8. Обычный код бумаги цену на бою менять не должен. Форму 82 не переключать.
- Цены: JSON не менять. Расхождение с раннером больше rel 0.001 — стоп, эталон под ответ API не подгонять.
- Формы: нет правок ezFC. После `close` этой задачи worktree `form-print-offset` делает `git rebase main`, ставит `черновик` и возвращает тест в свои «Файлы» ради `REF_FORM_DEFAULT`.

## Режим

прод

## Журнал передач

16.11.2026 — Analyst, Grok 4.7 — задача заведена по варианту 1 из `form-print-offset`: порт promo в `print_offset`, эталон mode 0 — дальше Implementer, Opus 5.5

## Найдено вне scope

- Радио «стандарт» на форме 82: value 0 и data-value 1. Боевой JS читает value. В калькулятор и в форму не переносить.
- Штатный раннер до этой задачи не загружает `calcPrintOffset.js`.

## Результат

- Ветка, PR или коммит:
- Период:
- Часы человека: оценка 1 ч — постановка
- Работа агентов:
- Было / стало: боевой `print_offset` на `OffsetPromoА51000` отдаёт price 0 и time_ready 8. Должно стать price 4244.4 и time_ready 56 при mode 0.
- Сделано:
- Чем проверено:
- Не сделано и почему:
- Требуется решение:
- Строка в `docs/js-runner-cases.md` (в ветке файл не править, внести при слиянии): `node scripts/run_js_calc.mjs calcPrintOffsetPromo --data current --args '[1000,"OffsetPromoА51000",0]'` → price 4244.4, time_ready 56.
