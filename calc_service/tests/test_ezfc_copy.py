"""scripts/ezfc_copy.py: id копии в JS и GET-пакет без касания боевой формы."""

from __future__ import annotations

import importlib.util
import json
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
