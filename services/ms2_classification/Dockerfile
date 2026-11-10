FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential libpq-dev curl && rm -rf /var/lib/apt/lists/*

COPY services/ms2_classification/requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

COPY services/common /app/common
COPY services/ms2_classification /app/

RUN useradd -u 1002 ms2user && chown -R ms2user:ms2user /app
USER ms2user

EXPOSE 8002

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8002"]

