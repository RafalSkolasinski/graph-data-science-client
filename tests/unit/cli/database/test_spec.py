import pytest

from graphdatascience.cli.database.graph import NodeIdMapping
from graphdatascience.cli.database.spec import graph_from_spec, random_graph_config_from_spec


def test_graph_from_spec_basic() -> None:
    spec = {
        "kind": "random",
        "nodes": {
            "Person": {
                "count": 10,
                "properties": {"age": {"type": "uniform_int", "low": 18, "high": 80}},
            },
            "Company": {"count": 5},
        },
        "relationships": [
            {
                "source": "Person",
                "type": "WORKS_AT",
                "target": "Company",
                "count": 8,
                "generator": {"type": "powerlaw", "alpha": 0.7},
                "properties": {"since": {"type": "uniform_int", "low": 2000, "high": 2024}},
            }
        ],
    }

    graph = graph_from_spec(spec)

    assert len(graph.node_dfs["Person"]) == 10
    assert len(graph.node_dfs["Company"]) == 5
    assert "age" in graph.node_dfs["Person"].columns
    assert len(graph.rel_dfs[("Person", "WORKS_AT", "Company")]) == 8


def test_random_graph_config_defaults_to_globally_unique_for_multi_label() -> None:
    spec = {
        "nodes": {"A": {"count": 1}, "B": {"count": 1}},
        "relationships": [],
    }

    config = random_graph_config_from_spec(spec)

    assert config.nodeIdMapping == NodeIdMapping.GLOBALLY_UNIQUE


def test_random_graph_config_missing_nodes_raises() -> None:
    with pytest.raises(ValueError, match="non-empty 'nodes' mapping"):
        random_graph_config_from_spec({"nodes": {}})


def test_random_graph_config_missing_count_raises() -> None:
    with pytest.raises(ValueError, match="missing 'count'"):
        random_graph_config_from_spec({"nodes": {"Person": {}}})


def test_random_graph_config_unknown_property_generator_raises() -> None:
    spec = {"nodes": {"Person": {"count": 1, "properties": {"x": {"type": "bogus"}}}}}

    with pytest.raises(ValueError, match="Unknown property generator type"):
        random_graph_config_from_spec(spec)


def test_random_graph_config_unknown_relationship_generator_raises() -> None:
    spec = {
        "nodes": {"Person": {"count": 1}},
        "relationships": [
            {"source": "Person", "type": "R", "target": "Person", "count": 1, "generator": {"type": "bogus"}}
        ],
    }

    with pytest.raises(ValueError, match="Unknown relationship generator type"):
        random_graph_config_from_spec(spec)


def test_random_graph_config_unknown_node_id_mapping_raises() -> None:
    spec = {"nodes": {"Person": {"count": 1}}, "node_id_mapping": "bogus"}

    with pytest.raises(ValueError, match="Unknown node_id_mapping"):
        random_graph_config_from_spec(spec)
