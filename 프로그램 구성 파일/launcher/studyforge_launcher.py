from __future__ import annotations

import os
import socket
import sys
import threading
import time
import urllib.request
import webbrowser
from pathlib import Path

import uvicorn


def app_root() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent / "프로그램 구성 파일"
    return Path(__file__).resolve().parents[1]


def port_is_open(port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.settimeout(0.2)
        return sock.connect_ex(("127.0.0.1", port)) == 0


def find_port() -> int:
    for port in range(8765, 8786):
        if not port_is_open(port):
            return port
    raise RuntimeError("No available port found in 8765-8785.")


def open_when_ready(url: str) -> None:
    if os.environ.get("STUDYFORGE_NO_BROWSER") == "1":
        return
    for _ in range(40):
        try:
            with urllib.request.urlopen(f"{url}/api/health", timeout=1):
                webbrowser.open(url)
                return
        except Exception:
            time.sleep(0.5)
    webbrowser.open(url)


def main() -> None:
    root = app_root()
    backend = root / "backend"
    os.environ["STUDYFORGE_APP_ROOT"] = str(root)
    sys.path.insert(0, str(backend))

    from studyforge.api import app

    port = find_port()
    url = f"http://127.0.0.1:{port}"
    threading.Thread(target=open_when_ready, args=(url,), daemon=True).start()
    print(f"시험 자료 암기 프로그램 실행 중: {url}")
    print("사용하는 동안 이 창을 닫지 마세요. 종료하려면 Ctrl+C를 누르세요.")
    uvicorn.run(app, host="127.0.0.1", port=port, reload=False)


if __name__ == "__main__":
    main()
