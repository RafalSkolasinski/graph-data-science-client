from pathlib import Path

import pytest
import yaml
from pydantic import ValidationError

from graphdatascience.cli.session.config import JOB_CONFIG_ENV_VAR, JobConfig

VALID_CONFIG = {
    "session": {"name": "gds-examples", "memory": "2GB", "ttl_minutes": 30},
    "projection": {"graph_name": "social", "query": "RETURN gds.graph.project.remote(n, m)"},
    "algorithms": [{"name": "louvain", "mode": "mutate", "mutate_property": "community"}],
    "writeback": {"node_properties": ["community"]},
}


def test_job_config_from_data_valid() -> None:
    cfg = JobConfig._from_data(VALID_CONFIG)

    assert cfg.session.name == "gds-examples"
    assert cfg.algorithms[0].name == "louvain"
    assert cfg.writeback is not None
    assert cfg.writeback.node_properties == ["community"]


def test_job_config_rejects_unknown_top_level_field() -> None:
    import jsonschema

    data = {**VALID_CONFIG, "extra": "nope"}

    with pytest.raises(jsonschema.exceptions.ValidationError):
        JobConfig._from_data(data)


def test_job_config_algorithm_mutate_requires_mutate_property() -> None:
    data = {
        **VALID_CONFIG,
        "algorithms": [{"name": "louvain", "mode": "mutate"}],
    }

    with pytest.raises(ValidationError, match="mode=mutate but no mutate_property"):
        JobConfig._from_data(data)


def test_job_config_algorithm_write_requires_write_property() -> None:
    data = {
        **VALID_CONFIG,
        "algorithms": [{"name": "louvain", "mode": "write"}],
    }

    with pytest.raises(ValidationError, match="mode=write but no write_property"):
        JobConfig._from_data(data)


def test_job_config_from_file(tmp_path: Path) -> None:
    config_path = tmp_path / "job.yaml"
    config_path.write_text(yaml.safe_dump(VALID_CONFIG))

    cfg = JobConfig.from_file(config_path)

    assert cfg.projection.graph_name == "social"


def test_job_config_from_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv(JOB_CONFIG_ENV_VAR, yaml.safe_dump(VALID_CONFIG))

    cfg = JobConfig.from_env()

    assert cfg.session.ttl_minutes == 30


def test_job_config_from_env_missing_raises(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv(JOB_CONFIG_ENV_VAR, raising=False)

    with pytest.raises(RuntimeError, match="GDS_JOB_CONFIG"):
        JobConfig.from_env()
