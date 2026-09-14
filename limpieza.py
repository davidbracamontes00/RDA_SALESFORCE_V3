# ==========================================================
# limpieza.py
# ==========================================================

from typing import Iterable

import pandas as pd


# ==========================================================
# NORMALIZACION
# ==========================================================

def normalizar_texto(valor) -> str:
    """
    Convierte un valor a texto limpio y en mayúsculas.
    """

    if pd.isna(valor):
        return ""

    return str(valor).strip().upper()


def normalizar_serie(
    serie: pd.Series
) -> pd.Series:
    """
    Normaliza una serie completa.
    """

    return (
        serie.fillna("")
        .astype(str)
        .str.strip()
        .str.upper()
    )


def limpiar_texto(valor):
    """
    Limpia espacios y valores vacíos.
    """

    if pd.isna(valor):
        return None

    valor = str(valor).strip()

    if not valor:
        return None

    return valor


def limpiar_telefono(valor):
    """
    Conserva únicamente dígitos.
    """

    if pd.isna(valor):
        return None

    telefono = "".join(
        caracter
        for caracter in str(valor)
        if caracter.isdigit()
    )

    return telefono or None


def limpiar_correo(valor):
    """
    Limpia y normaliza correos.
    """

    if pd.isna(valor):
        return None

    correo = (
        str(valor)
        .strip()
        .lower()
    )

    return correo or None


# ==========================================================
# VALIDACION
# ==========================================================

def validar_columnas(
    df: pd.DataFrame,
    columnas_requeridas: Iterable[str]
) -> None:
    """
    Valida que existan todas las columnas requeridas.
    """

    faltantes = sorted(
        set(columnas_requeridas)
        - set(df.columns)
    )

    if faltantes:

        raise ValueError(
            f"Faltan columnas obligatorias: {faltantes}"
        )


# ==========================================================
# DATAFRAME HELPERS
# ==========================================================

def asegurar_columnas(
    df: pd.DataFrame,
    columnas: Iterable[str],
    valor_default=0
) -> pd.DataFrame:
    """
    Agrega columnas faltantes.
    """

    df = df.copy()

    for columna in columnas:

        if columna not in df.columns:
            df[columna] = valor_default

    return df


def eliminar_filas_vacias(
    df: pd.DataFrame
) -> pd.DataFrame:

    return df.dropna(
        how="all"
    )


# ==========================================================
# ENCABEZADOS
# ==========================================================

def normalizar_encabezados(
    df: pd.DataFrame
) -> pd.DataFrame:
    """
    Limpia nombres de columnas.
    """

    df = df.copy()

    df.columns = [

        str(columna)
        .strip()
        .replace("\n", " ")
        .replace("\r", " ")

        for columna in df.columns

    ]

    df.columns = (
        pd.Index(df.columns)
        .str.replace(
            r"\s+",
            " ",
            regex=True
        )
        .str.strip()
    )

    return df


# ==========================================================
# FECHAS
# ==========================================================

def convertir_fechas(
    df: pd.DataFrame
) -> pd.DataFrame:
    """
    Convierte automáticamente
    columnas que contienen 'fecha'.
    """

    df = df.copy()

    for columna in df.columns:

        nombre = str(columna).lower()

        if "fecha" not in nombre:
            continue

        try:

            df[columna] = pd.to_datetime(
                df[columna],
                errors="coerce"
            )

        except Exception:
            pass

    return df


# ==========================================================
# LIMPIEZA GENERICA
# ==========================================================

def limpiar_dataframe(
    df: pd.DataFrame
) -> pd.DataFrame:
    """
    Limpieza general para cualquier archivo.
    """

    df = df.copy()

    # --------------------------
    # Encabezados
    # --------------------------

    df = normalizar_encabezados(df)

    # --------------------------
    # Filas vacías
    # --------------------------

    df = eliminar_filas_vacias(df)

    # --------------------------
    # Texto
    # --------------------------

    columnas_texto = (
        df.select_dtypes(
            include=["object"]
        )
        .columns
    )

    for columna in columnas_texto:

        df[columna] = (
            df[columna]
            .apply(limpiar_texto)
        )

    # --------------------------
    # Correos
    # --------------------------

    for columna in df.columns:

        nombre = columna.lower()

        if (
            "correo" in nombre
            or "email" in nombre
        ):

            df[columna] = (
                df[columna]
                .apply(limpiar_correo)
            )

    # --------------------------
    # Teléfonos
    # --------------------------

    for columna in df.columns:

        nombre = columna.lower()

        if (
            "telefono" in nombre
            or "teléfono" in nombre
        ):

            df[columna] = (
                df[columna]
                .apply(limpiar_telefono)
            )

    # --------------------------
    # Fechas
    # --------------------------

    df = convertir_fechas(df)

    return df


# ==========================================================
# CLIENTE ID
# ==========================================================

def generar_cliente_id(
    telefono=None,
    correo=None,
    nombre=None
):
    """
    Prioridad:
    1. Teléfono
    2. Correo
    3. Nombre
    """

    telefono = limpiar_telefono(
        telefono
    )

    if telefono:
        return telefono

    correo = normalizar_texto(
        correo
    )

    if correo:
        return correo

    nombre = normalizar_texto(
        nombre
    )

    if nombre:
        return nombre

    return None


# ==========================================================
# WRAPPERS
# ==========================================================

def limpiar_prospectos(
    df: pd.DataFrame
) -> pd.DataFrame:

    return limpiar_dataframe(df)


def limpiar_oportunidades(
    df: pd.DataFrame
) -> pd.DataFrame:

    return limpiar_dataframe(df)


def limpiar_eventos(
    df: pd.DataFrame
) -> pd.DataFrame:

    return limpiar_dataframe(df)