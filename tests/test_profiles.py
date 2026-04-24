from holosoma_retargeting.config_types import data_type as config_data_type
from holosoma_retargeting.config_types import robot as config_robot
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
    assert config_data_type.JOINTS_MAPPINGS is profile_mappings.JOINTS_MAPPINGS


def test_config_types_robot_defaults_alias_profile_object() -> None:
    assert config_robot._ROBOT_DEFAULTS is profile_robots.ROBOT_DEFAULTS
