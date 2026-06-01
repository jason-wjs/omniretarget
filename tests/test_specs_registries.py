from __future__ import annotations

import numpy as np
import pytest

from omniretarget.config_types.data_type import MotionDataConfig
from omniretarget.config_types.robot import RobotConfig
from omniretarget.specs.mappings import JOINTS_MAPPINGS
from omniretarget.specs.motion_formats import DATA_FORMAT_CONSTANTS, DEMO_JOINTS_REGISTRY, TOE_NAMES_BY_FORMAT
from omniretarget.specs.robots import ROBOT_DEFAULTS


@pytest.mark.parametrize("robot_type", ["g1", "t1", "adam_pro"])
def test_robot_config_matches_robot_specs(robot_type: str) -> None:
    cfg = RobotConfig(robot_type=robot_type)
    spec = ROBOT_DEFAULTS[robot_type]

    assert cfg.ROBOT_DOF == spec["robot_dof"]
    assert cfg.ROBOT_HEIGHT == spec["robot_height"]
    assert cfg.ROBOT_NAME == f"{robot_type}_{spec['robot_dof']}dof"
    assert cfg.ROBOT_URDF_FILE.endswith(f"models/{robot_type}/{robot_type}_{spec['robot_dof']}dof.urdf")
    assert isinstance(cfg.FOOT_STICKING_LINKS, list)
    assert isinstance(cfg.MANUAL_LB, dict)
    assert isinstance(cfg.MANUAL_UB, dict)
    assert isinstance(cfg.MANUAL_COST, dict)
    assert isinstance(cfg.NOMINAL_TRACKING_INDICES, np.ndarray)


@pytest.mark.parametrize(
    ("data_format", "robot_type"),
    [
        ("lafan", "g1"),
        ("smplh", "g1"),
        ("smplx", "g1"),
        ("mocap", "g1"),
        ("optitrack", "g1"),
        ("parc_humanoid", "g1"),
    ],
)
def test_motion_data_config_matches_motion_specs(data_format: str, robot_type: str) -> None:
    cfg = MotionDataConfig(data_format=data_format, robot_type=robot_type)

    assert cfg.resolved_demo_joints == DEMO_JOINTS_REGISTRY[data_format]
    assert cfg.resolved_joints_mapping == JOINTS_MAPPINGS[(data_format, robot_type)]
    assert cfg.toe_names == TOE_NAMES_BY_FORMAT[data_format]
    assert cfg.default_scale_factor == DATA_FORMAT_CONSTANTS.get(data_format, {}).get("default_scale_factor")
    assert cfg.default_human_height == DATA_FORMAT_CONSTANTS.get(data_format, {}).get("default_human_height")
