# Root-level Dockerfile.
#
# Hosts that build from the repository root (SnapDeploy's default when Root Directory
# is left unset) look for a Dockerfile here. The canonical per-service image is
# backend/Dockerfile — this one is thin wrapper that builds that same app from the
# repo root, so no Root Directory configuration is needed.

FROM python:3.13-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# Dependencies first so editing application code does not invalidate the pip layer.
COPY backend/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY backend/ ./

# Hosts inject PORT (SnapDeploy manages it); 8080 is only the local default.
ENV PORT=8080
EXPOSE 8080

CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT}"]
