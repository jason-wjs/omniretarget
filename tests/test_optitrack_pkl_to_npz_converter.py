import pickle
from pathlib import Path

import numpy as np

from omniretarget.data_utils.prep_optitrack_for_rt import (
    OPTITRACK_DEMO_JOINTS,
    convert_optitrack_pkl_to_npz,
)


def test_convert_optitrack_pkl_to_npz_outputs_standard_rt_npz(tmp_path: Path) -> None:
    frames: list[dict[str, list[list[float]]]] = []
    for t in range(2):
        frame: dict[str, list[list[float]]] = {}
        for j, joint_name in enumerate(OPTITRACK_DEMO_JOINTS):
            frame[joint_name] = [
                [float(t + j), float(j), float(t)],
                [1.0, 0.0, 0.0, 0.0],
            ]
        frames.append(frame)

    input_pkl = tmp_path / "dance.pkl"
    with input_pkl.open("wb") as f:
        pickle.dump(frames, f)

    output_dir = tmp_path / "out"
    output_path = convert_optitrack_pkl_to_npz(input_pkl, output_dir, height=1.7)

    assert output_path == output_dir / "dance.npz"
    assert output_path.is_file()

    data = np.load(output_path)
    joints = data["global_joint_positions"]
    assert joints.shape == (2, len(OPTITRACK_DEMO_JOINTS), 3)
    assert np.isclose(float(data["height"]), 1.7)
    assert np.allclose(joints[0, 0], [0.0, 0.0, 0.0])
    assert np.allclose(joints[1, 0], [1.0, 0.0, 1.0])
