"""Генератор пакетов сборки и обновления опций форм ezFC по эталону формы 79.

Формирует детерминированный JSON-пакет для scripts/ezfc_build_apply.php:
  1) сборка новой формы из декларативной JSON-спеки и шаблона формы 79:
     python scripts/ezfc_build_form.py spec.json --out /tmp/ezfc-build-pkg.json
  2) пакет обновления опций dropdown/radio/checkbox существующей формы из JSON-каталогов:
     python scripts/ezfc_build_form.py spec.json --update-options --form-id 99 --out /tmp/ezfc-upd.json
"""

from __future__ import annotations

import argparse
import copy
import json
import re
import sys
from pathlib import Path
from typing import Any, Iterable

import json5

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_TEMPLATE = ROOT / "scripts" / "ezfc_form_template_79.json"
DEFAULT_DATA_DIR = ROOT / "calc_service" / "data"
DEFAULT_FORMS_DIR = ROOT / "wp-plugin" / "forms"

SLUG_RE = re.compile(r"^[a-z][a-z0-9_]*$")
NAME_RE = re.compile(r"^[A-Za-z0-9_.-]+$")
PLACEHOLDER_RE = re.compile(r"\{\{([^\n}]*)\}\}")
GET_VALUE_FROM_NUMERIC_RE = re.compile(r"get_value_from\(\s*(\d+)")
GET_EL_BY_NAME_RE = re.compile(
    r"get_element_id_by_name\(\s*([^,)\n]+?)\s*(?:,\s*(['\"])([^'\"\n]+)\2\s*)?\)"
)

TYPE_ALIASES = {
    "num": "numbers",
    "numbers": "numbers",
    "dropdown": "dropdown",
    "radio": "radio",
    "checkbox": "checkbox",
    "hidden": "hidden",
    "set": "set",
    "group": "group",
    "html": "html",
    "heading": "heading",
    "fileupload": "fileupload",
    "subtotal": "subtotal",
    "custom_calculation": "custom_calculation",
    "cjsCalc": "custom_calculation",
}

GET_CHECKS = ("index", "value")
OPTION_TYPES = {"dropdown", "radio", "checkbox"}
FORBIDDEN_E_ID = 10  # Тип hidden (e_id 10) не используется на сайте.


def load_template(path: Path = DEFAULT_TEMPLATE) -> dict[str, Any]:
    """Загружает шаблон структуры формы 79."""
    if not path.is_file():
        raise FileNotFoundError(f"не найден файл шаблона: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def _as_ezfc_bool(value: Any, default: str = "0") -> str:
    if value is None:
        return default
    if isinstance(value, bool):
        return "1" if value else "0"
    s = str(value).strip().lower()
    if s in ("1", "true", "yes"):
        return "1"
    if s in ("0", "false", "no", ""):
        return "0"
    return str(value)


def _extract_item_label(item: dict[str, Any], key: str, label_field: str | None) -> str:
    if label_field:
        val = item.get(label_field)
        if isinstance(val, str) and val.strip():
            return val.strip()
        raise ValueError(f"у элемента '{key}' нет непустого поля '{label_field}'")
    for candidate in ("title", "name", "description"):
        val = item.get(candidate)
        if isinstance(val, str) and val.strip():
            return val.strip()
    raise ValueError(f"у элемента '{key}' нет title/name/description для подписи в UI")


def _is_section_dict(value: Any) -> bool:
    """Отличает секцию каталога (hardsheet.PVCUnextStrong) от плоской записи оборудования (laser.Qualitech11G1290)."""
    if not isinstance(value, dict):
        return False
    if "Default" in value and isinstance(value["Default"], dict):
        return True
    for sub_k, sub_v in value.items():
        if sub_k == "Default":
            continue
        if isinstance(sub_v, dict) and any(
            k in sub_v for k in ("title", "name", "description", "cost", "size", "density")
        ):
            return True
    return False


def _normalize_option_list(raw_options: list[dict[str, Any]], el_type: str) -> list[dict[str, str]]:
    result: list[dict[str, str]] = []
    for idx, opt in enumerate(raw_options, start=1):
        if not isinstance(opt, dict):
            raise ValueError(f"опция #{idx} должна быть объектом {{value, text}}")
        if "value" not in opt or "text" not in opt:
            raise ValueError(f"у опции #{idx} обязательны поля 'value' и 'text'")
        entry: dict[str, str] = {
            "id": str(opt.get("id") or idx),
            "value": str(opt["value"]),
            "text": str(opt["text"]),
        }
        if el_type in ("radio", "checkbox"):
            entry["image"] = str(opt.get("image", ""))
            entry["icon"] = str(opt.get("icon", ""))
        result.append(entry)
    return result


def resolve_options_from(
    options_spec: dict[str, Any] | str,
    data_dir: Path = DEFAULT_DATA_DIR,
    el_type: str = "dropdown",
) -> list[dict[str, str]]:
    """Собирает список опций ezFC из справочника calc_service/data/*.json."""
    if isinstance(options_spec, str):
        file_part, _, sec_part = options_spec.partition(":")
        cfg: dict[str, Any] = {"file": file_part}
        if sec_part:
            cfg["section"] = sec_part
    elif isinstance(options_spec, dict):
        cfg = options_spec
    else:
        raise ValueError("options_from должен быть строкой или объектом")

    rel_file = cfg.get("file")
    if not rel_file or not isinstance(rel_file, str):
        raise ValueError("в options_from не указано поле 'file'")

    base = data_dir.resolve()
    target_path = (base / rel_file).resolve()
    if not str(target_path).startswith(str(base)):
        raise ValueError(f"путь '{rel_file}' выходит за пределы {data_dir}")
    if not target_path.is_file():
        raise FileNotFoundError(f"справочник не найден: {target_path}")

    catalog = json5.loads(target_path.read_text(encoding="utf-8"))
    if not isinstance(catalog, dict):
        raise ValueError(f"файл {rel_file} должен содержать JSON-объект")

    requested_sections: list[str] | None = None
    if cfg.get("sections") is not None:
        if not isinstance(cfg["sections"], list) or not cfg["sections"]:
            raise ValueError("options_from.sections должен быть непустым списком")
        requested_sections = [str(s) for s in cfg["sections"]]
    elif cfg.get("section"):
        requested_sections = [str(cfg["section"])]

    exclude = {"Default"}
    if cfg.get("exclude"):
        exclude.update(str(x) for x in cfg["exclude"])

    include_list = [str(x) for x in cfg["include"]] if cfg.get("include") is not None else None
    label_field = cfg.get("label_field")
    value_prefix = str(cfg.get("value_prefix", ""))

    # Собираем плоский словарь {code: item_dict} из выбранных секций или плоского каталога.
    collected: dict[str, dict[str, Any]] = {}
    has_sections = any(_is_section_dict(v) for v in catalog.values())

    if has_sections:
        sections_to_scan = requested_sections if requested_sections is not None else list(catalog.keys())
        for sec in sections_to_scan:
            if sec not in catalog:
                raise ValueError(f"секция '{sec}' не найдена в {rel_file}")
            sec_val = catalog[sec]
            if not isinstance(sec_val, dict):
                raise ValueError(f"секция '{sec}' в {rel_file} не является объектом")
            for key, item in sec_val.items():
                if key in exclude or not isinstance(item, dict):
                    continue
                collected[key] = item
    else:
        if requested_sections is not None:
            raise ValueError(f"в плоском каталоге {rel_file} нет секций ({requested_sections})")
        for key, item in catalog.items():
            if key in exclude or not isinstance(item, dict):
                continue
            collected[key] = item

    ordered_keys: list[str]
    if include_list is not None:
        missing = [k for k in include_list if k not in collected]
        if missing:
            raise ValueError(f"позиции {missing} не найдены в {rel_file}")
        ordered_keys = include_list
    else:
        ordered_keys = list(collected.keys())

    resolved: list[dict[str, Any]] = []
    for item in cfg.get("prepend") or []:
        resolved.append(dict(item))

    for key in ordered_keys:
        label = _extract_item_label(collected[key], key, label_field)
        resolved.append({"value": f"{value_prefix}{key}", "text": label})

    for item in cfg.get("append") or []:
        resolved.append(dict(item))

    if not resolved:
        raise ValueError(f"из {rel_file} не выбрано ни одной опции")

    return _normalize_option_list(resolved, el_type)


def validate_read_file_js(
    js_text: str,
    element_names: Iterable[str],
    *,
    forbid_hardcoded_ids: bool = True,
    require_bridge: bool = False,
) -> list[str]:
    """Проверяет custom JS формы для режима read_file.

    В read_file-JS ezFC заменяет __form_id__ и {{name}} (без учёта регистра).
    Любой оставшийся {{…}} превращает расчёт в return 0.
    Рекомендуемый паттерн чтения остальных полей —
    ezfc_functions.get_element_id_by_name(__form_id__, '<name>').
    """
    names_lower = {str(n).lower(): str(n) for n in element_names}
    referenced: list[str] = []

    unknown_placeholders: list[str] = []
    for match in PLACEHOLDER_RE.finditer(js_text):
        raw = match.group(1)
        key = raw.strip()
        if not key or key != raw or key.lower() not in names_lower:
            unknown_placeholders.append(match.group(0))
        else:
            referenced.append(names_lower[key.lower()])
    if unknown_placeholders:
        raise ValueError(
            "неизвестные плейсхолдеры {{…}} в JS (ezFC обнулит расчёт): "
            + ", ".join(unknown_placeholders)
        )

    if "{{" in js_text or "}}" in js_text:
        # Все корректные пары уже сматчились выше; если остались одиночные/многострочные {{ — ошибка.
        cleaned = PLACEHOLDER_RE.sub("", js_text)
        if "{{" in cleaned or "}}" in cleaned:
            raise ValueError("незакрытые или многострочные скобки {{ / }} в JS")

    if forbid_hardcoded_ids:
        hardcoded = GET_VALUE_FROM_NUMERIC_RE.findall(js_text)
        if hardcoded:
            raise ValueError(
                "в новом read_file-JS нельзя хардкодить id в get_value_from("
                + ", ".join(hardcoded)
                + "); используйте ezfc_functions.get_element_id_by_name(__form_id__, '<name>')"
            )

    unknown_by_name: list[str] = []
    for match in GET_EL_BY_NAME_RE.finditer(js_text):
        first_arg = match.group(1).strip()
        second_arg = match.group(3)
        if second_arg is not None:
            if forbid_hardcoded_ids and first_arg != "__form_id__":
                raise ValueError(
                    f"первый аргумент get_element_id_by_name должен быть __form_id__, получено: {first_arg}"
                )
            target_name = second_arg
        else:
            # Одноаргументный вызов get_element_id_by_name('name')
            stripped = first_arg.strip("'\"")
            target_name = stripped
        if target_name.lower() not in names_lower:
            unknown_by_name.append(target_name)
        else:
            referenced.append(names_lower[target_name.lower()])
    if unknown_by_name:
        raise ValueError(
            "get_element_id_by_name ссылается на отсутствующие элементы: "
            + ", ".join(unknown_by_name)
        )

    if require_bridge:
        for required_call in ("insaincalc.calcApi(", "insaincalc.syncUrl(", "insaincalc.showResult("):
            if required_call not in js_text:
                raise ValueError(f"в JS отсутствует обязательный вызов {required_call}")

    return referenced


def _canonical_type(raw_type: str) -> str:
    if raw_type not in TYPE_ALIASES:
        raise ValueError(f"неподдерживаемый тип поля: '{raw_type}'")
    return TYPE_ALIASES[raw_type]


def _default_get_check(el_type: str, explicit_check: Any) -> str:
    if explicit_check is not None and str(explicit_check) != "":
        check = str(explicit_check)
        if check not in GET_CHECKS:
            raise ValueError(f"GET_check должен быть из {GET_CHECKS}, получено '{check}'")
        return check
    if el_type == "radio":
        return "value"
    return "index"


def _apply_field_overrides(
    data: dict[str, Any],
    field: dict[str, Any],
    el_type: str,
    el_name: str,
    data_dir: Path,
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    refs: list[dict[str, Any]] = []
    data["name"] = el_name

    if "label" in field:
        data["label"] = str(field["label"])
    if "title" in field:
        data["title"] = str(field["title"])
    if "tag" in field:
        data["tag"] = str(field["tag"])
    if "html" in field:
        data["html"] = str(field["html"])
    if "do_shortcode" in field:
        data["do_shortcode"] = _as_ezfc_bool(field["do_shortcode"], "0")
    if "required" in field:
        data["required"] = _as_ezfc_bool(field["required"], "0")
    if "columns" in field:
        data["columns"] = str(field["columns"])
    if "description" in field:
        data["description"] = str(field["description"])
    if "wrapper_class" in field:
        data["wrapper_class"] = str(field["wrapper_class"])
    if "wrapper_style" in field:
        data["wrapper_style"] = str(field["wrapper_style"])
    if "class" in field:
        data["class"] = str(field["class"])
    if "style" in field:
        data["style"] = str(field["style"])
    if "text_before" in field:
        data["text_before"] = str(field["text_before"])
    if "text_after" in field:
        data["text_after"] = str(field["text_after"])
    if "inline_calculation" in field:
        data["inline_calculation"] = str(field["inline_calculation"])
    if "inline" in field:
        data["inline"] = _as_ezfc_bool(field["inline"], "0")
    if "preselect" in field:
        data["preselect"] = str(field["preselect"])

    if el_type == "numbers":
        for k in ("value", "min", "max", "precision", "factor", "placeholder", "steps_slider", "steps_spinner"):
            if k in field:
                data[k] = str(field[k])
        if "read_only" in field:
            data["read_only"] = _as_ezfc_bool(field["read_only"], "0")

    # Скрытые элементы: всегда data.hidden="1" (+ calculate_when_hidden="1"), без e_id=10.
    if el_type == "hidden" or field.get("hidden"):
        data["hidden"] = "1"
        if el_type in ("hidden", "numbers", "subtotal", "set"):
            data["calculate_when_hidden"] = _as_ezfc_bool(field.get("calculate_when_hidden"), "1")
    elif "calculate_when_hidden" in field:
        data["calculate_when_hidden"] = _as_ezfc_bool(field["calculate_when_hidden"], "0")

    if "calculate_enabled" in field:
        data["calculate_enabled"] = _as_ezfc_bool(field["calculate_enabled"], "1")
    if "add_to_price" in field:
        data["add_to_price"] = _as_ezfc_bool(field["add_to_price"], "1")
    if "overwrite_price" in field:
        data["overwrite_price"] = _as_ezfc_bool(field["overwrite_price"], "0")

    # GET / GET_check_option_value
    if field.get("get") is True:
        data["GET"] = el_name
    elif isinstance(field.get("get"), str) and field["get"]:
        data["GET"] = field["get"]
    if el_type in OPTION_TYPES and (data.get("GET") or "get_check" in field):
        data["GET_check_option_value"] = _default_get_check(el_type, field.get("get_check"))

    # Опции для dropdown/radio/checkbox
    if el_type in OPTION_TYPES:
        if "options_from" in field:
            data["options"] = resolve_options_from(field["options_from"], data_dir=data_dir, el_type=el_type)
        elif "options" in field:
            if not isinstance(field["options"], list) or not field["options"]:
                raise ValueError(f"у поля '{el_name}' список options не должен быть пустым")
            data["options"] = _normalize_option_list(field["options"], el_type)
        else:
            raise ValueError(f"у поля '{el_name}' ({el_type}) нужно указать options или options_from")

    # Set-элемент: ссылки на целевые поля по именам
    if el_type == "set":
        if "set_operator" in field:
            data["set_operator"] = str(field["set_operator"])
        targets = field.get("set") or []
        if not isinstance(targets, list) or not targets:
            raise ValueError(f"у set-элемента '{el_name}' должен быть непустой список 'set'")
        set_rows = []
        for idx, t in enumerate(targets):
            target_name = t["target"] if isinstance(t, dict) else str(t)
            set_rows.append({"target": "0"})
            refs.append({"path": ["set", idx, "target"], "target_name": target_name})
        data["set"] = set_rows

    # Условия conditional по именам полей
    if "conditional" in field:
        conds = field["conditional"]
        if not isinstance(conds, list) or not conds:
            raise ValueError(f"у поля '{el_name}' conditional должен быть непустым списком")
        built_conds = []
        for idx, c in enumerate(conds):
            row = {
                "action": str(c.get("action", "0")),
                "target": "0",
                "compare_value_first": "0",
                "operator": str(c.get("operator", "0")),
                "value": str(c.get("value", "")),
                "target_value": str(c.get("target_value", "")),
                "redirect": str(c.get("redirect", "")),
                "option_index_value": str(c.get("option_index_value", "")),
            }
            target_name = c.get("target")
            if target_name and str(target_name) != "0":
                refs.append({"path": ["conditional", idx, "target"], "target_name": str(target_name)})
            cmp_first = c.get("compare_value_first")
            if cmp_first and str(cmp_first) != "0":
                refs.append(
                    {"path": ["conditional", idx, "compare_value_first"], "target_name": str(cmp_first)}
                )
            if "compare_value" in c and isinstance(c["compare_value"], list):
                row["compare_value"] = []
                for c_idx, cmp_target in enumerate(c["compare_value"]):
                    row["compare_value"].append("0")
                    if cmp_target and str(cmp_target) != "0":
                        refs.append(
                            {
                                "path": ["conditional", idx, "compare_value", c_idx],
                                "target_name": str(cmp_target),
                            }
                        )
            if "operator_chain" in c:
                row["operator_chain"] = [str(x) for x in c["operator_chain"]]
            if "value_chain" in c:
                row["value_chain"] = [str(x) for x in c["value_chain"]]
            built_conds.append(row)
        data["conditional"] = built_conds

    # Расчёты calculate по именам полей
    if "calculate" in field:
        calcs = field["calculate"]
        if not isinstance(calcs, list) or not calcs:
            raise ValueError(f"у поля '{el_name}' calculate должен быть непустым списком")
        built_calcs = []
        for idx, c in enumerate(calcs):
            row = {
                "prio": str(c.get("prio", "0")),
                "operator": str(c.get("operator", "0")),
                "target": "0",
                "use_calculated_target_value": _as_ezfc_bool(c.get("use_calculated_target_value"), "0"),
                "value": str(c.get("value", "")),
                "data": str(c.get("data", "")),
            }
            target_name = c.get("target")
            if target_name and str(target_name) != "0":
                refs.append({"path": ["calculate", idx, "target"], "target_name": str(target_name)})
            built_calcs.append(row)
        data["calculate"] = built_calcs

    return data, refs


def _topological_sort_elements(elements: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Сортирует элементы так, чтобы любая родительская группа шла до своих детей."""
    by_name = {el["name"]: el for el in elements}
    order_index = {el["name"]: i for i, el in enumerate(elements)}
    visited: dict[str, int] = {}  # 0 = visiting, 1 = done
    ordered: list[dict[str, Any]] = []

    def visit(name: str) -> None:
        state = visited.get(name)
        if state == 1:
            return
        if state == 0:
            raise ValueError(f"обнаружена циклическая вложенность групп с '{name}'")
        visited[name] = 0
        el = by_name[name]
        gname = el["group_name"]
        if gname != "0":
            if gname not in by_name:
                raise ValueError(f"группа '{gname}' элемента '{name}' не найдена в форме")
            visit(gname)
        visited[name] = 1
        ordered.append(el)

    for el in sorted(elements, key=lambda e: order_index[e["name"]]):
        visit(el["name"])
    return ordered


def build_form_package(
    spec: dict[str, Any],
    template: dict[str, Any] | None = None,
    data_dir: Path = DEFAULT_DATA_DIR,
    js_path: Path | None = None,
    check_js: bool = True,
) -> dict[str, Any]:
    """Валидирует спеку новой формы и строит пакет для ezfc_build_apply.php."""
    tpl = template or load_template()
    if not isinstance(spec, dict):
        raise ValueError("спека должна быть JSON-объектом")

    form_name = str(spec.get("name", "")).strip()
    if not form_name:
        raise ValueError("в спеке отсутствует непустое поле 'name'")
    if len(form_name) > 300:
        raise ValueError("имя формы не может быть длиннее 300 символов")

    slug = str(spec.get("slug", "")).strip()
    if not SLUG_RE.match(slug):
        raise ValueError(f"некорректный slug '{slug}' (ожидается ^[a-z][a-z0-9_]*$)")

    fields = spec.get("fields")
    if not isinstance(fields, list) or not fields:
        raise ValueError("в спеке должен быть непустой список 'fields'")

    reserved_result_names = {el["name"] for el in tpl["result_elements"]}
    reserved_fixed = {
        tpl["loader_element"]["name"],
        tpl["param_group"]["name"],
        tpl["calc_js_element"]["name"],
    } | reserved_result_names

    seen_lower: set[str] = set()
    for fixed_name in reserved_fixed:
        seen_lower.add(fixed_name.lower())

    user_elements: list[dict[str, Any]] = []
    group_names: set[str] = {"0", "grpParam"}
    user_names_set: set[str] = set()
    has_custom_fileupload = False

    # Сначала собираем имена всех полей и групп для валидации ссылок.
    parsed_fields: list[tuple[dict[str, Any], str, str, str]] = []
    for idx, field in enumerate(fields):
        if not isinstance(field, dict):
            raise ValueError(f"поле #{idx} должно быть объектом")
        el_name = str(field.get("name", "")).strip()
        if not el_name or not NAME_RE.match(el_name):
            raise ValueError(f"некорректное имя поля #{idx}: '{el_name}'")
        el_type = _canonical_type(str(field.get("type", "")))
        if el_name == tpl["fileupload_element"]["name"]:
            if el_type != "fileupload":
                raise ValueError(f"имя '{el_name}' зарезервировано для fileupload")
            has_custom_fileupload = True
        elif el_name.lower() in seen_lower:
            raise ValueError(f"дублирующее или зарезервированное имя поля: '{el_name}'")
        seen_lower.add(el_name.lower())
        user_names_set.add(el_name)
        gname = str(field.get("group", "grpParam")).strip() or "grpParam"
        if el_type == "group":
            group_names.add(el_name)
        parsed_fields.append((field, el_name, el_type, gname))

    qty_element = str(spec.get("qty_element", "numN"))
    if qty_element not in user_names_set:
        raise ValueError(
            f"в полях формы отсутствует поле количества '{qty_element}' "
            f"(нужно для расчёта штучной цены sbtPriceManager/sbtPriceDiscount)"
        )

    presets = tpl["field_presets"]
    for field, el_name, el_type, gname in parsed_fields:
        if gname not in group_names:
            raise ValueError(f"группа '{gname}' элемента '{el_name}' не объявлена в fields")
        preset = presets[el_type]
        e_id = int(preset["e_id"])
        assert e_id != FORBIDDEN_E_ID
        el_data = copy.deepcopy(preset["data"])
        el_data, refs = _apply_field_overrides(el_data, field, el_type, el_name, data_dir)
        user_elements.append(
            {
                "name": el_name,
                "e_id": e_id,
                "group_name": gname,
                "data": el_data,
                "refs": refs,
            }
        )

    # Формируем общий список элементов в порядке UI сверху вниз (position убывает: N .. 1).
    ui_order: list[dict[str, Any]] = [
        copy.deepcopy(tpl["loader_element"]),
        copy.deepcopy(tpl["param_group"]),
        *user_elements,
    ]
    if spec.get("include_fileupload", True) and not has_custom_fileupload:
        ui_order.append(copy.deepcopy(tpl["fileupload_element"]))

    calc_el = copy.deepcopy(tpl["calc_js_element"])
    calc_el["data"]["custom_calculation_function_read_file"] = "1"
    calc_el["data"]["custom_calculation_function_filename"] = (
        f"{{{{abspath}}}}wp-content/plugins/insain-calc-bridge/forms/{slug}.js"
    )
    calc_el["data"]["custom_calculation"] = ""
    ui_order.append(calc_el)

    result_els = copy.deepcopy(tpl["result_elements"])
    for rel in result_els:
        if rel["name"] == "rdoModeProduction" and spec.get("mode_options") is not None:
            mode_opts = _normalize_option_list(spec["mode_options"], "radio")
            if not mode_opts:
                raise ValueError("mode_options не должен быть пустым")
            rel["data"]["options"] = mode_opts
            if "mode_preselect" in spec:
                rel["data"]["preselect"] = str(spec["mode_preselect"])
            else:
                std_idx = next((i for i, o in enumerate(mode_opts) if o["value"] == "1"), 0)
                rel["data"]["preselect"] = str(std_idx)
        for ref in rel.get("refs", ()):
            if ref["target_name"] == "numN":
                ref["target_name"] = qty_element

    ui_order.extend(result_els)

    total = len(ui_order)
    for pos_idx, el in enumerate(ui_order):
        el["position"] = total - pos_idx
        el.setdefault("refs", [])

    all_names = {el["name"] for el in ui_order}
    # Валидация всех межэлементных ссылок (refs)
    for el in ui_order:
        for ref in el["refs"]:
            tname = ref["target_name"]
            if tname not in all_names:
                raise ValueError(
                    f"элемент '{el['name']}' ссылается на несуществующий элемент '{tname}'"
                )

    # Топологическая сортировка гарантирует вставку групп до их дочерних элементов
    ordered_elements = _topological_sort_elements(ui_order)

    # Проверка JS-файла формы (если передан явно или существует wp-plugin/forms/<slug>.js)
    resolved_js = js_path
    if resolved_js is None and check_js:
        candidate = DEFAULT_FORMS_DIR / f"{slug}.js"
        if candidate.is_file():
            resolved_js = candidate
    if resolved_js is not None:
        if not resolved_js.is_file():
            raise FileNotFoundError(f"JS-файл формы не найден: {resolved_js}")
        validate_read_file_js(
            resolved_js.read_text(encoding="utf-8"),
            all_names,
            forbid_hardcoded_ids=True,
        )

    return {
        "schema_version": 1,
        "action": "build",
        "slug": slug,
        "form": {
            "name": form_name,
            "data": copy.deepcopy(tpl["form_data"]),
        },
        "form_options": copy.deepcopy(tpl["form_options"]),
        "elements": ordered_elements,
    }


def build_update_options_package(
    spec: dict[str, Any],
    form_id: int,
    data_dir: Path = DEFAULT_DATA_DIR,
    element_names: list[str] | None = None,
) -> dict[str, Any]:
    """Строит пакет обновления массива options элементов dropdown/radio/checkbox."""
    if form_id <= 0:
        raise ValueError("--form-id должен быть положительным целым")
    slug = str(spec.get("slug", "")).strip()
    if not SLUG_RE.match(slug):
        raise ValueError(f"некорректный slug '{slug}'")

    fields = spec.get("fields")
    if not isinstance(fields, list) or not fields:
        raise ValueError("в спеке должен быть непустой список 'fields'")

    filter_set = set(element_names) if element_names else None
    updates: dict[str, dict[str, Any]] = {}
    tpl_types = load_template()["element_types"]

    for field in fields:
        el_name = str(field.get("name", "")).strip()
        if filter_set is not None and el_name not in filter_set:
            continue
        el_type = _canonical_type(str(field.get("type", "")))
        if el_type not in OPTION_TYPES:
            if filter_set is not None and el_name in filter_set:
                raise ValueError(
                    f"элемент '{el_name}' имеет тип '{el_type}', обновление опций поддерживается только для dropdown/radio/checkbox"
                )
            continue
        if "options_from" in field:
            opts = resolve_options_from(field["options_from"], data_dir=data_dir, el_type=el_type)
        elif "options" in field:
            opts = _normalize_option_list(field["options"], el_type)
        else:
            raise ValueError(f"у поля '{el_name}' нет options или options_from")
        updates[el_name] = {
            "e_id": int(tpl_types[el_type]),
            "options": opts,
        }

    if spec.get("mode_options") is not None and (
        filter_set is None or "rdoModeProduction" in filter_set
    ):
        updates["rdoModeProduction"] = {
            "e_id": int(tpl_types["radio"]),
            "options": _normalize_option_list(spec["mode_options"], "radio"),
        }

    if filter_set is not None:
        missing = sorted(filter_set - set(updates.keys()))
        if missing:
            raise ValueError(f"элементы {missing} не найдены среди полей с опциями в спеке")

    if not updates:
        raise ValueError("не найдено ни одного элемента dropdown/radio/checkbox для обновления опций")

    return {
        "schema_version": 1,
        "action": "update-options",
        "form_id": int(form_id),
        "slug": slug,
        "elements": updates,
    }


def _parse_elements_arg(raw_items: list[str]) -> list[str] | None:
    if not raw_items:
        return None
    out: list[str] = []
    for item in raw_items:
        for part in item.split(","):
            s = part.strip()
            if s:
                out.append(s)
    return out or None


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Генератор пакета сборки/обновления формы ezFC")
    ap.add_argument("spec", type=Path, help="JSON-спека формы")
    ap.add_argument("--template", type=Path, default=DEFAULT_TEMPLATE, help="Шаблон формы 79")
    ap.add_argument("--data-dir", type=Path, default=DEFAULT_DATA_DIR, help="Папка calc_service/data")
    ap.add_argument("--forms-js", type=Path, default=None, help="Путь к forms/<slug>.js для проверки")
    ap.add_argument("--no-check-js", action="store_true", help="Не искать wp-plugin/forms/<slug>.js автоматически")
    ap.add_argument("--update-options", action="store_true", help="Собрать пакет обновления опций")
    ap.add_argument("--form-id", type=int, default=0, help="ID существующей формы для --update-options")
    ap.add_argument("--elements", action="append", default=[], help="Имена элементов для --update-options")
    ap.add_argument("--out", type=Path, required=True, help="Куда сохранить пакет JSON")
    args = ap.parse_args(argv)

    try:
        spec = json.loads(args.spec.read_text(encoding="utf-8-sig"))
        if args.update_options:
            package = build_update_options_package(
                spec,
                form_id=args.form_id,
                data_dir=args.data_dir,
                element_names=_parse_elements_arg(args.elements),
            )
        else:
            template = load_template(args.template)
            package = build_form_package(
                spec,
                template=template,
                data_dir=args.data_dir,
                js_path=args.forms_js,
                check_js=not args.no_check_js,
            )
    except (ValueError, FileNotFoundError, json.JSONDecodeError) as exc:
        print(f"стоп: {exc}", file=sys.stderr)
        return 1

    args.out.write_text(json.dumps(package, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    if package["action"] == "build":
        print(f"build: {package['form']['name']} ({package['slug']}), элементов: {len(package['elements'])}, опций: {len(package['form_options'])}")
    else:
        print(f"update-options: форма {package['form_id']}, элементов: {', '.join(package['elements'])}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
