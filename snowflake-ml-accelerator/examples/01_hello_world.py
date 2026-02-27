"""
Example 1: Hello World ML Job

The simplest possible ML Job - just prints Snowflake version.

Run:
    python examples/01_hello_world.py
"""

import tempfile
from sfml.jobs import submit_file

script_content = '''
from snowflake.snowpark.context import get_active_session

session = get_active_session()
print(f"Connected to database: {session.get_current_database()}")

result = session.sql("SELECT CURRENT_VERSION()").collect()
print(f"Snowflake version: {result[0][0]}")

print("Hello from Snowflake ML Jobs!")
'''

with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
    f.write(script_content)
    script_path = f.name

print("Submitting hello world job...")
result = submit_file(
    script_path,
    compute_pool="ml_dev_pool",
    wait=True,
)

print(f"\nJob ID: {result['job_id']}")
print(f"Status: {result['status']}")
