"""Контракт custom JS форм в wp-plugin/forms: calcApi и syncUrl."""

from __future__ import annotations

import json
import re
import subprocess
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


# Оба калькулятора магнитов живут в test_magnets.py, не в test_<slug>.py.
SLUG_TEST_FILE = {
    "magnet_acrylic": "test_magnets.py",
}


def test_form_js_has_form_default_reference():
    """У формы на API есть эталон JS на дефолте боевой формы: REF_FORM_DEFAULT в test_<slug>.py."""
    missing = []
    for path in sorted(FORMS.glob("*.js")):
        slug = path.stem
        test = TESTS / SLUG_TEST_FILE.get(slug, f"test_{slug}.py")
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


def test_print_sheet_js_branches_by_dpd_laminat_with_form_id():
    """Форма 19/копия 107 определяется через __form_id__ и dpdLaminat, без null и без хардкода id формы."""
    text = (FORMS / "print_sheet.js").read_text(encoding="utf-8")
    assert "ezfc_functions.get_element_id_by_name(__form_id__, 'dpdLaminat')" in text
    assert "get_element_id_by_name(null," not in text
    assert "__form_id__ == 19" not in text and "__form_id__ === 19" not in text
    assert "__form_id__ == 107" not in text and "__form_id__ === 107" not in text
    assert "{{numCrease}}" not in text
    for el_id in (99, 100, 101, 102, 103, 400, 401, 402, 419, 519, 661, 663, 664, 665, 666, 667, 668):
        assert f"get_value_from({el_id}" in text
    assert "insaincalc.calcApi('print_sheet'" in text
    assert "insaincalc.syncUrl(" in text
    assert "insaincalc.showResult(" in text


def _cards_form_posted(radio):
    """Прогон forms/cards.js. radio — то, что вернул get_value_from элемента режима.

    get_element_id_by_name для режима отдаёт 4292 — id радио на копии 117.
    Скрипт копии подменяет только get_value_from, поэтому литерал 2311 в
    getElementById на копии input не найдёт.
    """
    src = (FORMS / "cards.js").read_text(encoding="utf-8").replace("{{numN}}", "100")
    harness = (
        "var radio = " + json.dumps(radio) + ";\n"
        "var __form_id__ = 117;\n"
        "var checkedId = null;\n"
        "var document = {\n"
        "  getElementById: function (id) {\n"
        "    return { set checked(v) { if (v) checkedId = id; } };\n"
        "  }\n"
        "};\n"
        "var ezfc_functions = {\n"
        "  get_value_from: function (id, calc, third, opts) {\n"
        "    if (opts && opts.return_value === 'index') {\n"
        "      if (id === 2289 || id === 2290 || id === 2288) return [0];\n"
        "      return '';\n"
        "    }\n"
        "    if (id === 2311) return radio;\n"
        "    if (id === 2289) return ['White'];\n"
        "    if (id === 2290) return ['gloss'];\n"
        "    return '';\n"
        "  },\n"
        "  get_element_id_by_name: function (formId, name) {\n"
        "    return name === 'rdoModeProduction' ? 4292 : 0;\n"
        "  }\n"
        "};\n"
        "var posted = null;\n"
        "var synced = null;\n"
        "var insaincalc = {\n"
        "  syncUrl: function (obj) { synced = obj; },\n"
        "  calcApi: function (slug, body) {\n"
        "    posted = { slug: slug, body: body };\n"
        "    return { then: function () { return { catch: function () {} }; } };\n"
        "  },\n"
        "  showResult: function () {},\n"
        "  showError: function () {}\n"
        "};\n"
        + src
        + "\nprocess.stdout.write(JSON.stringify({\n"
        "  mode: posted && posted.body.mode,\n"
        "  url: synced && synced.rdoModeProduction,\n"
        "  slug: posted && posted.slug,\n"
        "  checked: checkedId\n"
        "}));\n"
    )
    proc = subprocess.run(
        ["node", "-e", harness],
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    assert proc.returncode == 0, proc.stderr
    return json.loads(proc.stdout)


def test_cards_js_empty_radio_is_mode_one():
    """Форма 56: пустой radio режима отдаёт число 0. Это не «дешевле» — mode 1, как calcPlasticCards.

    Выбранные значения приходят массивом и сохраняются. Массив [0] не схлопывается в 1.
    """
    text = (FORMS / "cards.js").read_text(encoding="utf-8")
    assert "get_value_from(2311, true)" in text
    assert "querySelector" not in text
    assert not re.search(r"\bprice\s*=", text)

    empty = _cards_form_posted(0)
    assert empty["slug"] == "cards"
    assert empty["mode"] == 1
    assert empty["url"] == 1

    assert _cards_form_posted("0")["mode"] == 1
    assert _cards_form_posted(None)["mode"] == 1
    assert _cards_form_posted("")["mode"] == 1

    standard = _cards_form_posted([1])
    assert standard["mode"] == 1
    assert standard["url"] == 1
    fast = _cards_form_posted([2])
    assert fast["mode"] == 2
    assert fast["url"] == 2
    assert _cards_form_posted([0])["mode"] == 0
    assert _cards_form_posted([0])["url"] == 0


def test_cards_js_empty_radio_checks_standard_option():
    """Скаляр 0 и «0» уже дают mode 1. Радио «стандарт» (индекс 0) надо отметить.

    На боевой это ezfc_element-2311-0 с data-value 1. Id берётся по имени поля:
    на копии 117 радио — 4292. Выбранные [1] и [2] не переотмечаем.
    """
    text = (FORMS / "cards.js").read_text(encoding="utf-8")
    assert "querySelector" not in text
    assert "ezfc_element-2311" not in text
    assert not re.search(r"\bprice\s*=", text)

    for raw in (0, "0"):
        posted = _cards_form_posted(raw)
        assert posted["mode"] == 1
        assert posted["url"] == 1
        assert posted["checked"] == "ezfc_element-4292-0", raw

    for raw in ([1], [2], [0], None):
        assert _cards_form_posted(raw)["checked"] is None, raw


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
