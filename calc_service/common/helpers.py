from typing import Iterable, List, Sequence, Tuple


def find_in_table(table: Sequence[Tuple[float, float]], value: float) -> float:
    """
    Найти значение в таблице порогов.

    :param table: последовательность кортежей (threshold, result_value),
                  отсортированная по threshold по возрастанию.
    :param value: искомое значение (например, тираж).
    :return: result_value для первого threshold >= value,
             либо последнее result_value, если подходящего порога нет.
    """
    if not table:
        raise ValueError("таблица порогов не должна быть пустой")

    last_value = table[-1][1]

    for threshold, result in table:
        if value <= threshold:
            return result

    return last_value


def calc_weight(
    quantity: int,
    density: float,
    thickness: float,
    size: Sequence[float],
    density_unit: str,
) -> float:
    """
    Рассчитать вес тиража в килограммах.

    :param quantity: количество изделий
    :param density: плотность (г/см³ или г/м² в зависимости от density_unit)
    :param thickness: толщина материала в миллиметрах (для г/см³)
    :param size: [width_mm, height_mm]
    :param density_unit: "гсм3" для объёмной плотности, "гм2" для поверхностной
    :return: общий вес тиража в килограммах
    """
    if len(size) != 2:
        raise ValueError("size должен быть последовательностью вида [width_mm, height_mm]")

    width_mm, height_mm = size

    if density_unit == "гсм3":
        # Переводим мм → см: 10 мм = 1 см
        width_cm = width_mm / 10.0
        height_cm = height_mm / 10.0
        thickness_cm = thickness / 10.0

        volume_cm3 = width_cm * height_cm * thickness_cm
        weight_per_piece_g = volume_cm3 * density
    elif density_unit == "гм2":
        # Переводим мм → м: 1000 мм = 1 м
        width_m = width_mm / 1000.0
        height_m = height_mm / 1000.0

        area_m2 = width_m * height_m
        weight_per_piece_g = area_m2 * density
    else:
        raise ValueError('density_unit должен быть "гсм3" или "гм2"')

    total_weight_kg = quantity * weight_per_piece_g / 1000.0
    return total_weight_kg

