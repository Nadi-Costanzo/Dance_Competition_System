FROM python:3.11-slim-bookworm

# uv: копируем бинарник из образа, версия закреплена
COPY --from=ghcr.io/astral-sh/uv:0.12.5 /uv /uvx /bin/

# curl нужен для HEALTHCHECK (см. §A.12 Приложение В)
RUN apt-get update \
    && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/*

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_NO_DEV=1 \
    PATH="/app/.venv/bin:$PATH"

WORKDIR /app

# Слой зависимостей отдельно: пересобирается только при смене uv.lock
COPY pyproject.toml uv.lock ./
RUN uv sync --locked --no-install-project

COPY . .
RUN uv sync --locked

EXPOSE 8443

# в связи с отсутствием [build-system] запускаем через python -m
CMD ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8443", \
    "--ssl-keyfile=/certs/key.pem", "--ssl-certfile=/certs/cert.pem"]
