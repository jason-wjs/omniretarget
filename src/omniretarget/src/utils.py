"""Compatibility re-exports for legacy utility imports."""

from __future__ import annotations

from omniretarget.retargeting.motion_data import (
    calculate_scale_factor,
    estimate_human_orientation,
    extract_foot_sticking_sequence,
    extract_foot_sticking_sequence_velocity,
    extract_object_first_moving_frame,
    find_standing_pose,
    load_intermimic_data,
    load_smpl_motion,
    preprocess_motion_data,
    transform_y_up_to_z_up,
)
from omniretarget.retargeting.object_assets import (
    create_new_scene_xml_file,
    create_scaled_multi_boxes_urdf,
    create_scaled_multi_boxes_xml,
    create_scaled_object_mesh_and_urdf,
    create_top_surface_weight_function,
    load_object_data,
    scale_points_in_object_axes_frame,
    weighted_surface_sampling,
    weighted_surface_sampling_by_face_normal,
)
from omniretarget.retargeting.spatial import (
    augment_object_poses,
    transform_from_human_to_world,
    transform_points_local_to_world,
    transform_points_world_to_local,
)
from omniretarget.solver.laplacian import (
    calculate_laplacian_coordinates,
    calculate_laplacian_matrix,
    create_interaction_mesh,
    get_adjacency_list,
)

__all__ = [
    "augment_object_poses",
    "calculate_laplacian_coordinates",
    "calculate_laplacian_matrix",
    "calculate_scale_factor",
    "create_interaction_mesh",
    "create_new_scene_xml_file",
    "create_scaled_multi_boxes_urdf",
    "create_scaled_multi_boxes_xml",
    "create_scaled_object_mesh_and_urdf",
    "create_top_surface_weight_function",
    "estimate_human_orientation",
    "extract_foot_sticking_sequence",
    "extract_foot_sticking_sequence_velocity",
    "extract_object_first_moving_frame",
    "find_standing_pose",
    "get_adjacency_list",
    "load_intermimic_data",
    "load_object_data",
    "load_smpl_motion",
    "preprocess_motion_data",
    "scale_points_in_object_axes_frame",
    "transform_from_human_to_world",
    "transform_points_local_to_world",
    "transform_points_world_to_local",
    "transform_y_up_to_z_up",
    "weighted_surface_sampling",
    "weighted_surface_sampling_by_face_normal",
]
