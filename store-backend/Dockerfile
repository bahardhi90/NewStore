# Proxy: pass at build time, e.g.
#   docker build --build-arg http_proxy=http://proxy:3128 --build-arg https_proxy=http://proxy:3128 .
# http_proxy/https_proxy/no_proxy (and uppercase) are Docker's predefined build args: every RUN
# (apt-get, pip) sees them without an ARG line, and they are kept out of the image and its history.
# apt only reads the lowercase names, so always pass those.

# ---------- build stage: compile wheels
FROM python:3.12-slim AS builder
ENV PIP_DISABLE_PIP_VERSION_CHECK=1 PIP_NO_CACHE_DIR=1
WORKDIR /build
RUN apt-get update && apt-get install -y --no-install-recommends build-essential && rm -rf /var/lib/apt/lists/*
COPY requirements/ requirements/
ARG REQUIREMENTS=requirements/base.txt
RUN pip wheel --wheel-dir /wheels -r ${REQUIREMENTS}

# ---------- runtime stage
FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    DJANGO_SETTINGS_MODULE=config.settings.prod
WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends curl && rm -rf /var/lib/apt/lists/* \
    && useradd --create-home --uid 1000 app
COPY --from=builder /wheels /wheels
RUN pip install --no-cache-dir /wheels/* && rm -rf /wheels
COPY --chown=app:app . .
RUN mkdir -p /app/staticfiles /app/media && chown -R app:app /app/staticfiles /app/media \
    && chmod +x scripts/*.sh
USER app
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s --retries=3 CMD curl -fsS http://localhost:8000/api/health/ || exit 1
ENTRYPOINT ["sh", "scripts/entrypoint.sh"]
CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "3", "--timeout", "60", "--access-logfile", "-"]
