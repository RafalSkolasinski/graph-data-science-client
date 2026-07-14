"""The three job steps: project -> algorithms -> writeback.

Each step takes a connected gds handle and the JobConfig. Steps reference the
projected graph by name (``gds.graph.get``) so they can run in separate
processes/pods, reconnecting to the same session in between.
"""

from __future__ import annotations

from typing import Any, Optional, TypedDict

from graphdatascience.cli.session.algorithms import run_algorithm
from graphdatascience.cli.session.config import JobConfig
from graphdatascience.graph.graph_api import Graph
from graphdatascience.procedure_surface.api.catalog.node_properties_endpoints import NodePropertiesWriteResult
from graphdatascience.session.aura_graph_data_science import AuraGraphDataScience


def project(gds: AuraGraphDataScience, cfg: JobConfig, overwrite: bool = False) -> Graph:
    """Run the remote Cypher projection and return the projected graph handle.

    With ``overwrite=True`` an existing graph of the same name is dropped first,
    so re-running against a reused session does not fail on "graph already exists".
    """
    if overwrite:
        gds.graph.drop(cfg.projection.graph_name, fail_if_missing=False)
    result = gds.graph.project(cfg.projection.graph_name, cfg.projection.query)
    # GraphWithProjectResult is a NamedTuple (graph, result)
    return result.graph


def get_graph(gds: AuraGraphDataScience, cfg: JobConfig) -> Graph:
    """Look up the already-projected graph by name (for standalone later steps)."""
    return gds.graph.get(cfg.projection.graph_name)


def run_algorithms(
    gds: AuraGraphDataScience, cfg: JobConfig, graph: Graph | None = None, only: Optional[str] = None
) -> list[tuple[str, Any]]:
    """Run the ordered algorithms on the projected graph.

    ``only`` restricts the run to the single named algorithm.
    """
    if graph is None:
        graph = get_graph(gds, cfg)
    results: list[tuple[str, Any]] = []
    for algo in cfg.algorithms:
        if only is not None and algo.name != only:
            continue
        results.append((algo.name, run_algorithm(gds, graph, algo)))
    if only is not None and not results:
        raise ValueError(f"No algorithm named {only!r} in the config.")
    return results


def writeback(
    gds: AuraGraphDataScience, cfg: JobConfig, graph: Graph | None = None
) -> NodePropertiesWriteResult | None:
    """Write mutated node properties back to the database."""
    if cfg.writeback is None or not cfg.writeback.node_properties:
        return None
    if graph is None:
        graph = get_graph(gds, cfg)
    return gds.graph.node_properties.write(graph, cfg.writeback.node_properties)


def drop(gds: AuraGraphDataScience, cfg: JobConfig) -> None:
    """Drop the projected graph from the session catalog.

    Frees the graph's memory so the same session can be reused for another
    experiment (a different projection/config). Safe if the graph is missing.
    """
    gds.graph.drop(cfg.projection.graph_name, fail_if_missing=False)


class JobResult(TypedDict):
    graph: str
    algorithms: list[tuple[str, Any]]
    writeback: NodePropertiesWriteResult | None


def run_all(gds: AuraGraphDataScience, cfg: JobConfig, overwrite_graph: bool = False) -> JobResult:
    """Project, run every algorithm, then write back — all on one connection.

    ``overwrite_graph=True`` drops any existing same-named graph before projecting.
    """
    graph = project(gds, cfg, overwrite=overwrite_graph)
    algo_results = run_algorithms(gds, cfg, graph=graph)
    write_result = writeback(gds, cfg, graph=graph)
    return {
        "graph": cfg.projection.graph_name,
        "algorithms": algo_results,
        "writeback": write_result,
    }
