# ==========================================================
# eventos.py
# ==========================================================

import pandas as pd
from datetime import timedelta


from limpieza import (
    normalizar_texto,
    validar_columnas,
    asegurar_columnas
)


# ==========================================================
# CONFIGURACION
# ==========================================================

COLUMNAS_REQUERIDAS = [
    "Asignado",
    "Estatus",
    "Fecha",
    "Prospecto"
]


COLUMNAS_SALIDA = [
    "CITAS ASISTIDAS",
    "DEMOS",
    "SOLICITUDES"
]


ASESOR_SIN_ASIGNAR = "SIN ASESOR"


ESTATUS_VALIDOS = {
    "REALIZADA",
    "REALIZADO",
    "COMPLETADA",
    "COMPLETADO"
}


def obtener_eventos_manana(df):
    
    df = df.copy()

    df["Fecha"] = pd.to_datetime(
        df["Fecha"],
        errors="coerce"
    )

    manana = (
        pd.Timestamp.today().normalize()
        + timedelta(days=1)
    )

    eventos = df[
        df["Fecha"].dt.normalize() == manana
    ].copy()

    eventos = clasificar_eventos(eventos)

    columnas = [
        "Asignado",
        "Prospecto",
        "Tipo",
        "Fecha",
        "Estatus"
    ]


    for columna in columnas:
        if columna not in eventos.columns:
            eventos[columna] = ""

    return (
        eventos[columnas]
        .sort_values(
            ["Asignado", "Fecha"]
        )
        .reset_index(drop=True)
    )

# ==========================================================
# EVENTO
# ==========================================================

def obtener_columna_evento(df):
    """
    Obtiene la columna donde viene
    la descripción del evento.
    """

    if "Tipo de evento" in df.columns:
        return (
            df["Tipo de evento"]
            .fillna("")
            .astype(str)
        )

    if "Asunto" in df.columns:
        return (
            df["Asunto"]
            .fillna("")
            .astype(str)
        )

    raise ValueError(
        "No existe la columna "
        "'Tipo de evento' ni 'Asunto'"
    )


# ==========================================================
# FILTRO
# ==========================================================

def filtrar_eventos_realizados(df):
    """
    Conserva únicamente eventos realizados.
    """

    return df[
        df["Estatus"]
        .apply(normalizar_texto)
        .isin(ESTATUS_VALIDOS)
    ].copy()


# ==========================================================
# CLASIFICACION
# ==========================================================

def clasificar_eventos(df):
    """
    Clasifica los eventos en:
    - CITAS ASISTIDAS
    - DEMOS
    - SOLICITUDES
    """

    df = df.copy()

    eventos = (
        obtener_columna_evento(df)
        .apply(normalizar_texto)
    )

    df["Tipo"] = None

    # --------------------------
    # CITAS
    # --------------------------

    df.loc[
        eventos.str.contains(
            r"CITA",
            na=False,
            regex=True
        ),
        "Tipo"
    ] = "CITAS ASISTIDAS"

    # --------------------------
    # DEMOS
    # --------------------------

    df.loc[
        eventos.str.contains(
            r"PRUEBA|DEMO",
            na=False,
            regex=True
        ),
        "Tipo"
    ] = "DEMOS"

    # --------------------------
    # SOLICITUDES
    # --------------------------

    df.loc[
        eventos.str.contains(
            r"SOLICITUD|CREDITO|CRÉDITO",
            na=False,
            regex=True
        ),
        "Tipo"
    ] = "SOLICITUDES"

    return df[
        df["Tipo"].notna()
    ].copy()


# ==========================================================
# RESUMEN
# ==========================================================

def generar_resumen(df):
    """
    Genera el resumen por asesor.
    """

    resumen = pd.crosstab(
        df["Asignado"],
        df["Tipo"]
    ).reset_index()

    resumen = asegurar_columnas(
        resumen,
        COLUMNAS_SALIDA,
        0
    )

    resumen = resumen[
        ["Asignado"] +
        COLUMNAS_SALIDA
    ]

    resumen = resumen.sort_values(
        by="Asignado"
    )

    resumen.reset_index(
        drop=True,
        inplace=True
    )

    return resumen


# ==========================================================
# PROCESAMIENTO
# ==========================================================

def procesar_eventos(df):
   
    validar_columnas(
        df,
        COLUMNAS_REQUERIDAS
    )

    df = df.copy()

    # --------------------------
    # ASESOR
    # --------------------------

    df["Asignado"] = (
        df["Asignado"]
        .fillna(ASESOR_SIN_ASIGNAR)
        .astype(str)
        .str.strip()
        .replace("", ASESOR_SIN_ASIGNAR)
    )

    # --------------------------
    # EVENTOS DE MAÑANA
    # --------------------------

    eventos_manana = obtener_eventos_manana(df)

    # --------------------------
    # SOLO LOS REALIZADOS
    # --------------------------

    df = filtrar_eventos_realizados(df)

    df = clasificar_eventos(df)

    resumen = generar_resumen(df)

    return resumen, eventos_manana