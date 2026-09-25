# AI-OSINT Project Structure (Recommended)

## Overview

The project follows a Clean Architecture approach. Your responsibility is the **OSINT Data Collection Layer**, which is responsible for collecting public data from Instagram and Telegram, converting it into a common format, and storing it for downstream NLP, graph analysis, and risk scoring.

```
src/
└── drug_trafficking_osint/
    ├── application/
    ├── core/
    ├── domain/
    ├── infrastructure/
    │   ├── collectors/
    │   │   ├── instagram/
    │   │   ├── telegram/
    │   │   ├── database/
    │   │   └── storage/
    │   ├── nlp/
    │   └── logging.py
    ├── interfaces/
    └── main.py
```

---

# Collectors Folder

The `collectors` folder contains everything related to OSINT data acquisition.

It should **only** collect, parse, normalize, and save data.

It should **not** perform NLP, bot detection, graph analysis, or risk scoring.

```
collectors/
│
├── instagram/
│
├── telegram/
│
├── database/
│
└── storage/
```

---

# Instagram Collector

```
instagram/
│
├── client.py
├── scraper.py
├── parser.py
├── models.py
├── utils.py
└── __init__.py
```

## client.py

Responsible for:

- Authentication/session management
- Login (if required)
- Cookie handling
- Rate limiting
- Request retries

Example methods:

- create_session()
- login()
- close()

---

## scraper.py

Responsible for downloading raw data.

Examples:

- scrape_profile()
- scrape_hashtag()
- scrape_post()
- scrape_comments()

Returns raw platform data.

---

## parser.py

Converts raw platform responses into the project's internal schema.

Example:

Instagram JSON

↓

UnifiedPost object

Parser responsibilities:

- Extract hashtags
- Extract mentions
- Convert timestamps
- Normalize URLs
- Handle missing values

---

## models.py

Contains dataclasses or Pydantic models.

Example classes:

- InstagramPost
- InstagramProfile
- InstagramComment

---

## utils.py

Helper functions.

Examples:

- extract_hashtags()
- extract_mentions()
- format_date()
- clean_caption()

---

# Telegram Collector

```
telegram/
│
├── client.py
├── collector.py
├── parser.py
├── models.py
├── utils.py
└── __init__.py
```

## client.py

Responsible for:

- Telethon client
- API connection
- Authentication
- Session creation

---

## collector.py

Collects data from

- Public channels
- Public groups

Downloads:

- Messages
- Metadata
- Media
- Views
- Replies

---

## parser.py

Converts Telegram messages into the common internal schema.

Responsible for:

- Mentions
- Hashtags
- Timestamp conversion
- Media detection

---

## models.py

Contains

- TelegramMessage
- TelegramChannel

---

## utils.py

Utility functions

Examples

- parse_entities()
- extract_links()
- detect_media()

---

# Database Layer

```
database/
│
└── mongodb.py
```

Responsibilities

- save_post()
- save_profile()
- save_message()
- get_messages()
- get_posts()

Only database operations belong here.

---

# Storage Layer

```
storage/
│
└── exporter.py
```

Exports data into

- JSON
- CSV
- Parquet

Useful for creating datasets for training.

---

# Unified Data Model

Every platform should be converted into the same structure.

```json
{
  "platform": "instagram",
  "user": "...",
  "text": "...",
  "hashtags": [],
  "mentions": [],
  "timestamp": "...",
  "media": "...",
  "metadata": {}
}
```

The NLP pipeline should never need to know whether the data came from Instagram or Telegram.

---

# Overall Data Flow

```
Instagram / Telegram
        │
        ▼
Collector
        │
        ▼
Parser
        │
        ▼
Unified Model
        │
        ▼
MongoDB / JSON
        │
        ▼
NLP Pipeline
        │
        ▼
NER
        │
        ▼
Graph Analysis
        │
        ▼
Risk Scoring
```

---

# Future Scalability

This design makes it easy to add more platforms later.

```
collectors/
├── instagram/
├── telegram/
├── reddit/
├── twitter/
├── facebook/
└── youtube/
```

Each collector only needs to implement platform-specific collection and parsing while producing the same unified output schema.
