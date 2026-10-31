# heat-press-mug-vs-js

Статус: черновик
Сложность: высокая
Implementer: Opus 5.5
Reviewer: Grok 4.7
Почему: эталоны снимаются из JS, от `heat_press` зависит сублимация плакеток; возможен конфликт логики и прайса.

## Цель

`heat_press` и `mug` считают как `calcHeatPress` и `calcMug` на тех же кейсах, что в их тестах. Эталоны, снятые не с JS, пересняты раннером и помечены. Эпик `todo/EPIC-calc-port-structure.md`, шаг 4, после `todo/print-sheet-routing.md`.

## Контекст и ссылки

- `js_legacy/calc/calcHeatPress.js` — `calcHeatPress(n, size, transferID, itemID, options, modeProduction)`, вызывает `calcPrintSheet`, `calcPrintRoll`, `calcCutPlotter`, `calcCutSaber`, `calcSilkPrint`, `calcSticker`, `calcLayoutOnSheet`.
- `js_legacy/calc/calcMug.js` — `calcMug(n, mugID, options, modeProduction)`, опции `isDifferent`, `isPacking`, вызывает `calcHeatPress`.
- `calc_service/calculators/heat_press.py`, `calc_service/calculators/mug.py`. В обоих свой `_load_heatpress_raw` — дубль; в `mug.py` своя копия расчёта термопресса вместо вызова порта `heat_press` — проверить по `python scripts/js_port_gaps.py calcMug`.
- `scripts/run_js_calc.mjs` — `calcHeatPress.js` грузится, `calcMug.js` нет; общий вызов `--args` из `todo/print-inkjet-port.md`.
- `calc_service/tests/test_calculators/test_heat_press.py` (6 тестов), `test_mug.py` (7 тестов). Эталон без пометки `JS, ДД.ММ.ГГГГ` считается снятым не с JS. Тесты с `xfail` из `todo/print-sheet-routing.md`.
- Остальное не открывать.

## Scope

1. Раннер: добавить `js_legacy/calc/calcMug.js` в список скриптов (и прайс `mug`, если он нужен `--data current`). Файлы `js_legacy/` не меняются.
2. Для каждого кейса в `test_heat_press.py` и `test_mug.py` снять JS тем же входом (`--data current`); тираж 1 и ≥ 2 есть у каждого калькулятора, иначе добавить.
3. Совпало в пределах 0.1% — пометить эталон `# JS, ДД.ММ.ГГГГ`. Разошлось — найти ошибку переноса и исправить код; `mug` вызывает порт `heat_press`, а не копию; приватные функции чужого модуля не импортируются. Эталон, снятый не с JS, заменить числом JS с пометкой.
4. Снять все `xfail` с `reason` про `heat-press-mug-vs-js`.
5. Пропуски `python scripts/js_port_gaps.py calcHeatPress` и `calcMug`, которые не переносятся, — список «не перенесено» в docstring модуля и строки в `scripts/js_port_gaps_allowed.txt`.

## Не-scope

- `print_sheet`, `print_inkjet` — если расхождение там, стоп и строка в отчёт.
- `plaque.py`, `tablets.py`.
- `calc_service/data/`: расхождение из-за цены (старый прайс JS против текущего) отличать от логики; цену не править, строка в отчёт.
- `wp-plugin/`, формы, прод.

## Критерии приёмки

- [ ] `python -m pytest calc_service/tests/test_calculators/test_heat_press.py calc_service/tests/test_calculators/test_mug.py -q` — `passed`, не меньше 13 тестов, без `failed` и `xfailed`.
- [ ] `rg -n "xfail" calc_service/tests/test_calculators` — пустой вывод, код 1.
- [ ] Все эталоны с пометкой. Stdout `ok`:

```powershell
@'
import re
from pathlib import Path
for f in ["test_heat_press.py", "test_mug.py"]:
    t = Path("calc_service/tests/test_calculators", f).read_text(encoding="utf-8")
    refs = len(re.findall(r"approx\(", t))
    marks = len(re.findall(r"JS, \d\d\.\d\d\.2026", t))
    assert refs and marks >= 2, (f, refs, marks)
print("ok")
'@ | python -
```

- [ ] Раннер считает кружку. Stdout — JSON с полями `cost` и `price` (вход — первый эталон `test_mug.py`):

```powershell
@'
import json, subprocess
args = ["<вход первого эталона test_mug.py: n, mugID, {опции}, mode>"]
r = subprocess.run(["node", "scripts/run_js_calc.mjs", "calcMug", "--data", "current", "--args", json.dumps(args)], capture_output=True, text=True, encoding="utf-8")
print(r.stdout or r.stderr)
'@ | python -
```

- [ ] `rg -n "def _load_heatpress_raw" calc_service/calculators` — одна строка, в `heat_press.py`; `rg -n "from calculators\.\w+ import .*\b_[a-z]" calc_service/calculators` — пустой вывод.
- [ ] `python scripts/js_port_gaps.py --check` — `ok`.

## Проверки

- [ ] `make check` (или `python scripts/dev.py check`) — зелёный вывод
- [ ] Self-review — чеклист «Перед сдачей» в [AGENTS.md](../AGENTS.md)

## Риски

- Прод: нет деплоя в задаче. После следующего деплоя API изменятся `heat_press` и `mug`; на сайте через API они не вызываются.
- Цены: нет, JSON не меняются.
- Формы: нет.

## Режим

обычный

## Результат

- Ветка, PR или коммит:
- Сделано:
- Чем проверено:
- Не сделано и почему:
- Требуется решение:
