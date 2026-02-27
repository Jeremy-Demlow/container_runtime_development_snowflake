"""
Remote development connection.

Provides a simple way to connect to a Snowflake container for interactive development.
"""

from __future__ import annotations

import os
import platform
import shutil
import subprocess
import sys
from typing import Optional


def _find_editor_path(editor: str) -> Optional[str]:
    """Find the editor binary directory on macOS if not in PATH."""
    if shutil.which(editor):
        return None  # Already in PATH

    if platform.system() == "Darwin":
        mac_paths = {
            "code": "/Applications/Visual Studio Code.app/Contents/Resources/app/bin",
            "cursor": "/Applications/Cursor.app/Contents/Resources/app/bin",
        }
        if editor in mac_paths:
            bin_dir = mac_paths[editor]
            if os.path.exists(os.path.join(bin_dir, editor)):
                return bin_dir

    return None


def connect(
    name: str = "dev",
    compute_pool: str = "ML_ACCELERATOR_POOL",
    stage: str = "@ML_ACCELERATOR.PUBLIC.DEV_STAGE",
    eai: str = "ALLOW_ALL_INTEGRATION",
    connection_name: Optional[str] = None,
    editor: str = "cursor",
):
    """
    Connect to a remote dev container in Snowflake.

    This creates a container service and opens your editor connected to it.
    Your code syncs to the specified stage.

    Args:
        name: Name for the dev environment
        compute_pool: Compute pool to use (e.g., GPU_DEV_POOL, CPU_X64_M)
        stage: Stage path for code sync (e.g., @DB.SCHEMA.STAGE)
        eai: External access integration name
        connection_name: Snowflake connection name from ~/.snowflake/config.toml
        editor: Editor to use - "cursor" or "code" (VS Code)

    Example:
        from sfml import connect

        # Connect with Cursor to GPU pool
        connect(compute_pool="GPU_DEV_POOL")

        # Connect with VS Code to CPU pool
        connect(compute_pool="CPU_X64_M", editor="code")
    """
    editor_bin_dir = _find_editor_path(editor)

    env = os.environ.copy()
    if editor_bin_dir:
        env["PATH"] = editor_bin_dir + ":" + env.get("PATH", "")

    cmd = [
        "snow", "remote", editor, name,
        "--compute-pool", compute_pool,
        "--eai-name", eai,
        "--stage", stage,
    ]

    if connection_name:
        cmd.extend(["-c", connection_name])

    print(f"🚀 Connecting to remote dev environment '{name}'")
    print(f"   Pool: {compute_pool}")
    print(f"   Stage: {stage}")
    print(f"   Editor: {editor}")
    print()
    print("   (Keep this running - Ctrl+C to disconnect)")
    print()

    try:
        subprocess.run(cmd, check=True, env=env)
    except KeyboardInterrupt:
        print("\n\n👋 Disconnected from remote dev")
    except subprocess.CalledProcessError as e:
        print(f"\nConnection error. The service may still be starting.")
        print(f"Try again in a minute or check status: snow remote list -c {connection_name or 'default'}")
        sys.exit(1)
    except FileNotFoundError:
        print("Error: 'snow' CLI not found. Make sure snowflake-cli is installed:")
        print("  pip install -e .")
        sys.exit(1)


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Connect to Snowflake remote dev")
    parser.add_argument("--name", "-n", default="dev", help="Environment name")
    parser.add_argument("--pool", "-p", default="ML_ACCELERATOR_POOL", help="Compute pool")
    parser.add_argument("--stage", "-s", default="@ML_ACCELERATOR.PUBLIC.DEV_STAGE", help="Stage path")
    parser.add_argument("--eai", default="ALLOW_ALL_INTEGRATION", help="External access integration")
    parser.add_argument("--connection", "-c", help="Connection name")
    parser.add_argument("--editor", "-e", default="cursor", choices=["cursor", "code"], help="Editor")

    args = parser.parse_args()

    connect(
        name=args.name,
        compute_pool=args.pool,
        stage=args.stage,
        eai=args.eai,
        connection_name=args.connection,
        editor=args.editor,
    )


if __name__ == "__main__":
    main()
