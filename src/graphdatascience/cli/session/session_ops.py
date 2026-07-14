"""Create / reconnect to / delete / list the managed GDS session for a job.

``get_or_create`` is idempotent by session name, and the projected graph lives
server-side in the session catalog. That is what lets the per-step CLI commands
(project / algorithms / writeback) each reconnect independently and still see the
same graph by name.
"""

from __future__ import annotations

from datetime import timedelta

from graphdatascience.cli.common.env import aura_api_credentials_from_env, dbms_connection_info_from_env
from graphdatascience.cli.session.config import SessionConfig
from graphdatascience.session import AuraGraphDataScience, GdsSessions, SessionInfo


def build_sessions() -> GdsSessions:
    """Create a GdsSessions handle from Aura API credentials in the environment."""
    return GdsSessions(api_credentials=aura_api_credentials_from_env())


def connect(cfg: SessionConfig) -> AuraGraphDataScience:
    """Create the session if needed, otherwise reconnect to it; returns the gds handle."""
    sessions = build_sessions()
    gds = sessions.get_or_create(
        session_name=cfg.name,
        memory=cfg.memory,
        db_connection=dbms_connection_info_from_env(),
        ttl=timedelta(minutes=cfg.ttl_minutes),
    )
    gds.verify_connectivity()
    return gds


def delete(cfg: SessionConfig) -> bool:
    """Delete the session by name. Returns True if a session was deleted."""
    return build_sessions().delete(session_name=cfg.name)


def list_sessions() -> list[SessionInfo]:
    """List every GDS session visible to the configured Aura API credentials."""
    return build_sessions().list()
