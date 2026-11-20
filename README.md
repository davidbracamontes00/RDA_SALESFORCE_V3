# RDA Salesforce V3

Aplicación para limpiar y clasificar reportes de Salesforce, consolidar prospectos, oportunidades y eventos, y generar reportes de afluencia en Excel.

## Plataforma

- Python 3.12, FastAPI y Pydantic para la API.
- Pandas, OpenPyXL y Pillow para Excel.
- Docker Compose con API y proxy Nginx aislados.
- La API y el proxy corren como usuarios sin privilegios; la API no publica un puerto directamente.
- GitHub Actions revisa Ruff, audita paquetes de Python y construye la imagen.
- Dependabot propone actualizaciones semanales de dependencias, acciones y contenedores.

La aplicación no conserva clientes en una base de datos. Los Excel se guardan en un volumen Docker y se eliminan tras 90 días por defecto. Cambia `RDA_REPORT_RETENTION_DAYS` en `.env` para ajustar el periodo; `0` desactiva la limpieza automática.

## Iniciar con Docker

Requiere Docker Desktop en Windows/macOS o Docker Engine con Docker Compose en Linux.

1. Copia `.env.example` como `.env`.
2. Cambia el usuario y define una contraseña larga y única de al menos 16 caracteres. En Linux protege el archivo con `chmod 600 .env`.
3. Inicia la aplicación:

   ```powershell
   docker compose up --build -d
   ```

4. Abre [http://127.0.0.1:8080](http://127.0.0.1:8080) e inicia sesión. El navegador solicitará las credenciales.

La carga admite `.xlsx` y `.xls`, hasta 25 MB por archivo. El proxy limita cada petición a 80 MB. En `.xlsx` también se valida el tamaño descomprimido y la cantidad de componentes para rechazar archivos comprimidos sospechosos. Puedes ajustar estos límites con `RDA_MAX_FILE_MB` y `RDA_MAX_EXPANDED_MB`.

Los reportes están en el volumen `rda_reportes`. `docker compose down` conserva los datos; `docker compose down -v` los borra.

## Configurar en un servidor

1. Usa un servidor Linux con Docker Compose y cambia las credenciales de `.env`.
2. Configura `RDA_ALLOWED_HOSTS` con el dominio exacto, por ejemplo `reportes.ejemplo.com`.
3. Mantén `RDA_BIND_ADDRESS=127.0.0.1`. El puerto 8080 no debe quedar expuesto a Internet.
4. Coloca un proxy HTTPS con certificado TLS en el servidor y haz que reenvíe al puerto local configurado en `RDA_HTTP_PORT`. La autenticación básica solo es adecuada a través de HTTPS.
5. Abre en el firewall únicamente los puertos HTTPS y HTTP necesarios para el certificado y la redirección. Prepara respaldos cifrados del volumen `rda_reportes`.

Inicia o actualiza con `docker compose up --build -d` y revisa el estado con `docker compose ps`. `/healthz` comprueba que el proceso vive y `/readyz` también verifica que el volumen de reportes se pueda escribir.

La autenticación actual es una cuenta compartida para un entorno controlado. Para usuarios individuales, permisos por rol o inicio de sesión corporativo, falta integrar un proveedor de identidad antes de abrir el acceso a más personas.

## Automatización de GitHub

La CI se ejecuta en ramas `codex/*`, `main` y pull requests a `main`. Revisa el código con Ruff, ejecuta `pip-audit` y construye la imagen. Dependabot mantiene propuestas de actualización. No despliega automáticamente: el servidor, el dominio, TLS y el método de despliegue todavía dependen del entorno donde se instalará.

## Ejecutar como aplicación de escritorio

```powershell
python -m pip install -r requirements-desktop.txt
python launcher.py
```

La aplicación de escritorio mantiene la autenticación desactivada por defecto. Para revisión de código instala `requirements-dev.txt` y ejecuta `ruff check .`.
