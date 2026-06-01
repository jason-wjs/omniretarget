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
