from __future__ import annotations

from pathlib import Path

from omniretarget.config_types.retargeting import ParallelRetargetingConfig
from omniretarget.examples import parallel_robot_retarget
from omniretarget.examples.parallel_robot_retarget import find_files as legacy_find_files
from omniretarget.retargeting.batch import find_files


def test_find_files_matches_legacy_smplh_object_filter(tmp_path: Path) -> None:
    (tmp_path / "a_largebox.pt").write_bytes(b"")
    (tmp_path / "b_chair.pt").write_bytes(b"")

    actual = find_files(tmp_path, "smplh", object_name="largebox")
    expected = legacy_find_files(tmp_path, "smplh", object_name="largebox")

    assert actual == expected


def test_parallel_robot_retarget_main_delegates_to_batch(monkeypatch) -> None:
    cfg = ParallelRetargetingConfig()
    calls = []

    def fake_run_parallel_retargeting(actual_cfg):
        calls.append(actual_cfg)

    monkeypatch.setattr(parallel_robot_retarget, "run_parallel_retargeting", fake_run_parallel_retargeting)

    parallel_robot_retarget.main(cfg)

    assert calls == [cfg]
