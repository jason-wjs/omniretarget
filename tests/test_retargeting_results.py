from __future__ import annotations

from pathlib import Path

import pytest

from omniretarget.examples.robot_retarget import determine_output_path as legacy_determine_output_path
from omniretarget.retargeting.results import determine_output_path


@pytest.mark.parametrize("task_type", ["robot_only", "object_interaction", "climbing"])
@pytest.mark.parametrize("augmentation", [False, True])
def test_determine_output_path_matches_legacy(task_type: str, augmentation: bool) -> None:
    save_dir = Path("/tmp/results")

    actual = determine_output_path(task_type, save_dir, "sample", augmentation)
    expected = legacy_determine_output_path(task_type, save_dir, "sample", augmentation)

    assert actual == expected
