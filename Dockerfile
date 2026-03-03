FROM python:3.11-slim

COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

WORKDIR /app
COPY pyproject.toml .
COPY server/ server/

RUN uv pip install --system --no-cache . \
    && rm /usr/local/bin/uv

RUN useradd --no-create-home appuser
USER appuser

ENV HOST=0.0.0.0
ENV PORT=8080
EXPOSE 8080

CMD ["tokenhub-server"]
