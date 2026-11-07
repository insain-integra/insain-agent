# uv-print-prepare

Статус: выкатка
Сложность: обычная
Implementer: Opus 5.5
Reviewer: Grok 4.7
Site ops: Opus 5.5
Почему: меняются цены на проде (экономичный режим и круговая печать УФ у всех вызывающих калькуляторов), нужен деплой API.
Чат: человек открывает новый чат с моделью из поля Implementer.

## Цель

`UVPrintCalculator` считает время подготовки как JS `calcUVPrint`: плоская печать — `timePrepare * modeProduction`, круговая — `timePrepareAround * modeProduction`, при `mode=0` подготовка 0. На проде `POST /api/v1/calc/acrylic_prizes` на дефолте формы 78 (УФ на двух слоях) даёт ту же `price`, что JS `calcAcrilycPrizes`.

## Контекст и ссылки

- `js_legacy/calc/calcUVPrint.js`, строки 94–112 — расчёт `timePrepare` для `plain` и круговой печати.
- `calc_service/calculators/uv_print.py`, строки 230–241 — `max(1, mode.value)` в обеих ветках; в круговой ветке берётся `printer.time_prepare` вместо `timePrepareAround`.
- `calc_service/equipment/base.py` (`EquipmentSpec`) и `calc_service/equipment/loader.py` (загрузка принтеров) — поля `timePrepareAround` нет, в JSON оно есть: `RimalSuvUV` 0.5 (при `timePrepare` 0.2), `PrintUV` 0.05.
- `todo/form-acrylic-prizes.md`, «Журнал передач» — блокер Implementer с числами: `calcUVPrint` 100 шт. 20×20, JS mode 1 = 1048/1677, mode 0 = 684/1095, Python mode 0 = mode 1 = 1048/1677.
- `docs/js-runner-cases.md` — формат команды раннера.
- Образец без `max(1, …)`: `calc_service/calculators/print_inkjet.py`, строки 162–163.
- Остальное не открывать.

## Scope

- В git (Implementer):
  - `uv_print.py`: в ветке `plain` — `printer.time_prepare * mode.value`; в круговой — `printer.time_prepare_around * mode.value`. Дефолты `or 0.2` / `0.05` в коде не множить: значения из JSON.
  - `EquipmentSpec`: поле `time_prepare_around: float = 0.0`; загрузчик принтеров читает `timePrepareAround`.
  - `test_uv_print.py`: два эталона с прогона раннера, пометка `# JS, ДД.ММ.ГГГГ` и команда раннера рядом, допуск `rel=0.001`:
    1) 100 шт., 20×20, `plain`, mode 0 — `cost`/`price` как JS и меньше, чем у того же входа с mode 1;
    2) круговая печать (`surface` не `plain`), mode 1 — `cost`/`price` как JS.
    Оба теста падают на текущем `uv_print.py`.
  - `docs/js-runner-cases.md`: строка с командой раннера `calcUVPrint` для обоих эталонов.
- На проде (Site ops): после merge в `main` и зелёного CI — `bash infra/deploy.sh`, затем проверка `acrylic_prizes` из «Критериев».

## Файлы

- `calc_service/calculators/uv_print.py`
- `calc_service/equipment/base.py`, `calc_service/equipment/loader.py`
- `calc_service/tests/test_calculators/test_uv_print.py`
- `docs/js-runner-cases.md`

## Не-scope

- `acrylic_prizes.py`, `calc_service/data/`, `wp-plugin/`, формы ezFC и копии (26, 69, 91).
- `max(1, mode.value)` в других калькуляторах (`print_laser`, `print_sheet`, `print_offset`, `print_wide`, `pad_print`, `design`, `embossing`) — не сверялись с JS, не трогать.
- Эталоны `tablets`, `plaque`, `badge`, `uv_badge`, `shild`, `acrylic_prizes` не переснимать. Они на mode 1 и `plain`; если хоть один упал — стоп и эскалация Analyst.
- `test_acrylic_prizes.py` — его правит `form-acrylic-prizes`.

## Критерии приёмки

Скрипт через `@'…'@ | python -` в PowerShell 5.1 — первой строкой `$OutputEncoding = New-Object System.Text.UTF8Encoding $false`.

- [x] Раннер `calcUVPrint` на обоих эталонах печатает `cost` и `price`; на 100 шт. 20×20 `plain` mode 0 — `price` ≈ 1095, mode 1 — ≈ 1677. Команды — из `docs/js-runner-cases.md`.

```powershell
node scripts/run_js_calc.mjs calcUVPrint --data current --args '<args из docs/js-runner-cases.md>'
```

- [x] Загрузчик видит поле. Stdout: `0.5 0.05`.

```powershell
$OutputEncoding = New-Object System.Text.UTF8Encoding $false
@'
import sys
sys.path.insert(0, "calc_service")
from equipment import printer
print(printer.get("RimalSuvUV").time_prepare_around, printer.get("PrintUV").time_prepare_around)
'@ | python -
```

- [x] Новые тесты УФ. Stdout: `passed`, `failed` нет. На `git stash` правки `uv_print.py` оба новых теста падают (проверка «тест падал бы без правки»).

```powershell
python -m pytest calc_service/tests/test_calculators/test_uv_print.py -q
```

- [x] Вызывающие калькуляторы не сдвинулись. Stdout: `passed`, `failed` нет.

```powershell
python -m pytest calc_service/tests/test_calculators/test_tablets.py calc_service/tests/test_calculators/test_plaque.py calc_service/tests/test_calculators/test_badge.py calc_service/tests/test_calculators/test_uv_badge.py calc_service/tests/test_calculators/test_shild.py calc_service/tests/test_calculators/test_acrylic_prizes.py -q
```

- [ ] После деплоя (Site ops): дефолт формы 78 на боевом API равен JS. Тело — дефолт формы из блокера `form-acrylic-prizes` (100 шт., 2× AcrylTrans3 20×20, рез лазером и УФ на обоих слоях, mode 1); Implementer сверяет тело с раннером `calcAcrilycPrizes` и вписывает в отчёт. `price` = цене раннера (≈ 8977.92), разница ≤ 0.02 и `rel ≤ 0.001`; до правки было 9559.92.

```powershell
$api = Invoke-RestMethod -Method Post -Uri https://insain.ru/api/v1/calc/acrylic_prizes -ContentType 'application/json' -Body '<тело дефолта формы 78>'
$api | Select-Object price
```

## Проверки

- [x] `python scripts/dev.py check` — код выхода 0
- [x] Self-review — чеклист «Перед сдачей» в [AGENTS.md](../AGENTS.md)
- [ ] Деплой: `bash infra/deploy.sh` с `main`, smoke зелёный; откат — автооткат скрипта или образ `insain-agent-calc-api:rollback`.

## Риски

- Прод: деплой API с `main`.
- Цены: без правки JSON. Экономичный режим УФ дешевеет, круговая УФ дорожает (подготовка 0.5 ч вместо 0.2 ч на `RimalSuvUV`) у `uv_print`, `tablets`, `plaque`, `badge`, `uv_badge`, `shild`, `acrylic_prizes` — это возврат к ценам JS. Затронуты принятые копии 26 и 69 из `todo/forms-batch-switch.md`: после деплоя они ближе к боевым JS-формам, не дальше.
- Формы: нет.

## Режим

прод

## Журнал передач

Строка на сессию: `<дата> — <роль>, <модель> — <итог> — дальше <роль>`. Блокер — по формату
[docs/agents/workflow.md](../docs/agents/workflow.md). Замечания ревью — ниже, в «Ревью N».

- 2026-11-07 — Analyst, Opus 5.5 — задача-предпосылка для `form-acrylic-prizes` (блокер mode 0) + `timePrepareAround` круговой печати по решению человека — дальше Implementer
- 2026-11-08 — Implementer, Opus 5.5 — подготовка УФ как в JS (mode 0 / timePrepareAround); эталоны раннера; callers зелёные; `dev.py check` зелёный; деплой не делал — дальше Reviewer (Grok 4.7)
- 2026-11-08 — Reviewer, Grok 4.7 — принято — дальше человек: коммит и слияние
- 2026-11-08 — человек — слито в main — дальше Site ops

## Ревью 1

принято

- Diff против `main`: код и тесты только в файлах из «Файлы» (`uv_print.py`, `equipment/base.py`, `equipment/loader.py`, `test_uv_print.py`, `docs/js-runner-cases.md`). Ещё `todo/uv-print-prepare.md` (статус, журнал, отчёт) и `docs/dashboard.md` (статус `ревью`). Эталоны `tablets`, `plaque`, `badge`, `uv_badge`, `shild`, `acrylic_prizes` и `calc_service/data/` не менялись (`git diff main --stat` по ним пустой).
- Формулы: plain `time_prepare * mode.value`, круговая `time_prepare_around * mode.value` — как `calcUVPrint.js` строки 96 и 101 (`timePrepare` / `timePrepareAround` × `modeProduction`). `max(1, …)` и дефолты `or 0.2` / `0.05` сняты. Объёмы в строках 94–95 и 97–100 не трогались.
- Раннер: plain mode 0 `684/1095`, mode 1 `1048/1677`, around mode 1 `10894/17431`.
- Загрузчик: `0.5 0.05`.
- `pytest test_uv_print.py`: 10 passed. `git stash` только `uv_print.py`: оба новых теста FAIL (`1048` vs `684`, `10347` vs `10894`); stash возвращён.
- Callers: 61 passed.
- Деплой и боевой POST не проверялись: критерий Site ops, в diff его нет.

## Найдено вне scope

## Результат

- Ветка, PR или коммит: `task/uv-print-prepare`, слито в `main`
- Период: 2026-11-08
- Часы человека:
- Работа агентов: Implementer, одна сессия
- Было / стало: plain mode 0 готовил как mode 1 (`max(1, …)`); круговая брала `time_prepare` 0.2 вместо `timePrepareAround` 0.5. Стало: `time_prepare * mode` / `time_prepare_around * mode`.
- Сделано:
  - `EquipmentSpec.time_prepare_around` + загрузка `timePrepareAround`
  - `uv_print.py`: plain/around без `max(1, …)` и без локальных дефолтов `or 0.2`/`0.05`
  - два эталона в `test_uv_print.py` (JS, 08.11.2026; res=2, color=4+1 — как вызов из acrylic_prizes)
  - команды раннера в `docs/js-runner-cases.md`
- Чем проверено:
  - раннер: plain mode0 `684/1095`, mode1 `1048/1677`; around mode1 `10894/17431`
  - загрузчик: `0.5 0.05`
  - `pytest test_uv_print.py` — 10 passed; на `git stash` `uv_print.py` оба новых — FAIL (`1048` vs `684`, `10347` vs `10894`)
  - callers (tablets/plaque/badge/uv_badge/shild/acrylic_prizes) — 61 passed
  - `python scripts/dev.py check` — 513 passed + 2 skipped (calc), 81 passed (bot), exit 0
  - локально дефолт формы 78: JS и Python `cost/price` = `5599.45/8977.92`
- Не сделано и почему: деплой API и проверка боевого POST — Site ops после merge
- Требуется решение: деплой API — Site ops

Тело для Site ops (дефолт формы 78, совпадает с раннером `8977.92`):

```json
{"quantity":100,"layers":[{"materialID":"AcrylTrans3","size":[20,20],"isTop":true,"options":{"isCutLaser":{"sizeItem":0,"density":0,"difficulty":1.3,"lenCut":0},"isUVPrint":{"size":[20,20]}},{"materialID":"AcrylTrans3","size":[20,20],"isTop":false,"options":{"isCutLaser":{"sizeItem":0,"density":0,"difficulty":1.3,"lenCut":0},"isUVPrint":{"size":[20,20]}}}],"mode":1}
```

## Self-review

1. Diff только scope (+ `todo/uv-print-prepare.md`, `docs/dashboard.md` от статуса).
2. Цены/наценки не хардкод; `timePrepareAround` из JSON.
3. Контракт ответа УФ не менялся; `code` материалов не трогали.
4. Новые тесты падали на старом `uv_print.py` (показано stash).
5. Комментарии по-русски.
6. Доки: `js-runner-cases.md` обновлён; деплой не делался.
7. Прод: не выкатывал.
