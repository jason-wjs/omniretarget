from holosoma_retargeting.profiles.mappings import JOINTS_MAPPINGS
from holosoma_retargeting.profiles.motions import DEMO_JOINTS_REGISTRY
from holosoma_retargeting.profiles.robots import ROBOT_DEFAULTS


def test_profiles_expose_existing_robot_and_motion_defaults() -> None:
    assert "adam_pro" in ROBOT_DEFAULTS
    assert "optitrack" in DEMO_JOINTS_REGISTRY
    assert ("optitrack", "adam_pro") in JOINTS_MAPPINGS
