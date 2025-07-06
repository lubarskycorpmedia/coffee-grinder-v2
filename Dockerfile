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

ENV POETRY_VERSION=1.9.4
RUN curl -sSL https://install.python-poetry.org | python3 - --version $POETRY_VERSION \
    && ln -s /root/.local/bin/poetry /usr/local/bin/poetry

WORKDIR /app
COPY pyproject.toml poetry.lock ./
RUN poetry config virtualenvs.create false \
    && poetry install --no-interaction --no-ansi --no-root

COPY src/ ./src
COPY .config/ .config/
COPY run.py .
COPY cronjob /etc/cron.d/news
RUN chmod 0644 /etc/cron.d/news

CMD ["supercronic", "-quiet", "/etc/cron.d/news"]