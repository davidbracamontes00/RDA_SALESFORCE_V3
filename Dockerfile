FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONFAULTHANDLER=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    RDA_ENV=production \
    RDA_AUTH_ENABLED=true \
    RDA_ALLOWED_HOSTS=localhost,127.0.0.1 \
    RDA_REPORTS_DIR=/app/data/reports

LABEL org.opencontainers.image.title="RDA Salesforce GAC" \
      org.opencontainers.image.description="Procesamiento local protegido de reportes Salesforce" \
      org.opencontainers.image.source="https://github.com/davidbracamontes00/RDA_SALESFORCE_V3"

WORKDIR /app

RUN groupadd --system app \
    && useradd --system --gid app --home-dir /home/app app \
    && mkdir -p /app/data/reports \
    && chown -R app:app /app /home/app

COPY requirements.txt ./requirements.txt
RUN python -m pip install --no-cache-dir -r requirements.txt

COPY --chown=app:app *.py ./
COPY --chown=app:app logo.png ./logo.png
COPY --chown=app:app static ./static

USER app:app

EXPOSE 8000
STOPSIGNAL SIGTERM

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--proxy-headers", "--forwarded-allow-ips", "*"]
