"""``gds session`` — create/list/delete a managed Aura GDS session, and run a
standardized GDS job (projection -> algorithms -> writeback) against it.

Feed a standardized job config and run the whole pipeline (`run`), or one step
at a time (`project` / `algorithms` / `writeback`) so each can be a separate k8s
step. `drop` removes the projected graph so a session can be reused for another
experiment. Credentials come from the unified env set (see
:mod:`graphdatascience.cli.common.env`). A ``.env`` in the working directory is
loaded automatically; pass --env-file for another dotenv file. Real environment
variables always take precedence over dotenv files.

The job config itself is either a file (`--config`) or, if omitted, a YAML
document in the $GDS_JOB_CONFIG env var — lets a single k8s Job resource carry
its config inline instead of needing a paired ConfigMap + volume mount.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Optional

import typer

if TYPE_CHECKING:
    from graphdatascience.cli.session.config import JobConfig
    from graphdatascience.session.aura_graph_data_science import AuraGraphDataScience

app = typer.Typer(
    help="Manage a GDS session and run a standardized GDS job (projection -> algorithms -> writeback) against it.",
    no_args_is_help=True,
)

CONFIG_OPT = typer.Option(
    None, "--config", "-c", help="Path to the job config (YAML). If omitted, reads YAML from $GDS_JOB_CONFIG."
)
ENV_FILE_OPT = typer.Option(
    None,
    "--env-file",
    help="Extra dotenv file to read (a .env in the working dir loads automatically; real env vars win).",
)


def _load(config: Optional[str], env_file: Optional[str]) -> JobConfig:
    from graphdatascience.cli.common.env import load_env
    from graphdatascience.cli.session.config import JobConfig

    load_env(env_file)
    if config is not None:
        return JobConfig.from_file(config)
    return JobConfig.from_env()


def _connect(cfg: JobConfig) -> AuraGraphDataScience:
    from graphdatascience.cli.session.session_ops import connect

    typer.echo(f"Connecting to session '{cfg.session.name}' ...")
    gds = connect(cfg.session)
    typer.echo(f"Session '{cfg.session.name}' is ready.")
    return gds


@app.command()
def create(config: Optional[str] = CONFIG_OPT, env_file: Optional[str] = ENV_FILE_OPT) -> None:
    """Create (or reconnect to) the session defined in the config."""
    cfg = _load(config, env_file)
    _connect(cfg)


@app.command()
def delete(config: Optional[str] = CONFIG_OPT, env_file: Optional[str] = ENV_FILE_OPT) -> None:
    """Delete the session defined in the config."""
    from graphdatascience.cli.session.session_ops import delete as delete_session

    cfg = _load(config, env_file)
    deleted = delete_session(cfg.session)
    if deleted:
        typer.secho(f"Deleted session '{cfg.session.name}'.", fg=typer.colors.GREEN)
    else:
        typer.echo(f"No session named '{cfg.session.name}' found.")


@app.command(name="list")
def list_(env_file: Optional[str] = ENV_FILE_OPT) -> None:
    """List every GDS session visible to the configured Aura API credentials."""
    from graphdatascience.cli.common.env import load_env
    from graphdatascience.cli.session.session_ops import list_sessions

    load_env(env_file)
    sessions = list_sessions()
    if not sessions:
        typer.echo("No sessions found.")
        return
    for info in sessions:
        typer.echo(f"{info.name}  id={info.id}  status={info.status}  memory={info.memory}  ttl={info.ttl}")


@app.command()
def run(
    config: Optional[str] = CONFIG_OPT,
    overwrite_graph: bool = typer.Option(
        False, "--overwrite-graph", help="Drop an existing same-named graph before projecting."
    ),
    delete_session: bool = typer.Option(
        False,
        "--delete-session",
        envvar="GDS_RUNNER_DELETE_SESSION",
        help="Delete the session once the job completes (e.g. for a one-off k8s Job).",
    ),
    env_file: Optional[str] = ENV_FILE_OPT,
) -> None:
    """Run all steps: project -> algorithms -> writeback."""
    from graphdatascience.cli.session.session_ops import delete as delete_session_op
    from graphdatascience.cli.session.steps import run_all

    cfg = _load(config, env_file)
    gds = _connect(cfg)
    typer.echo(f"Proceeding with graph projection '{cfg.projection.graph_name}' ...")
    result = run_all(gds, cfg, overwrite_graph=overwrite_graph)
    typer.echo(f"Projected graph '{result['graph']}'.")
    for name, _ in result["algorithms"]:
        typer.echo(f"  ran algorithm: {name}")
    if result["writeback"] is not None:
        assert cfg.writeback is not None
        typer.echo(f"  wrote back: {cfg.writeback.node_properties}")
    if delete_session:
        delete_session_op(cfg.session)
        typer.echo(f"Deleted session '{cfg.session.name}'.")
    typer.secho("Job complete.", fg=typer.colors.GREEN)


@app.command()
def project(
    config: Optional[str] = CONFIG_OPT,
    overwrite_graph: bool = typer.Option(
        False, "--overwrite-graph", help="Drop an existing same-named graph before projecting."
    ),
    env_file: Optional[str] = ENV_FILE_OPT,
) -> None:
    """Step 1: project the graph into the session."""
    from graphdatascience.cli.session.steps import project as project_step

    cfg = _load(config, env_file)
    gds = _connect(cfg)
    typer.echo(f"Proceeding with graph projection '{cfg.projection.graph_name}' ...")
    graph = project_step(gds, cfg, overwrite=overwrite_graph)
    typer.secho(f"Projected graph '{graph.name()}'.", fg=typer.colors.GREEN)


@app.command()
def algorithms(
    config: Optional[str] = CONFIG_OPT,
    only: Optional[str] = typer.Option(None, "--only", help="Run only the named algorithm from the list."),
    env_file: Optional[str] = ENV_FILE_OPT,
) -> None:
    """Step 2: run the ordered list of algorithms on the projected graph."""
    from graphdatascience.cli.session.steps import run_algorithms

    cfg = _load(config, env_file)
    gds = _connect(cfg)
    results = run_algorithms(gds, cfg, only=only)
    for name, _ in results:
        typer.echo(f"  ran algorithm: {name}")
    typer.secho("Algorithms complete.", fg=typer.colors.GREEN)


@app.command()
def writeback(config: Optional[str] = CONFIG_OPT, env_file: Optional[str] = ENV_FILE_OPT) -> None:
    """Step 3: write mutated node properties back to the database."""
    from graphdatascience.cli.session.steps import writeback as writeback_step

    cfg = _load(config, env_file)
    gds = _connect(cfg)
    result = writeback_step(gds, cfg)
    if result is None:
        typer.echo("No writeback configured; nothing to do.")
    else:
        assert cfg.writeback is not None
        typer.secho(f"Wrote back: {cfg.writeback.node_properties}", fg=typer.colors.GREEN)


@app.command()
def drop(config: Optional[str] = CONFIG_OPT, env_file: Optional[str] = ENV_FILE_OPT) -> None:
    """Drop the projected graph from the session, keeping the session for reuse."""
    from graphdatascience.cli.session.steps import drop as drop_step

    cfg = _load(config, env_file)
    gds = _connect(cfg)
    drop_step(gds, cfg)
    typer.secho(f"Dropped graph '{cfg.projection.graph_name}'.", fg=typer.colors.GREEN)
