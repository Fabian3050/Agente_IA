FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential libpq-dev curl && rm -rf /var/lib/apt/lists/*

COPY services/ms3_auth/requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

COPY services/common /app/common
COPY services/ms3_auth /app/

RUN useradd -u 1003 ms3user && chown -R ms3user:ms3user /app
USER ms3user

EXPOSE 8003

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8003"]

