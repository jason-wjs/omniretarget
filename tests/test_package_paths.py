from __future__ import annotations

from pathlib import Path

from holosoma_retargeting.configs.robot import RobotConfig
from holosoma_retargeting.configs.viser import ViserConfig
from holosoma_retargeting.utils.motion import calculate_scale_factor


def test_package_path_resolves_height_dict() -> None:
    from holosoma_retargeting.path_utils import package_path

    path = package_path("demo_data/height_dict.pkl")
    assert path.exists()


def test_package_path_resolves_robot_urdf() -> None:
    from holosoma_retargeting.path_utils import package_path

    path = package_path("models/g1/g1_29dof.urdf")
    assert path.exists()


def test_package_path_preserves_absolute_paths(tmp_path) -> None:
    from holosoma_retargeting.path_utils import package_path

    absolute_path = tmp_path / "custom_asset.txt"
    assert package_path(absolute_path) == absolute_path


def test_model_path_resolves_packaged_model() -> None:
    from holosoma_retargeting.path_utils import model_path

    path = model_path("g1/g1_29dof.urdf")
    assert path.exists()


def test_model_path_preserves_absolute_paths(tmp_path) -> None:
    from holosoma_retargeting.path_utils import model_path

    absolute_path = tmp_path / "custom_model.urdf"
    assert model_path(absolute_path) == absolute_path


def test_demo_data_path_resolves_packaged_demo_data() -> None:
    from holosoma_retargeting.path_utils import demo_data_path

    path = demo_data_path("height_dict.pkl")
    assert path.exists()


def test_demo_data_path_preserves_absolute_paths(tmp_path) -> None:
    from holosoma_retargeting.path_utils import demo_data_path

    absolute_path = tmp_path / "custom_demo_data.pkl"
    assert demo_data_path(absolute_path) == absolute_path


def test_calculate_scale_factor_is_independent_of_cwd(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)

    assert calculate_scale_factor("sub3_largebox_003", robot_height=1.32) > 0


def test_robot_config_defaults_to_packaged_robot_urdf() -> None:
    from holosoma_retargeting.path_utils import package_path

    cfg = RobotConfig(robot_type="adam_pro")
    assert Path(cfg.ROBOT_URDF_FILE) == package_path("models/adam_pro/adam_pro_29dof.urdf")


def test_viser_config_defaults_to_packaged_robot_urdf() -> None:
    from holosoma_retargeting.path_utils import package_path

    cfg = ViserConfig()
    assert Path(cfg.robot_urdf) == package_path("models/g1/g1_29dof.urdf")
