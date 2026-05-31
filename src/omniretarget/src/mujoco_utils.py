from __future__ import annotations

from typing import Tuple

from omniretarget.mujoco.assets import (
    mesh_local_vertices_and_faces,
    transform_mesh_vertices_to_world,
    world_mesh_from_geom,
)

Pair = Tuple[str, str]


def _mesh_local_vf(model, geom_id):
    """Return local vertices and faces for a MuJoCo mesh geom."""
    return mesh_local_vertices_and_faces(model, geom_id)


def _to_world(v_local, data, geom_id):
    """Transform local vertices to world using geom pose."""
    return transform_mesh_vertices_to_world(v_local, data, geom_id)


def _world_mesh_from_geom(model, data, geom_id, geom_name):
    return world_mesh_from_geom(model, data, geom_id, geom_name)
