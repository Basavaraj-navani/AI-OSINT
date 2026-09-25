"""
Loads and validates the drug slang dictionary.
"""

from __future__ import annotations

import json
from pathlib import Path

from drug_trafficking_osint.infrastructure.slang_engine.constants import (
    DEFAULT_DICTIONARY_PATH,
)
from drug_trafficking_osint.infrastructure.slang_engine.exceptions import (
    DictionaryLoadError,
)
from drug_trafficking_osint.infrastructure.slang_engine.models import DrugEntry


class DictionaryLoader:
    """
    Loads the drug slang dictionary from a JSON file.
    """

    def __init__(self, dictionary_path: Path = DEFAULT_DICTIONARY_PATH) -> None:
        self._dictionary_path = dictionary_path

    def exists(self) -> bool:
        """
        Check whether the dictionary file exists.
        """
        return self._dictionary_path.exists()

    def load(self) -> list[DrugEntry]:
        """
        Load the slang dictionary from JSON.
        """
        if not self.exists():
            raise DictionaryLoadError(f"Dictionary file not found: {self._dictionary_path}")

        with self._dictionary_path.open("r", encoding="utf-8") as file:
            data = json.load(file)

        entries: list[DrugEntry] = []

        for item in data:
            entries.append(
                DrugEntry(
                    canonical_name=item["canonical_name"],
                    aliases=tuple(item["aliases"]),
                    hashtags=tuple(item["hashtags"]),
                    category=item["category"],
                    risk_weight=float(item["risk_weight"]),
                )
            )

        return entries
