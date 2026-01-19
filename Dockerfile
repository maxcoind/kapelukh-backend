FROM python:3.14
WORKDIR /app

COPY app ./
COPY uv.lock ./
COPY pyproject.toml ./
RUN pip install --no-cache-dir uv
RUN uv sync --frozen


CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
