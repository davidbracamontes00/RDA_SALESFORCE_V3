# ==========================================================
# prospectos.py
# ==========================================================

import unicodedata

import pandas as pd

from limpieza import (
    normalizar_texto,
    validar_columnas,
    generar_cliente_id
)




COLUMNAS_REQUERIDAS = [
    "Nombre completo",
    "Teléfono",
    "Correo",
    "Sitio de origen",
    "Origen del prospecto",
    "Asesor asignado",
    "Campaña de dealer"
]


CANALES = {
    "PISO": "PISO",
    "LEADS MARCA": "LEADS MARCA",
    "LEADS BDC": "LEADS BDC",
    "CALLE": "PROSPECCION",
    "PLAZAS": "POP-UP STORE",
    "EVENTOS": "EVENTOS",
    "FAN PAGE": "FAN PAGE",
    "REACTIVACIONES": "REACTIVACIONES",
    "SIN CLASIFICAR": "SIN CLASIFICAR"
}


PALABRAS_REACTIVACION = [
    "BASE DE DATOS",
    "BDD",
    "REACTIVACION",
    "REACTIVACIÓN",
    "CARTERA"
]


PALABRAS_PLAZA = [
    "FASHION",
    "SENDERO",
    "MISIONES",
    "PLAZA",
    "CHINA MART",
    "CHINAMART",
    "ALSUPER",
    "POP-UP STORE",
    "POP UP STORE"
]


def normalizar_clasificacion(valor):
    """Normaliza texto para comparar orígenes con o sin acentos."""
    texto = normalizar_texto(valor)
    return "".join(
        caracter
        for caracter in unicodedata.normalize("NFKD", texto)
        if not unicodedata.combining(caracter)
    )


# ==========================================================
# ESTANDARIZACION
# ==========================================================

def estandarizar_columnas(df):
    """
    Permite aceptar archivos con columnas
    alternativas.
    """

    df = df.copy()

    if (
        "Nombre completo" not in df.columns
        and "Nombre" in df.columns
        and "Apellidos" in df.columns
    ):

        df["Nombre completo"] = (
            df["Nombre"]
            .fillna("")
            .astype(str)
            .str.strip()
            +
            " "
            +
            df["Apellidos"]
            .fillna("")
            .astype(str)
            .str.strip()
        ).str.strip()

    if (
        "Correo" not in df.columns
        and "Email" in df.columns
    ):
        df["Correo"] = df["Email"]

    return df


# ==========================================================
# CLIENTE ID
# ==========================================================

def crear_cliente_id(row):
    """
    Prioridad:
    1. Teléfono
    2. Correo
    3. Nombre completo
    """

    return generar_cliente_id(
        telefono=row["Teléfono"],
        correo=row["Correo"],
        nombre=row["Nombre completo"]
    )


# ==========================================================
# CLASIFICACION
# ==========================================================

def clasificar_canal(row):

    sitio = normalizar_clasificacion(
        row["Sitio de origen"]
    )

    origen = normalizar_clasificacion(
        row["Origen del prospecto"]
    )

    campaña = normalizar_clasificacion(
        row["Campaña de dealer"]
    )

    # ----------------------------------
    # PISO
    # ----------------------------------

    if origen == "PISO":
        return CANALES["PISO"]

    # BDC origins take priority over generic site labels such as MARCA.
    if (
        origen in ["GOOGLE", "META", "TIKTOK", "TIKTOK LIVE", "BDC", "LEAD BDC", "LEADS BDC"]
        or sitio in ["BDC", "LEAD BDC", "LEADS BDC"]
    ):
        return CANALES["LEADS BDC"]

    # ----------------------------------
    # META
    # ----------------------------------

    if origen == "META ASESORES":
        return CANALES["FAN PAGE"]

    # Algunos reportes ya entregan la categoría final como origen.
    # Reconocerla directamente, aunque no venga marcada como PROSPECCION
    # ni incluya una campaña de plaza.
    if (
        "POP-UP STORE" in origen
        or "POP UP STORE" in origen
        or "PLAZA" in origen
    ):
        return CANALES["PLAZAS"]

    # ----------------------------------
    # PROSPECCION
    # ----------------------------------

    if "PROSPECCION" in origen or origen.startswith("CALLE"):
        if any(palabra in campaña for palabra in PALABRAS_PLAZA):
            return CANALES["PLAZAS"]

        # Toda prospección que no se identifica como actividad de plaza
        # se cuenta en PROSPECCION, aunque la campaña esté vacía.
        return CANALES["CALLE"]

    # ----------------------------------
    # EVENTOS
    # ----------------------------------

    if origen == "EVENTO":
        return CANALES["EVENTOS"]

    # ----------------------------------
    # CARTERA
    # ----------------------------------

    if origen == "CARTERA":
        return CANALES["REACTIVACIONES"]

    # ----------------------------------
    # OTRO
    # ----------------------------------

    if origen == "OTRO":

        if any(
            palabra in campaña
            for palabra in PALABRAS_REACTIVACION
        ):
            return CANALES["REACTIVACIONES"]

    # Mantener la clasificación específica antes del origen genérico MARCA.
    if origen in ["WEB", "MARCA"] or sitio == "MARCA":
        return CANALES["LEADS MARCA"]

    return CANALES["SIN CLASIFICAR"]


# ==========================================================
# RESULTADO
# ==========================================================

def construir_resultado(df):

    telefono = (
        df["Teléfono"]
        .fillna("")
        .astype(str)
        .str.strip()
    )

    correo = (
        df["Correo"]
        .fillna("")
        .astype(str)
        .str.strip()
    )

    fecha_creacion = (
        pd.to_datetime(
            df["Fecha de creación"],
            errors="coerce"
        )
        .dt.strftime("%Y-%m-%d")
        .fillna("")
    )

    resultado = pd.DataFrame({

        "cliente_id":
            (
                df["cliente_id"]
                .fillna("")
                .astype(str)
                .str.upper()
                .str.strip()
            ),

        "cliente":
            (
                df["Nombre completo"]
                .fillna("")
                .astype(str)
                .str.strip()
            ),

        "telefono":
            telefono,

        "correo":
            correo,

        "fecha_creacion":
            fecha_creacion,

        "asesor":
            (
                df["Asesor asignado"]
                .fillna("SIN ASESOR")
                .replace("", "SIN ASESOR")
                .astype(str)
                .str.strip()
            ),

        "canal":
            (
                df["canal"]
                .fillna("")
                .astype(str)
                .str.strip()
            ),

        "origen":
            (
                df["Origen del prospecto"]
                .fillna("")
                .astype(str)
                .str.strip()
            ),

        "fuente":
            "PROSPECTO"

    })

    # Si el CRM repite un cliente y una de sus filas no tenía canal,
    # conservar la fila que sí pudo clasificarse.
    resultado["_sin_clasificar"] = (
        resultado["canal"] == CANALES["SIN CLASIFICAR"]
    ).astype("int8")
    resultado = resultado.sort_values(
        "_sin_clasificar",
        kind="stable"
    ).drop(columns="_sin_clasificar")

    resultado = resultado.drop_duplicates(
        subset=["cliente_id"],
        keep="first"
    )

    resultado = resultado.fillna("")

    resultado.reset_index(
        drop=True,
        inplace=True
    )

    return resultado


# ==========================================================
# PROCESAMIENTO
# ==========================================================

def procesar_prospectos(df):

    df = estandarizar_columnas(df)

    validar_columnas(
        df,
        COLUMNAS_REQUERIDAS
    )

    df = df.copy()

    # ----------------------------------
    # CLIENTE ID
    # ----------------------------------

    df["cliente_id"] = df.apply(
        crear_cliente_id,
        axis=1
    )

    df = df[
        df["cliente_id"].notna()
    ].copy()

    # ----------------------------------
    # CANAL
    # ----------------------------------

    df["canal"] = df.apply(
        clasificar_canal,
        axis=1
    )

    # ----------------------------------
    # RESULTADO
    # ----------------------------------

    return construir_resultado(df)
