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
