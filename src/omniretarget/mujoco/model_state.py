from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import mujoco  # type: ignore[import-not-found]
import numpy as np

from omniretarget.mujoco.assets import resolve_robot_xml_path


@dataclass(frozen=True)
class MujocoModelState:
    model: mujoco.MjModel
    data: mujoco.MjData
    robot_xml_path: str
    has_dynamic_object: bool


def _qpos_length(model_or_data: Any) -> int:
    if hasattr(model_or_data, "nq"):
        return int(model_or_data.nq)
    if hasattr(model_or_data, "qpos"):
        return int(model_or_data.qpos.shape[0])
    raise TypeError("Expected a MuJoCo model or data object with nq or qpos")


def has_dynamic_object_qpos(model_or_data: Any, *, robot_dof: int) -> bool:
    """Return whether qpos has an extra freejoint after the robot qpos layout."""
    return _qpos_length(model_or_data) > 7 + robot_dof


def qpos_for_model(
    q: np.ndarray,
    model_or_data: Any,
    *,
    allow_trailing_dynamic_object: bool = False,
) -> np.ndarray:
    """Return a 1D qpos compatible with model_or_data.

    Some legacy call sites pass robot+object qpos to a robot-only model. That
    compatibility mode is explicit so ambiguous shape mismatches fail loudly.
    """
    qpos = np.asarray(q, dtype=float)
    model_nq = _qpos_length(model_or_data)
    if qpos.ndim != 1:
        raise ValueError(f"qpos shape must be 1D for model nq={model_nq}, got {qpos.shape}")
    if qpos.shape[0] == model_nq:
        return qpos
    if allow_trailing_dynamic_object and qpos.shape[0] == model_nq + 7:
        return qpos[:-7]
    raise ValueError(f"qpos shape {qpos.shape} is incompatible with model nq={model_nq}")


def set_qpos_and_forward(
    model: mujoco.MjModel,
    data: mujoco.MjData,
    q: np.ndarray,
    *,
    allow_trailing_dynamic_object: bool = False,
) -> None:
    """Set model qpos from q and run forward kinematics."""
    data.qpos[:] = qpos_for_model(q, model, allow_trailing_dynamic_object=allow_trailing_dynamic_object)
    mujoco.mj_forward(model, data)


def load_model_state(
    *,
    robot_model_path: str,
    object_name: str,
    robot_dof: int,
    scene_xml_file: str | None = None,
) -> MujocoModelState:
    """Load a MuJoCo model/data pair and detect whether qpos contains a dynamic object."""
    robot_xml_path = resolve_robot_xml_path(robot_model_path, object_name, scene_xml_file=scene_xml_file)
    model = mujoco.MjModel.from_xml_path(robot_xml_path)
    data = mujoco.MjData(model)
    return MujocoModelState(
        model=model,
        data=data,
        robot_xml_path=robot_xml_path,
        has_dynamic_object=has_dynamic_object_qpos(model, robot_dof=robot_dof),
    )
