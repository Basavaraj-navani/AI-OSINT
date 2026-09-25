"""
Test for the SQLite Database Manager.
"""

from __future__ import annotations

from datetime import datetime

from drug_trafficking_osint.infrastructure.database.database import (
    DatabaseManager,
)
from drug_trafficking_osint.infrastructure.database.models import (
    AnalysisRecord,
)


def main() -> None:
    """
    Test the database manager.
    """

    database = DatabaseManager()

    record = AnalysisRecord(
        text="Rahul will deliver ❄️ snow to Bangalore tomorrow.",
        risk_score=0.85,
        risk_label="HIGH_RISK",
        created_at=datetime.now(),
    )

    database.insert_record(record)

    print("Record inserted successfully.")

    database.close()


if __name__ == "__main__":
    main()
