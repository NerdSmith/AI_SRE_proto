FROM python:3.12-slim
COPY --from=ghcr.io/astral-sh/uv:0.9.9 /uv /bin/uv
WORKDIR /app
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev
COPY app ./app
CMD [".venv/bin/uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--log-level", "warning", "--no-access-log"]
