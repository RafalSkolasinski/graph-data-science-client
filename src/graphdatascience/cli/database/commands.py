"""``gds database`` — generate test graphs, upload them to Aura Neo4j, and read
them back to inspect what a GDS job wrote.

Connection details come from the unified env set (see
:mod:`graphdatascience.cli.common.env`). A ``.env`` in the working directory is
loaded automatically; pass --env-file for another dotenv file. Real environment
variables always take precedence over dotenv files.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Optional

import typer

from graphdatascience.cli.database.examples import EXAMPLES, build_example
from graphdatascience.cli.database.output import OutputFormat

if TYPE_CHECKING:
    from graphdatascience.cli.database.db import DatabaseClient
    from graphdatascience.cli.database.graph import Graph

app = typer.Typer(
    help="Generate test graphs, upload them to Aura Neo4j, and read them back.",
    no_args_is_help=True,
)


def _client(env_file: Optional[str]) -> DatabaseClient:
    from graphdatascience.cli.common.env import load_env
    from graphdatascience.cli.database.db import DatabaseClient

    load_env(env_file)
    return DatabaseClient.from_env()


ENV_FILE_OPT = typer.Option(
    None,
    "--env-file",
    help="Extra dotenv file to read (a .env in the working dir loads automatically; real env vars win).",
)


EXAMPLE_ARG_HELP = "Built-in example name (see list below). Omit if using --file."
NODES_OPT = typer.Option(None, "--nodes", "-n", help="Override node count (example graphs only).")
RELS_OPT = typer.Option(None, "--rels", "-r", help="Override relationship count (example graphs only).")


# Listing of the built-in examples, shown below the arguments/options panels in
# `upload --help`. Entries are separated by blank lines so the paragraph breaks
# survive rich's help rendering.
UPLOAD_EPILOG = "Built-in examples:\n\n" + "\n\n".join(
    f"{key}: {ex.description} (algorithms: {', '.join(ex.algorithms)})" for key, ex in EXAMPLES.items()
)


def _build(example: Optional[str], file: Optional[str], nodes: Optional[int], rels: Optional[int]) -> Graph:
    """Build the graph from exactly one source: a named example or a JSON file."""
    if (example is None) == (file is None):
        raise typer.BadParameter("Provide exactly one of EXAMPLE (positional) or --file/-f.")
    try:
        if file is not None:
            from graphdatascience.cli.database.construct import graph_from_file

            return graph_from_file(file)
        assert example is not None
        return build_example(example, nodes=nodes, rels=rels)
    except (ValueError, KeyError) as exc:
        typer.secho(f"Error: {exc}", fg=typer.colors.RED, err=True)
        raise typer.Exit(1) from exc


@app.command(epilog=UPLOAD_EPILOG)
def upload(
    example: Optional[str] = typer.Argument(None, help=EXAMPLE_ARG_HELP),
    nodes: Optional[int] = NODES_OPT,
    rels: Optional[int] = RELS_OPT,
    file: Optional[str] = typer.Option(
        None,
        "--file",
        "-f",
        help="Graph file: JSON construct format, or a random-graph spec (kind: random, JSON/YAML).",
    ),
    overwrite: bool = typer.Option(False, "--overwrite", help="Replace existing test data with the same labels."),
    dry_run: bool = typer.Option(False, "--dry-run", help="Build and summarize only; do not write to the database."),
    env_file: Optional[str] = ENV_FILE_OPT,
) -> None:
    """Upload a graph: a built-in EXAMPLE (positional) or a JSON file (--file/-f)."""
    from graphdatascience.cli.database.output import print_summary

    graph = _build(example, file, nodes, rels)
    print_summary(graph)
    source = f"file '{file}'" if file is not None else f"example '{example}'"
    if dry_run:
        typer.echo("Dry run: nothing written.")
        return
    _client(env_file).upload(graph, overwrite=overwrite)
    typer.echo(f"Uploaded {source}.")


LABEL_OPT = typer.Option(None, "--label", help="Only include nodes with this label.")


def _fetch(env_file: Optional[str], label: Optional[str]) -> Graph:
    client = _client(env_file)
    return client.fetch(node_labels=[label] if label else None)


@app.command()
def summary(
    label: Optional[str] = LABEL_OPT,
    env_file: Optional[str] = ENV_FILE_OPT,
) -> None:
    """Download test data and print a compact summary (counts + property names)."""
    from graphdatascience.cli.database.output import print_summary

    print_summary(_fetch(env_file, label))


@app.command()
def fetch(
    label: Optional[str] = LABEL_OPT,
    output: OutputFormat = typer.Option(
        OutputFormat.table, "--output", "-o", help="Output format: table (default) or json."
    ),
    limit: str = typer.Option("10", "--limit", "-n", help="Max rows per table, or 'all'."),
    env_file: Optional[str] = ENV_FILE_OPT,
) -> None:
    """Download test data and print full node/relationship tables (or construct JSON).

    The ``json`` format is the construct format ``upload --file`` accepts, so a
    graph round-trips: ``fetch -o json > g.json`` then ``upload -f g.json``.
    """
    graph = _fetch(env_file, label)
    if output is OutputFormat.json:
        from graphdatascience.cli.database.output import print_json

        print_json(graph)
        return
    if limit.lower() == "all":
        row_limit: Optional[int] = None
    else:
        try:
            row_limit = int(limit)
        except ValueError as exc:
            raise typer.BadParameter("--limit must be an integer or 'all'.") from exc

    from graphdatascience.cli.database.output import print_tables

    print_tables(graph, row_limit)


@app.command()
def delete(
    label: Optional[str] = typer.Option(None, "--label", help="Delete only nodes with this label."),
    all: bool = typer.Option(False, "--all", help="Delete all test (Dev-labelled) data."),
    dry_run: bool = typer.Option(False, "--dry-run", help="Report what would be deleted without deleting."),
    env_file: Optional[str] = ENV_FILE_OPT,
) -> None:
    """Delete uploaded test data from the database."""
    if not all and not label:
        raise typer.BadParameter("Pass --all or --label <LABEL>.")
    client = _client(env_file)
    target = "all Dev-labelled test data" if all else f"test data with label '{label}'"
    stats = client.delete(all=True, dry_run=dry_run) if all else client.delete(label, dry_run=dry_run)
    verb = "Would delete" if dry_run else "Deleted"
    typer.echo(f"{verb} {stats.nodes} nodes and {stats.relationships} relationships ({target}).")
