# ─── Stage 1: builder ────────────────────────────────────────────────────────
FROM python:3.11-slim AS builder

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt


# ─── Stage 2: runtime ────────────────────────────────────────────────────────
FROM python:3.11-slim

WORKDIR /app

# Copy installed packages from builder
COPY --from=builder /install /usr/local

# Copy application source
COPY *.py ./

# Create persistent directories
RUN mkdir -p /data/photos

# Runtime environment
ENV PORT=8888 \
    DB_PATH=/data/family_tree.db \
    PHOTO_DIR=/data/photos \
    PYTHONUNBUFFERED=1

EXPOSE 8888

# Non-root user for security
RUN useradd -m appuser && chown -R appuser /app /data
USER appuser

CMD ["python", "web_ui.py"]
