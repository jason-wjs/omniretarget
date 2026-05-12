from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
import pickle
from typing import Any, Mapping

import mujoco
import numpy as np
try:
    import yaml
except ModuleNotFoundError:  # pragma: no cover - exercised only when optional dependency is absent
    yaml = None

from omniretarget.parc_process.source_io import ParcSample, load_parc_sample


@dataclass(frozen=True)
class PairedOutputResult:
    motion_name: str
    motion_file: Path
    manifest_file: Path

    def load_motion_file(self) -> ParcSample:
        return load_parc_sample(self.motion_file)


def _package_root() -> Path:
    return Path(__file__).resolve().parent.parent


@lru_cache(maxsize=1)
def _g1_joint_axes() -> np.ndarray:
    model_path = _package_root() / "models" / "g1" / "g1_29dof.xml"
    model = mujoco.MjModel.from_xml_path(str(model_path))
    return np.asarray(model.jnt_axis[1:], dtype=np.float64).copy()


def _normalize_quat_wxyz(quat_wxyz: np.ndarray) -> np.ndarray:
    quat_wxyz = np.asarray(quat_wxyz, dtype=np.float64)
    norm = np.linalg.norm(quat_wxyz, axis=-1, keepdims=True)
    return quat_wxyz / np.clip(norm, 1e-8, None)


def _wxyz_to_xyzw(quat_wxyz: np.ndarray) -> np.ndarray:
    quat_wxyz = np.asarray(quat_wxyz, dtype=np.float64)
    return quat_wxyz[..., [1, 2, 3, 0]]


def _joint_angles_to_quats_xyzw(joint_angles: np.ndarray, axes: np.ndarray) -> np.ndarray:
    joint_angles = np.asarray(joint_angles, dtype=np.float64)
    axes = np.asarray(axes, dtype=np.float64)
    axes = axes / np.clip(np.linalg.norm(axes, axis=-1, keepdims=True), 1e-8, None)
    half = joint_angles / 2.0
    sin_half = np.sin(half)[..., None]
    quat_wxyz = np.concatenate([np.cos(half)[..., None], axes[None, :, :] * sin_half], axis=-1)
    return _wxyz_to_xyzw(quat_wxyz)


def _terrain_payload(source_sample: ParcSample) -> dict[str, Any]:
    return {
        "hf": np.asarray(source_sample.terrain_data.hf),
        "hf_maxmin": np.asarray(source_sample.terrain_data.hf_maxmin),
        "min_point": np.asarray(source_sample.terrain_data.min_point),
        "dx": float(source_sample.terrain_data.dx),
    }


def _motion_payload(qpos: np.ndarray, source_sample: ParcSample) -> dict[str, Any]:
    qpos = np.asarray(qpos, dtype=np.float64)
    joint_axes = _g1_joint_axes()
    expected_qpos = 7 + joint_axes.shape[0]
    if qpos.ndim != 2 or qpos.shape[1] < expected_qpos:
        raise ValueError(f"Expected qpos with shape (T, >= {expected_qpos}), got {qpos.shape}")

    root_pos = qpos[:, 0:3].astype(np.float32)
    root_rot = _wxyz_to_xyzw(_normalize_quat_wxyz(qpos[:, 3:7])).astype(np.float32)
    joint_rot = _joint_angles_to_quats_xyzw(qpos[:, 7:expected_qpos], joint_axes).astype(np.float32)
    body_contacts = source_sample.motion_data.body_contacts
    if body_contacts is not None:
        body_contacts = np.asarray(body_contacts).copy()

    return {
        "root_pos": root_pos,
        "root_rot": root_rot,
        "joint_rot": joint_rot,
        "body_contacts": body_contacts,
        "fps": int(source_sample.motion_data.fps),
        "loop_mode": str(source_sample.motion_data.loop_mode),
    }


def _misc_payload(
    *,
    source_sample: ParcSample,
    motion_name: str,
    scale_factor: float,
    workspace_path: str | Path | None,
    retarget_config: Mapping[str, Any] | None,
) -> dict[str, Any]:
    misc_data = dict(source_sample.misc_data or {})
    misc_data["motion_name"] = motion_name
    misc_data["parc_process:source_sample"] = str(source_sample.path)
    misc_data["parc_process:scale_factor"] = float(scale_factor)
    if workspace_path is not None:
        misc_data["parc_process:workspace_path"] = str(Path(workspace_path).expanduser().resolve())
    if source_sample.motion_data.body_contacts is not None:
        misc_data["parc_process:source_body_contacts"] = np.asarray(source_sample.motion_data.body_contacts).copy()
    if retarget_config is not None:
        misc_data["parc_process:retarget_config"] = dict(retarget_config)
    return misc_data


def _write_ms_container(
    *,
    motion_payload: dict[str, Any],
    terrain_payload: dict[str, Any],
    misc_payload: dict[str, Any],
    motion_file: Path,
) -> None:
    container = {
        "motion_data": pickle.dumps(motion_payload),
        "terrain_data": pickle.dumps(terrain_payload),
        "misc_data": pickle.dumps(misc_payload),
    }
    with motion_file.open("wb") as f:
        pickle.dump(container, f)


def _update_manifest(manifest_file: Path, motion_file: Path, motion_name: str, weight: float) -> None:
    if manifest_file.exists():
        if yaml is None:
            raise RuntimeError("PyYAML is required to update existing PARC motions.yaml manifests.")
        manifest = yaml.safe_load(manifest_file.read_text()) or {}
        motions = list(manifest.get("motions", []))
    else:
        motions = []

    new_entry = {"file": str(motion_file), "weight": float(weight), "name": motion_name}
    motions = [entry for entry in motions if entry.get("name") != motion_name and entry.get("file") != str(motion_file)]
    motions.append(new_entry)
    if yaml is not None:
        manifest_file.write_text(yaml.safe_dump({"motions": motions}, sort_keys=False))
    else:
        lines = ["motions:"]
        for entry in motions:
            lines.extend(
                [
                    f"- file: {entry['file']}",
                    f"  weight: {entry['weight']}",
                    f"  name: {entry['name']}",
                ]
            )
        manifest_file.write_text("\n".join(lines) + "\n")


def write_paired_output(
    *,
    qpos: np.ndarray,
    source_sample: ParcSample,
    output_root: str | Path,
    motion_name: str,
    scale_factor: float = 1.0,
    workspace_path: str | Path | None = None,
    retarget_config: Mapping[str, Any] | None = None,
    weight: float = 1.0,
) -> PairedOutputResult:
    root_dir = Path(output_root).expanduser().resolve()
    root_dir.mkdir(parents=True, exist_ok=True)

    motion_file = root_dir / f"{motion_name}.pkl"
    manifest_file = root_dir / "motions.yaml"

    _write_ms_container(
        motion_payload=_motion_payload(qpos, source_sample),
        terrain_payload=_terrain_payload(source_sample),
        misc_payload=_misc_payload(
            source_sample=source_sample,
            motion_name=motion_name,
            scale_factor=scale_factor,
            workspace_path=workspace_path,
            retarget_config=retarget_config,
        ),
        motion_file=motion_file,
    )
    _update_manifest(manifest_file, motion_file, motion_name, weight)

    return PairedOutputResult(
        motion_name=motion_name,
        motion_file=motion_file,
        manifest_file=manifest_file,
    )
