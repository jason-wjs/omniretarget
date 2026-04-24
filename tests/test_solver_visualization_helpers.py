from __future__ import annotations

import builtins
import importlib
import sys
import types

import numpy as np


def _install_visualization_stubs(monkeypatch) -> None:
    trimesh_module = types.ModuleType("trimesh")
    trimesh_module.primitives = types.SimpleNamespace(
        Sphere=lambda radius: types.SimpleNamespace(
            vertices=np.array([[0.0, 0.0, 0.0]], dtype=float),
            faces=np.array([[0, 0, 0]], dtype=int),
        )
    )
    monkeypatch.setitem(sys.modules, "trimesh", trimesh_module)

    viser_module = types.ModuleType("viser")
    viser_module.ViserServer = object
    monkeypatch.setitem(sys.modules, "viser", viser_module)

    viser_extras_module = types.ModuleType("viser.extras")
    viser_extras_module.ViserUrdf = object
    monkeypatch.setitem(sys.modules, "viser.extras", viser_extras_module)

    yourdfpy_module = types.ModuleType("yourdfpy")
    yourdfpy_module.URDF = types.SimpleNamespace(load=lambda *args, **kwargs: object())
    monkeypatch.setitem(sys.modules, "yourdfpy", yourdfpy_module)

    mujoco_utils_module = types.ModuleType("holosoma_retargeting.utils.mujoco_utils")
    mujoco_utils_module._world_mesh_from_geom = lambda *args, **kwargs: (
        np.zeros((0, 3), dtype=float),
        np.zeros((0, 3), dtype=int),
    )
    monkeypatch.setitem(sys.modules, "holosoma_retargeting.utils.mujoco_utils", mujoco_utils_module)

    viser_utils_module = types.ModuleType("holosoma_retargeting.utils.viser_utils")
    viser_utils_module.create_motion_control_sliders = lambda **kwargs: None
    monkeypatch.setitem(sys.modules, "holosoma_retargeting.utils.viser_utils", viser_utils_module)


def test_draw_keypoints_returns_empty_list_without_server(monkeypatch) -> None:
    _install_visualization_stubs(monkeypatch)
    monkeypatch.delitem(sys.modules, "holosoma_retargeting.solver.visualization", raising=False)
    visualization = importlib.import_module("holosoma_retargeting.solver.visualization")

    retargeter = types.SimpleNamespace()

    assert visualization.draw_keypoints(retargeter, np.array([1.0, 2.0, 3.0])) == []


def test_visualize_motion_uses_color_keyword_for_tetrahedra(monkeypatch) -> None:
    _install_visualization_stubs(monkeypatch)
    monkeypatch.delitem(sys.modules, "holosoma_retargeting.solver.visualization", raising=False)
    visualization = importlib.import_module("holosoma_retargeting.solver.visualization")

    monkeypatch.setattr(builtins, "input", lambda: "")
    tetrahedra_calls: list[dict[str, object]] = []
    draw_calls: list[tuple[str, object]] = []

    retargeter = types.SimpleNamespace(
        smplh_mapped_joint_indices=[0],
        laplacian_match_links={"robot": "robot"},
        draw_keypoints=lambda points, name="keypoint", rgba=(0, 0, 1, 1): draw_calls.append((name, rgba)),
        draw_q=lambda q: None,
        _get_robot_link_positions=lambda q, links: np.array([[0.5, 0.5, 0.5]], dtype=float),
        visualize_tetrahedra=lambda vertices, tetrahedra, name="tetrahedra", color=(0, 0, 0, 1): tetrahedra_calls.append(
            {"name": name, "color": color}
        ),
    )

    visualization.visualize_motion(
        retargeter,
        human_joint_motions=np.array([[[0.0, 0.0, 0.0]]], dtype=float),
        obj_pts_demo=[np.array([[1.0, 0.0, 0.0]], dtype=float)],
        obj_pts=[np.array([[0.0, 1.0, 0.0]], dtype=float)],
        retargeted_motions=np.array([[0.0] * 8], dtype=float),
        tetrahedra=[np.array([[0, 0, 0, 0]], dtype=int)],
        visualize_tetrahedra=True,
    )

    assert [call["name"] for call in tetrahedra_calls] == ["human_tetrahedra", "robot_tetrahedra"]
    assert tetrahedra_calls[1]["color"] == (0, 1, 1, 1)


def test_interaction_mesh_retargeter_import_does_not_eagerly_import_visualization(monkeypatch) -> None:
    monkeypatch.delitem(sys.modules, "holosoma_retargeting.solver.interaction_mesh_retargeter", raising=False)
    monkeypatch.delitem(sys.modules, "holosoma_retargeting.solver.visualization", raising=False)

    cvxpy_module = types.ModuleType("cvxpy")
    cvxpy_module.OPTIMAL = "optimal"
    cvxpy_module.OPTIMAL_INACCURATE = "optimal_inaccurate"
    monkeypatch.setitem(sys.modules, "cvxpy", cvxpy_module)

    mujoco_module = types.ModuleType("mujoco")
    mujoco_module.MjModel = object
    mujoco_module.MjData = object
    mujoco_module.mjtJoint = types.SimpleNamespace(mjJNT_HINGE=0, mjJNT_SLIDE=1)
    monkeypatch.setitem(sys.modules, "mujoco", mujoco_module)

    scipy_sparse_module = types.ModuleType("scipy.sparse")
    scipy_sparse_module.issparse = lambda value: False
    scipy_sparse_module.csr_matrix = lambda value: value
    scipy_sparse_module.kron = lambda a, b, format=None: None
    scipy_sparse_module.eye = lambda *args, **kwargs: None
    monkeypatch.setitem(sys.modules, "scipy.sparse", scipy_sparse_module)

    scipy_transform_module = types.ModuleType("scipy.spatial.transform")
    scipy_transform_module.Rotation = object
    monkeypatch.setitem(sys.modules, "scipy.spatial.transform", scipy_transform_module)

    tqdm_module = types.ModuleType("tqdm")
    tqdm_module.tqdm = lambda iterable, *args, **kwargs: iterable
    monkeypatch.setitem(sys.modules, "tqdm", tqdm_module)

    transforms_module = types.ModuleType("holosoma_retargeting.utils.transforms")
    transforms_module.calculate_laplacian_coordinates = lambda *args, **kwargs: None
    transforms_module.calculate_laplacian_matrix = lambda *args, **kwargs: None
    transforms_module.create_interaction_mesh = lambda *args, **kwargs: (None, None)
    transforms_module.get_adjacency_list = lambda *args, **kwargs: None
    transforms_module.transform_points_local_to_world = lambda *args, **kwargs: None
    transforms_module.transform_points_world_to_local = lambda *args, **kwargs: None
    monkeypatch.setitem(sys.modules, "holosoma_retargeting.utils.transforms", transforms_module)

    importlib.import_module("holosoma_retargeting.solver.interaction_mesh_retargeter")

    assert "holosoma_retargeting.solver.visualization" not in sys.modules
