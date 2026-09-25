"""
Loads the emoji intelligence dictionary.
"""

from __future__ import annotations

import json
from pathlib import Path

from drug_trafficking_osint.infrastructure.emoji_engine.constants import (
    DEFAULT_DICTIONARY_PATH,
)
from drug_trafficking_osint.infrastructure.emoji_engine.exceptions import (
    DictionaryLoadError,
)
from drug_trafficking_osint.infrastructure.emoji_engine.models import (
    EmojiEntry,
)


class DictionaryLoader:
    """
    Loads emoji entries from a JSON dictionary.
    """

    def __init__(
        self,
        dictionary_path: Path = DEFAULT_DICTIONARY_PATH,
    ) -> None:
        self.dictionary_path = dictionary_path

    def exists(self) -> bool:
        """
        Returns True if the dictionary file exists.
        """
        return self.dictionary_path.exists()

    def load(self) -> list[EmojiEntry]:
        """
        Loads all emoji entries from the JSON dictionary.

        Returns:
            list[EmojiEntry]: Loaded emoji entries.

        Raises:
            DictionaryLoadError: If the dictionary file cannot be found.
        """
        if not self.exists():
            raise DictionaryLoadError(f"Dictionary not found: {self.dictionary_path}")

        with self.dictionary_path.open(
            "r",
            encoding="utf-8",
        ) as file:
            data = json.load(file)

        entries: list[EmojiEntry] = []

        for item in data:
            entries.append(
                EmojiEntry(
                    emoji=item["emoji"],
                    canonical_name=item["canonical_name"],
                    category=item["category"],
                    aliases=tuple(item["aliases"]),
                )
            )

        return entries
