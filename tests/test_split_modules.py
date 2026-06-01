from __future__ import annotations

import numpy as np


def test_laplacian_module_builds_expected_tetrahedron_adjacency_and_matrix():
    from omniretarget.solver import laplacian

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
    assert [sorted(values) for values in adj_list] == [
        [1, 2, 3],
        [0, 2, 3],
        [0, 1, 3],
        [0, 1, 2],
    ]

    expected_matrix = np.array(
        [
            [1.0, -1.0 / 3.0, -1.0 / 3.0, -1.0 / 3.0],
            [-1.0 / 3.0, 1.0, -1.0 / 3.0, -1.0 / 3.0],
            [-1.0 / 3.0, -1.0 / 3.0, 1.0, -1.0 / 3.0],
            [-1.0 / 3.0, -1.0 / 3.0, -1.0 / 3.0, 1.0],
        ]
    )
    np.testing.assert_allclose(laplacian.calculate_laplacian_matrix(vertices, adj_list), expected_matrix)


def test_spatial_module_round_trips_points_between_local_and_world():
    from omniretarget.retargeting import spatial

    quat = np.array([1.0, 0.0, 0.0, 0.0])
    trans = np.array([0.25, -0.5, 1.5])
    points_local = np.array([[0.0, 0.0, 0.0], [1.0, 2.0, 3.0]])

    world = spatial.transform_points_local_to_world(quat, trans, points_local)
    local = spatial.transform_points_world_to_local(quat, trans, world)

    np.testing.assert_allclose(local, points_local)


def test_human_to_world_transform_uses_human_object_direction_as_x_axis():
    from omniretarget.retargeting import spatial

    human_initial_root = np.array([0.0, 0.0, 0.0])
    object_initial_pose = np.array([0.0, 0.0, 0.0, 1.0, 2.0, 0.0, 0.5])
    local_translation = np.array([0.2, 0.1, 0.0])

    world, quat = spatial.transform_from_human_to_world(
        human_initial_root,
        object_initial_pose,
        local_translation,
    )

    np.testing.assert_allclose(world, np.array([0.2, 0.1, 0.0]))
    np.testing.assert_allclose(quat, np.array([1.0, 0.0, 0.0, 0.0]))


def test_motion_data_module_transforms_y_up_points_to_z_up():
    from omniretarget.retargeting import motion_data

    points = np.array(
        [
            [[1.0, 2.0, 3.0], [4.0, 5.0, 6.0]],
            [[-1.0, -2.0, -3.0], [7.0, 8.0, 9.0]],
        ]
    )

    expected = np.array(
        [
            [[1.0, 3.0, 2.0], [4.0, 6.0, 5.0]],
            [[-1.0, -3.0, -2.0], [7.0, 9.0, 8.0]],
        ]
    )
    np.testing.assert_allclose(motion_data.transform_y_up_to_z_up(points), expected)


def test_motion_data_module_extracts_velocity_contacts_for_named_toes():
    from omniretarget.retargeting import motion_data

    joints = np.array(
        [
            [[0.0, 0.0, 0.0], [1.0, 0.0, 0.0]],
            [[0.001, 0.0, 0.0], [1.5, 0.0, 0.0]],
            [[0.002, 0.0, 0.0], [2.0, 0.0, 0.0]],
        ]
    )
    demo_joints = ["left_toe", "right_toe"]
    foot_names = ["left_toe", "right_toe"]

    assert motion_data.extract_foot_sticking_sequence_velocity(joints, demo_joints, foot_names) == [
        {"left_toe": False, "right_toe": False},
        {"left_toe": True, "right_toe": False},
        {"left_toe": True, "right_toe": False},
    ]


def test_object_assets_module_weights_top_surfaces():
    from omniretarget.retargeting import object_assets

    weight = object_assets.create_top_surface_weight_function(angle_threshold=30)

    assert weight(np.array([0.0, 0.0, 1.0]), np.array([0.0, 0.0, 1.0])) == 20.0
    assert weight(np.array([0.0, 0.0, 1.0]), np.array([0.0, 0.0, 0.1])) == 1.0
    assert weight(np.array([1.0, 0.0, 0.0]), np.array([0.0, 0.0, 0.1])) == 1.0
    assert weight(np.array([0.0, 0.0, -1.0]), np.array([0.0, 0.0, 0.1])) == 0.1


def test_object_assets_module_scales_points_in_object_axes_frame():
    from omniretarget.retargeting import object_assets

    points = np.array([[1.0, 2.0, 3.0], [-1.0, -2.0, -3.0]])
    scale_factors = np.array([2.0, 0.5, 1.5])
    object_axes = np.eye(3)

    np.testing.assert_allclose(
        object_assets.scale_points_in_object_axes_frame(points, scale_factors, object_axes),
        np.array([[2.0, 1.0, 4.5], [-2.0, -1.0, -4.5]]),
    )
