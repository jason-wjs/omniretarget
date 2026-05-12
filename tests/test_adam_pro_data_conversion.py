from omniretarget.config_types.data_conversion import DataConversionConfig


def test_adam_pro_joint_order_available_and_29dof() -> None:
    cfg = DataConversionConfig(input_file="dummy.npz", robot="adam_pro")
    names = cfg.JOINT_NAMES
    assert len(names) == 29
    assert len(set(names)) == 29
    assert names[0] == "hipPitch_Left"
    assert names[-1] == "wristRoll_Right"
