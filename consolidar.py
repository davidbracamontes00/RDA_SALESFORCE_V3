# ==========================================================
# consolidar.py
# ==========================================================

import pandas as pd

from limpieza import asegurar_columnas


# ==========================================================
# CONFIGURACION
# ==========================================================

CANALES = [
    "PISO",
    "LEADS MARCA",
    "LEADS BDC",
    "CALLE",
    "PLAZAS",
    "EVENTOS",
    "FAN PAGE",
    "REACTIVACIONES"
]


EVENTOS = [
    "CITAS ASISTIDAS",
    "DEMOS",
    "SOLICITUDES"
]


# ==========================================================
# CLIENTES
# ==========================================================

def generar_clientes_unicos(
    df_prospectos,
    df_oportunidades
):
    df_clientes = pd.concat(
        [
            df_oportunidades,
            df_prospectos
        ],
        ignore_index=True
    )

    df_clientes = (
        df_clientes
        .drop_duplicates(
            subset="cliente_id",
            keep="first"
        )
        .reset_index(
            drop=True
        )
    )

    return df_clientes


# ==========================================================
# RESUMEN CLIENTES
# ==========================================================

def generar_resumen_clientes(
    df_clientes
):
    """
    Genera conteo por asesor y canal.
    """

    resumen = pd.crosstab(
        df_clientes["asesor"],
        df_clientes["canal"]
    ).reset_index()

    resumen = asegurar_columnas(
        resumen,
        CANALES,
        0
    )

    resumen = resumen[
        ["asesor"] + CANALES
    ]

    return resumen


# ==========================================================
# EVENTOS
# ==========================================================

def preparar_eventos(
    df_eventos
):
    """
    Homologa el dataframe de eventos.
    """

    df = df_eventos.copy()

    if "Asignado" in df.columns:

        df = df.rename(
            columns={
                "Asignado": "asesor"
            }
        )

    df = asegurar_columnas(
        df,
        EVENTOS,
        0
    )

    return df[
        ["asesor"] + EVENTOS
    ]

# ==========================================================
# REPORTE FINAL
# ==========================================================

def construir_reporte_final(
    resumen_clientes,
    resumen_eventos
):
    """
    Une clientes y eventos
    en un único reporte.
    """

    reporte = resumen_clientes.merge(
        resumen_eventos,
        on="asesor",
        how="outer"
    )

    columnas_numericas = (
        CANALES +
        EVENTOS
    )

    reporte = asegurar_columnas(
        reporte,
        columnas_numericas,
        0
    )

    reporte[columnas_numericas] = (
        reporte[columnas_numericas]
        .fillna(0)
        .astype(int)
    )

    reporte["asesor"] = (
        reporte["asesor"]
        .fillna("SIN ASESOR")
    )

    reporte = (
        reporte
        .sort_values(
            by="asesor"
        )
        .reset_index(
            drop=True
        )
    )

    return reporte


# ==========================================================
# CONSOLIDACION
# ==========================================================

def consolidar(
    df_prospectos,
    df_oportunidades,
    df_eventos
):
    """
    Flujo completo:

    Prospectos
    + Oportunidades
        ↓
    Clientes únicos
        ↓
    Resumen clientes
        ↓
    Resumen eventos
        ↓
    Reporte final
    """

    # ----------------------------------
    # CLIENTES UNICOS
    # ----------------------------------

    df_clientes = generar_clientes_unicos(
        df_prospectos,
        df_oportunidades
    )

    # ----------------------------------
    # RESUMEN CLIENTES
    # ----------------------------------

    resumen_clientes = (
        generar_resumen_clientes(
            df_clientes
        )
    )



    resumen_eventos = preparar_eventos(
        df_eventos
    )

    # ----------------------------------
    # REPORTE FINAL
    # ----------------------------------

    reporte_final = (
        construir_reporte_final(
            resumen_clientes,
            resumen_eventos
        )
    )

    return reporte_final, df_clientes