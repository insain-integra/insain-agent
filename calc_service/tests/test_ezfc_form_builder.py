"""Тесты конструктора форм ezFC (scripts/ezfc_build_form.py, шаблон 79, PHP-скрипт)."""

from __future__ import annotations

import importlib.util
import json
import re
import shutil
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
_spec = importlib.util.spec_from_file_location("ezfc_build_form", ROOT / "scripts" / "ezfc_build_form.py")
ezfc_build = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(ezfc_build)

TEMPLATE_PATH = ROOT / "scripts" / "ezfc_form_template_79.json"
APPLY_PHP_PATH = ROOT / "scripts" / "ezfc_build_apply.php"
FORMS_DIR = ROOT / "wp-plugin" / "forms"


def _sample_spec() -> dict:
    return {
        "name": "CalcTestBuilder",
        "slug": "test_builder",
        "fields": [
            {
                "name": "numN",
                "type": "numbers",
                "label": "Тираж",
                "required": True,
                "value": "1",
                "min": "1",
                "max": "10000000",
                "get": "numN",
            },
            {
                "name": "dpdMaterial",
                "type": "dropdown",
                "label": "Материал",
                "required": True,
                "get": True,
                "options_from": {
                    "file": "materials/hardsheet.json",
                    "sections": ["PVCUnextStrong"],
                },
            },
            {
                "name": "grpExtra",
                "type": "group",
                "title": "Дополнительно",
            },
            {
                "name": "numW",
                "type": "num",
                "label": "Ширина, мм",
                "group": "grpExtra",
                "value": "100",
            },
            {
                "name": "chkLamination",
                "type": "checkbox",
                "options": [{"value": "1", "text": "Ламинация"}],
                "conditional": [
                    {
                        "action": "show",
                        "target": "numW",
                        "operator": "checked",
                        "value": "1",
                    }
                ],
            },
            {
                "name": "setMaxSize",
                "type": "set",
                "set_operator": "max",
                "set": ["numN", "numW"],
            },
            {
                "name": "hidMeta",
                "type": "hidden",
            },
        ],
    }


def test_template_79_matches_reference_structure():
    tpl = ezfc_build.load_template(TEMPLATE_PATH)
    assert tpl["meta"]["source_form_id"] == 79
    assert len(tpl["form_options"]) == 192
    assert 10 not in tpl["element_types"].values()

    by_name = {el["name"]: el for el in tpl["result_elements"]}
    expected_result = {
        "grpCalc",
        "grpPrice",
        "grpPriceManager",
        "hdgBase",
        "sbtPriceTotalManager",
        "sbtPriceManager",
        "grpPriceDiscount",
        "sbtPriceTotalDiscount",
        "sbtPriceDiscount",
        "htmCost",
        "grpTime",
        "htmTime",
        "rdoModeProduction",
        "sbtWeightTotal",
        "grpMaterial",
        "htmMaterial",
    }
    assert set(by_name) == expected_result

    # Скрытые элементы скидки — только через hidden="1" и calculate_when_hidden="1", без e_id=10
    for hidden_name in ("sbtPriceTotalDiscount", "sbtPriceDiscount"):
        el = by_name[hidden_name]
        assert el["e_id"] == 15
        assert el["data"]["hidden"] == "1"
        assert el["data"]["calculate_when_hidden"] == "1"

    assert by_name["hdgBase"]["data"]["title"] == "цена"
    assert by_name["htmTime"]["data"]["wrapper_class"] == ""
    assert "porto-tooltip inline htmTime" in by_name["htmTime"]["data"]["html"]
    assert "read_maxdiscount" in by_name["htmCost"]["data"]["html"]
    assert "{{sbtPriceTotalDiscount}}" in by_name["htmCost"]["data"]["html"]
    assert "read_material" in by_name["htmMaterial"]["data"]["html"]
    assert "data-material-table" in by_name["htmMaterial"]["data"]["html"]

    for preset_name, preset in tpl["field_presets"].items():
        assert preset["e_id"] != 10, f"пресет {preset_name} не должен использовать e_id=10"
    assert tpl["field_presets"]["hidden"]["data"]["hidden"] == "1"
    assert tpl["field_presets"]["hidden"]["data"]["calculate_when_hidden"] == "1"


def test_resolve_options_from_materials_and_equipment():
    pvc = ezfc_build.resolve_options_from(
        {"file": "materials/hardsheet.json", "sections": ["PVCUnextStrong"]}
    )
    assert len(pvc) >= 3
    values = [o["value"] for o in pvc]
    assert "Default" not in values
    assert "PVC3" in values
    pvc3 = next(o for o in pvc if o["value"] == "PVC3")
    assert pvc3["text"] == "ПВХ 3 мм"
    assert [o["id"] for o in pvc] == [str(i) for i in range(1, len(pvc) + 1)]

    puzzles = ezfc_build.resolve_options_from(
        {
            "file": "materials/puzzle.json",
            "section": "Puzzle",
            "prepend": [{"value": "none", "text": "Без пазла"}],
        }
    )
    assert puzzles[0] == {"id": "1", "value": "none", "text": "Без пазла"}
    assert any(o["value"] == "Puzzle300420" and "300" in o["text"] for o in puzzles)

    lasers = ezfc_build.resolve_options_from("equipment/laser.json")
    assert any(o["value"] == "Qualitech11G1290" and "Qualitech" in o["text"] for o in lasers)


def test_resolve_options_from_errors(tmp_path):
    with pytest.raises(ValueError, match="не найдена"):
        ezfc_build.resolve_options_from("materials/puzzle.json:NoSuchSection")
    with pytest.raises(ValueError, match="выходит за пределы"):
        ezfc_build.resolve_options_from({"file": "../app.py"})
    with pytest.raises(ValueError, match="не найдены"):
        ezfc_build.resolve_options_from(
            {"file": "materials/puzzle.json", "section": "Puzzle", "include": ["MissingCode"]}
        )


def test_build_form_package_structure_positions_and_refs():
    spec = _sample_spec()
    spec["mode_options"] = [
        {"value": "0", "text": "дешевле"},
        {"value": "1", "text": "стандарт"},
        {"value": "2", "text": "быстрее"},
    ]
    pkg = ezfc_build.build_form_package(spec, check_js=False)
    assert pkg["action"] == "build"
    assert pkg["form"]["name"] == "CalcTestBuilder"
    assert len(pkg["form_options"]) == 192

    elements = pkg["elements"]
    positions = [el["position"] for el in elements]
    assert sorted(positions) == list(range(1, len(elements) + 1))

    by_name = {el["name"]: el for el in elements}
    assert by_name["Загрузчик калькулятора"]["position"] == len(elements)
    assert by_name["htmMaterial"]["position"] == 1
    assert by_name["grpParam"]["position"] > by_name["grpCalc"]["position"]

    # Топологический порядок: любая родительская группа встречается в списке раньше детей.
    seen_groups = {"0"}
    for el in elements:
        assert el["group_name"] in seen_groups, f"группа {el['group_name']} должна идти до {el['name']}"
        if el["e_id"] == 25:
            seen_groups.add(el["name"])

    # Тип hidden (e_id 10) не используется нигде.
    assert all(el["e_id"] != 10 for el in elements)
    assert by_name["hidMeta"]["data"]["hidden"] == "1"
    assert by_name["hidMeta"]["data"]["calculate_when_hidden"] == "1"

    # Настройки cjsCalc read_file и GET
    cjs = by_name["cjsCalc"]["data"]
    assert cjs["custom_calculation"] == ""
    assert cjs["custom_calculation_function_read_file"] == "1"
    assert (
        cjs["custom_calculation_function_filename"]
        == "{{abspath}}wp-content/plugins/insain-calc-bridge/forms/test_builder.js"
    )
    assert by_name["dpdMaterial"]["data"]["GET"] == "dpdMaterial"
    assert by_name["dpdMaterial"]["data"]["GET_check_option_value"] == "index"
    assert by_name["rdoModeProduction"]["data"]["GET"] == "rdoModeProduction"
    assert by_name["rdoModeProduction"]["data"]["GET_check_option_value"] == "value"
    assert by_name["rdoModeProduction"]["data"]["preselect"] == "1"

    # Ссылки на элементы по именам в refs
    assert by_name["chkLamination"]["refs"] == [
        {"path": ["conditional", 0, "target"], "target_name": "numW"}
    ]
    assert by_name["setMaxSize"]["refs"] == [
        {"path": ["set", 0, "target"], "target_name": "numN"},
        {"path": ["set", 1, "target"], "target_name": "numW"},
    ]
    assert by_name["sbtPriceDiscount"]["refs"] == [
        {"path": ["calculate", 0, "target"], "target_name": "sbtPriceTotalDiscount"},
        {"path": ["calculate", 1, "target"], "target_name": "numN"},
    ]


@pytest.mark.parametrize(
    "mutator, expected_err",
    [
        (lambda s: s.update({"slug": "Bad-Slug"}), "некорректный slug"),
        (lambda s: s.update({"fields": s["fields"][1:]}), "количества"),
        (lambda s: s["fields"].append({"name": "numN", "type": "numbers"}), "дублирующее"),
        (lambda s: s["fields"][0].update({"group": "grpMissing"}), "не объявлена"),
        (
            lambda s: s["fields"][4]["conditional"][0].update({"target": "noSuchField"}),
            "несуществующий элемент",
        ),
        (lambda s: s["fields"][1].update({"get_check": "bad"}), "GET_check"),
    ],
)
def test_build_form_validation_errors(mutator, expected_err):
    spec = _sample_spec()
    mutator(spec)
    with pytest.raises(ValueError, match=expected_err):
        ezfc_build.build_form_package(spec, check_js=False)


def test_build_form_rejects_group_cycle():
    spec = _sample_spec()
    spec["fields"].append({"name": "grpA", "type": "group", "group": "grpB"})
    spec["fields"].append({"name": "grpB", "type": "group", "group": "grpA"})
    with pytest.raises(ValueError, match="циклическая"):
        ezfc_build.build_form_package(spec, check_js=False)


def test_validate_read_file_js_patterns_and_stray_placeholders(tmp_path):
    spec = _sample_spec()
    good_js = """
var qty = {{numN}};
var matEl = ezfc_functions.get_element_id_by_name(__form_id__, 'DPDMATERIAL');
var matId = ezfc_functions.get_value_from(matEl, true)[0];
insaincalc.syncUrl({ numN: qty });
insaincalc.calcApi('test_builder', { quantity: qty, material_id: matId }).then(function (c) {
    insaincalc.showResult(c, qty, __form_id__);
});
"""
    js_file = tmp_path / "test_builder.js"
    js_file.write_text(good_js, encoding="utf-8")
    pkg = ezfc_build.build_form_package(spec, js_path=js_file)
    assert pkg["slug"] == "test_builder"

    # Лишний {{…}} обнуляет расчёт в ezFC — генератор и валидатор обязаны падать.
    for bad_js in (
        "var x = {{unknownField}};",
        "var x = {{numN }};",
        "var x = {{ }};",
        "var x = {{numN;\n",
    ):
        with pytest.raises(ValueError):
            ezfc_build.validate_read_file_js(bad_js, ["numN", "dpdMaterial"])

    # Несуществующее имя в get_element_id_by_name
    with pytest.raises(ValueError, match="отсутствующие элементы"):
        ezfc_build.validate_read_file_js(
            "var id = ezfc_functions.get_element_id_by_name(__form_id__, 'missing');",
            ["numN", "dpdMaterial"],
        )

    # Хардкод numeric id в новом read_file-JS запрещён
    with pytest.raises(ValueError, match="нельзя хардкодить id"):
        ezfc_build.validate_read_file_js(
            "var v = ezfc_functions.get_value_from(3104, true)[0];",
            ["numN", "dpdMaterial"],
            forbid_hardcoded_ids=True,
        )


def test_wp_plugin_forms_js_have_no_stray_double_braces():
    """В read_file-JS лишний {{…}} обнуляет весь расчёт в ezFC (return 0)."""
    files = sorted(FORMS_DIR.glob("*.js"))
    assert files, f"не найдены *.js в {FORMS_DIR}"
    valid_ident = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")
    bad = []
    for path in files:
        text = path.read_text(encoding="utf-8")
        for match in re.finditer(r"\{\{([^\n}]*)\}\}", text):
            inner = match.group(1)
            if not valid_ident.match(inner):
                bad.append(f"{path.name}: недопустимый плейсхолдер {match.group(0)!r}")
        cleaned = re.sub(r"\{\{([^\n}]*)\}\}", "", text)
        if "{{" in cleaned or "}}" in cleaned:
            bad.append(f"{path.name}: незакрытые скобки {{ / }}")
    assert not bad, "\n".join(bad)


def test_update_options_cli(tmp_path):
    spec = _sample_spec()
    spec_path = tmp_path / "spec.json"
    out_path = tmp_path / "upd.json"
    spec_path.write_text(json.dumps(spec, ensure_ascii=False), encoding="utf-8")

    code = ezfc_build.main(
        [str(spec_path), "--update-options", "--form-id", "99", "--elements", "dpdMaterial", "--out", str(out_path)]
    )
    assert code == 0
    pkg = json.loads(out_path.read_text(encoding="utf-8"))
    assert pkg["action"] == "update-options"
    assert pkg["form_id"] == 99
    assert list(pkg["elements"].keys()) == ["dpdMaterial"]
    assert pkg["elements"]["dpdMaterial"]["e_id"] == 4
    assert any(o["value"] == "PVC3" for o in pkg["elements"]["dpdMaterial"]["options"])


def test_php_apply_script_syntax_and_safety():
    php_src = APPLY_PHP_PATH.read_text(encoding="utf-8")
    assert php_src.startswith("<?php")
    for token in (
        "ABSPATH",
        "JSON_UNESCAPED_UNICODE",
        "ezfc_form_id",
        "allow-published",
        "dry-run",
        "apply",
        "update-options",
        "restore",
        "wp_cache_flush()",
    ):
        assert token in php_src

    assert php_src.count("{") == php_src.count("}")

    php_bin = shutil.which("php")
    if php_bin:
        res = subprocess.run([php_bin, "-l", str(APPLY_PHP_PATH)], capture_output=True, text=True, check=False)
        assert res.returncode == 0, res.stderr or res.stdout
        assert "No syntax errors detected" in res.stdout
