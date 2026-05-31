from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest

from omniretarget.config_types.data_type import MotionDataConfig
from omniretarget.config_types.robot import RobotConfig
from omniretarget.config_types.task import TaskConfig
from omniretarget.runtime.context import build_runtime_context
from omniretarget.retargeter import InteractionMeshRetargeter
from omniretarget.solver.constraints import select_bilateral_foot_keys
from omniretarget.solver.interaction_mesh import build_interaction_mesh_frame


def _robot_only_constants():
    return build_runtime_context(
        robot_config=RobotConfig(robot_type="g1"),
        motion_data_config=MotionDataConfig(data_format="smplh", robot_type="g1"),
        task_config=TaskConfig(object_name="ground"),
        task_type="robot_only",
    ).to_legacy_namespace()


def test_interaction_mesh_retargeter_constructor_keeps_public_facade() -> None:
    retargeter = InteractionMeshRetargeter(
        _robot_only_constants(),
        object_urdf_path="",
        visualize=False,
    )

    assert retargeter.has_dynamic_object is False
    assert retargeter.robot_model.nq == 36
    assert callable(retargeter.retarget_motion)
    assert callable(retargeter.iterate)
    assert callable(retargeter.solve_single_iteration)


def test_retarget_motion_facade_delegates_to_trajectory_solver(monkeypatch, tmp_path: Path) -> None:
    from omniretarget.solver import trajectory

    captured = {}
    sentinel = (np.zeros((1, 36)), [], [], [])

    def fake_solve_trajectory(retargeter, **kwargs):
        captured["retargeter"] = retargeter
        captured.update(kwargs)
        return sentinel

    monkeypatch.setattr(trajectory, "solve_trajectory", fake_solve_trajectory)
    retargeter = InteractionMeshRetargeter.__new__(InteractionMeshRetargeter)

    human = np.zeros((1, 2, 3), dtype=np.float64)
    object_poses = np.zeros((1, 7), dtype=np.float64)
    object_points = np.zeros((4, 3), dtype=np.float64)
    foot_sequences = [{"left": False, "right": False}]
    out = tmp_path / "out.npz"

    actual = retargeter.retarget_motion(
        human,
        object_poses,
        object_poses,
        object_points,
        object_points,
        foot_sequences,
        q_a_init=np.ones(3),
        q_nominal_list=None,
        original=False,
        dest_res_path=out,
    )

    assert actual is sentinel
    assert captured["retargeter"] is retargeter
    assert captured["human_joint_motions"] is human
    assert captured["object_poses"] is object_poses
    assert captured["object_poses_augmented"] is object_poses
    assert captured["dest_res_path"] == out
    assert captured["original"] is False


def test_build_interaction_mesh_frame_keeps_ground_points_in_world_frame() -> None:
    human_mapped_joints = np.array(
        [
            [0.0, 0.0, 0.0],
            [1.0, 0.0, 0.0],
        ],
        dtype=np.float64,
    )
    object_points = np.array(
        [
            [0.0, 1.0, 0.0],
            [0.0, 0.0, 1.0],
            [1.0, 1.0, 0.0],
            [1.0, 0.0, 1.0],
        ],
        dtype=np.float64,
    )

    frame = build_interaction_mesh_frame(
        object_name="ground",
        human_mapped_joints=human_mapped_joints,
        object_pose_demo=np.array([0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0], dtype=np.float64),
        object_pose_augmented=np.array([0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0], dtype=np.float64),
        object_points_local_demo=object_points,
        object_points_local=object_points,
        include_debug_points=True,
    )

    np.testing.assert_allclose(frame.human_mapped_joints_in_object, human_mapped_joints)
    np.testing.assert_allclose(frame.source_vertices[:2], human_mapped_joints)
    assert frame.source_tetrahedra.shape[1] == 4
    assert len(frame.adj_list) == frame.source_vertices.shape[0]
    assert frame.target_laplacian.shape == frame.source_vertices.shape
    assert frame.object_points_demo_world is not None
    assert frame.object_points_world is not None


def test_select_bilateral_foot_keys_finds_left_and_right_entries() -> None:
    assert select_bilateral_foot_keys({"left_toe": True, "right_toe": False}) == ("left_toe", "right_toe")

    with pytest.raises(ValueError, match="left\\* and one right\\*"):
        select_bilateral_foot_keys({"left_toe": True})
