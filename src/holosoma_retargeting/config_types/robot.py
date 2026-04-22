"""Configuration types for robot retargeting."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TypedDict

import numpy as np

from holosoma_retargeting.path_utils import package_path


# Default values per robot type
class RobotDefaults(TypedDict):
    robot_dof: int
    robot_height: float
    object_name: str


_ROBOT_DEFAULTS: dict[str, RobotDefaults] = {
    "g1": {"robot_dof": 29, "robot_height": 1.32, "object_name": "ground"},
    "t1": {"robot_dof": 23, "robot_height": 1.2, "object_name": "ground"},
    "adam_pro": {"robot_dof": 29, "robot_height": 1.67, "object_name": "ground"},
}


def _validate_robot_type(robot_type: str) -> None:
    """Validate that robot_type exists in _ROBOT_DEFAULTS."""
    if robot_type not in _ROBOT_DEFAULTS:
        available = ", ".join(sorted(_ROBOT_DEFAULTS.keys()))
        raise ValueError(
            f"Invalid robot_type: '{robot_type}'. "
            f"Available robot types: {available}. "
            f"Add your robot to _ROBOT_DEFAULTS in config_types/robot.py"
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

    # Robot type selector - determines which defaults to use
    # Use str instead of Literal to allow dynamic robot types via _ROBOT_DEFAULTS
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

        if self.robot_type == "g1":
            return [
                "left_ankle_roll_sphere_1_link",
                "right_ankle_roll_sphere_1_link",
                "left_ankle_roll_sphere_2_link",
                "right_ankle_roll_sphere_2_link",
                "left_ankle_roll_sphere_3_link",
                "right_ankle_roll_sphere_3_link",
                "left_ankle_roll_sphere_4_link",
                "right_ankle_roll_sphere_4_link",
            ]
        if self.robot_type == "t1":
            return [
                "left_foot_sphere_1_link",
                "right_foot_sphere_1_link",
                "left_foot_sphere_2_link",
                "right_foot_sphere_2_link",
                "left_foot_sphere_3_link",
                "right_foot_sphere_3_link",
                "left_foot_sphere_4_link",
                "right_foot_sphere_4_link",
                "left_foot_sphere_5_link",
                "right_foot_sphere_5_link",
            ]
        if self.robot_type == "adam_pro":
            # Use foot patch markers (1..4) for sticking; keep sphere_5 as toe target for retargeting mapping.
            return [
                "left_foot_sphere_1_link",
                "right_foot_sphere_1_link",
                "left_foot_sphere_2_link",
                "right_foot_sphere_2_link",
                "left_foot_sphere_3_link",
                "right_foot_sphere_3_link",
                "left_foot_sphere_4_link",
                "right_foot_sphere_4_link",
            ]
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

        if self.robot_type == "g1":
            base.update(
                {
                    "20": -0.3,  # waist roll
                    "21": -0.1,  # waist pitch
                    "26": -0.1,  # right wrist
                    "27": -0.1,
                    "28": -0.05,
                    "33": -0.1,  # left wrist
                    "34": -0.1,
                    "35": -0.05,
                }
            )
        elif self.robot_type == "adam_pro":
            # qpos indices:
            #   left knee: 10, right knee: 16
            #   waist: 19=waistRoll, 20=waistPitch, 21=waistYaw
            #   left arm: 22/23/24=shoulder pitch/roll/yaw, 25=elbow, 26/27/28=wrist yaw/pitch/roll
            #   right arm: 29/30/31=shoulder pitch/roll/yaw, 32=elbow, 33/34/35=wrist yaw/pitch/roll
            base.update(
                {
                    "10": 0.12,
                    "16": 0.12,
                    "19": -0.18,
                    "20": -0.35,
                    "21": -0.829,
                    "22": -2.8,
                    "23": -0.5,
                    "24": -2.0,
                    "25": -2.496,
                    "26": -0.6,
                    "27": -0.45,
                    "28": -0.45,
                    "29": -2.8,
                    "30": -2.4,
                    "31": -2.0,
                    "32": -2.496,
                    "33": -0.6,
                    "34": -0.45,
                    "35": -0.45,
                }
            )

        return base

    MANUAL_LB = property(_manual_lb, doc="Get manual lower bounds.")

    def _manual_ub(self) -> dict[str, float]:
        """Get manual upper bounds."""
        if self.manual_ub is not None:
            return self.manual_ub

        base: dict[str, float] = {"3": 1.0, "4": 1.0, "5": 1.0, "6": 1.0}  # quaternion bounds

        if self.robot_type == "g1":
            base.update(
                {
                    "20": 0.3,  # waist roll
                    "25": 1.4,  # right elbow
                    "26": 0.2,  # right wrist
                    "27": 0.3,
                    "28": 0.05,
                    "32": 1.4,  # elbow
                    "33": 0.2,  # left wrist
                    "34": 0.3,
                    "35": 0.05,
                }
            )
        elif self.robot_type == "adam_pro":
            # qpos indices:
            #   waist: 19=waistRoll, 20=waistPitch, 21=waistYaw
            #   left arm: 22/23/24=shoulder pitch/roll/yaw, 25=elbow, 26/27/28=wrist yaw/pitch/roll
            #   right arm: 29/30/31=shoulder pitch/roll/yaw, 32=elbow, 33/34/35=wrist yaw/pitch/roll
            base.update(
                {
                    "19": 0.18,
                    "20": 0.75,
                    "21": 0.829,
                    "22": 1.8,
                    "23": 2.4,
                    "24": 2.0,
                    "25": -0.1,
                    "26": 0.6,
                    "27": 0.45,
                    "28": 0.45,
                    "29": 1.8,
                    "30": 0.5,
                    "31": 2.0,
                    "32": -0.1,
                    "33": 0.6,
                    "34": 0.45,
                    "35": 0.45,
                }
            )

        return base

    MANUAL_UB = property(_manual_ub, doc="Get manual upper bounds.")

    def _manual_cost(self) -> dict[str, float]:
        """Get manual cost weights."""
        if self.manual_cost is not None:
            return self.manual_cost

        if self.robot_type == "g1":
            return {"19": 0.2, "20": 0.2}  # waist yaw, waist roll
        if self.robot_type == "adam_pro":
            # qpos indices:
            #   left knee: 10, right knee: 16
            #   waist: 19=waistRoll, 20=waistPitch, 21=waistYaw
            #   left arm: 22/23/24=shoulder pitch/roll/yaw, 25=elbow
            #   right arm: 29/30/31=shoulder pitch/roll/yaw, 32=elbow
            return {
                # Keep these low: MANUAL_COST biases joints toward 0 rad;
                # lower bounds above are the primary anti-hyperextension safeguard.
                "10": 0.03,
                "16": 0.03,
                "19": 0.2,
                "20": 0.2,
                "21": 0.2,
                "22": 0.05,
                "23": 0.05,
                "24": 0.05,
                "25": 0.1,
                "29": 0.05,
                "30": 0.05,
                "31": 0.05,
                "32": 0.1,
            }
        return {}

    MANUAL_COST = property(_manual_cost, doc="Get manual cost weights.")

    def _nominal_tracking_indices(self) -> np.ndarray:
        """Get nominal tracking indices."""
        if self.nominal_tracking_indices is not None:
            return self.nominal_tracking_indices

        if self.robot_type == "g1":
            return np.arange(19)
        if self.robot_type == "t1":
            return np.concatenate([np.arange(7), np.arange(11, 23)])
        if self.robot_type == "adam_pro":
            # Lower-body (0..11) + waist (12..14).
            return np.arange(15)
        # Default: return empty array if robot type not defined (nominal tracking not used)
        return np.array([], dtype=int)

    NOMINAL_TRACKING_INDICES = property(
        _nominal_tracking_indices,
        doc="Get nominal tracking indices.",
    )
