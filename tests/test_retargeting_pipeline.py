from __future__ import annotations

from types import SimpleNamespace

from omniretarget.config_types.retargeter import RetargeterConfig
from omniretarget.config_types.retargeting import RetargetingConfig
from omniretarget.examples import robot_retarget
from omniretarget.examples.robot_retarget import build_retargeter_kwargs_from_config as legacy_build_kwargs
from omniretarget.retargeting.pipeline import DEFAULT_DATA_FORMATS, DEFAULT_SAVE_DIRS, build_retargeter_kwargs_from_config


def test_pipeline_default_data_formats_match_legacy() -> None:
    assert DEFAULT_DATA_FORMATS == robot_retarget.DEFAULT_DATA_FORMATS


def test_pipeline_default_save_dirs_match_legacy() -> None:
    assert DEFAULT_SAVE_DIRS == robot_retarget.DEFAULT_SAVE_DIRS


def test_build_retargeter_kwargs_matches_legacy_robot_only() -> None:
    retargeter_config = RetargeterConfig(q_a_init_idx=-3, activate_foot_sticking=False)
    constants = SimpleNamespace()

    actual = build_retargeter_kwargs_from_config(
        retargeter_config=retargeter_config,
        constants=constants,
        object_urdf_path=None,
        task_type="robot_only",
    )
    expected = legacy_build_kwargs(
        retargeter_config=retargeter_config,
        constants=constants,
        object_urdf_path=None,
        task_type="robot_only",
    )

    assert actual == expected


def test_build_retargeter_kwargs_matches_legacy_climbing_nominal_tau() -> None:
    retargeter_config = RetargeterConfig(nominal_tracking_tau=0.25)
    constants = SimpleNamespace()

    actual = build_retargeter_kwargs_from_config(
        retargeter_config=retargeter_config,
        constants=constants,
        object_urdf_path="object.urdf",
        task_type="climbing",
    )
    expected = legacy_build_kwargs(
        retargeter_config=retargeter_config,
        constants=constants,
        object_urdf_path="object.urdf",
        task_type="climbing",
    )

    assert actual == expected


def test_robot_retarget_main_delegates_to_pipeline(monkeypatch) -> None:
    cfg = RetargetingConfig()
    calls = []

    def fake_run_single_retargeting(actual_cfg):
        calls.append(actual_cfg)

    monkeypatch.setattr(robot_retarget, "run_single_retargeting", fake_run_single_retargeting)

    robot_retarget.main(cfg)

    assert calls == [cfg]
