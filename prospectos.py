# ==========================================================
# prospectos.py
# ==========================================================

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
    "CALLE": "CALLE",
    "PLAZAS": "PLAZAS",
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
    "SENDERO"
]


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

    sitio = normalizar_texto(
        row["Sitio de origen"]
    )

    origen = normalizar_texto(
        row["Origen del prospecto"]
    )

    campaña = normalizar_texto(
        row["Campaña de dealer"]
    )

    # ----------------------------------
    # PISO
    # ----------------------------------

    if origen == "PISO":
        return CANALES["PISO"]

    # ----------------------------------
    # LEADS MARCA
    # ----------------------------------

    if (
        sitio == "MARCA"
        or origen in ["WEB", "MARCA"]
    ):
        return CANALES["LEADS MARCA"]


    # ----------------------------------
    # LEADS BDC
    # ----------------------------------

    if origen in [
        "GOOGLE",
        "META",
        "TIKTOK",
        "TIKTOK LIVE"
    ]:
        return CANALES["LEADS BDC"]

    # ----------------------------------
    # META
    # ----------------------------------

    if origen == "META ASESORES":
        return CANALES["FAN PAGE"]

    # ----------------------------------
    # PROSPECCION
    # ----------------------------------

    if origen == "PROSPECCION":

        if "CALLE" in campaña:
            return CANALES["CALLE"]

        if any(
            palabra in campaña
            for palabra in PALABRAS_PLAZA
        ):
            return CANALES["PLAZAS"]

    # ----------------------------------
    # EVENTOS
    # ----------------------------------

    if sitio == "EVENTO":
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