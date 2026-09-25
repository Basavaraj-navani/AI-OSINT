"""
Graph Models
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class GraphNode:
    """
    Represents a node in the intelligence graph.
    """

    id: str
    label: str
    type: str


@dataclass(slots=True)
class GraphEdge:
    """
    Represents a relationship between two nodes.
    """

    source: str
    target: str
    relationship: str
