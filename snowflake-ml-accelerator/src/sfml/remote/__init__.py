"""
Remote development module for Snowflake ML Accelerator.

Provides functions to set up and connect to remote dev environments
in Snowflake Container Services.
"""

from sfml.remote.setup import setup
from sfml.remote.connect import connect
from sfml.remote.disconnect import disconnect, list_services
from sfml.remote.teardown import teardown

__all__ = ["setup", "connect", "disconnect", "list_services", "teardown"]
