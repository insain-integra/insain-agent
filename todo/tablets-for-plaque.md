# tablets-for-plaque

Статус: ревью
Сложность: высокая
Implementer: Opus 5.5
Reviewer: Grok 4.7
Почему: `calcTablets` вызывают плакетки (форма 69, пилот) и формы 36, 48, 51, 68, 76; эталоны снимаются из JS на двух уровнях.

## Цель

`TabletsCalculator` (`calc_service/calculators/tablets.py`) считает ветки `calcTablets`, нужные плакеткам, с теми же аргументами, что передаёт `calcPlaque`: `isCutManualMetal`, `isSublimation`, лазер (`isCutLaser` с `isGrave`/`isGraveFill`) и УФ (`isUVPrint`). Остальные ветки — явный список «не перенесено». Эталоны сняты на уровне `calcTablets`. Эпик `todo/EPIC-calc-port-structure.md`, шаг 5, после `todo/heat-press-mug-vs-js.md`.

## Контекст и ссылки

- `js_legacy/calc/calcTablets.js`:
  - `calcTablets(n, size, materialID, options, modeProduction)` — строки 2–300; `isCutManualMetal` — строка 41 (значение — id резака, раскладка на A4/A3), `isSublimation` — строки 75–89 (вызов `calcHeatPress`).
  - `calcPlaque` — строки 582–661; набор опций по `applicationID` — строки 620–639, вызов `calcTablets` — строка 640.
  - Аргументы из `calcPlaque`: `isUVPrint` — `isCutLaser {sizeItem, density 0, difficulty 1, lenCut 0}` и `isUVPrint {printerID 'RimalSuvUV', resolution 2, surface 'isPlain', color '4+1'}`; `isGrave` — `isCutLaser` (то же), `isGrave` 2, `isGraveFill` = `sizePlate`; `isSublimation` — `isCutManualMetal 'AccusheadPro12'`, `isSublimation true`.
- `calc_service/calculators/tablets.py` — сейчас карманы и рамка; веток плакеток нет. Порты для вызова: `LaserCalculator`, `UVPrintCalculator`, `HeatPressCalculator`, `common/process_tools.py`, `common/layout.py`.
- `python scripts/js_port_gaps.py calcTablets` — список пропусков до и после.
- `scripts/run_js_calc.mjs` — `calcTablets.js` грузится; общий вызов `--args` (опции — объект → `Map`).
- `calc_service/tests/test_calculators/test_tablets.py` — 6 тестов на `main`.
- `calc_service/data/materials/plaque.json` — `sizePlate` плакетки `Plaque2330` для входа эталонов.
- Остальное не открывать. `plaque.py` не открывать: он меняется в следующей задаче.

## Scope

1. `tablets.py`: ветки `isCutManualMetal`, `isSublimation`, `isCutLaser` (с передачей `isGrave`/`isGraveFill` в лазер, как в JS) и `isUVPrint`. Каждая — вызов Python-порта той функции, что вызывает JS (`calcLaser` → `LaserCalculator`, `calcUVPrint` → `UVPrintCalculator`, `calcHeatPress` → `HeatPressCalculator`, `calcCutSaber` и раскладка → `common/`). Приватные функции чужих модулей не импортируются.
2. Параметры принимают те же значения, что JS (`printerID`, `resolution`, `surface`, `color`, `sizeItem`, `density`, `difficulty`, `lenCut`, id резака); имена — snake_case, видны в `get_param_schema()`.
3. Остальные опции `calcTablets` (`isAdhesiveLayer`, `isBackgroundFilm`, `isCutManual`, `isCutMilling`, `isEVAFoam`, `isFilm`, `isHanger`, `isPrint`, `isShaft` и прочие, что покажет `js_port_gaps`) — список «не перенесено» в docstring `tablets.py` и строки в `scripts/js_port_gaps_allowed.txt`. Перенесённые ветки из файла пропусков удаляются, `MAX_ALLOWED` в тесте уменьшается.
4. Эталоны в `test_tablets.py` на уровне `calcTablets`: для каждой из трёх веток плакеток (УФ, гравировка, сублимация) тираж 1 и тираж ≥ 2, режим 1, `size` = `sizePlate` `Plaque2330`, материалы `PVC3` или `AcrylWhite3` для УФ и гравировки, `AluminiumSU055` для сублимации. Допуск 0.1%, пометка `# JS, ДД.ММ.ГГГГ`.

## Не-scope

- `plaque.py` и `test_plaque.py` — `todo/plaque-thin-wrapper.md`.
- Ветки `calcTablets` вне списка п. 1; формы 36, 48, 51, 68, 76 (они на старом JS).
- `laser`, `uv_print`, `heat_press` — если расхождение в них, стоп и строка в отчёт.
- `calc_service/data/`, `wp-plugin/`, формы, прод.

## Критерии приёмки

- [ ] `python -m pytest calc_service/tests/test_calculators/test_tablets.py -q` — `passed`, не меньше 12 тестов, без `failed`.
- [ ] `rg -c "JS, \d\d\.\d\d\.2026" calc_service/tests/test_calculators/test_tablets.py` — не меньше 6.
- [ ] Ветки плакеток перенесены. Stdout `ok`:

```powershell
@'
import subprocess, sys
out = subprocess.run([sys.executable, "scripts/js_port_gaps.py", "calcTablets"], capture_output=True, text=True, encoding="utf-8").stdout
block = out.split("calcTablets ->", 1)[1]
gaps = next(l for l in block.splitlines() if l.strip().startswith("нет в Python"))
for opt in ["isCutManualMetal", "isSublimation", "isCutLaser", "isUVPrint"]:
    assert opt not in gaps, opt
print("ok")
'@ | python -
```

- [ ] Файл пропусков уменьшился. Stdout `ok`:

```powershell
@'
import subprocess
from pathlib import Path
old = subprocess.run(["git", "show", "main:scripts/js_port_gaps_allowed.txt"], capture_output=True, text=True, encoding="utf-8").stdout.splitlines()
new = Path("scripts/js_port_gaps_allowed.txt").read_text(encoding="utf-8").splitlines()
assert len(new) < len(old) and set(new) <= set(old), (len(old), len(new))
print("ok")
'@ | python -
```

- [ ] `python scripts/js_port_gaps.py --check` — `ok`.
- [ ] `rg -n "не перенесено" calc_service/calculators/tablets.py` — есть строка в docstring модуля.
- [ ] `rg -n "from calculators\.\w+ import .*\b_[a-z]" calc_service/calculators` — пустой вывод, код 1.

## Проверки

- [ ] `make check` (или `python scripts/dev.py check`) — зелёный вывод
- [ ] Self-review — чеклист «Перед сдачей» в [AGENTS.md](../AGENTS.md)

## Риски

- Прод: нет деплоя в задаче. API `tablets` на сайте не вызывается.
- Цены: нет, JSON не меняются. Расхождение с JS из-за цены — строка в отчёт.
- Формы: нет. Формы 36, 48, 51, 68, 76 остаются на старом JS.

## Режим

обычный

## Результат

- Ветка, PR или коммит: `task/tablets-for-plaque` @ `de81a1b` (push не делался)
- Сделано: ветки `is_cut_manual_metal`, `is_sublimation`, `is_cut_laser` (+ `is_grave`/`is_grave_fill`), `is_uv_print` в `tablets.py` через порты; 6 JS-эталонов (+ переснят старый); из `js_port_gaps_allowed.txt` удалены 4 строки, `MAX_ALLOWED` 76→72
- Чем проверено: после фикса Reviewer — `pytest test_tablets.py` 14 passed; `js_port_gaps.py --check` ok; `python scripts/dev.py check` — 488 passed / 2 skipped (calc) + 81 passed (bot)
- Не сделано и почему: `plaque.py` / остальные ветки calcTablets — вне scope
- Требуется решение: нет
- Публичный параметр `print_method` из tablets удалён (заменён опциями `is_cut_laser` / `is_uv_print` / `is_grave` / `is_sublimation`); `plaque.py` его ещё передаёт в ветке сублимации (`elif application != "noApplication"`). Цена сублимации в plaque изменилась (на main 2390.76, на ветке 1516.41 при quantity=2, Plaque2330, AluminiumSU055; обе не совпадают с JS). Чинится в `plaque-thin-wrapper`. До его мержа не деплоить API с main.

### Расхождения до правки (старый tablets vs JS calcTablets)

| Слагаемое | JS | Python (до) | Причина |
| --- | --- | --- | --- |
| Лазер `len_cut` / `size_item` | `lenCut=0`, `sizeItem=min(w,h)` | `(w+h)*2`, `size_item=w*h` | `print_method=laser` не брал аргументы calcPlaque |
| УФ vs лазер | УФ **поверх** лазерной резки | взаимоисключение через `print_method` | нет раздельных опций |
| `isCutManualMetal` | `calcCutSaber` + раскладка A4/A3 + материал | отсутствовало | не перенесено |
| `isSublimation` | `calcHeatPress(sublimation, metal)` | отсутствовало | не перенесено |
| `time_ready` | `time + max(component.timeReady)` | `max(component.time_ready)` | другая формула |
| Эталон 297×210 UV | не с JS | cost 2025 / price 3285 | снят с Python, не с calcTablets |

### js_port_gaps calcTablets

- **До:** `нет в Python: option isCutManual, option isCutManualMetal, option isCutMilling, option isSublimation, option isFilm, option isBackgroundFilm, option isShaft, option isAdhesiveLayer, option isEVAFoam, call calcCutRoller, call calcCutSaber, call calcMilling, call calcHeatPress, call calcPrintRoll, call calcManualRoll, call calcSticker, call calcPockets, call calcFrame`
- **После:** `нет в Python: option isCutManual, option isCutMilling, option isFilm, option isBackgroundFilm, option isShaft, option isAdhesiveLayer, option isEVAFoam, call calcCutRoller, call calcMilling, call calcPrintRoll, call calcManualRoll, call calcSticker, call calcPockets, call calcFrame`
