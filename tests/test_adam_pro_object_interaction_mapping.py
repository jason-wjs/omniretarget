from holosoma_retargeting.config_types.data_type import MotionDataConfig
from holosoma_retargeting.config_types.robot import RobotConfig
from holosoma_retargeting.config_types.task import TaskConfig
from holosoma_retargeting.examples.robot_retarget import create_task_constants


def test_adam_pro_object_interaction_uses_hand_ee_links() -> None:
    constants = create_task_constants(
        robot_config=RobotConfig(robot_type="adam_pro"),
        motion_data_config=MotionDataConfig(data_format="smplh", robot_type="adam_pro"),
        task_config=TaskConfig(object_name="largebox"),
        task_type="object_interaction",
    )
    assert constants.JOINTS_MAPPING["L_Wrist"] == "left_hand_ee_link"
    assert constants.JOINTS_MAPPING["R_Wrist"] == "right_hand_ee_link"


def test_adam_pro_robot_only_keeps_wrist_roll_links() -> None:
    constants = create_task_constants(
        robot_config=RobotConfig(robot_type="adam_pro"),
        motion_data_config=MotionDataConfig(data_format="smplh", robot_type="adam_pro"),
        task_config=TaskConfig(object_name="ground"),
        task_type="robot_only",
    )
    assert constants.JOINTS_MAPPING["L_Wrist"] == "wristRollLeft"
    assert constants.JOINTS_MAPPING["R_Wrist"] == "wristRollRight"


def test_adam_pro_robot_only_adds_hip_roll_yaw_bounds_without_hip_costs() -> None:
    constants = create_task_constants(
        robot_config=RobotConfig(robot_type="adam_pro"),
        motion_data_config=MotionDataConfig(data_format="smplh", robot_type="adam_pro"),
        task_config=TaskConfig(object_name="ground"),
        task_type="robot_only",
    )
    assert constants.MANUAL_LB["8"] == -0.499
    assert constants.MANUAL_UB["8"] == 1.371
    assert constants.MANUAL_LB["9"] == -0.628
    assert constants.MANUAL_UB["9"] == 0.628
    assert constants.MANUAL_LB["14"] == -1.371
    assert constants.MANUAL_UB["14"] == 0.499
    assert constants.MANUAL_LB["15"] == -0.628
    assert constants.MANUAL_UB["15"] == 0.628
    assert "8" not in constants.MANUAL_COST
    assert "9" not in constants.MANUAL_COST
    assert "14" not in constants.MANUAL_COST
    assert "15" not in constants.MANUAL_COST


def test_adam_pro_object_interaction_does_not_apply_robot_only_hip_bounds() -> None:
    constants = create_task_constants(
        robot_config=RobotConfig(robot_type="adam_pro"),
        motion_data_config=MotionDataConfig(data_format="smplh", robot_type="adam_pro"),
        task_config=TaskConfig(object_name="largebox"),
        task_type="object_interaction",
    )
    assert "8" not in constants.MANUAL_LB
    assert "9" not in constants.MANUAL_LB
    assert "14" not in constants.MANUAL_LB
    assert "15" not in constants.MANUAL_LB
