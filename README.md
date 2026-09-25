# AI-Driven OSINT Framework

Private Python project for collecting, normalizing, and analyzing social-media text. It includes a FastAPI inference endpoint, deterministic NLP preprocessing, slang and emoji detection, spaCy NER, a pinned Hugging Face classifier, risk scoring, Telegram collection, and MongoDB/SQLite persistence.

## Model status

No project-specific model is trained in this repository, and collaborators do **not** need to train or fine-tune one before running it.

The API uses these pretrained models:

- `distilbert/distilbert-base-uncased-finetuned-sst-2-english`, pinned to revision `714eb0fa89d2f80546fda750413ed43d93601a13`
- `en_core_web_sm` version `3.8.0`, installed as a pinned dependency

The first analysis downloads the DistilBERT weights into the local Hugging Face cache. Later runs reuse the cache. Internet access is required for that first download.

The DistilBERT checkpoint is a general English sentiment model used as a prototype signal. It was not trained specifically for drug-trafficking detection, so its output must not be treated as a validated domain classifier.

## Requirements

- Python 3.13
- [uv](https://docs.astral.sh/uv/)
- Internet access for dependency and model downloads
- Docker with Compose for the container workflow

## Run locally

```bash
git clone <private-repository-url>
cd AI-OSINT
uv sync
uv run osint-api
```

The API is available at:

- Health response: `http://127.0.0.1:8000/`
- OpenAPI documentation: `http://127.0.0.1:8000/docs`
- Analysis endpoint: `http://127.0.0.1:8000/analyze`

Send a test request:

```bash
curl -X POST http://127.0.0.1:8000/analyze \
  -H "Content-Type: application/json" \
  -d '{"text":"Sample post mentioning a suspicious package and delivery location"}'
```

On PowerShell, `curl` may be an alias. Use `curl.exe` for the same request.

## Run with Docker

```bash
docker compose up --build
```

The API is published only on `127.0.0.1:8000`. The named `osint-data` volume stores the SQLite database and downloaded Hugging Face model cache. Stop the service with `docker compose down`; add `-v` only when you intentionally want to delete that local data.

## Collection configuration

API inference does not require Telegram or MongoDB credentials. To run collection features, copy `.env.example` to `.env` and set:

- `TELEGRAM_API_ID`
- `TELEGRAM_API_HASH`
- `MONGODB_URI`
- `MONGODB_DATABASE`

Telegram authorization sessions, `.env` files, databases, collected datasets, media, and exports are excluded from Git. Never commit or share `.env` or `*.session` files.

## Project layout

```text
src/drug_trafficking_osint/
├── application/       # Intelligence orchestration and use cases
├── core/              # Configuration and dependency composition
├── domain/            # Framework-independent business models
├── infrastructure/    # Models, NLP, collectors, and persistence adapters
└── interfaces/        # FastAPI routes and schemas
tests/                 # Isolated unit tests
```

## Quality checks

```bash
uv sync --extra dev
uv run ruff check .
uv run black --check .
uv run mypy src
uv run pytest
```

The default test run excludes live Telegram and MongoDB integration checks. They require explicit credentials and external services and should not be part of a normal unit-test run.

## Data handling

Analyzed text is stored in the local SQLite database. Collection data and downloaded media may contain personal or sensitive information. Review data-sharing rules and applicable privacy requirements before granting collaborators access to any exported dataset.
