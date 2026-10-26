# Container image for the FastAPI backend.
#
# Built for hosts that run a long-lived process (Zeabur, Back4App, Fly, a plain VM).
# It is deliberately NOT a serverless image: the research worker runs as an in-process
# background task and the progress endpoint streams SSE for up to 15 minutes, neither
# of which survives a request-scoped function runtime.

FROM python:3.13-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# Dependencies first so editing application code does not invalidate the pip layer.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Hosts inject PORT; 8080 is only the local default.
ENV PORT=8080
EXPOSE 8080

CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT}"]
