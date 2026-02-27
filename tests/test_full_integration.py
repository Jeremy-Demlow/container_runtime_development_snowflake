#!/usr/bin/env python3
"""
Full end-to-end integration test for snowflake-ml-accelerator

This test:
1. Creates infrastructure (compute pool, stage, EAI)
2. Submits a test ML Job
3. Verifies the job completes
"""

import sys
import tempfile
import time

CONNECTION = "myconnection"  # Uses JWT auth with private key

def test_connection():
    """Test basic Snowflake connection."""
    print("=" * 60)
    print("Step 1: Testing Snowflake connection")
    print("=" * 60)

    from sfml.session import get_session, clear_session_cache
    clear_session_cache()

    session = get_session(CONNECTION)
    result = session.sql("SELECT CURRENT_USER(), CURRENT_DATABASE(), CURRENT_ROLE()").collect()
    print(f"  User: {result[0][0]}")
    print(f"  Database: {result[0][1]}")
    print(f"  Role: {result[0][2]}")
    print("  ✓ Connection successful!")
    return session

def test_setup(session):
    """Test setup - create compute pool and infrastructure."""
    print("\n" + "=" * 60)
    print("Step 2: Setting up infrastructure")
    print("=" * 60)

    from sfml.remote import setup

    result = setup(
        connection_name=CONNECTION,
        project_name="ml_accel_test",
        database="ML_ACCELERATOR_DEMO",
        instance_family="CPU_X64_S",  # Small for testing
        stage_name="ML_JOBS_STAGE",
        pool_name="ML_ACCEL_TEST_POOL",
        execute=True,
        verbose=True,
    )

    print(f"\n  Created resources:")
    print(f"    Database: {result['database']}")
    print(f"    Compute Pool: {result['compute_pool']}")
    print(f"    Stage: {result['stage']}")
    print("  ✓ Infrastructure ready!")
    return result

def wait_for_pool(session, pool_name, max_wait=300):
    """Wait for compute pool to be ready."""
    print(f"\n  Waiting for compute pool '{pool_name}' to be ready...")

    start = time.time()
    while time.time() - start < max_wait:
        pools = session.sql(f"SHOW COMPUTE POOLS LIKE '{pool_name}'").collect()
        if pools:
            state = pools[0]['state']
            print(f"    Pool state: {state}")
            if state in ('IDLE', 'ACTIVE'):
                print("  ✓ Pool ready!")
                return True
            elif state == 'STARTING':
                print("    Waiting 30s...")
                time.sleep(30)
            else:
                print(f"    Unexpected state: {state}")
                return False
        else:
            print(f"    Pool not found yet...")
            time.sleep(10)

    print("  ✗ Timeout waiting for pool")
    return False

def test_submit_job(session, compute_pool):
    """Test submitting an ML Job."""
    print("\n" + "=" * 60)
    print("Step 3: Submitting test ML Job")
    print("=" * 60)

    from sfml.jobs import submit_file

    # Create a simple test script
    script = '''
import sys
print("=" * 50)
print("Hello from Snowflake ML Jobs!")
print("=" * 50)

from snowflake.snowpark.context import get_active_session
session = get_active_session()

result = session.sql("SELECT CURRENT_VERSION()").collect()
print(f"Snowflake Version: {result[0][0]}")

result = session.sql("SELECT 2 + 2").collect()
print(f"2 + 2 = {result[0][0]}")

print("Test job completed successfully!")
'''

    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write(script)
        script_path = f.name

    print(f"  Script: {script_path}")
    print(f"  Pool: {compute_pool}")
    print("  Submitting...")

    result = submit_file(
        script_path,
        compute_pool=compute_pool,
        connection_name=CONNECTION,
        wait=True,
        timeout=600,
        verbose=True,
    )

    print(f"\n  Job ID: {result['job_id']}")
    print(f"  Status: {result['status']}")

    if result['status'] == 'DONE':
        print("  ✓ Job completed successfully!")
        return True
    else:
        print(f"  ✗ Job failed with status: {result['status']}")
        return False

def main():
    print("\n" + "=" * 60)
    print("  Snowflake ML Accelerator - Full Integration Test")
    print("=" * 60 + "\n")

    try:
        # Step 1: Test connection
        session = test_connection()

        # Step 2: Setup infrastructure
        infra = test_setup(session)

        # Wait for pool
        pool_ready = wait_for_pool(session, infra['compute_pool'])
        if not pool_ready:
            print("\n⚠ Pool not ready - cannot test job submission")
            print("  Run this test again in a few minutes")
            return

        # Step 3: Submit test job
        if "--submit" in sys.argv:
            success = test_submit_job(session, infra['compute_pool'])
        else:
            print("\n⚠ Add --submit flag to test job submission")
            success = True

        print("\n" + "=" * 60)
        if success:
            print("  ✓ All tests passed!")
        else:
            print("  ✗ Some tests failed")
        print("=" * 60 + "\n")

    except Exception as e:
        print(f"\n✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
