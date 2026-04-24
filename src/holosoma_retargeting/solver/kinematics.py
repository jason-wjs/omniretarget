from __future__ import annotations

from typing import Any

import mujoco  # type: ignore[import-not-found]
import numpy as np
from scipy.spatial.transform import Rotation  # type: ignore[import-untyped]


def world_to_body_frame(retargeter: Any, p_w: np.ndarray, body_idx: int) -> np.ndarray:
    """Transform point from world frame to body frame."""
    p_w = np.asarray(p_w).reshape(3)
    body_pos = retargeter.robot_data.xpos[body_idx].reshape(3)
    body_mat = retargeter.robot_data.xmat[body_idx].reshape(3, 3)
    return body_mat.T @ (p_w - body_pos)


def build_transform_qdot_to_qvel_fast(retargeter: Any, use_world_omega: bool = True) -> np.ndarray:
    """
    Return T(q) (nv x nq) such that v = T(q) @ qdot.
    - Free root: qpos=[x,y,z, qw,qx,qy,qz], qvel=[vx,vy,vz, ωx,ωy,ωz]
    where ω and v are WORLD-expressed in MuJoCo.
    - 23 hinge joints: v = qdot.

    If use_world_omega=False, uses BODY-omega mapping (for debugging).
    """
    nq, nv = retargeter.robot_model.nq, retargeter.robot_model.nv
    T = np.zeros((nv, nq), dtype=float)

    j0 = 0
    assert retargeter.robot_model.jnt_type[j0] == mujoco.mjtJoint.mjJNT_FREE
    qadr = retargeter.robot_model.jnt_qposadr[j0]
    dadr = retargeter.robot_model.jnt_dofadr[j0]

    T[dadr : dadr + 3, qadr : qadr + 3] = np.eye(3)

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

    E_fn = get_e_world if use_world_omega else get_e_body

    j_free1 = 0
    assert retargeter.robot_model.jnt_type[j_free1] == mujoco.mjtJoint.mjJNT_FREE
    qadr1 = int(retargeter.robot_model.jnt_qposadr[j_free1])
    dadr1 = int(retargeter.robot_model.jnt_dofadr[j_free1])

    qw, qx, qy, qz = retargeter.robot_data.qpos[qadr1 + 3 : qadr1 + 7]
    E1 = 2.0 * E_fn(qw, qx, qy, qz)
    T[dadr1 + 0 : dadr1 + 3, qadr1 + 0 : qadr1 + 3] = np.eye(3)
    T[dadr1 + 3 : dadr1 + 6, qadr1 + 3 : qadr1 + 7] = E1

    if retargeter.has_dynamic_object:
        free_joints = [
            j for j in range(retargeter.robot_model.njnt) if retargeter.robot_model.jnt_type[j] == mujoco.mjtJoint.mjJNT_FREE
        ]
        assert len(free_joints) >= 2, "Expected two FREE joints (human + object)."
        j_free2 = free_joints[1]
        qadr2 = int(retargeter.robot_model.jnt_qposadr[j_free2])
        dadr2 = int(retargeter.robot_model.jnt_dofadr[j_free2])

        qw, qx, qy, qz = retargeter.robot_data.qpos[qadr2 + 3 : qadr2 + 7]
        E2 = 2.0 * E_fn(qw, qx, qy, qz)
        T[dadr2 + 0 : dadr2 + 3, qadr2 + 0 : qadr2 + 3] = np.eye(3)
        T[dadr2 + 3 : dadr2 + 6, qadr2 + 3 : qadr2 + 7] = E2

    for j in range(1, retargeter.robot_model.njnt):
        jt = retargeter.robot_model.jnt_type[j]
        if jt in (mujoco.mjtJoint.mjJNT_HINGE, mujoco.mjtJoint.mjJNT_SLIDE):
            qa = retargeter.robot_model.jnt_qposadr[j]
            da = retargeter.robot_model.jnt_dofadr[j]
            T[da, qa] = 1.0
        elif jt == mujoco.mjtJoint.mjJNT_BALL:
            raise NotImplementedError("BALL joint block not implemented.")

    return T


def calc_contact_jacobian_from_point(
    retargeter: Any, body_idx: int, p_body: np.ndarray, input_world: bool = False
) -> np.ndarray:
    """
    Translational Jacobian J(q) (3 x nq) such that
    v_point_world = J(q) @ qdot.

    Fast analytic version: J_qdot = J_v @ T(q)
    """
    p_body = np.asarray(p_body, dtype=float).reshape(3)

    mujoco.mj_forward(retargeter.robot_model, retargeter.robot_data)

    R_WB = retargeter.robot_data.xmat[body_idx].reshape(3, 3)
    p_WB = retargeter.robot_data.xpos[body_idx]

    if input_world:
        p_W = p_body.astype(np.float64).reshape(3, 1)
    else:
        p_W = (p_WB + R_WB @ p_body).astype(np.float64).reshape(3, 1)

    Jp = np.zeros((3, retargeter.robot_model.nv), dtype=np.float64, order="C")
    Jr = np.zeros((3, retargeter.robot_model.nv), dtype=np.float64, order="C")
    mujoco.mj_jac(retargeter.robot_model, retargeter.robot_data, Jp, Jr, p_W, int(body_idx))

    T = build_transform_qdot_to_qvel_fast(retargeter)
    return Jp @ T


def calc_manipulator_jacobians(
    retargeter: Any,
    q: np.ndarray,
    links: dict[str, str],
    obj_frame: bool = False,
    point_offsets: np.ndarray | None = None,
):
    """Compute position-based Jacobians using MuJoCo."""
    J_XC_dict = {}
    p_XC_dict = {}

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

    q_mujoco = q.copy()
    retargeter.robot_data.qpos[:] = q_mujoco

    mujoco.mj_forward(retargeter.robot_model, retargeter.robot_data)

    for name, link_name in links.items():
        body_id = mujoco.mj_name2id(retargeter.robot_model, mujoco.mjtObj.mjOBJ_BODY, link_name)

        if point_offsets is not None:
            pC_B = point_offsets
        else:
            pC_B = np.zeros(3)

        J = calc_contact_jacobian_from_point(retargeter, body_id, pC_B)
        pos_world = retargeter.robot_data.xpos[body_id]

        if obj_frame:
            p_XC = obj_rot_inv @ (pos_world - obj_pos)
            J_XC = obj_rot_inv @ J
        else:
            p_XC = pos_world
            J_XC = J

        J_XC_dict[name] = np.array(J_XC[:, retargeter.q_a_indices], dtype=float, copy=True)
        p_XC_dict[name] = np.array(p_XC, dtype=float, copy=True)

    P_WO = {"position": obj_pos, "rotation": obj_rot} if obj_frame else None

    return J_XC_dict, p_XC_dict, P_WO


def get_robot_link_positions(retargeter: Any, q: np.ndarray, link_names) -> np.ndarray:
    """Get robot link positions for given configuration using Mujoco."""
    mujoco_q = q.copy()

    if mujoco_q.shape != retargeter.robot_data.qpos.shape:
        retargeter.robot_data.qpos = mujoco_q[:-7]
    else:
        retargeter.robot_data.qpos = mujoco_q

    mujoco.mj_forward(retargeter.robot_model, retargeter.robot_data)

    robot_link_positions = []

    for link_name in link_names:
        body_id = mujoco.mj_name2id(retargeter.robot_model, mujoco.mjtObj.mjOBJ_BODY, link_name)
        if body_id == -1:
            raise ValueError(f"Body {link_name} not found in Mujoco model")

        pos = retargeter.robot_data.xpos[body_id].copy()
        robot_link_positions.append(pos)

    return np.array(robot_link_positions)
