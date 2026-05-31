from __future__ import annotations

from types import SimpleNamespace

import numpy as np

from omniretarget.config_types.task import TaskConfig
from omniretarget.examples.robot_retarget import _compute_q_init_base as legacy_compute_q_init_base
from omniretarget.examples.robot_retarget import convert_object_poses_to_mujoco_order as legacy_convert_object_poses
from omniretarget.examples.robot_retarget import initialize_robot_pose as legacy_initialize_robot_pose
from omniretarget.retargeting.initialization import (
    compute_q_init_base,
    convert_object_poses_to_mujoco_order,
    initialize_robot_pose,
)


def test_convert_object_poses_to_mujoco_order_matches_legacy() -> None:
    object_poses = np.array([[1.0, 0.1, 0.2, 0.3, 4.0, 5.0, 6.0]])

    actual = convert_object_poses_to_mujoco_order(object_poses)
    expected = legacy_convert_object_poses(object_poses)

    np.testing.assert_array_equal(actual, expected)


def test_compute_q_init_base_matches_legacy_robot_only_smplh() -> None:
    human_joints = np.array([[[0.1, 0.2, 0.3]]])
    object_poses = np.array([[1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]])
    constants = SimpleNamespace(ROBOT_DOF=2)

    actual = compute_q_init_base(
        task_type="robot_only",
        data_format="smplh",
        human_joints=human_joints,
        object_poses=object_poses,
        constants=constants,
    )
    expected = legacy_compute_q_init_base(
        task_type="robot_only",
        data_format="smplh",
        human_joints=human_joints,
        object_poses=object_poses,
        constants=constants,
    )

    np.testing.assert_array_equal(actual, expected)


def test_initialize_robot_pose_matches_legacy_robot_only_smplh(tmp_path) -> None:
    human_joints = np.array([[[0.1, 0.2, 0.3]]])
    object_poses = np.array([[1.0, 0.0, 0.0, 0.0, 4.0, 5.0, 6.0]])
    constants = SimpleNamespace(ROBOT_DOF=2)

    actual = initialize_robot_pose(
        task_type="robot_only",
        data_format="smplh",
        human_joints=human_joints,
        object_poses=object_poses,
        constants=constants,
        retargeter=SimpleNamespace(),
        task_config=TaskConfig(),
        augmentation=False,
        save_dir=tmp_path,
        task_name="sample",
    )
    expected = legacy_initialize_robot_pose(
        task_type="robot_only",
        data_format="smplh",
        human_joints=human_joints,
        object_poses=object_poses,
        constants=constants,
        retargeter=SimpleNamespace(),
        task_config=TaskConfig(),
        augmentation=False,
        save_dir=tmp_path,
        task_name="sample",
    )

    for actual_value, expected_value in zip(actual, expected):
        if actual_value is None or expected_value is None:
            assert actual_value is expected_value
        else:
            np.testing.assert_array_equal(actual_value, expected_value)
