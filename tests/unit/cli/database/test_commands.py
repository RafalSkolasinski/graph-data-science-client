from typer.testing import CliRunner

from graphdatascience.cli.database.commands import app

runner = CliRunner()


def test_upload_dry_run_does_not_touch_database() -> None:
    result = runner.invoke(app, ["upload", "homogeneous", "--dry-run"])

    assert result.exit_code == 0
    assert "Dry run: nothing written." in result.output


def test_upload_requires_exactly_one_source() -> None:
    result = runner.invoke(app, ["upload"])

    assert result.exit_code != 0
    assert "Provide exactly one of EXAMPLE" in result.output


def test_upload_rejects_example_and_file_together() -> None:
    result = runner.invoke(app, ["upload", "homogeneous", "--file", "whatever.json"])

    assert result.exit_code != 0
    assert "Provide exactly one of EXAMPLE" in result.output


def test_upload_unknown_example_exits_nonzero() -> None:
    result = runner.invoke(app, ["upload", "does-not-exist", "--dry-run"])

    assert result.exit_code == 1
    assert "Unknown example" in result.output


def test_delete_requires_all_or_label() -> None:
    result = runner.invoke(app, ["delete"])

    assert result.exit_code != 0
    assert "Pass --all or --label" in result.output
