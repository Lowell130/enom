# Backend EnotecaMolise per Google Cloud Run
# gcloud run deploy ... --source backend   (vedi deploy/LEGGIMI.md)
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

# Cloud Run passa la porta in $PORT; --proxy-headers per avere l'IP reale dei visitatori (limiti anti-abuso)
CMD exec uvicorn main:app --host 0.0.0.0 --port ${PORT:-8080} --proxy-headers --forwarded-allow-ips="*"
