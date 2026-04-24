import numpy as np

from holosoma_retargeting.retargeter import interaction_mesh
from holosoma_retargeting.utils import transform


def test_interaction_mesh_helpers_are_available_from_retargeter_module() -> None:
    assert callable(interaction_mesh.create_interaction_mesh)
    assert callable(interaction_mesh.get_adjacency_list)
    assert callable(interaction_mesh.calculate_laplacian_coordinates)
    assert callable(interaction_mesh.calculate_laplacian_matrix)


def test_local_world_point_transform_roundtrip() -> None:
    quat = np.array([0.9238795325, 0.0, 0.0, 0.3826834324])
    trans = np.array([1.0, -2.0, 0.5])
    points_local = np.array([[0.0, 0.0, 0.0], [1.0, 2.0, 3.0], [-0.5, 0.25, 2.0]])

    points_world = transform.transform_points_local_to_world(quat, trans, points_local)
    roundtripped = transform.transform_points_world_to_local(quat, trans, points_world)

    np.testing.assert_allclose(roundtripped, points_local, atol=1e-10)
