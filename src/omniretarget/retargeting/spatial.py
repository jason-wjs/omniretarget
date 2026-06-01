from __future__ import annotations

import numpy as np
import trimesh
from scipy.spatial.transform import Rotation as R  # type: ignore[import-untyped]  # noqa: N817


def augment_object_poses(
    object_poses,
    object_moving_frame_idx,
    human_initial_root,
    local_translation=None,
    rotation_initial=0,
    translation_tau=50,
    rotation_tau=25,
):
    """
    Augment object poses with translation and rotation.

    Args:
        object_poses (np.ndarray): Original object poses array.
        object_moving_frame_idx (int): Index of first moving frame.
        human_initial_root (np.ndarray): Initial human root position.
        local_translation (np.ndarray): Translation vector in human frame.
        rotation_initial (float): Initial rotation angle.

    Returns:
        np.ndarray: Augmented object poses.
    """

    if local_translation is None:
        local_translation = np.array([0, 0, 0])

    N = len(object_poses)
    object_poses_augmented = object_poses.copy()

    if (local_translation != 0).any():
        world_translation, _ = transform_from_human_to_world(human_initial_root, object_poses[0], local_translation)
        object_poses_augmented[:object_moving_frame_idx, -3:] += world_translation
        object_poses_augmented[object_moving_frame_idx:, -3:] += (
            world_translation
            * np.exp(
                (object_moving_frame_idx - np.arange(object_moving_frame_idx, len(object_poses))) / translation_tau
            )[:, None]
        )

    if rotation_initial != 0:
        rotation_list = np.zeros(N)
        rotation_list[:] = rotation_initial
        rotation_list[object_moving_frame_idx:] = rotation_initial * np.exp(
            (object_moving_frame_idx - np.arange(object_moving_frame_idx, N)) / rotation_tau
        )
        rotation = R.from_euler("z", rotation_list)
        object_quat = R.from_quat(object_poses[:, :4], scalar_first=True)
        object_quat_rotated = (rotation * object_quat).as_quat(scalar_first=True)
        object_poses_augmented[:, :4] = object_quat_rotated

    return object_poses_augmented


def transform_from_human_to_world(human_initial_root, object_initial_pose, local_translation):
    """
    Transform translation into a world frame coordinate system.

    Human frame definition:
    - Origin: human_initial_root
    - X-axis: Vector from human_initial_root[:2] to object_initial_pose[:2]
    - Z-axis: Pointing upwards [0, 0, 1]
    - Y-axis: Cross product of Z and X (right-handed coordinate system)

    Args:
        human_initial_root (np.ndarray): Human joint positions with shape (3).
        object_initial_pose (np.ndarray): Object poses with shape (7) [x, y, z, qw, qx, qy, qz].
        local_translation (np.ndarray): Local translation with shape (3).

    Returns:
        tuple: (world_translation, quaternion) - transformed translation and rotation.
    """
    human_to_object_2d = object_initial_pose[-3:-1] - human_initial_root[:2]
    norm = np.linalg.norm(human_to_object_2d)
    if norm < 1e-8:
        x_axis_2d = np.array([1.0, 0.0])
    else:
        x_axis_2d = human_to_object_2d / norm
    x_axis = np.array([x_axis_2d[0], x_axis_2d[1], 0.0])
    z_axis = np.array([0.0, 0.0, 1.0])
    y_axis = np.cross(z_axis, x_axis)
    y_axis = y_axis / np.linalg.norm(y_axis)

    rotation_matrix = np.column_stack([x_axis, y_axis, z_axis])
    quat = R.from_matrix(rotation_matrix).as_quat(scalar_first=True)
    return rotation_matrix @ local_translation, quat


def transform_points_world_to_local(quat, trans, points_world):
    """
    Transform points from world frame to local frame.

    Args:
        quat (np.ndarray): Object quaternion [qw, qx, qy, qz] (scalar-last format).
        trans (np.ndarray): Object translation [x, y, z] in world frame.
        points_world (np.ndarray): Points in world frame, shape (N, 3).

    Returns:
        np.ndarray: Points in local frame, shape (N, 3).
    """
    transform_matrix = trimesh.transformations.quaternion_matrix(quat)
    transform_matrix[:3, 3] = trans
    inverse_transform_matrix = np.linalg.inv(transform_matrix)

    hom_points = np.hstack([points_world, np.ones((points_world.shape[0], 1))])
    transformed_points_hom = (inverse_transform_matrix @ hom_points.T).T
    return transformed_points_hom[:, :3]


def transform_points_local_to_world(quat, trans, points_local):
    """Transform points from local frame to world frame."""
    transform_matrix = trimesh.transformations.quaternion_matrix(quat)
    transform_matrix[:3, 3] = trans
    hom_points = np.hstack([points_local, np.ones((points_local.shape[0], 1))])
    transformed_points_hom = (transform_matrix @ hom_points.T).T
    return transformed_points_hom[:, :3]
