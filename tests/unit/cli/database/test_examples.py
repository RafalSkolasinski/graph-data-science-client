import pytest

from graphdatascience.cli.database.examples import EXAMPLES, build_example


@pytest.mark.parametrize("name", list(EXAMPLES))
def test_build_example_default_size(name: str) -> None:
    graph = build_example(name)

    assert graph.node_dfs
    assert graph.rel_dfs


def test_build_example_overrides_size() -> None:
    graph = build_example("homogeneous", nodes=10, rels=20)

    assert len(graph.node_dfs["Node"]) == 10
    assert len(graph.rel_dfs[("Node", "REL", "Node")]) == 20


def test_build_example_unknown_name() -> None:
    with pytest.raises(KeyError, match="Unknown example"):
        build_example("does-not-exist")
