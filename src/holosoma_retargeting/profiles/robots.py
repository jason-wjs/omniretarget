"""Built-in robot profile defaults."""

from __future__ import annotations

from typing import TypedDict


class RobotDefaults(TypedDict):
    robot_dof: int
    robot_height: float
    object_name: str


ROBOT_DEFAULTS: dict[str, RobotDefaults] = {
    "g1": {"robot_dof": 29, "robot_height": 1.32, "object_name": "ground"},
    "t1": {"robot_dof": 23, "robot_height": 1.2, "object_name": "ground"},
    "adam_pro": {"robot_dof": 29, "robot_height": 1.67, "object_name": "ground"},
}

FOOT_STICKING_LINKS_BY_ROBOT: dict[str, tuple[str, ...]] = {
    "g1": (
        "left_ankle_roll_sphere_1_link",
        "right_ankle_roll_sphere_1_link",
        "left_ankle_roll_sphere_2_link",
        "right_ankle_roll_sphere_2_link",
        "left_ankle_roll_sphere_3_link",
        "right_ankle_roll_sphere_3_link",
        "left_ankle_roll_sphere_4_link",
        "right_ankle_roll_sphere_4_link",
    ),
    "t1": (
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
    ),
    "adam_pro": (
        # Use foot patch markers (1..4) for sticking; keep sphere_5 as toe target for retargeting mapping.
        "left_foot_sphere_1_link",
        "right_foot_sphere_1_link",
        "left_foot_sphere_2_link",
        "right_foot_sphere_2_link",
        "left_foot_sphere_3_link",
        "right_foot_sphere_3_link",
        "left_foot_sphere_4_link",
        "right_foot_sphere_4_link",
    ),
}

# qpos indices for Adam Pro:
#   left knee: 10, right knee: 16
#   waist: 19=waistRoll, 20=waistPitch, 21=waistYaw
#   left arm: 22/23/24=shoulder pitch/roll/yaw, 25=elbow, 26/27/28=wrist yaw/pitch/roll
#   right arm: 29/30/31=shoulder pitch/roll/yaw, 32=elbow, 33/34/35=wrist yaw/pitch/roll
MANUAL_LB_BY_ROBOT: dict[str, dict[str, float]] = {
    "g1": {
        "20": -0.3,  # waist roll
        "21": -0.1,  # waist pitch
        "26": -0.1,  # right wrist
        "27": -0.1,
        "28": -0.05,
        "33": -0.1,  # left wrist
        "34": -0.1,
        "35": -0.05,
    },
    "adam_pro": {
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
    },
}

MANUAL_UB_BY_ROBOT: dict[str, dict[str, float]] = {
    "g1": {
        "20": 0.3,  # waist roll
        "25": 1.4,  # right elbow
        "26": 0.2,  # right wrist
        "27": 0.3,
        "28": 0.05,
        "32": 1.4,  # elbow
        "33": 0.2,  # left wrist
        "34": 0.3,
        "35": 0.05,
    },
    "adam_pro": {
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
    },
}

MANUAL_COST_BY_ROBOT: dict[str, dict[str, float]] = {
    "g1": {"19": 0.2, "20": 0.2},  # waist yaw, waist roll
    "adam_pro": {
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
    },
}

NOMINAL_TRACKING_INDICES_BY_ROBOT: dict[str, tuple[int, ...]] = {
    "g1": tuple(range(19)),
    "t1": (*range(7), *range(11, 23)),
    # Lower-body (0..11) + waist (12..14).
    "adam_pro": tuple(range(15)),
}

__all__ = [
    "RobotDefaults",
    "ROBOT_DEFAULTS",
    "FOOT_STICKING_LINKS_BY_ROBOT",
    "MANUAL_LB_BY_ROBOT",
    "MANUAL_UB_BY_ROBOT",
    "MANUAL_COST_BY_ROBOT",
    "NOMINAL_TRACKING_INDICES_BY_ROBOT",
]
