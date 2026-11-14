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
