# Multi-stage Dockerfile para Agente IA DSpace-CRIS V3.0
FROM python:3.11-slim as base

# Evitar generación de bytecode .pyc innecesario y forzar stdout sin buffer
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Instalar dependencias del sistema requeridas
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Instalar dependencias de Python
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt \
    && pip install --no-cache-dir celery==5.3.6 beautifulsoup4==4.12.3

# Copiar el código del proyecto
COPY . /app/

# Crear usuario no privilegiado para ejecución segura en producción
RUN useradd -u 1001 -m appuser && chown -R appuser:appuser /app
USER appuser

EXPOSE 8000

# Comando por defecto para levantar la API FastAPI
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]

