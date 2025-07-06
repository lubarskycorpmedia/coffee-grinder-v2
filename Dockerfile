# /Dockerfile

FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
       curl ca-certificates build-essential \
    && curl -sSL -o /usr/local/bin/supercronic \
       https://github.com/aptible/supercronic/releases/latest/download/supercronic-linux-amd64 \
    && chmod +x /usr/local/bin/supercronic \
    && rm -rf /var/lib/apt/lists/*

ENV POETRY_VERSION=2.1.3
RUN curl -sSL https://install.python-poetry.org | python3 - --version $POETRY_VERSION \
    && ln -s /root/.local/bin/poetry /usr/local/bin/poetry

WORKDIR /app
COPY pyproject.toml poetry.lock ./
RUN poetry config virtualenvs.create false \
    && poetry install --no-interaction --no-ansi --no-root

COPY src/ ./src/
COPY .config/ .config/
COPY cronjob ./cronjob

RUN mkdir -p /app/logs

RUN chmod 0644 ./cronjob

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

CMD ["sh", "-c", "supercronic -quiet ./cronjob & uvicorn src.webapp.main:app --host 0.0.0.0 --port 8000"]