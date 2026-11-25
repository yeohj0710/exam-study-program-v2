from __future__ import annotations

import json
import ntpath
from pathlib import Path, PureWindowsPath
from tempfile import NamedTemporaryFile
from threading import RLock
from uuid import uuid4

from .final_models import StudySet
from .hashing import slugify

_studyset_lock = RLock()
_is_windows_reserved = getattr(ntpath, "isreserved", lambda name: PureWindowsPath(name).is_reserved())


def _studyset_path(studysets_root: Path, studyset_id: str) -> Path:
    if not studyset_id or any(char in studyset_id for char in '<>:"/\\|?*'):
        raise ValueError("Invalid studyset id.")
    path = (studysets_root / f"{studyset_id}.md").resolve()
    root = studysets_root.resolve()
    if not path.is_relative_to(root):
        raise ValueError("Invalid studyset id.")
    return path


def create_studyset(studysets_root: Path, *, title: str) -> StudySet:
    slug = slugify(title)
    path = studysets_root / f"{slug}.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    with _studyset_lock:
        if not path.exists():
            path.write_text("", encoding="utf-8")
        return _studyset_from_path(path)


def read_studyset(studysets_root: Path, studyset_id: str) -> str:
    return _studyset_path(studysets_root, studyset_id).read_text(encoding="utf-8")


def save_studyset(studysets_root: Path, studyset_id: str, markdown: str, *, require_existing: bool = False) -> None:
    path = _studyset_path(studysets_root, studyset_id)
    with _studyset_lock:
        if require_existing and not path.is_file():
            raise FileNotFoundError(studyset_id)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(markdown, encoding="utf-8")


def _write_namespaces(path: Path, names: dict[str, str], pending: dict[str, str] | None = None) -> None:
    with NamedTemporaryFile(mode="w", encoding="utf-8", dir=path.parent, delete=False) as handle:
        temporary = Path(handle.name)
        try:
            json.dump({"names": names, "pending": pending}, handle, ensure_ascii=False)
            handle.close()
            temporary.replace(path)
        finally:
            handle.close()
            temporary.unlink(missing_ok=True)


def _load_namespaces(root: Path, path: Path) -> dict[str, str]:
    if not path.is_file():
        return {}
    state = json.loads(path.read_text(encoding="utf-8"))
    names = state["names"]
    pending = state.get("pending")
    if pending:
        # A rename is published by the filesystem. Recover on either side of that step.
        if (root / f"{pending['target']}.md").is_file():
            names.pop(pending["source"].casefold(), None)
            if pending["target"] != pending["namespace"]:
                names[pending["target"].casefold()] = pending["namespace"]
            else:
                names.pop(pending["target"].casefold(), None)
        _write_namespaces(path, names)
    return names


def _namespace_for(studyset_id: str, names: dict[str, str]) -> str:
    existing = names.get(studyset_id.casefold())
    if existing is not None:
        return existing
    # A newly imported set can reuse a filename while the original set still exists under a new name.
    if studyset_id.casefold() in {name.casefold() for name in names.values()}:
        return f"{studyset_id}-{uuid4().hex}"
    return studyset_id


def read_studyset_with_namespace(studysets_root: Path, studyset_id: str) -> tuple[str, str]:
    with _studyset_lock:
        markdown = read_studyset(studysets_root, studyset_id)
        path = studysets_root / ".studyset-namespaces.json"
        names = _load_namespaces(studysets_root, path)
        namespace = _namespace_for(studyset_id, names)
        if namespace != studyset_id and studyset_id.casefold() not in names:
            names[studyset_id.casefold()] = namespace
            _write_namespaces(path, names)
        return markdown, namespace


def rename_studyset(studysets_root: Path, studyset_id: str, *, title: str) -> str:
    title = title.strip()
    if not title or len(title) > 160 or title.endswith(".") or any(ord(char) < 32 for char in title):
        raise ValueError("Invalid studyset title.")
    if _is_windows_reserved(f"{title}.md"):
        raise ValueError("Invalid studyset title.")
    with _studyset_lock:
        source = _studyset_path(studysets_root, studyset_id)
        if not source.is_file():
            raise FileNotFoundError(studyset_id)
        target = _studyset_path(studysets_root, title)
        if source.stem == title:
            return title
        if any(path.stem.casefold() == title.casefold() for path in studysets_root.glob("*.md")):
            raise FileExistsError(title)

        metadata = studysets_root / ".studyset-namespaces.json"
        names = _load_namespaces(studysets_root, metadata)
        namespace = _namespace_for(source.stem, names)
        pending = {"source": source.stem, "target": title, "namespace": namespace}
        _write_namespaces(metadata, names, pending)
        try:
            source.rename(target)
        except OSError:
            _write_namespaces(metadata, names)
            raise
        # The pending entry alone suffices to recover a rename interrupted here.
        _load_namespaces(studysets_root, metadata)
        return title


def list_studysets(studysets_root: Path) -> list[StudySet]:
    if not studysets_root.exists():
        return []
    return [_studyset_from_path(path) for path in sorted(studysets_root.glob("*.md"), key=lambda item: item.name)]


def _studyset_from_path(path: Path) -> StudySet:
    slug = path.stem
    return StudySet(
        id=slug,
        title=slug,
        slug=slug,
        path=str(path),
        updated_at=path.stat().st_mtime,
    )
