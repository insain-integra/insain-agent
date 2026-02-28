"""
Пошаговое сравнение калькулятора плоттерной резки (Python) с JS (calcCutPlotter.js)
при одинаковых входных данных: 1000 шт, 60×60 мм, Avery500c, difficulty=1.3, mode=1.

Запуск: из корня calc_service: python scripts/compare_cut_plotter_steps.py

В конце выводится сводка: на каком шаге возникает расхождение с JS (если известны эталонные значения).
"""

from __future__ import annotations

import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# Параметры как в эталонном тесте 1000 шт
PARAMS = {
    "quantity": 1000,
    "width_mm": 60,
    "height_mm": 60,
    "material_code": "Avery500c",
    "plotter_code": "",
    "difficulty": 1.3,
    "mode": 1,
}

# Эталон из JS (если известен): для сверки
JS_REF = {
    "len_cut_m": 0.312,
    "num_with_defects": 1005,  # ceil(1000*1.005) при defects=0.005
    "len_material_m": 3.22,    # в JS выбирается min из 4 вариантов раскроя рулона
    "time_hours": 1.64,
    "cost": 2716,
    "price": 4345,
}


def main():
    from calculators.cut_plotter import CutPlotterCalculator
    from common.layout import layout_on_roll
    from equipment import plotter as plotter_catalog

    calc = CutPlotterCalculator()
    quantity = int(PARAMS["quantity"])
    w = float(PARAMS["width_mm"])
    h = float(PARAMS["height_mm"])
    size = [w, h]
    material_code = PARAMS["material_code"]
    plotter_code = PARAMS.get("plotter_code") or "GraphtecCE5000-60"
    difficulty = float(PARAMS.get("difficulty", 1))
    mode = int(PARAMS.get("mode", 1))
    interval = 4.0

    plotter = plotter_catalog.get(plotter_code)
    from calculators.cut_plotter import _find_material
    material = _find_material(material_code)

    margins = list(plotter.margins or [30, 10, 10, 10])
    if len(margins) < 4:
        margins = [30, 10, 10, 10]

    print("=" * 60)
    print("Входные данные (как в эталоне 1000 шт)")
    print("=" * 60)
    print(f"  quantity={quantity}, size={w}x{h} mm, material={material_code}, difficulty={difficulty}, mode={mode}")
    print()

    # Шаг 1: брак
    defects = plotter.get_defect_rate(float(quantity))
    num_with_defects = math.ceil(quantity * (1 + defects))
    print("Шаг 1. Брак и количество с учётом брака")
    print("  defects (из таблицы по quantity):", defects)
    print("  num_with_defects = ceil(quantity * (1 + defects)):", num_with_defects)
    print("  JS: defects = plotter.defects.find(item => item[0] >= n)[1]; numWithDefects = Math.ceil(n*(1+defects))")
    if JS_REF.get("num_with_defects") and num_with_defects != JS_REF["num_with_defects"]:
        print("  >>> РАСХОЖДЕНИЕ: ожидалось num_with_defects =", JS_REF["num_with_defects"])
    print()

    # Шаг 2: len_cut (вычисляемая величина при 0 на входе)
    len_cut = (size[0] + size[1]) * 2.0 / 1000.0 * difficulty
    print("Шаг 2. Длина реза одного элемента (len_cut), м")
    print("  len_cut = (w+h)*2/1000 * difficulty:", len_cut)
    print("  JS: lenCut = (size[0]+size[1])*2; lenCut += ...; lenCut = lenCut*difficulty/1000")
    if JS_REF.get("len_cut_m") and abs(len_cut - JS_REF["len_cut_m"]) > 1e-6:
        print("  >>> РАСХОЖДЕНИЕ: ожидалось len_cut =", JS_REF["len_cut_m"])
    print()

    # Шаг 3: толщина и скорость
    thickness_um = 80.0
    if material:
        if getattr(material, "thickness", None):
            thickness_um = float(material.thickness)
            if thickness_um < 20:
                thickness_um *= 1000
        elif getattr(material, "density", None):
            thickness_um = material.density / 80.0 * 100.0
    process_per_hour = plotter.get_process_speed(thickness_um) if hasattr(plotter, "get_process_speed") else 120.0
    if process_per_hour <= 0:
        process_per_hour = 120.0
    print("Шаг 3. Толщина материала и скорость резки")
    print("  thickness_um:", thickness_um)
    print("  process_per_hour (м/ч):", process_per_hour)
    print()

    # Шаг 4: раскладка на рулоне (рулонный материал)
    is_roll = material and getattr(material, "is_roll", False)
    len_material_mm = None
    num_sheet = None
    len_cut_with_defects = len_cut * num_with_defects

    if is_roll and material and material.sizes:
        roll_size = next((s for s in material.sizes if s[1] == 0), material.sizes[0])
        roll_w = float(roll_size[0])
        size_with_margins = [size[0] + margins[0] + margins[2], size[1] + margins[1] + margins[3]]
        layout_roll = layout_on_roll(num_with_defects, size_with_margins, [roll_w, 0.0], interval)
        len_material_mm = layout_roll["length"]
        max_plotter = plotter.max_size or [603, 5000]
        num_sheet = math.ceil(len_material_mm / max_plotter[0])

        print("Шаг 4. Рулон: раскладка на материале")
        print("  roll_width (мм):", roll_w)
        print("  size_with_margins [w+m0+m2, h+m1+m3]:", size_with_margins)
        print("  layout_on_roll(num_with_defects, size_with_margins, [roll_w,0], interval)")
        print("  len_material (мм):", len_material_mm)
        print("  len_material (m):", round(len_material_mm / 1000.0, 2))
        print("  num_sheet (загрузок) = ceil(len_material_mm / max_plotter[0]):", num_sheet)
        print("  JS: для рулона перебирает 4 способа раскроя, выбирает min lenMaterial; result.material = lenMaterial/1000 (м)")
        if JS_REF.get("len_material_m") and len_material_mm is not None:
            js_m = JS_REF["len_material_m"]
            py_m = len_material_mm / 1000.0
            if abs(py_m - js_m) > 0.01:
                print("  >>> RASHOZHDENIE: ozhidalos len_material ~", js_m, "m, polucheno", round(py_m, 2), "m")
                print("      Причина: в JS используется несколько вариантов раскроя (короткой/длинной стороной по ширине рулона,")
                print("      разная ширина рулона с отступами), выбирается минимальный расход. В Python пока один вариант.")
    else:
        print("Шаг 4. Листовой материал (раскладка на листе плоттера)")
        max_plotter = plotter.max_size or [603, 5000]
        from common.layout import layout_on_sheet
        layout_plotter = layout_on_sheet(size, max_plotter, margins, interval)
        num_sheet = math.ceil(num_with_defects / layout_plotter["num"])
        len_cut_with_defects = len_cut * num_with_defects if num_sheet <= 1 else len_cut * layout_plotter["num"] * num_sheet
        print("  layout_plotter.num:", layout_plotter["num"])
        print("  num_sheet:", num_sheet)
        print("  len_cut_with_defects (м):", len_cut_with_defects)
    print()

    # Шаг 5: время и себестоимость
    time_prepare = (plotter.time_prepare or 0.05) * mode
    time_load_sheet = getattr(plotter, "time_load_sheet", 0.01) or 0.01
    time_cut = len_cut_with_defects / process_per_hour + time_prepare + num_sheet * time_load_sheet
    time_hours = round(time_cut * 100) / 100.0

    cost_depreciation = plotter.depreciation_per_hour * time_cut
    cost_process = len_cut_with_defects * (plotter.cost_process or 0.3)
    cost_operator = time_cut * plotter.operator_cost_per_hour
    cost = cost_depreciation + cost_process + cost_operator

    from common.markups import MARGIN_MIN, MARGIN_OPERATION, get_margin
    margin_extra = get_margin("marginPlotter")
    effective_margin = max(MARGIN_OPERATION + margin_extra, MARGIN_MIN)
    price = math.ceil(cost * (1 + effective_margin))

    print("Шаг 5. Время и деньги")
    print("  len_cut_with_defects (м):", len_cut_with_defects)
    print("  time_prepare:", time_prepare, ", time_load_sheet * num_sheet:", time_load_sheet * num_sheet)
    print("  time_cut = len_cut_with_defects/process_per_hour + time_prepare + num_sheet*time_load_sheet:", time_cut)
    print("  time_hours (округл. до 0.01):", time_hours)
    print("  cost (depreciation + process + operator):", cost)
    print("  price (ceil(cost * (1+margin))):", price)
    if JS_REF.get("time_hours") and abs(time_hours - JS_REF["time_hours"]) > 0.02:
        print("  >>> РАСХОЖДЕНИЕ по time: ожидалось", JS_REF["time_hours"])
    if JS_REF.get("cost") and abs(cost - JS_REF["cost"]) > 50:
        print("  >>> РАСХОЖДЕНИЕ по cost: ожидалось ~", JS_REF["cost"])
    print()

    # Итог через execute()
    result = calc.execute(PARAMS)
    print("=" * 60)
    print("Итог calc.execute(PARAMS)")
    print("=" * 60)
    print("  cost:", result["cost"])
    print("  price:", result["price"])
    print("  time_hours:", result["time_hours"])
    print("  time_ready:", result["time_ready"])
    for m in result.get("materials") or []:
        print("  material:", m.get("quantity"), m.get("unit"), "—", m.get("name", "")[:40])
    print()
    print("Etalon (JS): cost 2716, price 4345, time 1.64, ready 17.64, material 3.22 m")
    print("Расхождение по расходу материала ведёт к разному num_sheet и времени/себестоимости.")
    print("В JS для рулона используется выбор минимального расхода из нескольких вариантов раскроя.")


if __name__ == "__main__":
    main()
