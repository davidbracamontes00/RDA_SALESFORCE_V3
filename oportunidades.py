# ==========================================================
# oportunidades.py
# ==========================================================

import pandas as pd

from limpieza import (
    normalizar_texto,
    validar_columnas,
    generar_cliente_id
)




COLUMNAS_REQUERIDAS = [
    "Nombre de la cuenta",
    "Nombre de la oportunidad",
    "Teléfono",
    "Cuenta personal: Email",
    "Contacto: Email",
    "Origen del prospecto",
    "Otra razón",
    "Propietario de oportunidad"
]



ORIGEN_EQUIVALENCIAS = {
    "PISO": "PISO",
    "MARCA": "LEADS MARCA",
    "META": "LEADS BDC",
    "EVENTO": "EVENTOS",
    "CARTERA": "REACTIVACIONES",
    "OTRO": "REACTIVACIONES"
}

FANPAGE_KEYWORDS = {
    "FAN PAGE",
    "FANPAGE",
    "FANEPAGE"
}


PLAZAS_KEYWORDS = {
    "FASHION",
    "FASHION MALL",
    "FASHIONMALL",
    "SENDERO",
    "MISIONES",
    "PLAZA",
    "CHINA MART",
    "CHINAMART",
    "ALSUPER",
    "SUPER" 
}

CALLE_KEYWORDS = {
    "CALLE",
    "BANCO",
    "ESCUELA",
    "SUPER MERCADO",
    "SUPERMERCADO",
    "BBVA",
    "WALMART", 
    "SENTE",
    "GOBIERNO",
    "CALLE"
}



def crear_cliente_id(row):
    """
    Prioridad:
    1. Teléfono
    2. Email cuenta personal
    3. Email contacto
    4. Nombre de cuenta
    """

    correo = row["Cuenta personal: Email"]

    if pd.isna(correo) or not str(correo).strip():
        correo = row["Contacto: Email"]
 
    nombre = row["Nombre de la oportunidad"]

    if pd.isna(nombre) or not str(nombre).strip():
        nombre = row["Nombre de la cuenta"]

    return generar_cliente_id(
        telefono=row["Teléfono"],
        correo=correo,
        nombre=nombre
    )


def clasificar_origen(row):

    origen = normalizar_texto(
        row["Origen del prospecto"]
    )

    otra_razon = normalizar_texto(
        row["Otra razón"]
    )

    # ==========================================
    # FAN PAGE
    # ==========================================
    if origen == "META ASESORES":
        return "FANPAGE"

    # ==========================================
    # EVENTOS
    # ==========================================
    if origen == "EVENTO":
        return "EVENTOS"

    # ==========================================
    # PISO
    # ==========================================
    if origen == "PISO":
        return "PISO"

    # ==========================================
    # LEADS MARCA
    # ==========================================
    if origen in {
        "WEB",
        "MARCA"
    }:
        return "LEADS MARCA"

    # ==========================================
    # LEADS BDC
    # ==========================================
    if origen in {
        "GOOGLE",
        "META",
        "TIKTOK",
        "TIKTOK LIVE"
    }:
        return "LEADS BDC"

    # ==========================================
    # REACTIVACIONES
    # ==========================================
    if origen == "CARTERA":
        return "REACTIVACIONES"

    # ==========================================
    # PLAZAS / CALLE
    # ==========================================
    if origen in {
        "PROSPECCION",
        "OTRO"
    }:

        if any(
            palabra in otra_razon
            for palabra in PLAZAS_KEYWORDS
        ):
            return "POP-UP STORE"

        if any(
            palabra in otra_razon
            for palabra in CALLE_KEYWORDS
        ):
            return "PROSPECCION"

        # Toda prospección que no sea plaza
        # se considera calle.
        if origen == "PROSPECCION":
            return "PROSPECCION"

    # ==========================================
    # SIN CLASIFICAR
    # ==========================================
    return "SIN CLASIFICAR"



def filtrar_clientes_existentes(
    df,
    df_prospectos_maestro
):

    """
    Elimina oportunidades que ya existen
    en el maestro de prospectos.
    """

    ids_existentes = set(
        df_prospectos_maestro["cliente_id"]
        .astype(str)
        .str.upper()
    )

    return df[
        ~df["cliente_id"]
        .astype(str)
        .str.upper()
        .isin(ids_existentes)
    ].copy()



def construir_resultado(df):

    correo = (
        df["Cuenta personal: Email"]
        .fillna("")
        .astype(str)
        .str.strip()
    )

    correo_contacto = (
        df["Contacto: Email"]
        .fillna("")
        .astype(str)
        .str.strip()
    )

    correo = correo.mask(
        correo == "",
        correo_contacto
    )

    telefono = (
        df["Teléfono"]
        .fillna("")
        .astype(str)
        .str.strip()
    )

    fecha_creacion = (
        pd.to_datetime(
            df["Fecha de apertura"],
            errors="coerce"
        )
        .dt.strftime("%Y-%m-%d")
        .fillna("")
    )

    resultado = pd.DataFrame({
        "cliente_id": (
            df["cliente_id"]
            .fillna("")
            .astype(str)
        ),

        "cliente": (
            df["Nombre de la cuenta"]
            .fillna("")
            .astype(str)
        ),

        "telefono": telefono,

        "correo": correo,

        "fecha_creacion": fecha_creacion,

        "asesor": (
            df["Propietario de oportunidad"]
            .fillna("")
            .astype(str)
        ),

        "canal": (
            df["canal"]
            .fillna("")
            .astype(str)
        ),

        "origen": (
            df["Origen del prospecto"]
            .fillna("")
            .astype(str)
        ),

        "fuente": "OPORTUNIDAD"
    })

    resultado = resultado.drop_duplicates(
        subset=["cliente_id"]
    )

    resultado = resultado.fillna("")

    resultado.reset_index(
        drop=True,
        inplace=True
    )

    return resultado




def procesar_oportunidades(
    df_oportunidades,
    df_prospectos_maestro
):
    """
    Procesa oportunidades y devuelve
    únicamente clientes nuevos.
    """

    validar_columnas(
        df_oportunidades,
        COLUMNAS_REQUERIDAS
    )

    df = df_oportunidades.copy()

    df["cliente_id"] = df.apply(
        crear_cliente_id,
        axis=1
    )

    df = df[
        df["cliente_id"].notna()
    ].copy()

    df["canal"] = df.apply(
        clasificar_origen,
        axis=1
    )

    return construir_resultado(df)
