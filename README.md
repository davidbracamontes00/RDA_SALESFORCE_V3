# RDA Salesforce V3

Aplicación local para limpiar y clasificar reportes de Salesforce, consolidar prospectos, oportunidades y eventos, y generar reportes de afluencia en Excel.

## Tecnologías

- Python 3.12, FastAPI y Pydantic para la API.
- Pandas, OpenPyXL y Pillow para procesar y exportar Excel.
- Docker Compose para ejecutar servicios aislados.
- Nginx como proxy inverso delante de la API.
- GitHub Actions para revisar estilo Python con Ruff y construir la imagen Docker.

No se agrega una base de datos todavía: el procesamiento no necesita conservar clientes en una base entre ejecuciones. Los Excel generados se guardan en un volumen persistente de Docker.

## Ejecutar localmente con Docker

Requiere Docker Desktop en Windows/macOS o Docker Engine y el complemento Docker Compose en Linux.

1. Copia `.env.example` como `.env` y cambia la contraseña por una larga y única.
2. Inicia los servicios:

   ```powershell
   docker compose up --build -d
   ```

3. Abre [http://127.0.0.1:8080](http://127.0.0.1:8080) e inicia sesión con las credenciales de `.env`.

Los reportes quedan en el volumen `rda_reportes`. Para detener los servicios sin borrar esos archivos:

```powershell
docker compose down
```

`docker compose down -v` también elimina el volumen de reportes; úsalo solo si quieres borrar esos Excel.

## Ejecutar como aplicación de escritorio

Instala las dependencias de escritorio y ejecuta el launcher:

```powershell
python -m pip install -r requirements-desktop.txt
python launcher.py
```

El modo de escritorio no requiere credenciales por defecto. Si se configura `RDA_AUTH_ENABLED=true`, también solicitará autenticación.

## Preparación para un servidor

El Compose publica Nginx solo en `127.0.0.1:8080` de forma predeterminada. Mantén la API sin puertos públicos y coloca un proxy inverso con TLS/HTTPS delante de ese puerto en el servidor. La autenticación HTTP Basic solo protege credenciales de forma adecuada cuando se usa HTTPS. Configura el firewall para no publicar el puerto 8080 directamente.

La CI revisa Ruff y construye la imagen en cada actualización de `main` o de ramas `codex/*`, pero todavía no publica la imagen en un registro ni despliega automáticamente a un servidor. Para completar el lanzamiento falta elegir el proveedor/servidor, configurar dominio y TLS, preparar respaldos del volumen de reportes y añadir los secretos de despliegue en GitHub Actions.

## Desarrollo

```powershell
python -m pip install -r requirements-dev.txt
ruff check .
```
