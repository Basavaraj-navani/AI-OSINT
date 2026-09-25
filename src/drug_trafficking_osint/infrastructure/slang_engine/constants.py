"""
Constants for the Drug Slang Intelligence Engine.
"""

from __future__ import annotations

from pathlib import Path

# Path to the slang dictionary JSON file
DEFAULT_DICTIONARY_PATH = Path(__file__).resolve().parent / "slang_dictionary.json"

# Minimum confidence for accepting a slang match
DEFAULT_MATCH_CONFIDENCE = 0.80

# Supported match types
EXACT_MATCH = "exact"
FUZZY_MATCH = "fuzzy"
HASHTAG_MATCH = "hashtag"
