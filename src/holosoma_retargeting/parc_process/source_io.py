from __future__ import annotations

import pickle
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np


@dataclass(frozen=True)
class ParcMotionData:
    root_pos: np.ndarray
    root_rot: np.ndarray
    joint_rot: np.ndarray
    body_contacts: np.ndarray | None
    fps: int
    loop_mode: str


@dataclass(frozen=True)
class ParcTerrainData:
    hf: np.ndarray
    hf_maxmin: np.ndarray
    min_point: np.ndarray
    dx: float


@dataclass(frozen=True)
class ParcSample:
    path: Path
    motion_data: ParcMotionData
    terrain_data: ParcTerrainData
    misc_data: dict[str, Any]


def _require_payload(container: dict[str, Any], key: str) -> Any:
    payload = container.get(key)
    if payload is None:
        raise ValueError(f"Missing payload: {key}")
    return pickle.loads(payload)


def load_parc_sample(path: str | Path) -> ParcSample:
    sample_path = Path(path).expanduser().resolve()
    with sample_path.open("rb") as f:
        container = pickle.load(f)

    motion_payload = _require_payload(container, "motion_data")
    terrain_payload = _require_payload(container, "terrain_data")
    misc_payload = container.get("misc_data")
    misc_data = {} if misc_payload is None else pickle.loads(misc_payload)

    motion_data = ParcMotionData(**motion_payload)
    terrain_data = ParcTerrainData(**terrain_payload)
    return ParcSample(
        path=sample_path,
        motion_data=motion_data,
        terrain_data=terrain_data,
        misc_data=misc_data,
    )
