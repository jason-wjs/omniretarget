from pathlib import Path

from tests.path_helpers import REPO_ROOT


def test_optitrack_converter_script_exists_with_expected_defaults() -> None:
    script = REPO_ROOT / "scripts" / "data_process" / "convert_optitrack_pkl_to_npz.sh"

    assert script.is_file()
    content = script.read_text(encoding="utf-8")

    assert "uv run omniretarget-prep-optitrack" in content
    assert '--input-dir "demo_data/mocap_optitrack"' in content
    assert '--output-dir "demo_data/optitrack_npz"' in content
