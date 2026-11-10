FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential libpq-dev curl && rm -rf /var/lib/apt/lists/*

COPY services/ms1_retrieval/requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

COPY services/common /app/common
COPY services/ms1_retrieval /app/

RUN useradd -u 1001 ms1user && chown -R ms1user:ms1user /app
USER ms1user

EXPOSE 8001

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8001"]

