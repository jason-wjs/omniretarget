from __future__ import annotations

from pathlib import Path

from omniretarget.config_types.robot import RobotConfig
from omniretarget.config_types.viser import ViserConfig
from omniretarget.retargeting.motion_data import calculate_scale_factor


def test_package_path_resolves_height_dict() -> None:
    from omniretarget.path_utils import package_path

    path = package_path("demo_data/height_dict.pkl")
    assert path.exists()


def test_package_path_resolves_robot_urdf() -> None:
    from omniretarget.path_utils import package_path

    path = package_path("models/g1/g1_29dof.urdf")
    assert path.exists()


def test_calculate_scale_factor_is_independent_of_cwd(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)

    assert calculate_scale_factor("sub3_largebox_003", robot_height=1.32) > 0


def test_robot_config_defaults_to_packaged_robot_urdf() -> None:
    from omniretarget.path_utils import package_path

    cfg = RobotConfig(robot_type="adam_pro")
    assert Path(cfg.ROBOT_URDF_FILE) == package_path("models/adam_pro/adam_pro_29dof.urdf")


def test_viser_config_defaults_to_packaged_robot_urdf() -> None:
    from omniretarget.path_utils import package_path

    cfg = ViserConfig()
    assert Path(cfg.robot_urdf) == package_path("models/g1/g1_29dof.urdf")
