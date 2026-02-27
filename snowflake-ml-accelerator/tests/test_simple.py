#!/usr/bin/env python3
"""
Simple end-to-end test for snowflake-ml-accelerator
Tests ML Job submission using existing infrastructure.
"""

import sys
import tempfile
import time

CONNECTION = "myconnection"
DATABASE = "ML_ACCELERATOR"
COMPUTE_POOL = "ML_COMPUTE_POOL"
STAGE = "ML_JOBS_STAGE"

def test_connection():
    """Test Snowflake connection."""
    print("=" * 60)
    print("Step 1: Testing connection")
    print("=" * 60)

    from sfml.session import get_session, clear_session_cache
    clear_session_cache()

    session = get_session(CONNECTION)
    result = session.sql("SELECT CURRENT_USER(), CURRENT_ROLE()").collect()
    print(f"  User: {result[0][0]}, Role: {result[0][1]}")
    print("  ✓ Connected!")
    return session

def wait_for_pool(session, pool_name, max_wait=120):
    """Wait for compute pool."""
    print(f"\n  Waiting for pool '{pool_name}'...")
    start = time.time()
    while time.time() - start < max_wait:
        pools = session.sql(f"SHOW COMPUTE POOLS LIKE '{pool_name}'").collect()
        if pools:
            state = pools[0]['state']
            print(f"    State: {state}")
            if state in ('IDLE', 'ACTIVE'):
                return True
            time.sleep(15)
        else:
            time.sleep(5)
    return False

def test_submit_job(session):
    """Test submitting an ML Job."""
    print("\n" + "=" * 60)
    print("Step 2: Submitting test ML Job")
    print("=" * 60)

    from sfml.jobs import submit_file

    script = '''
import sys
print("=" * 50)
print("Hello from Snowflake ML Jobs!")
print("=" * 50)
print(f"Python: {sys.version}")

from snowflake.snowpark.context import get_active_session
session = get_active_session()
result = session.sql("SELECT CURRENT_VERSION()").collect()
print(f"Snowflake: {result[0][0]}")
print("SUCCESS!")
'''

    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write(script)
        script_path = f.name

    print(f"  Script: {script_path}")
    print(f"  Pool: {COMPUTE_POOL}")
    print("  Submitting...")

    result = submit_file(
        script_path,
        compute_pool=COMPUTE_POOL,
        connection_name=CONNECTION,
        stage_name=f"{DATABASE}.PUBLIC.{STAGE}",
        wait=True,
        timeout=300,
        verbose=True,
    )

    print(f"\n  Job ID: {result['job_id']}")
    print(f"  Status: {result['status']}")
    return result['status'] == 'DONE'

def main():
    print("\n  Snowflake ML Accelerator - Integration Test\n")

    try:
        session = test_connection()

        if not wait_for_pool(session, COMPUTE_POOL):
            print("  ✗ Pool not ready")
            return

        success = test_submit_job(session)

        print("\n" + "=" * 60)
        print("  ✓ SUCCESS!" if success else "  ✗ FAILED")
        print("=" * 60 + "\n")

    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
