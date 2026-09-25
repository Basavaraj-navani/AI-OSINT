"""
Constants used by the Emoji Intelligence Engine.
"""

from __future__ import annotations

from pathlib import Path

DEFAULT_DICTIONARY_PATH = Path(__file__).parent / "emoji_dictionary.json"

DEFAULT_MATCH_CONFIDENCE = 1.0

EXACT_MATCH = "exact"

EMOJI_MATCH = "emoji"
