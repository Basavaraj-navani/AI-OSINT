# Source Code Overview

This document provides a high-level summary of the files currently present in the `src` directory for the `drug_trafficking_osint` project.

## `src/drug_trafficking_osint/`

### Root Level
- **`main.py`**: The main entry point for the application.
- **`__init__.py`**: Marks the directory as a Python package.

### `application/`
Contains the application layer logic.
- **`runtime.py`**: Handles runtime execution and application state.
- **`__init__.py`**

### `core/`
Contains core application configuration and dependency injection.
- **`config.py`**: Manages configuration settings and environment variables.
- **`container.py`**: Likely sets up dependency injection containers.
- **`__init__.py`**

### `domain/`
Contains domain models and business logic interfaces.
- **`lifecycle.py`**: Manages the lifecycle of domain entities or application components.
- **`__init__.py`**

### `interfaces/`
Contains external-facing interfaces (e.g., API, CLI).
- **`__init__.py`**: Currently empty or just initializing the module.

### `infrastructure/`
Contains implementation details for external services, logging, and specific tools.
- **`logging.py`**: Configures and manages application logging.
- **`__init__.py`**

#### `infrastructure/nlp/`
A comprehensive Natural Language Processing module for analyzing text data.
- **`cleaner.py`**: Cleans and sanitizes raw text input.
- **`constants.py`**: Defines NLP-related constants (e.g., regex patterns, specific tokens).
- **`exceptions.py`**: Custom exceptions for the NLP processing pipeline.
- **`language_detector.py`**: Detects the language of the provided text.
- **`lemmatizer.py`**: Performs lemmatization on words to reduce them to their base form.
- **`normalizer.py`**: Normalizes text (e.g., lowercase, removing accents).
- **`pipeline.py`**: The core NLP processing pipeline orchestrating the various NLP components.
- **`stopwords.py`**: Manages and filters out stop words from the text.
- **`tokenizer.py`**: Splits text into individual tokens or words.
- **`utils.py`**: Utility functions for NLP operations.
- **`__init__.py`**
