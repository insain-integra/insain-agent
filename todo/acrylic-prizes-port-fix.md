# acrylic-prizes-port-fix

Статус: выкатка
Сложность: обычная
Implementer: Opus 5.5
Reviewer: Grok 4.7
Site ops: Opus 5.5
Почему: меняются срок и цена гравировки `acrylic_prizes` на проде, нужен деплой API; предпосылка `form-acrylic-prizes`.
Чат: человек открывает новый чат с моделью из поля Implementer.

## Цель

`AcrylicPrizesCalculator` считает `time_ready` как JS `calcAcrilycPrizes`, а гравировка с `isGraveFill` / `isGraveContur` доходит до лазера, как в JS. На проде дефолт формы 78 даёт `time_ready` ≈ 35.17 (как JS), а не 58.97.

## Контекст и ссылки

- `js_legacy/calc/calcAcrilycPrizes.js`, строки 47–123: `timeReady` операции (лазер, УФ, склейка) берётся только внутри `if (modeProduction… > 0)`, то есть с первого вызова; итог — `time + max(costLayers.timeReady, costOptions.timeReady)`. `layer.options` уходит в `calcLaser` как есть.
- `js_legacy/calc/calcLaser.js`, строки 65–83: ключи `isGrave`, `isGraveFill` `[w,h]`, `isGraveContur` `[w,l]`.
- `calc_service/calculators/acrylic_prizes.py`: строки 173–178 — читает `is_grave_fill` / `is_grave_contur`, а форма (`wp-plugin/forms/acrylic_prizes.js`, строки 52–54) и JS шлют `isGraveFill`; строки 188, 222, 236 — `max(time_ready…)` стоит до проверки `mode_* > 0`.
- Кейс дефолта формы уже снят Implementer `form-acrylic-prizes` (JS, 08.11.2026): `REF_FORM_DEFAULT` / `EXPECTED_FORM_DEFAULT` в `test_acrylic_prizes.py` на ветке `task/form-acrylic-prizes` — `cost` 5599.45, `price` 8977.92, `time_hours` 2.48, `time_ready` 35.17. Взять оттуда: `git show task/form-acrylic-prizes:calc_service/tests/test_calculators/test_acrylic_prizes.py`.
- `docs/js-runner-cases.md` — формат команды раннера.
- Остальное не открывать.

## Scope

- В git (Implementer):
  - `acrylic_prizes.py`: `time_ready_layer = max(...)` для лазера, УФ и склейки — внутри `if mode_* > 0`, как в JS. Режим 0 всего заказа — тоже как JS (сроки операций не входят, `time_ready` = `time_hours`), без «улучшений».
  - `acrylic_prizes.py`: ключи гравировки `isGraveFill` и `isGraveContur` передаются в лазер как `is_grave_fill` / `is_grave_contur`; старые snake_case-ключи в `options` тоже читаются. Схема слоёв (`get_param_schema` / tool schema) описывает `isGraveFill` и `isGraveContur`.
  - `test_acrylic_prizes.py`, эталоны с раннера, пометка `# JS, ДД.ММ.ГГГГ`, команда раннера рядом, `rel=0.001`:
    1) дефолт формы 78 — перенести `REF_FORM_DEFAULT` с ветки формы, assert `cost`, `price`, `time_hours`, `time_ready`;
    2) тот же дефолт с `mode` 0 — assert `price` и `time_ready`;
    3) гравировка: дефолт, на верхнем слое вместо УФ `isGrave: 1`, `isGraveFill: [20,20]` (как шлёт форма) — assert `cost`, `price`, `time_ready`.
    Все три падают на текущем `acrylic_prizes.py`.
  - `docs/js-runner-cases.md`: строки с командами раннера для трёх кейсов.
- На проде (Site ops): после merge в `main` и зелёного CI — `bash infra/deploy.sh`, затем проверка из «Критериев».

## Файлы

- `calc_service/calculators/acrylic_prizes.py`
- `calc_service/tests/test_calculators/test_acrylic_prizes.py` — пересекается с `form-acrylic-prizes`, она ждёт эту задачу
- `docs/js-runner-cases.md`

## Не-scope

- `laser.py`, `uv_print.py`, `calc_service/data/`, `wp-plugin/`, формы ezFC и копия 91.
- `weight_kg`: API `round(…, 2)` = 0.29 против JS 0.2856 — не трогать, assert веса в новых кейсах не делать.
- Такой же шаблон `max(time_ready…)` в других калькуляторах — не сверялся, не трогать.
- Расхождение раннера и Python на кейсе гравировки по цене, кроме ключа `isGraveFill`, — стоп и эскалация Analyst, не чинить по месту.

## Критерии приёмки

Скрипт через `@'…'@ | python -` в PowerShell 5.1 — первой строкой `$OutputEncoding = New-Object System.Text.UTF8Encoding $false`.

- [x] Раннер `calcAcrilycPrizes` на трёх кейсах печатает `cost`, `price`, `timeReady`; дефолт mode 1 — `price` 8977.92, `timeReady` ≈ 35.17. Команды — из `docs/js-runner-cases.md`.

```powershell
node scripts/run_js_calc.mjs calcAcrilycPrizes --data current --args '<args из docs/js-runner-cases.md>'
```

- [x] Тесты. Stdout: `passed`, `failed` нет. На `git stash` правки `acrylic_prizes.py` три новых кейса падают.

```powershell
python -m pytest calc_service/tests/test_calculators/test_acrylic_prizes.py -q
```

- [x] Эталон старого кейса (`REF_PARAMS`, один УФ) не менялся и зелёный — входит в прогон выше; если упал — стоп и эскалация Analyst.

- [ ] После деплоя (Site ops): дефолт формы 78 на боевом API. `price` 8977.92 (разница ≤ 0.02), `time_ready` ≈ 35.17 (`rel ≤ 0.001`); до правки — 58.97. Тело — `REF_FORM_DEFAULT` из теста в JSON. Кейс гравировки: `price` = раннеру, `rel ≤ 0.001`.

```powershell
$api = Invoke-RestMethod -Method Post -Uri https://insain.ru/api/v1/calc/acrylic_prizes -ContentType 'application/json' -Body '<REF_FORM_DEFAULT в JSON>'
$api | Select-Object price, time_ready
```

## Проверки

- [x] `python scripts/dev.py check` — код выхода 0
- [x] Self-review — чеклист «Перед сдачей» в [AGENTS.md](../AGENTS.md)
- [ ] Деплой: `bash infra/deploy.sh` с `main`, smoke зелёный; откат — автооткат скрипта или образ `insain-agent-calc-api:rollback`.

## Риски

- Прод: деплой API с `main`.
- Цены: JSON не меняется. Гравировка с заливкой в `acrylic_prizes` через API подорожает до уровня JS (сейчас площадь заливки теряется). Срок готовности при повторе операции на втором слое станет короче — как у боевой JS-формы.
- Режим 0: как и в JS, срок экономичного заказа может выйти короче стандартного. Это поведение JS, сохраняется намеренно; менять — отдельная задача с решением человека.
- Формы: нет. Из форм через API `acrylic_prizes` считает только копия 91 (draft).

## Режим

прод

## Журнал передач

Строка на сессию: `<дата> — <роль>, <модель> — <итог> — дальше <роль>`. Блокер — по формату
[docs/agents/workflow.md](../docs/agents/workflow.md). Замечания ревью — ниже, в «Ревью N».

- 2026-11-08 — Analyst, Opus 5.5 — предпосылка `form-acrylic-prizes`: срок как в JS (человек: «сроки отличаются на JS и API»), ключи `isGraveFill` / `isGraveContur`; кейс дефолта формы переезжает сюда — дальше Implementer
- 2026-11-08 — Implementer, Opus 5.5 — `time_ready` внутри `mode_*>0`, `isGraveFill`/`isGraveContur` в лазер; 3 эталона с раннера; stash-proof; `make check` зелёный — дальше Reviewer (Grok 4.7)
- 2026-11-08 — Reviewer, Grok 4.7 — принято — дальше человек: слияние
- 2026-11-08 — человек — слито в main — дальше Site ops

## Ревью 1

Вердикт: принято. Статус остаётся `ревью`.

- `time_ready` лазера, УФ и склейки берётся только внутри `if mode_* > 0`, затем режим обнуляется — как `calcAcrilycPrizes.js` строки 53–56, 78–81, 92–95. Итог `time_hours + max` по слоям совпадает со строкой 123 (`costOptions.timeReady` в JS остаётся 0). Режим 0: `time_ready` = `time_hours`.
- `isGraveFill` / `isGraveContur` (snake_case, если camelCase нет) уходят в лазер как `is_grave_fill` / `is_grave_contur`. Схема: строка описания `get_param_schema` и properties `get_tool_schema`.
- Раннер `calcAcrilycPrizes --data current`: mode 1 — `price` 8977.92, `time_ready` 35.17; mode 0 — `price` 7794.4, `time_ready` 2.02; гравировка — `cost` 6389.45, `price` 10241.92, `time_ready` 36.36. Эталоны тестов те же.
- С правкой: `python -m pytest calc_service/tests/test_calculators/test_acrylic_prizes.py -q` — 9 passed.
- `git stash` только `acrylic_prizes.py`: 3 failed (`time_ready` 58.97, `time_ready` 58.51, `cost` 4915.45), 6 passed, включая `REF_PARAMS`. Stash возвращён. Блок `REF_PARAMS` / `EXPECTED_REF` в diff нет.
- `желательно`: в рабочем дереве ещё `docs/dashboard.md` (make check дописал эту задачу в список). В «Файлы» его нет, файл общий с `dashboard-harness`. Коммит правки калькулятора — без него.

## Найдено вне scope

- На ветке `task/form-acrylic-prizes` эталон `REF_FORM_DEFAULT` был только в рабочем дереве (не в коммите); сняли заново раннером `calcAcrilycPrizes` 08.11.2026 — числа совпали с задачей.

## Результат

- Ветка, PR или коммит: `task/acrylic-prizes-port-fix`, fast-forward в `main`
- Период: 2026-11-08
- Часы человека:
- Работа агентов: Implementer, одна сессия
- Было / стало: `time_ready` дефолта формы 58.97 → 35.17; гравировка с `isGraveFill` cost 4915.45 → 6389.45 (как JS)
- Сделано:
  - `acrylic_prizes.py`: `max(time_ready…)` для лазера/УФ/склейки только внутри `if mode_* > 0`; `isGraveFill`/`isGraveContur` (+ snake_case) в лазер; схема tool/param
  - три эталона в `test_acrylic_prizes.py` + команды в `docs/js-runner-cases.md`
- Чем проверено:
  - раннер: mode1 `price` 8977.92 `time_ready` ≈35.17; mode0 `price` 7794.4 `time_ready` 2.02; grave `cost` 6389.45 `price` 10241.92 `time_ready` 36.36
  - `git stash` только `acrylic_prizes.py`: 3 новых FAIL (58.97 / 58.51 / cost 4915.45), `REF_PARAMS` PASS; после pop — 9 passed
  - `python scripts/dev.py check` — exit 0 (516+81 passed)
- Не сделано и почему: деплой API — Site ops после merge
- Требуется решение: нет
