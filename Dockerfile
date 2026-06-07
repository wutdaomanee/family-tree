# ─── Stage 1: builder ────────────────────────────────────────────────────────
FROM python:3.11-slim AS builder

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt


# ─── Stage 2: runtime ────────────────────────────────────────────────────────
FROM python:3.11-slim

WORKDIR /app

COPY --from=builder /install /usr/local
COPY *.py ./

# Data directory (ephemeral on free tier)
RUN mkdir -p /app/data/photos

ENV PORT=8888 \
    DB_PATH=/app/data/family_tree.db \
    PHOTO_DIR=/app/data/photos \
    PYTHONUNBUFFERED=1

EXPOSE 8888

RUN useradd -m appuser && chown -R appuser /app
USER appuser

CMD ["python", "web_ui.py"]
