"""Motion preprocessing helpers for utility-layer decomposition."""

from __future__ import annotations

import pickle

import numpy as np
from scipy.spatial.transform import Rotation as R  # type: ignore[import-untyped]  # noqa: N817

from holosoma_retargeting.path_utils import package_path


def calculate_scale_factor(task_name, robot_height):
    """Calculate scale factor based on human height."""
    with package_path("demo_data/height_dict.pkl").open("rb") as f:
        height_dict = pickle.load(f)
    sub_name = task_name.split("_")[0]
    human_height = height_dict[sub_name]
    return robot_height / human_height


def preprocess_motion_data(
    human_joints,
    retargeter,
    foot_names,
    scale=0.714,
    mat_height=0.1,
    ground_height_percentile=0.0,
    object_poses=None,
):
    """
    Preprocess human joints and object poses for retargeting.

    Args:
        human_joints (np.ndarray): Human joint positions.
        retargeter: Retargeting object with demo joint names.
        scale (float): Scaling factor.
        mat_height (float): Mat height offset to subtract when the demo starts on a mat.
        ground_height_percentile (float): Optional robust grounding percentile for toe heights.
        object_poses (np.ndarray | None): Optional object poses in [qw, qx, qy, qz, x, y, z] order.

    Returns:
        np.ndarray | tuple: Scaled human joints, and optionally scaled object poses with first moving frame.
    """
    # Normalize human joint heights
    toe_indices = [
        retargeter.demo_joints.index(foot_names[0]),
        retargeter.demo_joints.index(foot_names[1]),
    ]
    toe_heights = human_joints[:, toe_indices, 2].reshape(-1)
    if ground_height_percentile > 0:
        # Use "higher" to avoid interpolation pulling the floor down from sparse outliers.
        try:
            z_min = float(np.percentile(toe_heights, ground_height_percentile, method="higher"))
        except TypeError:
            z_min = float(np.percentile(toe_heights, ground_height_percentile, interpolation="higher"))
    else:
        z_min = float(toe_heights.min())

    if z_min >= mat_height:
        # On a mat.
        z_min -= mat_height
    human_joints[:, :, 2] -= z_min

    # Scale human joints
    human_joints = human_joints * scale

    if object_poses is not None:
        object_poses[:, -3:-1] = object_poses[:, -3:-1] * scale
        object_z0 = object_poses[0, -1]
        dz_scale = (object_poses[:, -1] - object_z0) * scale
        object_poses[:, -1] = object_z0 + dz_scale

        object_moving_frame_idx = extract_object_first_moving_frame(object_poses)

        return human_joints, object_poses, object_moving_frame_idx

    return human_joints


def extract_object_first_moving_frame(object_poses, vel_threshold=0.0025):
    """Extract the first frame where the object starts moving."""
    object_vel = np.diff(object_poses, axis=0)
    object_vel_norm = np.linalg.norm(object_vel, axis=1)
    return np.argmax(object_vel_norm > vel_threshold)


def transform_y_up_to_z_up(points):
    """
    Transform points from y-up to z-up coordinate system.

    Transformation:
    - Y-axis (up) becomes Z-axis (up)
    - Z-axis (forward) becomes Y-axis (forward)
    - X-axis (right) stays X-axis (right)

    Args:
        points (np.ndarray): Points with shape (..., 3) where last dimension is [x, y, z]

    Returns:
        np.ndarray: Transformed points with shape (..., 3) where last dimension is [x, y, z]
    """
    # Create transformation matrix
    # [x, y, z] -> [x, z, y]
    transform_matrix = np.array([[1, 0, 0], [0, 0, 1], [0, 1, 0]])

    # Apply transformation
    if points.ndim == 1:
        return transform_matrix @ points
    if points.ndim == 2:
        return (transform_matrix @ points.T).T
    if points.ndim == 3:
        original_shape = points.shape
        points_reshaped = points.reshape(-1, 3)
        transformed = (transform_matrix @ points_reshaped.T).T
        return transformed.reshape(original_shape)
    raise ValueError(f"Unsupported number of dimensions: {points.ndim}")


def estimate_human_orientation(human_joints, joint_names, frame_idx=0):
    """
    Estimate the human's global orientation quaternion based on joint positions.

    This function estimates the human's orientation by looking at the direction
    from the pelvis (Hips) to the spine/chest, and the direction from left to right hip.

    Args:
        human_joints (np.ndarray): Human joint positions with shape (frames, joints, 3)
        joint_names (list): List of joint names corresponding to the joint positions
        frame_idx (int): Frame index to estimate orientation from (default: 0)

    Returns:
        np.ndarray: Quaternion [w, x, y, z] representing the human's global orientation
    """
    # For LAFAN
    if "Hips" in joint_names:
        hips_idx = joint_names.index("Hips")
        spine_idx = joint_names.index("Spine")
        left_hip_idx = joint_names.index("LeftUpLeg")
        right_hip_idx = joint_names.index("RightUpLeg")
    else:
        # For SMPLH (OMOMO_new)
        hips_idx = joint_names.index("Pelvis")
        spine_idx = joint_names.index("Spine")
        left_hip_idx = joint_names.index("L_Hip")
        right_hip_idx = joint_names.index("R_Hip")

    hips_pos = human_joints[frame_idx, hips_idx]
    spine_pos = human_joints[frame_idx, spine_idx]
    left_hip_pos = human_joints[frame_idx, left_hip_idx]
    right_hip_pos = human_joints[frame_idx, right_hip_idx]

    # Calculate forward direction (from hips to spine)
    forward_vec = hips_pos - spine_pos
    forward_vec[2] = 0  # Project to horizontal plane (ignore vertical component)
    if np.linalg.norm(forward_vec) > 1e-6:
        forward_vec = forward_vec / np.linalg.norm(forward_vec)
    else:
        # If spine is directly above hips, use a default forward direction
        forward_vec = np.array([0, 1, 0])

    # Calculate right direction (from left hip to right hip)
    left_vec = left_hip_pos - right_hip_pos
    left_vec[2] = 0  # Project to horizontal plane
    if np.linalg.norm(left_vec) > 1e-6:
        left_vec = left_vec / np.linalg.norm(left_vec)
    else:
        # If hips are aligned vertically, use a default right direction
        left_vec = np.array([1, 0, 0])

    # Ensure left_vec is perpendicular to forward_vec
    left_vec = left_vec - np.dot(left_vec, forward_vec) * forward_vec
    if np.linalg.norm(left_vec) > 1e-6:
        left_vec = left_vec / np.linalg.norm(left_vec)
    else:
        # Fallback if vectors are parallel
        left_vec = np.array([1, 0, 0])

    # Calculate up direction (cross product to ensure orthogonality)
    up_vec = np.cross(forward_vec, left_vec)
    up_vec = up_vec / np.linalg.norm(up_vec)
    forward_vec = np.cross(left_vec, up_vec)
    forward_vec = forward_vec / np.linalg.norm(forward_vec)

    rotation_matrix = np.column_stack([forward_vec, left_vec, up_vec])
    assert np.linalg.det(rotation_matrix) > 0
    rotation = R.from_matrix(rotation_matrix)
    return rotation.as_quat(scalar_first=True)
