"""Built-in example graphs, each paired with algorithms that make sense on it.

The uploader maps ``nodeId -> elementId`` in a single dict, so any graph with
more than one node label must be remapped to globally-unique node ids first
(otherwise the per-label 0..n ranges collide). Homogeneous graphs are already
globally unique.

Each example is a public builder with its natural signature plus a private
``_name(nodes, rels)`` adapter that maps the CLI's generic ``--nodes``/``--rels``
overrides onto it. The two are registered together in :data:`EXAMPLES`.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field

from graphdatascience.cli.database.graph import (
    GaussianGenerator,
    Graph,
    NodeIdMapping,
    PowerLawRelationshipGenerator,
    RandomGraphConfig,
    RandomNodesConfig,
    RandomRelsConfig,
    UniformIntegerGenerator,
    UniformRelationshipGenerator,
    UniformStringCategoryGenerator,
    create_graph,
)

_NAMES = ["Alice", "Bob", "Carol", "Dave", "Erin", "Frank", "Grace", "Heidi", "Ivan", "Judy"]


@dataclass
class Example:
    # callable (nodes, rels) -> Graph; nodes/rels are optional size overrides
    build: Callable[[int | None, int | None], Graph]
    description: str
    algorithms: list[str] = field(default_factory=list)


def homogeneous(
    node_count: int = 100,
    rel_count: int = 300,
    node_label: str = "Node",
    rel_type: str = "REL",
) -> Graph:
    """One node type, one relationship type, a single numeric node property."""
    return create_graph(
        RandomGraphConfig(
            node_config={
                node_label: RandomNodesConfig(
                    node_count=node_count,
                    properties={"score": GaussianGenerator()},
                )
            },
            rel_config={
                (node_label, rel_type, node_label): RandomRelsConfig(
                    rel_count=rel_count,
                    rels=UniformRelationshipGenerator(),
                    properties={"weight": GaussianGenerator(mean=1.0)},
                )
            },
        )
    )


def _homogeneous(nodes: int | None, rels: int | None) -> Graph:
    return homogeneous(node_count=nodes or 100, rel_count=rels or 300)


# A-fraction of the total node count for the heterogeneous graph: close to 1:1
# but deliberately asymmetric.
_HETERO_A_FRACTION = 0.4


def _hetero_split(total: int) -> tuple[int, int]:
    a = max(1, round(total * _HETERO_A_FRACTION))
    a = min(a, total - 1) if total > 1 else a
    return (a, total - a)


def heterogeneous(
    node_counts: tuple[int, int] = (28, 42),
    edge_count: int = 100,
) -> Graph:
    """Two node types (A, B) and A->B relationships; globally-unique node ids."""
    a_count, b_count = node_counts
    return create_graph(
        RandomGraphConfig(
            node_config={
                "A": RandomNodesConfig(node_count=a_count, properties={"score": GaussianGenerator()}),
                "B": RandomNodesConfig(node_count=b_count, properties={"value": UniformIntegerGenerator(0, 100)}),
            },
            rel_config={
                ("A", "LINKS_TO", "B"): RandomRelsConfig(
                    rel_count=edge_count,
                    rels=PowerLawRelationshipGenerator(alpha=0.01),
                    properties={},
                )
            },
            nodeIdMapping=NodeIdMapping.GLOBALLY_UNIQUE,
        )
    )


def _heterogeneous(nodes: int | None, rels: int | None) -> Graph:
    # --nodes is the TOTAL, split ~2:3 across A and B (close to 1:1, still asymmetric).
    node_counts = _hetero_split(nodes) if nodes is not None else (28, 42)
    return heterogeneous(node_counts=node_counts, edge_count=rels or 100)


def people(node_count: int = 100, rel_count: int = 400) -> Graph:
    """A 'Person -KNOWS-> Person' social graph with name/age node properties."""
    return create_graph(
        RandomGraphConfig(
            node_config={
                "Person": RandomNodesConfig(
                    node_count=node_count,
                    properties={
                        "name": UniformStringCategoryGenerator(_NAMES),
                        "age": UniformIntegerGenerator(18, 80),
                    },
                )
            },
            rel_config={
                ("Person", "KNOWS", "Person"): RandomRelsConfig(
                    rel_count=rel_count,
                    rels=UniformRelationshipGenerator(),
                    properties={"since": UniformIntegerGenerator(2000, 2024)},
                )
            },
        )
    )


def _people(nodes: int | None, rels: int | None) -> Graph:
    return people(node_count=nodes or 100, rel_count=rels or 400)


def citation(node_count: int = 200, rel_count: int = 800) -> Graph:
    """Power-law 'Paper -CITES-> Paper' graph; hubs make PageRank interesting."""
    return create_graph(
        RandomGraphConfig(
            node_config={
                "Paper": RandomNodesConfig(
                    node_count=node_count,
                    properties={"year": UniformIntegerGenerator(1990, 2024)},
                )
            },
            rel_config={
                ("Paper", "CITES", "Paper"): RandomRelsConfig(
                    rel_count=rel_count,
                    rels=PowerLawRelationshipGenerator(alpha=0.7),
                    properties={},
                )
            },
        )
    )


def _citation(nodes: int | None, rels: int | None) -> Graph:
    return citation(node_count=nodes or 200, rel_count=rels or 800)


EXAMPLES: dict[str, Example] = {
    "homogeneous": Example(
        build=_homogeneous,
        description="Single-label random graph; good baseline for PageRank / WCC.",
        algorithms=["pageRank", "wcc"],
    ),
    "heterogeneous": Example(
        build=_heterogeneous,
        description="Two node labels (A, B) with A->B edges (--nodes = total, split ~2:3 across A/B).",
        algorithms=["pageRank"],
    ),
    "people": Example(
        build=_people,
        description="'Person -KNOWS-> Person' social graph; good for PageRank / community detection.",
        algorithms=["pageRank", "louvain", "wcc"],
    ),
    "citation": Example(
        build=_citation,
        description="Power-law citation graph with hubs; showcases PageRank & FastRP.",
        algorithms=["pageRank", "fastRP"],
    ),
}


def build_example(name: str, *, nodes: int | None = None, rels: int | None = None) -> Graph:
    """Build a named example graph, optionally overriding its node/relationship size."""
    if name not in EXAMPLES:
        raise KeyError(f"Unknown example {name!r}. Available: {', '.join(EXAMPLES)}")
    return EXAMPLES[name].build(nodes, rels)
