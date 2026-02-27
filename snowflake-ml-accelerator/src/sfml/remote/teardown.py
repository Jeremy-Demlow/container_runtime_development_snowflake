"""
Teardown remote development infrastructure.

Removes compute pools, services, stages, and other resources.
"""

from __future__ import annotations

from typing import Any, Dict, Optional

from rich.console import Console

from sfml.config import Config
from sfml.session import get_session

console = Console()


def teardown(
    connection_name: str,
    project_name: str,
    database: str = "ML_DEV",
    pool_name: Optional[str] = None,
    stage_name: str = "DEV_STAGE",
    eai_name: str = "ALLOW_ALL_INTEGRATION",
    keep_stage: bool = True,
    keep_database: bool = True,
    execute: bool = True,
    verbose: bool = True,
) -> Dict[str, Any]:
    """
    Teardown remote dev infrastructure.

    By default, preserves stage (your files) and database for safety.

    Args:
        connection_name: Snowflake connection name
        project_name: Project name
        database: Database name
        pool_name: Compute pool name
        stage_name: Stage name
        eai_name: External Access Integration name
        keep_stage: If True, keep the stage (preserves files)
        keep_database: If True, keep the database
        execute: If True, execute SQL. If False, just return SQL.
        verbose: Print progress messages

    Returns:
        Dict with status and generated SQL
    """
    pool_name = pool_name or f"{project_name}_pool"

    sql_parts = [f"-- Teardown for project: {project_name}", "USE ROLE ACCOUNTADMIN;"]

    sql_parts.append(f"\n-- Suspend and drop compute pool")
    sql_parts.append(f"ALTER COMPUTE POOL IF EXISTS {pool_name} STOP ALL;")
    sql_parts.append(f"ALTER COMPUTE POOL IF EXISTS {pool_name} SUSPEND;")
    sql_parts.append(f"DROP COMPUTE POOL IF EXISTS {pool_name};")

    sql_parts.append(f"\n-- Drop External Access Integration")
    sql_parts.append(f"DROP INTEGRATION IF EXISTS {eai_name};")
    sql_parts.append(f"DROP NETWORK RULE IF EXISTS {database}.PUBLIC.{eai_name}_rule;")

    if not keep_stage:
        sql_parts.append(f"\n-- Drop Stage (WARNING: deletes all files!)")
        sql_parts.append(f"DROP STAGE IF EXISTS {database}.PUBLIC.{stage_name};")

    if not keep_database:
        sql_parts.append(f"\n-- Drop Database")
        sql_parts.append(f"DROP DATABASE IF EXISTS {database};")

    sql = "\n".join(sql_parts)

    result = {
        "project_name": project_name,
        "database": database,
        "compute_pool": pool_name,
        "stage_preserved": keep_stage,
        "database_preserved": keep_database,
        "sql": sql,
    }

    if verbose:
        console.print(f"[bold yellow]Tearing down remote dev environment[/]")
        console.print(f"  Project: {project_name}")
        console.print(f"  Compute Pool: {pool_name}")
        if keep_stage:
            console.print(f"  Stage: {stage_name} [green](preserved)[/]")
        else:
            console.print(f"  Stage: {stage_name} [red](will be deleted!)[/]")
        if keep_database:
            console.print(f"  Database: {database} [green](preserved)[/]")

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
            console.print(f"\n[bold green]✓ Teardown complete![/]")

        result["status"] = "complete"
    else:
        result["status"] = "sql_generated"

    return result


def teardown_from_config(
    config_path: Optional[str] = None,
    keep_stage: bool = True,
    keep_database: bool = True,
    execute: bool = True,
) -> Dict[str, Any]:
    """
    Teardown from a YAML config file.

    Args:
        config_path: Path to config YAML
        keep_stage: If True, preserve the stage
        keep_database: If True, preserve the database
        execute: If True, execute SQL

    Returns:
        Dict with status
    """
    config = Config.load(config_path)

    return teardown(
        connection_name=config.connection_name,
        project_name=config.project.name,
        database=config.project.database,
        pool_name=config.compute.pool_name,
        stage_name=config.storage.stage_name,
        eai_name=config.network.eai_name,
        keep_stage=keep_stage,
        keep_database=keep_database,
        execute=execute,
    )
