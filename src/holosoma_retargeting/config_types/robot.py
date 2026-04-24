"""Configuration types for robot retargeting."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from holosoma_retargeting.path_utils import package_path
from holosoma_retargeting.profiles.robots import (
    FOOT_STICKING_LINKS_BY_ROBOT as _FOOT_STICKING_LINKS_BY_ROBOT,
    MANUAL_COST_BY_ROBOT as _MANUAL_COST_BY_ROBOT,
    MANUAL_LB_BY_ROBOT as _MANUAL_LB_BY_ROBOT,
    MANUAL_UB_BY_ROBOT as _MANUAL_UB_BY_ROBOT,
    NOMINAL_TRACKING_INDICES_BY_ROBOT as _NOMINAL_TRACKING_INDICES_BY_ROBOT,
    ROBOT_DEFAULTS as _ROBOT_DEFAULTS,
    RobotDefaults,
)


def _validate_robot_type(robot_type: str) -> None:
    """Validate that robot_type exists in the built-in robot profiles."""
    if robot_type not in _ROBOT_DEFAULTS:
        available = ", ".join(sorted(_ROBOT_DEFAULTS.keys()))
        raise ValueError(
            f"Invalid robot_type: '{robot_type}'. "
            f"Available robot types: {available}. "
            f"Add your robot to ROBOT_DEFAULTS in profiles/robots.py"
        )


@dataclass(frozen=True)
class RobotConfig:
    """Unified configuration for all robot constants (G1, T1) using tyro.

    Example usage:
        # From CLI:
        config = tyro.cli(RobotConfig)  # --robot-type g1 --robot-dof 30

        # With defaults:
        config = RobotConfig(robot_type="g1")

        # Access values:
        robot_dof = config.ROBOT_DOF
        robot_height = config.ROBOT_HEIGHT
    """

    # Robot type selector - determines which profile defaults to use
    # Use str instead of Literal to allow dynamic robot types via profiles.robots.ROBOT_DEFAULTS
    robot_type: str = "g1"

    def __post_init__(self) -> None:
        """Validate robot_type after initialization."""
        _validate_robot_type(self.robot_type)

    # Robot configuration (optional overrides)
    robot_dof: int | None = None
    robot_height: float | None = None
    robot_name: str | None = None
    robot_urdf_file: str | None = None

    # Joint definitions (optional overrides)
    foot_sticking_links: list[str] | None = None

    # Manual joint limits
    manual_lb: dict[str, float] | None = None
    manual_ub: dict[str, float] | None = None
    manual_cost: dict[str, float] | None = None

    # Nominal tracking indices
    nominal_tracking_indices: np.ndarray | None = None

    # Basic robot properties
    def _robot_dof(self) -> int:
        """Get robot DOF - use override if provided, else use robot_type default."""
        if self.robot_dof is not None:
            return self.robot_dof
        return _ROBOT_DEFAULTS[self.robot_type]["robot_dof"]

    ROBOT_DOF = property(
        _robot_dof,
        doc="Get robot DOF - use override if provided, else use robot_type default.",
    )

    def _robot_height(self) -> float:
        """Get robot height - use override if provided, else use robot_type default."""
        if self.robot_height is not None:
            return self.robot_height
        return _ROBOT_DEFAULTS[self.robot_type]["robot_height"]

    ROBOT_HEIGHT = property(
        _robot_height,
        doc="Get robot height - use override if provided, else use robot_type default.",
    )

    def _robot_name(self) -> str:
        """Get robot name - use override if provided, else compute from robot_type and DOF."""
        if self.robot_name is not None:
            return self.robot_name
        return f"{self.robot_type}_{self.ROBOT_DOF}dof"

    ROBOT_NAME = property(
        _robot_name,
        doc="Get robot name - use override if provided, else compute from robot_type and DOF.",
    )

    def _robot_urdf_file(self) -> str:
        """Get robot URDF file path."""
        if self.robot_urdf_file is not None:
            return self.robot_urdf_file
        return str(package_path(f"models/{self.robot_type}/{self.robot_type}_{self.ROBOT_DOF}dof.urdf"))

    ROBOT_URDF_FILE = property(_robot_urdf_file, doc="Get robot URDF file path.")

    def _foot_sticking_links(self) -> list[str]:
        """Get foot sticking links - use override if provided, else use robot_type default."""
        if self.foot_sticking_links is not None:
            return self.foot_sticking_links

        if self.robot_type in _FOOT_STICKING_LINKS_BY_ROBOT:
            return list(_FOOT_STICKING_LINKS_BY_ROBOT[self.robot_type])
        raise ValueError(f"Invalid robot type: {self.robot_type}")

    FOOT_STICKING_LINKS = property(
        _foot_sticking_links,
        doc="Get foot sticking links - use override if provided, else use robot_type default.",
    )

    def _manual_lb(self) -> dict[str, float]:
        """Get manual lower bounds."""
        if self.manual_lb is not None:
            return self.manual_lb

        base: dict[str, float] = {"3": -1.0, "4": -1.0, "5": -1.0, "6": -1.0}  # quaternion bounds
        base.update(_MANUAL_LB_BY_ROBOT.get(self.robot_type, {}))
        return base

    MANUAL_LB = property(_manual_lb, doc="Get manual lower bounds.")

    def _manual_ub(self) -> dict[str, float]:
        """Get manual upper bounds."""
        if self.manual_ub is not None:
            return self.manual_ub

        base: dict[str, float] = {"3": 1.0, "4": 1.0, "5": 1.0, "6": 1.0}  # quaternion bounds
        base.update(_MANUAL_UB_BY_ROBOT.get(self.robot_type, {}))
        return base

    MANUAL_UB = property(_manual_ub, doc="Get manual upper bounds.")

    def _manual_cost(self) -> dict[str, float]:
        """Get manual cost weights."""
        if self.manual_cost is not None:
            return self.manual_cost

        return dict(_MANUAL_COST_BY_ROBOT.get(self.robot_type, {}))

    MANUAL_COST = property(_manual_cost, doc="Get manual cost weights.")

    def _nominal_tracking_indices(self) -> np.ndarray:
        """Get nominal tracking indices."""
        if self.nominal_tracking_indices is not None:
            return self.nominal_tracking_indices

        if self.robot_type in _NOMINAL_TRACKING_INDICES_BY_ROBOT:
            return np.array(_NOMINAL_TRACKING_INDICES_BY_ROBOT[self.robot_type], dtype=int)
        # Default: return empty array if robot type not defined (nominal tracking not used)
        return np.array([], dtype=int)

    NOMINAL_TRACKING_INDICES = property(
        _nominal_tracking_indices,
        doc="Get nominal tracking indices.",
    )
