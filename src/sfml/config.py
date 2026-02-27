"""
Configuration management for Snowflake ML Accelerator.

Loads settings from YAML config files.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml


@dataclass
class ComputeConfig:
    pool_name: str = "ml_dev_pool"
    instance_family: str = "CPU_X64_M"
    min_nodes: int = 1
    max_nodes: int = 1


@dataclass
class StorageConfig:
    stage_name: str = "DEV_STAGE"
    encryption: str = "SNOWFLAKE_SSE"


@dataclass
class NetworkConfig:
    eai_name: str = "ALLOW_ALL_INTEGRATION"
    allow_ports: List[int] = field(default_factory=lambda: [443, 80])


@dataclass
class ProjectConfig:
    name: str = "ml_dev"
    database: str = "ML_DEV"


@dataclass
class Config:
    """Main configuration for Snowflake ML Accelerator."""

    connection_name: str = "default"
    project: ProjectConfig = field(default_factory=ProjectConfig)
    compute: ComputeConfig = field(default_factory=ComputeConfig)
    storage: StorageConfig = field(default_factory=StorageConfig)
    network: NetworkConfig = field(default_factory=NetworkConfig)

    @classmethod
    def load(cls, config_path: Optional[str] = None) -> "Config":
        """
        Load configuration from YAML file.

        Args:
            config_path: Path to config file. If None, searches for:
                        1. config/config.yaml
                        2. config/default.yaml

        Returns:
            Config instance
        """
        if config_path:
            path = Path(config_path)
        else:
            base = Path(__file__).parent.parent.parent.parent
            user_config = base / "config" / "config.yaml"
            default_config = base / "config" / "default.yaml"

            path = user_config if user_config.exists() else default_config

        if not path.exists():
            return cls()

        with open(path) as f:
            data = yaml.safe_load(f) or {}

        return cls.from_dict(data)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Config":
        """Create Config from dictionary."""
        project_data = data.get("project", {})
        compute_data = data.get("compute", {})
        storage_data = data.get("storage", {})
        network_data = data.get("network", {})

        return cls(
            connection_name=data.get("connection_name", "default"),
            project=ProjectConfig(**project_data) if project_data else ProjectConfig(),
            compute=ComputeConfig(**compute_data) if compute_data else ComputeConfig(),
            storage=StorageConfig(**storage_data) if storage_data else StorageConfig(),
            network=NetworkConfig(**network_data) if network_data else NetworkConfig(),
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "connection_name": self.connection_name,
            "project": {"name": self.project.name, "database": self.project.database},
            "compute": {
                "pool_name": self.compute.pool_name,
                "instance_family": self.compute.instance_family,
                "min_nodes": self.compute.min_nodes,
                "max_nodes": self.compute.max_nodes,
            },
            "storage": {
                "stage_name": self.storage.stage_name,
                "encryption": self.storage.encryption,
            },
            "network": {
                "eai_name": self.network.eai_name,
                "allow_ports": self.network.allow_ports,
            },
        }
