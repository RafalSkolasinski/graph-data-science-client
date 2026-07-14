from datetime import timedelta
from unittest.mock import MagicMock, patch

import pytest

from graphdatascience.cli.session.config import SessionConfig
from graphdatascience.cli.session.session_ops import build_sessions, connect, delete, list_sessions


@pytest.fixture(autouse=True)
def _aura_credentials_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("CLIENT_ID", "client-id")
    monkeypatch.setenv("CLIENT_SECRET", "client-secret")
    monkeypatch.setenv("NEO4J_USERNAME", "neo4j")
    monkeypatch.setenv("NEO4J_PASSWORD", "password")
    monkeypatch.setenv("AURA_INSTANCEID", "instance-id")


def test_build_sessions_uses_env_credentials() -> None:
    with patch("graphdatascience.cli.session.session_ops.GdsSessions") as gds_sessions_cls:
        build_sessions()

    _, kwargs = gds_sessions_cls.call_args
    assert kwargs["api_credentials"].client_id == "client-id"
    assert kwargs["api_credentials"].client_secret == "client-secret"


def test_connect_gets_or_creates_and_verifies() -> None:
    cfg = SessionConfig(name="my-session", memory="2GB", ttl_minutes=30)
    fake_gds = MagicMock()
    fake_sessions = MagicMock()
    fake_sessions.get_or_create.return_value = fake_gds

    with patch("graphdatascience.cli.session.session_ops.GdsSessions", return_value=fake_sessions):
        result = connect(cfg)

    fake_sessions.get_or_create.assert_called_once()
    _, kwargs = fake_sessions.get_or_create.call_args
    assert kwargs["session_name"] == "my-session"
    assert kwargs["memory"] == "2GB"
    assert kwargs["ttl"] == timedelta(minutes=30)
    fake_gds.verify_connectivity.assert_called_once()
    assert result is fake_gds


def test_delete_calls_sessions_delete() -> None:
    cfg = SessionConfig(name="my-session", memory="2GB", ttl_minutes=30)
    fake_sessions = MagicMock()
    fake_sessions.delete.return_value = True

    with patch("graphdatascience.cli.session.session_ops.GdsSessions", return_value=fake_sessions):
        result = delete(cfg)

    fake_sessions.delete.assert_called_once_with(session_name="my-session")
    assert result is True


def test_list_sessions_calls_sessions_list() -> None:
    fake_sessions = MagicMock()
    fake_sessions.list.return_value = []

    with patch("graphdatascience.cli.session.session_ops.GdsSessions", return_value=fake_sessions):
        result = list_sessions()

    fake_sessions.list.assert_called_once()
    assert result == []
