from __future__ import annotations

import numpy as np


def test_laplacian_module_matches_legacy_utils():
    from omniretarget.solver import laplacian
    from omniretarget.src import utils as legacy_utils

    vertices = np.array(
        [
            [0.0, 0.0, 0.0],
            [1.0, 0.0, 0.0],
            [0.0, 1.0, 0.0],
            [0.0, 0.0, 1.0],
        ]
    )
    tetrahedra = np.array([[0, 1, 2, 3]])

    _, generated_tetrahedra = laplacian.create_interaction_mesh(vertices)
    assert generated_tetrahedra.shape[1] == 4

    adj_list = laplacian.get_adjacency_list(tetrahedra, len(vertices))
    expected_adj_list = legacy_utils.get_adjacency_list(tetrahedra, len(vertices))
    assert [sorted(values) for values in adj_list] == [sorted(values) for values in expected_adj_list]

    np.testing.assert_allclose(
        laplacian.calculate_laplacian_coordinates(vertices, adj_list),
        legacy_utils.calculate_laplacian_coordinates(vertices, expected_adj_list),
    )
    np.testing.assert_allclose(
        laplacian.calculate_laplacian_matrix(vertices, adj_list),
        legacy_utils.calculate_laplacian_matrix(vertices, expected_adj_list),
    )


def test_spatial_module_matches_legacy_utils_round_trip():
    from omniretarget.retargeting import spatial
    from omniretarget.src import utils as legacy_utils

    quat = np.array([1.0, 0.0, 0.0, 0.0])
    trans = np.array([0.25, -0.5, 1.5])
    points_local = np.array([[0.0, 0.0, 0.0], [1.0, 2.0, 3.0]])

    world_new = spatial.transform_points_local_to_world(quat, trans, points_local)
    world_legacy = legacy_utils.transform_points_local_to_world(quat, trans, points_local)
    np.testing.assert_allclose(world_new, world_legacy)

    local_new = spatial.transform_points_world_to_local(quat, trans, world_new)
    local_legacy = legacy_utils.transform_points_world_to_local(quat, trans, world_new)
    np.testing.assert_allclose(local_new, local_legacy)
    np.testing.assert_allclose(local_new, points_local)


def test_human_to_world_transform_matches_legacy_utils():
    from omniretarget.retargeting import spatial
    from omniretarget.src import utils as legacy_utils

    human_initial_root = np.array([0.0, 0.0, 0.0])
    object_initial_pose = np.array([0.0, 0.0, 0.0, 1.0, 2.0, 0.0, 0.5])
    local_translation = np.array([0.2, 0.1, 0.0])

    world_new, quat_new = spatial.transform_from_human_to_world(
        human_initial_root,
        object_initial_pose,
        local_translation,
    )
    world_legacy, quat_legacy = legacy_utils.transform_from_human_to_world(
        human_initial_root,
        object_initial_pose,
        local_translation,
    )

    np.testing.assert_allclose(world_new, world_legacy)
    np.testing.assert_allclose(quat_new, quat_legacy)


def test_motion_data_module_matches_legacy_y_up_transform():
    from omniretarget.retargeting import motion_data
    from omniretarget.src import utils as legacy_utils

    points = np.array(
        [
            [[1.0, 2.0, 3.0], [4.0, 5.0, 6.0]],
            [[-1.0, -2.0, -3.0], [7.0, 8.0, 9.0]],
        ]
    )

    np.testing.assert_allclose(
        motion_data.transform_y_up_to_z_up(points),
        legacy_utils.transform_y_up_to_z_up(points),
    )


def test_motion_data_module_matches_legacy_velocity_contacts():
    from omniretarget.retargeting import motion_data
    from omniretarget.src import utils as legacy_utils

    joints = np.array(
        [
            [[0.0, 0.0, 0.0], [1.0, 0.0, 0.0]],
            [[0.001, 0.0, 0.0], [1.5, 0.0, 0.0]],
            [[0.002, 0.0, 0.0], [2.0, 0.0, 0.0]],
        ]
    )
    demo_joints = ["left_toe", "right_toe"]
    foot_names = ["left_toe", "right_toe"]

    assert motion_data.extract_foot_sticking_sequence_velocity(joints, demo_joints, foot_names) == (
        legacy_utils.extract_foot_sticking_sequence_velocity(joints, demo_joints, foot_names)
    )


def test_object_assets_module_matches_legacy_top_surface_weights():
    from omniretarget.retargeting import object_assets
    from omniretarget.src import utils as legacy_utils

    new_weight = object_assets.create_top_surface_weight_function(angle_threshold=30)
    legacy_weight = legacy_utils.create_top_surface_weight_function(angle_threshold=30)

    top_normal = np.array([0.0, 0.0, 1.0])
    side_normal = np.array([1.0, 0.0, 0.0])
    down_normal = np.array([0.0, 0.0, -1.0])
    high_center = np.array([0.0, 0.0, 1.0])
    low_center = np.array([0.0, 0.0, 0.1])

    assert new_weight(top_normal, high_center) == legacy_weight(top_normal, high_center)
    assert new_weight(top_normal, low_center) == legacy_weight(top_normal, low_center)
    assert new_weight(side_normal, low_center) == legacy_weight(side_normal, low_center)
    assert new_weight(down_normal, low_center) == legacy_weight(down_normal, low_center)


def test_object_assets_module_matches_legacy_axis_scaling():
    from omniretarget.retargeting import object_assets
    from omniretarget.src import utils as legacy_utils

    points = np.array([[1.0, 2.0, 3.0], [-1.0, -2.0, -3.0]])
    scale_factors = np.array([2.0, 0.5, 1.5])
    object_axes = np.eye(3)

    np.testing.assert_allclose(
        object_assets.scale_points_in_object_axes_frame(points, scale_factors, object_axes),
        legacy_utils.scale_points_in_object_axes_frame(points, scale_factors, object_axes),
    )
