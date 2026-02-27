"""
Example 4: Setup and Connect to Remote Dev

Shows the full workflow for setting up remote development.

Run:
    python examples/04_remote_dev_setup.py
"""

from sfml.remote import setup, generate_connect_script

CONNECTION_NAME = "default"
PROJECT_NAME = "ml_dev"

print("Setting up remote dev environment...")
print("=" * 50)

result = setup(
    connection_name=CONNECTION_NAME,
    project_name=PROJECT_NAME,
    database="ML_DEV",
    instance_family="CPU_X64_M",
    execute=True,
)

print("\n" + "=" * 50)
print("Generated resources:")
for key, value in result.items():
    if key != "sql":
        print(f"  {key}: {value}")

print("\n" + "=" * 50)
print("Generating connect script...")

script_path = generate_connect_script(
    connection_name=CONNECTION_NAME,
    project_name=PROJECT_NAME,
    output_path="./scripts/connect.sh",
)

print(f"\nTo connect to your remote environment:")
print(f"  ./scripts/connect.sh")
print(f"\nOr programmatically:")
print(f"  from sfml.remote import connect")
print(f"  connect('{CONNECTION_NAME}', '{PROJECT_NAME}')")
