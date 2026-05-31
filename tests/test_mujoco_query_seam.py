from __future__ import annotations

from types import SimpleNamespace

import mujoco
import numpy as np
import pytest

from omniretarget.mujoco.assets import resolve_robot_xml_path
from omniretarget.mujoco.collision import (
    geom_pair_allowed_for_object_or_ground,
    should_enforce_non_penetration_pair,
)
from omniretarget.mujoco.kinematics import link_positions
from omniretarget.mujoco.model_state import has_dynamic_object_qpos, qpos_for_model
from tests.path_helpers import PACKAGE_ROOT


G1_XML = PACKAGE_ROOT / "models" / "g1" / "g1_29dof.xml"
G1_LARGEBOX_XML = PACKAGE_ROOT / "models" / "g1" / "g1_29dof_w_largebox.xml"
G1_URDF = PACKAGE_ROOT / "models" / "g1" / "g1_29dof.urdf"


def test_resolve_robot_xml_path_matches_legacy_object_rules() -> None:
    assert resolve_robot_xml_path(str(G1_URDF), "ground") == str(G1_XML)
    assert resolve_robot_xml_path(str(G1_URDF), "largebox") == str(G1_LARGEBOX_XML)
    assert resolve_robot_xml_path(str(G1_URDF), "multi_boxes", scene_xml_file="workspace/scene.xml") == (
        "workspace/scene.xml"
    )


def test_detects_dynamic_object_qpos_layout_from_model_size() -> None:
    robot_only_model = mujoco.MjModel.from_xml_path(str(G1_XML))
    largebox_model = mujoco.MjModel.from_xml_path(str(G1_LARGEBOX_XML))

    assert not has_dynamic_object_qpos(robot_only_model, robot_dof=29)
    assert has_dynamic_object_qpos(largebox_model, robot_dof=29)


def test_qpos_for_model_strips_trailing_object_pose_only_when_allowed() -> None:
    robot_only_model = mujoco.MjModel.from_xml_path(str(G1_XML))
    q_with_object = np.arange(robot_only_model.nq + 7, dtype=np.float64)

    np.testing.assert_array_equal(
        qpos_for_model(q_with_object, robot_only_model, allow_trailing_dynamic_object=True),
        q_with_object[:-7],
    )
    with pytest.raises(ValueError, match="qpos shape"):
        qpos_for_model(q_with_object, robot_only_model)


def test_link_positions_match_mujoco_body_xpos_for_known_links() -> None:
    model = mujoco.MjModel.from_xml_path(str(G1_XML))
    data = mujoco.MjData(model)
    q = np.zeros(model.nq, dtype=np.float64)
    q[3] = 1.0

    actual = link_positions(model, data, q, ["pelvis_contour_link", "left_hip_pitch_link"])

    mujoco.mj_forward(model, data)
    expected = np.vstack(
        [
            data.xpos[mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_BODY, "pelvis_contour_link")],
            data.xpos[mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_BODY, "left_hip_pitch_link")],
        ]
    )
    np.testing.assert_allclose(actual, expected)


def test_link_positions_raise_for_unknown_body() -> None:
    model = mujoco.MjModel.from_xml_path(str(G1_XML))
    data = mujoco.MjData(model)
    q = np.zeros(model.nq, dtype=np.float64)
    q[3] = 1.0

    with pytest.raises(ValueError, match="Body missing_link not found"):
        link_positions(model, data, q, ["missing_link"])


def test_collision_pair_filter_keeps_only_collidable_object_or_ground_pairs() -> None:
    model = SimpleNamespace(
        geom_contype=np.array([1, 1, 1, 1, 0]),
        geom_conaffinity=np.array([1, 1, 1, 1, 0]),
    )
    geom_names = [
        "multi_boxes_collision",
        "left_foot_collision",
        "ground",
        "right_foot_collision",
        "visual_only",
    ]

    assert geom_pair_allowed_for_object_or_ground(model, geom_names, "multi_boxes", 0, 1)
    assert geom_pair_allowed_for_object_or_ground(model, geom_names, "multi_boxes", 1, 2)
    assert not geom_pair_allowed_for_object_or_ground(model, geom_names, "multi_boxes", 0, 2)
    assert not geom_pair_allowed_for_object_or_ground(model, geom_names, "multi_boxes", 1, 3)
    assert not geom_pair_allowed_for_object_or_ground(model, geom_names, "multi_boxes", 0, 4)


def test_non_penetration_pair_gate_preserves_ground_when_object_constraints_disabled() -> None:
    geom_names = ["multi_boxes_collision", "left_foot_collision", "ground"]

    assert not should_enforce_non_penetration_pair(
        (0, 1),
        geom_names=geom_names,
        object_name="multi_boxes",
        activate_obj_non_penetration=False,
    )
    assert should_enforce_non_penetration_pair(
        (1, 2),
        geom_names=geom_names,
        object_name="multi_boxes",
        activate_obj_non_penetration=False,
    )
