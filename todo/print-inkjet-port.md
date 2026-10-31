# print-inkjet-port

Статус: черновик
Сложность: высокая
Implementer: Opus 5.5
Reviewer: Grok 4.7
Почему: общий калькулятор печати, от него зависят термоперенос, кружки и сублимация плакеток; правка раннера эталонов и строки skill.

## Цель

`PrintInkjetCalculator` (`calc_service/calculators/print_inkjet.py`) считает как `calcPrintInkJet` (`js_legacy/calc/calcPrintInkJet.js`). Раннер `scripts/run_js_calc.mjs` вызывает `calcPrintInkJet`, эталоны в тестах сняты им. Эпик `todo/EPIC-calc-port-structure.md`, шаг 2, после `todo/js-port-gaps.md`.

## Контекст и ссылки

- Старый черновик: `git show task/plaque-sublimation:todo/print-inkjet-js.md` — таблица замеров от 31.10.2026. Брать первые две строки; маршрутизация `print_sheet` — отдельная задача.
- `js_legacy/calc/calcPrintInkJet.js` — эталонная логика: `calcPrintInkJet(numSheet, sizeSheet, quality, color, materialID, printerID, modeProduction)`, вызывает `calcLayoutOnSheet`, `calcWeight`.
- `calc_service/calculators/print_inkjet.py` — текущий порт, расходится с JS. Из других калькуляторов его никто не вызывает (только реестр `calculators/__init__.py`).
- `scripts/run_js_calc.mjs` — `calcPrintInkJet.js` уже грузится, но вызов принимает только `calcPlaque` (строка `if (name !== 'calcPlaque')`) с фиксированными полями.
- `calc_service/tests/test_calculators/test_print_inkjet.py` — 15 тестов на `main`, эталоны без пометки `JS`.
- `.cursor/skills/ezfc-form-to-api/SKILL.md`, шаг 2 раздела «Сверка до перевода» — «сейчас только `calcPlaque`».
- `python scripts/js_port_gaps.py calcPrintInkJet` — пропуски порта до и после.
- Остальное не открывать.

Замеры JS (`--data current`, 31.10.2026, из старого черновика):

| Вызов | cost | price | time | timeReady |
|---|---|---|---|---|
| `calcPrintInkJet(1, [297,420], 1, '4+0', 'PaperSublimation128', 'EPSONWF7610', 1)` | 433.5 | 695.76 | 0.31 | 8.31 |
| то же, 6 листов | 950 | 1528.4 | 0.8 | 8.8 |

## Scope

1. Раннер: общий вызов любой загруженной функции `insaincalc.calcX` позиционными аргументами — `--args '<JSON-массив>'`. Объект верхнего уровня в массиве становится `Map` (опции JS); вложенные значения остаются объектами. Вывод — те же поля, что у `calcPlaque` (`cost`, `price`, `unit_price` = `price / args[0]`, `time_hours`, `time_ready`, `weight_kg`). Вызов `calcPlaque` с `--params` не меняется. Файлы `js_legacy/` не меняются.
2. `print_inkjet.py` — расчёт как в `calcPrintInkJet`, вся функция. Чего не перенесено — список «не перенесено» в docstring и строки в `scripts/js_port_gaps_allowed.txt`.
3. Тесты `test_print_inkjet.py`: эталоны из JS на тираже 1 и на тираже ≥ 2 (обе строки таблицы и хотя бы один кейс с `quality` 0 или `DTFTransfer`), допуск 0.1% (`pytest.approx(rel=1e-3)`), пометка `# JS, ДД.ММ.ГГГГ`. Старые эталоны, которые разошлись с JS, переснять раннером с пометкой; не удалять.
4. Строка в skill `ezfc-form-to-api`, шаг 2: раннер вызывает `calcPlaque` по `--params`, остальные функции — по `--args`.

## Не-scope

- `print_sheet.py` и выбор расчёта по принтеру — `todo/print-sheet-routing.md`.
- `heat_press`, `mug`, `plaque`, `tablets` и их тесты.
- `calc_service/data/` — расхождение в логике, не в прайсе. Расхождение из-за цены — строка в отчёт, не правка JSON.
- `wp-plugin/`, формы, прод.

## Критерии приёмки

- [ ] Раннер на двух строках таблицы. Stdout `ok`:

```powershell
@'
import json, subprocess
def js(args):
    r = subprocess.run(["node", "scripts/run_js_calc.mjs", "calcPrintInkJet", "--data", "current", "--args", json.dumps(args)], capture_output=True, text=True, encoding="utf-8")
    assert r.returncode == 0, r.stderr
    return json.loads(r.stdout)
a = js([1, [297, 420], 1, "4+0", "PaperSublimation128", "EPSONWF7610", 1])
assert abs(a["cost"] - 433.5) < 0.01 and abs(a["price"] - 695.76) < 0.01, a
b = js([6, [297, 420], 1, "4+0", "PaperSublimation128", "EPSONWF7610", 1])
assert abs(b["cost"] - 950) < 0.01 and abs(b["price"] - 1528.4) < 0.01, b
print("ok")
'@ | python -
```

- [ ] Раннер плакеток не сломан. Stdout `6205.71`:

```powershell
@'
import json, subprocess
p = {"quantity": 2, "plaque_id": "Plaque2330", "material_id": "PVC3", "application": "isUVPrint", "mode": 1}
r = subprocess.run(["node", "scripts/run_js_calc.mjs", "calcPlaque", "--data", "current", "--params", json.dumps(p)], capture_output=True, text=True, encoding="utf-8")
print(json.loads(r.stdout)["price"])
'@ | python -
```
- [ ] `python -m pytest calc_service/tests/test_calculators/test_print_inkjet.py -q` — `passed`, не меньше 15 тестов, без `failed`.
- [ ] `rg -n "433\.5|695\.76|1528\.4" calc_service/tests/test_calculators/test_print_inkjet.py` — все три числа найдены.
- [ ] `rg -c "JS, \d\d\.\d\d\.2026" calc_service/tests/test_calculators/test_print_inkjet.py` — не меньше 3.
- [ ] `python scripts/js_port_gaps.py --check` — `ok`; в выводе `python scripts/js_port_gaps.py calcPrintInkJet` строка `нет в Python` пустая или каждый пропуск есть в docstring `print_inkjet.py` после слов «не перенесено».

## Проверки

- [ ] `make check` (или `python scripts/dev.py check`) — зелёный вывод
- [ ] Self-review — чеклист «Перед сдачей» в [AGENTS.md](../AGENTS.md)

## Риски

- Прод: нет. После следующего деплоя API изменится ответ `print_inkjet`; на сайте через API он не вызывается (реестр — `docs/site/forms.md`).
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
