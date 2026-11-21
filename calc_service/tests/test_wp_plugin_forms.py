"""Контракт custom JS форм в wp-plugin/forms: calcApi и syncUrl."""

from __future__ import annotations

import re
from pathlib import Path

FORMS = Path(__file__).resolve().parents[2] / "wp-plugin" / "forms"


def test_form_js_calls_calc_api_and_sync_url():
    files = sorted(FORMS.glob("*.js"))
    assert files, f"нет *.js в {FORMS}"
    missing = []
    for path in files:
        text = path.read_text(encoding="utf-8")
        if "insaincalc.calcApi(" not in text:
            missing.append(f"{path.name}: нет insaincalc.calcApi(")
        if "insaincalc.syncUrl(" not in text:
            missing.append(f"{path.name}: нет insaincalc.syncUrl(")
    assert not missing, "\n".join(missing)


TESTS = Path(__file__).resolve().parent / "test_calculators"

# Копии приняты до правила «эталон на дефолте формы» (08.11.2026); список только сокращается.
NO_FORM_DEFAULT_YET = {"embossing", "mug", "plaque", "uv_print"}


def test_form_js_has_form_default_reference():
    """У формы на API есть эталон JS на дефолте боевой формы: REF_FORM_DEFAULT в test_<slug>.py."""
    missing = []
    for path in sorted(FORMS.glob("*.js")):
        slug = path.stem
        test = TESTS / f"test_{slug}.py"
        has = test.is_file() and "REF_FORM_DEFAULT" in test.read_text(encoding="utf-8")
        if has and slug in NO_FORM_DEFAULT_YET:
            missing.append(f"{slug}: кейс дефолта есть — убрать из NO_FORM_DEFAULT_YET")
        elif not has and slug not in NO_FORM_DEFAULT_YET:
            missing.append(f"{slug}: нет REF_FORM_DEFAULT в {test.name} (skill ezfc-form-to-api, шаг 1)")
    assert not missing, "\n".join(missing)


def test_sticker_js_posts_wide_print():
    """Форма 22: широкие принтеры и ламинация 1064 уходят в calcApi, не только в URL."""
    text = (FORMS / "sticker.js").read_text(encoding="utf-8")
    assert "var wideLaminat = ezfc_functions.get_value_from(1064, true)[0];" in text
    assert (
        "printerId === 'Technojet160ECO' || printerId === 'HPLatex335' "
        "|| printerId === 'TechnojetXR720'"
    ) in text
    assert re.search(
        r"printerId === 'Technojet160ECO' && wideLaminat && String\(wideLaminat\) !== 'No'\) \{\s*"
        r"params\.lamination_id = wideLaminat;",
        text,
    )
    assert "printerId === 'KMBizhubC220'" in text
    assert "params.lamination_id = sheetLaminat;" in text
    assert "insaincalc.calcApi('sticker'" in text
    assert not re.search(r"\bprice\s*=", text)


def test_sticker_pack_js_branches_on_format_field():
    """Форма 29: свои id и ветка по полю dpdFormat, id формы 22 не подменяют её."""
    text = (FORMS / "sticker.js").read_text(encoding="utf-8")
    assert "get_element_id_by_name(__form_id__, 'dpdFormat')" in text
    assert "/* form 29 */" in text
    assert "/* form 22 */" in text
    assert "ezfc_functions.get_value_from(1062, true)[0]" in text
    assert "ezfc_functions.get_value_from(1039, true)[0]" in text
    assert "ezfc_functions.get_value_from(1056, true)[0]" in text
    assert "is_find_mark: true" in text
    assert "size_item: 50" in text
    assert "density: 1" in text
    assert "var wideLaminat = ezfc_functions.get_value_from(1064, true)[0];" in text
    assert "querySelector" not in text
    assert not re.search(r"\bprice\s*=", text)


def test_laser_js_calls_laser_api():
    """Форма 28: материал, резка и режим уходят в calcApi('laser'), без своей цены."""
    text = (FORMS / "laser.js").read_text(encoding="utf-8")
    assert "insaincalc.calcApi('laser'" in text
    assert "insaincalc.syncUrl(" in text
    assert "insaincalc.showResult(" in text
    assert "ezfc_functions.get_value_from(989, true)" in text
    assert "ezfc_functions.get_value_from(985, true)" in text
    assert "ezfc_functions.get_value_from(1006, true)[0]" in text
    assert "material_id: materialId" in text
    assert "String(cut) !== 'noCut'" in text
    assert "is_cut_laser" in text
    assert "querySelector" not in text
    assert "calcLaser" not in text
    assert not re.search(r"\bprice\s*=", text)


def test_print_roll_js_writes_eyelet_step_cm_and_reads_radio_zero():
    """Ссылка: шаг люверсов в см поля, радио value 0 не теряется. sameEdges не меняется."""
    text = (FORMS / "print_roll.js").read_text(encoding="utf-8")
    assert "numStepEyelets: stepAll / 10" in text
    assert "numStepEyeletsTop: stepTop / 10" in text
    assert "numStepEyeletsRight: stepRight / 10" in text
    assert "numStepEyeletsBottom: stepBottom / 10" in text
    assert "numStepEyeletsLeft: stepLeft / 10" in text
    assert "processUrl === '0'" in text
    assert "processListed = [1]" in text
    assert "sameEdges = processNum === 1" in text
    assert "insaincalc.calcApi('print_roll'" in text
    assert "querySelector" not in text
    assert not re.search(r"\bprice\s*=", text)


def test_forms_keep_mode_zero():
    """Режим 0 («дешевле») не превращается в 1 через ||, даже если сейчас в форме его нет."""
    bad = []
    for path in sorted(FORMS.glob("*.js")):
        text = path.read_text(encoding="utf-8")
        if "rdoModeProduction" not in text:
            continue
        if re.search(r"get_value_from\(\d+, true\)\[0\]\)\s*\|\|\s*1", text):
            bad.append(f"{path.name}: режим через || 1")
        elif "modeRaw == null || isNaN(modeNum)" not in text:
            bad.append(f"{path.name}: нет проверки пустого режима, как в mug.js")
    assert not bad, "\n".join(bad)
