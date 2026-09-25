"""
Database Exceptions
"""

from __future__ import annotations


class DatabaseError(Exception):
    """
    Base exception for the database layer.
    """


class DatabaseConnectionError(DatabaseError):
    """
    Raised when a database connection cannot be established.
    """


class RecordNotFoundError(DatabaseError):
    """
    Raised when a requested record does not exist.
    """
