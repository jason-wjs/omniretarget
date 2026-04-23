from __future__ import annotations

import logging
from pathlib import Path
from types import SimpleNamespace

import numpy as np

from holosoma_retargeting.config_types.data_type import MotionDataConfig
from holosoma_retargeting.pipelines.task_setup import TaskType
from holosoma_retargeting.src.utils import (
    calculate_scale_factor,
    load_intermimic_data,
    transform_y_up_to_z_up,
)


logger = logging.getLogger(__name__)


def create_ground_points(x_range: tuple[float, float], y_range: tuple[float, float], size: int) -> np.ndarray:
    """Create ground point meshgrid."""
    x = np.linspace(x_range[0], x_range[1], size)
    y = np.linspace(y_range[0], y_range[1], size)
    X, Y = np.meshgrid(x, y)
    return np.stack([X.flatten(), Y.flatten(), np.zeros_like(X.flatten())], axis=1)


def load_motion_data(
    task_type: TaskType,
    data_format: str,
    data_path: Path,
    task_name: str,
    constants: SimpleNamespace,
    motion_data_config: MotionDataConfig,
) -> tuple[np.ndarray, np.ndarray, float]:
    """Load motion data based on task type and format."""
    logger.info("Loading motion data for task: %s, format: %s", task_name, data_format)

    if task_type == "robot_only":
        if data_format == "lafan":
            npy_path = data_path / f"{task_name}.npy"
            if not npy_path.exists():
                raise FileNotFoundError(f"LAFAN data file not found: {npy_path}")

            human_joints = np.load(str(npy_path))
            human_joints = transform_y_up_to_z_up(human_joints)
            spine_joint_idx = constants.DEMO_JOINTS.index("Spine1")
            # LAFAN-specific spine adjustment.
            human_joints[:, spine_joint_idx, -1] -= 0.06
            # LAFAN data is normalized to ~1.7m subjects; scale per robot height.
            smpl_scale = constants.ROBOT_HEIGHT / 1.7
        elif data_format == "smplh":
            pt_path = data_path / f"{task_name}.pt"
            if not pt_path.exists():
                raise FileNotFoundError(f"InterMimic data file not found: {pt_path}")

            human_joints, object_poses = load_intermimic_data(str(pt_path))
            smpl_scale = calculate_scale_factor(task_name, constants.ROBOT_HEIGHT)
        elif data_format == "mocap":
            downsample = 4
            npy_file = data_path / f"{task_name}.npy"
            if not npy_file.exists():
                raise FileNotFoundError(f"MOCAP data file not found: {npy_file}")

            human_joints = np.load(str(npy_file))[::downsample]

            default_human_height = motion_data_config.default_human_height or 1.78
            smpl_scale = constants.ROBOT_HEIGHT / default_human_height
        elif data_format == "smplx":
            npz_file = data_path / f"{task_name}.npz"

            human_data = np.load(str(npz_file))
            human_joints = human_data["global_joint_positions"]
            human_height = human_data["height"]
            smpl_scale = constants.ROBOT_HEIGHT / human_height
        else:
            # Custom formats can reuse the SMPL-X layout when they provide standard NPZ keys.
            npz_file = data_path / f"{task_name}.npz"

            human_data = np.load(str(npz_file))
            human_joints = human_data["global_joint_positions"]
            human_height = human_data["height"]
            smpl_scale = constants.ROBOT_HEIGHT / human_height

        # Create dummy object poses for robot_only.
        num_frames = human_joints.shape[0]
        object_poses = np.tile(np.array([[1, 0, 0, 0, 0, 0, 0]]), (num_frames, 1))

    elif task_type == "object_interaction":
        pt_path = data_path / f"{task_name}.pt"
        if not pt_path.exists():
            raise FileNotFoundError(f"InterMimic data file not found: {pt_path}")

        human_joints, object_poses = load_intermimic_data(str(pt_path))
        smpl_scale = calculate_scale_factor(task_name, constants.ROBOT_HEIGHT)

    elif task_type == "climbing":
        task_dir = data_path / task_name
        npy_files = list(task_dir.glob("*.npy"))
        if not npy_files:
            raise FileNotFoundError(f"No .npy file found in {task_dir}")

        npy_file = npy_files[0]
        # MOCAP-specific downsample factor.
        downsample = 4
        human_joints = np.load(str(npy_file))[::downsample]
        num_frames = human_joints.shape[0]
        object_poses = np.tile(np.array([[1, 0, 0, 0, 0, 0, 0]]), (num_frames, 1))
        default_human_height = motion_data_config.default_human_height or 1.78
        smpl_scale = constants.ROBOT_HEIGHT / default_human_height

    logger.debug(
        "Loaded %d frames, scale factor: %.4f",
        human_joints.shape[0],
        smpl_scale,
    )
    return human_joints, object_poses, smpl_scale
