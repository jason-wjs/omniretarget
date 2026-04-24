import numpy as np

from holosoma_retargeting.cli.eval_retargeting import RetargetingEvaluator
from holosoma_retargeting.src.utils import extract_foot_sticking_sequence_velocity


def test_extract_foot_sticking_sequence_velocity_uses_requested_toe_names() -> None:
    # 3 frames, 2 toe joints; left toe static, right toe moves in xy.
    smpl_joints = np.array(
        [
            [[0.0, 0.0, 0.0], [0.0, 0.0, 0.0]],
            [[0.0, 0.0, 0.0], [0.2, 0.0, 0.0]],
            [[0.0, 0.0, 0.0], [0.4, 0.0, 0.0]],
        ],
        dtype=float,
    )
    demo_joints = ["LeftToeBase", "RightToeBase"]
    toe_names = ["LeftToeBase", "RightToeBase"]

    seq = extract_foot_sticking_sequence_velocity(smpl_joints, demo_joints, toe_names, velocity_threshold=0.05)

    assert set(seq[0].keys()) == {"LeftToeBase", "RightToeBase"}
    # First frame is always marked non-contact by construction.
    assert not bool(seq[0]["LeftToeBase"])
    assert not bool(seq[0]["RightToeBase"])


def test_detect_foot_sliding_uses_robot_mapping_for_toe_links() -> None:
    class _DummyEvaluator:
        sliding_threshold = 0.01
        joints_mapping = {
            "LeftToeBase": "left_foot_sphere_5_link",
            "RightToeBase": "right_foot_sphere_5_link",
        }

        def __init__(self) -> None:
            self.last_links: tuple[str, str] | None = None

        def _get_robot_link_positions(self, q: np.ndarray, link_names: list[str]) -> np.ndarray:
            self.last_links = (link_names[0], link_names[1])
            # left toe static, right toe moves with q[1]
            return np.array([[0.0, 0.0, 0.0], [float(q[1]), 0.0, 0.0]], dtype=float)

    evaluator = _DummyEvaluator()
    q_trajectory = np.array([[0.0, 0.0], [0.0, 0.02], [0.0, 0.04]], dtype=float)
    contact_sequences = [
        {"LeftToeBase": True, "RightToeBase": True},
        {"LeftToeBase": True, "RightToeBase": True},
        {"LeftToeBase": True, "RightToeBase": True},
    ]

    RetargetingEvaluator.detect_foot_sliding(
        evaluator, q_trajectory, contact_sequences, ["LeftToeBase", "RightToeBase"]
    )

    assert evaluator.last_links == ("left_foot_sphere_5_link", "right_foot_sphere_5_link")
