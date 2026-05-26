from pathlib import Path

from tests.path_helpers import REPO_ROOT


def test_batch_retarget_script_defaults_to_optitrack_robot_only() -> None:
    script = REPO_ROOT / "scripts" / "retarget_batch_clips.sh"

    assert script.is_file()
    content = script.read_text(encoding="utf-8")

    assert "examples/parallel_robot_retarget.py" in content
    assert '--task-type robot_only' in content
    assert 'DATA_FORMAT="${DATA_FORMAT:-optitrack}"' in content
    assert 'DATA_DIR="${DATA_DIR:-demo_data/optitrack_npz}"' in content
    assert 'SAVE_DIR="${SAVE_DIR:-demo_results_parallel/${ROBOT}/robot_only/optitrack}"' in content
