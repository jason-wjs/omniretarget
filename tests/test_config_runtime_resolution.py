from holosoma_retargeting.config_types.data_conversion import DataConversionConfig
from holosoma_retargeting.config_types.data_type import MotionDataConfig
from holosoma_retargeting.config_types.retargeting import RetargetingConfig
from holosoma_retargeting.config_types.robot import RobotConfig
from holosoma_retargeting.configs.runtime import (
    resolve_retargeting_config,
    resolve_robot_and_motion_configs,
)


def test_resolve_retargeting_config_syncs_robot_and_motion_format() -> None:
    cfg = RetargetingConfig(robot="adam_pro", data_format="optitrack", task_type="robot_only")

    resolved = resolve_retargeting_config(cfg)

    assert resolved.robot_config.robot_type == "adam_pro"
    assert resolved.motion_data_config.robot_type == "adam_pro"
    assert resolved.motion_data_config.data_format == "optitrack"


def test_resolve_retargeting_config_uses_caller_resolved_data_format_without_mutating_original() -> None:
    cfg = RetargetingConfig(robot="adam_pro", data_format=None, task_type="robot_only")

    resolved = resolve_retargeting_config(cfg, data_format="smplh")

    assert resolved.motion_data_config.robot_type == "adam_pro"
    assert resolved.motion_data_config.data_format == "smplh"
    assert cfg.data_format is None
    assert cfg.robot_config.robot_type == "g1"
    assert cfg.motion_data_config.robot_type == "g1"
    assert cfg.motion_data_config.data_format == "smplh"


def test_resolve_retargeting_config_preserves_matching_nested_overrides() -> None:
    robot_config = RobotConfig(robot_type="adam_pro", robot_urdf_file="custom_adam_pro.urdf")
    motion_data_config = MotionDataConfig(
        data_format="optitrack",
        robot_type="adam_pro",
        demo_joints=["custom_marker"],
        joints_mapping={"custom_marker": "custom_link"},
    )
    cfg = RetargetingConfig(
        robot="adam_pro",
        data_format="optitrack",
        task_type="robot_only",
        robot_config=robot_config,
        motion_data_config=motion_data_config,
    )

    resolved = resolve_retargeting_config(cfg)

    assert resolved.robot_config is robot_config
    assert resolved.motion_data_config is motion_data_config


def test_resolve_robot_and_motion_configs_returns_data_conversion_runtime_pair() -> None:
    cfg = DataConversionConfig(input_file="dummy.npz", robot="adam_pro", data_format="optitrack")

    robot_config, motion_data_config = resolve_robot_and_motion_configs(
        robot=cfg.robot,
        data_format=cfg.data_format,
        robot_config=cfg.robot_config,
        motion_data_config=cfg.motion_data_config,
    )

    assert robot_config.robot_type == "adam_pro"
    assert motion_data_config.robot_type == "adam_pro"
    assert motion_data_config.data_format == "optitrack"
