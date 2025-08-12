# backend/Dockerfile
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install dependencies first for better layer caching
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt \
    && pip install --no-cache-dir "uvicorn[standard]" gunicorn

# Copy app code
COPY . .

ENV PORT=8080 HOST=0.0.0.0
EXPOSE 8080

# Production server: Gunicorn + Uvicorn workers
CMD ["gunicorn","-k","uvicorn.workers.UvicornWorker","app:app","--bind","0.0.0.0:8080","--workers","2","--timeout","120"]

