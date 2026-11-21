"""Пакет для копии формы ezFC: JS из wp-plugin/forms/<slug>.js с id копии и GET-настройки.

Пакет применяет на сервере scripts/ezfc_copy_apply.php (skill ezfc-form-to-api, шаги 10 и 15).
Боевую форму скрипт не трогает: id подставляются только из таблицы «имя → id боевой → id копии».

    python scripts/ezfc_copy.py wp-plugin/forms/<slug>.js --live <id> --copy <copy> \
        --map <таблица шага 9> --get numN --get rdoModeProduction:value --out <пакет.json>

Таблица — вывод SQL шага 9 (`name<TAB>id_live<TAB>id_copy`). `--get имя[:index|value]` — имя элемента,
оно же имя GET-параметра; после двоеточия — GET_check_option_value.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

GET_VALUE_FROM = re.compile(r"get_value_from\(\s*(\d+)")
# Вторая форма того же slug: /* form 29 */ … /* /form */. Чужая ветка не переписывается.
FORM_BLOCK = re.compile(
    r"/\*\s*form\s+(\d+)\s*\*/(.*?)/\*\s*/form\s*\*/",
    re.DOTALL,
)
GET_CHECKS = ("index", "value")


def parse_id_map(text: str) -> dict[str, tuple[int, int]]:
    """Таблица шага 9 → {имя: (id боевой, id копии)}. Пустой или совпадающий id копии — ошибка."""
    result: dict[str, tuple[int, int]] = {}
    for line in text.splitlines():
        cells = line.strip().split("\t")
        if len(cells) < 2 or not cells[0] or not cells[1].isdigit():
            continue
        name, live = cells[0], int(cells[1])
        copy = cells[2].strip() if len(cells) > 2 else ""
        if not copy.isdigit() or int(copy) == 0:
            raise ValueError(f"нет id копии у элемента {name} ({live}): дубль не создался или не тот <copy>")
        if int(copy) == live:
            raise ValueError(f"id копии {name} совпадает с боевым {live}: в запросе не та форма")
        if name in result and result[name] != (live, int(copy)):
            raise ValueError(f"имя {name} встречается дважды с разными id — сопоставить вручную")
        result[name] = (live, int(copy))
    if not result:
        raise ValueError("таблица id пуста")
    return result


def _rewrite_known_ids(js: str, live_to_copy: dict[int, int], *, enforce: bool) -> str:
    """Числовые get_value_from → id копии. Чужой блок (enforce=False) не трогаем."""
    found = {int(n) for n in GET_VALUE_FROM.findall(js)}
    unknown = sorted(found - live_to_copy.keys())
    if unknown and enforce:
        raise ValueError(f"get_value_from с id не из боевой формы: {unknown}")
    if not enforce:
        return js

    def repl(match: re.Match) -> str:
        return f"get_value_from({live_to_copy[int(match.group(1))]}"

    return GET_VALUE_FROM.sub(repl, js)


def build_copy_js(
    js: str,
    id_map: dict[str, tuple[int, int]],
    live: int | None = None,
) -> str:
    """Id боевой формы в get_value_from(N) → id копии.

    Без блоков /* form N */ неизвестный id — ошибка.
    С блоками переписывается только ветка этой формы и код вне блоков.
    Id другой формы остаются: на копии эта ветка не выполняется.
    """
    live_to_copy = {live_id: copy for live_id, copy in id_map.values()}
    blocks = list(FORM_BLOCK.finditer(js))
    if not blocks:
        return _rewrite_known_ids(js, live_to_copy, enforce=True)
    if live is None:
        raise ValueError("в JS есть блоки /* form N */ — нужен id боевой формы")
    if live not in {int(block.group(1)) for block in blocks}:
        raise ValueError(f"в JS нет блока /* form {live} */")
    parts: list[str] = []
    cursor = 0
    for block in blocks:
        parts.append(_rewrite_known_ids(js[cursor:block.start()], live_to_copy, enforce=True))
        inner = block.group(2)
        if int(block.group(1)) == live:
            inner = _rewrite_known_ids(inner, live_to_copy, enforce=True)
        parts.append(js[block.start() : block.start(2)] + inner + js[block.end(2) : block.end()])
        cursor = block.end()
    parts.append(_rewrite_known_ids(js[cursor:], live_to_copy, enforce=True))
    return "".join(parts)


def build_package(
    js: str,
    live: int,
    copy: int,
    id_map: dict[str, tuple[int, int]],
    calc_name: str,
    gets: list[str],
) -> dict:
    """Пакет для ezfc_copy_apply.php: только ключи из его белого списка."""
    if live == copy:
        raise ValueError("копия и боевая форма — одна и та же форма")
    if calc_name not in id_map:
        raise ValueError(f"элемента расчёта {calc_name} нет в таблице id")
    elements: dict[str, dict[str, str]] = {
        str(id_map[calc_name][1]): {
            "custom_calculation": build_copy_js(js, id_map, live),
            "custom_calculation_function_read_file": "0",
        }
    }
    for item in gets:
        name, _, check = item.partition(":")
        if name not in id_map:
            raise ValueError(f"элемента {name} нет в таблице id")
        if check and check not in GET_CHECKS:
            raise ValueError(f"GET_check для {name}: только {', '.join(GET_CHECKS)}")
        fields = {"GET": name}
        if check:
            fields["GET_check_option_value"] = check
        elements.setdefault(str(id_map[name][1]), {}).update(fields)
    return {"live": live, "copy": copy, "elements": elements}


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Пакет JS и GET для копии формы ezFC")
    ap.add_argument("js", type=Path, help="wp-plugin/forms/<slug>.js с id боевой формы")
    ap.add_argument("--live", type=int, required=True, help="id боевой формы")
    ap.add_argument("--copy", type=int, required=True, help="id копии")
    ap.add_argument("--map", type=Path, required=True, help="вывод SQL шага 9")
    ap.add_argument("--calc", default="cjsCalc", help="имя элемента расчёта")
    ap.add_argument("--get", action="append", default=[], help="имя[:index|value]")
    ap.add_argument("--out", type=Path, required=True, help="куда записать пакет JSON")
    args = ap.parse_args(argv)
    try:
        id_map = parse_id_map(args.map.read_text(encoding="utf-8-sig"))
        package = build_package(
            args.js.read_text(encoding="utf-8"), args.live, args.copy, id_map, args.calc, args.get
        )
    except ValueError as exc:
        print(f"стоп: {exc}", file=sys.stderr)
        return 1
    args.out.write_text(json.dumps(package, ensure_ascii=False, indent=1), encoding="utf-8")
    for el_id, fields in package["elements"].items():
        print(el_id, ", ".join(sorted(fields)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
