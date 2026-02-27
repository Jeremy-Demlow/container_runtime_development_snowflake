"""
Submit ML Jobs to Snowflake.

Provides simple functions to submit Python files and directories
to run on Snowflake's ML Jobs infrastructure (Ray on SPCS).
"""

from __future__ import annotations

import shutil
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Optional

from rich.console import Console

from sfml.session import get_session

console = Console()


def submit_file(
    file_path: str,
    compute_pool: str,
    connection_name: Optional[str] = None,
    pip_requirements: Optional[List[str]] = None,
    args: Optional[List[str]] = None,
    stage_name: str = "ML_JOBS_STAGE",
    external_access_integrations: Optional[List[str]] = None,
    wait: bool = False,
    timeout: int = 3600,
    verbose: bool = True,
) -> Dict[str, Any]:
    """
    Submit a single Python file as an ML Job.

    The file will be uploaded and executed on the specified compute pool.

    Args:
        file_path: Path to the Python file to run
        compute_pool: Name of compute pool to run on
        connection_name: Snowflake connection name (uses default if None)
        pip_requirements: List of pip packages to install (e.g., ["torch", "pandas"])
        args: Command line arguments to pass to the script
        stage_name: Stage to upload the file to
        external_access_integrations: EAIs for internet access
        wait: If True, wait for job completion
        timeout: Timeout in seconds when waiting
        verbose: Print progress messages

    Returns:
        Dict with job_id, status, and other metadata

    Example:
        result = submit_file(
            "train_model.py",
            compute_pool="GPU_POOL",
            pip_requirements=["torch", "transformers"],
            wait=True
        )
        print(f"Job {result['job_id']} completed with status: {result['status']}")
    """
    from snowflake.ml.jobs import submit_file as sf_submit_file

    file_path = Path(file_path)
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    session = get_session(connection_name)

    eais = external_access_integrations or ["ALLOW_ALL_INTEGRATION"]

    if verbose:
        console.print(f"[bold blue]Submitting ML Job[/]")
        console.print(f"  File: {file_path}")
        console.print(f"  Compute Pool: {compute_pool}")
        if pip_requirements:
            console.print(f"  Requirements: {', '.join(pip_requirements)}")

    job = sf_submit_file(
        str(file_path),
        compute_pool=compute_pool,
        stage_name=stage_name,
        session=session,
        pip_requirements=pip_requirements or [],
        external_access_integrations=eais,
        args=args or [],
    )

    if verbose:
        console.print(f"  Job ID: {job.id}")
        console.print(f"  Status: {job.status}")

    result = {
        "job_id": job.id,
        "status": str(job.status),
        "file": str(file_path),
        "compute_pool": compute_pool,
    }

    if wait:
        if verbose:
            console.print(f"[dim]Waiting for completion (timeout: {timeout}s)...[/]")

        job.wait(timeout=timeout)
        result["status"] = str(job.status)

        if verbose:
            console.print(f"[bold green]✓ Job complete: {job.status}[/]")

        try:
            job_result = job.result()
            if job_result:
                result["result"] = job_result
        except Exception:
            pass

    return result


def submit_directory(
    dir_path: str,
    entrypoint: str,
    compute_pool: str,
    connection_name: Optional[str] = None,
    pip_requirements: Optional[List[str]] = None,
    args: Optional[List[str]] = None,
    stage_name: str = "ML_JOBS_STAGE",
    target_instances: int = 1,
    external_access_integrations: Optional[List[str]] = None,
    wait: bool = False,
    timeout: int = 3600,
    verbose: bool = True,
    exclude_patterns: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """
    Submit a directory as an ML Job.

    The directory will be packaged and uploaded, then the entrypoint
    script will be executed on the compute pool.

    Args:
        dir_path: Path to the directory to upload
        entrypoint: Relative path to the main script within the directory
        compute_pool: Name of compute pool to run on
        connection_name: Snowflake connection name
        pip_requirements: List of pip packages to install
        args: Command line arguments to pass to the entrypoint
        stage_name: Stage to upload to
        target_instances: Number of Ray nodes to use
        external_access_integrations: EAIs for internet access
        wait: If True, wait for job completion
        timeout: Timeout in seconds when waiting
        verbose: Print progress messages
        exclude_patterns: Patterns to exclude from upload (e.g., ["__pycache__", "*.pyc"])

    Returns:
        Dict with job_id, status, and other metadata

    Example:
        result = submit_directory(
            "./my_project",
            entrypoint="train.py",
            compute_pool="GPU_POOL",
            pip_requirements=["torch", "sentence-transformers"],
            target_instances=2,
            wait=True
        )
    """
    from snowflake.ml.jobs import submit_directory as sf_submit_directory

    dir_path = Path(dir_path)
    if not dir_path.exists():
        raise FileNotFoundError(f"Directory not found: {dir_path}")

    session = get_session(connection_name)

    exclude = exclude_patterns or ["__pycache__", "*.pyc", ".pytest_cache", ".git"]
    eais = external_access_integrations or ["ALLOW_ALL_INTEGRATION"]

    if verbose:
        console.print(f"[bold blue]Submitting ML Job (directory)[/]")
        console.print(f"  Directory: {dir_path}")
        console.print(f"  Entrypoint: {entrypoint}")
        console.print(f"  Compute Pool: {compute_pool}")
        console.print(f"  Instances: {target_instances}")
        if pip_requirements:
            console.print(f"  Requirements: {', '.join(pip_requirements)}")

    with tempfile.TemporaryDirectory() as tmpdir:
        clean_dir = Path(tmpdir) / dir_path.name

        shutil.copytree(
            dir_path,
            clean_dir,
            ignore=shutil.ignore_patterns(*exclude)
        )

        job = sf_submit_directory(
            str(clean_dir),
            entrypoint=entrypoint,
            compute_pool=compute_pool,
            stage_name=stage_name,
            session=session,
            target_instances=target_instances,
            pip_requirements=pip_requirements or [],
            external_access_integrations=eais,
            args=args or [],
        )

    if verbose:
        console.print(f"  Job ID: {job.id}")
        console.print(f"  Status: {job.status}")

    result = {
        "job_id": job.id,
        "status": str(job.status),
        "directory": str(dir_path),
        "entrypoint": entrypoint,
        "compute_pool": compute_pool,
        "instances": target_instances,
    }

    if wait:
        if verbose:
            console.print(f"[dim]Waiting for completion (timeout: {timeout}s)...[/]")

        job.wait(timeout=timeout)
        result["status"] = str(job.status)

        if verbose:
            console.print(f"[bold green]✓ Job complete: {job.status}[/]")

        try:
            job_result = job.result()
            if job_result:
                result["result"] = job_result
        except Exception:
            pass

    return result
