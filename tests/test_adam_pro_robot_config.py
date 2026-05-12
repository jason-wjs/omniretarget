from pathlib import Path

import numpy as np
from omniretarget.config_types.robot import RobotConfig


def test_adam_pro_defaults_registered() -> None:
    cfg = RobotConfig(robot_type="adam_pro")
    from omniretarget.path_utils import package_path

    assert cfg.ROBOT_DOF == 29
    assert cfg.ROBOT_NAME == "adam_pro_29dof"
    assert Path(cfg.ROBOT_URDF_FILE) == package_path("models/adam_pro/adam_pro_29dof.urdf")


def test_adam_pro_has_foot_links_for_sticking() -> None:
    cfg = RobotConfig(robot_type="adam_pro")
    assert len(cfg.FOOT_STICKING_LINKS) == 8
    assert "left_foot_sphere_1_link" in cfg.FOOT_STICKING_LINKS
    assert "right_foot_sphere_4_link" in cfg.FOOT_STICKING_LINKS


def test_adam_pro_nominal_tracking_and_waist_manual_priors() -> None:
    cfg = RobotConfig(robot_type="adam_pro")
    np.testing.assert_array_equal(cfg.NOMINAL_TRACKING_INDICES, np.arange(15))
    assert cfg.MANUAL_LB["19"] == -0.18
    assert cfg.MANUAL_LB["20"] == -0.35
    assert cfg.MANUAL_LB["21"] == -0.829
    assert cfg.MANUAL_LB["10"] == 0.12
    assert cfg.MANUAL_LB["16"] == 0.12
    assert cfg.MANUAL_UB["19"] == 0.18
    assert cfg.MANUAL_UB["20"] == 0.75
    assert cfg.MANUAL_UB["21"] == 0.829
    assert cfg.MANUAL_COST == {
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

    # Shoulder moderation (not too strict, but avoids extreme rotation)
    assert cfg.MANUAL_LB["22"] == -2.8
    assert cfg.MANUAL_UB["22"] == 1.8
    assert cfg.MANUAL_LB["23"] == -0.5
    assert cfg.MANUAL_UB["23"] == 2.4
    assert cfg.MANUAL_LB["24"] == -2.0
    assert cfg.MANUAL_UB["24"] == 2.0
    assert cfg.MANUAL_LB["29"] == -2.8
    assert cfg.MANUAL_UB["29"] == 1.8
    assert cfg.MANUAL_LB["30"] == -2.4
    assert cfg.MANUAL_UB["30"] == 0.5
    assert cfg.MANUAL_LB["31"] == -2.0
    assert cfg.MANUAL_UB["31"] == 2.0

    # Elbow anti-hyperextension
    assert cfg.MANUAL_LB["25"] == -2.496
    assert cfg.MANUAL_UB["25"] == -0.1
    assert cfg.MANUAL_LB["32"] == -2.496
    assert cfg.MANUAL_UB["32"] == -0.1

    # Wrist motion limits (yaw/pitch/roll) on both sides
    assert cfg.MANUAL_LB["26"] == -0.6
    assert cfg.MANUAL_UB["26"] == 0.6
    assert cfg.MANUAL_LB["27"] == -0.45
    assert cfg.MANUAL_UB["27"] == 0.45
    assert cfg.MANUAL_LB["28"] == -0.45
    assert cfg.MANUAL_UB["28"] == 0.45
    assert cfg.MANUAL_LB["33"] == -0.6
    assert cfg.MANUAL_UB["33"] == 0.6
    assert cfg.MANUAL_LB["34"] == -0.45
    assert cfg.MANUAL_UB["34"] == 0.45
    assert cfg.MANUAL_LB["35"] == -0.45
    assert cfg.MANUAL_UB["35"] == 0.45
