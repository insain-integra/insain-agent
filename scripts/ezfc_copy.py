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


def build_copy_js(js: str, id_map: dict[str, tuple[int, int]]) -> str:
    """Id боевой формы в get_value_from(N) → id копии. Неизвестный id — ошибка."""
    live_to_copy = {live: copy for live, copy in id_map.values()}
    unknown = sorted({int(n) for n in GET_VALUE_FROM.findall(js)} - live_to_copy.keys())
    if unknown:
        raise ValueError(f"get_value_from с id не из боевой формы: {unknown}")
    return GET_VALUE_FROM.sub(lambda m: f"get_value_from({live_to_copy[int(m.group(1))]}", js)


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
            "custom_calculation": build_copy_js(js, id_map),
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
