from __future__ import annotations

from collections.abc import Iterable

import mujoco  # type: ignore[import-not-found]
import numpy as np

from omniretarget.mujoco.model_state import set_qpos_and_forward


def body_id(model: mujoco.MjModel, body_name: str) -> int:
    """Return a MuJoCo body id or raise a caller-facing error."""
    body_idx = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_BODY, body_name)
    if body_idx == -1:
        raise ValueError(f"Body {body_name} not found in Mujoco model")
    return int(body_idx)


def link_positions(
    model: mujoco.MjModel,
    data: mujoco.MjData,
    q: np.ndarray,
    link_names: Iterable[str],
    *,
    allow_trailing_dynamic_object: bool = False,
) -> np.ndarray:
    """Return world-frame body positions for link_names at q."""
    set_qpos_and_forward(model, data, q, allow_trailing_dynamic_object=allow_trailing_dynamic_object)
    return np.array([data.xpos[body_id(model, link_name)].copy() for link_name in link_names])


def world_to_body_frame(data: mujoco.MjData, p_w: np.ndarray, body_idx: int) -> np.ndarray:
    """Transform a world-frame point into a MuJoCo body frame."""
    p_w = np.asarray(p_w).reshape(3)
    body_pos = data.xpos[body_idx].reshape(3)
    body_mat = data.xmat[body_idx].reshape(3, 3)
    return body_mat.T @ (p_w - body_pos)


def _quat_dot_to_world_omega(qw: float, qx: float, qy: float, qz: float) -> np.ndarray:
    return np.array(
        [
            [-qx, qw, qz, -qy],
            [-qy, -qz, qw, qx],
            [-qz, qy, -qx, qw],
        ]
    )


def _quat_dot_to_body_omega(qw: float, qx: float, qy: float, qz: float) -> np.ndarray:
    return np.array(
        [
            [-qx, qw, -qz, qy],
            [-qy, qz, qw, -qx],
            [-qz, -qy, qx, qw],
        ]
    )


def qdot_to_qvel_transform(
    model: mujoco.MjModel,
    data: mujoco.MjData,
    *,
    has_dynamic_object: bool,
    use_world_omega: bool = True,
) -> np.ndarray:
    """Return T(q) such that MuJoCo qvel = T(q) @ qdot."""
    transform = np.zeros((model.nv, model.nq), dtype=float)
    e_fn = _quat_dot_to_world_omega if use_world_omega else _quat_dot_to_body_omega

    root_joint = 0
    if model.jnt_type[root_joint] != mujoco.mjtJoint.mjJNT_FREE:
        raise AssertionError("Expected root joint to be FREE")

    root_qadr = int(model.jnt_qposadr[root_joint])
    root_dadr = int(model.jnt_dofadr[root_joint])
    qw, qx, qy, qz = data.qpos[root_qadr + 3 : root_qadr + 7]
    transform[root_dadr : root_dadr + 3, root_qadr : root_qadr + 3] = np.eye(3)
    transform[root_dadr + 3 : root_dadr + 6, root_qadr + 3 : root_qadr + 7] = 2.0 * e_fn(qw, qx, qy, qz)

    if has_dynamic_object:
        free_joints = [j for j in range(model.njnt) if model.jnt_type[j] == mujoco.mjtJoint.mjJNT_FREE]
        if len(free_joints) < 2:
            raise AssertionError("Expected two FREE joints (human + object).")
        object_joint = free_joints[1]
        object_qadr = int(model.jnt_qposadr[object_joint])
        object_dadr = int(model.jnt_dofadr[object_joint])
        qw, qx, qy, qz = data.qpos[object_qadr + 3 : object_qadr + 7]
        transform[object_dadr : object_dadr + 3, object_qadr : object_qadr + 3] = np.eye(3)
        transform[object_dadr + 3 : object_dadr + 6, object_qadr + 3 : object_qadr + 7] = 2.0 * e_fn(
            qw, qx, qy, qz
        )

    for joint_id in range(1, model.njnt):
        joint_type = model.jnt_type[joint_id]
        if joint_type in (mujoco.mjtJoint.mjJNT_HINGE, mujoco.mjtJoint.mjJNT_SLIDE):
            qadr = int(model.jnt_qposadr[joint_id])
            dadr = int(model.jnt_dofadr[joint_id])
            transform[dadr, qadr] = 1.0
        elif joint_type == mujoco.mjtJoint.mjJNT_BALL:
            raise NotImplementedError("BALL joint block not implemented.")

    return transform


def point_jacobian_qpos(
    model: mujoco.MjModel,
    data: mujoco.MjData,
    body_idx: int,
    point: np.ndarray,
    *,
    input_world: bool = False,
    has_dynamic_object: bool,
    use_world_omega: bool = True,
) -> np.ndarray:
    """Return translational point Jacobian with respect to qpos."""
    point = np.asarray(point, dtype=float).reshape(3)
    mujoco.mj_forward(model, data)

    body_rot = data.xmat[body_idx].reshape(3, 3)
    body_pos = data.xpos[body_idx]
    point_world = point if input_world else body_pos + body_rot @ point

    jac_pos = np.zeros((3, model.nv), dtype=np.float64, order="C")
    jac_rot = np.zeros((3, model.nv), dtype=np.float64, order="C")
    mujoco.mj_jac(model, data, jac_pos, jac_rot, point_world.astype(np.float64), int(body_idx))

    return jac_pos @ qdot_to_qvel_transform(
        model,
        data,
        has_dynamic_object=has_dynamic_object,
        use_world_omega=use_world_omega,
    )
