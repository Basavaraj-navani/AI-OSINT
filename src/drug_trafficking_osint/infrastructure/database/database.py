"""
SQLite Database Manager
"""

from __future__ import annotations

import sqlite3

from drug_trafficking_osint.infrastructure.database.constants import (
    ANALYSIS_TABLE,
    COLUMN_CREATED_AT,
    COLUMN_RISK_LABEL,
    COLUMN_RISK_SCORE,
    COLUMN_TEXT,
    DATABASE_NAME,
)
from drug_trafficking_osint.infrastructure.database.models import (
    AnalysisRecord,
)


class DatabaseManager:
    """
    Handles SQLite database operations.
    """

    def __init__(self, database_name: str = DATABASE_NAME) -> None:
        self.connection = sqlite3.connect(
            database_name,
            check_same_thread=False,
        )
        self.create_table()

    def create_table(self) -> None:
        """
        Create the analysis table if it does not exist.
        """

        cursor = self.connection.cursor()

        cursor.execute(
            f"""
            CREATE TABLE IF NOT EXISTS {ANALYSIS_TABLE} (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                {COLUMN_TEXT} TEXT NOT NULL,
                {COLUMN_RISK_SCORE} REAL NOT NULL,
                {COLUMN_RISK_LABEL} TEXT NOT NULL,
                {COLUMN_CREATED_AT} TEXT NOT NULL
            )
            """
        )

        self.connection.commit()

    def insert_record(self, record: AnalysisRecord) -> None:
        """
        Insert an analysis record.
        """

        cursor = self.connection.cursor()

        cursor.execute(
            f"""
            INSERT INTO {ANALYSIS_TABLE}
            (
                {COLUMN_TEXT},
                {COLUMN_RISK_SCORE},
                {COLUMN_RISK_LABEL},
                {COLUMN_CREATED_AT}
            )
            VALUES (?, ?, ?, ?)
            """,
            (
                record.text,
                record.risk_score,
                record.risk_label,
                record.created_at.isoformat(),
            ),
        )

        self.connection.commit()

    def close(self) -> None:
        """
        Close the database connection.
        """

        self.connection.close()
