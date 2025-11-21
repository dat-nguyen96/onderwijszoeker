# ---------- Single-stage Python + FastAPI ----------
FROM python:3.11-slim

# Basis tools
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
 && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Backend code
COPY backend ./backend

WORKDIR /app/backend

# Python deps
RUN pip install --no-cache-dir -r requirements.txt

# Railway geeft $PORT mee, default 8000 lokaal
ENV PORT=8000

# Start FastAPI met uvicorn
CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}"]
