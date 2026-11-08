"""Сводка расхода ИИ-агентов по выгрузке Usage из кабинета Cursor (CSV).

Колонки ищутся по подстроке в заголовке (без учёта регистра), потому что Cursor меняет их названия:
дата — `date`, модель — `model`, стоимость — `cost`, чтение кэша — `cache read`, выход — `output`,
вход — остальные колонки с `input`, всего — `total`. Нет колонки «всего» — сумма входа, кэша и выхода.

Строка сводки дописывается сверху таблицы в docs/history/usage.md; строка за тот же период заменяется.
"""

from __future__ import annotations

import csv
import re
import sys
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
USAGE_MD = ROOT / "docs" / "history" / "usage.md"
FAMILIES = ("Opus", "Grok", "Auto", "Прочие")
HEADER = (
    "| Период | Запросов | Токенов, млн | Стоимость, $ | Opus | Grok | Auto | Прочие | Кэш, % входа |\n"
    "| --- | --- | --- | --- | --- | --- | --- | --- | --- |"
)


def family(model: str) -> str:
    m = model.lower()
    if "opus" in m:
        return "Opus"
    if "grok" in m:
        return "Grok"
    if m in {"", "auto", "default"} or m.startswith("auto"):
        return "Auto"
    return "Прочие"


def _num(raw: str | None) -> float:
    """Число из ячейки: «1,234», «$0.12», «Included» (= 0)."""
    s = (raw or "").replace(",", "").replace("$", "").strip()
    try:
        return float(s)
    except ValueError:
        return 0.0


def _date(raw: str) -> str:
    raw = raw or ""
    m = re.search(r"\d{4}-\d{2}-\d{2}", raw)
    if m:
        return m.group(0)
    for pattern, fmt in (
        (r"[A-Z][a-z]{2} \d{1,2}, \d{4}", "%b %d, %Y"),
        (r"\d{2}\.\d{2}\.\d{4}", "%d.%m.%Y"),
        (r"\d{1,2}/\d{1,2}/\d{4}", "%m/%d/%Y"),
    ):
        m = re.search(pattern, raw)
        if m:
            try:
                return datetime.strptime(m.group(0), fmt).strftime("%Y-%m-%d")
            except ValueError:
                continue
    return ""


@dataclass
class Stat:
    requests: int = 0
    tokens: float = 0.0
    cost: float = 0.0


@dataclass
class Report:
    first: str = ""
    last: str = ""
    by_family: dict[str, Stat] = field(default_factory=lambda: {f: Stat() for f in FAMILIES})
    other_models: set[str] = field(default_factory=set)
    input_tokens: float = 0.0
    cache_read: float = 0.0

    @property
    def total(self) -> Stat:
        t = Stat()
        for s in self.by_family.values():
            t.requests += s.requests
            t.tokens += s.tokens
            t.cost += s.cost
        return t


def _columns(header: list[str]) -> dict[str, list[str]]:
    cols: dict[str, list[str]] = {"date": [], "model": [], "cost": [], "cache": [], "output": [], "input": [], "total": []}
    for h in header:
        low = h.lower()
        if "date" in low:
            cols["date"].append(h)
        elif "model" in low:
            cols["model"].append(h)
        elif "cost" in low:
            cols["cost"].append(h)
        elif "cache read" in low:
            cols["cache"].append(h)
        elif "output" in low:
            cols["output"].append(h)
        elif "input" in low:
            cols["input"].append(h)
        elif "total" in low:
            cols["total"].append(h)
    if not cols["model"]:
        raise SystemExit(f"в CSV нет колонки модели; заголовки: {header}")
    return cols


def parse(path: Path) -> Report:
    with path.open(encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        cols = _columns(reader.fieldnames or [])
        rep = Report()
        dates: list[str] = []
        for row in reader:
            model = (row.get(cols["model"][0]) or "").strip()
            fam = family(model)
            if fam == "Прочие":
                rep.other_models.add(model)
            inp = sum(_num(row.get(c)) for c in cols["input"])
            cache = sum(_num(row.get(c)) for c in cols["cache"])
            out = sum(_num(row.get(c)) for c in cols["output"])
            total = sum(_num(row.get(c)) for c in cols["total"]) or inp + cache + out
            s = rep.by_family[fam]
            s.requests += 1
            s.tokens += total
            s.cost += sum(_num(row.get(c)) for c in cols["cost"])
            rep.input_tokens += inp + cache
            rep.cache_read += cache
            if cols["date"]:
                d = _date(row.get(cols["date"][0]) or "")
                if d:
                    dates.append(d)
    if dates:
        rep.first, rep.last = min(dates), max(dates)
    return rep


def _pct(part: float, whole: float) -> str:
    return f"{round(100 * part / whole)}%" if whole else "—"


def row(rep: Report) -> str:
    t = rep.total
    cells = [
        f"{rep.first} — {rep.last}" if rep.first else "—",
        str(t.requests),
        f"{t.tokens / 1e6:.1f}",
        f"{t.cost:.2f}",
    ]
    for fam in FAMILIES:
        s = rep.by_family[fam]
        cells.append(f"{_pct(s.tokens, t.tokens)} ток. / {_pct(s.cost, t.cost)} $")
    cells.append(_pct(rep.cache_read, rep.input_tokens))
    return "| " + " | ".join(cells) + " |"


def write(rep: Report, path: Path = USAGE_MD) -> None:
    text = path.read_text(encoding="utf-8")
    if HEADER not in text:
        raise SystemExit(f"в {path} нет таблицы с заголовком сводки")
    new = row(rep)
    period = new.split("|")[1].strip()
    lines = [ln for ln in text.splitlines() if not ln.startswith(f"| {period} |")]
    text = "\n".join(lines) + "\n"
    path.write_text(text.replace(HEADER, HEADER + "\n" + new, 1), encoding="utf-8", newline="\n")


def main(csv_path: str) -> None:
    p = Path(csv_path)
    if not p.is_file():
        raise SystemExit(f"нет файла {p}")
    rep = parse(p)
    print(HEADER)
    print(row(rep))
    if rep.other_models:
        print("Прочие модели:", ", ".join(sorted(rep.other_models)))
    write(rep)
    print(f"строка записана в {USAGE_MD.relative_to(ROOT)}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        raise SystemExit("usage: python scripts/usage_report.py <usage.csv>")
    main(sys.argv[1])
