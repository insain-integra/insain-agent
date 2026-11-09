# print-sheet-weight-port-fix

Статус: черновик
Сложность: высокая
Implementer: Opus 5.5
Reviewer: Grok 4.7
Site ops: Grok 4.7
Почему: порт веса расходится с JS; правка `print_sheet` сдвигает вес у вызывающих (pennant, flag и др.); после merge — деплой API по skill.
Чат: человек открывает новый чат с моделью из поля Implementer.

## Цель

`weight_kg` листовой печати на лазерной ветке совпадает с JS (`calcPrintSheet` → `calcPrintLaser`: вес по `numSheet` и `sizeSheet`, плюс ламинация). На входе блокера `form-pennant` (50 шт., 80×120, `PaperCoated115M`, `4+0`, mode 1, без ламинации) раннер, локальный Python и боевой API после деплоя дают один и тот же `weight_kg` с `rel ≤ 0.001`. Цена и срок на этом входе не разъезжаются.

## Контекст и ссылки

- `.cursor/skills/port-fix-prerequisite/SKILL.md` — порядок предпосылки.
- Держит `todo/form-pennant.md` (форма 73). Блокер 2026-11-10: без ламинации раннер `weight_kg` 0.1328, Python и боевой API 0.1052; с ламинацией (дефолт формы) JS страницы 1.0144 против API 0.8818.
- Гипотеза: `calc_service/calculators/print_sheet.py` (~716–728) на не-inkjet считает `calc_weight(quantity, …, size=изделие)`; JS `calcPrintLaser` / `calcPrintInkJet` — `calcWeight(numSheet, …, sizeSheet)`.
- `js_legacy/calc/calcPrintSheet.js` (~178), `js_legacy/calc/calcPrintLaser.js` (~61–63).
- Эталоны и команда раннера — `docs/js-runner-cases.md`; кейс pennant без ламинации уже есть.
- Остальное не открывать.

## Scope

- В git (Implementer): локализовать расхождение раннером (`calcPrintSheet` и/или `calcPennantPaper` без ламинации); выровнять вес в `print_sheet` с JS; эталоны только с раннера; тест падает без правки; соседи, вызывающие `PrintSheetCalculator`, зелёные или осознанно пересняты только если их вес не был сверен с JS; строка раннера в `docs/js-runner-cases.md` при новом кейсе.
- На проде (Site ops): после ревью, слияния в `main` и зелёного CI — `bash infra/deploy.sh` (skill `deploy-api`); smoke веса на входе блокера `form-pennant`.

## Файлы

- `calc_service/calculators/print_sheet.py`
- `calc_service/tests/test_calculators/test_print_sheet.py`
- `calc_service/tests/test_calculators/test_pennant.py` — только `weight_kg` (и связанные assert) эталона блокера, если сдвинулся после правки
- `docs/js-runner-cases.md` — при новом или уточнённом кейсе веса

## Не-scope

- `wp-plugin/forms/pennant.js`, дубль формы 73, `todo/form-pennant.md` кроме снятия «ждёт» через `close`.
- Правка цен, наценок, `calc_service/data/`.
- `scripts/run_js_calc.mjs` (загрузка `laminat.json` / `calcLamination.js`) — harness; сверка веса — на кейсе без ламинации.
- Тот же шаблон веса в других калькуляторах, если они не вызывают `PrintSheetCalculator` и не сверены с JS.
- Формы эпика, кроме возврата к `form-pennant` после закрытия.

## Критерии приёмки

Каждый пункт — команда и ожидаемый результат. В PowerShell 5.1 кавычки JSON внутри аргумента экранируются `\"`.

- [ ] Локализация. На входе pennant без ламинации записаны `weight_kg` раннера и локального Python/`POST` до правки; указана строка JS и Python, дающая разницу. Без правки `print_sheet` новый тест веса `failed`.

```powershell
node scripts/run_js_calc.mjs calcPennantPaper --data current --args '[50,[80,120],\"4+0\",\"PaperCoated115M\",{},1]'
python -c "from calculators.pennant import PennantCalculator; print(PennantCalculator().execute({'quantity':50,'width_mm':80,'height_mm':120,'material_id':'PaperCoated115M','color':'4+0','mode':1})['weight_kg'])"
```

- [ ] Эталон веса с раннера в тесте `print_sheet` и/или `pennant`: пометка `# JS, ДД.ММ.ГГГГ`, команда раннера рядом, assert `weight_kg` с `rel=0.001`. `price` и `time_ready` на том же входе — `rel ≤ 0.001` к раннеру (не разъехались).

```powershell
python -m pytest calc_service/tests/test_calculators/test_print_sheet.py calc_service/tests/test_calculators/test_pennant.py -q
```

- [ ] Падение без правки. Откат только `print_sheet.py` → новые кейсы веса `failed`, старые эталоны цены где возможно `passed`; после возврата файла — снова `passed`.

```powershell
git stash push -- calc_service/calculators/print_sheet.py
python -m pytest calc_service/tests/test_calculators/test_print_sheet.py calc_service/tests/test_calculators/test_pennant.py -q
git stash pop
```

- [ ] Соседи. Калькуляторы с `PrintSheetCalculator` — тесты зелёные. Упал эталон соседа, сверенный с JS на другом режиме — стоп, `заблокировано: аналитик`, не переснимать в этой задаче.

```powershell
Select-String -Path calc_service\calculators\*.py -Pattern 'PrintSheetCalculator'
python -m pytest calc_service/tests/test_calculators/ -q --tb=no
```

- [ ] Боевой API после деплоя. `weight_kg` равен раннеру (`rel ≤ 0.001`) на теле эталона pennant без ламинации.

```powershell
Invoke-RestMethod -Method Post -Uri https://insain.ru/api/v1/calc/pennant -ContentType 'application/json' -Body '{"quantity":50,"width_mm":80,"height_mm":120,"material_id":"PaperCoated115M","color":"4+0","mode":1}' | Select-Object weight_kg, price, time_ready
```

## Проверки

- [ ] `python scripts/dev.py check` — код выхода 0.
- [ ] Self-review — чеклист «Перед сдачей» в [AGENTS.md](../AGENTS.md).

## Риски

- Прод: деплой API меняет `weight_kg` у всех расчётов через `print_sheet` (вымпелы, флаги, календари, магниты и др.). Откат — предыдущий образ по skill `deploy-api`.
- Цены: JSON не трогать. Если при выравнивании веса сдвинется `price`/`time_ready` — стоп и эскалация Analyst.
- Формы: боевые формы не переключать. `form-pennant` ждёт закрытия этой задачи.

## Режим

прод

## Журнал передач

2026-11-10 — Analyst, Grok 4.7 — заведена предпосылка по весу print_sheet; `form-pennant` ждёт — дальше Implementer, Opus 5.5

## Найдено вне scope

- Раннер не грузит `laminat.json` / `calcLamination.js` — дефолт формы 73 с ламинацией раннером не считается. Сверка веса в этой задаче — без ламинации.

## Результат

- Ветка, PR или коммит:
- Период:
- Часы человека:
- Работа агентов:
- Было / стало:
- Сделано:
- Чем проверено:
- Не сделано и почему:
- Требуется решение:
