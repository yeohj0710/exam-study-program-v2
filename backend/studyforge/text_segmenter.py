from __future__ import annotations

from dataclasses import dataclass, field
import re

QUESTION_ENDINGS = (
    "?",
    "하시오.",
    "쓰시오.",
    "고치시오.",
    "정의하시오.",
    "설명하시오.",
    "서술하시오.",
    "비교하시오.",
    "나열하시오.",
    "그리시오.",
    "논하시오.",
)

QUESTION_HINT_RE = re.compile(
    r"(무엇인가|왜|어떤|다음 중|정의|설명|서술|비교|고치|쓰시오|하시오|그리시오|나열|의미)"
)
NUMBERED_RE = re.compile(r"^\s*(?:Q\s*)?\d{1,3}[\.)]\s+\S")
SOURCE_NOTE_RE = re.compile(r"(?:p\.\s*\d+|pp\.\s*\d+|페이지|강의자료|수업자료|범위|참고)", re.IGNORECASE)


@dataclass
class TextSegment:
    front_text: str
    back_text: str
    raw_text: str
    confidence: float
    flags: list[str] = field(default_factory=list)
    line_start: int = 0
    line_end: int = 0


def normalize_lines(text: str) -> list[str]:
    normalized = text.replace("\r\n", "\n").replace("\r", "\n")
    lines = [re.sub(r"\s+", " ", line).strip() for line in normalized.split("\n")]
    return [line for line in lines if line]


def is_question_line(line: str) -> bool:
    if len(line) > 180:
        return False
    stripped = line.strip()
    if not stripped or stripped.startswith(("→", "-", "•")):
        return False
    if re.match(r"^\(\d{1,3}\)", stripped):
        return False
    if NUMBERED_RE.match(stripped) and QUESTION_HINT_RE.search(stripped):
        return True
    if stripped.endswith(QUESTION_ENDINGS):
        return True
    return bool(QUESTION_HINT_RE.search(stripped) and stripped.endswith(("?", ".")))


def split_front_back(lines: list[str]) -> tuple[str, str, list[str], float]:
    if not lines:
        return "", "", ["empty_segment"], 0.0

    flags: list[str] = []
    arrow_index = next((i for i, line in enumerate(lines) if "→" in line), None)
    if arrow_index is not None:
        split_at = max(1, arrow_index - 1)
        front_lines = lines[:split_at]
        back_lines = lines[split_at:]
        confidence = 0.88
    else:
        front_lines = [lines[0]]
        back_lines = lines[1:]
        confidence = 0.78 if back_lines else 0.42

    if back_lines and SOURCE_NOTE_RE.search(back_lines[-1]) and len(back_lines) > 1:
        flags.append("has_source_note")

    if not back_lines:
        flags.append("missing_answer")
    if len(" ".join(front_lines)) < 5:
        flags.append("short_front")
        confidence -= 0.12
    if len(" ".join(back_lines)) < 5:
        flags.append("short_back")
        confidence -= 0.16

    return "\n".join(front_lines), "\n".join(back_lines), flags, max(0.0, min(1.0, confidence))


def segment_text(text: str) -> list[TextSegment]:
    lines = normalize_lines(text)
    if not lines:
        return []

    starts = [i for i, line in enumerate(lines) if is_question_line(line)]
    if not starts:
        joined = "\n".join(lines)
        return [
            TextSegment(
                front_text=lines[0],
                back_text="\n".join(lines[1:]),
                raw_text=joined,
                confidence=0.35,
                flags=["page_fallback", "no_question_boundary"],
                line_start=0,
                line_end=len(lines),
            )
        ]

    segments: list[TextSegment] = []
    for offset, start in enumerate(starts):
        end = starts[offset + 1] if offset + 1 < len(starts) else len(lines)
        segment_lines = lines[start:end]
        front, back, flags, confidence = split_front_back(segment_lines)
        raw = "\n".join(segment_lines)
        if len(segment_lines) > 24:
            flags.append("long_segment")
            confidence -= 0.08
        segments.append(
            TextSegment(
                front_text=front,
                back_text=back,
                raw_text=raw,
                confidence=max(0.0, confidence),
                flags=flags,
                line_start=start,
                line_end=end,
            )
        )
    return segments
