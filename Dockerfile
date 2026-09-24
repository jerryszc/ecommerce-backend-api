FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /code

# Install deps first (better layer caching)
COPY requirements.txt ./
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# App code + migrations config + entrypoint
COPY app/ ./app/
COPY alembic.ini ./
COPY start.sh ./

# Non-root for security
RUN useradd -m appuser && chmod +x /code/start.sh && chown -R appuser:appuser /code
USER appuser

EXPOSE 8000

# PORT-aware (Render inyecta PORT; local default 8000)
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import os, urllib.request; urllib.request.urlopen('http://localhost:' + os.environ.get('PORT', '8000') + '/health')"

CMD ["./start.sh"]
