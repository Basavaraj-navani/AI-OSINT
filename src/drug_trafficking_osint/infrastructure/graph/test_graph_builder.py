"""
Test Graph Builder
"""

from __future__ import annotations

from drug_trafficking_osint.infrastructure.graph.graph_builder import (
    GraphBuilder,
)
from drug_trafficking_osint.infrastructure.graph.models import (
    GraphEdge,
    GraphNode,
)


def main() -> None:
    """
    Test the GraphBuilder class.
    """

    builder = GraphBuilder()

    person = GraphNode(
        id="rahul",
        label="Rahul",
        type="PERSON",
    )

    city = GraphNode(
        id="bangalore",
        label="Bangalore",
        type="LOCATION",
    )

    edge = GraphEdge(
        source="rahul",
        target="bangalore",
        relationship="LOCATED_IN",
    )

    builder.build(
        nodes=[person, city],
        edges=[edge],
    )

    print("Nodes:")
    for node in builder.get_nodes():
        print(node)

    print("\nEdges:")
    for graph_edge in builder.get_edges():
        print(graph_edge)

    print("\nJSON Export:")
    print(builder.export_json())


if __name__ == "__main__":
    main()
