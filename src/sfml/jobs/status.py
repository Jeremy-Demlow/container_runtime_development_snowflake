"""
ML Job status and monitoring.

Functions to check job status and list jobs.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from rich.console import Console
from rich.table import Table

from sfml.session import get_session

console = Console()


def get_job_status(
    job_id: str,
    connection_name: Optional[str] = None,
    verbose: bool = True,
) -> Dict[str, Any]:
    """
    Get status of an ML Job.

    Args:
        job_id: The job ID returned from submit_file/submit_directory
        connection_name: Snowflake connection name
        verbose: Print status to console

    Returns:
        Dict with job status and metadata

    Example:
        status = get_job_status("01b12345-...")
        print(f"Status: {status['status']}")
    """
    from snowflake.ml.jobs import get_job

    session = get_session(connection_name)
    job = get_job(job_id, session=session)

    result = {
        "job_id": job.id,
        "status": str(job.status),
    }

    if verbose:
        console.print(f"[bold]Job {job_id}[/]")
        console.print(f"  Status: {job.status}")

    if str(job.status).upper() == "DONE":
        try:
            job_result = job.result()
            if job_result:
                result["result"] = job_result
                if verbose:
                    console.print(f"  Result: {job_result}")
        except Exception:
            pass

    return result


def list_jobs(
    connection_name: Optional[str] = None,
    limit: int = 10,
    verbose: bool = True,
) -> List[Dict[str, Any]]:
    """
    List recent ML Jobs.

    Args:
        connection_name: Snowflake connection name
        limit: Maximum number of jobs to return
        verbose: Print table to console

    Returns:
        List of job dicts with id, status, compute_pool, etc.

    Example:
        jobs = list_jobs(limit=5)
        for job in jobs:
            print(f"{job['job_id']}: {job['status']}")
    """
    from snowflake.ml import jobs

    session = get_session(connection_name)

    job_df = jobs.list_jobs(session=session)

    if hasattr(job_df, "to_pandas"):
        df = job_df.to_pandas()
    else:
        df = job_df

    if len(df) > limit:
        df = df.head(limit)

    result = []
    for _, row in df.iterrows():
        job_info = {
            "job_id": str(row.get("name", row.get("NAME", ""))),
            "status": str(row.get("status", row.get("STATUS", ""))),
            "compute_pool": str(row.get("compute_pool", row.get("COMPUTE_POOL", ""))),
        }
        result.append(job_info)

    if verbose and result:
        table = Table(title="Recent ML Jobs")
        table.add_column("Job ID", style="cyan")
        table.add_column("Status", style="green")
        table.add_column("Compute Pool")

        for job in result:
            table.add_row(
                job["job_id"][:40] + "..." if len(job["job_id"]) > 40 else job["job_id"],
                job["status"],
                job["compute_pool"],
            )

        console.print(table)

    return result


def wait_for_job(
    job_id: str,
    connection_name: Optional[str] = None,
    timeout: int = 3600,
    verbose: bool = True,
) -> Dict[str, Any]:
    """
    Wait for a job to complete.

    Args:
        job_id: The job ID
        connection_name: Snowflake connection name
        timeout: Timeout in seconds
        verbose: Print progress

    Returns:
        Dict with final status
    """
    from snowflake.ml.jobs import get_job

    session = get_session(connection_name)
    job = get_job(job_id, session=session)

    if verbose:
        console.print(f"[dim]Waiting for job {job_id}...[/]")

    job.wait(timeout=timeout)

    result = {
        "job_id": job.id,
        "status": str(job.status),
    }

    if verbose:
        console.print(f"[bold green]✓ Job complete: {job.status}[/]")

    return result
