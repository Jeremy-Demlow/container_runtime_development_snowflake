"""
Setup infrastructure for remote development.

Creates compute pools, stages, network rules, and external access integrations.
"""

from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Any, Dict, List, Optional

from rich.console import Console

from sfml.config import Config
from sfml.session import get_session

console = Console()


def setup(
    connection_name: str,
    project_name: str = "ml_accelerator",
    database: str = "ML_ACCELERATOR",
    instance_family: str = "CPU_X64_M",
    stage_name: str = "DEV_STAGE",
    pool_name: Optional[str] = None,
    eai_name: str = "ALLOW_ALL_INTEGRATION",
    allow_ports: Optional[List[int]] = None,
    min_nodes: int = 1,
    max_nodes: int = 1,
    execute: bool = True,
    verbose: bool = True,
) -> Dict[str, Any]:
    """
    Create all infrastructure for remote development.

    Creates:
    - Database (if not exists)
    - Compute Pool
    - Stage for persistent storage
    - Network rules for internet access
    - External Access Integration

    Args:
        connection_name: Snowflake connection name from ~/.snowflake/config.toml
        project_name: Project name (used in resource naming)
        database: Database name to create
        instance_family: Compute instance type
                        CPU: CPU_X64_S, CPU_X64_M, CPU_X64_L
                        GPU: GPU_NV_S, GPU_NV_M
        stage_name: Stage name for persistent storage
        pool_name: Compute pool name (defaults to {project_name}_pool)
        eai_name: External Access Integration name
        allow_ports: Ports to allow (default: [443, 80])
        min_nodes: Minimum compute nodes
        max_nodes: Maximum compute nodes
        execute: If True, execute SQL. If False, just return SQL.
        verbose: Print progress messages

    Returns:
        Dict with created resource names and generated SQL

    Example:
        result = setup(
            connection_name="my_conn",
            project_name="ml_dev",
            instance_family="GPU_NV_S"
        )
    """
    pool_name = pool_name or f"{project_name}_pool"
    allow_ports = allow_ports or [443, 80]

    port_list = ", ".join([f"'0.0.0.0:{port}'" for port in allow_ports])

    sql = f"""-- Snowflake Remote Dev Setup
-- Project: {project_name}

USE ROLE ACCOUNTADMIN;

-- Create Database
CREATE DATABASE IF NOT EXISTS {database};
USE DATABASE {database};

-- Create Network Rule for External Access
CREATE OR REPLACE NETWORK RULE {eai_name}_rule
  MODE = EGRESS
  TYPE = HOST_PORT
  VALUE_LIST = ({port_list});

-- Create External Access Integration
CREATE OR REPLACE EXTERNAL ACCESS INTEGRATION {eai_name}
  ALLOWED_NETWORK_RULES = ({eai_name}_rule)
  ENABLED = true;

-- Grant permissions
GRANT USAGE ON INTEGRATION {eai_name} TO ROLE ACCOUNTADMIN;

-- Create Stage for Persistent Storage
CREATE STAGE IF NOT EXISTS {stage_name}
  ENCRYPTION = (TYPE = 'SNOWFLAKE_SSE');

-- Create Compute Pool
CREATE COMPUTE POOL IF NOT EXISTS {pool_name}
  MIN_NODES = {min_nodes}
  MAX_NODES = {max_nodes}
  INSTANCE_FAMILY = {instance_family};

-- Show created resources
SHOW COMPUTE POOLS LIKE '{pool_name}';
"""

    result = {
        "database": database,
        "compute_pool": pool_name,
        "stage": stage_name,
        "eai_name": eai_name,
        "instance_family": instance_family,
        "sql": sql,
    }

    if verbose:
        console.print(f"[bold blue]Setting up remote dev environment[/]")
        console.print(f"  Project: {project_name}")
        console.print(f"  Database: {database}")
        console.print(f"  Compute Pool: {pool_name} ({instance_family})")
        console.print(f"  Stage: {stage_name}")

    if execute:
        if verbose:
            console.print("\n[yellow]SQL to execute:[/]")
            console.print(sql)
            console.print()

        session = get_session(connection_name)

        statements = [s.strip() for s in sql.split(";") if s.strip() and not s.strip().startswith("--")]

        for stmt in statements:
            if stmt:
                try:
                    session.sql(stmt).collect()
                except Exception as e:
                    if verbose:
                        console.print(f"[yellow]Warning:[/] {e}")

        if verbose:
            console.print(f"\n[bold green]✓ Setup complete![/]")
            console.print(f"\nNext steps:")
            console.print(f"  1. Wait 2-3 minutes for compute pool to start")
            console.print(f"  2. Run: connect('{connection_name}', '{project_name}')")

        result["status"] = "complete"
    else:
        result["status"] = "sql_generated"

    return result


def setup_from_config(config_path: Optional[str] = None, execute: bool = True) -> Dict[str, Any]:
    """
    Setup from a YAML config file.

    Args:
        config_path: Path to config YAML. Uses default if None.
        execute: If True, execute SQL. If False, just return SQL.

    Returns:
        Dict with created resource names
    """
    config = Config.load(config_path)

    return setup(
        connection_name=config.connection_name,
        project_name=config.project.name,
        database=config.project.database,
        instance_family=config.compute.instance_family,
        stage_name=config.storage.stage_name,
        pool_name=config.compute.pool_name,
        eai_name=config.network.eai_name,
        allow_ports=config.network.allow_ports,
        min_nodes=config.compute.min_nodes,
        max_nodes=config.compute.max_nodes,
        execute=execute,
    )
