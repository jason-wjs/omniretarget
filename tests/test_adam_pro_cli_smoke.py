from pathlib import Path

import numpy as np
import pytest


def test_robot_only_smoke_output_exists_and_shape_matches() -> None:
    out = Path("/tmp/adam_pro_rt_smoke/sub3_largebox_003.npz")
    if not out.is_file():
        pytest.skip("Generate /tmp/adam_pro_rt_smoke/sub3_largebox_003.npz before running this smoke check.")
    assert out.is_file()
    qpos = np.load(out)["qpos"]
    assert qpos.shape[1] == 36  # 7 floating base + 29 robot dof
