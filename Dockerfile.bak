# Root-level Dockerfile that builds the backend/ app
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Copy backend deps and install
COPY backend/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt \
    && pip install --no-cache-dir "uvicorn[standard]" gunicorn

# Copy backend app code into image
COPY backend/ .

ENV PORT=8080 HOST=0.0.0.0
EXPOSE 8080

# Serve FastAPI with Gunicorn/Uvicorn workers
CMD ["gunicorn", "-k", "uvicorn.workers.UvicornWorker", "main:app", \
     "--bind", "0.0.0.0:8080", "--workers", "2", "--timeout", "120"]

CMD ["bash","-lc","gunicorn -k uvicorn.workers.UvicornWorker main:app -b 0.0.0.0:${PORT} --access-logfile - --error-logfile -"]
