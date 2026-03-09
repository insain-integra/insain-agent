from __future__ import annotations

"""
Миграция файлов data/materials/*.json к новому формату полей материалов.

Что делает скрипт:
1. Проходит по всем JSON-файлам в calc_service/data/materials.
2. Для каждого материала:
   - переносит name → description (если description ещё нет),
   - добавляет/обновляет title (краткое имя для UI, ≤ 50 символов),
   - извлекает cost_date и cost_source из комментариев к полю cost (если были),
   - сохраняет изменения обратно в файл (без комментариев).

Скрипт можно запускать многократно — он работает идемпотентно.

Запуск (из корня репозитория):
    python -m calc_service.scripts.migrate_materials_metadata
или:
    python calc_service/scripts/migrate_materials_metadata.py
"""

import json
import re
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

import json5


ROOT_DIR = Path(__file__).resolve().parents[2]
MATERIALS_DIR = ROOT_DIR / "calc_service" / "data" / "materials"


DATE_RE = re.compile(r"(\d{2})\.(\d{2})\.(\d{4})")


def extract_cost_metadata_from_comment(comment: str) -> Tuple[Optional[str], Optional[str]]:
    """
    Извлечь (cost_date_iso, cost_source) из строки комментария.

    Примеры:
        "// 24.03.2025 ТрастФМ"            -> ("2025-03-24", "ТрастФМ")
        "// руб./бобина 02.07.2022"       -> ("2022-07-02", None)
        "// р/м2 14.05.2024 Зенон"        -> ("2024-05-14", "Зенон")
    """
    # Уберём начальные слэши и пробелы
    text = comment.lstrip("/").strip()
    if not text:
        return None, None

    m = DATE_RE.search(text)
    if not m:
        return None, None

    day, month, year = m.groups()
    date_iso = f"{year}-{month}-{day}"

    before = text[: m.start()].strip()
    after = text[m.end() :].strip()

    # Шумовые слова про единицы измерения и валюту
    noise_tokens = {"руб", "руб.", "руб./шт", "руб./м2", "руб./мп", "р/м2", "р/м³", "р/м", "р/шт"}

    def cleanup_source(s: str) -> Optional[str]:
        if not s:
            return None
        # Разобьём на слова и уберём очевидный "шум"
        tokens = [t for t in re.split(r"\s+", s) if t]
        tokens = [t for t in tokens if t.lower() not in noise_tokens]
        if not tokens:
            return None
        return " ".join(tokens)

    # В одних комментариях сначала дата, потом источник, в других наоборот.
    source = cleanup_source(after) or cleanup_source(before)
    return date_iso, source


def scan_cost_comments(path: Path) -> Dict[str, Tuple[Optional[str], Optional[str]]]:
    """
    Быстрый парсер исходного JSON5-текста для извлечения даты/источника по коду материала.

    Алгоритм:
      - идём по строкам,
      - запоминаем текущий code по строкам вида `"PVC3": {`,
      - на строках с `"cost": ... // ...` парсим комментарий и вешаем на текущий code.
    """
    mapping: Dict[str, Tuple[Optional[str], Optional[str]]] = {}
    current_code: Optional[str] = None

    code_re = re.compile(r'^\s*"([^"]+)"\s*:\s*\{')
    cost_re = re.compile(r'^\s*"cost"\s*:\s*([^,]+)(,?\s*//(?P<comment>.*))?$')

    for line in path.read_text(encoding="utf-8").splitlines():
        m_code = code_re.match(line)
        if m_code:
            current_code = m_code.group(1)
            continue

        m_cost = cost_re.match(line)
        if not m_cost or current_code is None:
            continue

        comment = m_cost.group("comment")
        if not comment:
            continue

        date_iso, source = extract_cost_metadata_from_comment(comment)
        if date_iso or source:
            mapping[current_code] = (date_iso, source)

    return mapping


def generate_title(description: str, code: str) -> str:
    """
    Сгенерировать краткий title из полного описания.

    Правила (упрощённо, но по духу задачи):
      - убираем некоторые "длинные" или брендовские части,
      - режем до 50 символов.
    """
    title = description

    # Убираем явно брендовые/служебные части
    patterns = [
        r"\bPlexiglas\b.*?\bXT\b",
        r"\bUnext\b.*?\bStrong\b",
        r"\bGEBAU\b.*?\bHIPS\b",
        r"\bJUST\b.*?\bRoll\b",
        r"\b3M\b",
        r"\bZENOTAPE\b.*?\bАТ610\b",
        r"\bPOLI-MOUNT\b.*?\b385\b",
        r"рекламное поле",
        r"для сублимации",
        r"под заливку смолой",
        r"на цанге",
    ]
    for p in patterns:
        title = re.sub(p, "", title, flags=re.IGNORECASE)

    # Сжимаем лишние пробелы и запятые
    title = re.sub(r"\s+", " ", title)
    title = title.strip(" ,")

    if not title:
        title = description or code

    # Обрезаем до 50 символов
    if len(title) > 50:
        title = title[:50].rstrip()

    return title or code


def migrate_file(path: Path) -> None:
    """Мигрировать один файл materials/*.json."""
    print(f"Миграция {path.name} ...")

    cost_meta_by_code = scan_cost_comments(path)
    data: Dict[str, Any] = json5.loads(path.read_text(encoding="utf-8"))

    changed = False

    for group_id, group_data in data.items():
        if not isinstance(group_data, dict):
            continue
        for code, spec in group_data.items():
            if code == "Default" or not isinstance(spec, dict):
                continue

            desc = spec.get("description")
            name = spec.get("name")

            if not desc:
                # Перенос name → description
                desc = name or code
                spec["description"] = desc
                changed = True

            # Генерация title при отсутствии
            if not spec.get("title"):
                spec["title"] = generate_title(str(desc), code)
                changed = True
            else:
                # Гарантируем ограничение по длине
                t = str(spec["title"])
                if len(t) > 50:
                    spec["title"] = t[:50].rstrip()
                    changed = True

            # Если description есть, а name только дублирует её — можно удалить name.
            if name and name == desc:
                # Оставляем только description/title, чтобы не плодить дубли.
                del spec["name"]
                changed = True

            # Метаданные стоимости из комментариев (по коду материала).
            date_iso, source = cost_meta_by_code.get(code, (None, None))
            if date_iso and spec.get("cost_date") != date_iso:
                spec["cost_date"] = date_iso
                changed = True
            if source and spec.get("cost_source") != source:
                spec["cost_source"] = source
                changed = True

    if not changed:
        print(f"  {path.name}: без изменений")
        return

    # Перезаписываем файл в чистом JSON (комментарии пропадут, но дата/источник уже в полях).
    text = json.dumps(data, ensure_ascii=False, indent=4)
    path.write_text(text + "\n", encoding="utf-8")
    print(f"  {path.name}: обновлён")


def main() -> None:
    if not MATERIALS_DIR.is_dir():
        raise SystemExit(f"Не найдена директория материалов: {MATERIALS_DIR}")

    files = sorted(MATERIALS_DIR.glob("*.json"))
    if not files:
        raise SystemExit(f"В {MATERIALS_DIR} нет файлов *.json")

    for path in files:
        migrate_file(path)


if __name__ == "__main__":
    main()

