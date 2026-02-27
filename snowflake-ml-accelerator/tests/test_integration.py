#!/usr/bin/env python3
"""Integration test for snowflake-ml-accelerator"""

import sys
import tempfile
from pathlib import Path

def test_imports():
    print("1. Testing imports...")
    from sfml import setup, submit_file, submit_directory, get_session
    from sfml.config import Config
    print("   ✓ All imports work")

def test_config():
    print("\n2. Testing config...")
    from sfml.config import Config
    cfg = Config.load()
    print(f"   ✓ Config loads: connection={cfg.connection_name}")
    print(f"   ✓ Project: {cfg.project.name}, Database: {cfg.project.database}")

def test_connection():
    print("\n3. Testing Snowflake connection...")
    from sfml.session import get_session, clear_session_cache
    clear_session_cache()

    session = get_session("snowhouse")
    result = session.sql("SELECT CURRENT_USER(), CURRENT_DATABASE(), CURRENT_ROLE()").collect()
    print(f"   ✓ Connected as: {result[0][0]}")
    print(f"   ✓ Database: {result[0][1]}")
    print(f"   ✓ Role: {result[0][2]}")
    return session

def test_compute_pools(session):
    print("\n4. Checking compute pools...")
    pools = session.sql("SHOW COMPUTE POOLS").collect()
    print(f"   Found {len(pools)} compute pools:")
    for p in pools[:5]:
        print(f"   - {p['name']}: {p['state']}")
    return len(pools) > 0

def test_submit_file(session):
    print("\n5. Testing submit_file...")
    from sfml.jobs import submit_file

    script = '''
from snowflake.snowpark.context import get_active_session
session = get_active_session()
print("Hello from ML Jobs!")
result = session.sql("SELECT 1+1").collect()
print(f"Result: {result[0][0]}")
'''

    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write(script)
        script_path = f.name

    print(f"   Submitting: {script_path}")

    try:
        result = submit_file(
            script_path,
            compute_pool="SYSTEM_COMPUTE_POOL_CPU",
            connection_name="snowhouse",
            wait=True,
            timeout=300,
            verbose=True,
        )
        print(f"   ✓ Job ID: {result['job_id']}")
        print(f"   ✓ Status: {result['status']}")
        return True
    except Exception as e:
        print(f"   ✗ Error: {e}")
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("Snowflake ML Accelerator - Integration Test")
    print("=" * 60)

    try:
        test_imports()
        test_config()
        session = test_connection()
        has_pools = test_compute_pools(session)

        if has_pools and "--submit" in sys.argv:
            test_submit_file(session)
        elif not has_pools:
            print("\n⚠ No compute pools found - skipping job submission test")
        else:
            print("\n⚠ Add --submit flag to test job submission")

        print("\n" + "=" * 60)
        print("✓ All basic tests passed!")
        print("=" * 60)
    except Exception as e:
        print(f"\n✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
