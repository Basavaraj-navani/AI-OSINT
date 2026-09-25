FROM python:3.13-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONFAULTHANDLER=1 \
    PIP_NO_CACHE_DIR=1 \
    HF_HOME=/app/data/huggingface

WORKDIR /app

RUN addgroup --system app && adduser --system --ingroup app app

COPY pyproject.toml README.md ./
COPY src ./src
RUN python -m pip install --no-cache-dir . \
    && mkdir -p /app/data \
    && chown -R app:app /app/data

USER app
WORKDIR /app/data

EXPOSE 8000

CMD ["uvicorn", "drug_trafficking_osint.interfaces.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
