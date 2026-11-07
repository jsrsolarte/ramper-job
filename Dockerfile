FROM python:3.14-slim AS builder

ENV UV_PROJECT_ENVIRONMENT=/opt/venv \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

RUN pip install --no-cache-dir uv==0.12.1

COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project

COPY . .
RUN DJANGO_DEBUG=false \
    DJANGO_SECRET_KEY=build-only-placeholder \
    DJANGO_ALLOWED_HOSTS=localhost \
    /opt/venv/bin/python manage.py collectstatic --noinput

FROM python:3.14-slim AS runtime

ENV PATH="/opt/venv/bin:${PATH}" \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=8000 \
    PRIVATE_MEDIA_ROOT=/var/lib/ramper/private-media

RUN apt-get update \
    && apt-get install --no-install-recommends -y ca-certificates \
    && rm -rf /var/lib/apt/lists/* \
    && groupadd --system --gid 10001 ramper \
    && useradd --system --uid 10001 --gid ramper --home-dir /app --no-create-home ramper

WORKDIR /app
COPY --from=builder --chown=10001:10001 /opt/venv /opt/venv
COPY --from=builder --chown=10001:10001 /app /app
RUN mkdir -p /var/lib/ramper/private-media \
    && chown -R 10001:10001 /var/lib/ramper

USER 10001:10001
EXPOSE 8000

CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "2", "--access-logfile", "-", "--error-logfile", "-", "--graceful-timeout", "30", "--timeout", "120"]
