"""
Snowflake ML Accelerator - Rapid ML development and scaling on Snowflake.

Two main capabilities:
1. Remote Dev - Develop in VS Code/Cursor connected to Snowflake container
2. ML Jobs - Submit Python files/directories to run on Snowflake compute

Quick Start:
    # Setup remote dev environment
    from sfml.remote import setup, connect
    setup(connection_name="my_conn", project_name="ml_dev")
    connect(connection_name="my_conn", project_name="ml_dev")

    # Submit ML Jobs
    from sfml.jobs import submit_file, submit_directory
    result = submit_file("my_script.py", compute_pool="GPU_POOL", wait=True)
"""

__version__ = "0.1.0"

from sfml.remote import setup, connect, teardown
from sfml.jobs import submit_file, submit_directory, get_job_status, list_jobs
from sfml.session import get_session

__all__ = [
    "setup",
    "connect",
    "teardown",
    "submit_file",
    "submit_directory",
    "get_job_status",
    "list_jobs",
    "get_session",
]
