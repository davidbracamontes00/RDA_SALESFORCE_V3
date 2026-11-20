import logging
import os
from pathlib import Path
import secrets
import time
from typing import Any
import zipfile

import pandas as pd

from pydantic import BaseModel, ConfigDict, Field
from fastapi import FastAPI
from fastapi import UploadFile
from fastapi import File
from fastapi import Depends
from fastapi.responses import FileResponse
from fastapi.responses import HTMLResponse
from fastapi import HTTPException
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from fastapi.staticfiles import StaticFiles
from starlette.middleware.trustedhost import TrustedHostMiddleware


from limpieza import (
    limpiar_prospectos,
    limpiar_oportunidades,
    limpiar_eventos
)

from prospectos import (
    procesar_prospectos
)

from oportunidades import (
    procesar_oportunidades
)

from eventos import (
    procesar_eventos
)

from consolidar import (
    consolidar
)

from exportar_excel import (
    exportar_excel
)


# ==========================================================
# APP
# ==========================================================

logger = logging.getLogger("rda_gac")
ENTORNO = os.getenv("RDA_ENV", "development").strip().lower()
AUTENTICACION_ACTIVA = os.getenv("RDA_AUTH_ENABLED", "false").strip().lower() in {
    "1", "true", "yes", "si", "sí"
}
USUARIO_APP = os.getenv("RDA_USERNAME", "")
CONTRASENA_APP = os.getenv("RDA_PASSWORD", "")
HOSTS_PERMITIDOS = [
    host.strip()
    for host in os.getenv("RDA_ALLOWED_HOSTS", "localhost,127.0.0.1").split(",")
    if host.strip()
]
MAX_ARCHIVO_MB = int(os.getenv("RDA_MAX_FILE_MB", "25"))
MAX_DESCOMPRIMIDO_MB = int(os.getenv("RDA_MAX_EXPANDED_MB", "128"))
RETENCION_REPORTES_DIAS = int(os.getenv("RDA_REPORT_RETENTION_DAYS", "90"))

if AUTENTICACION_ACTIVA and (not USUARIO_APP or not CONTRASENA_APP):
    raise RuntimeError(
        "RDA_AUTH_ENABLED está activo, pero faltan RDA_USERNAME o RDA_PASSWORD."
    )

es_produccion = ENTORNO == "production"
if es_produccion and not AUTENTICACION_ACTIVA:
    raise RuntimeError("La autenticación debe estar activa en producción.")
if es_produccion and len(CONTRASENA_APP) < 16:
    raise RuntimeError("En producción, RDA_PASSWORD debe tener al menos 16 caracteres.")
if es_produccion and (not HOSTS_PERMITIDOS or "*" in HOSTS_PERMITIDOS):
    raise RuntimeError("Configura RDA_ALLOWED_HOSTS con los dominios permitidos.")
if MAX_ARCHIVO_MB < 1 or MAX_ARCHIVO_MB > 100:
    raise RuntimeError("RDA_MAX_FILE_MB debe estar entre 1 y 100.")
if MAX_DESCOMPRIMIDO_MB < 16 or MAX_DESCOMPRIMIDO_MB > 512:
    raise RuntimeError("RDA_MAX_EXPANDED_MB debe estar entre 16 y 512.")
if RETENCION_REPORTES_DIAS < 0:
    raise RuntimeError("RDA_REPORT_RETENTION_DAYS no puede ser negativo.")

app = FastAPI(
    title="Reporte de Afluencia GAC",
    version="3.0.0",
    docs_url=None if es_produccion else "/docs",
    redoc_url=None if es_produccion else "/redoc",
    openapi_url=None if es_produccion else "/openapi.json"
)
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=HOSTS_PERMITIDOS
)
RUTA_STATIC = Path(__file__).parent / "static"
app.mount("/static", StaticFiles(directory=RUTA_STATIC), name="static")


@app.middleware("http")
async def agregar_cabeceras_privadas(request, call_next):
    response = await call_next(request)
    response.headers.setdefault("Cache-Control", "no-store")
    response.headers.setdefault("X-Content-Type-Options", "nosniff")
    response.headers.setdefault("Referrer-Policy", "no-referrer")
    response.headers.setdefault("X-Frame-Options", "DENY")
    return response

esquema_basico = HTTPBasic(auto_error=False)


def requerir_autenticacion(
    credenciales: HTTPBasicCredentials | None = Depends(esquema_basico)
):
    if not AUTENTICACION_ACTIVA:
        return None

    usuario_valido = bool(
        credenciales
        and secrets.compare_digest(credenciales.username, USUARIO_APP)
    )
    contrasena_valida = bool(
        credenciales
        and secrets.compare_digest(credenciales.password, CONTRASENA_APP)
    )
    if not (usuario_valido and contrasena_valida):
        logger.warning("Solicitud rechazada por credenciales inválidas.")
        raise HTTPException(
            status_code=401,
            detail="Se requieren credenciales válidas.",
            headers={"WWW-Authenticate": "Basic"}
        )
    return credenciales.username


class DescargaFiltradaRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    reporte: list[dict[str, Any]] = Field(min_length=1)
    clientes: list[dict[str, Any]] = Field(default_factory=list)

# ==========================================================
# CONFIGURACION
# ==========================================================

COLUMNAS_FINALES = [
    "APV",
    "PISO",
    "LEADS MARCA",
    "LEADS BDC",
    "PROSPECCION",
    "POP-UP STORE",
    "EVENTOS",
    "REACTIVACIONES",
    "FAN PAGE",
    "DEMOS",
    "SOLICITUDES",
    "CITAS ASISTIDAS"
]


CARPETA_REPORTES = Path(
    os.getenv("RDA_REPORTS_DIR", str(Path.home() / "Downloads"))
)




# ==========================================================
# UTILIDADES
# ==========================================================

def leer_excel(
    archivo: UploadFile
) -> pd.DataFrame:
    """
    Lee un archivo Excel recibido
    desde FastAPI.
    """

    nombre = Path(archivo.filename or "").name
    extension = Path(nombre).suffix.lower()
    if extension not in {".xlsx", ".xls"}:
        raise HTTPException(
            status_code=415,
            detail="Usa un archivo Excel con extensión .xlsx o .xls."
        )

    archivo.file.seek(0, os.SEEK_END)
    tamano = archivo.file.tell()
    archivo.file.seek(0)
    if tamano == 0:
        raise HTTPException(status_code=400, detail=f"El archivo {nombre} está vacío.")
    if tamano > MAX_ARCHIVO_MB * 1024 * 1024:
        raise HTTPException(
            status_code=413,
            detail=f"El archivo {nombre} supera el límite de {MAX_ARCHIVO_MB} MB."
        )

    firma = archivo.file.read(8)
    archivo.file.seek(0)
    firma_valida = (
        firma.startswith(b"PK") if extension == ".xlsx"
        else firma.startswith(bytes.fromhex("D0CF11E0A1B11AE1"))
    )
    if not firma_valida:
        raise HTTPException(
            status_code=415,
            detail=f"El contenido de {nombre} no coincide con un archivo Excel {extension}."
        )

    if extension == ".xlsx":
        try:
            with zipfile.ZipFile(archivo.file) as libro:
                entradas = libro.infolist()
                expandido = sum(entrada.file_size for entrada in entradas)
                comprimido = sum(entrada.compress_size for entrada in entradas)
                if len(entradas) > 10_000:
                    raise HTTPException(
                        status_code=413,
                        detail=f"El archivo {nombre} contiene demasiados componentes."
                    )
                if expandido > MAX_DESCOMPRIMIDO_MB * 1024 * 1024:
                    raise HTTPException(
                        status_code=413,
                        detail=f"El contenido descomprimido de {nombre} supera el límite."
                    )
                if comprimido == 0 or expandido / comprimido > 500:
                    raise HTTPException(
                        status_code=413,
                        detail=f"El nivel de compresión de {nombre} no es aceptable."
                    )
                if any(entrada.flag_bits & 0x1 for entrada in entradas):
                    raise HTTPException(
                        status_code=415,
                        detail=f"El archivo {nombre} está cifrado y no se puede procesar."
                    )
        except zipfile.BadZipFile as error:
            raise HTTPException(
                status_code=415,
                detail=f"El archivo {nombre} no es un libro .xlsx válido."
            ) from error
        finally:
            archivo.file.seek(0)

    try:
        return pd.read_excel(archivo.file)
    except Exception as error:
        raise ValueError(
            f"No se pudo leer {nombre}. Verifica que el archivo Excel esté íntegro."
        ) from error


def limpiar_reportes_expirados() -> None:
    """Elimina exportaciones antiguas de la carpeta exclusiva de reportes."""
    if RETENCION_REPORTES_DIAS == 0 or not CARPETA_REPORTES.is_dir():
        return

    limite = time.time() - RETENCION_REPORTES_DIAS * 24 * 60 * 60
    for archivo in CARPETA_REPORTES.glob("RDA_GAC_*.xlsx"):
        try:
            if archivo.is_file() and archivo.stat().st_mtime < limite:
                archivo.unlink()
        except OSError:
            logger.warning("No se pudo aplicar la retención de un reporte antiguo.")


def preparar_reporte_final(
    reporte_final: pd.DataFrame
) -> pd.DataFrame:
    """
    Homologa columnas y orden final.
    """

    reporte_final = reporte_final.rename(
        columns={
            "asesor": "APV"
        }
    )

    for columna in COLUMNAS_FINALES:

        if columna not in reporte_final.columns:

            if columna == "APV":
                reporte_final[columna] = ""

            else:
                reporte_final[columna] = 0

    reporte_final = (
        reporte_final[
            COLUMNAS_FINALES
        ]
        .fillna(0)
        .sort_values(
            by="APV"
        )
        .reset_index(
            drop=True
        )
    )

    return reporte_final


def guardar_excel(
    reporte_final: pd.DataFrame,
    df_clientes: pd.DataFrame,
    eventos_manana: pd.DataFrame
) -> Path:


    CARPETA_REPORTES.mkdir(parents=True, exist_ok=True)
    limpiar_reportes_expirados()

    fecha_hoy = pd.Timestamp.now().strftime(
        "%Y-%m-%d"
    )

    archivo_excel = (
        CARPETA_REPORTES
        / f"RDA_GAC_{fecha_hoy}.xlsx"
    )

    exportar_excel(
        reporte_resumen=reporte_final,
        df_clientes=df_clientes,
        eventos_manana=eventos_manana,
        ruta_salida=archivo_excel
    )

    return archivo_excel





# ==========================================================
# EXCEL FILTRADO
# ==========================================================

def guardar_excel_filtrado(
    reporte_filtrado: pd.DataFrame,
    clientes_filtrados: pd.DataFrame
) -> Path:

    CARPETA_REPORTES.mkdir(parents=True, exist_ok=True)
    limpiar_reportes_expirados()

    fecha_hoy = pd.Timestamp.now().strftime(
        "%Y-%m-%d_%H-%M-%S-%f"
    )

    archivo_excel = (
        CARPETA_REPORTES
        / f"RDA_GAC_{fecha_hoy}_Filtrado.xlsx"
    )

    exportar_excel(
        reporte_resumen=reporte_filtrado,
        df_clientes=clientes_filtrados,
        eventos_manana=pd.DataFrame(),
        ruta_salida=archivo_excel
    )

    return archivo_excel


@app.get("/", response_class=HTMLResponse)
def inicio(_usuario: str | None = Depends(requerir_autenticacion)):

    try:

        ruta_html = (
            Path(__file__).parent
            / "static"
            / "index.html"
        )

        with open(
            ruta_html,
            "r",
            encoding="utf-8"
        ) as archivo:

            return archivo.read()

    except Exception:

        logger.error("No se pudo cargar la interfaz web.")

        return HTMLResponse(
            content="""
            <h1>Error cargando index.html</h1>
            """,
            status_code=500
        )


@app.get("/healthz")
def healthz():
    """Endpoint sin datos personales para health checks del contenedor."""
    return {"status": "ok"}


@app.get("/readyz")
def readyz():
    try:
        CARPETA_REPORTES.mkdir(parents=True, exist_ok=True)
        if not os.access(CARPETA_REPORTES, os.W_OK):
            raise OSError("Report directory is not writable")
        return {"status": "ready"}
    except OSError:
        logger.error("El volumen de reportes no está disponible.")
        raise HTTPException(status_code=503, detail="El servicio no está listo.")



# ==========================================================
# DESCARGA FILTRADA
# ==========================================================

@app.post("/descargar-filtrado")
def descargar_filtrado(
    payload: DescargaFiltradaRequest,
    _usuario: str | None = Depends(requerir_autenticacion)
):

    try:

        reporte_filtrado = pd.DataFrame(
            payload.reporte
        )

        clientes_filtrados = pd.DataFrame(
            payload.clientes
        )

        archivo_excel = (
            guardar_excel_filtrado(
                reporte_filtrado,
                clientes_filtrados
            )
        )

        return FileResponse(
            path=archivo_excel,
            filename=archivo_excel.name,
            media_type=
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

    except Exception as error:
        error_id = secrets.token_hex(6)
        logger.error(
            "Falló la exportación filtrada. id=%s tipo=%s",
            error_id,
            type(error).__name__
        )
        raise HTTPException(
            status_code=500,
            detail=f"No se pudo generar el Excel. Código de error: {error_id}."
        )

        
# ==========================================================
# PROCESAMIENTO
# ==========================================================

@app.post("/procesar")
def procesar_archivos(

    prospectos: UploadFile = File(...),

    oportunidades: UploadFile = File(...),

    eventos: UploadFile = File(...),
    _usuario: str | None = Depends(requerir_autenticacion)

):

    try:


        df_prospectos = leer_excel(
            prospectos
        )

        df_oportunidades = leer_excel(
            oportunidades
        )

        df_eventos = leer_excel(
            eventos
        )



        df_prospectos = (
            limpiar_prospectos(
                df_prospectos
            )
        )

        df_oportunidades = (
            limpiar_oportunidades(
                df_oportunidades
            )
        )

        df_eventos = (
            limpiar_eventos(
                df_eventos
            )
        )



        df_prospectos_maestro = (
            procesar_prospectos(
                df_prospectos
            )
        )



        df_oportunidades_maestro = (
            procesar_oportunidades(
                df_oportunidades,
                df_prospectos_maestro
            )
        )

        # ==================================================
        # EVENTOS
        # ==================================================

        df_eventos_resumen, eventos_manana = (
            procesar_eventos( 
                df_eventos
            )
        )

        # ==================================================
        # CONSOLIDADO
        # ==================================================

        reporte_final, df_clientes = (
            consolidar(
                df_prospectos_maestro,
                df_oportunidades_maestro,
                df_eventos_resumen
            )
        )

        # ==================================================
        # REPORTE FINAL
        # ==================================================

        reporte_final = (
            preparar_reporte_final(
                reporte_final
            )
        )
        
        reporte_final = reporte_final.fillna("")
        df_clientes = df_clientes.fillna("")
        # ==================================================
        # EXCEL
        # ==================================================

        archivo_excel = guardar_excel(
            reporte_final,
            df_clientes,
            eventos_manana
        )

        # ==================================================
        # RESPUESTA
        # ==================================================

        return {
            "status": "success",

            "archivo_excel": archivo_excel.name,

            "registros": len(
                df_clientes
            ),

            "datos": reporte_final.to_dict(
                orient="records"
            ),

            "clientes": df_clientes.to_dict(
                orient="records"
            )

        }

    except HTTPException:
        raise
    except ValueError as error:
        logger.warning("Se rechazó un reporte por datos no válidos: %s", error)
        raise HTTPException(status_code=422, detail=str(error))
    except Exception as error:
        error_id = secrets.token_hex(6)
        logger.error(
            "Falló el procesamiento del reporte. id=%s tipo=%s",
            error_id,
            type(error).__name__
        )
        raise HTTPException(
            status_code=500,
            detail=f"No se pudo procesar el reporte. Código de error: {error_id}."
        )
