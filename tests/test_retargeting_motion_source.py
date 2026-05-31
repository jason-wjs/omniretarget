from __future__ import annotations

from types import SimpleNamespace

import numpy as np

from omniretarget.config_types.data_type import MotionDataConfig
from omniretarget.examples.robot_retarget import load_motion_data as legacy_load_motion_data
from omniretarget.retargeting.motion_source import load_motion_data


def test_motion_source_matches_legacy_robot_only_smplx_npz(tmp_path) -> None:
    human_joints = np.arange(2 * 4 * 3, dtype=float).reshape(2, 4, 3)
    np.savez(
        tmp_path / "sample.npz",
        global_joint_positions=human_joints,
        height=np.asarray(1.65),
    )
    constants = SimpleNamespace(ROBOT_HEIGHT=1.32)
    motion_data_config = MotionDataConfig(data_format="smplx", robot_type="g1")

    expected = legacy_load_motion_data(
        task_type="robot_only",
        data_format="smplx",
        data_path=tmp_path,
        task_name="sample",
        constants=constants,
        motion_data_config=motion_data_config,
    )
    actual = load_motion_data(
        task_type="robot_only",
        data_format="smplx",
        data_path=tmp_path,
        task_name="sample",
        constants=constants,
        motion_data_config=motion_data_config,
    )

    for actual_array, expected_array in zip(actual[:2], expected[:2]):
        np.testing.assert_array_equal(actual_array, expected_array)
    assert actual[2] == expected[2]
