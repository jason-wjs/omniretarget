from __future__ import annotations

from omniretarget.config_types.data_type import DEMO_JOINTS_REGISTRY
from omniretarget.config_types.retargeting import RetargetingConfig


def validate_retargeting_config(cfg: RetargetingConfig) -> None:
    """Validate retargeting config compatibility rules used by the CLI adapter."""
    if cfg.data_format is not None and cfg.data_format not in DEMO_JOINTS_REGISTRY:
        available = ", ".join(sorted(DEMO_JOINTS_REGISTRY.keys()))
        raise ValueError(
            f"Unknown data_format: '{cfg.data_format}'. "
            f"Available formats: {available}. "
            f"Add your format to DEMO_JOINTS_REGISTRY in config_types/data_type.py"
        )

    if cfg.task_type == "climbing" and cfg.data_format not in (None, "mocap", "parc_humanoid"):
        raise ValueError("Climbing task requires 'mocap' or 'parc_humanoid' data format")
    if cfg.task_type == "object_interaction" and cfg.data_format not in (None, "smplh"):
        raise ValueError("Object interaction requires 'smplh' data format")
