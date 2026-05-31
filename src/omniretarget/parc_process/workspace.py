from __future__ import annotations

from dataclasses import dataclass, replace
from pathlib import Path
from typing import Any, Mapping

import numpy as np

from omniretarget.parc_process.source_fk import build_source_joint_positions
from omniretarget.parc_process.source_io import ParcSample
from omniretarget.parc_process.terrain_scene import export_parc_scene


@dataclass(frozen=True)
class ParcWorkspace:
    task_name: str
    task_dir: Path
    joints_file: Path
    object_dir: Path
    asset_xml_path: Path
    scene_xml_path: Path
    urdf_path: Path
    obj_path: Path
    terrain_hf_path: Path
    terrain_collision_path: Path
    joint_names: tuple[str, ...]
    z_origin: float = 0.0


def _terrain_z_origin(sample: ParcSample) -> float:
    hf = np.asarray(sample.terrain_data.hf, dtype=np.float64)
    if hf.size == 0:
        return 0.0
    finite_hf = hf[np.isfinite(hf)]
    if finite_hf.size == 0:
        return 0.0
    return float(np.min(finite_hf))


def _normalized_terrain(sample: ParcSample, z_origin: float):
    return replace(
        sample.terrain_data,
        hf=np.asarray(sample.terrain_data.hf, dtype=np.float32) - np.float32(z_origin),
        hf_maxmin=np.asarray(sample.terrain_data.hf_maxmin, dtype=np.float32) - np.float32(z_origin),
    )


def build_parc_workspace(
    *,
    sample: ParcSample,
    source_xml: str | Path,
    output_dir: str | Path,
    task_name: str,
    object_name: str = "multi_boxes",
    xy_scale: float = 1.0,
    height_scale: float = 1.0,
    scale_source: Mapping[str, Any] | None = None,
) -> ParcWorkspace:
    root_dir = Path(output_dir).expanduser().resolve()
    task_dir = root_dir / task_name
    task_dir.mkdir(parents=True, exist_ok=True)

    human_joints, joint_names = build_source_joint_positions(sample.motion_data, source_xml)
    z_origin = _terrain_z_origin(sample)
    human_joints = np.asarray(human_joints, dtype=np.float32).copy()
    human_joints[:, :, 2] -= np.float32(z_origin)
    normalized_terrain = _normalized_terrain(sample, z_origin)

    joints_file = task_dir / "human_joints.npy"
    np.save(joints_file, human_joints)

    scene = export_parc_scene(
        normalized_terrain,
        task_dir,
        object_name=object_name,
        xy_scale=xy_scale,
        height_scale=height_scale,
        scale_source={
            **dict(scale_source or {}),
            "z_origin": float(z_origin),
            "z_origin_rule": "terrain_data.hf nanmin",
        },
    )

    return ParcWorkspace(
        task_name=task_name,
        task_dir=task_dir,
        joints_file=joints_file,
        object_dir=task_dir,
        asset_xml_path=scene.asset_xml_path,
        scene_xml_path=scene.scene_xml_path,
        urdf_path=scene.urdf_path,
        obj_path=scene.obj_path,
        terrain_hf_path=scene.terrain_hf_path,
        terrain_collision_path=scene.terrain_collision_path,
        joint_names=joint_names,
        z_origin=float(z_origin),
    )
