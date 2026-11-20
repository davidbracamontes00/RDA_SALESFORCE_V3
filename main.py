from io import BytesIO
import os
from pathlib import Path
import secrets
from typing import Any

import pandas as pd

from pydantic import BaseModel, Field
from fastapi import FastAPI
from fastapi import UploadFile
from fastapi import File
from fastapi import Depends
from fastapi.responses import FileResponse
from fastapi.responses import HTMLResponse
from fastapi import HTTPException
from fastapi.security import HTTPBasic, HTTPBasicCredentials


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

ENTORNO = os.getenv("RDA_ENV", "development").strip().lower()
AUTENTICACION_ACTIVA = os.getenv("RDA_AUTH_ENABLED", "false").strip().lower() in {
    "1", "true", "yes", "si", "sí"
}
USUARIO_APP = os.getenv("RDA_USERNAME", "")
CONTRASENA_APP = os.getenv("RDA_PASSWORD", "")

if AUTENTICACION_ACTIVA and (not USUARIO_APP or not CONTRASENA_APP):
    raise RuntimeError(
        "RDA_AUTH_ENABLED está activo, pero faltan RDA_USERNAME o RDA_PASSWORD."
    )

es_produccion = ENTORNO == "production"
app = FastAPI(
    title="Reporte de Afluencia GAC",
    version="3.0.0",
    docs_url=None if es_produccion else "/docs",
    redoc_url=None if es_produccion else "/redoc",
    openapi_url=None if es_produccion else "/openapi.json"
)

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
        raise HTTPException(
            status_code=401,
            detail="Se requieren credenciales válidas.",
            headers={"WWW-Authenticate": "Basic"}
        )
    return credenciales.username


class DescargaFiltradaRequest(BaseModel):
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

    contenido = archivo.file.read()

    return pd.read_excel(
        BytesIO(contenido)
    )


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

    except Exception as e:

        return HTMLResponse(
            content=f"""
            <h1>Error cargando index.html</h1>
            <pre>{str(e)}</pre>
            """,
            status_code=500
        )


@app.get("/healthz")
def healthz():
    """Endpoint sin datos personales para health checks del contenedor."""
    return {"status": "ok"}



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

        print("\n================================")
        print("ERROR DESCARGA FILTRADA")
        print("================================")
        print(error)
        print("================================\n")

        raise HTTPException(status_code=400, detail=str(error))

        
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

            "archivo_excel": str(
                archivo_excel
            ),

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

    except Exception as error:

        print("\n================================")
        print("ERROR EN PROCESAMIENTO")
        print("================================")
        print(error)
        print("================================\n")

        raise HTTPException(status_code=400, detail=str(error))
