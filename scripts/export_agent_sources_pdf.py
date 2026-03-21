#!/usr/bin/env python3
"""
Сборка PDF для внешнего LLM: агент (bot_service), описание проекта, примеры
калькуляторов и фрагменты данных (JSON).

Зависимость: pip install fpdf2

Перенос строк: разбиение по get_string_width(), не multi_cell CHAR.

Запуск из корня репозитория:
  python scripts/export_agent_sources_pdf.py
  python scripts/export_agent_sources_pdf.py --out exports/my.pdf
  python scripts/export_agent_sources_pdf.py --no-context --no-data

Дополнительно: текстовый файл с последними логами LLM
  exports/insain-latest-logs-YYYYMMDD.txt  (отключить: --no-logs-file)
Только PDF с логами (без большого контекста):
  python scripts/export_agent_sources_pdf.py --logs-pdf-only --logs-count 13
"""

from __future__ import annotations

import argparse
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable, NamedTuple

# Корень репозитория: scripts/..
ROOT = Path(__file__).resolve().parent.parent


class SourceBlock(NamedTuple):
    """rel_path от корня репозитория, заголовок в PDF, лимит строк (None = весь файл)."""

    rel_path: str
    title: str
    max_lines: int | None = None


# --- 1. Описание проекта и документация ---
CONTEXT_BLOCKS: list[SourceBlock] = [
    SourceBlock(
        "docs/project_summary.md",
        "Документация: обзор проекта (docs/project_summary.md)",
        220,
    ),
    SourceBlock(
        "docs/architecture.md",
        "Документация: архитектура — начало (docs/architecture.md)",
        90,
    ),
    SourceBlock(
        "CLAUDE.md",
        "Инструкции для ИИ — начало (CLAUDE.md)",
        160,
    ),
]

# --- 2. Исходники агента ---
AGENT_FILES: list[SourceBlock] = [
    SourceBlock(
        "bot_service/agent.py",
        "Исходник: bot_service/agent.py",
    ),
    SourceBlock(
        "bot_service/prompts.py",
        "Исходник: bot_service/prompts.py",
    ),
    SourceBlock(
        "bot_service/llm_provider.py",
        "Исходник: bot_service/llm_provider.py",
    ),
    SourceBlock(
        "bot_service/bot.py",
        "Исходник: bot_service/bot.py",
    ),
    SourceBlock(
        "bot_service/token_analyzer.py",
        "Исходник: bot_service/token_analyzer.py",
    ),
    SourceBlock(
        "bot_service/analyze_tokens.py",
        "Исходник: bot_service/analyze_tokens.py",
    ),
    SourceBlock(
        "bot_service/knowledge_base.py",
        "Исходник: bot_service/knowledge_base.py",
    ),
    SourceBlock(
        "bot_service/wiki_parser.py",
        "Исходник: bot_service/wiki_parser.py",
    ),
    SourceBlock(
        "bot_service/check.py",
        "Исходник: bot_service/check.py",
    ),
    SourceBlock(
        "bot_service/tests/test_agent.py",
        "Исходник: bot_service/tests/test_agent.py",
    ),
]

# --- 3. Примеры калькуляторов (calc_service) ---
CALCULATOR_BLOCKS: list[SourceBlock] = [
    SourceBlock(
        "calc_service/calculators/_template.py",
        "Пример калькулятора: шаблон (_template.py)",
    ),
    SourceBlock(
        "calc_service/calculators/base.py",
        "Пример калькулятора: базовый класс (base.py, фрагмент)",
        140,
    ),
    SourceBlock(
        "calc_service/calculators/laser.py",
        "Пример калькулятора: лазер (laser.py, фрагмент)",
        85,
    ),
    SourceBlock(
        "calc_service/calculators/print_sheet.py",
        "Пример калькулятора: листовая печать (print_sheet.py, фрагмент)",
        95,
    ),
]

# --- 4. Примеры данных (JSON) ---
DATA_BLOCKS: list[SourceBlock] = [
    SourceBlock(
        "calc_service/data/common.json",
        "Данные: common.json (наценки, сроки, валюты — фрагмент)",
        58,
    ),
    SourceBlock(
        "calc_service/data/materials/sheet.json",
        "Данные: materials/sheet.json (листовые бумаги — фрагмент)",
        72,
    ),
    SourceBlock(
        "calc_service/data/equipment/printer.json",
        "Данные: equipment/printer.json (принтеры — фрагмент)",
        55,
    ),
    SourceBlock(
        "calc_service/data/equipment/laser.json",
        "Данные: equipment/laser.json (лазеры — фрагмент)",
        58,
    ),
]


def _find_mono_font() -> Path:
    """Моноширинный TTF с кириллицей (код + комментарии)."""
    candidates = [
        Path(r"C:\Windows\Fonts\consola.ttf"),
        Path(r"C:\Windows\Fonts\lucon.ttf"),
        Path("/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf"),
        Path("/usr/share/fonts/TTF/DejaVuSansMono.ttf"),
        Path("/usr/share/fonts/truetype/liberation/LiberationMono-Regular.ttf"),
    ]
    for p in candidates:
        if p.is_file():
            return p
    raise FileNotFoundError(
        "Не найден моноширинный TTF (Consolas / DejaVu Sans Mono). "
        "Установите шрифт или укажите путь через переменную окружения AGENT_EXPORT_FONT."
    )


def _sanitize_for_mono_font(s: str) -> str:
    """Consolas: убрать эмодзи и символы, которых нет в моноширинном TTF (иначе fpdf ругается)."""
    s = s.replace("\u2011", "-")  # неразрывный дефис (часто в markdown)
    out: list[str] = []
    for ch in s:
        o = ord(ch)
        if o < 32 and ch not in "\n\r\t":
            out.append("?")
            continue
        if o == 0xFE0F:
            continue
        if o > 0xFFFF or (0x1F000 <= o <= 0x1FFFF):
            out.append(" ")
            continue
        if 0x2300 <= o <= 0x27BF or 0x2190 <= o <= 0x21FF:
            out.append(" ")
            continue
        out.append(ch)
    return "".join(out)


def _read_block_text(path: Path, max_lines: int | None) -> str:
    if not path.is_file():
        return f"[Файл не найден: {path}]"
    raw = path.read_text(encoding="utf-8")
    lines = raw.splitlines()
    if max_lines is not None and len(lines) > max_lines:
        clipped = "\n".join(lines[:max_lines])
        return (
            f"{clipped}\n\n"
            f"... [обрезано: показаны первые {max_lines} строк из {len(lines)}] ..."
        )
    return raw


def _split_line_to_max_width(pdf: object, text: str, max_w: float) -> list[str]:
    get_w = pdf.get_string_width
    if not text:
        return [""]
    parts: list[str] = []
    i = 0
    n = len(text)
    eps = 0.02
    while i < n:
        lo, hi = i + 1, n
        best = i
        while lo <= hi:
            mid = (lo + hi) // 2
            w = get_w(text[i:mid])
            if w <= max_w + eps:
                best = mid
                lo = mid + 1
            else:
                hi = mid - 1
        if best <= i:
            best = i + 1
        parts.append(text[i:best])
        i = best
    return parts


def _emit_pages_for_text(
    pdf: object,
    *,
    title: str,
    body: str,
    code_font_pt: float,
    line_h: float,
    tw_code: float,
    new_page: bool,
) -> None:
    from fpdf.enums import Align, WrapMode, XPos, YPos

    if new_page:
        pdf.add_page()
    pdf.set_font("Mono", "", 9)
    pdf.multi_cell(
        tw_code,
        4.5,
        title,
        align=Align.L,
        wrapmode=WrapMode.WORD,
    )
    pdf.set_font("Mono", "", code_font_pt)
    pdf.ln(0.6)

    for raw_line in body.splitlines():
        line = raw_line.replace("\t", "    ")
        raw = "".join(c if c >= " " or c in "\n\r\t" else "?" for c in line)
        safe = _sanitize_for_mono_font(raw)
        if not safe:
            pdf.ln(line_h)
            continue
        for chunk in _split_line_to_max_width(pdf, safe, tw_code):
            pdf.cell(
                tw_code,
                line_h,
                chunk,
                new_x=XPos.LMARGIN,
                new_y=YPos.NEXT,
            )


def _emit_blocks(
    pdf: object,
    blocks: Iterable[SourceBlock],
    *,
    code_font_pt: float,
    line_h: float,
    tw_code: float,
) -> None:
    for block in blocks:
        path = ROOT / block.rel_path
        text = _read_block_text(path, block.max_lines)
        _emit_pages_for_text(
            pdf,
            title=block.title,
            body=text,
            code_font_pt=code_font_pt,
            line_h=line_h,
            tw_code=tw_code,
            new_page=True,
        )


def build_pdf(
    out_path: Path,
    font_path: Path,
    *,
    code_font_pt: float = 6.0,
    margin_mm: float = 8.0,
    landscape: bool = True,
    include_context: bool = True,
    include_agent: bool = True,
    include_calc: bool = True,
    include_data: bool = True,
) -> None:
    try:
        from fpdf import FPDF
        from fpdf.enums import Align, WrapMode
    except ImportError as e:
        raise SystemExit(
            "Нужен пакет fpdf2: pip install fpdf2"
        ) from e

    orient = "L" if landscape else "P"
    pdf = FPDF(orientation=orient)
    pdf.set_auto_page_break(auto=True, margin=10)
    pdf.c_margin = 0.0
    pdf.set_margins(margin_mm, 10, margin_mm)
    pdf.add_font("Mono", "", str(font_path))

    def text_width_mm() -> float:
        return float(pdf.epw)

    title = "Insain Agent — контекст для анализа (проект, агент, калькуляторы, данные)"
    pdf.add_page()
    pdf.set_font("Mono", "", 11)
    tw = text_width_mm()
    pdf.multi_cell(tw, 5.5, title, align=Align.L, wrapmode=WrapMode.WORD)
    pdf.set_font("Mono", "", 8)
    pdf.multi_cell(
        tw,
        4.2,
        f"Сформировано: {datetime.now(timezone.utc).astimezone().isoformat(timespec='seconds')}",
        align=Align.L,
        wrapmode=WrapMode.WORD,
    )
    pdf.multi_cell(
        tw,
        4.2,
        f"Корень: {ROOT}",
        align=Align.L,
        wrapmode=WrapMode.WORD,
    )
    parts_desc: list[str] = []
    if include_context:
        parts_desc.append("обзор проекта + docs")
    if include_agent:
        parts_desc.append("исходники бота")
    if include_calc:
        parts_desc.append("примеры калькуляторов")
    if include_data:
        parts_desc.append("фрагменты JSON")
    pdf.multi_cell(
        tw,
        4.2,
        "Содержимое: " + "; ".join(parts_desc) if parts_desc else "(пусто)",
        align=Align.L,
        wrapmode=WrapMode.WORD,
    )
    pdf.ln(2)

    line_h = max(2.2, code_font_pt * 0.42)
    pdf.set_font("Mono", "", code_font_pt)
    tw_code = text_width_mm()

    if include_context:
        _emit_blocks(
            pdf,
            CONTEXT_BLOCKS,
            code_font_pt=code_font_pt,
            line_h=line_h,
            tw_code=tw_code,
        )

    if include_agent:
        _emit_blocks(
            pdf,
            AGENT_FILES,
            code_font_pt=code_font_pt,
            line_h=line_h,
            tw_code=tw_code,
        )

    if include_calc:
        _emit_blocks(
            pdf,
            CALCULATOR_BLOCKS,
            code_font_pt=code_font_pt,
            line_h=line_h,
            tw_code=tw_code,
        )

    if include_data:
        _emit_blocks(
            pdf,
            DATA_BLOCKS,
            code_font_pt=code_font_pt,
            line_h=line_h,
            tw_code=tw_code,
        )

    out_path.parent.mkdir(parents=True, exist_ok=True)
    pdf.output(str(out_path))


def _collect_latest_llm_log_files(root: Path, count: int) -> list[Path]:
    """Последние по времени изменения файлы logs/llm_request_*.json (новые первыми)."""
    log_dir = root / "logs"
    if not log_dir.is_dir():
        return []
    files = sorted(
        log_dir.glob("llm_request_*.json"),
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )
    return files[: max(0, count)]


def write_latest_logs_txt(
    out_path: Path,
    root: Path,
    *,
    count: int = 12,
) -> int:
    """
    Собрать последние логи LLM в один UTF-8 текстовый файл.
    Возвращает число включённых файлов.
    """
    paths = _collect_latest_llm_log_files(root, count)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    sep = "\n" + ("=" * 80) + "\n"
    lines: list[str] = [
        "Insain — последние логи запросов LLM (llm_request_*.json)",
        f"Сформировано: {datetime.now(timezone.utc).astimezone().isoformat(timespec='seconds')}",
        f"Корень: {root}",
        f"Файлов в пакете: {len(paths)} (макс. запрошено: {count})",
        sep,
    ]
    if not paths:
        lines.append(
            f"[Папка logs пуста или нет файлов llm_request_*.json: {root / 'logs'}]\n"
        )
    for i, p in enumerate(paths, start=1):
        rel = p.relative_to(root)
        try:
            body = p.read_text(encoding="utf-8")
        except OSError as e:
            body = f"[Ошибка чтения: {e}]\n"
        lines.append(f"### [{i}/{len(paths)}] {rel}\n")
        lines.append(body.rstrip() + "\n")
        lines.append(sep)

    out_path.write_text("".join(lines), encoding="utf-8")
    return len(paths)


def build_logs_pdf(
    out_path: Path,
    root: Path,
    font_path: Path,
    *,
    count: int = 13,
    code_font_pt: float = 5.5,
    margin_mm: float = 8.0,
    landscape: bool = True,
) -> int:
    """
    PDF с последними N файлами llm_request_*.json (каждый лог с новой страницы).
    Возвращает число включённых файлов.
    """
    try:
        from fpdf import FPDF
        from fpdf.enums import Align, WrapMode
    except ImportError as e:
        raise SystemExit(
            "Нужен пакет fpdf2: pip install fpdf2"
        ) from e

    paths = _collect_latest_llm_log_files(root, count)
    orient = "L" if landscape else "P"
    pdf = FPDF(orientation=orient)
    pdf.set_auto_page_break(auto=True, margin=10)
    pdf.c_margin = 0.0
    pdf.set_margins(margin_mm, 10, margin_mm)
    pdf.add_font("Mono", "", str(font_path))

    pdf.add_page()
    pdf.set_font("Mono", "", 11)
    tw = float(pdf.epw)
    pdf.multi_cell(
        tw,
        5.5,
        "Insain — последние логи LLM (logs/llm_request_*.json)",
        align=Align.L,
        wrapmode=WrapMode.WORD,
    )
    pdf.set_font("Mono", "", 8)
    pdf.multi_cell(
        tw,
        4.2,
        f"Сформировано: {datetime.now(timezone.utc).astimezone().isoformat(timespec='seconds')}",
        align=Align.L,
        wrapmode=WrapMode.WORD,
    )
    pdf.multi_cell(
        tw,
        4.2,
        f"Корень: {root} | файлов в PDF: {len(paths)} (запрошено: {count})",
        align=Align.L,
        wrapmode=WrapMode.WORD,
    )

    line_h = max(2.2, code_font_pt * 0.42)
    tw_code = float(pdf.epw)

    if not paths:
        pdf.add_page()
        _emit_pages_for_text(
            pdf,
            title="Нет логов",
            body=f"Папка пуста или нет llm_request_*.json:\n{root / 'logs'}",
            code_font_pt=code_font_pt,
            line_h=line_h,
            tw_code=tw_code,
            new_page=True,
        )
    else:
        for i, p in enumerate(paths, start=1):
            rel = p.relative_to(root)
            try:
                body = p.read_text(encoding="utf-8")
            except OSError as e:
                body = f"[Ошибка чтения: {e}]"
            title = f"[{i}/{len(paths)}] {rel.as_posix()}"
            _emit_pages_for_text(
                pdf,
                title=title,
                body=body,
                code_font_pt=code_font_pt,
                line_h=line_h,
                tw_code=tw_code,
                new_page=True,
            )

    out_path.parent.mkdir(parents=True, exist_ok=True)
    pdf.output(str(out_path))
    return len(paths)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Экспорт контекста проекта в PDF (агент + документация + калькуляторы + данные)"
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=None,
        help="Путь к выходному PDF (по умолчанию exports/insain-agent-context-YYYYMMDD.pdf)",
    )
    parser.add_argument(
        "--font-size",
        type=float,
        default=6.0,
        help="Размер шрифта кода/текста, pt (по умолчанию 6)",
    )
    parser.add_argument(
        "--margin",
        type=float,
        default=8.0,
        help="Поля страницы, мм (по умолчанию 8)",
    )
    parser.add_argument(
        "--portrait",
        action="store_true",
        help="Книжная ориентация (по умолчанию — альбомная)",
    )
    parser.add_argument(
        "--no-context",
        action="store_true",
        help="Не включать документацию проекта (docs, CLAUDE.md)",
    )
    parser.add_argument(
        "--no-agent",
        action="store_true",
        help="Не включать исходники bot_service",
    )
    parser.add_argument(
        "--no-calc",
        action="store_true",
        help="Не включать примеры калькуляторов",
    )
    parser.add_argument(
        "--no-data",
        action="store_true",
        help="Не включать фрагменты JSON",
    )
    parser.add_argument(
        "--logs-out",
        type=Path,
        default=None,
        help="Куда сохранить сшивку последних логов LLM (по умолчанию exports/insain-latest-logs-YYYYMMDD.txt)",
    )
    parser.add_argument(
        "--logs-count",
        type=int,
        default=12,
        help="Сколько последних файлов llm_request_*.json включить (по умолчанию 12)",
    )
    parser.add_argument(
        "--no-logs-file",
        action="store_true",
        help="Не создавать текстовый файл с логами",
    )
    parser.add_argument(
        "--logs-only",
        action="store_true",
        help="Только сшить логи в .txt (без PDF, не нужен fpdf2)",
    )
    parser.add_argument(
        "--logs-pdf-out",
        type=Path,
        default=None,
        help="Куда сохранить PDF с последними логами (по умолчанию exports/insain-latest-logs-YYYYMMDD.pdf)",
    )
    parser.add_argument(
        "--logs-pdf-only",
        action="store_true",
        help="Только PDF с последними логами (без большого контекстного PDF)",
    )
    args = parser.parse_args()

    ts = datetime.now().strftime("%Y-%m-%d")
    out = args.out or (ROOT / "exports" / f"insain-agent-context-{ts}.pdf")
    logs_out = args.logs_out or (ROOT / "exports" / f"insain-latest-logs-{ts}.txt")
    logs_pdf_out = args.logs_pdf_out or (ROOT / "exports" / f"insain-latest-logs-{ts}.pdf")

    if args.logs_only:
        try:
            n = write_latest_logs_txt(logs_out, ROOT, count=args.logs_count)
            print(f"OK логи ({n} файлов): {logs_out.resolve()}")
        except Exception as e:
            print(f"Ошибка: {e}", file=sys.stderr)
            return 1
        return 0

    if args.logs_pdf_only:
        font_env = __import__("os").environ.get("AGENT_EXPORT_FONT")
        font_path = Path(font_env) if font_env else _find_mono_font()
        try:
            n = build_logs_pdf(
                logs_pdf_out,
                ROOT,
                font_path,
                count=args.logs_count,
                code_font_pt=args.font_size,
                margin_mm=args.margin,
                landscape=not args.portrait,
            )
            print(f"OK PDF логов ({n} файлов): {logs_pdf_out.resolve()}")
        except Exception as e:
            print(f"Ошибка: {e}", file=sys.stderr)
            return 1
        return 0

    font_env = __import__("os").environ.get("AGENT_EXPORT_FONT")
    font_path = Path(font_env) if font_env else _find_mono_font()

    try:
        build_pdf(
            out,
            font_path,
            code_font_pt=args.font_size,
            margin_mm=args.margin,
            landscape=not args.portrait,
            include_context=not args.no_context,
            include_agent=not args.no_agent,
            include_calc=not args.no_calc,
            include_data=not args.no_data,
        )
    except Exception as e:
        print(f"Ошибка: {e}", file=sys.stderr)
        return 1

    print(f"OK PDF: {out.resolve()}")
    if not args.no_logs_file:
        try:
            n = write_latest_logs_txt(
                logs_out,
                ROOT,
                count=args.logs_count,
            )
            print(f"OK логи ({n} файлов): {logs_out.resolve()}")
        except Exception as e:
            print(f"Предупреждение: не удалось записать логи: {e}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
