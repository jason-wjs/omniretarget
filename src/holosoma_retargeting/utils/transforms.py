"""Transform and geometry helpers for utility-layer decomposition."""

from __future__ import annotations

import numpy as np
from scipy.spatial import Delaunay  # type: ignore[import-untyped]
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
        object_initial_pose (np.ndarray): Object pose with shape (7) [qw, qx, qy, qz, x, y, z].
        local_translation (np.ndarray): Local translation with shape (3).

    Returns:
        tuple: (world_translation, quaternion) - transformed translation and rotation.
    """
    human_to_object_2d = object_initial_pose[-3:-1] - human_initial_root[:2]
    x_axis_2d = human_to_object_2d / np.linalg.norm(human_to_object_2d)
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
        quat (np.ndarray): Object quaternion [qw, qx, qy, qz] in scalar-first format.
        trans (np.ndarray): Object translation [x, y, z] in world frame.
        points_world (np.ndarray): Points in world frame, shape (N, 3).

    Returns:
        np.ndarray: Points in local frame, shape (N, 3).
    """
    from trimesh.transformations import quaternion_matrix  # type: ignore[import-not-found]

    transform_matrix = quaternion_matrix(quat)
    transform_matrix[:3, 3] = trans
    inverse_transform_matrix = np.linalg.inv(transform_matrix)

    hom_points = np.hstack([points_world, np.ones((points_world.shape[0], 1))])
    transformed_points_hom = (inverse_transform_matrix @ hom_points.T).T
    return transformed_points_hom[:, :3]


def transform_points_local_to_world(quat, trans, points_local):
    """Transform points from local frame to world frame."""
    from trimesh.transformations import quaternion_matrix  # type: ignore[import-not-found]

    transform_matrix = quaternion_matrix(quat)
    transform_matrix[:3, 3] = trans
    hom_points = np.hstack([points_local, np.ones((points_local.shape[0], 1))])
    transformed_points_hom = (transform_matrix @ hom_points.T).T
    return transformed_points_hom[:, :3]


def create_interaction_mesh(vertices: np.ndarray):
    """
    Creates a tetrahedral mesh from human and object points using Delaunay triangulation.

    Args:
        vertices (np.ndarray): (num_vertices, 3) array.

    Returns:
        tuple: (vertices, tetrahedra) - combined points and generated tetrahedra.
    """
    tri = Delaunay(vertices)
    return vertices, tri.simplices


def get_adjacency_list(tetrahedra, num_vertices):
    """Creates an adjacency list from the tetrahedra."""
    adj = [set() for _ in range(num_vertices)]
    for tet in tetrahedra:
        for i in range(4):
            for j in range(i + 1, 4):
                u, v = tet[i], tet[j]
                adj[u].add(v)
                adj[v].add(u)
    return [list(s) for s in adj]


def calculate_laplacian_coordinates(vertices, adj_list, epsilon=1e-6, uniform_weight=True):
    """
    Calculates the Laplacian coordinates for each vertex in the mesh.

    Args:
        vertices (np.ndarray): (N, 3) array of vertex positions.
        adj_list (list of lists): Adjacency list for the mesh.
        epsilon (float): Small value to prevent division by zero.
        uniform_weight (bool): Whether to use uniform weights.

    Returns:
        np.ndarray: (N, 3) array of Laplacian coordinates.
    """
    laplacian = np.zeros_like(vertices)

    for i in range(len(vertices)):
        neighbors_indices = adj_list[i]
        if len(neighbors_indices) > 0:
            vi = vertices[i]
            neighbor_positions = vertices[neighbors_indices]
            distances = np.linalg.norm(vi - neighbor_positions, axis=1)

            if uniform_weight:
                weights = np.ones_like(distances)
            else:
                weights = 1.0 / (1.5 * distances + epsilon)

            sum_of_weights = np.sum(weights)
            weighted_sum_of_neighbors = np.sum(weights[:, np.newaxis] * neighbor_positions, axis=0)
            center_of_neighbors = weighted_sum_of_neighbors / sum_of_weights
            laplacian[i] = vi - center_of_neighbors

    return laplacian


def calculate_laplacian_matrix(vertices, adj_list, epsilon=1e-6, uniform_weight=True):
    """
    Calculates the Laplacian matrix for the mesh with optional weight schemes.

    Args:
        vertices (np.ndarray): (N, 3) array of vertex positions.
        adj_list (list of lists): Adjacency list for the mesh.
        epsilon (float): Small value to prevent division by zero.
        uniform_weight (bool): If True, use uniform weights; if False, use distance-based weights.

    Returns:
        np.ndarray: (N, N) Laplacian matrix.
    """
    N = len(vertices)
    laplacian_matrix = np.zeros((N, N))

    for i in range(N):
        neighbors_indices = adj_list[i]
        if len(neighbors_indices) > 0:
            if uniform_weight:
                weights = np.ones(len(neighbors_indices)) / len(neighbors_indices)
            else:
                vi = vertices[i]
                neighbor_positions = vertices[neighbors_indices]
                distances = np.linalg.norm(vi - neighbor_positions, axis=1)
                weights = 1.0 / (distances + epsilon)
                sum_weights = np.sum(weights)
                weights = weights / sum_weights

            laplacian_matrix[i, i] = 1.0

            for j, neighbor_idx in enumerate(neighbors_indices):
                laplacian_matrix[i, neighbor_idx] = -weights[j]

    return laplacian_matrix


def find_standing_pose(q: np.ndarray):
    """Find standing pose from current configuration q."""
    q_standing = np.copy(q)
    # rpy_vector = RollPitchYaw(Quaternion(q[:4])).vector()
    # standing_quat = RollPitchYaw(0, 0, rpy_vector[2]).ToQuaternion()
    # quat = standing_quat.wxyz()
    # if np.dot(quat, q[:4]) < 0:
    #     quat = -quat
    # q_standing[:4] = quat
    # q_standing[6] = 0.76  # slightly shorter than the height of G1 pelvis due to bending
    # q_standing[7 : 7 + 29] = Q_A_STANDING
    q_standing[19:22] = 0.0
    return q_standing
