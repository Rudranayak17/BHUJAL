# -------------------------------
# 1) Builder Stage
# -------------------------------
FROM python:3.13-slim AS builder

ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

WORKDIR /app

RUN apt-get update && apt-get install -y build-essential

COPY requirements.txt .
RUN pip install --upgrade pip && \
    pip install --prefix=/install -r requirements.txt


# -------------------------------
# 2) Final Stage
# -------------------------------
FROM python:3.13-slim

ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Create user
RUN useradd -m -r appuser

# Copy installed deps from builder
COPY --from=builder /install /usr/local

WORKDIR /app

# Copy source code
COPY --chown=appuser:appuser . .

# Make entrypoint executable
RUN chmod +x /app/entrypoint.prod.sh

USER appuser

EXPOSE 8000

CMD ["/app/entrypoint.prod.sh"]
