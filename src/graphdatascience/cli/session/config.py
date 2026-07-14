"""Standardized GDS job config (see ``cli/session/schema/job-config.schema.json``).

A job = project a graph, run an ordered list of algorithms on it, optionally
write mutated properties back. Credentials are never part of the config.

Every config is validated against ``job-config.schema.json`` (the same document
the ``gds-jobs-api`` Go server validates against) before pydantic parsing, so a
config that satisfies one validates the same way against the other.
"""

from __future__ import annotations

import functools
import json
import os
from importlib import resources
from pathlib import Path
from typing import Any, Literal, Optional

import jsonschema
import yaml
from pydantic import BaseModel, ConfigDict, Field, model_validator

JOB_CONFIG_ENV_VAR = "GDS_JOB_CONFIG"


@functools.lru_cache(maxsize=1)
def _schema() -> dict[str, Any]:
    schema_text = (
        resources.files("graphdatascience.cli.session").joinpath("schema", "job-config.schema.json").read_text()
    )
    schema: dict[str, Any] = json.loads(schema_text)
    return schema


def _validate_against_schema(data: Any) -> None:
    jsonschema.Draft202012Validator(_schema()).validate(data)


class SessionConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str
    memory: str
    ttl_minutes: int = Field(ge=1)


class ProjectionConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    graph_name: str
    query: str


class AlgorithmConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str
    mode: Literal["mutate", "write"]
    mutate_property: Optional[str] = None
    write_property: Optional[str] = None
    parameters: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def _check_property(self) -> "AlgorithmConfig":
        if self.mode == "mutate" and not self.mutate_property:
            raise ValueError(f"algorithm '{self.name}' has mode=mutate but no mutate_property")
        if self.mode == "write" and not self.write_property:
            raise ValueError(f"algorithm '{self.name}' has mode=write but no write_property")
        return self


class WritebackConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    node_properties: list[str] = Field(default_factory=list)


class JobConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    session: SessionConfig
    projection: ProjectionConfig
    algorithms: list[AlgorithmConfig] = Field(min_length=1)
    writeback: Optional[WritebackConfig] = None

    @classmethod
    def _from_data(cls, data: Any) -> "JobConfig":
        _validate_against_schema(data)
        return cls.model_validate(data)

    @classmethod
    def from_file(cls, path: str | Path) -> "JobConfig":
        data = yaml.safe_load(Path(path).expanduser().read_text())
        return cls._from_data(data)

    @classmethod
    def from_env(cls, var: str = JOB_CONFIG_ENV_VAR) -> "JobConfig":
        """Build a config from a YAML document in an environment variable.

        Lets a single k8s Job resource carry its config inline (as a literal env
        var) instead of needing a paired ConfigMap + volume mount.
        """
        raw = os.environ.get(var)
        if not raw:
            raise RuntimeError(f"No --config given and {var!r} is not set")
        return cls._from_data(yaml.safe_load(raw))
