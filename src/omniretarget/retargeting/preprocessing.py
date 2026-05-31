from __future__ import annotations

from typing import Any

import numpy as np

from omniretarget.src.utils import extract_foot_sticking_sequence_velocity, preprocess_motion_data


def preprocess_retargeting_motion(
    *,
    task_type: str,
    data_format: str,
    human_joints: np.ndarray,
    object_poses: np.ndarray,
    retargeter: Any,
    toe_names: list[str],
    smpl_scale: float,
) -> tuple[np.ndarray, np.ndarray, int | None]:
    """Preprocess human/object motion while preserving task-specific height rules."""
    if task_type == "robot_only":
        ground_height_percentile = 5.0 if data_format == "optitrack" else 0.0
        mat_height = 0.0 if data_format == "optitrack" else 0.1
        human_joints = preprocess_motion_data(
            human_joints,
            retargeter,
            toe_names,
            smpl_scale,
            mat_height=mat_height,
            ground_height_percentile=ground_height_percentile,
        )
        return human_joints, object_poses, None

    if task_type in {"object_interaction", "climbing"}:
        human_joints, object_poses, object_moving_frame_idx = preprocess_motion_data(
            human_joints,
            retargeter,
            toe_names,
            scale=smpl_scale,
            object_poses=object_poses,
            normalize_height=not (task_type == "climbing" and data_format == "parc_humanoid"),
        )
        return human_joints, object_poses, object_moving_frame_idx

    raise ValueError(f"Unknown task type: {task_type}")


def build_foot_sticking_sequences(
    *,
    task_type: str,
    human_joints: np.ndarray,
    demo_joints: list[str],
    toe_names: list[str],
):
    """Build foot-sticking sequences with legacy task-specific adjustments."""
    foot_sticking_sequences = extract_foot_sticking_sequence_velocity(human_joints, demo_joints, toe_names)

    if task_type == "object_interaction":
        foot_sticking_sequences[0][toe_names[0]] = False
        foot_sticking_sequences[0][toe_names[1]] = False

    return foot_sticking_sequences
