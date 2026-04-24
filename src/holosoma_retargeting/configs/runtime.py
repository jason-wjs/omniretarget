"""Runtime resolution for CLI config selections.

Tyro exposes both top-level selectors (for example ``robot`` and
``data_format``) and nested config objects. Command modules resolve task
defaults first, then use these helpers to align nested runtime config objects.
"""

from __future__ import annotations

from dataclasses import replace
from typing import TypeVar

from holosoma_retargeting.configs.motion import MotionDataConfig
from holosoma_retargeting.configs.retargeting import RetargetingConfig
from holosoma_retargeting.configs.robot import RobotConfig

_RetargetingConfigT = TypeVar("_RetargetingConfigT", bound=RetargetingConfig)


def resolve_robot_config(robot: str, robot_config: RobotConfig) -> RobotConfig:
    """Return a robot config aligned with the top-level robot selector."""
    if robot_config.robot_type == robot:
        return robot_config
    return RobotConfig(robot_type=robot)


def resolve_motion_data_config(
    robot: str,
    data_format: str,
    motion_data_config: MotionDataConfig,
) -> MotionDataConfig:
    """Return a motion config aligned with top-level robot and data format."""
    if motion_data_config.robot_type == robot and motion_data_config.data_format == data_format:
        return motion_data_config
    return MotionDataConfig(data_format=data_format, robot_type=robot)


def resolve_robot_and_motion_configs(
    *,
    robot: str,
    data_format: str,
    robot_config: RobotConfig,
    motion_data_config: MotionDataConfig,
) -> tuple[RobotConfig, MotionDataConfig]:
    """Resolve nested robot and motion configs without mutating a parent config."""
    return (
        resolve_robot_config(robot, robot_config),
        resolve_motion_data_config(robot, data_format, motion_data_config),
    )


def resolve_retargeting_config(
    cfg: _RetargetingConfigT,
    data_format: str | None = None,
) -> _RetargetingConfigT:
    """Return ``cfg`` with nested configs aligned to resolved runtime selectors."""
    resolved_data_format = data_format if data_format is not None else cfg.data_format
    if resolved_data_format is None:
        raise ValueError("data_format must be resolved before runtime config synchronization")

    robot_config, motion_data_config = resolve_robot_and_motion_configs(
        robot=cfg.robot,
        data_format=resolved_data_format,
        robot_config=cfg.robot_config,
        motion_data_config=cfg.motion_data_config,
    )
    if robot_config is cfg.robot_config and motion_data_config is cfg.motion_data_config:
        return cfg
    return replace(cfg, robot_config=robot_config, motion_data_config=motion_data_config)
