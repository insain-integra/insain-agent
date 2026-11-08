# presswall-banner-options

Статус: закрытие
Сложность: высокая
Implementer: Opus 5.5
Reviewer: Grok 4.7
Site ops: Grok 4.7
Почему: правка общей `calc_eyelet` сдвигает цены у всех вызывающих; выкатка API — шаги skill `deploy-api`.
Чат: человек открывает новый чат с моделью из поля Implementer.

## Цель

`POST /api/v1/calc/presswall` считает баннер прессвола так же, как `insaincalc.calcPresswall` на боевой форме 46: принимает крепление баннера (люверсы или карман), чехол и режим. На входах формы 46 `price` и `time_ready` API равны раннеру JS (rel ≤ 0.001). Задача держит `todo/form-presswall.md`.

## Контекст и ссылки

- Блокер — `todo/form-presswall.md`, «Журнал передач», 08.11.2026. Порядок — `.cursor/skills/port-fix-prerequisite/SKILL.md`, шаги 8–13.
- Форма 46, cjsCalc 1862: dpdAttachment = люверсы — `options.isEyelet = [300,300,300,300]`; карман — `isPocket = [1,0,1,0]` и `isCutting = [0,1,0,1]`. Одна из двух опций уходит всегда.
- Четыре расхождения на тираже 1, `Joker30_20_eyelet`, `BannerFronlitCoat400`, каркас (раннер против Python, 08.11.2026, Analyst):
  1. Крепление не доходит до печати. `js_legacy/calc/calcPresswall.js:50` — `calcPrintRoll(n, presswall.sizeBanner, materialID, printerID, options, …)`, options целиком. `calc_service/calculators/presswall.py:224-231` — `PrintRollCalculator().calculate` без опций; в `get_tool_schema` крепления нет. `print_roll.py` опции `is_eyelet`, `is_pocket`, `is_cutting` уже принимает (строки 138–141). Карман после проброса сходится с JS точно: 12659.624.
  2. Число люверсов. `js_legacy/calc/calcProcessTools.js:269` — `Math.round((len[i]-margin*2)/step[i])`; `calc_service/common/process_tools.py:504` — `round(...)`, банковское округление. Баннер 3000×2000, шаг 300: `(2000-50)/300 = 6.5`, JS 7, Python 6 — 34 люверса против 32. `calcEyelet(1,[3000,2000],[300,300,300,300],1)`: JS cost 713.0888888888888, price 1140.9422222222222, time 0.43; Python 675.5778, 1080.9244, 0.41. `calcPrintRoll` с этими люверсами: JS cost 4286, price 6908, time_ready 17.78; Python 4249, 6848, 17.76.
  3. Режим баннера. `calcPresswall.js:50` передаёт `modeProduction = 1` — присваивание: печать баннера и следующий за ней `calcSewingCovers` в JS всегда в режиме 1, каркас (`calcCutProfile`, строка 40) — в режиме формы. `presswall.py:230` и `:256` передают `mode.value`. Без крепления: mode 2 — JS 11579.704 / 18.34, Python 12370.704 / 10.88; mode 0 — price совпадает (11327.544), time_ready JS 26.08, Python 26.24.
  4. Чехол не считается. `bag160` и `bag210` лежат на верхнем уровне `calc_service/data/materials/presswall.json` (строки 502–517), цикл `presswall.py:248-252` ищет их внутри групп и молча пропускает. `is_bag: "bag160"` в Python не меняет цену; в JS чехол — +2017.6175. `calc_sewing_covers(1,[1600,150,150],"Oxford600D",1)` с JS сходится: 1251.125 / 2017.6175 / 25.25.
- `weight_kg`: раннер 9.79, Python 9.78 — `print_roll` отдаёт вес баннера, уже округлённый до 0.01 (JS 2.41, Python 2.40). Не чинится; в assert веса — допуск `abs=0.02`.
- Тесты: `calc_service/tests/test_calculators/test_presswall.py`, `test_print_roll.py`, `calc_service/tests/test_process_tools.py` (класс `TestEyelet`).
- Остальное не открывать.

## Scope

В git (Implementer):

- `presswall.py`: параметры `is_eyelet`, `is_pocket`, `is_cutting` — формат и описания как в `get_tool_schema` `print_roll.py`; в `get_tool_schema` и `get_param_schema` (группа `options`). Пробросить в `PrintRollCalculator` баннера. Шаг люверсов и стороны кармана приходят с формы, в Python не задаются.
- `presswall.py`: печать баннера — `mode` 1, как `calcPresswall.js:50`. Чехол после печати баннера — тоже `mode` 1; без баннера (`material_id` пуст) — режим формы. Каркас — режим формы. Поведение и ссылка на строку JS — в docstring модуля.
- `presswall.py`: чехол `bag160` / `bag210` находится по коду верхнего уровня `presswall.json`. JSON не менять.
- `process_tools.py`, `calc_eyelet`: округление числа люверсов как `Math.round` — до ближайшего, половина вверх (6.5 → 7, 6.3 → 6), не `ceil`. Решение человека 08.11.2026.
- Эталоны раннера (`# JS, ДД.ММ.ГГГГ`, команда раннера рядом): `calcEyelet` в `TestEyelet`, `calcPrintRoll` с люверсами в `test_print_roll.py`, четыре кейса `calcPresswall` в `test_presswall.py`. Старый `REF_PARAMS` (без крепления, 11453.624) остаётся. Assert `cost`, `price`, `time_ready` — `rel=0.001`; `weight_kg` — `abs=0.02`.
- `docs/js-runner-cases.md`: строки и команды новых кейсов `calcPresswall`.

На проде (Site ops): после слияния в `main` и зелёного CI — skill `deploy-api`, затем боевой API на кейсах ниже.

## Файлы

- `calc_service/calculators/presswall.py`
- `calc_service/common/process_tools.py` — только `calc_eyelet`
- `calc_service/tests/test_calculators/test_presswall.py`
- `calc_service/tests/test_calculators/test_print_roll.py`
- `calc_service/tests/test_process_tools.py`
- `docs/js-runner-cases.md`

## Не-scope

- `round(` и похожие места в других функциях `process_tools.py` и других калькуляторах — не сверялись с JS. Найдено — строка в «Найдено вне scope».
- Вес баннера в `print_roll` (округление до 0.01) — только допуск в assert.
- `calc_service/data/`, `scripts/js_port_gaps_allowed.txt`, `scripts/run_js_calc.mjs`, `js_legacy/`.
- `wp-plugin/`, формы ezFC, `todo/form-presswall.md` — после закрытия этой задачи.
- Другие опции `print_roll` (`is_gluing`, `is_joining`, `is_lamination`) в presswall — форма 46 их не передаёт.
- Режим формы для баннера и чехла. Решение человека 08.11.2026: режим 1 в JS — ошибка, верно передавать `modeProduction`. Пока идёт сверка — как JS; после принятия копии 46 — отдельная задача `presswall-banner-mode` (эпик, «Порядок»).

## Критерии приёмки

Каждый пункт — команда и ожидаемый результат. В PowerShell 5.1 кавычки JSON внутри `--args` экранируются `\"`.
Скрипт через `@'…'@ | python -` в PowerShell 5.1 — первой строкой `$OutputEncoding = New-Object System.Text.UTF8Encoding $false`, иначе кириллица в нём станет `?`.

- [x] Эталоны раннера на `--data current`. Ожидается (08.11.2026, перед правкой — переснять): `calcEyelet` — cost 713.0888888888888, price 1140.9422222222222, time 0.43; `calcPrintRoll` — cost 4286, price 6908, time_ready 17.78; `calcPresswall` — люверсы mode 1: 8556 / 13914.624 / 19.94; карман mode 1: 7772 / 12659.624 / 19.12; люверсы mode 2: 8634.8 / 14040.704 / 19.99; люверсы и `bag160` mode 1: 9807.125 / 15932.2415 / 28.66.

```powershell
node scripts/run_js_calc.mjs calcEyelet --data current --args '[1,[3000,2000],[300,300,300,300],1]'
node scripts/run_js_calc.mjs calcPrintRoll --data current --args '[1,[3000,2000],\"BannerFronlitCoat400\",\"TechnojetXR720\",{\"isEyelet\":[300,300,300,300]},1]'
node scripts/run_js_calc.mjs calcPresswall --data current --args '[1,\"Joker30_20_eyelet\",\"BannerFronlitCoat400\",{\"isPresswall\":true,\"isRent\":0,\"isEyelet\":[300,300,300,300]},1]'
node scripts/run_js_calc.mjs calcPresswall --data current --args '[1,\"Joker30_20_eyelet\",\"BannerFronlitCoat400\",{\"isPresswall\":true,\"isRent\":0,\"isPocket\":[1,0,1,0],\"isCutting\":[0,1,0,1]},1]'
node scripts/run_js_calc.mjs calcPresswall --data current --args '[1,\"Joker30_20_eyelet\",\"BannerFronlitCoat400\",{\"isPresswall\":true,\"isRent\":0,\"isEyelet\":[300,300,300,300]},2]'
node scripts/run_js_calc.mjs calcPresswall --data current --args '[1,\"Joker30_20_eyelet\",\"BannerFronlitCoat400\",{\"isPresswall\":true,\"isRent\":0,\"isEyelet\":[300,300,300,300],\"isBag\":\"bag160\"},1]'
```

- [x] Новые эталоны в тестах — числа раннера, пометка `# JS, ДД.ММ.ГГГГ`. Stdout: `passed`, `failed` нет.

```powershell
python -m pytest calc_service/tests/test_calculators/test_presswall.py calc_service/tests/test_calculators/test_print_roll.py calc_service/tests/test_process_tools.py -q
```

- [x] Тест падает без правки. Ожидается: новые кейсы `failed` (presswall с люверсами — 11453.624 без проброса; `calcEyelet` — 32 люверса), старый `REF_PARAMS` presswall — `passed`. После `pop` — снова `passed`. Числа — в «Результат».

```powershell
git stash push -- calc_service/calculators/presswall.py calc_service/common/process_tools.py
python -m pytest calc_service/tests/test_calculators/test_presswall.py calc_service/tests/test_calculators/test_print_roll.py calc_service/tests/test_process_tools.py -q
git stash pop
```

- [x] Соседи не сдвинулись: калькуляторы, которые вызывают `PrintRollCalculator`. Stdout: `passed`. Упал эталон соседа — стоп, `заблокировано: аналитик`.

```powershell
python -m pytest calc_service/tests/test_calculators/test_rollup.py calc_service/tests/test_calculators/test_canvas.py -q
```

- [x] Схема: в выводе есть `is_eyelet`, `is_pocket`, `is_cutting`.

```powershell
$env:PYTHONIOENCODING='utf-8'; @'
import sys; sys.path.insert(0, "calc_service")
from calculators.presswall import PresswallCalculator
print(sorted(PresswallCalculator().get_tool_schema()["parameters"]["properties"]))
'@ | python -
```

- [x] `docs/js-runner-cases.md`: четыре новые строки `calcPresswall` с `price` раннера и их команды.

```powershell
Select-String -Path docs\js-runner-cases.md -Pattern 'calcPresswall'
```

- [x] После деплоя (Site ops): боевой API на кейсе «люверсы, mode 1» — `price` 13914.624 (rel ≤ 0.001 к раннеру), `time_ready` 19.94. То же для трёх остальных кейсов — тела по образцу.

```powershell
Invoke-RestMethod -Method Post -Uri https://insain.ru/api/v1/calc/presswall -ContentType 'application/json' -Body '{"quantity":1,"presswall_id":"Joker30_20_eyelet","material_id":"BannerFronlitCoat400","is_presswall":true,"is_rent":0,"is_eyelet":[300,300,300,300],"mode":1}' | Select-Object price, time_ready
```

## Проверки

- [x] `python scripts/dev.py check` — код выхода 0
- [x] Self-review — чеклист «Перед сдачей» в [AGENTS.md](../AGENTS.md)

## Риски

- Прод: выкатка API по skill `deploy-api`, откат — его же автооткат. Формы на `presswall` и `print_roll` не переведены (`docs/site/forms.md`: форма 23 и 46 на старом JS), принятых копий нет — клиентские цены на сайте не меняются.
- Цены: `print_roll` через API с люверсами, где `(сторона − 50) / шаг` даёт ровно x.5, станет на люверс дороже на сторону — как в JS. `presswall` API: с креплением и чехлом дороже, в mode 2 с баннером дешевле (баннер в режиме 1, как на боевой форме). JSON не меняется.
- Режим 1 для баннера повторяет присваивание в JS (`modeProduction = 1`) только на время сверки. Переход на режим формы — `presswall-banner-mode`, смена цены на сайте: mode 2 без крепления 11579.704 → 12370.704, срок 18.34 → 10.88 ч; mode 0 — меняется срок.
- Формы: нет.

## Режим

прод

## Журнал передач

Строка на сессию: `<дата> — <роль>, <модель> — <итог> — дальше <роль>`. Блокер — по формату
[docs/agents/workflow.md](../docs/agents/workflow.md). Замечания ревью — ниже, в «Ревью N».

08.11.2026 — Analyst, Opus 5.5 — задача заведена по блокеру `todo/form-presswall.md`; раннером найдены ещё три расхождения той же функции (люверсы `calc_eyelet`, режим баннера, чехол) — дальше Implementer

08.11.2026 — Implementer, Composer — четыре расхождения закрыты в Python (крепление, Math.round люверсов, mode 1 баннера/чехла, bag160 верхний уровень); `make check` зелёный — дальше Reviewer, Grok 4.7

08.11.2026 — Reviewer, Grok 4.7 — блокер: `execute()` на люверсах падает, POST не отдаёт price — дальше Implementer, Opus 5.5

08.11.2026 — Implementer, Composer — блокер «Ревью 1»: `calc_eyelet` code=`Eyelet`, name/title=`Люверсы`; четыре кейса на `execute()`; 2 skip → passed; `make check` зелёный — дальше Reviewer, Grok 4.7

08.11.2026 — Reviewer, Grok 4.7 — принято: `execute()` на люверсах отдаёт price раннера — дальше человек: слияние

08.11.2026 — человек — принято, слияние в `main` — дальше Site ops, выкатка API

08.11.2026 — Site ops, Grok 4.7 — API `7799935` выкачен, smoke зелёный, четыре кейса presswall совпали с раннером — дальше человек: закрытие

## Ревью 1

08.11.2026 — Reviewer, Grok 4.7. Вердикт: доработка.

- `блокер` — `POST /api/v1/calc/presswall` вызывает `execute()` (`calc_service/main.py`, `ValueError` → 400). На теле «люверсы, mode 1» `PresswallCalculator.execute()` падает: `у материала 'Люверсы' поле name совпадает с code`. Цену 13914.624 этот код не отдаст, критерий боевого API невыполним. `test_js_ref_eyelet_mode1`, `test_js_ref_eyelet_mode2`, `test_js_ref_eyelet_bag160` и `test_expected_values_print_roll_eyelet_3000x2000` зовут `calculate()` и ошибку не ловят. Карман через `execute()` проходит.

  Сделать: в `calc_eyelet` пользовательские `name` и `title` остаются «Люверсы» (как JS `result.material.set('Люверсы',['Люверсы',…])`), `code` — другой и не равен им. `execute()` на трёх кейсах presswall с люверсами и на `REF_PARAMS_EYELET_3000` возвращает `price` и `time_ready` раннера, допуск прежний. Цену не менять. Два skip в `test_print_roll.py` (эталон 2, строка 284, и JS-эталон 1000×1500, строка 455) после правки — `passed`: на 1500×1000 и 1000×1500 половины нет, число люверсов то же.

Локальные критерии этого круга, кроме пути `execute()`, выполнены. Раннер 08.11.2026 совпал с эталонами (в том числе чехол: weight 10.0329605). Pytest трёх файлов: 70 passed, 2 skipped. Соседи rollup+canvas: 12 passed. В схеме есть `is_eyelet`, `is_pocket`, `is_cutting`. В `docs/js-runner-cases.md` — четыре строки `calcPresswall`. Деплой не смотрел: он после слияния. `make check` и stash в этом круге не повторял.

- `вне scope` — в рабочем дереве ещё `todo/form-presswall.md` и `todo/EPIC-forms-to-api.md`. В коммит `task/presswall-banner-options` не входят.

## Ревью 2

08.11.2026 — Reviewer, Grok 4.7. Вердикт: принято.

Блокер «Ревью 1» закрыт. `calc_eyelet`: `code` = `Eyelet`, `name` и `title` = «Люверсы». `execute()` на трёх кейсах presswall с люверсами и на `calcPrintRoll` 3000×2000 отдаёт price и time_ready раннера (13914.624 / 19.94, 14040.704 / 19.99, 15932.2415 / 28.66, 6908 / 17.78), люверсов 34. Pytest трёх файлов: 72 passed, skipped нет — эталон 2 и JS-эталон 1000×1500 больше не пропускаются. Цена не сдвинута. Деплой по-прежнему после слияния.

- `вне scope` — `todo/form-presswall.md` и `todo/EPIC-forms-to-api.md` в рабочем дереве. В коммит ветки не входят.

## Найдено вне scope

- `STATUS.md`, раздел Git: снимок всё ещё `e52e947` (25–28.10.2026). На VDS до этой выкатки был `511c660`. Файл не правил.

## Результат

- Ветка, PR или коммит: `7799935` на `main`. На VDS `git pull --ff-only`: `511c660` → `7799935`.
- Период: 08.11.2026
- Часы человека:
- Работа агентов: Implementer (доработка «Ревью 1»); Site ops (выкатка API)
- Было / стало: прод API `511c660` → `7799935`. Боевой `POST /api/v1/calc/presswall` с креплением отдаёт price и time_ready раннера.
- Сделано:
  - `bash infra/deploy.sh` на `insain-prod`, `/opt/insain-agent`. Образ до сборки сохранён как `insain-agent-calc-api:rollback` (`49b557527730`). Контейнер `insain-calc-api` пересоздан, healthy, `127.0.0.1:8002->8001`.
  - В образ из диапазона `511c660..7799935` вошли `presswall.py` и `process_tools.py` (`calc_eyelet`). Плагин WordPress не выкладывался.
  - Код до выкатки (Implementer, круг «Ревью 1»): `code=Eyelet`, name/title «Люверсы»; pytest 72 passed; `python scripts/dev.py check` — 537 + 81 passed, exit 0.
- Чем проверено:
  - CI `7799935`: GitHub Actions run 42466986665, check `completed` / `success`.
  - Smoke `infra/deploy.sh`: `GET /api/v1/calculators` → 200, `POST /api/v1/calc/puzzle` → 200. «Готово: 7799935 выкачен, smoke пройден.»
  - Снаружи: `curl -fsS https://insain.ru/api/v1/calculators` → 200, начало `[{"slug":"laser","name":"Лазерная резка и гравировка",…`.
  - Боевой POST `Invoke-RestMethod` на `https://insain.ru/api/v1/calc/presswall`, тела из критерия. rel к раннеру ≤ 0.001 (mode 2 — float `14040.704000000002` / `19.990000000000002`, rel ~ 1e-16):
    - люверсы, mode 1: price 13914.624, time_ready 19.94, cost 8556
    - карман, mode 1: price 12659.624, time_ready 19.12, cost 7772
    - люверсы, mode 2: price 14040.704, time_ready 19.99, cost 8634.8
    - люверсы и `bag160`, mode 1: price 15932.2415, time_ready 28.66, cost 9807.125
- Не сделано и почему: `todo/form-presswall.md`, `todo/EPIC-forms-to-api.md`, `docs/dashboard.md` не трогал. Коммит и пуш не делал.
- Как откатить: образ `insain-agent-calc-api:rollback` — состояние до этой сборки. На VDS из `/opt/insain-agent`: `git -c safe.directory=/opt/insain-agent reset --hard 511c6603303e9459a4816a5b0f1a5f51d541f0cc`, `docker tag insain-agent-calc-api:rollback insain-agent-calc-api:latest`, `docker compose -f docker-compose.calc-only.yml up -d --no-build --force-recreate`. Это вернёт весь диапазон `511c660..7799935`, не только presswall. Автооткат скрипта не срабатывал: smoke прошёл.
- Требуется решение: нет
