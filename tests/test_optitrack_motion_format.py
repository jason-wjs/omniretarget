from holosoma_retargeting.configs.motion import MotionDataConfig


def test_optitrack_adam_pro_mapping_and_constants() -> None:
    cfg = MotionDataConfig(data_format="optitrack", robot_type="adam_pro")

    assert len(cfg.resolved_demo_joints) == 26
    assert cfg.toe_names == ["LeftToeBase", "RightToeBase"]
    assert cfg.default_human_height == 1.7

    mapping = cfg.resolved_joints_mapping
    assert mapping["Spine1"] == "pelvis"
    assert mapping["LeftUpLeg"] == "hipPitchLeft"
    assert mapping["RightUpLeg"] == "hipPitchRight"
    assert mapping["LeftForeArm"] == "elbowLeft"
    assert mapping["RightForeArm"] == "elbowRight"
    assert mapping["LeftToeBase"] == "left_foot_sphere_5_link"
    assert mapping["RightToeBase"] == "right_foot_sphere_5_link"
    assert mapping["LeftHand"] == "wristRollLeft"
    assert mapping["RightHand"] == "wristRollRight"


def test_optitrack_g1_mapping_exists_and_targets_expected_links() -> None:
    cfg = MotionDataConfig(data_format="optitrack", robot_type="g1")

    mapping = cfg.resolved_joints_mapping
    assert mapping["Spine1"] == "pelvis_contour_link"
    assert mapping["LeftUpLeg"] == "left_hip_pitch_link"
    assert mapping["RightUpLeg"] == "right_hip_pitch_link"
    assert mapping["LeftLeg"] == "left_knee_link"
    assert mapping["RightLeg"] == "right_knee_link"
    assert mapping["LeftArm"] == "left_shoulder_roll_link"
    assert mapping["RightArm"] == "right_shoulder_roll_link"
    assert mapping["LeftForeArm"] == "left_elbow_link"
    assert mapping["RightForeArm"] == "right_elbow_link"
    assert mapping["LeftFoot"] == "left_ankle_intermediate_1_link"
    assert mapping["RightFoot"] == "right_ankle_intermediate_1_link"
    assert mapping["LeftToeBase"] == "left_ankle_roll_sphere_5_link"
    assert mapping["RightToeBase"] == "right_ankle_roll_sphere_5_link"
    assert mapping["LeftHand"] == "left_rubber_hand_link"
    assert mapping["RightHand"] == "right_rubber_hand_link"
