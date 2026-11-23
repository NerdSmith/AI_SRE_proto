FROM python:3.12-slim
COPY --from=ghcr.io/astral-sh/uv:0.9.9 /uv /bin/uv
WORKDIR /app
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev
COPY main.py .
CMD [".venv/bin/python", "main.py"]
