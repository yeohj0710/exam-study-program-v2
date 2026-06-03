from __future__ import annotations

import hashlib
import json
import os
import socket
import sys
import threading
import time
import traceback
import urllib.request
import webbrowser
from pathlib import Path

_DEVNULL_STREAMS = []


def app_root() -> Path:
    if getattr(sys, "frozen", False):
        exe_dir = Path(sys.executable).resolve().parent
        for child in exe_dir.iterdir():
            if (child / "backend" / "studyforge" / "api.py").exists() and (child / "dist" / "index.html").exists():
                return child
        return exe_dir
    return Path(__file__).resolve().parents[1]


def ensure_stdio() -> None:
    for name in ("stdout", "stderr"):
        if getattr(sys, name, None) is None:
            stream = open(os.devnull, "w", encoding="utf-8", buffering=1)
            setattr(sys, name, stream)
            _DEVNULL_STREAMS.append(stream)


def write_launch_error() -> None:
    try:
        log_path = app_root() / "launcher-error.log"
        with log_path.open("a", encoding="utf-8") as handle:
            handle.write(f"\n[{time.strftime('%Y-%m-%d %H:%M:%S')}]\n")
            traceback.print_exc(file=handle)
    except Exception:
        pass


def instance_id(root: Path) -> str:
    return hashlib.sha1(str(root).encode("utf-8")).hexdigest()[:16]


def port_is_open(port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.settimeout(0.2)
        return sock.connect_ex(("127.0.0.1", port)) == 0


def health_for_port(port: int) -> dict[str, object] | None:
    try:
        with urllib.request.urlopen(f"http://127.0.0.1:{port}/api/health", timeout=1) as response:
            return json.loads(response.read().decode("utf-8"))
    except Exception:
        return None


def find_existing_server(root: Path) -> int | None:
    expected_id = instance_id(root)
    for port in range(8765, 8786):
        health = health_for_port(port)
        if health and health.get("instance_id") == expected_id:
            return port
    return None


def find_port() -> int:
    for port in range(8765, 8786):
        if not port_is_open(port):
            return port
    raise RuntimeError("No available port found in 8765-8785.")


def open_when_ready(url: str) -> None:
    if os.environ.get("STUDYFORGE_NO_BROWSER") == "1":
        return
    for _ in range(240):
        try:
            with urllib.request.urlopen(f"{url}/api/health", timeout=1):
                webbrowser.open(url)
                return
        except Exception:
            time.sleep(0.5)
    webbrowser.open(url)


def open_url(url: str) -> None:
    if os.environ.get("STUDYFORGE_NO_BROWSER") == "1":
        return
    webbrowser.open(url)


def main() -> None:
    ensure_stdio()
    root = app_root()
    existing_port = find_existing_server(root)
    if existing_port is not None:
        open_url(f"http://127.0.0.1:{existing_port}")
        return

    backend = root / "backend"
    os.environ["STUDYFORGE_APP_ROOT"] = str(root)
    sys.path.insert(0, str(backend))

    from studyforge.api import app
    import uvicorn

    port = find_port()
    url = f"http://127.0.0.1:{port}"
    threading.Thread(target=open_when_ready, args=(url,), daemon=True).start()
    uvicorn.run(
        app,
        host="127.0.0.1",
        port=port,
        reload=False,
        access_log=False,
        log_config=None,
        log_level="warning",
    )


if __name__ == "__main__":
    try:
        main()
    except Exception:
        write_launch_error()
        if not getattr(sys, "frozen", False):
            raise
