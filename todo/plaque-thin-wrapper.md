# plaque-thin-wrapper

Статус: черновик
Сложность: высокая
Implementer: Opus 5.5
Reviewer: Grok 4.7
Почему: калькулятор пилотной формы 69 на проде; эталоны берутся из старого коммита другой ветки и переснимаются с JS.

## Цель

`plaque.py` повторяет `calcPlaque`: основа плакетки плюс вызов `TabletsCalculator` с опциями нанесения, как в JS. Копий логики пластины в `plaque.py` нет. Эталоны плакеток (УФ, гравировка, сублимация) совпадают с JS. Эпик `todo/EPIC-calc-port-structure.md`, шаг 6, после `todo/tablets-for-plaque.md`; затем `todo/pilot-plaque-form.md`.

## Контекст и ссылки

- `js_legacy/calc/calcTablets.js`, `calcPlaque` — строки 582–661: стоимость основы (`plaque.cost * n`, наценка `marginMaterial`), опции по `applicationID` (строки 620–639), вызов `calcTablets(n, plaque.sizePlate, materialID, optionsApplication, modeProduction = 1)` (строка 640), `price = (plate + plaque + set) * (1 + marginPlaque)`, вес `ceil(…*100)/100`, `timeReady = time + max(…)`.
- `calc_service/calculators/plaque.py` на `main` — 465 строк, своя пластина `_calc_plate` (строка 80), импорты `LaserCalculator`, `UVPrintCalculator`.
- `git show 314893f:calc_service/calculators/plaque.py` — ветка `task/plaque-sublimation`, не сливается: там ещё `_calc_plate_sublimation`, `_calc_sublimation_metal` и импорт приватного `_load_heatpress_raw` из `heat_press`. Код не переносить.
- `git show 314893f -- calc_service/tests/test_calculators/test_plaque.py` — тесты поведения: без пластины только УФ-печать (`isGrave`, `isSublimation` с пустым `material_id` — ошибка), УФ на основе без пластины, сублимация только на алюминии. Числовых эталонов сублимации там нет.
- Замер JS из `git show task/plaque-sublimation:todo/print-inkjet-js.md`: 2 шт., `Plaque2330`, `AluminiumSU055`, `isSublimation`, mode 1 — `price` 4018.24.
- `calc_service/tests/test_calculators/test_plaque.py` на `main` — 19 тестов, `EXPECTED_REF` (`price` 6205.71) и 8 кейсов `JS, 29.10.2026`.
- Остальное не открывать.

## Scope

1. `plaque.py`: основа плакетки + опции нанесения как в строках 620–639 JS + вызов `TabletsCalculator` + итог как в JS. Режим пластины — как в строке 640 JS (`modeProduction = 1`: пластина всегда в стандартном режиме), иначе разойдутся эталоны `mode` 2.
2. Удалить `_calc_plate` и импорты калькуляторов, которые теперь вызывает `tablets`. В `plaque.py` нет `_calc_plate`, `_calc_plate_sublimation`, `_calc_sublimation_metal`, `_load_heatpress_raw`.
3. Сублимация: эталоны из JS раннером — 2 шт. (ожидается `price` 4018.24) и 1 шт., `Plaque2330`, `AluminiumSU055`, mode 1; пометка `# JS, ДД.ММ.ГГГГ`, допуск 0.1%.
4. Тесты поведения из `314893f` перенести, если JS ведёт себя так же (проверить раннером: пустой `material_id` с `isUVPrint`, `isGrave`, `isSublimation`; `isSublimation` с `AcrylWhite3`). Разошлось с JS — тест не переносить, строка в отчёт.
5. Тесты плакеток не ослаблять: `EXPECTED_REF` и 8 кейсов `JS, 29.10.2026` без изменений; число тестов не меньше, чем на `main`.

## Не-scope

- `tablets.py` — если расхождение в ветке `tablets`, стоп и строка в отчёт.
- Форма 69, `wp-plugin/forms/plaque.js`, деплой API и плагина — `todo/pilot-plaque-form.md`.
- Слияние или удаление ветки `task/plaque-sublimation`.
- `calc_service/data/`.

## Критерии приёмки

- [ ] `python -m pytest calc_service/tests/test_calculators/test_plaque.py -q` — `passed`, не меньше 22 тестов (19 с `main` + 2 эталона сублимации + хотя бы один тест поведения), без `failed`.
- [ ] `rg -n "_calc_plate|_calc_sublimation_metal|_load_heatpress_raw|LaserCalculator|UVPrintCalculator|HeatPressCalculator|PrintSheetCalculator" calc_service/calculators/plaque.py` — пустой вывод, код 1.
- [ ] `rg -n "TabletsCalculator\(\)" calc_service/calculators/plaque.py` — хотя бы одна строка.
- [ ] Старые эталоны не тронуты: `git diff main -- calc_service/tests/test_calculators/test_plaque.py | rg "^-.*(JS, 29\.10\.2026|6205\.71|EXPECTED_REF|JS_CASES)"` — пустой вывод, код 1.
- [ ] Эталоны сублимации с пометкой. Stdout `ok`:

```powershell
@'
import re, subprocess
from pathlib import Path
new = Path("calc_service/tests/test_calculators/test_plaque.py").read_text(encoding="utf-8")
old = subprocess.run(["git", "show", "main:calc_service/tests/test_calculators/test_plaque.py"], capture_output=True, text=True, encoding="utf-8").stdout
mark = r"JS, \d\d\.\d\d\.2026"
assert "4018.24" in new
assert len(re.findall(mark, new)) >= len(re.findall(mark, old)) + 2
assert new.count("AluminiumSU055") >= 2
print("ok")
'@ | python -
```
- [ ] Раннер на эталоне сублимации. Stdout `ok`:

```powershell
@'
import json, subprocess
p = {"quantity": 2, "plaque_id": "Plaque2330", "material_id": "AluminiumSU055", "application": "isSublimation", "mode": 1}
r = subprocess.run(["node", "scripts/run_js_calc.mjs", "calcPlaque", "--data", "current", "--params", json.dumps(p)], capture_output=True, text=True, encoding="utf-8")
assert abs(json.loads(r.stdout)["price"] - 4018.24) < 0.01, r.stdout or r.stderr
print("ok")
'@ | python -
```

- [ ] `python scripts/js_port_gaps.py calcPlaque` — в блоке `calcPlaque` строка `нет в Python` пустая; `python scripts/js_port_gaps.py --check` — `ok`.
- [ ] `rg -n "from calculators\.\w+ import .*\b_[a-z]" calc_service/calculators` — пустой вывод, код 1.

## Проверки

- [ ] `make check` (или `python scripts/dev.py check`) — зелёный вывод
- [ ] Self-review — чеклист «Перед сдачей» в [AGENTS.md](../AGENTS.md)

## Риски

- Прод: нет деплоя в задаче. После деплоя API (в пилоте) изменится ответ `plaque`; ворота пилота (`price` 6205.71) прогнать заново.
- Цены: нет, JSON не меняются. Если 4018.24 не сходится из-за цены в текущем прайсе — стоп, строка в отчёт.
- Формы: нет. Форма 69 переводится в пилоте, со всеми нанесениями, включая сублимацию.

## Режим

обычный

## Результат

- Ветка, PR или коммит:
- Сделано:
- Чем проверено:
- Не сделано и почему:
- Требуется решение:
