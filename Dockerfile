# Use a slim Python base image
FROM python:3.10-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PORT=7860 \
    HF_HOME=/app/.cache

# System deps (if needed, keep minimal)
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt /app/
RUN pip install --upgrade pip && pip install -r requirements.txt

# Copy the rest of the app
COPY . /app

# Create and set permissions for runtime directories that the app needs to write to
RUN mkdir -p /app/logs /app/uploads /app/sample_pdfs /app/.cache && chown -R 1000:1000 /app/logs /app/uploads /app/sample_pdfs /app/.cache

EXPOSE 7860

CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "7860"]
