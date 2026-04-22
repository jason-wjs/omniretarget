from pathlib import Path


def test_batch_retarget_script_defaults_to_optitrack_robot_only() -> None:
    repo_root = Path(__file__).resolve().parents[3]
    script = repo_root / "scripts" / "retargeting" / "retarget_batch_clips.sh"

    assert script.is_file()
    content = script.read_text(encoding="utf-8")

    assert "examples/parallel_robot_retarget.py" in content
    assert '--task-type robot_only' in content
    assert 'DATA_FORMAT="${DATA_FORMAT:-optitrack}"' in content
    assert 'DATA_DIR="${DATA_DIR:-demo_data/optitrack_npz}"' in content
    assert 'SAVE_DIR="${SAVE_DIR:-demo_results_parallel/${ROBOT}/robot_only/optitrack}"' in content
