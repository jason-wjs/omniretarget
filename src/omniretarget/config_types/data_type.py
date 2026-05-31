"""Configuration types for motion data format."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from omniretarget.specs.mappings import JOINTS_MAPPINGS
from omniretarget.specs.motion_formats import (
    DATA_FORMAT_CONSTANTS,
    DEMO_JOINTS_REGISTRY,
    LAFAN_DEMO_JOINTS,
    MOCAP_DEMO_JOINTS,
    OPTITRACK_DEMO_JOINTS,
    PARC_HUMANOID_DEMO_JOINTS,
    SMPLH_DEMO_JOINTS,
    SMPLX_DEMO_JOINTS,
    TOE_NAMES_BY_FORMAT,
    FormatConstants,
)

# Type alias for data formats - use str to allow dynamic data formats via DEMO_JOINTS_REGISTRY
# No need to update this when adding new formats - just add to DEMO_JOINTS_REGISTRY above
DataFormat = str


def _validate_data_format(data_format: str) -> None:
    """Validate that data_format exists in DEMO_JOINTS_REGISTRY."""
    if data_format not in DEMO_JOINTS_REGISTRY:
        available = ", ".join(sorted(DEMO_JOINTS_REGISTRY.keys()))
        raise ValueError(
            f"Invalid data_format: '{data_format}'. "
            f"Available formats: {available}. "
            f"Add your format to DEMO_JOINTS_REGISTRY in specs/motion_formats.py"
        )


@dataclass(frozen=True)
class MotionDataConfig:
    # Use str instead of Literal to allow dynamic data formats via DEMO_JOINTS_REGISTRY
    data_format: str = "smplh"
    # Use str instead of Literal to allow dynamic robot types
    robot_type: str = "g1"

    def __post_init__(self) -> None:
        """Validate data_format and robot_type."""
        _validate_data_format(self.data_format)
        from omniretarget.config_types.robot import _validate_robot_type

        _validate_robot_type(self.robot_type)

    # Optional overrides - if None, will use defaults from data_format
    demo_joints: list[str] | None = None
    joints_mapping: dict[str, str] | None = None

    @property
    def resolved_demo_joints(self) -> list[str]:
        """Get demo joints - use override if provided, else use data_format default."""
        if self.demo_joints is not None:
            return self.demo_joints

        if self.data_format not in DEMO_JOINTS_REGISTRY:
            raise ValueError(
                f"Unknown data_format: {self.data_format}. "
                f"Available formats: {list(DEMO_JOINTS_REGISTRY.keys())}. "
                f"Add your format to DEMO_JOINTS_REGISTRY in specs/motion_formats.py"
            )
        return DEMO_JOINTS_REGISTRY[self.data_format]

    @property
    def resolved_joints_mapping(self) -> dict[str, str]:
        """Get joints mapping - use override if provided, else lookup by (data_format, robot_type)."""
        if self.joints_mapping is not None:
            return self.joints_mapping

        key = (self.data_format, self.robot_type)
        if key in JOINTS_MAPPINGS:
            return JOINTS_MAPPINGS[key]

        raise ValueError(f"No joint mapping found for data_format={self.data_format}, robot_type={self.robot_type}")

    @property
    def toe_names(self) -> list[str]:
        """Get toe joint names for this data format."""
        if self.data_format not in TOE_NAMES_BY_FORMAT:
            raise ValueError(
                f"Toe names not defined for data_format: {self.data_format}. "
                f"Add entry to TOE_NAMES_BY_FORMAT in specs/motion_formats.py"
            )
        return TOE_NAMES_BY_FORMAT[self.data_format]

    @property
    def default_scale_factor(self) -> float | None:
        """Get default scale factor for this data format (None if calculated per subject)."""
        format_constants: FormatConstants = DATA_FORMAT_CONSTANTS.get(self.data_format, {})
        return format_constants.get("default_scale_factor")

    @property
    def default_human_height(self) -> float | None:
        """Get default human height for this data format (None if not applicable)."""
        format_constants: FormatConstants = DATA_FORMAT_CONSTANTS.get(self.data_format, {})
        return format_constants.get("default_human_height")

    def legacy_constants(self) -> dict[str, Any]:
        """Return uppercase legacy constants for backward compatibility."""
        return {
            "DEMO_JOINTS": self.resolved_demo_joints,
            "JOINTS_MAPPING": self.resolved_joints_mapping,
            "TOE_NAMES": self.toe_names,
            "DEFAULT_SCALE_FACTOR": self.default_scale_factor,
            "DEFAULT_HUMAN_HEIGHT": self.default_human_height,
        }
