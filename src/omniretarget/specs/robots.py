from __future__ import annotations

from typing import TypedDict

import numpy as np


class RobotDefaults(TypedDict):
    robot_dof: int
    robot_height: float
    object_name: str


ROBOT_DEFAULTS: dict[str, RobotDefaults] = {
    "g1": {"robot_dof": 29, "robot_height": 1.32, "object_name": "ground"},
    "t1": {"robot_dof": 23, "robot_height": 1.2, "object_name": "ground"},
    "adam_pro": {"robot_dof": 29, "robot_height": 1.67, "object_name": "ground"},
}


def validate_robot_type(robot_type: str) -> None:
    """Validate that robot_type exists in ROBOT_DEFAULTS."""
    if robot_type not in ROBOT_DEFAULTS:
        available = ", ".join(sorted(ROBOT_DEFAULTS.keys()))
        raise ValueError(
            f"Invalid robot_type: '{robot_type}'. "
            f"Available robot types: {available}. "
            f"Add your robot to ROBOT_DEFAULTS in specs/robots.py"
        )


def foot_sticking_links(robot_type: str) -> list[str]:
    """Return default foot-sticking links for a robot type."""
    if robot_type == "g1":
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
    if robot_type == "t1":
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
    if robot_type == "adam_pro":
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
    raise ValueError(f"Invalid robot type: {robot_type}")


def manual_lb(robot_type: str) -> dict[str, float]:
    """Return default manual lower bounds for a robot type."""
    base: dict[str, float] = {"3": -1.0, "4": -1.0, "5": -1.0, "6": -1.0}

    if robot_type == "g1":
        base.update(
            {
                "20": -0.3,
                "21": -0.1,
                "26": -0.1,
                "27": -0.1,
                "28": -0.05,
                "33": -0.1,
                "34": -0.1,
                "35": -0.05,
            }
        )
    elif robot_type == "adam_pro":
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


def manual_ub(robot_type: str) -> dict[str, float]:
    """Return default manual upper bounds for a robot type."""
    base: dict[str, float] = {"3": 1.0, "4": 1.0, "5": 1.0, "6": 1.0}

    if robot_type == "g1":
        base.update(
            {
                "20": 0.3,
                "25": 1.4,
                "26": 0.2,
                "27": 0.3,
                "28": 0.05,
                "32": 1.4,
                "33": 0.2,
                "34": 0.3,
                "35": 0.05,
            }
        )
    elif robot_type == "adam_pro":
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


def manual_cost(robot_type: str) -> dict[str, float]:
    """Return default manual cost weights for a robot type."""
    if robot_type == "g1":
        return {"19": 0.2, "20": 0.2}
    if robot_type == "adam_pro":
        return {
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


def nominal_tracking_indices(robot_type: str) -> np.ndarray:
    """Return default nominal tracking indices for a robot type."""
    if robot_type == "g1":
        return np.arange(19)
    if robot_type == "t1":
        return np.concatenate([np.arange(7), np.arange(11, 23)])
    if robot_type == "adam_pro":
        return np.arange(15)
    return np.array([], dtype=int)
