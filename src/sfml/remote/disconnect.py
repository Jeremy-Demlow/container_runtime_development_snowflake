"""
Disconnect from remote development service.

Stops the running container service to save costs.
"""

from __future__ import annotations

import os
import subprocess
from typing import Optional

from rich.console import Console

console = Console()


def disconnect(
    name: str = "dev",
    connection_name: Optional[str] = None,
) -> bool:
    """
    Stop a running remote dev service.

    This stops the container service to save compute costs while preserving
    your files on the stage. You can reconnect later with connect().

    Args:
        name: Service name (default: "dev")
        connection_name: Snowflake connection name (uses default if None)

    Returns:
        True if successful, False otherwise

    Example:
        >>> from sfml.remote import disconnect
        >>> disconnect()  # Stops the "dev" service
        >>> disconnect(name="gpu-dev")  # Stops a different service
    """
    console.print(f"[yellow]Stopping remote dev service:[/] {name}")

    cmd = ["snow", "remote", "stop", "--name", name]

    if connection_name:
        cmd.extend(["--connection", connection_name])

    env = os.environ.copy()
    if connection_name:
        env["SNOWFLAKE_DEFAULT_CONNECTION_NAME"] = connection_name

    try:
        result = subprocess.run(
            cmd,
            env=env,
            capture_output=True,
            text=True,
        )

        if result.returncode == 0:
            console.print(f"[green]Service '{name}' stopped successfully[/]")
            console.print("[dim]Your files on stage are preserved. Use connect() to restart.[/]")
            return True
        else:
            if "not found" in result.stderr.lower() or "does not exist" in result.stderr.lower():
                console.print(f"[yellow]Service '{name}' not found or already stopped[/]")
                return True
            console.print(f"[red]Failed to stop service:[/] {result.stderr}")
            return False

    except FileNotFoundError:
        console.print("[red]Error:[/] 'snow' CLI not found. Install with: pip install snowflake-cli")
        return False
    except Exception as e:
        console.print(f"[red]Error stopping service:[/] {e}")
        return False


def list_services(
    connection_name: Optional[str] = None,
) -> None:
    """
    List active remote dev services.

    Args:
        connection_name: Snowflake connection name (uses default if None)
    """
    cmd = ["snow", "remote", "list"]

    if connection_name:
        cmd.extend(["--connection", connection_name])

    env = os.environ.copy()
    if connection_name:
        env["SNOWFLAKE_DEFAULT_CONNECTION_NAME"] = connection_name

    try:
        result = subprocess.run(
            cmd,
            env=env,
            capture_output=True,
            text=True,
        )

        if result.returncode == 0:
            console.print("[bold]Active Remote Dev Services:[/]")
            console.print(result.stdout or "[dim]No active services[/]")
        else:
            console.print(f"[yellow]Could not list services:[/] {result.stderr}")

    except FileNotFoundError:
        console.print("[red]Error:[/] 'snow' CLI not found")
    except Exception as e:
        console.print(f"[red]Error:[/] {e}")
