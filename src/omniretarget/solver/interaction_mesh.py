from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from omniretarget.src.utils import (
    calculate_laplacian_coordinates,
    create_interaction_mesh,
    get_adjacency_list,
    transform_points_local_to_world,
    transform_points_world_to_local,
)


@dataclass(frozen=True)
class InteractionMeshFrame:
    human_mapped_joints_in_object: np.ndarray
    source_vertices: np.ndarray
    source_tetrahedra: np.ndarray
    adj_list: list[list[int]]
    target_laplacian: np.ndarray
    object_points_demo_world: np.ndarray | None = None
    object_points_world: np.ndarray | None = None


def build_interaction_mesh_frame(
    *,
    object_name: str,
    human_mapped_joints: np.ndarray,
    object_pose_demo: np.ndarray,
    object_pose_augmented: np.ndarray,
    object_points_local_demo: np.ndarray,
    object_points_local: np.ndarray,
    include_debug_points: bool = False,
) -> InteractionMeshFrame:
    """Build one frame's interaction mesh and target Laplacian inputs."""
    object_quat_demo = object_pose_demo[3:]
    object_trans_demo = object_pose_demo[:3]

    if object_name == "ground":
        human_mapped_joints_in_object = human_mapped_joints
    else:
        human_mapped_joints_in_object = transform_points_world_to_local(
            object_quat_demo,
            object_trans_demo,
            human_mapped_joints,
        )

    source_vertices, source_tetrahedra = create_interaction_mesh(
        np.vstack([human_mapped_joints_in_object, object_points_local_demo])
    )
    adj_list = get_adjacency_list(source_tetrahedra, len(source_vertices))
    target_laplacian = calculate_laplacian_coordinates(source_vertices, adj_list)

    object_points_demo_world = None
    object_points_world = None
    if include_debug_points:
        object_quat = object_pose_augmented[3:]
        object_trans = object_pose_augmented[:3]
        object_points_demo_world = transform_points_local_to_world(
            object_quat_demo,
            object_trans_demo,
            object_points_local_demo,
        )
        object_points_world = transform_points_local_to_world(object_quat, object_trans, object_points_local)

    return InteractionMeshFrame(
        human_mapped_joints_in_object=human_mapped_joints_in_object,
        source_vertices=source_vertices,
        source_tetrahedra=source_tetrahedra,
        adj_list=adj_list,
        target_laplacian=target_laplacian,
        object_points_demo_world=object_points_demo_world,
        object_points_world=object_points_world,
    )
