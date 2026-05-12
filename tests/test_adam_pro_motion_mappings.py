from omniretarget.config_types.data_type import MotionDataConfig


def test_adam_pro_mapping_exists_for_smplh_smplx_lafan() -> None:
    for fmt in ("smplh", "smplx", "lafan"):
        cfg = MotionDataConfig(data_format=fmt, robot_type="adam_pro")
        mapping = cfg.resolved_joints_mapping
        assert len(mapping) > 0


def test_adam_pro_mapping_contains_core_targets() -> None:
    cfg = MotionDataConfig(data_format="smplh", robot_type="adam_pro")
    m = cfg.resolved_joints_mapping
    assert "Pelvis" in m
    assert "L_Hip" in m and "R_Hip" in m
    assert "L_Wrist" in m and "R_Wrist" in m
    assert "L_Toe" in m and "R_Toe" in m
    assert m["L_Toe"] == "left_foot_sphere_5_link"
    assert m["R_Toe"] == "right_foot_sphere_5_link"
