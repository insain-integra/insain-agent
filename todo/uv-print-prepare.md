# uv-print-prepare

Статус: черновик
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

- [ ] Раннер `calcUVPrint` на обоих эталонах печатает `cost` и `price`; на 100 шт. 20×20 `plain` mode 0 — `price` ≈ 1095, mode 1 — ≈ 1677. Команды — из `docs/js-runner-cases.md`.

```powershell
node scripts/run_js_calc.mjs calcUVPrint --data current --args '<args из docs/js-runner-cases.md>'
```

- [ ] Загрузчик видит поле. Stdout: `0.5 0.05`.

```powershell
$OutputEncoding = New-Object System.Text.UTF8Encoding $false
@'
import sys
sys.path.insert(0, "calc_service")
from equipment import printer
print(printer.get("RimalSuvUV").time_prepare_around, printer.get("PrintUV").time_prepare_around)
'@ | python -
```

- [ ] Новые тесты УФ. Stdout: `passed`, `failed` нет. На `git stash` правки `uv_print.py` оба новых теста падают (проверка «тест падал бы без правки»).

```powershell
python -m pytest calc_service/tests/test_calculators/test_uv_print.py -q
```

- [ ] Вызывающие калькуляторы не сдвинулись. Stdout: `passed`, `failed` нет.

```powershell
python -m pytest calc_service/tests/test_calculators/test_tablets.py calc_service/tests/test_calculators/test_plaque.py calc_service/tests/test_calculators/test_badge.py calc_service/tests/test_calculators/test_uv_badge.py calc_service/tests/test_calculators/test_shild.py calc_service/tests/test_calculators/test_acrylic_prizes.py -q
```

- [ ] После деплоя (Site ops): дефолт формы 78 на боевом API равен JS. Тело — дефолт формы из блокера `form-acrylic-prizes` (100 шт., 2× AcrylTrans3 20×20, рез лазером и УФ на обоих слоях, mode 1); Implementer сверяет тело с раннером `calcAcrilycPrizes` и вписывает в отчёт. `price` = цене раннера (≈ 8977.92), разница ≤ 0.02 и `rel ≤ 0.001`; до правки было 9559.92.

```powershell
$api = Invoke-RestMethod -Method Post -Uri https://insain.ru/api/v1/calc/acrylic_prizes -ContentType 'application/json' -Body '<тело дефолта формы 78>'
$api | Select-Object price
```

## Проверки

- [ ] `python scripts/dev.py check` — код выхода 0
- [ ] Self-review — чеклист «Перед сдачей» в [AGENTS.md](../AGENTS.md)
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

## Найдено вне scope

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
