from __future__ import annotations

from typing import Any

import numpy as np


def resolve_robot_xml_path(
    robot_model_path: str,
    object_name: str,
    *,
    scene_xml_file: str | None = None,
) -> str:
    """Resolve the MuJoCo XML path using the legacy task object rules."""
    if object_name == "ground":
        return robot_model_path.replace(".urdf", ".xml")
    if object_name == "multi_boxes":
        if scene_xml_file is None:
            raise ValueError("scene_xml_file is required when object_name='multi_boxes'")
        return scene_xml_file
    return robot_model_path.replace(".urdf", f"_w_{object_name}.xml")


def mesh_local_vertices_and_faces(model: Any, geom_id: int) -> tuple[np.ndarray, np.ndarray]:
    """Return local vertices and faces for a MuJoCo mesh geom."""
    mesh_id = int(model.geom_dataid[geom_id])

    v0, nv = int(model.mesh_vertadr[mesh_id]), int(model.mesh_vertnum[mesh_id])
    f0, nf = int(model.mesh_faceadr[mesh_id]), int(model.mesh_facenum[mesh_id])

    vertices = model.mesh_vert[v0 : v0 + nv].astype(np.float64, copy=True)
    faces = model.mesh_face[f0 : f0 + nf].astype(np.int32, copy=True)

    return vertices, faces


def transform_mesh_vertices_to_world(vertices_local: np.ndarray, data: Any, geom_id: int) -> np.ndarray:
    """Transform local MuJoCo mesh vertices into world coordinates."""
    rotation = data.geom_xmat[geom_id].reshape(3, 3)
    translation = data.geom_xpos[geom_id]

    return vertices_local @ rotation.T + translation


def world_mesh_from_geom(
    model: Any,
    data: Any,
    geom_id: int,
    geom_name: str | None = None,
) -> tuple[np.ndarray, np.ndarray]:
    """Return world-frame vertices and faces for a MuJoCo mesh geom."""
    _ = geom_name
    vertices_local, faces = mesh_local_vertices_and_faces(model, geom_id)
    vertices_world = transform_mesh_vertices_to_world(vertices_local, data, geom_id)

    return vertices_world, faces
