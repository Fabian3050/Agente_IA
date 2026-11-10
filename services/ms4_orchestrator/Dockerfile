FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential libpq-dev curl && rm -rf /var/lib/apt/lists/*

COPY services/ms4_orchestrator/requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

COPY services/common /app/common
COPY services/ms4_orchestrator /app/

RUN useradd -u 1004 ms4user && chown -R ms4user:ms4user /app
USER ms4user

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]

