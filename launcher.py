# ==========================================================
# launcher.py
# ==========================================================

import sys
import time
import threading
from pathlib import Path

import uvicorn
import webview


# ==========================================================
# CONFIGURACION
# ==========================================================

HOST = "127.0.0.1"
PORT = 8000

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


def iniciar_servidor():

    uvicorn.run(
        app,
        host=HOST,
        port=PORT,
        reload=False,
        access_log=False,
        log_config=None
    )


# ==========================================================
# MAIN
# ==========================================================

if __name__ == "__main__":

    servidor = threading.Thread(
        target=iniciar_servidor,
        daemon=True
    )

    servidor.start()

    print("SERVIDOR INICIADO")
    time.sleep(10)

    webview.create_window(
        title=APP_TITLE,
        url=f"http://{HOST}:{PORT}",
        width=1500,
        height=950,
        min_size=(1200, 800)
    )

    webview.start()