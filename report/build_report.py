#!/usr/bin/env python3
"""Build the Task 5 Markdown report as a styled PDF. Requires ReportLab."""

from __future__ import annotations

import html
import re
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    Flowable,
    ListFlowable,
    ListItem,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)


ROOT = Path(__file__).resolve().parent
SOURCE = ROOT / "final_project_report.md"
OUTPUT = ROOT / "final_project_report.pdf"

NAVY = colors.HexColor("#17324D")
TEAL = colors.HexColor("#23877D")
PALE_BLUE = colors.HexColor("#EAF1F7")
PALE_TEAL = colors.HexColor("#EAF5F2")
INK = colors.HexColor("#243342")
MUTED = colors.HexColor("#637487")
RULE = colors.HexColor("#CBD5DF")


def inline_markup(text: str) -> str:
    text = html.escape(text, quote=False)
    text = re.sub(
        r"`([^`]+)`",
        r'<font name="Courier" size="7.6">\1</font>',
        text,
    )
    text = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", text)
    text = re.sub(r"(?<!\*)\*(.+?)\*(?!\*)", r"<i>\1</i>", text)
    text = re.sub(
        r"\[([^\]]+)\]\((https?://[^)]+)\)",
        r'<link href="\2" color="#23877D" underline="1">\1</link>',
        text,
    )
    return text


class ArchitectureDiagram(Flowable):
    """Compact two-stage flow diagram for indexing and answering."""

    def __init__(self, width: float):
        super().__init__()
        self.width = width
        self.height = 150

    def _box(self, x, y, w, h, label, fill, font_size=7.5):
        canvas = self.canv
        canvas.setFillColor(fill)
        canvas.setStrokeColor(RULE)
        canvas.roundRect(x, y, w, h, 6, stroke=1, fill=1)
        style = ParagraphStyle(
            "diagram",
            fontName="Helvetica-Bold",
            fontSize=font_size,
            leading=font_size + 2,
            alignment=TA_CENTER,
            textColor=NAVY,
        )
        paragraph = Paragraph(label, style)
        _, ph = paragraph.wrap(w - 8, h - 6)
        paragraph.drawOn(canvas, x + 4, y + (h - ph) / 2)

    def _arrow(self, x1, y1, x2, y2):
        canvas = self.canv
        canvas.setStrokeColor(TEAL)
        canvas.setFillColor(TEAL)
        canvas.setLineWidth(1.15)
        canvas.line(x1, y1, x2 - 4, y2)
        canvas.line(x2 - 4, y2, x2 - 8, y2 + 3)
        canvas.line(x2 - 4, y2, x2 - 8, y2 - 3)

    def draw(self):
        canvas = self.canv
        left = 7
        canvas.setFillColor(TEAL)
        canvas.setFont("Helvetica-Bold", 7.2)
        canvas.drawString(left, 139, "INDEXING")
        top_y, top_h = 100, 31
        top_w, top_gap = 91, 31
        top_labels = [
            "PDF and TXT\nhandbook files",
            "pypdf extraction\n1,000 / 200 chunks",
            "nomic-embed-text\nembeddings",
            "Persistent\nChroma index",
        ]
        for index, label in enumerate(top_labels):
            x = left + index * (top_w + top_gap)
            self._box(x, top_y, top_w, top_h, label, PALE_BLUE)
            if index < len(top_labels) - 1:
                self._arrow(x + top_w + 1, top_y + top_h / 2, x + top_w + top_gap - 1, top_y + top_h / 2)

        canvas.setFillColor(TEAL)
        canvas.drawString(left, 78, "QUESTION AND ANSWER")
        bottom_y, bottom_h = 25, 39
        bottom_w, bottom_gap = 84, 16
        bottom_labels = [
            "Student\nquestion",
            "Embed query and\nretrieve top 5",
            "0.30 score gate\nand grounded prompt",
            "qwen2.5:1.5b\nthrough Ollama",
            "CLI or web answer\nwith page sources",
        ]
        for index, label in enumerate(bottom_labels):
            x = left + index * (bottom_w + bottom_gap)
            self._box(x, bottom_y, bottom_w, bottom_h, label, PALE_TEAL, font_size=7.0)
            if index < len(bottom_labels) - 1:
                self._arrow(x + bottom_w + 1, bottom_y + bottom_h / 2, x + bottom_w + bottom_gap - 1, bottom_y + bottom_h / 2)

        # Show that retrieval reads from the persisted index above.
        index_x = left + 3 * (top_w + top_gap) + top_w / 2
        retrieval_x = left + (bottom_w + bottom_gap) + bottom_w / 2
        canvas.saveState()
        canvas.setStrokeColor(MUTED)
        canvas.setDash(2, 2)
        canvas.line(index_x, top_y, retrieval_x, bottom_y + bottom_h)
        canvas.restoreState()


def make_styles():
    base = getSampleStyleSheet()
    return {
        "h1": ParagraphStyle(
            "ReportH1", parent=base["Heading1"], fontName="Helvetica-Bold",
            fontSize=15, leading=19, textColor=NAVY, spaceBefore=12,
            spaceAfter=6, keepWithNext=True,
        ),
        "h2": ParagraphStyle(
            "ReportH2", parent=base["Heading2"], fontName="Helvetica-Bold",
            fontSize=10.5, leading=13, textColor=TEAL, spaceBefore=8,
            spaceAfter=4, keepWithNext=True,
        ),
        "body": ParagraphStyle(
            "ReportBody", parent=base["BodyText"], fontName="Helvetica",
            fontSize=9.2, leading=13.2, textColor=INK, alignment=TA_LEFT,
            spaceAfter=6,
        ),
        "list": ParagraphStyle(
            "ReportList", parent=base["BodyText"], fontName="Helvetica",
            fontSize=9.1, leading=12.3, textColor=INK, spaceAfter=2,
        ),
        "caption": ParagraphStyle(
            "ReportCaption", parent=base["BodyText"], fontName="Helvetica-Oblique",
            fontSize=8, leading=10, textColor=MUTED, alignment=TA_CENTER,
            spaceBefore=3, spaceAfter=8,
        ),
        "table": ParagraphStyle(
            "ReportTable", parent=base["BodyText"], fontName="Helvetica",
            fontSize=7.3, leading=9.2, textColor=INK, spaceAfter=0,
        ),
        "table_head": ParagraphStyle(
            "ReportTableHead", parent=base["BodyText"], fontName="Helvetica-Bold",
            fontSize=7.4, leading=9.2, textColor=colors.white, spaceAfter=0,
        ),
        "cover_title": ParagraphStyle(
            "CoverTitle", parent=base["Title"], fontName="Helvetica-Bold",
            fontSize=28, leading=34, textColor=NAVY, alignment=TA_CENTER,
            spaceAfter=16,
        ),
        "cover_subtitle": ParagraphStyle(
            "CoverSubtitle", parent=base["Normal"], fontName="Helvetica",
            fontSize=16, leading=22, textColor=TEAL, alignment=TA_CENTER,
            spaceAfter=26,
        ),
        "cover_meta": ParagraphStyle(
            "CoverMeta", parent=base["Normal"], fontName="Helvetica",
            fontSize=10, leading=16, textColor=INK, alignment=TA_CENTER,
            spaceAfter=4,
        ),
    }


def parse_table(lines, styles, width):
    raw_rows = []
    for line in lines:
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        if cells and all(re.fullmatch(r":?-{3,}:?", cell) for cell in cells):
            continue
        raw_rows.append(cells)
    if not raw_rows:
        return None

    column_count = max(map(len, raw_rows))
    rows = []
    for row_index, row in enumerate(raw_rows):
        row += [""] * (column_count - len(row))
        style = styles["table_head"] if row_index == 0 else styles["table"]
        rows.append([Paragraph(inline_markup(cell), style) for cell in row])

    if column_count == 5:
        widths = [width * 0.27, width * 0.18, width * 0.18, width * 0.18, width * 0.19]
    elif column_count == 3:
        widths = [width * 0.23, width * 0.36, width * 0.41]
    else:
        widths = [width / column_count] * column_count

    table = Table(rows, colWidths=widths, repeatRows=1, hAlign="LEFT")
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), NAVY),
        ("BACKGROUND", (0, 1), (-1, -1), colors.white),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, PALE_BLUE]),
        ("GRID", (0, 0), (-1, -1), 0.35, RULE),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 5),
        ("RIGHTPADDING", (0, 0), (-1, -1), 5),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]))
    return table


def parse_body(text, styles, width):
    story = []
    paragraph_lines = []
    list_items = []
    list_numbered = False
    table_lines = []

    def flush_paragraph():
        nonlocal paragraph_lines
        if paragraph_lines:
            paragraph_text = " ".join(line.strip() for line in paragraph_lines)
            story.append(Paragraph(inline_markup(paragraph_text), styles["body"]))
            paragraph_lines = []

    def flush_list():
        nonlocal list_items, list_numbered
        if list_items:
            flow = ListFlowable(
                [ListItem(Paragraph(inline_markup(item), styles["list"]), leftIndent=8) for item in list_items],
                bulletType="1" if list_numbered else "bullet",
                start="1",
                leftIndent=18,
                bulletFontName="Helvetica",
                bulletFontSize=7,
                bulletColor=TEAL,
                spaceAfter=7,
            )
            story.append(flow)
            list_items = []
            list_numbered = False

    def flush_table():
        nonlocal table_lines
        if table_lines:
            table = parse_table(table_lines, styles, width)
            if table is not None:
                story.extend([Spacer(1, 3), table, Spacer(1, 8)])
            table_lines = []

    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line:
            flush_paragraph()
            flush_list()
            flush_table()
            continue
        if line == "[[PAGEBREAK]]":
            flush_paragraph()
            flush_list()
            flush_table()
            story.append(PageBreak())
            continue
        if line == "[[ARCHITECTURE_DIAGRAM]]":
            flush_paragraph()
            flush_list()
            flush_table()
            story.extend([ArchitectureDiagram(width), Spacer(1, 2)])
            continue
        if line.startswith("|") and line.endswith("|"):
            flush_paragraph()
            flush_list()
            table_lines.append(line)
            continue
        flush_table()
        if line.startswith("### "):
            flush_paragraph()
            flush_list()
            story.append(Paragraph(inline_markup(line[4:]), styles["h2"]))
            continue
        if line.startswith("## "):
            flush_paragraph()
            flush_list()
            story.append(Paragraph(inline_markup(line[3:]), styles["h1"]))
            continue
        if line.startswith("# "):
            flush_paragraph()
            flush_list()
            story.append(Paragraph(inline_markup(line[2:]), styles["h1"]))
            continue
        if line.startswith("- "):
            flush_paragraph()
            if list_items and list_numbered:
                flush_list()
            list_numbered = False
            list_items.append(line[2:])
            continue
        numbered = re.match(r"^\d+\.\s+(.*)$", line)
        if numbered:
            flush_paragraph()
            if list_items and not list_numbered:
                flush_list()
            list_numbered = True
            list_items.append(numbered.group(1))
            continue
        if line == "---":
            flush_paragraph()
            flush_list()
            story.append(Spacer(1, 5))
            continue
        flush_list()
        paragraph_lines.append(line)

    flush_paragraph()
    flush_list()
    flush_table()
    return story


def build():
    source_text = SOURCE.read_text(encoding="utf-8")
    cover_text, body_text = source_text.split("[[PAGEBREAK]]", 1)
    styles = make_styles()
    page_width, _ = A4
    margin = 18 * mm
    content_width = page_width - 2 * margin

    doc = SimpleDocTemplate(
        str(OUTPUT), pagesize=A4,
        rightMargin=margin, leftMargin=margin,
        topMargin=19 * mm, bottomMargin=18 * mm,
        title="Final Project Report - Local RAG System",
        author="CS311 Advanced Deep Learning project",
    )

    cover_lines = [line.strip() for line in cover_text.splitlines() if line.strip()]
    title = cover_lines[0][2:]
    subtitle = cover_lines[1][3:]
    metadata = [line.replace("  ", " ").replace("**", "") for line in cover_lines[2:]]
    story = [Spacer(1, 48 * mm)]
    story.append(Paragraph(inline_markup(title), styles["cover_title"]))
    story.append(Paragraph(inline_markup(subtitle), styles["cover_subtitle"]))
    story.append(Table([[""]], colWidths=[42 * mm], rowHeights=[1.4], style=TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), TEAL),
    ]), hAlign="CENTER"))
    story.append(Spacer(1, 18 * mm))
    for line in metadata:
        if line.startswith("**"):
            line = line.replace("**", "")
        story.append(Paragraph(inline_markup(line), styles["cover_meta"]))
    story.append(Spacer(1, 35 * mm))
    story.append(Paragraph("Local models. Traceable evidence. Reproducible deployment.", styles["cover_meta"]))
    story.append(PageBreak())
    story.extend(parse_body(body_text, styles, content_width))

    def draw_page(canvas, document):
        canvas.saveState()
        if document.page > 1:
            canvas.setStrokeColor(RULE)
            canvas.setLineWidth(0.45)
            canvas.line(margin, A4[1] - 13 * mm, A4[0] - margin, A4[1] - 13 * mm)
            canvas.setFont("Helvetica", 7.5)
            canvas.setFillColor(MUTED)
            canvas.drawString(margin, A4[1] - 10 * mm, "CS311 Advanced Deep Learning | Task 5 Report")
            canvas.drawRightString(A4[0] - margin, 10 * mm, f"Fall 2026  |  {document.page}")
        canvas.restoreState()

    doc.build(story, onFirstPage=draw_page, onLaterPages=draw_page)
    print(f"Wrote {OUTPUT}")


if __name__ == "__main__":
    build()
