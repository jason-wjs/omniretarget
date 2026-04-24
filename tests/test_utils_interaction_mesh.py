import numpy as np

from holosoma_retargeting.src import utils as legacy_utils
from holosoma_retargeting.utils import interaction_mesh


def test_interaction_mesh_helpers_reexport_legacy_functions() -> None:
    assert legacy_utils.transform_points_world_to_local is interaction_mesh.transform_points_world_to_local
    assert legacy_utils.transform_points_local_to_world is interaction_mesh.transform_points_local_to_world
    assert legacy_utils.create_interaction_mesh is interaction_mesh.create_interaction_mesh
    assert legacy_utils.get_adjacency_list is interaction_mesh.get_adjacency_list
    assert legacy_utils.calculate_laplacian_coordinates is interaction_mesh.calculate_laplacian_coordinates
    assert legacy_utils.calculate_laplacian_matrix is interaction_mesh.calculate_laplacian_matrix


def test_local_world_point_transform_roundtrip() -> None:
    quat = np.array([0.9238795325, 0.0, 0.0, 0.3826834324])
    trans = np.array([1.0, -2.0, 0.5])
    points_local = np.array([[0.0, 0.0, 0.0], [1.0, 2.0, 3.0], [-0.5, 0.25, 2.0]])

    points_world = interaction_mesh.transform_points_local_to_world(quat, trans, points_local)
    roundtripped = interaction_mesh.transform_points_world_to_local(quat, trans, points_world)

    np.testing.assert_allclose(roundtripped, points_local, atol=1e-10)
