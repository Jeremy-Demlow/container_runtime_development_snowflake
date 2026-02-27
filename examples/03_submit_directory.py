"""
Example 3: Submit a Directory as ML Job

Shows how to submit a multi-file project.

Run:
    python examples/03_submit_directory.py
"""

import tempfile
import os
from pathlib import Path
from sfml.jobs import submit_directory

project_dir = Path(tempfile.mkdtemp())

(project_dir / "utils.py").write_text('''
def greet(name):
    return f"Hello, {name}!"

def compute_stats(data):
    return {
        "count": len(data),
        "sum": sum(data),
        "mean": sum(data) / len(data) if data else 0,
    }
''')

(project_dir / "main.py").write_text('''
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from utils import greet, compute_stats
from snowflake.snowpark.context import get_active_session

session = get_active_session()
print(greet("Snowflake"))

data = [1, 2, 3, 4, 5, 10, 20, 30]
stats = compute_stats(data)
print(f"Stats: {stats}")

result = session.sql("SELECT CURRENT_USER()").collect()
print(f"Running as: {result[0][0]}")

print("\\nDirectory job complete!")
''')

print(f"Created project at: {project_dir}")
print(f"  - main.py (entrypoint)")
print(f"  - utils.py (helper module)")
print()

result = submit_directory(
    str(project_dir),
    entrypoint="main.py",
    compute_pool="ml_dev_pool",
    wait=True,
)

print(f"\nJob ID: {result['job_id']}")
print(f"Status: {result['status']}")

import shutil
shutil.rmtree(project_dir)
