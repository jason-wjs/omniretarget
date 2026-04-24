#!/usr/bin/env python3
"""Convert OptiTrack pkl clips to retargeting-ready npz clips."""

from __future__ import annotations

import pickle
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import tyro

from holosoma_retargeting.config_types.data_type import OPTITRACK_DEMO_JOINTS


def _extract_joint_position(joint_entry: object, joint_name: str) -> np.ndarray:
    """Extract xyz position from one OptiTrack joint entry."""
    if not isinstance(joint_entry, (list, tuple)) or len(joint_entry) < 1:
        raise ValueError(f"Invalid entry for joint '{joint_name}': expected [pos, quat], got {type(joint_entry)}")

    pos = np.asarray(joint_entry[0], dtype=np.float64)
    if pos.shape != (3,):
        raise ValueError(f"Invalid position shape for joint '{joint_name}': expected (3,), got {pos.shape}")
    return pos


def convert_optitrack_pkl_to_npz(input_pkl: Path, output_dir: Path, height: float = 1.7) -> Path:
    """Convert one OptiTrack .pkl file into standard retargeting .npz format."""
    with input_pkl.open("rb") as f:
        frames = pickle.load(f)

    if not isinstance(frames, list) or len(frames) == 0:
        raise ValueError(f"OptiTrack file '{input_pkl}' must contain a non-empty list of frames")

    num_frames = len(frames)
    num_joints = len(OPTITRACK_DEMO_JOINTS)
    positions = np.zeros((num_frames, num_joints, 3), dtype=np.float64)

    for frame_idx, frame in enumerate(frames):
        if not isinstance(frame, dict):
            raise ValueError(f"Frame {frame_idx} in '{input_pkl}' is not a dict")

        for joint_idx, joint_name in enumerate(OPTITRACK_DEMO_JOINTS):
            if joint_name not in frame:
                raise KeyError(f"Missing joint '{joint_name}' in frame {frame_idx} of '{input_pkl}'")
            positions[frame_idx, joint_idx] = _extract_joint_position(frame[joint_name], joint_name)

    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / f"{input_pkl.stem}.npz"
    np.savez(
        output_path,
        global_joint_positions=positions,
        height=float(height),
    )
    return output_path


@dataclass
class Config:
    """Configuration for converting OptiTrack pkl data."""

    input_dir: str = "demo_data/mocap_optitrack"
    output_dir: str = "demo_data/mocap_optitrack_npz"
    height: float = 1.7


def main(cfg: Config) -> None:
    input_dir = Path(cfg.input_dir)
    output_dir = Path(cfg.output_dir)

    if not input_dir.exists():
        raise FileNotFoundError(f"Input directory not found: {input_dir}")

    pkl_files = sorted(input_dir.glob("*.pkl"))
    if len(pkl_files) == 0:
        raise FileNotFoundError(f"No .pkl files found under: {input_dir}")

    for pkl_file in pkl_files:
        output_path = convert_optitrack_pkl_to_npz(pkl_file, output_dir, cfg.height)
        print(f"Converted {pkl_file} -> {output_path}")


def entrypoint() -> None:
    main(tyro.cli(Config))


if __name__ == "__main__":
    entrypoint()
