# print-sheet-routing

Статус: черновик
Сложность: высокая
Implementer: Opus 5.5
Reviewer: Grok 4.7
Почему: общий калькулятор печати, через него считают пазлы (форма 79 на API), термоперенос, кружки и сублимация плакеток; решение об округлении цены станет правилом.

## Цель

`PrintSheetCalculator` выбирает расчёт печати по принтеру, как `calcPrintSheet`: `EPSONWF7610` и `DTFTransfer` — вызов порта `print_inkjet`, `KMBizhubC220` — лазерная ветка, как сейчас. Качество по умолчанию как в JS. Материал печати в ответе несёт размер листа `size_mm`. Где округляется цена (API или `showResult`) — записано одной строкой. Пазлы не изменились. Эпик `todo/EPIC-calc-port-structure.md`, шаг 3, после `todo/print-inkjet-port.md`.

## Контекст и ссылки

- `js_legacy/calc/calcPrintSheet.js`: принтер — `options.get('printer')['printerID']`, по умолчанию `KMBizhubC220` (строки 25–29); выбор расчёта — строки 83–97: `EPSONWF7610` — `calcPrintInkJet` с `quality` из `options.get('printer')['quality']`, по умолчанию 1; `DTFTransfer` — `calcPrintInkJet` с `quality` 0; `KMBizhubC220` — `calcPrintLaser`. Материал в ответе JS — `[name, size, n]`.
- `calc_service/calculators/print_sheet.py`: `printer_code` (строка 435), печать «лазерная логика как в calcPrintLaser» для любого принтера (около строки 511), элемент материала без `size_mm` (около строки 673), цена округляется.
- Вызовы со струйным принтером: `heat_press.py` (`SUBLIMATION_PRINTER` `EPSONWF7610`, `DTF_PRINTER` `DTFTransfer`), `mug.py` (`printer_code` `EPSONWF7610`). `puzzle.py` вызывает `PrintSheetCalculator` без `printer_code` — лазерная ветка.
- Прецедент округления: коммит `663864d` — `plaque` отдаёт `price` в копейках, округление вывода делает `insaincalc.showResult` на сайте.
- `calc_service/tests/test_calculators/test_puzzle.py` — `EXPECTED_REF` (`price` 1171). `test_print_sheet.py` — 16 тестов на `main`.
- Старый черновик: `git show task/plaque-sublimation:todo/print-inkjet-js.md`, третья строка таблицы.
- Остальное не открывать.

Замер JS (`--data current`, 31.10.2026, из старого черновика): `calcPrintSheet(1, [420,297], '4+0', [0,0,0,0], 2, 'PaperSublimation128', {printer: {printerID: 'EPSONWF7610'}}, 1)` — cost 523.1, price 841.856, time 0.35, timeReady 8.66. Python на `main` — cost 360.908, price 583.

## Scope

1. `print_sheet.py`: выбор расчёта по `printer_code` как в `calcPrintSheet`; струйные принтеры — вызов `PrintInkjetCalculator` (порт), не пересчёт. Качество по умолчанию: 1 для `EPSONWF7610`, 0 для `DTFTransfer`; параметр качества в схеме, если его нет. Лазерная ветка не меняется, включая её округление.
2. Отдельным коммитом: элемент материала печати в ответе `print_sheet` получает `size_mm` — размер листа из каталога (`material.sizes[0]`), как `material.size` в JS.
3. Одна строка решения в `calc_service/AGENTS.md`, раздел «Контракт ответа»: где округляется `price`. По умолчанию, как в `663864d`: API отдаёт `price` в копейках без округления до рубля, округление вывода — `showResult`. Если решение меняет цену лазерной ветки или пазлов — стоп, вопрос человеку.
4. Тесты `test_print_sheet.py`: эталоны из JS для `EPSONWF7610` на тираже 1 и ≥ 2 и для `DTFTransfer`, допуск 0.1%, пометка `# JS, ДД.ММ.ГГГГ`; тест `size_mm`.
5. Тесты `heat_press` и `mug`, которые упали из-за смены маршрута, — `pytest.mark.xfail(strict=True, reason="переснять с JS в heat-press-mug-vs-js")`, эталоны не трогать. Снимаются в следующей задаче.

## Не-scope

- `heat_press.py`, `mug.py`, `plaque.py`, `tablets.py` — код не меняется.
- Ветки ламинации, нумерации, скругления, биговки `calcPrintSheet` — только если тесты их задевают.
- `calc_service/data/` — цены не меняются. Размер листа уже есть в каталоге (`size` у `PaperSublimation128` — `[297, 420]`); если у нужной бумаги размера нет — строка в отчёт.
- `wp-plugin/`, формы, прод.

## Критерии приёмки

- [ ] Раннер на замере. Stdout `ok`:

```powershell
@'
import json, subprocess
args = [1, [420, 297], "4+0", [0, 0, 0, 0], 2, "PaperSublimation128", {"printer": {"printerID": "EPSONWF7610"}}, 1]
r = subprocess.run(["node", "scripts/run_js_calc.mjs", "calcPrintSheet", "--data", "current", "--args", json.dumps(args)], capture_output=True, text=True, encoding="utf-8")
a = json.loads(r.stdout)
assert abs(a["cost"] - 523.1) < 0.01 and abs(a["price"] - 841.856) < 0.01, a
print("ok")
'@ | python -
```

- [ ] `python -m pytest calc_service/tests/test_calculators/test_print_sheet.py -q` — `passed`, не меньше 17 тестов, без `failed`.
- [ ] `rg -n "523\.1|841\.86?" calc_service/tests/test_calculators/test_print_sheet.py` — оба числа найдены; `rg -c "JS, \d\d\.\d\d\.2026" calc_service/tests/test_calculators/test_print_sheet.py` — не меньше 3.
- [ ] Пазлы не изменились: `git diff main --stat -- calc_service/tests/test_calculators/test_puzzle.py` — пустой вывод; `python -m pytest calc_service/tests/test_calculators/test_puzzle.py -q` — `6 passed`.
- [ ] Лазерная ветка не изменилась. Stdout `ok` (числа `main` снять до правки и вписать вместо `<…>`):

```powershell
@'
import sys
sys.path.insert(0, "calc_service")
from calculators.print_sheet import PrintSheetCalculator
r = PrintSheetCalculator().calculate({"quantity": 10, "width": 90, "height": 50, "material_id": "PaperSublimation128", "color": "4+0", "mode": 1})
assert (r["cost"], r["price"]) == (<cost main>, <price main>), (r["cost"], r["price"])
print("ok")
'@ | python -
```

- [ ] `rg -n "\"size_mm\"" calc_service/calculators/print_sheet.py` — одна строка в элементе `materials`.
- [ ] `rg -n "showResult|округл" calc_service/AGENTS.md` — одна строка решения в разделе «Контракт ответа».
- [ ] `rg -n "xfail" calc_service/tests/test_calculators` — только тесты `test_heat_press.py` и `test_mug.py` с `reason` про `heat-press-mug-vs-js`, или пустой вывод.

## Проверки

- [ ] `make check` (или `python scripts/dev.py check`) — зелёный вывод
- [ ] Self-review — чеклист «Перед сдачей» в [AGENTS.md](../AGENTS.md)

## Риски

- Прод: нет деплоя в задаче. После следующего деплоя API изменятся `print_sheet` со струйным принтером, `heat_press`, `mug`. На сайте через API из них никто не считает; форма 79 (пазлы) — лазерная ветка, должна остаться прежней.
- Цены: нет, JSON не меняются.
- Формы: нет. Форма 79 косвенно — через `puzzle` → `print_sheet`; защищена тестом пазлов.

## Режим

обычный

## Результат

- Ветка, PR или коммит:
- Сделано:
- Чем проверено:
- Не сделано и почему:
- Требуется решение:
