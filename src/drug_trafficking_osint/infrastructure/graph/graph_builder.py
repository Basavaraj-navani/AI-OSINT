"""
Graph Builder
"""

from __future__ import annotations

import json
from collections.abc import Iterable
from dataclasses import asdict

from drug_trafficking_osint.infrastructure.graph.models import (
    GraphEdge,
    GraphNode,
)


class GraphBuilder:
    """
    Builds an in-memory intelligence graph from extracted entities.
    """

    def __init__(self) -> None:
        self.nodes: list[GraphNode] = []
        self.edges: list[GraphEdge] = []

    def add_node(self, node: GraphNode) -> None:
        """
        Add a node if it does not already exist.
        """
        if not any(existing.id == node.id for existing in self.nodes):
            self.nodes.append(node)

    def add_edge(self, edge: GraphEdge) -> None:
        """
        Add a relationship between two nodes.
        """
        self.edges.append(edge)

    def build(
        self,
        nodes: Iterable[GraphNode],
        edges: Iterable[GraphEdge],
    ) -> None:
        """
        Build the graph from collections of nodes and edges.
        """
        for node in nodes:
            self.add_node(node)

        for edge in edges:
            self.add_edge(edge)

    def get_nodes(self) -> list[GraphNode]:
        """
        Return all graph nodes.
        """
        return self.nodes

    def get_edges(self) -> list[GraphEdge]:
        """
        Return all graph edges.
        """
        return self.edges

    def export_json(self) -> str:
        """
        Export the graph as a formatted JSON string.
        """

        graph = {
            "nodes": [asdict(node) for node in self.nodes],
            "edges": [asdict(edge) for edge in self.edges],
        }

        return json.dumps(graph, indent=4)
