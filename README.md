# RDA Salesforce V3

Sistema de automatización para el procesamiento, limpieza, clasificación y generación de reportes de información proveniente de Salesforce.

## Versión

**V3**

## Descripción

RDA Salesforce V3 automatiza el procesamiento de información comercial proveniente de Salesforce para generar reportes de afluencia y facilitar el análisis de oportunidades, prospectos y eventos.

El sistema realiza procesos de limpieza, clasificación, consolidación y exportación de información.

## Estructura del proyecto

```text
RDA_SALESFORCE_V3/
│
├── reportes/
│   ├── Reporte_Afluencia_GAC.xlsx
│   └── Reporte_Afluencia_GAC_Filtrado.xlsx
│
├── static/
│   └── index.html
│
├── consolidar.py
├── eventos.py
├── exportar_excel.py
├── limpieza.py
├── oportunidades.py
├── prospectos.py
├── main.py
├── launcher.py
│
├── logo.png
├── icono.ico
│
├── RDA_GAC.spec
├── Reporte de Afluencia GAC.spec
└── Reporte_Afluencia_GAC.spec
