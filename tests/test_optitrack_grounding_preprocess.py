import numpy as np

from holosoma_retargeting.utils.motion_preprocessing import preprocess_motion_data


class _DummyRetargeter:
    def __init__(self) -> None:
        self.demo_joints = ["LeftToeBase", "RightToeBase", "Hips"]


def _make_human_joints_with_toe_outlier() -> np.ndarray:
    """Build synthetic sequence with one noisy low toe sample."""
    T = 20
    J = 3
    human_joints = np.zeros((T, J, 3), dtype=float)

    # Typical toe height is 1cm; one frame has -2cm outlier noise on left toe.
    human_joints[:, 0, 2] = 0.01  # LeftToeBase
    human_joints[:, 1, 2] = 0.01  # RightToeBase
    human_joints[0, 0, 2] = -0.02
    return human_joints


def test_preprocess_motion_data_default_min_behavior_preserved() -> None:
    retargeter = _DummyRetargeter()
    human_joints = _make_human_joints_with_toe_outlier()

    processed = preprocess_motion_data(
        human_joints.copy(),
        retargeter,
        ["LeftToeBase", "RightToeBase"],
        scale=1.0,
    )

    # Default behavior uses strict min and shifts sequence by +0.02.
    assert np.isclose(processed[:, 1, 2].mean(), 0.03)


def test_preprocess_motion_data_percentile_grounding_rejects_toe_outlier() -> None:
    retargeter = _DummyRetargeter()
    human_joints = _make_human_joints_with_toe_outlier()

    processed = preprocess_motion_data(
        human_joints.copy(),
        retargeter,
        ["LeftToeBase", "RightToeBase"],
        scale=1.0,
        mat_height=0.0,
        ground_height_percentile=5.0,
    )

    # Robust grounding should align typical toe height to near-ground (0.0)
    # instead of lifting sequence by the noisy global minimum.
    assert np.isclose(processed[:, 1, 2].mean(), 0.0)
