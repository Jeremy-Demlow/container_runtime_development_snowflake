# 🚀 Snowflake ML Accelerator

**Develop and scale ML on Snowflake in minutes, not days.**

Two powerful capabilities in one package:
- **🖥️ Remote Dev** — Code in VS Code/Cursor connected directly to Snowflake containers with GPU access
- **⚡ ML Jobs** — Submit Python scripts to run on Snowflake compute pools with one line of code

---

## 📦 Installation

```bash
# Clone the repo
git clone https://github.com/your-org/snowflake-ml-accelerator.git
cd snowflake-ml-accelerator

# Install (includes all dependencies)
pip install -e .
```

That's it! This installs:
- Snowflake CLI with remote dev support
- Snowflake ML Python SDK
- All required dependencies

---

## ⚙️ Configuration

### 1. Create Snowflake Connection

Add to `~/.snowflake/config.toml`:

```toml
[connections.myconnection]
account = "YOUR_ACCOUNT"           # e.g., "abc12345.us-west-2"
user = "YOUR_USER"
role = "ACCOUNTADMIN"              # Or role with compute pool access
warehouse = "COMPUTE_WH"
database = "ML_ACCELERATOR"

# Choose ONE authentication method:

# Option A: Password
password = "YOUR_PASSWORD"

# Option B: Key-pair (recommended)
authenticator = "SNOWFLAKE_JWT"
private_key_path = "~/.snowflake/keys/rsa_key.p8"

# Option C: SSO
authenticator = "externalbrowser"
```

### 2. Set Up Infrastructure (First Time Only)

```python
from sfml import setup

setup(
    connection_name="myconnection",
    instance_family="CPU_X64_M",    # Or "GPU_NV_S" for GPU
)
```

This creates:
- `ML_ACCELERATOR` database
- `ML_ACCELERATOR_POOL` compute pool
- `DEV_STAGE` for code sync
- `ML_JOBS_STAGE` for job payloads
- Network rules for internet access

---

## 🖥️ Remote Development

Connect VS Code or Cursor directly to a Snowflake container:

```python
from sfml import connect

# Open Cursor connected to CPU pool
connect(connection_name="myconnection")

# Open VS Code connected to GPU pool
connect(connection_name="myconnection", compute_pool="GPU_DEV_POOL", editor="code")
```

### From Command Line

```bash
# Default (Cursor + ML_ACCELERATOR_POOL)
python -m sfml.remote.connect -c myconnection

# VS Code + GPU
python -m sfml.remote.connect -c myconnection --pool GPU_DEV_POOL --editor code
```

### What You Get

Once connected, you're inside a Snowflake container with:
- Full Python environment
- GPU access (if using GPU pool)
- Pre-installed ML libraries
- Your code synced to a Snowflake stage
- Internet access for pip install

---

## ⚡ ML Jobs

Submit Python scripts to run on Snowflake compute:

### Submit a Single File

```python
from sfml import submit_file

result = submit_file(
    "train.py",
    compute_pool="ML_ACCELERATOR_POOL",
    connection_name="myconnection",
    pip_requirements=["torch", "transformers"],
    wait=True,  # Wait for completion
)

print(f"Job {result['job_id']}: {result['status']}")
```

### Submit a Directory

```python
from sfml import submit_directory

result = submit_directory(
    "./my_project",
    entrypoint="train.py",
    compute_pool="GPU_DEV_POOL",
    connection_name="myconnection",
    pip_requirements=["torch", "sentence-transformers"],
    target_instances=2,  # Multi-node for distributed training
    wait=True,
)
```

### From Command Line

```bash
# Submit a file
python -c "from sfml import submit_file; submit_file('train.py', 'ML_ACCELERATOR_POOL', wait=True)"
```

---

## 🔧 Compute Pool Options

| Pool Type | Instance Family | Resources | Use Case |
|-----------|----------------|-----------|----------|
| CPU Small | `CPU_X64_S` | 2 vCPU, 8GB RAM | Testing, light work |
| CPU Medium | `CPU_X64_M` | 4 vCPU, 32GB RAM | Development, data prep |
| CPU Large | `CPU_X64_L` | 8 vCPU, 64GB RAM | Heavy processing |
| GPU Small | `GPU_NV_S` | 1 GPU (24GB), 8 vCPU | ML training, inference |
| GPU Medium | `GPU_NV_M` | 4 GPU (96GB), 44 vCPU | Large models, multi-GPU |

---

## 📁 Project Structure

```
snowflake-ml-accelerator/
├── src/sfml/
│   ├── __init__.py          # Main exports
│   ├── session.py           # Snowflake session management
│   ├── remote/
│   │   ├── setup.py         # Infrastructure creation
│   │   ├── connect.py       # Remote dev connection
│   │   └── teardown.py      # Cleanup
│   └── jobs/
│       └── submit.py        # ML Job submission
├── pyproject.toml           # Package config
└── README.md
```

---

## 🔐 Security

This repo includes pre-commit hooks to prevent accidentally committing secrets:

```bash
# Install pre-commit hooks
pip install pre-commit
pre-commit install
```

**Never commit:**
- `.snowflake/config.toml` with passwords
- Private keys (`.p8`, `.pem`)
- API tokens or credentials

---

## 🛠️ Troubleshooting

### "Compute pool not found"

```bash
# Check available pools
snow sql -q "SHOW COMPUTE POOLS" -c myconnection
```

### "Connection failed"

```bash
# Test connection
snow sql -q "SELECT CURRENT_USER()" -c myconnection
```

### "Editor not found in PATH"

The package auto-detects VS Code and Cursor on macOS. If issues persist:
- VS Code: Open app → Cmd+Shift+P → "Shell Command: Install 'code' command"
- Cursor: Open app → Cmd+Shift+P → "Shell Command: Install 'cursor' command"

### Remote dev service stuck

```bash
# Check status
snow remote list -c myconnection

# Delete and recreate
snow remote delete SNOW_REMOTE_YOUR_USER_DEV -c myconnection
```

---

## 📚 API Reference

### `setup()`
```python
setup(
    connection_name: str,           # Required: connection from config.toml
    project_name: str = "ml_accelerator",
    database: str = "ML_ACCELERATOR",
    instance_family: str = "CPU_X64_M",
    stage_name: str = "DEV_STAGE",
    pool_name: str = None,          # Auto-generated if None
    eai_name: str = "ALLOW_ALL_INTEGRATION",
    min_nodes: int = 1,
    max_nodes: int = 1,
)
```

### `connect()`
```python
connect(
    name: str = "dev",              # Environment name
    compute_pool: str = "ML_ACCELERATOR_POOL",
    stage: str = "@ML_ACCELERATOR.PUBLIC.DEV_STAGE",
    eai: str = "ALLOW_ALL_INTEGRATION",
    connection_name: str = None,
    editor: str = "cursor",         # "cursor" or "code"
)
```

### `submit_file()`
```python
submit_file(
    file_path: str,                 # Required: path to Python file
    compute_pool: str,              # Required: pool name
    connection_name: str = None,
    pip_requirements: List[str] = None,
    args: List[str] = None,
    stage_name: str = "ML_JOBS_STAGE",
    external_access_integrations: List[str] = None,
    wait: bool = False,
    timeout: int = 3600,
)
```

### `submit_directory()`
```python
submit_directory(
    dir_path: str,                  # Required: directory path
    entrypoint: str,                # Required: main script (relative path)
    compute_pool: str,              # Required: pool name
    connection_name: str = None,
    pip_requirements: List[str] = None,
    target_instances: int = 1,      # Number of nodes
    wait: bool = False,
    timeout: int = 3600,
)
```

---

## 🎯 Quick Start Checklist

- [ ] Clone repo and `pip install -e .`
- [ ] Create connection in `~/.snowflake/config.toml`
- [ ] Run `setup(connection_name="myconnection")`
- [ ] Wait 2-3 min for compute pool to start
- [ ] Run `connect(connection_name="myconnection")` to develop
- [ ] Use `submit_file()` to scale out training

---

## 📄 License

MIT License - See LICENSE file for details.

---

**Questions?** Open an issue or reach out to your Snowflake account team.
