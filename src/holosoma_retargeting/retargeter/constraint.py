from __future__ import annotations

import mujoco  # type: ignore[import-not-found]
import numpy as np
from scipy.spatial.transform import Rotation  # type: ignore[import-untyped]


def compute_jacobian_for_contact_relative(retargeter, geom1, geom2, geom1_name, geom2_name, fromto, dist):
    """Compute the contact-normal relative Jacobian for a MuJoCo geom pair."""
    pos1 = fromto[:3]
    pos2 = fromto[3:]

    relative = pos1 - pos2
    relative_norm = np.linalg.norm(relative)

    if relative_norm > 1e-12:
        normal_world = np.sign(dist) * (relative / relative_norm)
    elif "ground" in geom2_name.lower():
        normal_world = np.array([0.0, 0.0, 1.0]) * (1.0 if dist >= 0 else -1.0)
    elif "ground" in geom1_name.lower():
        normal_world = np.array([0.0, 0.0, -1.0]) * (1.0 if dist >= 0 else -1.0)
    else:
        normal_world = np.array([0.0, 0.0, 0.0])

    jacobian_body_a = calc_contact_jacobian_from_point(retargeter, geom1.bodyid, pos1, input_world=True)
    jacobian_body_b = calc_contact_jacobian_from_point(retargeter, geom2.bodyid, pos2, input_world=True)

    return normal_world @ (jacobian_body_a - jacobian_body_b)


def prefilter_pairs_with_mj_collision(retargeter, threshold: float):
    model, data = retargeter.robot_model, retargeter.robot_data
    ngeom = model.ngeom

    retargeter._geom_names = [
        mujoco.mj_id2name(model, mujoco.mjtObj.mjOBJ_GEOM, geom_id) or "" for geom_id in range(ngeom)
    ]

    if not hasattr(retargeter, "_saved_margins"):
        retargeter._saved_margins = np.empty_like(model.geom_margin)
    retargeter._saved_margins[:] = model.geom_margin

    model.geom_margin[:] = threshold
    mujoco.mj_collision(model, data)

    candidates = set()
    for contact_idx in range(data.ncon):
        contact = data.contact[contact_idx]
        geom1, geom2 = int(contact.geom1), int(contact.geom2)
        if geom1 < 0 or geom2 < 0:
            continue
        candidates.add((min(geom1, geom2), max(geom1, geom2)))

    model.geom_margin[:] = retargeter._saved_margins

    return candidates


def update_jacobians_and_phis_from_q(retargeter, q: np.ndarray):
    """Extract active non-penetration Jacobians and signed distances for the solver."""
    retargeter.robot_data.qpos[:] = q

    mujoco.mj_forward(retargeter.robot_model, retargeter.robot_data)

    model, data = retargeter.robot_model, retargeter.robot_data
    threshold = float(retargeter.collision_detection_threshold)
    candidates = prefilter_pairs_with_mj_collision(retargeter, threshold)

    jacobians, phis = {}, {}
    fromto = np.zeros(6, dtype=float)
    contype, conaff = model.geom_contype, model.geom_conaffinity

    def masks_ok(geom1, geom2):
        if contype[geom1] == 0 and conaff[geom1] == 0:
            return False
        if contype[geom2] == 0 and conaff[geom2] == 0:
            return False
        if retargeter.object_name in retargeter._geom_names[geom1] and "ground" in retargeter._geom_names[geom2]:
            return False
        if "ground" in retargeter._geom_names[geom1] and retargeter.object_name in retargeter._geom_names[geom2]:
            return False
        return (
            retargeter.object_name in retargeter._geom_names[geom1]
            or retargeter.object_name in retargeter._geom_names[geom2]
            or "ground" in retargeter._geom_names[geom1]
            or "ground" in retargeter._geom_names[geom2]
        )

    for geom1, geom2 in candidates:
        if not masks_ok(geom1, geom2):
            continue

        fromto[:] = 0.0
        dist = mujoco.mj_geomDistance(model, data, geom1, geom2, threshold, fromto)
        if dist <= threshold:
            jacobian_relative = compute_jacobian_for_contact_relative(
                retargeter,
                model.geom(geom1),
                model.geom(geom2),
                retargeter._geom_names[geom1],
                retargeter._geom_names[geom2],
                fromto,
                dist,
            )
            jacobians[(geom1, geom2)] = jacobian_relative
            phis[(geom1, geom2)] = float(dist)

    return jacobians, phis


def world_to_body_frame(retargeter, point_world: np.ndarray, body_idx: int) -> np.ndarray:
    """Transform a point from world frame to body frame."""
    point_world = np.asarray(point_world).reshape(3)
    body_pos = retargeter.robot_data.xpos[body_idx].reshape(3)
    body_mat = retargeter.robot_data.xmat[body_idx].reshape(3, 3)
    return body_mat.T @ (point_world - body_pos)


def get_geometry_name(retargeter, geom_id: int) -> str:
    """Get a MuJoCo geometry name from its id."""
    return mujoco.mj_id2name(retargeter.robot_model, mujoco.mjtObj.mjOBJ_GEOM, geom_id)


def build_transform_qdot_to_qvel_fast(retargeter, use_world_omega=True):
    """
    Return T(q) (nv x nq) such that v = T(q) @ qdot.

    The free root uses qpos=[x,y,z, qw,qx,qy,qz] and qvel=[vx,vy,vz, wx,wy,wz].
    Hinge and slide joints use v = qdot.
    """
    nq, nv = retargeter.robot_model.nq, retargeter.robot_model.nv
    transform = np.zeros((nv, nq), dtype=float)

    joint0 = 0
    assert retargeter.robot_model.jnt_type[joint0] == mujoco.mjtJoint.mjJNT_FREE

    def get_e_world(qw, qx, qy, qz):
        return np.array(
            [
                [-qx, qw, qz, -qy],
                [-qy, -qz, qw, qx],
                [-qz, qy, -qx, qw],
            ]
        )

    def get_e_body(qw, qx, qy, qz):
        return np.array(
            [
                [-qx, qw, -qz, qy],
                [-qy, qz, qw, -qx],
                [-qz, -qy, qx, qw],
            ]
        )

    e_fn = get_e_world if use_world_omega else get_e_body

    joint_free1 = 0
    assert retargeter.robot_model.jnt_type[joint_free1] == mujoco.mjtJoint.mjJNT_FREE
    qadr1 = int(retargeter.robot_model.jnt_qposadr[joint_free1])
    dadr1 = int(retargeter.robot_model.jnt_dofadr[joint_free1])

    qw, qx, qy, qz = retargeter.robot_data.qpos[qadr1 + 3 : qadr1 + 7]
    e1 = 2.0 * e_fn(qw, qx, qy, qz)
    transform[dadr1 + 0 : dadr1 + 3, qadr1 + 0 : qadr1 + 3] = np.eye(3)
    transform[dadr1 + 3 : dadr1 + 6, qadr1 + 3 : qadr1 + 7] = e1

    if retargeter.has_dynamic_object:
        free_joints = [
            joint_id
            for joint_id in range(retargeter.robot_model.njnt)
            if retargeter.robot_model.jnt_type[joint_id] == mujoco.mjtJoint.mjJNT_FREE
        ]
        assert len(free_joints) >= 2, "Expected two FREE joints (human + object)."
        joint_free2 = free_joints[1]
        qadr2 = int(retargeter.robot_model.jnt_qposadr[joint_free2])
        dadr2 = int(retargeter.robot_model.jnt_dofadr[joint_free2])

        qw, qx, qy, qz = retargeter.robot_data.qpos[qadr2 + 3 : qadr2 + 7]
        e2 = 2.0 * e_fn(qw, qx, qy, qz)
        transform[dadr2 + 0 : dadr2 + 3, qadr2 + 0 : qadr2 + 3] = np.eye(3)
        transform[dadr2 + 3 : dadr2 + 6, qadr2 + 3 : qadr2 + 7] = e2

    for joint_id in range(1, retargeter.robot_model.njnt):
        joint_type = retargeter.robot_model.jnt_type[joint_id]
        if joint_type in (mujoco.mjtJoint.mjJNT_HINGE, mujoco.mjtJoint.mjJNT_SLIDE):
            qadr = retargeter.robot_model.jnt_qposadr[joint_id]
            dadr = retargeter.robot_model.jnt_dofadr[joint_id]
            transform[dadr, qadr] = 1.0
        elif joint_type == mujoco.mjtJoint.mjJNT_BALL:
            raise NotImplementedError("BALL joint block not implemented.")

    return transform


def calc_contact_jacobian_from_point(retargeter, body_idx: int, point_body: np.ndarray, input_world=False):
    """Compute translational point Jacobian with respect to qdot."""
    point_body = np.asarray(point_body, dtype=float).reshape(3)

    mujoco.mj_forward(retargeter.robot_model, retargeter.robot_data)

    rotation_world_body = retargeter.robot_data.xmat[body_idx].reshape(3, 3)
    position_world_body = retargeter.robot_data.xpos[body_idx]

    if input_world:
        point_world = point_body.astype(np.float64).reshape(3, 1)
    else:
        point_world = (position_world_body + rotation_world_body @ point_body).astype(np.float64).reshape(3, 1)

    jacobian_pos = np.zeros((3, retargeter.robot_model.nv), dtype=np.float64, order="C")
    jacobian_rot = np.zeros((3, retargeter.robot_model.nv), dtype=np.float64, order="C")
    mujoco.mj_jac(retargeter.robot_model, retargeter.robot_data, jacobian_pos, jacobian_rot, point_world, int(body_idx))

    qdot_to_qvel = build_transform_qdot_to_qvel_fast(retargeter)

    return jacobian_pos @ qdot_to_qvel


def calc_manipulator_jacobians(
    retargeter,
    q: np.ndarray,
    links: dict[str, str],
    obj_frame: bool = False,
    point_offsets: np.ndarray | None = None,
):
    """Compute solver-ready link point Jacobians and positions."""
    jacobian_dict = {}
    position_dict = {}

    if obj_frame:
        if retargeter.has_dynamic_object:
            obj_quat = q[-4:]
            obj_pos = q[-7:-4]
            obj_rot = Rotation.from_quat([obj_quat[1], obj_quat[2], obj_quat[3], obj_quat[0]]).as_matrix()
            obj_rot_inv = obj_rot.T
        else:
            obj_rot = Rotation.from_quat([0, 0, 0, 1]).as_matrix()
            obj_rot_inv = obj_rot.T
            obj_pos = np.zeros(3)

    retargeter.robot_data.qpos[:] = q.copy()
    mujoco.mj_forward(retargeter.robot_model, retargeter.robot_data)

    for name, link_name in links.items():
        body_id = mujoco.mj_name2id(retargeter.robot_model, mujoco.mjtObj.mjOBJ_BODY, link_name)
        point_body = point_offsets if point_offsets is not None else np.zeros(3)

        jacobian = calc_contact_jacobian_from_point(retargeter, body_id, point_body)
        pos_world = retargeter.robot_data.xpos[body_id]

        if obj_frame:
            position = obj_rot_inv @ (pos_world - obj_pos)
            jacobian_frame = obj_rot_inv @ jacobian
        else:
            position = pos_world
            jacobian_frame = jacobian

        jacobian_dict[name] = np.array(jacobian_frame[:, retargeter.q_a_indices], dtype=float, copy=True)
        position_dict[name] = np.array(position, dtype=float, copy=True)

    object_pose = {"position": obj_pos, "rotation": obj_rot} if obj_frame else None

    return jacobian_dict, position_dict, object_pose
