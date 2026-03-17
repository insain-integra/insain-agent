"""
Тесты для common/process_tools.py.

Проверяем корректность миграции вспомогательных функций из
js_legacy/calc/calcProcessTools.js.
"""

from __future__ import annotations

import math

import pytest

from common.process_tools import (
    ProcessResult,
    calc_attachment,
    calc_button_pins,
    calc_crease,
    calc_cut_profile,
    calc_cut_saber,
    calc_cutting_edge,
    calc_epoxy,
    calc_eyelet,
    calc_eyelet_sheet,
    calc_form,
    calc_gluing_banner,
    calc_manual_press,
    calc_manual_roll,
    calc_packing,
    calc_pocket,
    calc_press,
    calc_punching,
    calc_rounding,
    calc_set_cursor,
    calc_set_insert,
    calc_set_profile,
    calc_set_rigel,
    calc_set_rope,
    calc_set_shaft,
    calc_set_staples,
    calc_set_sticker,
    calc_sewing_covers,
    calc_shipment,
    calc_silk_print,
    calc_uv_gluing,
)


# ── ProcessResult ─────────────────────────────────────────────────────

class TestProcessResult:
    def test_default_values(self):
        r = ProcessResult()
        assert r.cost == 0.0
        assert r.price == 0.0
        assert r.time_hours == 0.0
        assert r.weight_kg == 0.0
        assert r.materials == []

    def test_merge(self):
        a = ProcessResult(cost=100, price=200, time_hours=1, weight_kg=0.5,
                          materials=[{"code": "A"}])
        b = ProcessResult(cost=50, price=80, time_hours=0.5, weight_kg=0.2,
                          materials=[{"code": "B"}])
        c = a.merge(b)
        assert c.cost == 150
        assert c.price == 280
        assert c.time_hours == 1.5
        assert c.weight_kg == pytest.approx(0.7)
        assert len(c.materials) == 2


# ── Постпечатная обработка ────────────────────────────────────────────

class TestPunching:
    def test_basic(self):
        r = calc_punching(100, mode=1)
        assert r.cost > 0
        assert r.price > r.cost
        assert r.time_hours > 0

    def test_economy_mode_faster(self):
        r_std = calc_punching(100, mode=1)
        r_eco = calc_punching(100, mode=0)
        # В режиме эконом timePrepare=0 → время меньше или равно
        assert r_eco.time_hours <= r_std.time_hours

    def test_express_more_expensive(self):
        r_std = calc_punching(100, mode=1)
        r_exp = calc_punching(100, mode=2)
        assert r_exp.price >= r_std.price


class TestRounding:
    def test_basic(self):
        r = calc_rounding(50, mode=1)
        assert r.cost > 0
        assert r.price > r.cost

    def test_scales_with_quantity(self):
        r1 = calc_rounding(10, mode=1)
        r2 = calc_rounding(100, mode=1)
        assert r2.cost > r1.cost


class TestCrease:
    def test_single_crease(self):
        r = calc_crease(100, crease=1, size=[210, 297], mode=1)
        assert r.cost > 0
        assert r.time_hours > 0

    def test_multiple_creases_more_expensive(self):
        r1 = calc_crease(100, crease=1, size=[210, 297], mode=1)
        r3 = calc_crease(100, crease=3, size=[210, 297], mode=1)
        assert r3.cost > r1.cost

    def test_oversize_raises(self):
        with pytest.raises(ValueError, match="больше допустимого"):
            calc_crease(10, crease=1, size=[500, 500], mode=1)


class TestCuttingEdge:
    def test_all_edges(self):
        r = calc_cutting_edge(10, [200, 300], [1, 1, 1, 1], mode=1)
        assert r.cost > 0

    def test_no_edges(self):
        r = calc_cutting_edge(10, [200, 300], [0, 0, 0, 0], mode=1)
        assert r.cost == 0

    def test_partial_edges(self):
        r_partial = calc_cutting_edge(10, [200, 300], [1, 0, 1, 0], mode=1)
        r_all = calc_cutting_edge(10, [200, 300], [1, 1, 1, 1], mode=1)
        assert r_all.cost > r_partial.cost


class TestManualPress:
    def test_basic(self):
        r = calc_manual_press(50, mode=1)
        assert r.cost > 0
        assert r.price > 0


class TestPress:
    def test_basic(self):
        r = calc_press(50, mode=1)
        assert r.cost > 0
        assert r.price > 0


# ── Переплёт и крепёж ────────────────────────────────────────────────

class TestSetStaples:
    def test_basic(self):
        r = calc_set_staples(100, mode=1)
        assert r.cost > 0
        assert r.price > r.cost
        assert r.time_hours > 0
        assert len(r.materials) == 1
        assert r.materials[0]["code"] == "Staples26_6"


# ── Люверсы ───────────────────────────────────────────────────────────

class TestEyelet:
    def test_basic(self):
        r = calc_eyelet(10, [2000, 1000], [300, 300, 300, 300], mode=1)
        assert r.cost > 0
        assert len(r.materials) == 1
        assert r.materials[0]["quantity"] > 0

    def test_no_eyelets(self):
        r = calc_eyelet(10, [2000, 1000], [0, 0, 0, 0], mode=1)
        assert r.cost == 0


class TestEyeletSheet:
    def test_basic(self):
        r = calc_eyelet_sheet(100, mode=1)
        assert r.cost > 0
        assert len(r.materials) == 1
        assert r.materials[0]["quantity"] == 100


# ── Проклейка и наклейка ─────────────────────────────────────────────

class TestGluingBanner:
    def test_all_edges(self):
        r = calc_gluing_banner(5, [2000, 1000], [1, 1, 1, 1], mode=1)
        assert r.cost > 0

    def test_no_edges(self):
        r = calc_gluing_banner(5, [2000, 1000], [0, 0, 0, 0], mode=1)
        assert r.cost == 0


class TestSetSticker:
    def test_basic(self):
        r = calc_set_sticker(100, mode=1)
        assert r.cost > 0
        assert r.time_ready > 0


class TestManualRoll:
    def test_no_bend(self):
        r = calc_manual_roll(10, [300, 200], {"isEdge": ""}, mode=1)
        assert r.cost > 0

    def test_bend_edge(self):
        r = calc_manual_roll(5, [500, 400], {"isEdge": "isBendEdge"}, mode=1)
        assert r.cost > 0


# ── Полимерная заливка ────────────────────────────────────────────────

class TestEpoxy:
    def test_basic(self):
        r = calc_epoxy(100, [30, 20], difficulty=1, mode=1)
        assert r.cost > 0
        assert r.weight_kg > 0
        assert r.time_ready > r.time_hours
        assert len(r.materials) == 1
        assert r.materials[0]["code"] == "EpoxyPoly"

    def test_complex_form(self):
        r_simple = calc_epoxy(100, [30, 20], difficulty=1, mode=1)
        r_complex = calc_epoxy(100, [30, 20], difficulty=1.5, mode=1)
        # Сложная форма использует более медленный режим заливки
        assert r_complex.time_hours >= r_simple.time_hours


# ── УФ-склейка ────────────────────────────────────────────────────────

class TestUVGluing:
    def test_basic(self):
        r = calc_uv_gluing(50, [50, 50], mode=1)
        assert r.cost > 0
        assert r.time_hours > 0


# ── Установка элементов ──────────────────────────────────────────────

class TestSetSticker2:
    def test_scales(self):
        r1 = calc_set_sticker(10, mode=1)
        r2 = calc_set_sticker(100, mode=1)
        assert r2.cost > r1.cost


class TestSetInsert:
    def test_basic(self):
        r = calc_set_insert(200, mode=1)
        assert r.cost > 0
        assert r.time_hours > 0
        assert r.time_ready == r.time_hours


# ── Крепления и карманы ───────────────────────────────────────────────

class TestAttachment:
    def test_basic(self):
        r = calc_attachment(100, "PinMetall20", mode=1)
        assert r.cost > 0
        assert r.weight_kg > 0
        assert len(r.materials) == 1
        assert r.materials[0]["code"] == "PinMetall20"

    def test_scales_with_quantity(self):
        r1 = calc_attachment(10, "PinMetall20", mode=1)
        r2 = calc_attachment(100, "PinMetall20", mode=1)
        assert r2.cost > r1.cost


class TestPocket:
    def test_basic(self):
        r = calc_pocket(50, "Pocket", mode=1)
        assert r.cost > 0
        assert len(r.materials) == 1


class TestPacking:
    def test_auto_select(self):
        r = calc_packing(100, [80, 60, 2], {"isPacking": ""}, mode=1)
        assert r.cost > 0
        assert len(r.materials) == 1

    def test_specific_pack(self):
        r = calc_packing(100, [80, 60, 2], {"isPacking": "ZipLock1015"}, mode=1)
        assert r.cost > 0
        assert r.materials[0]["code"] == "ZipLock1015"

    def test_no_packing(self):
        r = calc_packing(100, [80, 60, 2], {}, mode=1)
        assert r.cost == 0


# ── Нарезка ───────────────────────────────────────────────────────────

class TestCutProfile:
    def test_basic(self):
        r = calc_cut_profile(5, [[500, 2], [300, 4]], "DWE713XPS", mode=1)
        assert r.cost > 0
        assert r.time_ready > r.time_hours


# ── Доставка ──────────────────────────────────────────────────────────

class TestShipment:
    def test_dellin(self):
        r = calc_shipment(2, [300, 200, 100], 5.0, "Dellin")
        assert r.cost > 0
        assert r.time_ready == 40.0

    def test_own(self):
        r = calc_shipment(1, [500, 300, 200], 3.0, "Own")
        assert r.cost > 0
        assert r.time_ready == 40.0

    def test_luch(self):
        r = calc_shipment(1, [200, 200, 200], 2.0, "Luch")
        assert r.cost > 0
        assert r.time_ready == 16.0


# ── Вырубная форма ────────────────────────────────────────────────────

class TestForm:
    def test_basic(self):
        r = calc_form([50, 30], num_items=4, difficulty=1.0, mode=1)
        assert r.cost > 0
        assert r.time_ready > 0
        assert r.time_hours == 0  # форма изготавливается подрядчиком

    def test_min_cost(self):
        r = calc_form([5, 3], num_items=1, difficulty=1.0, mode=1)
        # Минимальная стоимость формы = 1000
        assert r.cost >= 1000


# ── Шелкография ───────────────────────────────────────────────────────

class TestSilkPrint:
    def test_tshirt_white(self):
        r = calc_silk_print(50, [300, 250], color=2, item_id="tshirtwhite", mode=1)
        assert r.cost > 0
        assert r.price > 0
        assert r.time_ready > 0

    def test_transfer(self):
        r = calc_silk_print(100, [200, 150], color=1, item_id="transfer", mode=1)
        assert r.cost > 0

    def test_scales(self):
        r1 = calc_silk_print(50, [300, 250], color=1, item_id="tshirtwhite", mode=1)
        r2 = calc_silk_print(500, [300, 250], color=1, item_id="tshirtwhite", mode=1)
        assert r2.cost > r1.cost


# ── Закатные значки ───────────────────────────────────────────────────

class TestButtonPins:
    def test_small_batch(self):
        r = calc_button_pins(100, "D38", {"isPacking": ""}, mode=1)
        assert r.cost > 0
        assert r.price > 0
        assert r.time_hours > 0
        assert len(r.materials) >= 1
