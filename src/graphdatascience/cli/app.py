"""Root ``gds`` command: ``gds database ...`` and ``gds session ...``."""

from __future__ import annotations

try:
    import typer
except ImportError as exc:
    raise SystemExit(
        "The `gds` CLI requires extra dependencies that are not installed.\n"
        'Install them with: pip install "graphdatascience[cli]"\n'
        '(or, for an editable/tool install: uv tool install --editable ".[cli]")'
    ) from exc

from graphdatascience.cli.database.commands import app as database_app
from graphdatascience.cli.session.commands import app as session_app

app = typer.Typer(
    help="Manage GDS test databases and Aura GDS sessions.",
    no_args_is_help=True,
)
app.add_typer(database_app, name="database")
app.add_typer(session_app, name="session")


if __name__ == "__main__":
    app()
