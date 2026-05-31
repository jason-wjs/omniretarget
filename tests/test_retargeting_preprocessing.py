from __future__ import annotations

from types import SimpleNamespace

import numpy as np

from omniretarget.retargeting import preprocessing as preprocessing_module
from omniretarget.retargeting.preprocessing import build_foot_sticking_sequences, preprocess_retargeting_motion


def test_preprocess_retargeting_motion_uses_optitrack_grounding(monkeypatch) -> None:
    human_joints = np.zeros((2, 3, 3))
    processed = np.ones((2, 3, 3))
    retargeter = SimpleNamespace()
    toe_names = ["left", "right"]

    def fake_preprocess_motion_data(
        actual_human_joints,
        actual_retargeter,
        actual_toe_names,
        scale,
        *,
        mat_height,
        ground_height_percentile,
    ):
        assert actual_human_joints is human_joints
        assert actual_retargeter is retargeter
        assert actual_toe_names == toe_names
        assert scale == 1.25
        assert mat_height == 0.0
        assert ground_height_percentile == 5.0
        return processed

    monkeypatch.setattr(preprocessing_module, "preprocess_motion_data", fake_preprocess_motion_data)

    actual_human_joints, actual_object_poses, object_moving_frame_idx = preprocess_retargeting_motion(
        task_type="robot_only",
        data_format="optitrack",
        human_joints=human_joints,
        object_poses=np.zeros((2, 7)),
        retargeter=retargeter,
        toe_names=toe_names,
        smpl_scale=1.25,
    )

    assert actual_human_joints is processed
    np.testing.assert_array_equal(actual_object_poses, np.zeros((2, 7)))
    assert object_moving_frame_idx is None


def test_preprocess_retargeting_motion_preserves_parc_height_origin(monkeypatch) -> None:
    human_joints = np.zeros((2, 3, 3))
    source_object_poses = np.zeros((2, 7))
    processed_human = np.ones((2, 3, 3))
    processed_object = np.ones((2, 7))
    retargeter = SimpleNamespace()

    def fake_preprocess_motion_data(
        actual_human_joints,
        actual_retargeter,
        actual_toe_names,
        *,
        scale,
        object_poses,
        normalize_height,
    ):
        assert actual_human_joints is human_joints
        assert actual_retargeter is retargeter
        assert actual_toe_names == ["left", "right"]
        assert scale == 2.0
        assert object_poses is source_object_poses
        assert normalize_height is False
        return processed_human, processed_object, 3

    monkeypatch.setattr(preprocessing_module, "preprocess_motion_data", fake_preprocess_motion_data)

    actual = preprocess_retargeting_motion(
        task_type="climbing",
        data_format="parc_humanoid",
        human_joints=human_joints,
        object_poses=source_object_poses,
        retargeter=retargeter,
        toe_names=["left", "right"],
        smpl_scale=2.0,
    )

    assert actual == (processed_human, processed_object, 3)


def test_build_foot_sticking_sequences_disables_object_interaction_initial_contacts(monkeypatch) -> None:
    sequences = [{"left": True, "right": True}, {"left": True, "right": False}]

    def fake_extract(human_joints, demo_joints, toe_names):
        assert demo_joints == ["hip", "left", "right"]
        assert toe_names == ["left", "right"]
        return sequences

    monkeypatch.setattr(preprocessing_module, "extract_foot_sticking_sequence_velocity", fake_extract)

    actual = build_foot_sticking_sequences(
        task_type="object_interaction",
        human_joints=np.zeros((2, 3, 3)),
        demo_joints=["hip", "left", "right"],
        toe_names=["left", "right"],
    )

    assert actual[0] == {"left": False, "right": False}
    assert actual[1] == {"left": True, "right": False}
