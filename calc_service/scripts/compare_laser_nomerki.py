#!/usr/bin/env python3
"""
Сравнение расчёта «Номерки с гравировкой» между JS (calcLaser.js) и Python (laser.py).

Входные параметры (как в test_laser.py):
  quantity=50, 40×80 мм, AcrylColor3, mode=1, is_grave=1, is_grave_fill=[30,40], is_cut_laser={}

Запуск из каталога calc_service: python scripts/compare_laser_nomerki.py
"""

from __future__ import annotations

import json
import math
import sys
from pathlib import Path

# Добавляем корень calc_service в путь
ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# Параметры кейса
N = 50
SIZE = [40.0, 80.0]
MATERIAL_ID = "AcrylColor3"
MODE = 1
INTERVAL = 5.0
MARGINS = [0.0, 0.0, 0.0, 0.0]
IS_GRAVE = 1
IS_GRAVE_FILL = [30.0, 40.0]


def load_json5(path: Path) -> dict:
    try:
        import json5
        with open(path, "r", encoding="utf-8") as f:
            return json5.load(f)
    except ImportError:
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()
        # Удаляем однострочные комментарии для простого json
        lines = []
        for line in content.splitlines():
            if "//" in line:
                line = line[: line.index("//")].rstrip()
            lines.append(line)
        return json.loads("\n".join(lines))


def js_style_layout_on_sheet(size: list, size_sheet: list, margins: list, interval: float) -> int:
    """Воспроизведение JS calcLayoutOnSheet: margins [left, top, right, bottom]."""
    width_print = size_sheet[0] - margins[0] - margins[2]
    height_print = size_sheet[1] - margins[1] - margins[3]
    min_size = min(size[0], size[1]) + interval
    max_size = max(size[0], size[1]) + interval
    min_sheet = min(width_print, height_print) + interval
    max_sheet = max(width_print, height_print) + interval
    along_long = math.floor(max_sheet / max_size) * math.floor(min_sheet / min_size)
    along_short = math.floor(max_sheet / min_size) * math.floor(min_sheet / max_size)
    if along_long >= along_short:
        return along_long
    return along_short


def main() -> None:
    common = load_json5(ROOT / "data" / "common.json")
    laser_raw = load_json5(ROOT / "data" / "equipment" / "laser.json")
    laser_data = laser_raw["Qualitech11G1290"]

    # Курсы и наценки
    usd = float(common.get("USD", 95))
    eur = float(common.get("EUR", 100))
    cost_operator = float(common.get("costOperator", 1400))
    margin_material = float(common.get("marginMaterial", 0.6))
    margin_operation = float(common.get("marginOperation", 0.55))
    margin_laser = float(common.get("marginLaser", 0))

    # Лазер: cost в JS подставляется как USD*11600
    laser_cost_usd = 11600
    laser_cost_rub = laser_cost_usd * usd
    cost_laser_tube_usd = 680
    cost_laser_tube_rub = cost_laser_tube_usd * usd
    life_tube = 8000
    cost_cut_per_hour = cost_laser_tube_rub / life_tube + 5.0 * 1.85
    cost_grave_per_hour = cost_cut_per_hour
    time_depreciation = 10
    work_day = 250
    hours_day = 4
    cost_depreciation_hour = laser_cost_rub / time_depreciation / work_day / hours_day

    # Брак: defects find first row where item[0] >= n
    defects_table = [[10, 0.1], [100, 0.05], [500, 0.02], [1000, 0.01], [10000000, 0.01]]
    defect_rate = next(v for th, v in defects_table if N <= th)
    if MODE > 1:
        defect_rate += defect_rate * (MODE - 1)

    # Количество с учётом брака — источник расхождений
    n_raw = N * (1 + defect_rate)  # 52.5
    num_js = int(n_raw + 0.5)       # JS: Math.round(52.5) = 53
    num_py = round(n_raw)           # Python 3: round(52.5) = 52 (banker's rounding)

    print("=== Входные параметры ===")
    print(f"  quantity={N}, size={SIZE}, material={MATERIAL_ID}, mode={MODE}")
    print(f"  interval={INTERVAL}, is_grave={IS_GRAVE}, is_grave_fill={IS_GRAVE_FILL}")
    print()
    print("=== Курсы и наценки ===")
    print(f"  USD={usd}, EUR={eur}, costOperator={cost_operator}")
    print(f"  marginMaterial={margin_material}, marginOperation={margin_operation}, marginLaser={margin_laser}")
    print()
    print("=== Брак и количество ===")
    print(f"  defect_rate = {defect_rate}")
    print(f"  n*(1+defect) = {N * (1 + defect_rate)}")
    print(f"  JS:  Math.round(...) = {num_js}")
    print(f"  Py:  round(...)      = {num_py}")
    print(f"  >>> РАСХОЖДЕНИЕ: {num_js} vs {num_py} (52.5: JS round=53, Python round=52)")
    print()

    # Загружаем материал AcrylColor3 из hardsheet
    hardsheet = load_json5(ROOT / "data" / "materials" / "hardsheet.json")
    material = None
    for group_id, group_data in hardsheet.items():
        if not isinstance(group_data, dict) or "Default" not in group_data:
            continue
        if MATERIAL_ID in group_data:
            defs = group_data.get("Default", {}) or {}
            rec = {**defs, **group_data[MATERIAL_ID]}
            material = rec
            break
    if not material:
        print("Материал AcrylColor3 не найден")
        return

    cost_mat_flat = material.get("cost")
    if isinstance(cost_mat_flat, list):
        cost_mat_flat = cost_mat_flat[-1][1] if cost_mat_flat else 0
    thickness = float(material.get("thickness", 3))
    set_size_material = material.get("size", [[3050, 2050]])
    if isinstance(set_size_material[0], (int, float)):
        set_size_material = [set_size_material]
    size_material_0 = set_size_material[0]
    min_size = material.get("minSize", [200, 200])
    if isinstance(min_size, (int, float)):
        min_size = [min_size, 0]

    # Длина реза и гравировка
    len_cut = (SIZE[0] + SIZE[1]) * 2
    area_grave = IS_GRAVE_FILL[0] * IS_GRAVE_FILL[1] / 1e6
    grave_per_hour = laser_data["gravePerHour"][IS_GRAVE]
    time_grave_js = area_grave * num_js / grave_per_hour
    time_grave_py = area_grave * num_py / grave_per_hour

    # Раскладка на поле лазера
    laser_max = laser_data["maxSize"][:2]
    num_on_laser = js_style_layout_on_sheet(SIZE, laser_max, MARGINS, INTERVAL)
    num_load_js = math.ceil(num_js / num_on_laser)
    num_load_py = math.ceil(num_py / num_on_laser)

    # Скорость резки: first row where thickness >= material.thickness
    cut_table = laser_data["cutPerHour"]
    cut_per_hour = next(v for th, v in cut_table if th >= thickness)

    time_cut_js = len_cut * num_js / cut_per_hour / 1000 + num_load_js * laser_data["timeLoad"]
    time_cut_py = len_cut * num_py / cut_per_hour / 1000 + num_load_py * laser_data["timeLoad"]

    # Раскладка на листе материала
    layout_sheet_num = js_style_layout_on_sheet(SIZE, size_material_0, MARGINS, INTERVAL)
    layout_min_num = js_style_layout_on_sheet(min_size, size_material_0, [0, 0, 0, 0], 0)
    num_sheet_js = math.ceil(num_js / layout_sheet_num * layout_min_num) / layout_min_num
    num_sheet_py = math.ceil(num_py / layout_sheet_num * layout_min_num) / layout_min_num

    cost_material_js = cost_mat_flat * num_sheet_js * size_material_0[0] * size_material_0[1] / 1e6
    cost_material_py = cost_mat_flat * num_sheet_py * size_material_0[0] * size_material_0[1] / 1e6

    # Время и стоимость (оператор, резка, гравировка)
    time_prepare = laser_data["timePrepare"] * MODE
    time_operator_js = 0.75 * time_cut_js + 0.5 * time_grave_js + time_prepare
    time_operator_py = 0.75 * time_cut_py + 0.5 * time_grave_py + time_prepare

    cost_operator_js = time_operator_js * cost_operator
    cost_operator_py = time_operator_py * cost_operator
    cost_cut_js = cost_depreciation_hour * time_cut_js + time_cut_js * cost_cut_per_hour
    cost_cut_py = cost_depreciation_hour * time_cut_py + time_cut_py * cost_cut_per_hour
    cost_grave_js = cost_depreciation_hour * time_grave_js + time_grave_js * cost_grave_per_hour
    cost_grave_py = cost_depreciation_hour * time_grave_py + time_grave_py * cost_grave_per_hour

    cost_js = cost_cut_js + cost_grave_js + cost_material_js + cost_operator_js
    cost_py_raw = cost_cut_py + cost_grave_py + cost_material_py + cost_operator_py
    cost_js = math.ceil(cost_js)
    cost_py_ceil = math.ceil(cost_py_raw)
    if num_js == N:
        cost_js *= 1 + defect_rate
    if num_py == N:
        cost_py_ceil = math.ceil(cost_py_raw * (1 + defect_rate))

    margin_eff = max(margin_operation + margin_laser, 0.25)
    price_js = math.ceil(
        cost_material_js * (1 + margin_material)
        + (cost_cut_js + cost_grave_js + cost_operator_js) * (1 + margin_eff)
    )
    price_py = math.ceil(
        cost_material_py * (1 + margin_material)
        + (cost_cut_py + cost_grave_py + cost_operator_py) * (1 + margin_eff)
    )

    base_time_ready = laser_data["baseTimeReady"][MODE]  # JS: Math.ceil(1)=1 → index 1
    time_hours_js = math.ceil((time_cut_js + time_grave_js + time_prepare) * 100) / 100
    time_hours_py = math.ceil((time_cut_py + time_grave_py + time_prepare) * 100) / 100
    time_ready_js = time_hours_js + base_time_ready
    time_ready_py = time_hours_py + base_time_ready

    print("=== Промежуточные значения (JS-логика с num=53 vs Python с num=52) ===")
    print(f"  len_cut = {len_cut} mm")
    print(f"  num_on_laser = {num_on_laser}, num_load: JS={num_load_js} Py={num_load_py}")
    print(f"  layout_sheet_num = {layout_sheet_num}, layout_min_num = {layout_min_num}")
    print(f"  num_sheet: JS={num_sheet_js:.6f} Py={num_sheet_py:.6f}")
    print(f"  time_grave: JS={time_grave_js:.4f} Py={time_grave_py:.4f}")
    print(f"  time_cut:   JS={time_cut_js:.4f} Py={time_cut_py:.4f}")
    print(f"  cost_material: JS={cost_material_js:.2f} Py={cost_material_py:.2f}")
    print()
    print("=== Итог (ручная эмуляция JS vs Python при своём num) ===")
    print(f"  cost:  JS~{cost_js}  Py~{cost_py_ceil}")
    print(f"  price: JS~{price_js}  Py~{price_py}")
    print(f"  time_hours:  JS={time_hours_js}  Py={time_hours_py}")
    print(f"  time_ready:  JS={time_ready_js}  Py={time_ready_py}")
    print()

    # Реальный запуск Python-калькулятора (если окружение есть)
    try:
        from calculators.laser import LaserCalculator
        calc = LaserCalculator()
        params = {
            "quantity": N,
            "width": SIZE[0],
            "height": SIZE[1],
            "material_id": MATERIAL_ID,
            "mode": MODE,
            "is_cut_laser": {},
            "is_grave": IS_GRAVE,
            "is_grave_fill": IS_GRAVE_FILL,
        }
        result = calc.execute(params)
        print("=== Результат Python-калькулятора (после исправления округления) ===")
        print(f"  cost       = {result['cost']}")
        print(f"  price      = {result['price']}")
        print(f"  time_hours = {result['time_hours']}")
        print(f"  time_ready = {result['time_ready']}")
        print(f"  weight_kg  = {result['weight_kg']}")
    except Exception as e:
        print(f"  (калькулятор не запущен: {e})")
    print()
    print("=== Вывод ===")
    print("Расхождение было из-за округления num_with_defects (кол-во с учетом брака):")
    print("  JS:  Math.round(50 * 1.05) = 53")
    print("  Py3: round(50 * 1.05)      = 52 (banker's rounding)")
    print("В laser.py применено: int(quantity * (1 + defect_rate) + 0.5) для совпадения с JS.")


if __name__ == "__main__":
    main()
