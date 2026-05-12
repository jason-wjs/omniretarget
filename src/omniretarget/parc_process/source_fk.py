from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import xml.etree.ElementTree as ET

import numpy as np

from omniretarget.parc_process.source_io import ParcMotionData


@dataclass(frozen=True)
class SourceSkeleton:
    body_names: tuple[str, ...]
    parent_indices: np.ndarray
    local_translations: np.ndarray
    local_rotations_wxyz: np.ndarray


def _parse_vec(attr: str | None, *, size: int, default: list[float]) -> np.ndarray:
    if attr is None:
        return np.asarray(default, dtype=np.float64)
    values = [float(x) for x in attr.split()]
    if len(values) != size:
        raise ValueError(f"Expected {size} values, got {len(values)}")
    return np.asarray(values, dtype=np.float64)


def _normalize_quat(quat_wxyz: np.ndarray) -> np.ndarray:
    norm = np.linalg.norm(quat_wxyz, axis=-1, keepdims=True)
    return quat_wxyz / np.clip(norm, 1e-8, None)


def _xyzw_to_wxyz(quat_xyzw: np.ndarray) -> np.ndarray:
    quat_xyzw = np.asarray(quat_xyzw, dtype=np.float64)
    return quat_xyzw[..., [3, 0, 1, 2]]


def _quat_mul(q1: np.ndarray, q2: np.ndarray) -> np.ndarray:
    w1, x1, y1, z1 = np.moveaxis(q1, -1, 0)
    w2, x2, y2, z2 = np.moveaxis(q2, -1, 0)
    return np.stack(
        (
            w1 * w2 - x1 * x2 - y1 * y2 - z1 * z2,
            w1 * x2 + x1 * w2 + y1 * z2 - z1 * y2,
            w1 * y2 - x1 * z2 + y1 * w2 + z1 * x2,
            w1 * z2 + x1 * y2 - y1 * x2 + z1 * w2,
        ),
        axis=-1,
    )


def _quat_rotate(quat_wxyz: np.ndarray, vec_xyz: np.ndarray) -> np.ndarray:
    qvec = quat_wxyz[..., 1:]
    uv = np.cross(qvec, vec_xyz)
    uuv = np.cross(qvec, uv)
    return vec_xyz + 2.0 * (quat_wxyz[..., :1] * uv + uuv)


def parse_humanoid_xml(xml_path: str | Path) -> SourceSkeleton:
    tree = ET.parse(Path(xml_path))
    worldbody = tree.getroot().find("worldbody")
    if worldbody is None:
        raise ValueError("humanoid.xml is missing <worldbody>")

    body_names: list[str] = []
    parent_indices: list[int] = []
    local_translations: list[np.ndarray] = []
    local_rotations_wxyz: list[np.ndarray] = []

    def visit(node: ET.Element, parent_idx: int) -> None:
        name = node.attrib.get("name")
        if not name:
            return
        curr_idx = len(body_names)
        body_names.append(name)
        parent_indices.append(parent_idx)
        local_translations.append(
            _parse_vec(node.attrib.get("pos"), size=3, default=[0.0, 0.0, 0.0])
        )
        local_rotations_wxyz.append(
            _normalize_quat(
                _parse_vec(node.attrib.get("quat"), size=4, default=[1.0, 0.0, 0.0, 0.0])
            )
        )
        for child in node.findall("body"):
            visit(child, curr_idx)

    root_body = next((child for child in worldbody.findall("body") if child.attrib.get("name")), None)
    if root_body is None:
        raise ValueError("humanoid.xml has no named root body")
    visit(root_body, -1)

    return SourceSkeleton(
        body_names=tuple(body_names),
        parent_indices=np.asarray(parent_indices, dtype=np.int64),
        local_translations=np.asarray(local_translations, dtype=np.float64),
        local_rotations_wxyz=np.asarray(local_rotations_wxyz, dtype=np.float64),
    )


def build_source_joint_positions(
    motion_data: ParcMotionData,
    xml_path: str | Path,
) -> tuple[np.ndarray, tuple[str, ...]]:
    skeleton = parse_humanoid_xml(xml_path)
    root_pos = np.asarray(motion_data.root_pos, dtype=np.float64)
    root_rot_wxyz = _normalize_quat(_xyzw_to_wxyz(motion_data.root_rot))
    joint_rot_wxyz = _normalize_quat(_xyzw_to_wxyz(motion_data.joint_rot))

    num_frames = root_pos.shape[0]
    num_bodies = len(skeleton.body_names)
    body_pos = np.zeros((num_frames, num_bodies, 3), dtype=np.float64)
    body_rot = np.zeros((num_frames, num_bodies, 4), dtype=np.float64)

    body_pos[:, 0, :] = root_pos
    body_rot[:, 0, :] = root_rot_wxyz

    for body_idx in range(1, num_bodies):
        parent_idx = int(skeleton.parent_indices[body_idx])
        parent_pos = body_pos[:, parent_idx, :]
        parent_rot = body_rot[:, parent_idx, :]
        local_trans = np.broadcast_to(skeleton.local_translations[body_idx], parent_pos.shape)
        local_rot = np.broadcast_to(skeleton.local_rotations_wxyz[body_idx], parent_rot.shape)
        world_trans = _quat_rotate(parent_rot, local_trans)
        body_pos[:, body_idx, :] = parent_pos + world_trans
        body_rot[:, body_idx, :] = _quat_mul(parent_rot, _quat_mul(local_rot, joint_rot_wxyz[:, body_idx - 1, :]))

    return body_pos.astype(np.float32), skeleton.body_names
