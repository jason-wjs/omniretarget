from __future__ import annotations

from collections.abc import Sequence

import mujoco  # type: ignore[import-not-found]
import numpy as np


def geometry_name(model: mujoco.MjModel, geom_id: int) -> str:
    """Return a MuJoCo geometry name, using the legacy empty string fallback."""
    return mujoco.mj_id2name(model, mujoco.mjtObj.mjOBJ_GEOM, geom_id) or ""


def geometry_names(model: mujoco.MjModel) -> list[str]:
    """Return all geometry names in model order."""
    return [geometry_name(model, geom_id) for geom_id in range(model.ngeom)]


def prefilter_pairs_with_mj_collision(
    model: mujoco.MjModel,
    data: mujoco.MjData,
    threshold: float,
) -> set[tuple[int, int]]:
    """Collect unique MuJoCo contact candidate pairs using temporary geom margins."""
    saved_margins = np.empty_like(model.geom_margin)
    saved_margins[:] = model.geom_margin
    try:
        model.geom_margin[:] = threshold
        mujoco.mj_collision(model, data)

        candidates: set[tuple[int, int]] = set()
        for contact_idx in range(data.ncon):
            contact = data.contact[contact_idx]
            geom1, geom2 = int(contact.geom1), int(contact.geom2)
            if geom1 < 0 or geom2 < 0:
                continue
            candidates.add((min(geom1, geom2), max(geom1, geom2)))
        return candidates
    finally:
        model.geom_margin[:] = saved_margins


def _has_collision_mask(model: mujoco.MjModel, geom_id: int) -> bool:
    return not (model.geom_contype[geom_id] == 0 and model.geom_conaffinity[geom_id] == 0)


def _is_object_geom(geom_name: str, object_name: str) -> bool:
    return object_name in geom_name


def _is_ground_geom(geom_name: str) -> bool:
    return "ground" in geom_name


def geom_pair_allowed_for_object_or_ground(
    model: mujoco.MjModel,
    geom_names: Sequence[str],
    object_name: str,
    geom1: int,
    geom2: int,
) -> bool:
    """Return whether a pair is relevant to object/ground collision checks."""
    if not _has_collision_mask(model, geom1) or not _has_collision_mask(model, geom2):
        return False

    geom1_is_object = _is_object_geom(geom_names[geom1], object_name)
    geom2_is_object = _is_object_geom(geom_names[geom2], object_name)
    geom1_is_ground = _is_ground_geom(geom_names[geom1])
    geom2_is_ground = _is_ground_geom(geom_names[geom2])

    if (geom1_is_object and geom2_is_ground) or (geom2_is_object and geom1_is_ground):
        return False

    return geom1_is_object or geom2_is_object or geom1_is_ground or geom2_is_ground


def should_enforce_non_penetration_pair(
    pair_key: tuple[int, int],
    *,
    geom_names: Sequence[str] | None,
    object_name: str,
    activate_obj_non_penetration: bool,
) -> bool:
    """Gate object non-penetration constraints while preserving ground constraints."""
    if activate_obj_non_penetration or object_name == "ground":
        return True
    if geom_names is None:
        return True

    geom1, geom2 = pair_key
    geom1_name = geom_names[geom1]
    geom2_name = geom_names[geom2]
    if _is_ground_geom(geom1_name) or _is_ground_geom(geom2_name):
        return True
    return not (_is_object_geom(geom1_name, object_name) or _is_object_geom(geom2_name, object_name))


def geom_distance(
    model: mujoco.MjModel,
    data: mujoco.MjData,
    geom1: int,
    geom2: int,
    threshold: float,
) -> tuple[float, np.ndarray]:
    """Return signed geom distance and closest-point segment."""
    fromto = np.zeros(6, dtype=float)
    distance = mujoco.mj_geomDistance(model, data, geom1, geom2, threshold, fromto)
    return float(distance), fromto


def geom_ids_containing(model: mujoco.MjModel, name_part: str) -> list[int]:
    """Return geom ids whose names contain name_part."""
    return [geom_id for geom_id in range(model.ngeom) if name_part in geometry_name(model, geom_id)]


def body_geom_ids(model: mujoco.MjModel, body_idx: int) -> list[int]:
    """Return geom ids attached to body_idx."""
    return [geom_id for geom_id in range(model.ngeom) if model.geom_bodyid[geom_id] == body_idx]


def min_distance_between_body_and_geoms(
    model: mujoco.MjModel,
    data: mujoco.MjData,
    body_idx: int,
    target_geom_ids: Sequence[int],
    threshold: float,
) -> float:
    """Return the minimum current distance between body geoms and target geoms."""
    dist_min = np.inf
    for body_geom_id in body_geom_ids(model, body_idx):
        for target_geom_id in target_geom_ids:
            distance, _ = geom_distance(model, data, body_geom_id, target_geom_id, threshold)
            dist_min = min(dist_min, distance)
    return float(dist_min)
