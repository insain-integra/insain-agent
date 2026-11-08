"""Контракт custom JS форм в wp-plugin/forms: calcApi и syncUrl."""

from __future__ import annotations

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


def test_mug_keeps_mode_zero():
    """Режим 0 («дешевле») не должен превращаться в 1 через ||."""
    text = (FORMS / "mug.js").read_text(encoding="utf-8")
    assert "get_value_from(1617, true)[0]) || 1" not in text
    assert "modeRaw == null || isNaN(modeNum)" in text
    assert "rdoModeProduction: mode" in text
