#!/usr/bin/env python3
"""Create narrated Task 1-4 walkthrough videos on macOS.

Requires Pillow, FFmpeg, and the macOS `say` command. Narration is generated
locally; intermediate slides and audio are kept in a temporary work folder.
"""

from __future__ import annotations

import argparse
import shutil
import subprocess
import tempfile
import textwrap
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parent.parent
OUTPUT = ROOT / "demo_video"
WIDTH, HEIGHT = 1920, 1080
BG = "#0A1425"
PANEL = "#122238"
PANEL_ALT = "#182D47"
INK = "#F4F7FB"
MUTED = "#A8B8C8"
TEAL = "#31C6B0"
GOLD = "#FFC857"
RED = "#FF786F"
RULE = "#29415D"

FONT_REGULAR = "/System/Library/Fonts/Supplemental/Arial.ttf"
FONT_BOLD = "/System/Library/Fonts/Supplemental/Arial Bold.ttf"
FONT_MONO = "/System/Library/Fonts/SFNSMono.ttf"
SCREENSHOT = ROOT / "screenshots" / "task4_answer_with_sources.png"


def F(size: int, bold: bool = False, mono: bool = False):
    path = FONT_MONO if mono else (FONT_BOLD if bold else FONT_REGULAR)
    return ImageFont.truetype(path, size)


def wrap_lines(draw: ImageDraw.ImageDraw, text: str, font, max_width: int):
    result = []
    for paragraph in text.split("\n"):
        if not paragraph:
            result.append("")
            continue
        words = paragraph.split()
        current = ""
        for word in words:
            test = f"{current} {word}".strip()
            if current and draw.textlength(test, font=font) > max_width:
                result.append(current)
                current = word
            else:
                current = test
        if current:
            result.append(current)
    return result


def paragraph(draw, text, x, y, width, font, fill=INK, leading=None, max_lines=None):
    leading = leading or int(font.size * 1.35)
    lines = wrap_lines(draw, text, font, width)
    if max_lines is not None:
        lines = lines[:max_lines]
    for line in lines:
        draw.text((x, y), line, font=font, fill=fill)
        y += leading
    return y


def rounded(draw, box, radius=22, fill=PANEL, outline=None, width=1):
    draw.rounded_rectangle(box, radius=radius, fill=fill, outline=outline, width=width)


def draw_bullets(draw, items, x, y, width, font_size=26, gap=18):
    font = F(font_size)
    for item in items:
        draw.ellipse((x, y + 9, x + 14, y + 23), fill=TEAL)
        end_y = paragraph(draw, item, x + 31, y, width - 31, font, leading=font_size + 10)
        y = end_y + gap


def draw_code_panel(draw, x, y, width, height, heading, code):
    rounded(draw, (x, y, x + width, y + height), fill="#0D192A", outline=RULE, width=2)
    draw.text((x + 26, y + 20), heading, font=F(19, bold=True), fill=TEAL)
    draw.line((x + 24, y + 57, x + width - 24, y + 57), fill=RULE, width=2)
    font = F(18, mono=True)
    line_height = 27
    max_width = width - 54
    cy = y + 77
    for raw_line in code.splitlines():
        line = raw_line.expandtabs(4)
        chunks = []
        current = ""
        for char in line:
            if current and draw.textlength(current + char, font=font) > max_width:
                chunks.append(current)
                current = ""
            current += char
        chunks.append(current)
        if not line:
            chunks = [""]
        for wrapped in chunks:
            if cy > y + height - 25:
                draw.text((x + 26, y + height - 42), "...", font=font, fill=GOLD)
                return
            draw.text((x + 26, cy), wrapped, font=font, fill=INK)
            cy += line_height


def draw_terminal_panel(draw, x, y, width, height, heading, lines):
    rounded(draw, (x, y, x + width, y + height), fill="#0B111B", outline=RULE, width=2)
    draw.text((x + 26, y + 20), heading, font=F(19, bold=True), fill=GOLD)
    draw.line((x + 24, y + 57, x + width - 24, y + 57), fill=RULE, width=2)
    font = F(19, mono=True)
    cy = y + 82
    for raw_line in lines:
        color = TEAL if raw_line.startswith("A:") or raw_line.startswith("PASS") else INK
        cy = paragraph(draw, raw_line, x + 26, cy, width - 52, font, color, leading=29) + 9
        if cy > y + height - 30:
            break


def draw_stats_panel(draw, x, y, width, height):
    rounded(draw, (x, y, x + width, y + height), fill=PANEL, outline=RULE, width=2)
    draw.text((x + 26, y + 20), "MANUALLY REVIEWED ANSWERS / 13 QUESTIONS", font=F(18, bold=True), fill=MUTED)
    cards = [
        ("qwen2.5:0.5b", "4 / 13", "fully correct", "#F1A75B"),
        ("qwen2.5:1.5b", "8 / 13", "fully correct", TEAL),
    ]
    card_y = y + 76
    card_w = (width - 76) // 2
    for i, (name, score, label, color) in enumerate(cards):
        cx = x + 26 + i * (card_w + 24)
        rounded(draw, (cx, card_y, cx + card_w, card_y + 216), radius=20, fill=PANEL_ALT)
        draw.text((cx + 22, card_y + 22), name, font=F(22, bold=True), fill=INK)
        draw.text((cx + 22, card_y + 82), score, font=F(52, bold=True), fill=color)
        draw.text((cx + 22, card_y + 146), label, font=F(23), fill=MUTED)
        draw.text((cx + 22, card_y + 184), "same index, questions, and temperature", font=F(15), fill=MUTED)
    bottom_y = card_y + 245
    breakdown = [
        ("0.5B", "1 incomplete  |  7 incorrect  |  1 source conflict"),
        ("1.5B", "1 incomplete  |  3 incorrect  |  1 source conflict"),
    ]
    for label, detail in breakdown:
        draw.text((x + 33, bottom_y), label, font=F(18, bold=True), fill=GOLD)
        draw.text((x + 120, bottom_y), detail, font=F(18), fill=INK)
        bottom_y += 43


def draw_flow_panel(draw, x, y, width, height, heading, nodes):
    rounded(draw, (x, y, x + width, y + height), fill=PANEL, outline=RULE, width=2)
    draw.text((x + 26, y + 20), heading, font=F(19, bold=True), fill=TEAL)
    cy = y + 79
    box_h = 78
    gap = 29
    node_x = x + 35
    node_w = width - 70
    for i, label in enumerate(nodes):
        rounded(draw, (node_x, cy, node_x + node_w, cy + box_h), radius=18, fill=PANEL_ALT)
        lines = wrap_lines(draw, label, F(22, bold=True), node_w - 40)
        text_h = len(lines) * 30
        ty = cy + (box_h - text_h) // 2
        for line in lines:
            tw = draw.textlength(line, font=F(22, bold=True))
            draw.text((node_x + (node_w - tw) / 2, ty), line, font=F(22, bold=True), fill=INK)
            ty += 30
        if i < len(nodes) - 1:
            mid = x + width / 2
            draw.line((mid, cy + box_h + 3, mid, cy + box_h + gap - 7), fill=TEAL, width=4)
            draw.polygon([(mid - 9, cy + box_h + gap - 13), (mid + 9, cy + box_h + gap - 13), (mid, cy + box_h + gap - 2)], fill=TEAL)
        cy += box_h + gap


def draw_screenshot_panel(draw, x, y, width, height, heading):
    rounded(draw, (x, y, x + width, y + height), fill=PANEL, outline=RULE, width=2)
    draw.text((x + 26, y + 18), heading, font=F(19, bold=True), fill=TEAL)
    im = Image.open(SCREENSHOT).convert("RGB")
    max_w, max_h = width - 66, height - 88
    im.thumbnail((max_w, max_h), Image.Resampling.LANCZOS)
    sx = x + (width - im.width) // 2
    sy = y + 67 + (max_h - im.height) // 2
    rounded(draw, (sx - 4, sy - 4, sx + im.width + 4, sy + im.height + 4), radius=8, fill="#05080D", outline=RULE, width=2)
    # Paste is performed by the caller after this helper returns its image position.
    return im, (sx, sy)


def render_slide(task_number, slide_number, title, subtitle, left_heading, bullets, right_heading, panel_type, content, takeaway):
    image = Image.new("RGB", (WIDTH, HEIGHT), BG)
    draw = ImageDraw.Draw(image)

    # Subtle framing and task progress.
    draw.rectangle((0, 0, WIDTH, 9), fill=TEAL)
    draw.text((66, 30), "CS311  |  ADVANCED DEEP LEARNING", font=F(19, bold=True), fill=MUTED)
    badge = f"TASK {task_number}  /  4     SCENE {slide_number}  /  4"
    badge_font = F(17, bold=True)
    badge_w = int(draw.textlength(badge, font=badge_font)) + 34
    rounded(draw, (WIDTH - 66 - badge_w, 24, WIDTH - 66, 66), radius=18, fill=PANEL_ALT, outline=RULE)
    draw.text((WIDTH - 66 - badge_w + 17, 35), badge, font=badge_font, fill=TEAL)

    title_font = F(55, bold=True)
    ty = 112
    ty = paragraph(draw, title, 66, ty, WIDTH - 132, title_font, INK, leading=65, max_lines=2)
    subtitle_font = F(25)
    paragraph(draw, subtitle, 68, ty + 8, WIDTH - 136, subtitle_font, MUTED, leading=34, max_lines=2)

    panel_y = 326
    panel_h = 626
    left_x, left_w = 66, 805
    right_x, right_w = 905, WIDTH - 66 - 905
    rounded(draw, (left_x, panel_y, left_x + left_w, panel_y + panel_h), radius=24, fill=PANEL, outline=RULE, width=2)
    draw.text((left_x + 28, panel_y + 24), left_heading.upper(), font=F(19, bold=True), fill=TEAL)
    draw.line((left_x + 26, panel_y + 63, left_x + left_w - 26, panel_y + 63), fill=RULE, width=2)
    draw_bullets(draw, bullets, left_x + 30, panel_y + 91, left_w - 60, font_size=25, gap=20)

    if panel_type == "code":
        draw_code_panel(draw, right_x, panel_y, right_w, panel_h, right_heading, content)
    elif panel_type == "terminal":
        draw_terminal_panel(draw, right_x, panel_y, right_w, panel_h, right_heading, content)
    elif panel_type == "stats":
        draw_stats_panel(draw, right_x, panel_y, right_w, panel_h)
    elif panel_type == "flow":
        draw_flow_panel(draw, right_x, panel_y, right_w, panel_h, right_heading, content)
    elif panel_type == "screenshot":
        im, pos = draw_screenshot_panel(draw, right_x, panel_y, right_w, panel_h, right_heading)
        image.paste(im, pos)
    elif panel_type == "cards":
        rounded(draw, (right_x, panel_y, right_x + right_w, panel_y + panel_h), radius=24, fill=PANEL, outline=RULE, width=2)
        draw.text((right_x + 26, panel_y + 22), right_heading, font=F(19, bold=True), fill=TEAL)
        cy = panel_y + 78
        for label, detail, color in content:
            rounded(draw, (right_x + 24, cy, right_x + right_w - 24, cy + 145), radius=18, fill=PANEL_ALT)
            draw.text((right_x + 45, cy + 19), label, font=F(21, bold=True), fill=color)
            paragraph(draw, detail, right_x + 45, cy + 58, right_w - 90, F(21), INK, leading=28, max_lines=3)
            cy += 165
    elif panel_type == "metrics":
        rounded(draw, (right_x, panel_y, right_x + right_w, panel_y + panel_h), radius=24, fill=PANEL, outline=RULE, width=2)
        draw.text((right_x + 26, panel_y + 22), right_heading, font=F(19, bold=True), fill=TEAL)
        cy = panel_y + 85
        for value, label, color in content:
            draw.text((right_x + 36, cy), value, font=F(45, bold=True), fill=color)
            draw.text((right_x + 260, cy + 10), label, font=F(23), fill=INK)
            cy += 108

    # Takeaway strip, deliberately short enough to read while narration plays.
    draw.line((66, 980, WIDTH - 66, 980), fill=RULE, width=2)
    draw.text((68, 998), "KEY POINT", font=F(16, bold=True), fill=GOLD)
    paragraph(draw, takeaway, 205, 993, WIDTH - 280, F(20, bold=True), INK, leading=25, max_lines=1)
    draw.text((68, 1041), "TASK 6  |  NARRATED WALKTHROUGH", font=F(14, bold=True), fill=MUTED)
    draw.text((WIDTH - 170, 1041), f"{slide_number:02d} / 04", font=F(15, bold=True), fill=MUTED)
    return image


DEMOS = [
    {
        "task": 1,
        "slug": "task1_pdf_support",
        "title": "Task 1: PDF file support",
        "scenes": [
            {
                "title": "Bring course PDFs into the RAG pipeline",
                "subtitle": "Purpose: answer from PDF content and preserve the page needed to verify each fact.",
                "left_heading": "Why this task matters",
                "bullets": [
                    "The starter application read text files only.",
                    "The extension accepts selectable-text PDFs and keeps source filenames and page numbers.",
                    "The same embedding and vector-search pipeline then works for PDF and TXT documents.",
                ],
                "right_heading": "Document-to-answer flow",
                "panel_type": "flow",
                "content": ["PDF page text", "1,000-character chunks with 200 overlap", "nomic-embed-text embeddings", "Chroma retrieval with PDF page citations"],
                "takeaway": "The key implementation change is page-aware PDF ingestion.",
                "narration": "Task 1 adds selectable-text PDF support to the starter RAG pipeline. The purpose is to answer from course documents while preserving the evidence page for review.",
            },
            {
                "title": "Extract one page at a time",
                "subtitle": "The loader stores page metadata before splitting, embedding, and indexing the text.",
                "left_heading": "Implementation steps",
                "bullets": [
                    "Use pypdf to extract text from each page.",
                    "Skip pages with no selectable text and identify image-only PDFs as needing OCR.",
                    "Split each page into overlapping chunks so nearby context is retained.",
                ],
                "right_heading": "sample_code/run_txt.py",
                "panel_type": "code",
                "content": "pdf = PdfReader(str(file_path))\nfor page_number, page in enumerate(\n        pdf.pages, start=1):\n    content = page.extract_text() or \"\"\n    if content.strip():\n        documents.append(Document(\n            page_content=content,\n            metadata={\"source\": file_path.name,\n                      \"page\": page_number}\n        ))",
                "takeaway": "Page metadata survives retrieval and appears in the answer sources.",
                "narration": "The implementation reads each PDF page with pypdf, records the filename and one-based page number, splits text into chunks of 1,000 characters with 200 characters of overlap, then embeds and stores the chunks in Chroma.",
            },
            {
                "title": "Run the PDF demonstration",
                "subtitle": "The example indexes the supplied assignment PDFs and asks a question with a known answer.",
                "left_heading": "What the run checks",
                "bullets": [
                    "Pass the assignment PDF folder as the input source.",
                    "Use --rebuild-index so the current PDF files are processed.",
                    "Check both the generated answer and the retrieved page citations.",
                ],
                "right_heading": "Verified local output",
                "panel_type": "terminal",
                "content": [
                    "$ python run_txt.py --data-dir .. \\",
                    "  --vector-store data_txt/task1_pdf_demo_store \\",
                    "  --rebuild-index --question \"How many main tasks does this final project have?\"",
                    "Indexing 41 chunks...",
                    "A: The project comprises seven (07) main tasks.",
                    "Sources: assignment PDFs, pages 6, 12, and 7",
                ],
                "takeaway": "The retrieved evidence supports the expected answer: seven project tasks.",
                "narration": "In the verified assignment-PDF demonstration, the system indexed 41 chunks. It answered that the project has seven main tasks and returned source references to the supplied PDF pages.",
            },
            {
                "title": "What Task 1 demonstrates",
                "subtitle": "PDF support is verified for selectable text; image-only scans remain a separate case.",
                "left_heading": "Result and scope",
                "bullets": [
                    "PDF pages become source documents with stable page metadata.",
                    "Retrieved chunks can be traced to their original file and page.",
                    "OCR is not implemented; scanned pages need an OCR preprocessing step.",
                ],
                "right_heading": "Processing pipeline",
                "panel_type": "flow",
                "content": ["Select PDF files", "Extract text by page", "Split, embed, and index", "Ask a question and inspect sources"],
                "takeaway": "This demo verifies the PDF path, not OCR for scanned images.",
                "narration": "This test covers PDFs with selectable text. A scanned, image-only PDF still needs OCR; that limitation is documented so the output is not mistaken for full document-image support.",
            },
        ],
    },
    {
        "task": 2,
        "slug": "task2_handbook_chatbot",
        "title": "Task 2: CS handbook chatbot",
        "scenes": [
            {
                "title": "Ground answers in one handbook",
                "subtitle": "The chatbot searches the Computer Science major handbook instead of mixing multiple majors' rules.",
                "left_heading": "Selected knowledge source",
                "bullets": [
                    "19-page B.S. Computer Science undergraduate major handbook.",
                    "Indexed on its own so other major handbooks cannot enter the answer context.",
                    "The same source is used by the CLI, evaluation script, and Task 4 web app.",
                ],
                "right_heading": "Index configuration",
                "panel_type": "metrics",
                "content": [
                    ("57", "handbook chunks in the verified Docker indexing run", TEAL),
                    ("1,000 / 200", "chunk size / overlap in characters", GOLD),
                    ("Top 5", "passages retrieved for a question", TEAL),
                    ("Page metadata", "source is shown for user verification", GOLD),
                ],
                "takeaway": "Narrow source scope makes handbook answers easier to trace.",
                "narration": "Task 2 narrows the knowledge base to the nineteen-page Computer Science major handbook. This prevents answers from mixing requirements across different majors.",
            },
            {
                "title": "Retrieve evidence before generating",
                "subtitle": "The prompt constrains the local model to answer from the retrieved handbook passages.",
                "left_heading": "Answer pipeline",
                "bullets": [
                    "Embed the question with nomic-embed-text and retrieve the top five chunks.",
                    "Use qwen2.5:1.5b at temperature 0.0 as the selected default.",
                    "Preserve qualifications and say when the handbook does not contain an answer.",
                ],
                "right_heading": "Grounded-answer prompt",
                "panel_type": "code",
                "content": "Use only the information in the context.\nDo not fill gaps with general knowledge.\nIf the context does not answer the question,\nsay you could not find it in the handbook.\n\nPreserve qualifications and cite the\nsource page when it is available.",
                "takeaway": "The prompt encourages grounded answers and abstention, but cannot guarantee either.",
                "narration": "The question pipeline embeds a query, retrieves five handbook passages, and asks Qwen 2.5 1.5B to answer only from that evidence. The prompt asks it to preserve qualifications and say when the handbook is silent.",
            },
            {
                "title": "Compare two local models",
                "subtitle": "Both models used the same index, retrieval settings, questions, and temperature.",
                "left_heading": "Evaluation method",
                "bullets": [
                    "Thirteen questions cover requirements, course data, learning outcomes, and unsupported facts.",
                    "Answers were manually checked against handbook evidence.",
                    "This is a small qualitative comparison, not a general benchmark.",
                ],
                "right_heading": "Observed outcomes",
                "panel_type": "stats",
                "content": [],
                "takeaway": "The larger model did better on this set, yet still made important errors.",
                "narration": "We manually reviewed thirteen questions for each model. The 1.5B model was fully correct on eight questions, compared with four for the 0.5B model. Both models still had one incomplete response and one source-conflict case.",
            },
            {
                "title": "Inspect the failures, not just the score",
                "subtitle": "Retrieval mistakes and source ambiguity remain visible in the evaluation.",
                "left_heading": "What still went wrong",
                "bullets": [
                    "CS 311 topics and the Core curriculum were confused with nearby sections.",
                    "The 56-credit total was not stated even when relevant page evidence was retrieved.",
                    "The handbook contradicts itself about the degree name; the chatbot did not flag it.",
                ],
                "right_heading": "Failure analysis",
                "panel_type": "cards",
                "content": [
                    ("RETRIEVAL", "Top passages can come from a semantically similar but wrong handbook section.", RED),
                    ("GENERATION", "A model can omit a requested total or misread a course-availability qualifier.", GOLD),
                    ("SOURCE QUALITY", "Citations help inspection, but cannot resolve a contradiction in the handbook.", TEAL),
                ],
                "takeaway": "Improve retrieval and document structure before relying on a larger model alone.",
                "narration": "The remaining errors show two different problems: retrieval can select the wrong section, while generation can misread or omit a qualification. Page citations help a user check the answer; they do not guarantee correctness.",
            },
        ],
    },
    {
        "task": 3,
        "slug": "task3_docker_deployment",
        "title": "Task 3: Docker deployment",
        "scenes": [
            {
                "title": "Package a reproducible RAG application",
                "subtitle": "Docker Compose runs the Python app while preserving the handbook index across container runs.",
                "left_heading": "Deployment goals",
                "bullets": [
                    "Pin the Python base image by digest and lock package versions.",
                    "Keep the selected handbook read-only inside the container.",
                    "Store Chroma data in a named volume instead of the disposable container layer.",
                ],
                "right_heading": "Runtime layout",
                "panel_type": "flow",
                "content": ["CLI or Streamlit container", "host.docker.internal:11434", "Ollama on the Mac host", "Persistent rag_index volume"],
                "takeaway": "The app container is reproducible while model inference stays on the host.",
                "narration": "Task 3 packages the RAG application so its Python environment and deployment steps can be reproduced with Docker Compose.",
            },
            {
                "title": "Compose shares one backend across two services",
                "subtitle": "The CLI and web app use the same image, handbook mount, index volume, and Ollama endpoint.",
                "left_heading": "What the configuration does",
                "bullets": [
                    "The handbook file is mounted read-only.",
                    "The named Chroma volume survives container replacement.",
                    "The web port is bound to the local computer at port 8501.",
                ],
                "right_heading": "docker-compose.yml — web service excerpt",
                "panel_type": "code",
                "content": "web:\n  build:\n    context: .\n    dockerfile: docker/Dockerfile\n  ports:\n    - \"127.0.0.1:8501:8501\"\n  volumes:\n    - ./sample_code/major_handbook_pdfs/CS_MajorHandbook.pdf:/app/major_handbook_pdfs/CS_MajorHandbook.pdf:ro\n    - rag_index:/app/data_txt\n  environment:\n    OLLAMA_URL: ${OLLAMA_URL:-http://host.docker.internal:11434}",
                "takeaway": "The compose file defines data persistence and host connectivity explicitly.",
                "narration": "The image uses a digest-pinned Python base and locked dependencies. Compose mounts the CS handbook read-only and saves Chroma data in a named volume that survives container replacement.",
            },
            {
                "title": "Start the host model and Compose service",
                "subtitle": "Ollama runs outside Docker so the Mac can manage local models and host acceleration.",
                "left_heading": "Run sequence",
                "bullets": [
                    "Start Colima or another Docker Engine.",
                    "Start Ollama on the host at port 11434.",
                    "Build and start the CLI or browser service with Compose.",
                ],
                "right_heading": "Example commands",
                "panel_type": "terminal",
                "content": [
                    "$ colima start --cpu 2 --memory 3 --disk 30",
                    "$ OLLAMA_HOST=0.0.0.0:11434 ollama serve",
                    "$ docker-compose build",
                    "$ docker-compose run --rm chatbot",
                    "# Or start the browser service:",
                    "$ docker-compose up --build web",
                ],
                "takeaway": "The container connects to Ollama through host.docker.internal.",
                "narration": "Ollama runs on the Mac host. Docker reaches it through the host gateway at port eleven thousand four hundred thirty-four, so model management stays outside the application image.",
            },
            {
                "title": "Verify a fresh index and a later reuse",
                "subtitle": "The local Docker run checked both first-time indexing and persistence.",
                "left_heading": "Observed result",
                "bullets": [
                    "A fresh named volume indexed 57 handbook chunks.",
                    "A later container reused the saved vector index.",
                    "The CS 311 prerequisite answer was CS 313, with a page 18 citation.",
                ],
                "right_heading": "Deployment checks",
                "panel_type": "metrics",
                "content": [
                    ("57", "chunks indexed on a fresh volume", TEAL),
                    ("REUSED", "vector index survived container replacement", GOLD),
                    ("CS 313", "CS 311 prerequisite returned", TEAL),
                    ("Page 18", "handbook citation displayed", GOLD),
                ],
                "takeaway": "The Docker setup passed both indexing and persistence checks.",
                "narration": "A fresh volume indexed fifty-seven handbook chunks. A later run reused that index, answered that CS 313 is the prerequisite for CS 311, and cited page eighteen.",
            },
        ],
    },
    {
        "task": 4,
        "slug": "task4_web_interface",
        "title": "Task 4: Browser-based chatbot",
        "scenes": [
            {
                "title": "Make handbook Q&A available in a browser",
                "subtitle": "The interface is designed for question input, readable history, source inspection, and clearing a session.",
                "left_heading": "User-facing features",
                "bullets": [
                    "Ask a question through Streamlit chat input.",
                    "Keep question-answer turns in browser-session history.",
                    "Expand citations showing handbook page and retrieval score.",
                    "Clear the conversation without rebuilding the index.",
                ],
                "right_heading": "Interface and backend",
                "panel_type": "flow",
                "content": ["Browser question", "Streamlit session history", "Shared run_txt.ask backend", "Answer and source pages"],
                "takeaway": "The web app reuses the same RAG logic as the command-line chatbot.",
                "narration": "Task 4 gives students a browser interface to the same RAG backend. It accepts a question, keeps a session history, and provides a clear-chat control.",
            },
            {
                "title": "Keep the web app connected to the same RAG functions",
                "subtitle": "The UI displays results from the shared retrieval path instead of implementing a separate answer engine.",
                "left_heading": "Integration details",
                "bullets": [
                    "Ollama embeddings and the Chroma handbook index are cached for the session.",
                    "Each question is passed to run_txt.ask().",
                    "The answer and up to three sources are appended to session state.",
                ],
                "right_heading": "sample_code/streamlit_app.py",
                "panel_type": "code",
                "content": "question = st.chat_input(\n    \"Nhập câu hỏi về yêu cầu ngành, môn học hoặc chuẩn đầu ra...\"\n)\nif question:\n    result = run_txt.ask(question, db, llm)\n    assistant_message = {\n        \"role\": \"assistant\",\n        \"content\": result[\"answer\"],\n        \"sources\": result[\"sources\"][:3],\n        \"used_fallback\": result[\"used_fallback\"],\n    }\n    st.session_state.messages.append(assistant_message)\n    show_sources(assistant_message)",
                "takeaway": "The interface layer preserves the existing backend behavior and citations.",
                "narration": "Streamlit passes each question to the shared ask function. The answer is shown with an expandable source panel containing PDF pages and retrieval scores.",
            },
            {
                "title": "See the real browser answer and source panel",
                "subtitle": "The screenshot is from the verified local Task 4 interface.",
                "left_heading": "What the screenshot shows",
                "bullets": [
                    "A handbook-grounded answer about declaring the CS major.",
                    "A source disclosure with three retrieved passages.",
                    "The browser view was checked after submitting two questions.",
                ],
                "right_heading": "Verified Streamlit interface",
                "panel_type": "screenshot",
                "content": [],
                "takeaway": "The browser displays both the answer and a control for opening its sources.",
                "narration": "In the browser check, the CS 311 prerequisite question returned CS 313 with a page eighteen source. The declaration question returned the two-course requirement and noted that MATH 202 counts.",
            },
            {
                "title": "Verify multiple questions and source pages",
                "subtitle": "The interface passed two known-answer checks using the selected CS handbook.",
                "left_heading": "Browser verification",
                "bullets": [
                    "Question 1: CS 311 prerequisite -> CS 313, page 18.",
                    "Question 2: declare the major -> two CS courses; MATH 202 counts.",
                    "Three retrieved passages were shown from pages 7, 7, and 4.",
                    "Both turns remained in history, and the clear-chat button was available.",
                ],
                "right_heading": "Run the web demo",
                "panel_type": "terminal",
                "content": [
                    "$ docker-compose up --build web",
                    "",
                    "Open: http://localhost:8501",
                    "",
                    "Web service: HTTP 200 OK",
                    "Backend: same handbook index and Ollama host",
                ],
                "takeaway": "The browser, session history, and source citations were verified end to end.",
                "narration": "The second answer displayed three retrieved source passages from pages seven, seven, and four. Compose exposes the interface on localhost port 8501, and the conversation history and clear button were also verified.",
            },
        ],
    },
]


def run(command):
    subprocess.run(command, check=True, stdout=subprocess.DEVNULL, timeout=120)


def probe_duration(ffprobe: str, path: Path) -> float:
    result = subprocess.run(
        [ffprobe, "-v", "error", "-show_entries", "format=duration", "-of", "default=nw=1:nk=1", str(path)],
        check=True, capture_output=True, text=True,
    )
    return float(result.stdout.strip())


def create_demo(demo, ffmpeg, ffprobe, work_dir: Path, voice: str):
    segments = []
    transcript_lines = [demo["title"], "Narration language: English", ""]

    for index, scene in enumerate(demo["scenes"], start=1):
        slide_path = work_dir / f"{demo['slug']}_{index:02d}.png"
        audio_path = work_dir / f"{demo['slug']}_{index:02d}.aiff"
        segment_path = work_dir / f"{demo['slug']}_{index:02d}.mp4"

        slide = render_slide(
            demo["task"], index,
            scene["title"], scene["subtitle"],
            scene["left_heading"], scene["bullets"],
            scene["right_heading"], scene["panel_type"], scene["content"],
            scene["takeaway"],
        )
        slide.save(slide_path, format="PNG", optimize=True)
        run(["say", "-v", voice, "-r", "170", "-o", str(audio_path), scene["narration"]])
        duration = probe_duration(ffprobe, audio_path) + 1.0
        run([
            ffmpeg, "-y", "-loglevel", "error",
            "-loop", "1", "-framerate", "24", "-i", str(slide_path),
            "-i", str(audio_path), "-t", f"{duration:.2f}",
            "-vf", "fps=24,format=yuv420p",
            "-af", "apad=pad_dur=0.8",
            "-c:v", "libx264", "-preset", "medium", "-crf", "25", "-tune", "stillimage",
            "-c:a", "aac", "-b:a", "128k", "-ar", "48000",
            "-movflags", "+faststart", str(segment_path),
        ])
        segments.append(segment_path)
        transcript_lines.append(f"Scene {index}: {scene['narration']}\n")

    concat_path = work_dir / f"{demo['slug']}_concat.txt"
    concat_path.write_text("\n".join(f"file '{segment.as_posix()}'" for segment in segments), encoding="utf-8")
    video_path = OUTPUT / f"{demo['slug']}.mp4"
    run([
        ffmpeg, "-y", "-loglevel", "error",
        "-f", "concat", "-safe", "0", "-i", str(concat_path),
        "-c:v", "libx264", "-preset", "medium", "-crf", "25",
        "-c:a", "aac", "-b:a", "128k", "-ar", "48000",
        "-pix_fmt", "yuv420p", "-movflags", "+faststart", str(video_path),
    ])
    transcript_path = OUTPUT / f"{demo['slug']}_transcript.txt"
    transcript_path.write_text("\n".join(transcript_lines).strip() + "\n", encoding="utf-8")
    return video_path, transcript_path


def main():
    parser = argparse.ArgumentParser(description="Build narrated Task 1-4 demo videos")
    parser.add_argument("--work-dir", type=Path, help="Temporary working directory for slides and audio")
    parser.add_argument("--voice", default="Daniel", help="macOS English voice name")
    parser.add_argument("--tasks", nargs="+", type=int, choices=[1, 2, 3, 4], help="Only build selected tasks")
    args = parser.parse_args()

    ffmpeg = shutil.which("ffmpeg")
    ffprobe = shutil.which("ffprobe")
    if not ffmpeg or not ffprobe or not shutil.which("say"):
        raise SystemExit("Requires ffmpeg, ffprobe, and macOS say.")
    if not SCREENSHOT.is_file():
        raise SystemExit(f"Task 4 screenshot not found: {SCREENSHOT}")

    OUTPUT.mkdir(parents=True, exist_ok=True)
    work_root = args.work_dir or Path(tempfile.gettempdir())
    work_root.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="task6-demos-", dir=work_root) as temporary:
        work_dir = Path(temporary)
        selected = [demo for demo in DEMOS if args.tasks is None or demo["task"] in args.tasks]
        for demo in selected:
            video_path, transcript_path = create_demo(demo, ffmpeg, ffprobe, work_dir, args.voice)
            duration = probe_duration(ffprobe, video_path)
            size_mb = video_path.stat().st_size / (1024 * 1024)
            print(f"{video_path.name}: {duration:.1f} seconds, {size_mb:.2f} MB")
            print(f"  transcript: {transcript_path.name}")


if __name__ == "__main__":
    main()
