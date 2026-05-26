from __future__ import annotations

import argparse
import time
from dataclasses import dataclass
from pathlib import Path

import mujoco  # type: ignore[import-not-found]
import numpy as np
import torch

from omniretarget.data_conversion.convert_data_format_mj import (
    quat_conjugate,
    quat_mul,
    quat_to_rotvec,
    world_body_velocities,
)

try:
    import mujoco.viewer as mjv  # type: ignore[import-not-found]
except ImportError:  # pragma: no cover - viewer is optional in headless environments
    mjv = None


DEFAULT_G1_XML_PATH = Path(
    "/home/humanoid/Projects/Junsong_WU/learning/locomotion/controller/mjlab/src/mjlab/asset_zoo/robots/unitree_g1/xmls/g1.xml"
)

PARC_G1_JOINT_NAMES = [
    "left_hip_pitch_joint",
    "left_hip_roll_joint",
    "left_hip_yaw_joint",
    "left_knee_joint",
    "left_ankle_pitch_joint",
    "left_ankle_roll_joint",
    "right_hip_pitch_joint",
    "right_hip_roll_joint",
    "right_hip_yaw_joint",
    "right_knee_joint",
    "right_ankle_pitch_joint",
    "right_ankle_roll_joint",
    "waist_yaw_joint",
    "waist_roll_joint",
    "waist_pitch_joint",
    "left_shoulder_pitch_joint",
    "left_shoulder_roll_joint",
    "left_shoulder_yaw_joint",
    "left_elbow_joint",
    "left_wrist_roll_joint",
    "left_wrist_pitch_joint",
    "left_wrist_yaw_joint",
    "right_shoulder_pitch_joint",
    "right_shoulder_roll_joint",
    "right_shoulder_yaw_joint",
    "right_elbow_joint",
    "right_wrist_roll_joint",
    "right_wrist_pitch_joint",
    "right_wrist_yaw_joint",
]


@dataclass(frozen=True)
class ParcMjConversionConfig:
    input_file: Path
    output_name: Path
    robot_xml: Path = DEFAULT_G1_XML_PATH
    output_fps: int = 50
    line_range: tuple[int, int] | None = None
    once: bool = False


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Convert retargeted PARC qpos.npz into an mjlab-compatible motion.npz."
    )
    parser.add_argument("--input-file", type=Path, required=True)
    parser.add_argument("--output-name", type=Path, required=True)
    parser.add_argument("--robot-xml", type=Path, default=DEFAULT_G1_XML_PATH)
    parser.add_argument("--output-fps", type=int, default=50)
    parser.add_argument("--line-range", type=int, nargs=2, default=None, metavar=("START", "END"))
    parser.add_argument("--once", action="store_true")
    return parser


def _load_qpos_npz(input_file: Path, line_range: tuple[int, int] | None) -> tuple[np.ndarray, int]:
    with np.load(input_file) as data:
        if "qpos" not in data:
            raise ValueError("PARC motion input must contain 'qpos'")
        qpos = np.asarray(data["qpos"], dtype=np.float32)
        if qpos.ndim != 2:
            raise ValueError("PARC motion 'qpos' must be a rank-2 array")
        if qpos.shape[1] < 36:
            raise ValueError("PARC motion 'qpos' must have at least 36 columns")
        if "fps" not in data:
            raise ValueError("PARC motion input must contain 'fps'")
        fps = int(np.asarray(data["fps"]).item())

    if line_range is not None:
        start, end = line_range
        total_frames = qpos.shape[0] - 1
        if not (0 <= start <= end <= total_frames):
            raise ValueError(
                f"line_range out of bounds: start={start}, end={end}, total_frames={total_frames}"
            )
        qpos = qpos[start : end + 1]

    if qpos.shape[0] < 2:
        raise ValueError("PARC motion input must contain at least 2 frames")
    return qpos, fps


def _lerp(a: np.ndarray, b: np.ndarray, blend: np.ndarray) -> np.ndarray:
    return a * (1.0 - blend) + b * blend


def _slerp(q0: np.ndarray, q1: np.ndarray, t: np.ndarray, eps: float = 1e-8) -> np.ndarray:
    q0 = q0 / np.linalg.norm(q0, axis=-1, keepdims=True).clip(min=eps)
    q1 = q1 / np.linalg.norm(q1, axis=-1, keepdims=True).clip(min=eps)

    dot = np.sum(q0 * q1, axis=-1, keepdims=True)
    q1 = np.where(dot < 0.0, -q1, q1)
    dot = np.sum(q0 * q1, axis=-1, keepdims=True).clip(-1.0, 1.0)

    theta = np.arccos(dot)
    sin_theta = np.sin(theta)
    close = np.abs(sin_theta) < eps

    s0 = np.sin((1.0 - t) * theta) / (sin_theta + eps)
    s1 = np.sin(t * theta) / (sin_theta + eps)
    out = s0 * q0 + s1 * q1
    linear = (1.0 - t) * q0 + t * q1
    out = np.where(close, linear, out)
    return out / np.linalg.norm(out, axis=-1, keepdims=True).clip(min=eps)


def _so3_derivative_wxyz(rotations: np.ndarray, dt: float) -> np.ndarray:
    if rotations.shape[0] == 1:
        return np.zeros((1, 3), dtype=np.float32)

    q_prev = rotations[:-2]
    q_next = rotations[2:]
    q_next_t = torch.from_numpy(q_next.astype(np.float32))
    q_prev_t = torch.from_numpy(q_prev.astype(np.float32))
    q_rel = quat_mul(q_next_t, quat_conjugate(q_prev_t))
    omega = quat_to_rotvec(q_rel).cpu().numpy().astype(np.float32) / (2.0 * dt)
    return np.concatenate([omega[:1], omega, omega[-1:]], axis=0)


def _resample_qpos(qpos: np.ndarray, input_fps: int, output_fps: int) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    input_dt = 1.0 / float(input_fps)
    output_dt = 1.0 / float(output_fps)
    input_frames = qpos.shape[0]
    duration = (input_frames - 1) * input_dt
    times = np.arange(0.0, duration, output_dt, dtype=np.float32)
    if times.size == 0:
        times = np.array([0.0], dtype=np.float32)

    phase = times / duration
    index_0 = np.floor(phase * (input_frames - 1)).astype(np.int64)
    index_1 = np.minimum(index_0 + 1, input_frames - 1)
    blend = (phase * (input_frames - 1) - index_0).astype(np.float32)[:, None]

    root_pos = _lerp(qpos[index_0, :3], qpos[index_1, :3], blend).astype(np.float32)
    root_quat_wxyz = _slerp(qpos[index_0, 3:7], qpos[index_1, 3:7], blend).astype(np.float32)
    joint_pos = _lerp(qpos[index_0, 7:36], qpos[index_1, 7:36], blend).astype(np.float32)
    return root_pos, root_quat_wxyz, joint_pos


def _compute_derivatives(
    root_pos: np.ndarray,
    root_quat_wxyz: np.ndarray,
    joint_pos: np.ndarray,
    output_fps: int,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    dt = 1.0 / float(output_fps)
    root_lin_vel = np.gradient(root_pos, dt, axis=0).astype(np.float32)
    joint_vel = np.gradient(joint_pos, dt, axis=0).astype(np.float32)
    root_ang_vel = _so3_derivative_wxyz(root_quat_wxyz, dt).astype(np.float32)
    return root_lin_vel, root_ang_vel, joint_vel


def _robot_joint_names(model: mujoco.MjModel) -> list[str]:
    names: list[str] = []
    for joint_id in range(model.njnt):
        if model.jnt_type[joint_id] == mujoco.mjtJoint.mjJNT_FREE:
            continue
        name = mujoco.mj_id2name(model, mujoco.mjtObj.mjOBJ_JOINT, joint_id)
        if name is None:
            raise ValueError(f"Joint id {joint_id} has no name in robot XML")
        names.append(name)
    return names


def _input_to_robot_joint_indices(robot_joint_names: list[str]) -> list[int]:
    return [PARC_G1_JOINT_NAMES.index(name) for name in robot_joint_names]


def _collect_motion_arrays(
    *,
    model: mujoco.MjModel,
    data: mujoco.MjData,
    root_pos: np.ndarray,
    root_quat_wxyz: np.ndarray,
    root_lin_vel: np.ndarray,
    root_ang_vel: np.ndarray,
    joint_pos_input_order: np.ndarray,
    joint_vel_input_order: np.ndarray,
    joint_reorder: list[int],
    output_fps: int,
    once: bool,
) -> dict[str, np.ndarray]:
    viewer = None
    if once:
        if mjv is None:
            raise RuntimeError("mujoco.viewer is not available in this environment")
        viewer = mjv.launch_passive(model, data, show_left_ui=False, show_right_ui=False)

    joint_pos = joint_pos_input_order[:, joint_reorder].astype(np.float32)
    joint_vel = joint_vel_input_order[:, joint_reorder].astype(np.float32)

    # Exclude the world body to match mjlab Entity.body_names ordering.
    body_pos_w = np.zeros((joint_pos.shape[0], model.nbody - 1, 3), dtype=np.float32)
    body_quat_w = np.zeros((joint_pos.shape[0], model.nbody - 1, 4), dtype=np.float32)
    body_lin_vel_w = np.zeros_like(body_pos_w)
    body_ang_vel_w = np.zeros_like(body_pos_w)

    dt = 1.0 / float(output_fps)
    for frame in range(joint_pos.shape[0]):
        start_time = time.perf_counter()
        data.qpos[:] = np.concatenate([root_pos[frame], root_quat_wxyz[frame], joint_pos[frame]], axis=0)
        data.qvel[:] = np.concatenate([root_lin_vel[frame], root_ang_vel[frame], joint_vel[frame]], axis=0)
        mujoco.mj_forward(model, data)

        body_pos_w[frame] = data.xpos[1:].copy()
        body_quat_w[frame] = data.xquat[1:].copy()
        lin_vel_w, ang_vel_w = world_body_velocities(model, data)
        body_lin_vel_w[frame] = lin_vel_w[1:].astype(np.float32)
        body_ang_vel_w[frame] = ang_vel_w[1:].astype(np.float32)

        if viewer is not None:
            viewer.sync()
            time.sleep(max(0.0, dt - (time.perf_counter() - start_time)))

    if viewer is not None:
        viewer.close()

    return {
        "fps": np.asarray(output_fps, dtype=np.int32),
        "joint_pos": joint_pos,
        "joint_vel": joint_vel,
        "body_pos_w": body_pos_w,
        "body_quat_w": body_quat_w,
        "body_lin_vel_w": body_lin_vel_w,
        "body_ang_vel_w": body_ang_vel_w,
    }


def convert_parc_qpos_to_motion(config: ParcMjConversionConfig) -> dict[str, np.ndarray]:
    qpos, input_fps = _load_qpos_npz(config.input_file, config.line_range)
    root_pos, root_quat_wxyz, joint_pos = _resample_qpos(qpos, input_fps, config.output_fps)
    root_lin_vel, root_ang_vel, joint_vel = _compute_derivatives(
        root_pos, root_quat_wxyz, joint_pos, config.output_fps
    )

    if not config.robot_xml.exists():
        raise FileNotFoundError(config.robot_xml)
    model = mujoco.MjModel.from_xml_path(str(config.robot_xml))
    data = mujoco.MjData(model)
    robot_joint_names = _robot_joint_names(model)
    joint_reorder = _input_to_robot_joint_indices(robot_joint_names)

    return _collect_motion_arrays(
        model=model,
        data=data,
        root_pos=root_pos,
        root_quat_wxyz=root_quat_wxyz,
        root_lin_vel=root_lin_vel,
        root_ang_vel=root_ang_vel,
        joint_pos_input_order=joint_pos,
        joint_vel_input_order=joint_vel,
        joint_reorder=joint_reorder,
        output_fps=config.output_fps,
        once=config.once,
    )


def convert_parc_qpos_to_motion_file(config: ParcMjConversionConfig) -> Path:
    payload = convert_parc_qpos_to_motion(config)
    config.output_name.parent.mkdir(parents=True, exist_ok=True)
    np.savez(config.output_name, **payload)
    return config.output_name


def main() -> None:
    args = build_arg_parser().parse_args()
    convert_parc_qpos_to_motion_file(
        ParcMjConversionConfig(
            input_file=args.input_file.resolve(),
            output_name=args.output_name.resolve(),
            robot_xml=args.robot_xml.resolve(),
            output_fps=args.output_fps,
            line_range=tuple(args.line_range) if args.line_range is not None else None,
            once=args.once,
        )
    )


if __name__ == "__main__":
    main()
