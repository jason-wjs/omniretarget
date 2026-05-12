from omniretarget.evaluation.eval_retargeting import RetargetingEvaluator


def test_object_contact_defaults_prefer_smpl_wrists() -> None:
    demo_joints = ["Pelvis", "L_Wrist", "R_Wrist", "L_Toe", "R_Toe"]
    mapping_keys = ["L_Wrist", "R_Wrist", "L_Toe", "R_Toe"]

    joint_names = RetargetingEvaluator._resolve_default_joint_names(
        demo_joints,
        mapping_keys,
        mode="object_contact",
    )

    assert joint_names == ["L_Wrist", "R_Wrist"]


def test_object_contact_defaults_fallback_to_lafan_hands() -> None:
    demo_joints = ["Spine1", "LeftHand", "RightHand", "LeftToeBase", "RightToeBase"]
    mapping_keys = ["LeftHand", "RightHand", "LeftToeBase", "RightToeBase"]

    joint_names = RetargetingEvaluator._resolve_default_joint_names(
        demo_joints,
        mapping_keys,
        mode="object_contact",
    )

    assert joint_names == ["LeftHand", "RightHand"]


def test_terrain_contact_defaults_collect_available_end_effectors() -> None:
    demo_joints = ["LeftHand", "RightHand", "LeftFoot", "RightFoot", "LeftToeBase", "RightToeBase"]
    mapping_keys = ["LeftHand", "RightHand", "LeftFoot", "RightFoot", "LeftToeBase", "RightToeBase"]

    joint_names = RetargetingEvaluator._resolve_default_joint_names(
        demo_joints,
        mapping_keys,
        mode="terrain_contact",
    )

    assert joint_names == [
        "LeftHand",
        "RightHand",
        "LeftFoot",
        "RightFoot",
        "LeftToeBase",
        "RightToeBase",
    ]
