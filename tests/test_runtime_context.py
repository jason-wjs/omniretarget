from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace
from typing import Iterable

import numpy as np

from omniretarget.config_types.data_type import MotionDataConfig
from omniretarget.config_types.robot import RobotConfig
from omniretarget.config_types.task import TaskConfig
from omniretarget.data_conversion import convert_data_format_mj
from omniretarget.evaluation import eval_retargeting
from omniretarget.examples import robot_retarget
from omniretarget.runtime.context import (
    build_evaluation_runtime_context,
    build_mj_conversion_runtime_context,
    build_runtime_context,
)


def _assert_namespace_fields_equal(actual: SimpleNamespace, expected: SimpleNamespace, fields: Iterable[str]) -> None:
    for field in fields:
        assert hasattr(actual, field) == hasattr(expected, field), f"field presence mismatch for {field}"
        if not hasattr(expected, field):
            continue
        actual_value = getattr(actual, field)
        expected_value = getattr(expected, field)
        if isinstance(actual_value, np.ndarray) or isinstance(expected_value, np.ndarray):
            np.testing.assert_array_equal(actual_value, expected_value, err_msg=field)
        else:
            assert actual_value == expected_value, field


def test_runtime_context_matches_robot_retarget_robot_only_adam_pro_lafan() -> None:
    robot_config = RobotConfig(robot_type="adam_pro")
    motion_data_config = MotionDataConfig(data_format="lafan", robot_type="adam_pro")
    task_config = TaskConfig(object_name="ground")

    expected = robot_retarget.create_task_constants(
        robot_config=robot_config,
        motion_data_config=motion_data_config,
        task_config=task_config,
        task_type="robot_only",
    )
    actual = build_runtime_context(
        robot_config=robot_config,
        motion_data_config=motion_data_config,
        task_config=task_config,
        task_type="robot_only",
    ).to_legacy_namespace()

    _assert_namespace_fields_equal(
        actual,
        expected,
        (
            "ROBOT_DOF",
            "ROBOT_HEIGHT",
            "ROBOT_NAME",
            "ROBOT_URDF_FILE",
            "FOOT_STICKING_LINKS",
            "MANUAL_LB",
            "MANUAL_UB",
            "MANUAL_COST",
            "NOMINAL_TRACKING_INDICES",
            "DEMO_JOINTS",
            "JOINTS_MAPPING",
            "TOE_NAMES",
            "DEFAULT_SCALE_FACTOR",
            "DEFAULT_HUMAN_HEIGHT",
            "OBJECT_NAME",
            "OBJECT_URDF_FILE",
            "OBJECT_MESH_FILE",
        ),
    )


def test_runtime_context_matches_robot_retarget_object_interaction_adam_pro_smplh() -> None:
    robot_config = RobotConfig(robot_type="adam_pro")
    motion_data_config = MotionDataConfig(data_format="smplh", robot_type="adam_pro")
    task_config = TaskConfig(object_name="largebox")

    expected = robot_retarget.create_task_constants(
        robot_config=robot_config,
        motion_data_config=motion_data_config,
        task_config=task_config,
        task_type="object_interaction",
    )
    actual = build_runtime_context(
        robot_config=robot_config,
        motion_data_config=motion_data_config,
        task_config=task_config,
        task_type="object_interaction",
    ).to_legacy_namespace()

    _assert_namespace_fields_equal(
        actual,
        expected,
        (
            "ROBOT_DOF",
            "ROBOT_HEIGHT",
            "ROBOT_NAME",
            "ROBOT_URDF_FILE",
            "FOOT_STICKING_LINKS",
            "MANUAL_LB",
            "MANUAL_UB",
            "MANUAL_COST",
            "NOMINAL_TRACKING_INDICES",
            "DEMO_JOINTS",
            "JOINTS_MAPPING",
            "TOE_NAMES",
            "DEFAULT_SCALE_FACTOR",
            "DEFAULT_HUMAN_HEIGHT",
            "OBJECT_NAME",
            "OBJECT_URDF_FILE",
            "OBJECT_MESH_FILE",
            "OBJECT_URDF_TEMPLATE",
        ),
    )


def test_runtime_context_matches_robot_retarget_climbing_mocap_g1() -> None:
    robot_config = RobotConfig(robot_type="g1")
    motion_data_config = MotionDataConfig(data_format="mocap", robot_type="g1")
    task_config = TaskConfig(object_name="multi_boxes", object_dir=Path("/tmp/mocap_climb_seq_0"))

    expected = robot_retarget.create_task_constants(
        robot_config=robot_config,
        motion_data_config=motion_data_config,
        task_config=task_config,
        task_type="climbing",
    )
    actual = build_runtime_context(
        robot_config=robot_config,
        motion_data_config=motion_data_config,
        task_config=task_config,
        task_type="climbing",
    ).to_legacy_namespace()

    _assert_namespace_fields_equal(
        actual,
        expected,
        (
            "ROBOT_DOF",
            "ROBOT_HEIGHT",
            "ROBOT_NAME",
            "ROBOT_URDF_FILE",
            "FOOT_STICKING_LINKS",
            "MANUAL_LB",
            "MANUAL_UB",
            "MANUAL_COST",
            "NOMINAL_TRACKING_INDICES",
            "DEMO_JOINTS",
            "JOINTS_MAPPING",
            "TOE_NAMES",
            "DEFAULT_SCALE_FACTOR",
            "DEFAULT_HUMAN_HEIGHT",
            "OBJECT_NAME",
            "OBJECT_DIR",
            "OBJECT_URDF_FILE",
            "OBJECT_MESH_FILE",
            "SCENE_XML_FILE",
        ),
    )


def test_runtime_context_matches_robot_retarget_climbing_parc_humanoid_g1() -> None:
    robot_config = RobotConfig(robot_type="g1")
    motion_data_config = MotionDataConfig(data_format="parc_humanoid", robot_type="g1")
    task_config = TaskConfig(object_name="multi_boxes")

    expected = robot_retarget.create_task_constants(
        robot_config=robot_config,
        motion_data_config=motion_data_config,
        task_config=task_config,
        task_type="climbing",
    )
    actual = build_runtime_context(
        robot_config=robot_config,
        motion_data_config=motion_data_config,
        task_config=task_config,
        task_type="climbing",
    ).to_legacy_namespace()

    _assert_namespace_fields_equal(
        actual,
        expected,
        (
            "ROBOT_DOF",
            "ROBOT_HEIGHT",
            "ROBOT_NAME",
            "ROBOT_URDF_FILE",
            "FOOT_STICKING_LINKS",
            "MANUAL_LB",
            "MANUAL_UB",
            "MANUAL_COST",
            "NOMINAL_TRACKING_INDICES",
            "DEMO_JOINTS",
            "JOINTS_MAPPING",
            "TOE_NAMES",
            "DEFAULT_SCALE_FACTOR",
            "DEFAULT_HUMAN_HEIGHT",
            "OBJECT_NAME",
            "OBJECT_DIR",
            "OBJECT_URDF_FILE",
            "OBJECT_MESH_FILE",
            "SCENE_XML_FILE",
        ),
    )


def test_runtime_context_matches_eval_retargeting_ground_object() -> None:
    robot_config = RobotConfig(robot_type="g1")
    motion_data_config = MotionDataConfig(data_format="smplh", robot_type="g1")

    expected = eval_retargeting.create_task_constants(
        robot_config=robot_config,
        motion_data_config=motion_data_config,
        object_name="ground",
    )
    actual = build_evaluation_runtime_context(
        robot_config=robot_config,
        motion_data_config=motion_data_config,
        object_name="ground",
    ).to_legacy_namespace()

    _assert_namespace_fields_equal(
        actual,
        expected,
        (
            "ROBOT_DOF",
            "ROBOT_HEIGHT",
            "ROBOT_NAME",
            "ROBOT_URDF_FILE",
            "FOOT_STICKING_LINKS",
            "MANUAL_LB",
            "MANUAL_UB",
            "MANUAL_COST",
            "NOMINAL_TRACKING_INDICES",
            "DEMO_JOINTS",
            "JOINTS_MAPPING",
            "TOE_NAMES",
            "DEFAULT_SCALE_FACTOR",
            "DEFAULT_HUMAN_HEIGHT",
            "OBJECT_NAME",
            "OBJECT_DIR",
            "OBJECT_URDF_FILE",
            "OBJECT_MESH_FILE",
            "OBJECT_URDF_TEMPLATE",
            "SCENE_XML_FILE",
        ),
    )


def test_runtime_context_matches_eval_retargeting_largebox_object() -> None:
    robot_config = RobotConfig(robot_type="g1")
    motion_data_config = MotionDataConfig(data_format="smplh", robot_type="g1")

    expected = eval_retargeting.create_task_constants(
        robot_config=robot_config,
        motion_data_config=motion_data_config,
        object_name="largebox",
    )
    actual = build_evaluation_runtime_context(
        robot_config=robot_config,
        motion_data_config=motion_data_config,
        object_name="largebox",
    ).to_legacy_namespace()

    _assert_namespace_fields_equal(
        actual,
        expected,
        (
            "ROBOT_DOF",
            "ROBOT_HEIGHT",
            "ROBOT_NAME",
            "ROBOT_URDF_FILE",
            "FOOT_STICKING_LINKS",
            "MANUAL_LB",
            "MANUAL_UB",
            "MANUAL_COST",
            "NOMINAL_TRACKING_INDICES",
            "DEMO_JOINTS",
            "JOINTS_MAPPING",
            "TOE_NAMES",
            "DEFAULT_SCALE_FACTOR",
            "DEFAULT_HUMAN_HEIGHT",
            "OBJECT_NAME",
            "OBJECT_DIR",
            "OBJECT_URDF_FILE",
            "OBJECT_MESH_FILE",
            "OBJECT_URDF_TEMPLATE",
            "SCENE_XML_FILE",
        ),
    )


def test_runtime_context_matches_eval_retargeting_multi_boxes_with_object_dir() -> None:
    robot_config = RobotConfig(robot_type="g1")
    motion_data_config = MotionDataConfig(data_format="parc_humanoid", robot_type="g1")
    object_dir = "/tmp/parc_sample"

    expected = eval_retargeting.create_task_constants(
        robot_config=robot_config,
        motion_data_config=motion_data_config,
        object_name="multi_boxes",
        object_dir=object_dir,
    )
    actual = build_evaluation_runtime_context(
        robot_config=robot_config,
        motion_data_config=motion_data_config,
        object_name="multi_boxes",
        object_dir=object_dir,
    ).to_legacy_namespace()

    _assert_namespace_fields_equal(
        actual,
        expected,
        (
            "ROBOT_DOF",
            "ROBOT_HEIGHT",
            "ROBOT_NAME",
            "ROBOT_URDF_FILE",
            "FOOT_STICKING_LINKS",
            "MANUAL_LB",
            "MANUAL_UB",
            "MANUAL_COST",
            "NOMINAL_TRACKING_INDICES",
            "DEMO_JOINTS",
            "JOINTS_MAPPING",
            "TOE_NAMES",
            "DEFAULT_SCALE_FACTOR",
            "DEFAULT_HUMAN_HEIGHT",
            "OBJECT_NAME",
            "OBJECT_DIR",
            "OBJECT_URDF_FILE",
            "OBJECT_MESH_FILE",
            "OBJECT_URDF_TEMPLATE",
            "SCENE_XML_FILE",
        ),
    )


def test_runtime_context_matches_mj_conversion_ground_object() -> None:
    robot_config = RobotConfig(robot_type="g1")
    motion_data_config = MotionDataConfig(data_format="smplh", robot_type="g1")

    expected = convert_data_format_mj.create_task_constants(
        robot_config=robot_config,
        motion_data_config=motion_data_config,
        object_name="ground",
    )
    actual = build_mj_conversion_runtime_context(
        robot_config=robot_config,
        motion_data_config=motion_data_config,
        object_name="ground",
    ).to_legacy_namespace()

    _assert_namespace_fields_equal(
        actual,
        expected,
        (
            "ROBOT_DOF",
            "ROBOT_HEIGHT",
            "ROBOT_NAME",
            "ROBOT_URDF_FILE",
            "FOOT_STICKING_LINKS",
            "MANUAL_LB",
            "MANUAL_UB",
            "MANUAL_COST",
            "NOMINAL_TRACKING_INDICES",
            "DEMO_JOINTS",
            "JOINTS_MAPPING",
            "TOE_NAMES",
            "DEFAULT_SCALE_FACTOR",
            "DEFAULT_HUMAN_HEIGHT",
            "OBJECT_NAME",
            "OBJECT_DIR",
            "OBJECT_URDF_FILE",
            "OBJECT_MESH_FILE",
            "OBJECT_URDF_TEMPLATE",
            "SCENE_XML_FILE",
        ),
    )


def test_runtime_context_matches_mj_conversion_largebox_object() -> None:
    robot_config = RobotConfig(robot_type="g1")
    motion_data_config = MotionDataConfig(data_format="smplh", robot_type="g1")

    expected = convert_data_format_mj.create_task_constants(
        robot_config=robot_config,
        motion_data_config=motion_data_config,
        object_name="largebox",
    )
    actual = build_mj_conversion_runtime_context(
        robot_config=robot_config,
        motion_data_config=motion_data_config,
        object_name="largebox",
    ).to_legacy_namespace()

    _assert_namespace_fields_equal(
        actual,
        expected,
        (
            "ROBOT_DOF",
            "ROBOT_HEIGHT",
            "ROBOT_NAME",
            "ROBOT_URDF_FILE",
            "FOOT_STICKING_LINKS",
            "MANUAL_LB",
            "MANUAL_UB",
            "MANUAL_COST",
            "NOMINAL_TRACKING_INDICES",
            "DEMO_JOINTS",
            "JOINTS_MAPPING",
            "TOE_NAMES",
            "DEFAULT_SCALE_FACTOR",
            "DEFAULT_HUMAN_HEIGHT",
            "OBJECT_NAME",
            "OBJECT_DIR",
            "OBJECT_URDF_FILE",
            "OBJECT_MESH_FILE",
            "OBJECT_URDF_TEMPLATE",
            "SCENE_XML_FILE",
        ),
    )
