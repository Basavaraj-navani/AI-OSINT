"""
Graph Exceptions
"""

from __future__ import annotations


class GraphError(Exception):
    """
    Base exception for the graph module.
    """


class GraphBuildError(GraphError):
    """
    Raised when graph construction fails.
    """
