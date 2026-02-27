# Форматы данных JSON

Все JSON содержат комментарии (`// ...`).
Для чтения используется библиотека json5.

## Материалы: паттерн «группа + Default + варианты»

Каждый JSON-файл материалов содержит группы.
Группа — это семейство вариантов с общими параметрами.

```json
{
  "PVCUnextStrong": {
    "Default": {
      "size": [[3050, 2050], [2050, 1525]],
      "minSize": [200, 200],
      "density": 0.55,
      "unitDensity": "гсм3"
    },
    "PVC3": {
      "name": "ПВХ Unext Strong 3 мм",
      "cost": 750,
      "thickness": 3
    },
    "PVC5": {
      "name": "ПВХ Unext Strong 5 мм",
      "cost": 1182,
      "thickness": 5
    }
  }
}
```

Как читает loader.py:

Для каждого варианта (PVC3, PVC5) берёт его поля
Недостающие поля берёт из Default (size, minSize, density...)
Default не хранится как отдельный объект
Результат: MaterialSpec с полным набором полей

### Размеры: три формата

```
Один лист:
  "size": [3000, 2000]
  → sizes = [[3000, 2000]]

Несколько листов (калькулятор выбирает оптимальный):
  "size": [[3050, 2050], [2050, 1525]]
  → sizes = [[3050, 2050], [2050, 1525]]

Рулон (height = 0):
  "size": [620, 0]
  → sizes = [[620, 0]], is_roll = True
```

### Цена: два формата

```
Фиксированная:
  "cost": 750
  → cost = 750.0

Градированная (зависит от объёма):
  "cost": [[10, 800], [50, 700], [100, 600]]
  → cost_tiers = [(10, 800.0), (50, 700.0), (100, 600.0)]
```

## Оборудование: справочные таблицы

Скорость и брак заданы массивами [порог, значение]:

```JSON
{
  "cutPerHour": [[0.5, 200], [1.0, 120], [2.0, 60]],
  "defects": [[10, 0.1], [100, 0.05], [500, 0.02]]
}
```

В Python это LookupTable:

```
table.find(0.3)  → 200  (первый порог ≥ 0.3 это 0.5 → значение 200)
table.find(1.5)  → 60   (первый порог ≥ 1.5 это 2.0 → значение 60)
table.find(5.0)  → 60   (нет порога ≥ 5.0 → последнее значение 60)
```

### Цены в долларах и евро

```JSON
"cost": "$11600"    →  parse_currency()  → 11600 × 95 = 1 102 000 ₽
"cost": "€5000"     →  parse_currency()  → 5000 × 100 = 500 000 ₽
```

### Вычисляемые поля (формулы)

```JSON
"costCut": "^.costLaserTube/^.lifeLaserTube+^.costPower*^.powerPerHour"
```

В Python — не парсятся, а реализуются как @property:

```Python
@property
def consumables_per_hour(self):
    return self.laser_tube_cost / self.laser_tube_life_hours + ...
```

## Маппинг файлов JS → Python

### Материалы (копируются без изменений)

```
material/roll.json       → data/materials/roll.json
material/hardsheet.json  → data/materials/hardsheet.json
material/sheet.json      → data/materials/sheet.json
material/laminat.json    → data/materials/laminat.json
material/profile.json    → data/materials/profile.json
material/presswall.json  → data/materials/presswall.json
material/calendar.json   → data/materials/calendar.json
material/magnet.json     → data/materials/magnet.json
material/keychain.json   → data/materials/keychain.json
material/mug.json        → data/materials/mug.json
material/misc.json       → data/materials/misc.json
```

### Оборудование (копируются без изменений)

```
equipment/printer.json   → data/equipment/printer.json
equipment/plotter.json   → data/equipment/plotter.json
equipment/cutter.json    → data/equipment/cutter.json
equipment/laminator.json → data/equipment/laminator.json
equipment/laser.json     → data/equipment/laser.json
equipment/milling.json   → data/equipment/milling.json
equipment/heatpress.json → data/equipment/heatpress.json
equipment/cards.json     → data/equipment/cards.json
equipment/metalpins.json → data/equipment/metalpins.json
equipment/design.json    → data/equipment/design.json
equipment/tools.json     → data/equipment/tools.json
```

### Общие файлы

```
calc/common.json    → data/common.json       (копия без изменений)
calc/common.js      → common/helpers.py      (переписано на Python)
calc/calcLayout.js  → common/layout.py       (переписано на Python)
```

### Калькуляторы

```
calcLaser.js         → calculators/laser.py
calcPrintWide.js     → calculators/print_wide.py
calcPrintRoll.js     → calculators/print_roll.py
calcUVPrint.js       → calculators/print_uv.py
calcPrintOffset.js   → calculators/print_offset.py
calcPrintSheet.js    → calculators/print_sheet.py
calcPrintInkJet.js   → calculators/print_inkjet.py
calcPrintLaser.js    → calculators/print_laser.py
calcCanvas.js        → calculators/canvas.py
calcCutPlotter.js    → calculators/cut_plotter.py
calcCutGuillotine.js → calculators/cut_guillotine.py
calcCutRoller.js     → calculators/cut_roller.py
calcMilling.js       → calculators/milling.py
calcLamination.js    → calculators/lamination.py
calcEmbossing.js     → calculators/embossing.py
calcHeatPress.js     → calculators/heat_press.py
calcTablets.js       → calculators/tablets.py
calcShild.js         → calculators/shild.py
calcBadge.js         → calculators/badge.py
calcUVBadge.js       → calculators/uv_badge.py
calcPresswall.js     → calculators/presswall.py
calcRollup.js        → calculators/rollup.py
calcFlag.js          → calculators/flag.py
calcPennant.js       → calculators/pennant.py
calcMug.js           → calculators/mug.py
calcPuzzle.js        → calculators/puzzle.py
calcMagnets.js       → calculators/magnets.py
calcKeychain.js      → calculators/keychain.py
calcMetalPins.js     → calculators/metal_pins.py
calcAcrilycPrizes.js → calculators/acrylic_prizes.py
calcSticker.js       → calculators/sticker.py
calcPolySticker.js   → calculators/poly_sticker.py
calcCards.js         → calculators/cards.py
calcCalendar.js      → calculators/calendar.py
calcNotebook.js      → calculators/notebook.py
calcPadPrint.js      → calculators/pad_print.py
calcDesign.js        → calculators/design.py
calcProcessTools.js  → calculators/process_tools.py
```

Если JS-файл содержит несколько функций расчёта —  
все остаются в одном Python-файле, каждая регистрируется  
в CALCULATORS под своим slug.