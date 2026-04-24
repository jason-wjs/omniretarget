from __future__ import annotations

from typing import Any

import mujoco  # type: ignore[import-not-found]
import numpy as np


def compute_jacobian_for_contact_relative(
    retargeter: Any,
    geom1,
    geom2,
    geom1_name,
    geom2_name,
    fromto,
    dist,
):
    # Get closest points from fromto buffer
    pos1 = fromto[:3]  # closest point on geom1
    pos2 = fromto[3:]  # closest point on geom2

    v = pos1 - pos2
    norm_v = np.linalg.norm(v)

    if norm_v > 1e-12:
        nhat_BA_W = np.sign(dist) * (v / norm_v)
    # Degenerate: points coincide. Heuristics fallback.
    # If one side is a plane/ground, use its known normal.
    elif "ground" in geom2_name.lower():
        nhat_BA_W = np.array([0.0, 0.0, 1.0]) * (1.0 if dist >= 0 else -1.0)
    elif "ground" in geom1_name.lower():
        nhat_BA_W = np.array([0.0, 0.0, -1.0]) * (1.0 if dist >= 0 else -1.0)
    else:
        nhat_BA_W = np.array([0.0, 0.0, 0.0])

    J_bodyA = retargeter._calc_contact_jacobian_from_point(geom1.bodyid, pos1, input_world=True)
    J_bodyB = retargeter._calc_contact_jacobian_from_point(geom2.bodyid, pos2, input_world=True)

    # Compute relative Jacobian
    Jc = J_bodyA - J_bodyB

    return nhat_BA_W @ Jc


def prefilter_pairs_with_mj_collision(retargeter: Any, threshold: float):
    m, d = retargeter.robot_model, retargeter.robot_data
    ngeom = m.ngeom

    retargeter._geom_names = [mujoco.mj_id2name(m, mujoco.mjtObj.mjOBJ_GEOM, g) or "" for g in range(ngeom)]

    if not hasattr(retargeter, "_saved_margins"):
        retargeter._saved_margins = np.empty_like(m.geom_margin)
    retargeter._saved_margins[:] = m.geom_margin

    retargeter.robot_model.geom_margin[:] = threshold

    # Run collision. This runs broad→narrow and fills d.contact.
    mujoco.mj_collision(m, d)

    # Collect unique candidate pairs that involve at least one masked geom
    candidates = set()
    for k in range(d.ncon):
        c = d.contact[k]
        g1, g2 = int(c.geom1), int(c.geom2)
        if g1 < 0 or g2 < 0:
            continue
        candidates.add((min(g1, g2), max(g1, g2)))

    # Restore margins to keep physics untouched
    retargeter.robot_model.geom_margin[:] = retargeter._saved_margins

    return candidates


def update_jacobians_and_phis_from_q(retargeter: Any, q: np.ndarray):
    retargeter.robot_data.qpos[:] = q

    mujoco.mj_forward(retargeter.robot_model, retargeter.robot_data)  # kinematics & AABBs valid

    m, d = retargeter.robot_model, retargeter.robot_data
    threshold = float(retargeter.collision_detection_threshold)

    # 1) Fast prefilter via mj_collision with temporary margins
    candidates = prefilter_pairs_with_mj_collision(retargeter, threshold)

    Js, phis = {}, {}
    fromto = np.zeros(6, dtype=float)

    # 2) Precise distance only on candidates (early-exit at threshold)
    contype, conaff = m.geom_contype, m.geom_conaffinity

    def masks_ok(g1, g2):
        if contype[g1] == 0 and conaff[g1] == 0:
            return False
        if contype[g2] == 0 and conaff[g2] == 0:
            return False
        if retargeter.object_name in retargeter._geom_names[g1] and "ground" in retargeter._geom_names[g2]:
            return False
        if "ground" in retargeter._geom_names[g1] and retargeter.object_name in retargeter._geom_names[g2]:
            return False
        return (
            retargeter.object_name in retargeter._geom_names[g1]
            or retargeter.object_name in retargeter._geom_names[g2]
            or "ground" in retargeter._geom_names[g1]
            or "ground" in retargeter._geom_names[g2]
        )

    for g1, g2 in candidates:
        if not masks_ok(g1, g2):
            continue

        fromto[:] = 0.0
        dist = mujoco.mj_geomDistance(m, d, g1, g2, threshold, fromto)
        if dist <= threshold:
            J_rel = compute_jacobian_for_contact_relative(
                retargeter,
                m.geom(g1),
                m.geom(g2),
                retargeter._geom_names[g1],
                retargeter._geom_names[g2],
                fromto,
                dist,
            )
            Js[(g1, g2)] = J_rel
            phis[(g1, g2)] = float(dist)

            # For debug
            # retargeter.draw_mesh_pair_with_contact(retargeter.robot_model, retargeter.robot_data, g1, g2,   \
            #     retargeter._geom_names[g1], retargeter._geom_names[g2], fromto=fromto)

    return Js, phis


def get_geometry_name(retargeter: Any, geom_id: int) -> str:
    """Get geometry name from ID."""
    return mujoco.mj_id2name(retargeter.robot_model, mujoco.mjtObj.mjOBJ_GEOM, geom_id)
