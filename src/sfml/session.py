"""
Snowflake session management.

Provides a simple way to get a Snowpark session using connection names
from ~/.snowflake/config.toml
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Optional
from functools import lru_cache

import tomllib
import snowflake.connector
from snowflake.snowpark import Session
from cryptography.hazmat.primitives import serialization


def _load_config():
    """Load snowflake config from ~/.snowflake/config.toml"""
    config_path = Path.home() / ".snowflake" / "config.toml"
    if not config_path.exists():
        return {}
    with open(config_path, "rb") as f:
        return tomllib.load(f)


def _load_private_key(key_path: str) -> bytes:
    """Load private key from file and return as bytes for Snowflake connector."""
    key_path = os.path.expanduser(key_path)
    with open(key_path, "rb") as f:
        p_key = serialization.load_pem_private_key(
            f.read(),
            password=None,
        )
    return p_key.private_bytes(
        encoding=serialization.Encoding.DER,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption()
    )


def _get_connection_config(connection_name: str) -> dict:
    """Get connection config with private key loaded if needed."""
    config = _load_config()

    if "connections" not in config or connection_name not in config["connections"]:
        raise ValueError(f"Connection '{connection_name}' not found in ~/.snowflake/config.toml")

    conn_config = dict(config["connections"][connection_name])

    # Handle JWT auth with private key
    if conn_config.get("authenticator") == "SNOWFLAKE_JWT":
        key_path = conn_config.pop("private_key_path", None)
        if key_path:
            conn_config["private_key"] = _load_private_key(key_path)
        conn_config.pop("authenticator", None)  # Not needed with private_key

    return conn_config


@lru_cache(maxsize=1)
def get_session(connection_name: Optional[str] = None) -> Session:
    """
    Get a Snowpark session using a connection name.

    Args:
        connection_name: Name of the connection in ~/.snowflake/config.toml
                        Defaults to SNOWFLAKE_CONNECTION_NAME env var or "default"

    Returns:
        Snowpark Session

    Example:
        session = get_session("my_connection")
        df = session.sql("SELECT 1").collect()
    """
    conn_name = connection_name or os.getenv("SNOWFLAKE_CONNECTION_NAME", "myconnection")
    conn_config = _get_connection_config(conn_name)

    conn = snowflake.connector.connect(**conn_config)
    return Session.builder.configs({"connection": conn}).create()


def get_connection(connection_name: Optional[str] = None):
    """
    Get a raw Snowflake connector connection.

    Args:
        connection_name: Name of the connection in ~/.snowflake/config.toml

    Returns:
        snowflake.connector.SnowflakeConnection
    """
    conn_name = connection_name or os.getenv("SNOWFLAKE_CONNECTION_NAME", "myconnection")
    conn_config = _get_connection_config(conn_name)
    return snowflake.connector.connect(**conn_config)


def clear_session_cache():
    """Clear cached session (useful for reconnecting)."""
    get_session.cache_clear()
