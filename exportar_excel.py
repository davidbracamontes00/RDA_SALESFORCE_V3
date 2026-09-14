# ==========================================================
# exportar_excel.py
# ==========================================================

import pandas as pd
from openpyxl.drawing.image import Image
from openpyxl.styles import (
    Font,
    PatternFill,
    Alignment,
    Border,
    Side
)

from openpyxl.utils import (
    get_column_letter
)


# ==========================================================
# CONFIGURACION
# ==========================================================

HOJAS_CANALES = [
    "PISO",
    "LEADS MARCA",
    "LEADS BDC",
    "CALLE",
    "PLAZAS",
    "EVENTOS",
    "REACTIVACIONES",
    "FAN PAGE"
]


COLUMNAS_DETALLE = [
    "cliente",
    "telefono",
    "correo",
    "fecha_creacion",
    "asesor",
    "canal",
    "origen",
    "fuente"
]


# ==========================================================
# ESTILOS
# ==========================================================

COLOR_GAC = "8B0000"
COLOR_HEADER = "C0C0C0"
COLOR_BORDE = "404040"


FUENTE_TITULO = Font(
    bold=True,
    size=18,
    color="FFFFFF"
)

FUENTE_HEADER = Font(
    bold=True,
    color="000000"
)

BORDE = Border(
    left=Side(
        style="thin",
        color=COLOR_BORDE
    ),
    right=Side(
        style="thin",
        color=COLOR_BORDE
    ),
    top=Side(
        style="thin",
        color=COLOR_BORDE
    ),
    bottom=Side(
        style="thin",
        color=COLOR_BORDE
    )
)

# ==========================================================
# LOGO
# ==========================================================

def aplicar_logo(
    hoja,
    ruta_logo
):

    logo = Image("logo.png")

    logo.width = 170
    logo.height = 110

    hoja.add_image(
        logo,
        "A1"
    )

# ==========================================================
# ENCABEZADO
# ==========================================================

def aplicar_encabezado(hoja):

    fecha = pd.Timestamp.now().strftime("%d/%m/%Y")


    for fila in range(1, 7):

        for columna in range(1, hoja.max_column + 1):

            hoja.cell(
                fila,
                columna
            ).fill = PatternFill(
                fill_type="solid",
                fgColor="C3C3C3"
            )


    # --------------------------------------------------
    # TITULO
    # --------------------------------------------------

    hoja["C2"] = "GAC MOTOR"

    hoja["C2"].font = Font(
        size=30,
        bold=True,
        color=COLOR_GAC
    )

    # --------------------------------------------------
    # SUBTITULO
    # --------------------------------------------------

    hoja["C3"] = "REPORTE DIARIO DE AFLUENCIA"

    hoja["C3"].font = Font(
        size=15,
        bold=True,
        color="404040"
    )

    # --------------------------------------------------
    # INFORMACION
    # --------------------------------------------------

    hoja["C4"] = f"Generado automáticamente • {fecha}"

    hoja["C4"].font = Font(
        size=10,
        italic=True,
        color="7A7A7A"
    )

    # --------------------------------------------------
    # FRANJA ROJA
    # --------------------------------------------------

    for columna in range(1, hoja.max_column + 1):

        celda = hoja.cell(
            row=6,
            column=columna
        )

        celda.fill = PatternFill(
            fill_type="solid",
            fgColor=COLOR_GAC
        )

    # --------------------------------------------------
    # ALINEACION
    # --------------------------------------------------

    for fila in (2, 3, 4):

        hoja[f"D{fila}"].alignment = Alignment(
            vertical="center",
            horizontal="center",
        )

# ==========================================================
# ENCABEZADOS_tabla
# ==========================================================

def aplicar_encabezados_tabla(hoja):

    fila_header = 7

    for celda in hoja[fila_header]:

        celda.alignment = Alignment(
            horizontal="center"
        )

        celda.border = BORDE


# ==========================================================
# MARCO ENCABEZADO
# ==========================================================

def aplicar_marco_encabezado(hoja):

    ultima_columna = get_column_letter(
        hoja.max_column
    )

    # Fondo blanco
    for fila in hoja.iter_rows(
        min_row=1,
        max_row=6,
        min_col=1,
        max_col=hoja.max_column
    ):

        for celda in fila:

            celda.fill = PatternFill(
                fill_type="solid",
                fgColor="FFFFFF"
            )

    borde_grueso = Side(
        style="medium",
        color="B7B7B7"
    )

    # Marco exterior
    for columna in range(1, hoja.max_column + 1):

        hoja.cell(1, columna).border = Border(
            top=borde_grueso
        )

        hoja.cell(6, columna).border = Border(
            bottom=Side(
                style="medium",
                color=COLOR_GAC
            )
        )

    for fila in range(1, 7):

        hoja.cell(fila, 1).border = Border(
            left=borde_grueso
        )

        hoja.cell(
            fila,
            hoja.max_column
        ).border = Border(
            right=borde_grueso
        )



# ==========================================================
# FILTROS
# ==========================================================

def aplicar_filtros(hoja):

    ultima_fila = hoja.max_row
    ultima_columna = hoja.max_column

    rango = f"A7:{get_column_letter(ultima_columna)}{ultima_fila}"

    hoja.auto_filter.ref = rango

# ==========================================================
# BORDES
# ==========================================================

def aplicar_bordes(hoja):

    for fila in hoja.iter_rows(
        min_row=7,
        max_row=hoja.max_row,
        min_col=1,
        max_col=hoja.max_column
    ):

        for celda in fila:

            celda.border = BORDE


# ==========================================================
# ANCHO COLUMNAS
# ==========================================================

def ajustar_ancho_columnas(hoja):

    for columna in hoja.columns:

        longitud_maxima = 0

        try:
            letra = columna[0].column_letter
        except Exception:
            continue
        
        
        if letra == "A":
            hoja.column_dimensions["A"].width = 35
            continue


        for celda in columna:

            try:

                valor = ""

                if celda.value is not None:
                    valor = str(celda.value)

                longitud_maxima = max(
                    longitud_maxima,
                    len(valor)
                )

            except Exception:
                pass

        ancho = min(
            max(
                longitud_maxima + 4,
                12
            ),
            50
        )

        hoja.column_dimensions[
            letra
        ].width = ancho


# ==========================================================
# ALINEACION
# ==========================================================

def aplicar_alineacion(hoja):

    for fila in hoja.iter_rows(
        min_row=8,
        max_row=hoja.max_row
    ):

        for celda in fila:

            celda.alignment = Alignment(
                vertical="center"
            )


# ==========================================================
# FORMATO GENERAL
# ==========================================================

def formatear_hoja(
    hoja,
    nombre_hoja=None
):
    aplicar_marco_encabezado(
        hoja
    )

    aplicar_logo(
        hoja,
        "logo.png"
    )

    aplicar_encabezado(
        hoja
    )


    
    aplicar_colores_por_canal(
        hoja,
        nombre_hoja
    )

    
    aplicar_encabezados_tabla(
        hoja
    )

   
    aplicar_bordes(
        hoja
    )

   
    aplicar_filtros(
        hoja
    )

    
    aplicar_alineacion(
        hoja
    )

    ajustar_ancho_columnas(
        hoja
    )

    aplicar_congelado(
        hoja
    )


# ==========================================================
# COLORES POR CANAL
# ==========================================================

def aplicar_colores_por_canal(
    hoja,
    nombre_hoja
):

    colores = {
        "RESUMEN": "8B0000",          
        "PISO": "1F4E78",             
        "LEADS MARCA": "70AD47",      
        "LEADS BDC": "ED7D31",        
        "CALLE": "7F7F7F",            
        "PLAZAS": "7030A0",            
        "EVENTOS": "FFC000",          
        "REACTIVACIONES": "C00000",   
        "FAN PAGE": "5B9BD5",  
        "EVENTOS MAÑANA": "4472C4",       
        "INFO": "A5A5A5" 
    }

    color = colores.get(
        nombre_hoja,
        COLOR_HEADER
    )

    
    hoja.sheet_properties.tabColor = color

    for celda in hoja[7]:

        celda.fill = PatternFill(
            fill_type="solid",
            fgColor=color
        )

        celda.font = Font(
            bold=True,
            color="FFFFFF"
        )





# ==========================================================
# CONGELAR PANELES
# ==========================================================

def aplicar_congelado(hoja):
    hoja.freeze_panes = "B8"



# ==========================================================
# EXPORTAR
# ==========================================================

def exportar_excel(
    reporte_resumen,
    df_clientes,
    eventos_manana,
    ruta_salida
):

    with pd.ExcelWriter(
        ruta_salida,
        engine="openpyxl"
    ) as writer:

        # ==================================
        # RESUMEN
        # ==================================

        reporte_resumen.to_excel(
            writer,
            sheet_name="RESUMEN",
            startrow=6,
            index=False
        )

        hoja_resumen = writer.sheets[
            "RESUMEN"
        ]

        formatear_hoja(
            hoja_resumen,
            "RESUMEN"
        )

        # ==================================
        # DETALLE POR CANAL
        # ==================================

        for canal in HOJAS_CANALES:

            detalle = (
                df_clientes[
                    df_clientes["canal"] == canal
                ]
                .copy()
            )

            for columna in COLUMNAS_DETALLE:

                if columna not in detalle.columns:
                    detalle[columna] = ""

            detalle = (
                detalle[
                    COLUMNAS_DETALLE
                ]
                .sort_values(
                    by=[
                        "asesor",
                        "cliente"
                    ]
                )
                .reset_index(
                    drop=True
                )
            )

            nombre_hoja = canal[:31]

            detalle.to_excel(
                writer,
                sheet_name=nombre_hoja,
                startrow=6,
                index=False
            )

            hoja = writer.sheets[
                nombre_hoja
            ]

            formatear_hoja(
                hoja,
                nombre_hoja
            )

        # ==================================
        # EVENTOS MAÑANA
        # ==================================

        eventos_manana.to_excel(
            writer,
            sheet_name="EVENTOS MAÑANA",
            startrow=6,
            index=False
        )

        hoja_eventos = writer.sheets[
            "EVENTOS MAÑANA"
        ]

        formatear_hoja(
            hoja_eventos,
            "EVENTOS MAÑANA"
        )

        # ==================================
        # HOJA INFORMACION
        # ==================================

        info = pd.DataFrame({

            "Información": [

                "GAC MOTOR",

                "Reporte generado automáticamente",

                f"Total clientes: {len(df_clientes)}",

                f"Fecha generación: {pd.Timestamp.now():%Y-%m-%d %H:%M}"

            ]

        })

        info.to_excel(
            writer,
            sheet_name="INFO",
            startrow=6,
            index=False
        )

        hoja_info = writer.sheets[
            "INFO"
        ]

        formatear_hoja(
            hoja_info,
            "INFO"
        )

        # ==================================
        # GUARDAR
        # ==================================

        workbook = writer.book

        for hoja in workbook.worksheets:

            hoja.sheet_view.showGridLines = False