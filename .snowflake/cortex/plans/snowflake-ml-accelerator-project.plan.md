---
name: "snowflake-ml-accelerator-project"
created: "2026-02-27T03:52:02.260Z"
status: pending
---

# Plan: snowflake-ml-accelerator Project

## Overview

Create a new, customer-ready Python package called `snowflake-ml-accelerator` that provides:

1. **Remote Development Setup** - Easy compute pool + container service creation for interactive development inside Snowflake
2. **ML Jobs Submission** - Simple API to submit Python files/directories to Snowflake ML Jobs
3. **UV-based Installation** - Modern, fast dependency management using `uv`

This will be used for tomorrow's customer presentation to enable them to:

- Develop interactively inside a Snowflake container (VS Code/Cursor)
- Scale out compute by submitting ML Jobs from their code

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    snowflake-ml-accelerator                             │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ┌─────────────────────────────┐    ┌─────────────────────────────────┐ │
│  │   Remote Dev Module         │    │   ML Jobs Module                │ │
│  │                             │    │                                 │ │
│  │  • setup()                  │    │  • submit_file()                │ │
│  │  • connect()                │    │  • submit_directory()           │ │
│  │  • teardown()               │    │  • get_job_status()             │ │
│  │                             │    │  • list_jobs()                  │ │
│  │  Creates:                   │    │                                 │ │
│  │  - Compute Pool             │    │  Uses:                          │ │
│  │  - Stage                    │    │  - snowflake.ml.jobs API        │ │
│  │  - Network Rules            │    │  - Ray on SPCS                  │ │
│  │  - Container Service        │    │                                 │ │
│  └─────────────────────────────┘    └─────────────────────────────────┘ │
│                                                                         │
│  ┌─────────────────────────────────────────────────────────────────────┐│
│  │   Examples & Quick Start                                            ││
│  │   • notebooks/getting_started.ipynb                                 ││
│  │   • examples/submit_simple_job.py                                   ││
│  │   • examples/gpu_matching_pipeline.py                               ││
│  └─────────────────────────────────────────────────────────────────────┘│
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
                           │
                           │ Customer uses
                           ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                        Snowflake                                        │
│                                                                         │
│   ┌──────────────────┐          ┌──────────────────────────────────┐   │
│   │  Container        │          │  ML Jobs Compute Pool            │   │
│   │  Runtime Service  │          │  (GPU or CPU)                    │   │
│   │                   │          │                                  │   │
│   │  • VS Code/Cursor │          │  • Ray workers                   │   │
│   │  • Jupyter        │          │  • PyTorch/GPU                   │   │
│   │  • SSH access     │          │  • Distributed execution         │   │
│   └──────────────────┘          └──────────────────────────────────┘   │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## Task 1: Create Project Structure and pyproject.toml with UV

### Directory Structure

```
snowflake-ml-accelerator/
├── pyproject.toml              # UV/pip compatible, modern Python packaging
├── README.md                   # Getting started guide
├── Makefile                    # Quick commands
├── .gitignore                  # Python + Snowflake ignores
│
├── src/
│   └── sfml/                   # Main package (short name)
│       ├── __init__.py         # Exports: setup, connect, submit_file, submit_directory
│       ├── remote/             # Remote dev module
│       │   ├── __init__.py
│       │   ├── setup.py        # Compute pool, stage, EAI creation
│       │   ├── connect.py      # SSH tunnel, Cursor/VS Code launch
│       │   └── teardown.py     # Cleanup resources
│       ├── jobs/               # ML Jobs module
│       │   ├── __init__.py
│       │   ├── submit.py       # submit_file(), submit_directory()
│       │   └── status.py       # get_status(), list_jobs()
│       ├── session.py          # Snowflake connection helper
│       └── config.py           # YAML config loading
│
├── config/
│   ├── default.yaml            # Default settings
│   └── config.yaml.template    # User template
│
├── examples/
│   ├── 01_hello_world.py       # Simplest ML Job
│   ├── 02_gpu_embedding.py     # GPU embedding example
│   └── 03_distributed_job.py   # Multi-node Ray job
│
├── notebooks/
│   └── getting_started.ipynb   # Interactive tutorial
│
└── scripts/
    ├── setup.sh                # One-liner setup
    └── connect.sh              # Generated connection script
```

### pyproject.toml (UV Compatible)

```
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "snowflake-ml-accelerator"
version = "0.1.0"
description = "Rapid ML development and scaling on Snowflake"
readme = "README.md"
requires-python = ">=3.9"
dependencies = [
    "snowflake-snowpark-python>=1.11.0",
    "snowflake-ml-python>=1.8.0",
    "pyyaml>=6.0",
    "rich>=13.0.0",
]

[project.optional-dependencies]
dev = ["pytest", "ruff"]
gpu = ["torch>=2.0.0", "sentence-transformers>=2.2.0"]

[tool.hatch.build.targets.wheel]
packages = ["src/sfml"]
```

---

## Task 2: Build Remote Dev Infrastructure Module

Port and simplify the logic from 01\_clean\_demo/setup.py.

### Key Functions

**`sfml/remote/setup.py`**:

```
def setup(
    connection_name: str,
    project_name: str = "ml_dev",
    database: str = "ML_DEV",
    instance_family: str = "CPU_X64_M",  # or GPU_NV_S, GPU_NV_M
    stage_name: str = "DEV_STAGE",
) -> dict:
    """
    Create all infrastructure for remote development.
    
    Creates:
    - Database (if not exists)
    - Compute Pool
    - Stage for persistent storage
    - Network rules for internet access
    - External Access Integration
    
    Returns dict with created resource names.
    """
```

**`sfml/remote/connect.py`**:

```
def connect(
    connection_name: str,
    project_name: str,
    compute_pool: str,
    stage: str,
    eai_name: str = "ALLOW_ALL_INTEGRATION",
    ide: str = "cursor",  # or "vscode"
) -> None:
    """
    Connect to remote dev environment.
    
    Uses snow remote CLI to:
    1. Create/resume container service
    2. Set up SSH tunnel
    3. Launch IDE connected to container
    """
```

### SQL Generation

Generate SQL similar to 01\_clean\_demo/generated\_setup.sql:

```
-- Create Database
CREATE DATABASE IF NOT EXISTS ML_DEV;

-- Create Compute Pool
CREATE COMPUTE POOL IF NOT EXISTS ml_dev_pool
  MIN_NODES = 1
  MAX_NODES = 1
  INSTANCE_FAMILY = CPU_X64_M;

-- Create Stage
CREATE STAGE IF NOT EXISTS ML_DEV.PUBLIC.DEV_STAGE
  ENCRYPTION = (TYPE = 'SNOWFLAKE_SSE');

-- Create Network Rule + EAI
CREATE OR REPLACE NETWORK RULE ALLOW_ALL_INTEGRATION_rule
  MODE = EGRESS
  TYPE = HOST_PORT
  VALUE_LIST = ('0.0.0.0:443', '0.0.0.0:80');

CREATE OR REPLACE EXTERNAL ACCESS INTEGRATION ALLOW_ALL_INTEGRATION
  ALLOWED_NETWORK_RULES = (ALLOW_ALL_INTEGRATION_rule)
  ENABLED = true;
```

---

## Task 3: Create ML Jobs Submission Module

Port and simplify from snowmatch/runners/ml\_jobs.py.

### Key Functions

**`sfml/jobs/submit.py`**:

```
def submit_file(
    file_path: str,
    compute_pool: str,
    connection_name: str = None,
    pip_requirements: list[str] = None,
    args: list[str] = None,
    gpu: bool = False,
    wait: bool = False,
) -> dict:
    """
    Submit a single Python file as an ML Job.
    
    Example:
        result = submit_file(
            "my_script.py",
            compute_pool="GPU_POOL",
            pip_requirements=["torch", "transformers"],
            wait=True
        )
    """

def submit_directory(
    dir_path: str,
    entrypoint: str,
    compute_pool: str,
    stage_name: str = "ML_JOBS_STAGE",
    connection_name: str = None,
    pip_requirements: list[str] = None,
    args: list[str] = None,
    target_instances: int = 1,
    external_access_integrations: list[str] = None,
    wait: bool = False,
) -> dict:
    """
    Submit a directory as an ML Job.
    
    Example:
        result = submit_directory(
            "./my_project",
            entrypoint="main.py",
            compute_pool="GPU_POOL",
            pip_requirements=["torch"],
            wait=True
        )
    """
```

### Implementation Pattern

Based on existing code in ml\_jobs.py:264-410:

```
from snowflake.ml.jobs import submit_directory as sf_submit_directory, submit_file as sf_submit_file

def submit_file(file_path, compute_pool, **kwargs):
    job = sf_submit_file(
        file_path,
        compute_pool=compute_pool,
        pip_requirements=kwargs.get("pip_requirements", []),
        args=kwargs.get("args", []),
        session=_get_session(kwargs.get("connection_name")),
    )
    
    if kwargs.get("wait"):
        job.wait(timeout=kwargs.get("timeout", 3600))
    
    return {"job_id": job.id, "status": job.status}
```

---

## Task 4: Create Getting Started Examples and README

### README.md Structure

````
# Snowflake ML Accelerator

Develop locally or remotely. Scale to GPUs with one command.

## Quick Start (5 minutes)

### 1. Install
​```bash
uv pip install snowflake-ml-accelerator
# or
pip install snowflake-ml-accelerator
​```

### 2. Configure
​```bash
cp config/config.yaml.template config/config.yaml
# Edit with your Snowflake connection
​```

### 3. Setup Remote Dev Environment
​```python
from sfml.remote import setup, connect

# Create compute pool and infrastructure
setup(connection_name="my_connection", project_name="ml_dev")

# Connect to remote VS Code/Cursor
connect(connection_name="my_connection", project_name="ml_dev")
​```

### 4. Submit ML Jobs
​```python
from sfml.jobs import submit_file, submit_directory

# Submit a single file
result = submit_file(
    "my_gpu_script.py",
    compute_pool="GPU_POOL",
    wait=True
)

# Submit a directory
result = submit_directory(
    "./my_project",
    entrypoint="main.py",
    compute_pool="GPU_POOL"
)
​```

## Two Workflows

### Workflow 1: Interactive Development (Remote Dev)
- Code in VS Code/Cursor connected to Snowflake container
- Full GPU access
- Snowpark session auto-available
- Files persist on Snowflake stage

### Workflow 2: Scale Out (ML Jobs)
- Submit Python files/directories
- Auto-scales to multiple nodes
- Ray for distributed compute
- No container management needed
````

### Example: examples/01\_hello\_world.py

```
"""
Simplest ML Job example.

Run:
    python examples/01_hello_world.py
"""
from sfml.jobs import submit_file
from sfml.session import get_session

# Create a simple script
script = '''
import os
from snowflake.snowpark.context import get_active_session

session = get_active_session()
result = session.sql("SELECT CURRENT_VERSION()").collect()
print(f"Running on Snowflake: {result[0][0]}")
'''

# Write to temp file
with open("/tmp/hello.py", "w") as f:
    f.write(script)

# Submit as ML Job
result = submit_file(
    "/tmp/hello.py",
    compute_pool="SYSTEM_COMPUTE_POOL",
    wait=True
)

print(f"Job completed: {result['status']}")
```

### Example: examples/02\_gpu\_embedding.py

```
"""
GPU embedding job using sentence-transformers.
"""
from sfml.jobs import submit_directory
import tempfile
import shutil

# Create job directory
job_dir = tempfile.mkdtemp()

# Main script
main_script = '''
import torch
from sentence_transformers import SentenceTransformer
from snowflake.snowpark.context import get_active_session

session = get_active_session()
print(f"GPU available: {torch.cuda.is_available()}")

# Load model
model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
if torch.cuda.is_available():
    model = model.to("cuda")

# Sample embeddings
texts = ["Hello world", "ML on Snowflake", "GPU acceleration"]
embeddings = model.encode(texts)
print(f"Embedded {len(texts)} texts, shape: {embeddings.shape}")
'''

with open(f"{job_dir}/main.py", "w") as f:
    f.write(main_script)

# Submit
result = submit_directory(
    job_dir,
    entrypoint="main.py",
    compute_pool="GPU_POOL",
    pip_requirements=["torch", "sentence-transformers"],
    wait=True
)

print(f"Job completed: {result['status']}")
shutil.rmtree(job_dir)
```

---

## Task 5: Build Makefile and Quick-Start Scripts

### Makefile

```
.PHONY: install setup connect submit clean help

# Default connection (override with: make setup CONNECTION=my_conn)
CONNECTION ?= default
PROJECT ?= ml_dev
POOL ?= ml_dev_pool
INSTANCE ?= CPU_X64_M

help:
    @echo "Snowflake ML Accelerator"
    @echo ""
    @echo "Setup:"
    @echo "  make install          Install package with uv"
    @echo "  make setup            Create compute pool and infrastructure"
    @echo "  make connect          Connect to remote dev environment"
    @echo ""
    @echo "ML Jobs:"
    @echo "  make submit FILE=x.py Submit a Python file as ML Job"
    @echo "  make submit-dir DIR=x Submit a directory as ML Job"
    @echo ""
    @echo "Options:"
    @echo "  CONNECTION=name       Snowflake connection name"
    @echo "  PROJECT=name          Project name (default: ml_dev)"
    @echo "  INSTANCE=family       Instance family (default: CPU_X64_M)"
    @echo "                        Options: CPU_X64_S, CPU_X64_M, GPU_NV_S, GPU_NV_M"

install:
    uv pip install -e .

setup:
    python -c "from sfml.remote import setup; setup('', '', instance_family='')"

connect:
    python -c "from sfml.remote import connect; connect('', '')"

submit:
    python -c "from sfml.jobs import submit_file; print(submit_file('', '', wait=True))"

submit-dir:
    python -c "from sfml.jobs import submit_directory; print(submit_directory('', 'main.py', '', wait=True))"

clean:
    python -c "from sfml.remote import teardown; teardown('', '')"
```

### scripts/setup.sh

```
#!/bin/bash
# One-liner setup for customers
set -e

echo "🚀 Snowflake ML Accelerator Setup"
echo "================================="

# Check for uv
if ! command -v uv &> /dev/null; then
    echo "Installing uv..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
fi

# Install package
echo "Installing package..."
uv pip install -e .

# Copy config template if needed
if [ ! -f config/config.yaml ]; then
    cp config/config.yaml.template config/config.yaml
    echo "Created config/config.yaml - please edit with your settings"
fi

echo ""
echo "✅ Setup complete!"
echo ""
echo "Next steps:"
echo "  1. Edit config/config.yaml with your Snowflake connection"
echo "  2. Run: make setup"
echo "  3. Run: make connect"
```

---

## Implementation Order

1. **Task 1** (30 min): Create directory structure and pyproject.toml
2. **Task 2** (45 min): Port remote dev module from 01\_clean\_demo
3. **Task 3** (45 min): Port ML Jobs module from snowmatch
4. **Task 4** (30 min): Create examples and README
5. **Task 5** (15 min): Create Makefile and scripts

**Total estimated time: \~2.5 hours**

---

## Files to Create

| File                              | Description       | Source                                        |
| --------------------------------- | ----------------- | --------------------------------------------- |
| `pyproject.toml`                  | Package config    | New                                           |
| `README.md`                       | Documentation     | New                                           |
| `Makefile`                        | Quick commands    | New                                           |
| `src/sfml/__init__.py`            | Package exports   | New                                           |
| `src/sfml/remote/setup.py`        | Infra creation    | Based on 01\_clean\_demo/setup.py             |
| `src/sfml/remote/connect.py`      | IDE connection    | Based on 01\_clean\_demo/connect.sh           |
| `src/sfml/jobs/submit.py`         | Job submission    | Based on snowmatch/runners/ml\_jobs.py        |
| `src/sfml/session.py`             | Connection helper | Based on snowmatch/session.py                 |
| `config/config.yaml.template`     | Config template   | Based on 01\_clean\_demo/config.yaml.template |
| `examples/*.py`                   | Usage examples    | New                                           |
| `notebooks/getting_started.ipynb` | Tutorial          | New                                           |

---

## Success Criteria

For tomorrow's customer presentation:

1. Customer can run `make install` to get the package
2. Customer can run `make setup` to create compute resources
3. Customer can run `make connect` to open VS Code/Cursor in Snowflake
4. Customer can write Python code and submit as ML Job with `submit_file()` or `submit_directory()`
5. All code is documented and easy to understand
