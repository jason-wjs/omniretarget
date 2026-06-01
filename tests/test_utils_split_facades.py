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
