from __future__ import annotations

import sys
from pathlib import Path

import uvicorn

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))


if __name__ == "__main__":
    uvicorn.run("studyforge.api:app", host="127.0.0.1", port=8765, reload=True, app_dir=str(ROOT / "backend"))
