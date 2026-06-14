from __future__ import annotations

from dataclasses import asdict
import json
from pathlib import Path
from time import time

from .final_models import QuestionProgress


def load_final_progress(path: Path) -> dict[str, QuestionProgress]:
    if not path.exists():
        return {}
    payload = json.loads(path.read_text(encoding="utf-8"))
    entries: dict[str, QuestionProgress] = {}
    for item in payload.get("questions", []):
        entry = QuestionProgress(**item)
        entries[entry.question_id] = entry
    return entries


def save_final_progress(path: Path, progress: dict[str, QuestionProgress]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "schema_version": 1,
        "updated_at": time(),
        "questions": [asdict(entry) for entry in sorted(progress.values(), key=lambda item: item.question_id)],
    }
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def record_seen(
    progress: dict[str, QuestionProgress],
    question_id: str,
    *,
    now: float | None = None,
) -> QuestionProgress:
    entry = _entry(progress, question_id)
    current_time = time() if now is None else now
    entry.seen_count += 1
    entry.last_seen_at = current_time
    entry.updated_at = current_time
    return entry


def record_reveal(
    progress: dict[str, QuestionProgress],
    question_id: str,
    *,
    now: float | None = None,
) -> QuestionProgress:
    entry = _entry(progress, question_id)
    current_time = time() if now is None else now
    entry.reveal_count += 1
    entry.updated_at = current_time
    return entry


def mark_memorized(
    progress: dict[str, QuestionProgress],
    question_id: str,
    *,
    now: float | None = None,
) -> QuestionProgress:
    entry = _entry(progress, question_id)
    current_time = time() if now is None else now
    entry.memorized = True
    entry.updated_at = current_time
    return entry


def restore_question(
    progress: dict[str, QuestionProgress],
    question_id: str,
    *,
    now: float | None = None,
) -> QuestionProgress:
    entry = _entry(progress, question_id)
    current_time = time() if now is None else now
    entry.memorized = False
    entry.updated_at = current_time
    return entry


def _entry(progress: dict[str, QuestionProgress], question_id: str) -> QuestionProgress:
    entry = progress.get(question_id)
    if entry is None:
        entry = QuestionProgress(question_id=question_id)
        progress[question_id] = entry
    return entry
