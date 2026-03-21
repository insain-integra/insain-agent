#!/usr/bin/env python3
"""
Генерация PDF для передачи во внешний LLM:
  1) Код: agent, bot, prompts (+ llm_provider)
  2) Логи llm_request с указанного файла по возрастанию имён

Зависимость: pip install reportlab

Запуск из корня репозитория:
  python scripts/export_llm_handoff_pdf.py
"""

from __future__ import annotations

import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from xml.sax.saxutils import escape as xml_escape

ROOT = Path(__file__).resolve().parent.parent

try:
    from reportlab.lib.enums import TA_LEFT
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
    from reportlab.lib.units import mm
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    from reportlab.platypus import (
        Paragraph,
        SimpleDocTemplate,
        Spacer,
        PageBreak,
    )
except ImportError as e:
    print("Установите: pip install reportlab", file=sys.stderr)
    raise SystemExit(1) from e

_ARIAL_REGISTERED = False


def _arial_path() -> Path:
    windir = Path(os.environ.get("WINDIR", r"C:\Windows"))
    for name in ("arial.ttf", "Arial.ttf", "ARIAL.TTF"):
        p = windir / "Fonts" / name
        if p.is_file():
            return p
    raise FileNotFoundError(
        "Не найден arial.ttf в Windows\\Fonts. Укажите шрифт с кириллицей вручную."
    )


def _ensure_arial_font() -> None:
    global _ARIAL_REGISTERED
    if _ARIAL_REGISTERED:
        return
    arial = str(_arial_path())
    pdfmetrics.registerFont(TTFont("ArialCustom", arial))
    _ARIAL_REGISTERED = True


def _esc_line(s: str) -> str:
    return (
        xml_escape(s, {"'": "&apos;"})
        .replace("\x00", "")
    )


def _paragraphs_from_text(text: str, style) -> list:
    """Разбить на Paragraph по строкам (устойчиво к очень длинным файлам)."""
    out: list = []
    for line in text.splitlines():
        out.append(Paragraph(_esc_line(line), style))
    return out


def build_code_pdf(out_path: Path) -> None:
    _ensure_arial_font()

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "DocTitle",
        parent=styles["Heading1"],
        fontName="ArialCustom",
        fontSize=16,
        leading=20,
        alignment=TA_LEFT,
    )
    h2_style = ParagraphStyle(
        "Section",
        parent=styles["Heading2"],
        fontName="ArialCustom",
        fontSize=12,
        leading=15,
        spaceAfter=6,
    )
    body_style = ParagraphStyle(
        "MonoBody",
        parent=styles["Normal"],
        fontName="ArialCustom",
        fontSize=7,
        leading=8.5,
        leftIndent=0,
        spaceAfter=0,
    )

    sections = [
        ("bot_service/agent.py", ROOT / "bot_service" / "agent.py"),
        ("bot_service/bot.py", ROOT / "bot_service" / "bot.py"),
        ("bot_service/prompts.py", ROOT / "bot_service" / "prompts.py"),
        ("bot_service/llm_provider.py", ROOT / "bot_service" / "llm_provider.py"),
    ]

    story: list = []
    story.append(
        Paragraph(
            _esc_line(
                "Insain Agent — код бота, агента, промптов и LLM (экспорт для внешней модели)"
            ),
            title_style,
        )
    )
    story.append(
        Paragraph(
            _esc_line(
                f"Сгенерировано: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}"
            ),
            body_style,
        )
    )
    story.append(Spacer(1, 8 * mm))

    for label, fpath in sections:
        if not fpath.is_file():
            story.append(Paragraph(_esc_line(f"[ОТСУТСТВУЕТ] {label}"), h2_style))
            story.append(PageBreak())
            continue
        story.append(Paragraph(_esc_line(label), h2_style))
        text = fpath.read_text(encoding="utf-8")
        story.extend(_paragraphs_from_text(text, body_style))
        story.append(PageBreak())

    out_path.parent.mkdir(parents=True, exist_ok=True)
    doc = SimpleDocTemplate(
        str(out_path),
        pagesize=A4,
        leftMargin=18 * mm,
        rightMargin=18 * mm,
        topMargin=16 * mm,
        bottomMargin=16 * mm,
        title="Insain bot_service code",
    )
    doc.build(story)


def _log_files_from(start_name: str) -> list[Path]:
    logs_dir = ROOT / "logs"
    if not logs_dir.is_dir():
        return []
    all_json = sorted(logs_dir.glob("llm_request_*.json"))
    return [p for p in all_json if p.name >= start_name]


def build_logs_pdf(out_path: Path, start_name: str) -> None:
    _ensure_arial_font()

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "LogTitle",
        parent=styles["Heading1"],
        fontName="ArialCustom",
        fontSize=14,
        leading=18,
    )
    h2_style = ParagraphStyle(
        "LogFile",
        parent=styles["Heading2"],
        fontName="ArialCustom",
        fontSize=10,
        leading=12,
        spaceAfter=4,
    )
    body_style = ParagraphStyle(
        "LogBody",
        parent=styles["Normal"],
        fontName="ArialCustom",
        fontSize=6.5,
        leading=7.5,
    )

    files = _log_files_from(start_name)
    story: list = []
    story.append(
        Paragraph(
            _esc_line(f"LLM request logs с файла {start_name} включительно"),
            title_style,
        )
    )
    story.append(
        Paragraph(
            _esc_line(
                f"Файлов: {len(files)}. {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}"
            ),
            body_style,
        )
    )
    story.append(Spacer(1, 6 * mm))

    if not files:
        story.append(Paragraph(_esc_line("Нет подходящих файлов в logs/"), body_style))
    for p in files:
        story.append(Paragraph(_esc_line(f"=== {p.name} ==="), h2_style))
        try:
            text = p.read_text(encoding="utf-8")
        except OSError as e:
            story.append(Paragraph(_esc_line(f"(ошибка чтения: {e})"), body_style))
            story.append(PageBreak())
            continue
        story.extend(_paragraphs_from_text(text, body_style))
        story.append(PageBreak())

    out_path.parent.mkdir(parents=True, exist_ok=True)
    doc = SimpleDocTemplate(
        str(out_path),
        pagesize=A4,
        leftMargin=14 * mm,
        rightMargin=14 * mm,
        topMargin=14 * mm,
        bottomMargin=14 * mm,
        title="Insain LLM logs",
    )
    doc.build(story)


def main() -> None:
    start = "llm_request_2026-03-21T11-36-00-144482.json"
    out_dir = ROOT / "exports"
    code_pdf = out_dir / "insain_bot_agent_prompts_llm.pdf"
    logs_pdf = out_dir / "insain_llm_logs_from_11-36-00.pdf"

    build_code_pdf(code_pdf)
    build_logs_pdf(logs_pdf, start)
    print(f"OK: {code_pdf}")
    print(f"OK: {logs_pdf}")


if __name__ == "__main__":
    main()
