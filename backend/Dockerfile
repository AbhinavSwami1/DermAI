# Build from the repository root:  docker build -f backend/Dockerfile .
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app:/app/backend

# libGL/glib are required by opencv-python
RUN apt-get update \
    && apt-get install -y --no-install-recommends libgl1 libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# CPU-only PyTorch (a CUDA build would add several GB); versions come from requirements.txt
COPY backend/requirements.txt backend/requirements.txt
RUN pip install --no-cache-dir $(grep -E '^(torch|torchvision)==' backend/requirements.txt) \
        --index-url https://download.pytorch.org/whl/cpu \
    && pip install --no-cache-dir -r backend/requirements.txt

COPY alembic.ini .
COPY backend backend
COPY ml/__init__.py ml/__init__.py
COPY ml/src ml/src

RUN useradd --create-home app \
    && mkdir -p backend/storage/original \
    && chown -R app:app /app/backend/storage
USER app

EXPOSE 8001
HEALTHCHECK --interval=30s --timeout=5s --start-period=60s \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8001/health')"

# Apply migrations, then start the API
CMD ["sh", "-c", "alembic upgrade head && uvicorn app.main:app --app-dir backend --host 0.0.0.0 --port 8001"]
