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

# Существующие чекбоксы в syncUrl, не уходящие в calcApi (приняты до регламента или ветка без порта).
# Для новых форм сюда не добавлять; при переносе/исправлении опции — убрать из списка.
SYNC_URL_ONLY_CHECKBOXES = {
    ("cards", "ckbVariables"): "calcPlasticCards и cards.py не считают переменные данные (только URL)",
    ("embossing", "ckbPacking"): "calcEmbossing и embossing.py не считают упаковку (только URL)",
    ("embossing", "ckbMaterialCustomer"): "calcEmbossing и embossing.py не считают материал заказчика (только URL)",
    ("sticker", "chkMark"): "в форме 22 не передаётся в calcApi (в sticker.py есть is_find_mark, не в tool_schema)",
    ("tablets", "ckbShaft"): "ветка isShaft не портирована в tablets.py (только URL)",
    ("tablets", "chkAdhesiveLayer"): "ветка chkAdhesiveLayer не портирована в tablets.py (только URL)",
}


# Оба калькулятора магнитов живут в test_magnets.py, не в test_<slug>.py.
SLUG_TEST_FILE = {
    "magnet_acrylic": "test_magnets.py",
    "magnet_laminated": "test_magnets.py",
}


def test_magnet_laminated_js_posts_postprint_flags():
    """Форма 54: нумерация, штрихкод и переменные данные уходят в calcApi, не только в URL."""
    text = (FORMS / "magnet_laminated.js").read_text(encoding="utf-8")
    assert "insaincalc.calcApi('magnet_laminated'" in text
    assert "insaincalc.syncUrl(" in text
    assert "insaincalc.showResult(" in text
    params_at = text.index("var params")
    sync_at = text.index("insaincalc.syncUrl(")
    body = text[params_at:sync_at]
    assert "is_number: isNumber" in body
    assert "is_barcode: isBarcode" in body
    assert "is_variables: isVariables" in body
    assert "ckbNumber" not in body
    assert "ckbNumber: isNumber ? 0 : ''" in text
    assert "ckbBarcode: isBarcode ? 0 : ''" in text
    assert "ckbVariables: isVariables ? 0 : ''" in text
    assert "querySelector" not in text
    assert not re.search(r"\bprice\s*=", text)


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


def _strip_js_comments(code: str) -> str:
    """Убирает // и /* ... */ комментарии, не трогая строковые литералы."""
    out: list[str] = []
    i = 0
    n = len(code)
    while i < n:
        ch = code[i]
        if ch in ("'", '"'):
            quote = ch
            out.append(ch)
            i += 1
            while i < n:
                c = code[i]
                out.append(c)
                if c == "\\" and i + 1 < n:
                    out.append(code[i + 1])
                    i += 2
                    continue
                if c == quote:
                    i += 1
                    break
                i += 1
            continue
        if ch == "/" and i + 1 < n and code[i + 1] == "/":
            i += 2
            while i < n and code[i] != "\n":
                i += 1
            continue
        if ch == "/" and i + 1 < n and code[i + 1] == "*":
            end = code.find("*/", i + 2)
            i = n if end == -1 else end + 2
            continue
        out.append(ch)
        i += 1
    return "".join(out)


def _extract_sync_url_calls(code: str) -> list[tuple[int, int, str]]:
    """Находит все вызовы insaincalc.syncUrl({...}) и возвращает (start, end, body)."""
    calls: list[tuple[int, int, str]] = []
    marker = "insaincalc.syncUrl("
    idx = 0
    n = len(code)
    while True:
        pos = code.find(marker, idx)
        if pos == -1:
            break
        open_paren = pos + len(marker) - 1
        depth = 0
        i = open_paren
        while i < n:
            ch = code[i]
            if ch in ("'", '"'):
                quote = ch
                i += 1
                while i < n:
                    if code[i] == "\\" and i + 1 < n:
                        i += 2
                        continue
                    if code[i] == quote:
                        break
                    i += 1
            elif ch == "(":
                depth += 1
            elif ch == ")":
                depth -= 1
                if depth == 0:
                    calls.append((pos, i + 1, code[open_paren + 1 : i]))
                    break
            i += 1
        idx = pos + len(marker)
    return calls


def _split_top_level_object_entries(obj_body: str) -> list[tuple[str, str]]:
    """Разбирает верхнеуровневые пары key: value из аргумента syncUrl({...})."""
    s = obj_body.strip()
    if s.startswith("{") and s.endswith("}"):
        s = s[1:-1]
    parts: list[str] = []
    cur: list[str] = []
    depth_paren = depth_brace = depth_bracket = 0
    i = 0
    n = len(s)
    while i < n:
        ch = s[i]
        if ch in ("'", '"'):
            quote = ch
            cur.append(ch)
            i += 1
            while i < n:
                cur.append(s[i])
                if s[i] == "\\" and i + 1 < n:
                    cur.append(s[i + 1])
                    i += 2
                    continue
                if s[i] == quote:
                    break
                i += 1
        elif ch == "(":
            depth_paren += 1
            cur.append(ch)
        elif ch == ")":
            depth_paren -= 1
            cur.append(ch)
        elif ch == "{":
            depth_brace += 1
            cur.append(ch)
        elif ch == "}":
            depth_brace -= 1
            cur.append(ch)
        elif ch == "[":
            depth_bracket += 1
            cur.append(ch)
        elif ch == "]":
            depth_bracket -= 1
            cur.append(ch)
        elif ch == "," and depth_paren == 0 and depth_brace == 0 and depth_bracket == 0:
            parts.append("".join(cur))
            cur = []
            i += 1
            continue
        else:
            cur.append(ch)
        i += 1
    if cur:
        parts.append("".join(cur))

    entries: list[tuple[str, str]] = []
    for part in parts:
        m = re.match(r"^\s*(?:['\"])?([A-Za-z0-9_]+)(?:['\"])?\s*:\s*([\s\S]+)$", part)
        if m:
            entries.append((m.group(1), m.group(2).strip()))
    return entries


def _checkbox_reaches_calc_api(branch_code: str, val_expr: str) -> bool:
    """Проверяет, что переменная или элемент чекбокса из syncUrl участвует в формировании calcApi."""
    m_ident = re.match(r"^([A-Za-z_]\w*)\b", val_expr)
    if m_ident:
        ident = m_ident.group(1)
        if re.search(rf"\b(?:var|let|const)\s+{re.escape(ident)}\b", branch_code):
            without_decl = re.sub(
                rf"\b(?:var|let|const)\s+{re.escape(ident)}\s*=[^;]*;",
                "",
                branch_code,
            )
            return bool(re.search(rf"\b{re.escape(ident)}\b", without_decl))

    m_el = re.search(r"get_value_from\(\s*(\d+)", val_expr)
    if m_el:
        el_id = m_el.group(1)
        assigned = re.findall(
            rf"\b(?:var|let|const)\s+([A-Za-z_]\w*)\s*=[^;]*get_value_from\(\s*{el_id}\b[^;]*;",
            branch_code,
        )
        for var_name in assigned:
            without_decl = re.sub(
                rf"\b(?:var|let|const)\s+{re.escape(var_name)}\s*=[^;]*;",
                "",
                branch_code,
            )
            if re.search(rf"\b{re.escape(var_name)}\b", without_decl):
                return True
        without_var_decls = re.sub(
            rf"\b(?:var|let|const)\s+[A-Za-z_]\w*\s*=[^;]*get_value_from\(\s*{el_id}\b[^;]*;",
            "",
            branch_code,
        )
        return bool(re.search(rf"get_value_from\(\s*{el_id}\b", without_var_decls))

    return False


def test_sync_url_checkboxes_reach_calc_api():
    """Каждый чекбокс ckb*/chk* в syncUrl либо уходит в calcApi, либо явно разрешён в SYNC_URL_ONLY_CHECKBOXES."""
    errors: list[str] = []
    seen_url_only: set[tuple[str, str]] = set()

    for path in sorted(FORMS.glob("*.js")):
        slug = path.stem
        code = _strip_js_comments(path.read_text(encoding="utf-8"))
        calls = _extract_sync_url_calls(code)
        for idx, (start, end, body) in enumerate(calls):
            prev_end = calls[idx - 1][1] if idx > 0 else 0
            next_start = calls[idx + 1][0] if idx + 1 < len(calls) else len(code)
            branch_code = code[prev_end:start] + code[end:next_start]

            for key, val_expr in _split_top_level_object_entries(body):
                if not re.match(r"^(?:ckb|chk)[A-Za-z0-9_]+$", key):
                    continue
                used = _checkbox_reaches_calc_api(branch_code, val_expr)
                pair = (slug, key)
                if used:
                    if pair in SYNC_URL_ONLY_CHECKBOXES:
                        errors.append(
                            f"{slug}.js: чекбокс {key} уже уходит в calcApi — убрать из SYNC_URL_ONLY_CHECKBOXES"
                        )
                else:
                    if pair in SYNC_URL_ONLY_CHECKBOXES:
                        seen_url_only.add(pair)
                    else:
                        errors.append(
                            f"{slug}.js: чекбокс {key} ({val_expr}) есть в syncUrl, но не участвует в calcApi"
                        )

    for pair in sorted(SYNC_URL_ONLY_CHECKBOXES):
        if pair not in seen_url_only:
            errors.append(f"{pair[0]}.js: {pair[1]} из SYNC_URL_ONLY_CHECKBOXES не найден как url-only в syncUrl")

    assert not errors, "\n".join(errors)
