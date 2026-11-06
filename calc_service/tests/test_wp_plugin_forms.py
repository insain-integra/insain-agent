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


def test_mug_keeps_mode_zero():
    """Режим 0 («дешевле») не должен превращаться в 1 через ||."""
    text = (FORMS / "mug.js").read_text(encoding="utf-8")
    assert "get_value_from(1617, true)[0]) || 1" not in text
    assert "modeRaw == null || isNaN(modeNum)" in text
    assert "rdoModeProduction: mode" in text
