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
from typing import Any

_DEVNULL_STREAMS = []


def app_root() -> Path:
    if getattr(sys, "frozen", False):
        exe_dir = Path(sys.executable).resolve().parent
        candidates = [exe_dir, *exe_dir.parents[:3]]
        for candidate in candidates:
            if (candidate / "backend" / "studyforge" / "api.py").exists() and (
                candidate / "dist" / "index.html"
            ).exists():
                return candidate
            for child in candidate.iterdir():
                if (child / "backend" / "studyforge" / "api.py").exists() and (
                    child / "dist" / "index.html"
                ).exists():
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


def run_server(root: Path, port: int, state: dict[str, Any]) -> None:
    backend = root / "backend"
    os.environ["STUDYFORGE_APP_ROOT"] = str(root)
    sys.path.insert(0, str(backend))

    try:
        from studyforge.api import app
        import uvicorn

        uvicorn.run(
            app,
            host="127.0.0.1",
            port=port,
            reload=False,
            access_log=False,
            log_config=None,
            log_level="warning",
        )
    except Exception:
        state["error"] = traceback.format_exc()
        write_launch_error()


def show_splash_until_ready(url: str, port: int, state: dict[str, Any]) -> None:
    if os.environ.get("STUDYFORGE_NO_SPLASH") == "1":
        open_when_ready(url)
        return

    try:
        import tkinter as tk
        from tkinter import ttk
    except Exception:
        open_when_ready(url)
        return

    ready = False
    started_at = time.monotonic()

    window = tk.Tk()
    window.title("시험 자료 암기 프로그램")
    window.geometry("460x210")
    window.resizable(False, False)
    window.configure(bg="#f7f7f8")
    window.attributes("-topmost", True)

    frame = tk.Frame(window, bg="#f7f7f8", padx=28, pady=24)
    frame.pack(fill="both", expand=True)

    mark = tk.Canvas(frame, width=48, height=48, bg="#f7f7f8", highlightthickness=0)
    mark.create_rectangle(4, 4, 44, 44, fill="#202123", outline="#202123", width=0)
    mark.create_polygon(16, 17, 31, 17, 36, 22, 36, 36, 16, 36, fill="#ffffff", outline="")
    mark.create_line(20, 26, 25, 31, 34, 21, fill="#0f766e", width=4, capstyle=tk.ROUND, joinstyle=tk.ROUND)
    mark.pack(anchor="w", pady=(0, 12))

    title = tk.Label(
        frame,
        text="StudyForge 준비 중",
        bg="#f7f7f8",
        fg="#202123",
        font=("Malgun Gothic", 14, "bold"),
    )
    title.pack(anchor="w")

    status = tk.StringVar(value="자료와 서버를 불러오는 중입니다.")
    status_label = tk.Label(frame, textvariable=status, bg="#f7f7f8", fg="#6b6f76", font=("Malgun Gothic", 10))
    status_label.pack(anchor="w", pady=(8, 14))

    progress = ttk.Progressbar(frame, mode="indeterminate", length=360)
    progress.pack(fill="x")
    progress.start(12)

    cancel = ttk.Button(frame, text="취소", command=lambda: os._exit(0))
    cancel.pack(anchor="e", pady=(16, 0))

    def center_window() -> None:
        window.update_idletasks()
        width = window.winfo_width()
        height = window.winfo_height()
        x = (window.winfo_screenwidth() - width) // 2
        y = (window.winfo_screenheight() - height) // 2
        window.geometry(f"{width}x{height}+{x}+{y}")

    def poll() -> None:
        nonlocal ready
        if state.get("error"):
            progress.stop()
            status.set("실행 오류가 발생했습니다. launcher-error.log를 확인해 주세요.")
            cancel.configure(text="닫기")
            return

        if health_for_port(port):
            ready = True
            progress.stop()
            status.set("브라우저를 여는 중입니다.")
            window.after(200, window.destroy)
            return

        elapsed = int(time.monotonic() - started_at)
        if elapsed >= 15:
            status.set("처음 실행은 준비 시간이 조금 걸릴 수 있습니다.")
        window.after(500, poll)

    window.protocol("WM_DELETE_WINDOW", lambda: os._exit(0))
    center_window()
    window.after(100, poll)
    window.mainloop()

    if ready:
        open_url(url)


def main() -> None:
    ensure_stdio()
    root = app_root()
    existing_port = find_existing_server(root)
    if existing_port is not None:
        open_url(f"http://127.0.0.1:{existing_port}")
        return

    port = find_port()
    url = f"http://127.0.0.1:{port}"
    state: dict[str, Any] = {}

    if os.environ.get("STUDYFORGE_NO_BROWSER") == "1":
        run_server(root, port, state)
        return

    server_thread = threading.Thread(target=run_server, args=(root, port, state), daemon=False)
    server_thread.start()
    show_splash_until_ready(url, port, state)
    server_thread.join()


if __name__ == "__main__":
    try:
        main()
    except Exception:
        write_launch_error()
        if not getattr(sys, "frozen", False):
            raise
