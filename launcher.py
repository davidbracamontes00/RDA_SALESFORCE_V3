# ==========================================================
# launcher.py
# ==========================================================

import sys
import time
import threading
import socket
from pathlib import Path

import uvicorn
import webview


# ==========================================================
# CONFIGURACION
# ==========================================================

HOST = "127.0.0.1"
PORT = None

APP_TITLE = "Reporte de Afluencia GAC"


# ==========================================================
# RUTAS
# ==========================================================

def obtener_base_dir():

    if getattr(sys, "frozen", False):

        return Path(sys.executable).parent

    return Path(__file__).parent


BASE_DIR = obtener_base_dir()


INDEX_HTML = BASE_DIR / "static" / "index.html"


# ==========================================================
# SERVIDOR
# ==========================================================

from main import app


def obtener_puerto_libre():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind((HOST, 0))
        return sock.getsockname()[1]


# ==========================================================
# MAIN
# ==========================================================

if __name__ == "__main__":

    PORT = obtener_puerto_libre()
    config = uvicorn.Config(
        app,
        host=HOST,
        port=PORT,
        reload=False,
        access_log=False,
        log_config=None
    )
    servidor_http = uvicorn.Server(config)

    servidor = threading.Thread(
        target=servidor_http.run,
        daemon=True
    )

    servidor.start()

    limite = time.monotonic() + 15
    while not servidor_http.started and servidor.is_alive():
        if time.monotonic() >= limite:
            servidor_http.should_exit = True
            raise RuntimeError("El servidor local no pudo iniciar en 15 segundos.")
        time.sleep(0.05)

    if not servidor_http.started:
        raise RuntimeError("El servidor local terminó antes de iniciar.")

    webview.create_window(
        title=APP_TITLE,
        url=f"http://{HOST}:{PORT}",
        width=1400,
        height=900,
        min_size=(980, 680)
    )

    webview.start()
    servidor_http.should_exit = True
    servidor.join(timeout=5)
