import numpy as np
import pytest

from holosoma_retargeting.config_types import data_type as config_data_type
from holosoma_retargeting.config_types.data_type import MotionDataConfig
from holosoma_retargeting.config_types import robot as config_robot
from holosoma_retargeting.config_types.robot import RobotConfig
from holosoma_retargeting.profiles.mappings import JOINTS_MAPPINGS
from holosoma_retargeting.profiles.motions import DEMO_JOINTS_REGISTRY
from holosoma_retargeting.profiles import mappings as profile_mappings
from holosoma_retargeting.profiles import motions as profile_motions
from holosoma_retargeting.profiles import robots as profile_robots
from holosoma_retargeting.profiles.robots import ROBOT_DEFAULTS


def test_profiles_expose_existing_robot_and_motion_defaults() -> None:
    assert "adam_pro" in ROBOT_DEFAULTS
    assert "optitrack" in DEMO_JOINTS_REGISTRY
    assert ("optitrack", "adam_pro") in JOINTS_MAPPINGS


def test_config_types_motion_imports_alias_profile_objects() -> None:
    assert config_data_type.LAFAN_DEMO_JOINTS is profile_motions.LAFAN_DEMO_JOINTS
    assert config_data_type.SMPLH_DEMO_JOINTS is profile_motions.SMPLH_DEMO_JOINTS
    assert config_data_type.MOCAP_DEMO_JOINTS is profile_motions.MOCAP_DEMO_JOINTS
    assert config_data_type.OPTITRACK_DEMO_JOINTS is profile_motions.OPTITRACK_DEMO_JOINTS
    assert config_data_type.SMPLX_DEMO_JOINTS is profile_motions.SMPLX_DEMO_JOINTS
    assert config_data_type.DEMO_JOINTS_REGISTRY is profile_motions.DEMO_JOINTS_REGISTRY
    assert config_data_type.TOE_NAMES_BY_FORMAT is profile_motions.TOE_NAMES_BY_FORMAT
    assert config_data_type.DATA_FORMAT_CONSTANTS is profile_motions.DATA_FORMAT_CONSTANTS
    assert config_data_type.JOINTS_MAPPINGS is profile_mappings.JOINTS_MAPPINGS


def test_config_types_robot_defaults_alias_profile_object() -> None:
    assert config_robot._ROBOT_DEFAULTS is profile_robots.ROBOT_DEFAULTS
    assert config_robot._FOOT_STICKING_LINKS_BY_ROBOT is profile_robots.FOOT_STICKING_LINKS_BY_ROBOT
    assert config_robot._MANUAL_LB_BY_ROBOT is profile_robots.MANUAL_LB_BY_ROBOT
    assert config_robot._MANUAL_UB_BY_ROBOT is profile_robots.MANUAL_UB_BY_ROBOT
    assert config_robot._MANUAL_COST_BY_ROBOT is profile_robots.MANUAL_COST_BY_ROBOT
    assert config_robot._NOMINAL_TRACKING_INDICES_BY_ROBOT is profile_robots.NOMINAL_TRACKING_INDICES_BY_ROBOT


def test_robot_profile_defaults_preserve_mutable_return_semantics() -> None:
    g1 = RobotConfig(robot_type="g1")
    assert g1.FOOT_STICKING_LINKS == list(profile_robots.FOOT_STICKING_LINKS_BY_ROBOT["g1"])
    assert g1.MANUAL_LB["3"] == -1.0
    assert g1.MANUAL_LB["20"] == -0.3
    assert g1.MANUAL_UB["25"] == 1.4
    assert g1.MANUAL_COST == {"19": 0.2, "20": 0.2}

    t1 = RobotConfig(robot_type="t1")
    assert t1.MANUAL_LB == {"3": -1.0, "4": -1.0, "5": -1.0, "6": -1.0}
    assert t1.MANUAL_UB == {"3": 1.0, "4": 1.0, "5": 1.0, "6": 1.0}
    assert t1.MANUAL_COST == {}
    assert t1.NOMINAL_TRACKING_INDICES.tolist() == [*range(7), *range(11, 23)]

    assert g1.MANUAL_LB is not g1.MANUAL_LB
    assert g1.FOOT_STICKING_LINKS is not g1.FOOT_STICKING_LINKS
    assert g1.NOMINAL_TRACKING_INDICES is not g1.NOMINAL_TRACKING_INDICES

    manual_lb_override = {"7": -0.5}
    manual_ub_override = {"7": 0.5}
    manual_cost_override = {"7": 0.1}
    nominal_override = np.array([1, 2, 3])
    cfg = RobotConfig(
        robot_type="g1",
        manual_lb=manual_lb_override,
        manual_ub=manual_ub_override,
        manual_cost=manual_cost_override,
        nominal_tracking_indices=nominal_override,
    )
    assert cfg.MANUAL_LB is manual_lb_override
    assert cfg.MANUAL_UB is manual_ub_override
    assert cfg.MANUAL_COST is manual_cost_override
    assert cfg.NOMINAL_TRACKING_INDICES is nominal_override


def test_missing_joint_mapping_message_points_to_profile_mappings() -> None:
    cfg = MotionDataConfig(data_format="smplx", robot_type="t1")

    with pytest.raises(ValueError, match="profiles/mappings.py") as exc_info:
        _ = cfg.resolved_joints_mapping

    assert "No joint mapping found for data_format=smplx, robot_type=t1" in str(exc_info.value)


def test_missing_foot_sticking_profile_message_points_to_profile_robots(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setitem(
        profile_robots.ROBOT_DEFAULTS,
        "profile_without_feet",
        {"robot_dof": 1, "robot_height": 1.0, "object_name": "ground"},
    )
    cfg = RobotConfig(robot_type="profile_without_feet")

    with pytest.raises(ValueError, match="profiles/robots.py") as exc_info:
        _ = cfg.FOOT_STICKING_LINKS

    assert "FOOT_STICKING_LINKS_BY_ROBOT" in str(exc_info.value)
