from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

import uvicorn

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=int(os.environ.get("STUDYFORGE_PORT", "8765")))
    parser.add_argument("--reload", action="store_true")
    args = parser.parse_args()

    uvicorn.run(
        "studyforge.api:app",
        host="127.0.0.1",
        port=args.port,
        reload=args.reload,
        app_dir=str(ROOT / "backend"),
    )
