# Telegram OSINT Collector Design

## Purpose

The Telegram module is responsible **only** for collecting public
Telegram data, converting it into the project's unified schema, and
storing it for downstream analysis.

It **must not** perform NLP, NER, bot detection, graph analysis, or risk
scoring.

------------------------------------------------------------------------

# Folder Structure

``` text
telegram/
│
├── client.py
├── collector.py
├── parser.py
├── models.py
├── filters.py
├── rate_limiter.py
├── scheduler.py
├── utils.py
└── __init__.py
```

------------------------------------------------------------------------

# Overall Flow

``` text
Public Telegram Channel
        │
        ▼
 Telethon Client
(client.py)
        │
        ▼
Raw Telegram Messages
        │
        ▼
collector.py
        │
        ▼
parser.py
        │
        ▼
UnifiedMessage Model
        │
        ▼
MongoDB / JSON
        │
        ▼
NLP Pipeline
```

------------------------------------------------------------------------

# client.py

## Goal

Create and manage the Telethon connection.

## Responsibilities

-   Read configuration (API ID, API Hash, Session Name)
-   Create Telethon client
-   Connect to Telegram
-   Authenticate (first run)
-   Reuse existing session
-   Disconnect cleanly

## Should NOT

-   Download messages
-   Parse content
-   Save to database

## Suggested Public Methods

``` python
connect()

disconnect()

is_connected()

get_client()
```

------------------------------------------------------------------------

# collector.py

## Goal

Orchestrate data collection.

This file coordinates the collection process.

## Responsibilities

-   Accept one or more public channels
-   Request messages from Telethon
-   Iterate over raw messages
-   Pass each message to parser
-   Pass parsed objects to storage layer

## Should NOT

-   Extract hashtags
-   Parse URLs
-   Normalize text
-   Connect directly to MongoDB

## Suggested Methods

``` python
collect_channel()

collect_channels()

collect_recent_messages(limit)

collect_between_dates()

collect_user_messages()
```

------------------------------------------------------------------------

# parser.py

## Goal

Convert Telethon message objects into the project's unified schema.

## Input

``` text
Telethon Message Object
```

## Output

``` text
UnifiedMessage
```

## Responsibilities

Extract:

-   Message ID
-   Channel ID
-   Sender ID
-   Text
-   Timestamp
-   Mentions
-   Hashtags
-   URLs
-   Media information
-   Forward count
-   Reply count
-   View count

Normalize:

-   Timestamp format
-   Empty values
-   Missing metadata

No API calls should happen inside this file.

------------------------------------------------------------------------

# models.py

## Goal

Define the data structures used by the Telegram collector.

## Suggested Models

### TelegramMessage

Fields:

-   message_id
-   channel_id
-   sender_id
-   text
-   timestamp
-   views
-   forwards
-   replies
-   hashtags
-   mentions
-   urls
-   media_type
-   metadata

### TelegramChannel

Fields:

-   id
-   username
-   title
-   description
-   participants
-   verified

### UnifiedMessage

Platform-independent representation used by the rest of the project.

Example fields:

-   platform
-   source
-   user
-   text
-   timestamp
-   hashtags
-   mentions
-   urls
-   media
-   metadata

------------------------------------------------------------------------

# filters.py

## Goal

Determine whether a collected message should be processed.

## Example Filters

-   Ignore deleted messages
-   Ignore service messages
-   Ignore empty messages
-   Date range filter
-   Language filter
-   Keyword filter
-   Public channels only
-   Minimum message length

Each filter should return True or False.

------------------------------------------------------------------------

# rate_limiter.py

## Goal

Protect the collector from API limits.

## Responsibilities

-   Track requests
-   Delay requests when needed
-   Retry temporary failures
-   Handle FloodWait exceptions

The collector should not contain sleep logic.

------------------------------------------------------------------------

# scheduler.py

## Goal

Run collection automatically.

Examples

-   Every hour
-   Every midnight
-   Every six hours

For the first version of the project this module can remain minimal or
unused.

------------------------------------------------------------------------

# utils.py

## Goal

Provide reusable helper functions.

Examples

-   extract_hashtags()
-   extract_mentions()
-   extract_urls()
-   detect_media_type()
-   normalize_timestamp()
-   remove_duplicate_messages()
-   sanitize_text()

Only generic helper functions belong here.

------------------------------------------------------------------------

# **init**.py

Exports the public Telegram collector API.

Example exports

``` python
TelegramClient
TelegramCollector
TelegramParser
```

------------------------------------------------------------------------

# Data Flow Between Files

``` text
client.py
    │
    ▼
Connected Telethon Client
    │
    ▼
collector.py
    │
    ▼
Raw Telegram Messages
    │
    ▼
parser.py
    │
    ▼
UnifiedMessage
    │
    ▼
Database Layer
    │
    ▼
JSON Export
    │
    ▼
NLP Pipeline
```

------------------------------------------------------------------------

# Suggested Development Order

## Phase 1

-   client.py
-   Verify connection
-   Authenticate
-   Disconnect

## Phase 2

-   collector.py
-   Download latest messages from a public channel

## Phase 3

-   parser.py
-   Convert raw Telethon messages into UnifiedMessage objects

## Phase 4

-   models.py
-   Introduce dataclasses or Pydantic models

## Phase 5

-   filters.py
-   Add keyword/date/language filtering

## Phase 6

-   rate_limiter.py
-   Handle FloodWait and retries

## Phase 7

-   scheduler.py
-   Optional periodic collection

------------------------------------------------------------------------

# Design Principles

-   Each file should have a single responsibility.
-   Avoid business logic inside `client.py`.
-   Keep parsing independent of the Telegram API.
-   Keep filtering independent of parsing.
-   Use strongly typed models instead of dictionaries.
-   Return a single unified schema so downstream NLP and graph modules
    do not need to know the original platform.
