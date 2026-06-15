from __future__ import annotations

from html import escape
from pathlib import Path
import re

from PIL import Image as PILImage
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A5
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import HRFlowable, Image, Paragraph, SimpleDocTemplate, Spacer

from .final_models import Question

IMAGE_RE = re.compile(r"!\[(?P<alt>[^\]]*)]\((?P<path>[^)]+)\)")
COMMENT_RE = re.compile(r"<!--.*?-->")
INLINE_TOKEN_RE = re.compile(r"(\*\*|==)(.+?)\1")
HEADING_RE = re.compile(r"^#{1,6}\s+")
LIST_MARKER_RE = re.compile(r"^\s*[-*]\s+")
ORDERED_MARKER_RE = re.compile(r"^\s*\d{1,2}[.)]\s+")
WINDOWS_SOURCE_PATH_RE = re.compile(
    r"[A-Za-z]:[\\/](?:[^+,\n\r\\/]+[\\/])*(?P<name>[^+,\n\r\\/]+\.(?:pdf|pptx?|docx?|hwp|hwpx|png|jpe?g|webp))",
    re.IGNORECASE,
)

ACCENT = "#c8403a"
TEXT = "#232624"
MUTED = "#747973"
LINE = "#d9dbd5"
ANSWER_BG = "#fff7db"
FONT_REGULAR = "StudyForgeKorean"
FONT_BOLD = "StudyForgeKorean-Bold"


def export_studyset_pdf(
    *,
    studyset_id: str,
    questions: list[Question],
    output_path: Path,
    asset_root: Path,
) -> Path:
    if not questions:
        raise ValueError("studyset PDF export requires at least one item in questions.")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    fonts = _register_fonts()
    styles = _styles(fonts["regular"], fonts["bold"])
    doc = SimpleDocTemplate(
        str(output_path),
        pagesize=A5,
        rightMargin=14 * mm,
        leftMargin=14 * mm,
        topMargin=13 * mm,
        bottomMargin=15 * mm,
        title=f"{studyset_id} 문답",
        author="Exam Study Program",
    )

    story = _build_story(studyset_id, questions, asset_root, styles)
    doc.build(
        story,
        onFirstPage=lambda canvas, document: _draw_footer(canvas, document, studyset_id, fonts["regular"]),
        onLaterPages=lambda canvas, document: _draw_footer(canvas, document, studyset_id, fonts["regular"]),
    )
    return output_path


def _build_story(
    studyset_id: str,
    questions: list[Question],
    asset_root: Path,
    styles: dict[str, ParagraphStyle],
) -> list:
    story: list = [
        Paragraph(_inline_markup(studyset_id), styles["title"]),
        Paragraph(f"{len(questions)}문항 문답 PDF", styles["subtitle"]),
        Spacer(1, 8),
    ]
    for index, question in enumerate(questions):
        if index:
            story.append(Spacer(1, 8))
            story.append(HRFlowable(width="100%", thickness=0.65, color=colors.HexColor(LINE), spaceAfter=10))
        story.append(Paragraph(f"Q{question.ordinal}", styles["question_label"]))
        story.extend(_render_markdown_block(question.prompt_markdown, asset_root, styles, style_name="body"))
        story.append(Spacer(1, 5))
        story.append(Paragraph("답", styles["answer_label"]))
        answer = question.answer_markdown.strip() or "답 없음"
        story.extend(_render_markdown_block(answer, asset_root, styles, style_name="answer"))
        if question.source_markdown.strip():
            story.append(Spacer(1, 5))
            story.append(Paragraph("출처", styles["source_label"]))
            story.extend(_render_markdown_block(question.source_markdown, asset_root, styles, style_name="source"))
    return story


def _render_markdown_block(
    markdown: str,
    asset_root: Path,
    styles: dict[str, ParagraphStyle],
    *,
    style_name: str,
) -> list:
    flowables: list = []
    for raw_line in markdown.replace("\r\n", "\n").replace("\r", "\n").split("\n"):
        line = COMMENT_RE.sub("", raw_line).strip()
        if not line:
            if flowables and not isinstance(flowables[-1], Spacer):
                flowables.append(Spacer(1, 3))
            continue

        cursor = 0
        image_found = False
        for match in IMAGE_RE.finditer(line):
            before = line[cursor : match.start()].strip()
            if before:
                flowables.append(_paragraph(before, styles, style_name))
            flowables.append(_image_flowable(match.group("path"), asset_root, styles))
            image_found = True
            cursor = match.end()
        after = line[cursor:].strip()
        if after:
            flowables.append(_paragraph(after, styles, style_name))
        elif not image_found:
            flowables.append(_paragraph(line, styles, style_name))
    return flowables


def _paragraph(line: str, styles: dict[str, ParagraphStyle], style_name: str) -> Paragraph:
    stripped = HEADING_RE.sub("", line).strip()
    if style_name == "source":
        stripped = _compact_source_references(stripped)
    is_choice = bool(LIST_MARKER_RE.match(stripped))
    if is_choice:
        stripped = LIST_MARKER_RE.sub("", stripped).strip()
        return Paragraph(f"• {_inline_markup(stripped)}", styles["choice"])
    stripped = ORDERED_MARKER_RE.sub("", stripped).strip()
    return Paragraph(_inline_markup(stripped), styles[style_name])


def _inline_markup(text: str) -> str:
    text = COMMENT_RE.sub("", text)
    text = text.replace("`", "")
    output: list[str] = []
    cursor = 0
    for match in INLINE_TOKEN_RE.finditer(text):
        output.append(escape(text[cursor : match.start()], quote=False))
        content = escape(match.group(2), quote=False)
        if match.group(1) == "**":
            output.append(f'<font color="{ACCENT}"><b>{content}</b></font>')
        else:
            output.append(f'<font backColor="{ANSWER_BG}"><b>{content}</b></font>')
        cursor = match.end()
    output.append(escape(text[cursor:], quote=False))
    return "".join(output).replace("**", "").replace("==", "")


def _compact_source_references(text: str) -> str:
    compacted = WINDOWS_SOURCE_PATH_RE.sub(lambda match: match.group("name"), text)
    return compacted.replace("\\", "/")


def _image_flowable(path_text: str, asset_root: Path, styles: dict[str, ParagraphStyle]):
    target = Path(path_text.strip())
    if not target.is_absolute():
        target = asset_root / target
    if not target.exists() or not target.is_file():
        return Paragraph(f"이미지 없음: {escape(path_text, quote=False)}", styles["missing_image"])

    with PILImage.open(target) as image:
        width, height = image.size
    max_width = A5[0] - 28 * mm
    max_height = A5[1] * 0.42
    scale = min(max_width / width, max_height / height, 1.0)
    flowable = Image(str(target), width=width * scale, height=height * scale)
    flowable.hAlign = "CENTER"
    return flowable


def _register_fonts() -> dict[str, str]:
    candidates = [
        (Path("C:/Windows/Fonts/malgun.ttf"), Path("C:/Windows/Fonts/malgunbd.ttf")),
        (Path("C:/Windows/Fonts/NanumGothic.ttf"), Path("C:/Windows/Fonts/NanumGothicBold.ttf")),
    ]
    for regular, bold in candidates:
        if regular.exists():
            _register_ttf(FONT_REGULAR, regular)
            _register_ttf(FONT_BOLD, bold if bold.exists() else regular)
            return {"regular": FONT_REGULAR, "bold": FONT_BOLD}
    return {"regular": "Helvetica", "bold": "Helvetica-Bold"}


def _register_ttf(font_name: str, path: Path) -> None:
    if font_name in pdfmetrics.getRegisteredFontNames():
        return
    pdfmetrics.registerFont(TTFont(font_name, str(path)))


def _styles(font_regular: str, font_bold: str) -> dict[str, ParagraphStyle]:
    base = getSampleStyleSheet()
    return {
        "title": ParagraphStyle(
            "StudyPdfTitle",
            parent=base["Title"],
            fontName=font_bold,
            fontSize=16,
            leading=20,
            textColor=colors.HexColor(TEXT),
            alignment=TA_CENTER,
            spaceAfter=2,
        ),
        "subtitle": ParagraphStyle(
            "StudyPdfSubtitle",
            parent=base["BodyText"],
            fontName=font_regular,
            fontSize=8.8,
            leading=11,
            textColor=colors.HexColor(MUTED),
            alignment=TA_CENTER,
            spaceAfter=8,
        ),
        "question_label": ParagraphStyle(
            "StudyPdfQuestionLabel",
            parent=base["BodyText"],
            fontName=font_bold,
            fontSize=10.8,
            leading=13,
            textColor=colors.HexColor(ACCENT),
            spaceBefore=2,
            spaceAfter=5,
        ),
        "body": ParagraphStyle(
            "StudyPdfBody",
            parent=base["BodyText"],
            fontName=font_regular,
            fontSize=10.2,
            leading=15,
            textColor=colors.HexColor(TEXT),
            alignment=TA_LEFT,
            spaceAfter=3,
        ),
        "choice": ParagraphStyle(
            "StudyPdfChoice",
            parent=base["BodyText"],
            fontName=font_regular,
            fontSize=9.8,
            leading=14,
            textColor=colors.HexColor(TEXT),
            leftIndent=8,
            spaceAfter=2.5,
        ),
        "answer_label": ParagraphStyle(
            "StudyPdfAnswerLabel",
            parent=base["BodyText"],
            fontName=font_bold,
            fontSize=9.8,
            leading=12,
            textColor=colors.HexColor(ACCENT),
            spaceBefore=4,
            spaceAfter=3,
        ),
        "answer": ParagraphStyle(
            "StudyPdfAnswer",
            parent=base["BodyText"],
            fontName=font_bold,
            fontSize=10,
            leading=14.5,
            textColor=colors.HexColor(TEXT),
            backColor=colors.HexColor("#fffdf4"),
            borderColor=colors.HexColor("#eee3be"),
            borderWidth=0.4,
            borderPadding=5,
            spaceAfter=4,
        ),
        "source_label": ParagraphStyle(
            "StudyPdfSourceLabel",
            parent=base["BodyText"],
            fontName=font_bold,
            fontSize=8.4,
            leading=10,
            textColor=colors.HexColor(MUTED),
            spaceBefore=2,
            spaceAfter=2,
        ),
        "source": ParagraphStyle(
            "StudyPdfSource",
            parent=base["BodyText"],
            fontName=font_regular,
            fontSize=7.7,
            leading=10.5,
            textColor=colors.HexColor(MUTED),
            spaceAfter=2,
        ),
        "missing_image": ParagraphStyle(
            "StudyPdfMissingImage",
            parent=base["BodyText"],
            fontName=font_regular,
            fontSize=7.8,
            leading=10,
            textColor=colors.HexColor(ACCENT),
            spaceAfter=3,
        ),
    }


def _draw_footer(canvas, document, studyset_id: str, font_name: str) -> None:
    canvas.saveState()
    canvas.setFont(font_name, 7)
    canvas.setFillColor(colors.HexColor(MUTED))
    canvas.drawString(document.leftMargin, 7 * mm, studyset_id)
    canvas.drawRightString(A5[0] - document.rightMargin, 7 * mm, str(document.page))
    canvas.restoreState()
