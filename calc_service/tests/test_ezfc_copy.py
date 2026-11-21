"""scripts/ezfc_copy.py: id копии в JS и GET-пакет без касания боевой формы."""

from __future__ import annotations

import importlib.util
import json
import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
_spec = importlib.util.spec_from_file_location("ezfc_copy", ROOT / "scripts" / "ezfc_copy.py")
ezfc_copy = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(ezfc_copy)

MAP_78_91 = "numN\t3071\t3463\nrdoModeProduction\t3094\t3484\ncjsCalc\t3081\t3471\n"


def test_acrylic_prizes_js_gets_copy_ids():
    js = (ROOT / "wp-plugin" / "forms" / "acrylic_prizes.js").read_text(encoding="utf-8")
    out = ezfc_copy.build_copy_js(js, ezfc_copy.parse_id_map(MAP_78_91))
    assert "get_value_from(3484, true)" in out
    assert "get_value_from(3094" not in out
    assert "insaincalc.calcApi('acrylic_prizes'" in out


def test_unknown_live_id_stops():
    id_map = ezfc_copy.parse_id_map(MAP_78_91)
    with pytest.raises(ValueError, match="3999"):
        ezfc_copy.build_copy_js("ezfc_functions.get_value_from(3999, true)[0]", id_map)


@pytest.mark.parametrize(
    "table, msg",
    [
        ("numN\t3071\tNULL\n", "нет id копии"),
        ("numN\t3071\t3071\n", "совпадает с боевым"),
        ("", "пуста"),
    ],
)
def test_bad_id_map_stops(table, msg):
    with pytest.raises(ValueError, match=msg):
        ezfc_copy.parse_id_map(table)


def test_package_has_only_whitelisted_keys(tmp_path):
    js_path = ROOT / "wp-plugin" / "forms" / "acrylic_prizes.js"
    map_path = tmp_path / "map.tsv"
    map_path.write_text(MAP_78_91, encoding="utf-8")
    out = tmp_path / "pkg.json"
    code = ezfc_copy.main(
        [str(js_path), "--live", "78", "--copy", "91", "--map", str(map_path),
         "--get", "numN", "--get", "rdoModeProduction:value", "--out", str(out)]
    )
    assert code == 0
    pkg = json.loads(out.read_text(encoding="utf-8"))
    assert (pkg["live"], pkg["copy"]) == (78, 91)
    assert set(pkg["elements"]) == {"3471", "3463", "3484"}
    assert pkg["elements"]["3484"] == {"GET": "rdoModeProduction", "GET_check_option_value": "value"}
    keys = {k for fields in pkg["elements"].values() for k in fields}
    php = (ROOT / "scripts" / "ezfc_copy_apply.php").read_text(encoding="utf-8")
    for key in keys:
        assert f"'{key}'" in php.split("$allowed = array(")[1].split(");")[0]


def test_same_form_or_bad_check_stops():
    id_map = ezfc_copy.parse_id_map(MAP_78_91)
    with pytest.raises(ValueError, match="одна и та же"):
        ezfc_copy.build_package("", 78, 78, id_map, "cjsCalc", [])
    with pytest.raises(ValueError, match="GET_check"):
        ezfc_copy.build_package("", 78, 91, id_map, "cjsCalc", ["numN:idx"])


def _form_block(js: str, form_id: int) -> str:
    match = re.search(rf"/\*\s*form\s+{form_id}\s*\*/(.*?)/\*\s*/form\s*\*/", js, re.DOTALL)
    assert match, form_id
    return match.group(1)


def _id_map_for(ids: set[int], copy_base: int) -> dict:
    lines = [f"cjsCalc\t1042\t{copy_base}"]
    for offset, live in enumerate(sorted(ids), start=1):
        lines.append(f"el{offset}\t{live}\t{copy_base + offset}")
    return ezfc_copy.parse_id_map("\n".join(lines) + "\n")


def test_sticker_copy_rewrites_only_live_form_block():
    """Форма 29 и форма 22 в одном файле: копия переписывает id только своей ветки."""
    js = (ROOT / "wp-plugin" / "forms" / "sticker.js").read_text(encoding="utf-8")
    ids_29 = {int(n) for n in re.findall(r"get_value_from\(\s*(\d+)", _form_block(js, 29))}
    ids_22 = {int(n) for n in re.findall(r"get_value_from\(\s*(\d+)", _form_block(js, 22))}
    assert {1039, 1056, 1062} <= ids_29
    assert 1064 in ids_22
    assert ids_29.isdisjoint(ids_22)

    out_29 = ezfc_copy.build_copy_js(js, _id_map_for(ids_29, 29000), live=29)
    assert "get_value_from(1064, true)" in out_29
    assert "get_value_from(1039" not in _form_block(out_29, 29)
    assert "get_value_from(29001" in _form_block(out_29, 29)

    out_22 = ezfc_copy.build_copy_js(js, _id_map_for(ids_22, 22000), live=22)
    assert "get_value_from(1039, true)" in out_22
    assert "get_value_from(1064" not in _form_block(out_22, 22)

    broken = js.replace("get_value_from(1039, true)", "get_value_from(3999, true)", 1)
    with pytest.raises(ValueError, match="3999"):
        ezfc_copy.build_copy_js(broken, _id_map_for(ids_29 - {1039}, 29000), live=29)


def test_print_sheet_copy_rewrites_only_live_form_block():
    """Форма 19 и форма 6 в одном файле: копия live=19 переписывает id 19 и оставляет id 6."""
    js = (ROOT / "wp-plugin" / "forms" / "print_sheet.js").read_text(encoding="utf-8")
    ids_19 = {432, 435, 436, 439, 574, 725, 726, 727, 728, 731}
    ids_6 = {99, 100, 101, 102, 103, 400, 401, 402, 419, 519, 661, 663, 664, 665, 666, 667, 668}
    assert ids_19.isdisjoint(ids_6)

    id_map_19 = _id_map_for(ids_19, 19000)
    out_19 = ezfc_copy.build_copy_js(js, id_map_19, live=19)
    assert "get_value_from(99, true)" in _form_block(out_19, 6)
    assert "get_value_from(665)" in _form_block(out_19, 6)
    assert "get_value_from(432" not in _form_block(out_19, 19)
    assert "get_value_from(19001, true)" in _form_block(out_19, 19)
    for live_id in ids_6:
        assert f"get_value_from({live_id}" in out_19
    for live_id in ids_19:
        assert f"get_value_from({live_id}" not in out_19

