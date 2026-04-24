from pathlib import Path

from tests.path_helpers import REPO_ROOT


def test_lafan_bvh_to_npy_script_exists_with_expected_converter_call() -> None:
    script = REPO_ROOT / "scripts" / "data_process" / "convert_lafan_bvh_to_npy.sh"

    assert script.is_file()
    content = script.read_text(encoding="utf-8")

    assert "uv run omniretarget-extract-global-positions" in content
    assert '--input-dir "demo_data/lafan1_raw_bvh"' in content
    assert '--output-dir "demo_data/lafan1"' in content
